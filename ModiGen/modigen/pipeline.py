"""
ModiGen パイプラインの一元化モジュール

このモジュールは既存の CLI から呼び出される共通処理を集約し、
将来の MCP 化 / GUI 化時にも同一 API を利用できるようにします。

提供機能（主な関数）
- setup_embeddings_and_llm(cfg): 埋め込みモデルと LLM の初期化
- build_or_load_rag_index(cfg): RAG 用のインデックスを構築 or 既存ストレージからロード
- run_generation(cfg): RAG を用いた Modelica コード生成（GRAG/generate.py から利用）
- run_validation_and_analysis(cfg, ...): 抽出→分類→検証→集計（__main__.py から利用）

注意:
- ここでは I/O やリソース初期化（OMC セッション / LlamaIndex Settings）を局所化し、
  上位（CLI/MCP/GUI）に副作用を漏らさない設計を心がけています。
"""

import os
import re
import json
import time
import concurrent.futures
from typing import Optional, Dict, Any

from OMPython import OMCSessionZMQ
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    PropertyGraphIndex,
)
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.prompts import PromptTemplate
from llama_index.core.embeddings import resolve_embed_model

from modigen.config import Config, load_config, resolve_output_dir
from modigen.llm import create_llm

from validation.text_postprocess import process_files, classify_files
from validation.model_test_for_instance import (
    load_simulation_durations,
    process_version_instance,
    load_libraries1,
)
from validation.model_test_for_model import (
    process_version_model,
    load_libraries,
)
from validation.result_analysis import analyze_relationship, add_type_to_results
from validation.calc_passatk import estimate_pass_at_k


MAX_TIMEOUT = 60  # 生成のタイムアウト（秒）


def setup_embeddings_and_llm(cfg: Config) -> None:
    """埋め込みモデルと LLM を LlamaIndex の Settings に設定する。

    - 埋め込みは resolve_embed_model の文字列指定（local: など）を利用。
    - LLM は modigen.llm.create_llm のファクトリで選択（local_hf / openai / azure_openai）。
    """
    # Embeddings（設定文字列に従う）
    Settings.embed_model = resolve_embed_model(cfg.generation.embed_model)

    # LLM（プロバイダに応じて切り替え）
    if cfg.generation.llm_provider == "local_hf":
        if not cfg.generation.llm_model_path:
            raise RuntimeError("local_hf を使用するには generation.llm_model_path を設定してください。")
        Settings.llm = create_llm(
            provider="local_hf",
            model_path=cfg.generation.llm_model_path,
            temperature=cfg.generation.temperature,
            max_new_tokens=cfg.generation.max_new_tokens,
        )
    elif cfg.generation.llm_provider in ("openai", "azure_openai"):
        Settings.llm = create_llm(
            provider=cfg.generation.llm_provider,
            model=cfg.generation.llm_model,
            openai_api_base=cfg.generation.openai_api_base,
            openai_api_key=cfg.generation.openai_api_key,
            openai_api_version=cfg.generation.openai_api_version,
            openai_deployment=cfg.generation.openai_deployment,
            apim_subscription_key_header=cfg.generation.apim_subscription_key_header,
            apim_subscription_key=cfg.generation.apim_subscription_key,
        )
    else:
        raise RuntimeError(f"未対応の llm_provider です: {cfg.generation.llm_provider}")


def build_or_load_rag_index(cfg: Config):
    """RAG の PropertyGraph インデックスをロード（永続済）または新規構築する。

    戻り値: (pg_index, query_engine)
    """
    documents = SimpleDirectoryReader(cfg.generation.docs_dir).load_data()
    try:
        storage_context = StorageContext.from_defaults(persist_dir=cfg.generation.rag_persist_dir)
        pg_index = load_index_from_storage(storage_context)
    except Exception:
        # 永続化が見つからない/ロード失敗 → 新規構築
        space_name = "modelica"
        graph_store = SimpleGraphStore(space_name=space_name, edge_types=["relationship"], tags=["entity"])
        storage_context = StorageContext.from_defaults(graph_store=graph_store)
        pg_index = PropertyGraphIndex.from_documents(
            documents=documents,
            storage_context=storage_context,
            show_progress=True,
            max_triplets_per_chunk=10,
            include_embeddings=True,
        )
        pg_index.storage_context.persist(cfg.generation.rag_persist_dir)

    qa_prompt_tmpl_str = (
        """These are examples of modelica code generation. 
        Focus on the contents which related to the query and ignore irrelevant information.\n"""
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        """Focus on the source of the library and components being used.
        Query: {query_str}\n
        Note: You only need to output valid and well-structured Modelica scripts.\n"""
    )
    qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
    query_engine = pg_index.as_query_engine(similarity_top_k=1)
    query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
    return pg_index, query_engine


def run_generation(cfg: Optional[Config] = None) -> None:
    """RAG を利用した生成処理一式を実行する。

    - コンテキスト: context/0_Prompt_{mode}.txt
    - 入力 JSON: json_files/test_6_libraries_new.json
    - 出力: generation_example/{mode}_result/...（設定に依存）
    """
    cfg = cfg or load_config()
    total_start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート想定
    current_folder = os.path.join(base_dir)

    mode = cfg.generation.mode
    context_file = os.path.join(current_folder, f"context/0_Prompt_{mode}.txt")
    output_dir = os.path.join(current_folder, resolve_output_dir(cfg))
    json_file_path = os.path.join(current_folder, f"json_files/test_6_libraries_new.json")

    # 設定に基づき Embeddings / LLM を準備
    setup_embeddings_and_llm(cfg)
    # RAG インデックスを構築/ロード
    _, query_engine = build_or_load_rag_index(cfg)

    # コンテキスト / 指示文の読み込み
    with open(context_file, "r", encoding="utf-8") as f:
        context_text = f.read()
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    instructions = [item["instruction"] for item in data[f"{mode}"]]

    os.makedirs(output_dir, exist_ok=True)

    def _write_file(path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as wf:
            wf.write(content)

    # 生成ループ（回数は設定依存）
    for run_number in range(1, cfg.generation.num_runs + 1):
        run_start_time = time.time()
        for idx, instruction in enumerate(instructions):
            prompt_text = instruction
            combined_query = prompt_text  # 必要に応じて context_text 連結も可
            output_file_name = f"{mode}_{idx+1}_response_{run_number}.txt"
            output_path = os.path.join(output_dir, output_file_name)
            if os.path.exists(output_path):
                print(f"既存ファイルをスキップ: {output_file_name}")
                continue
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(query_engine.query, combined_query)
                    response_rag = future.result(timeout=MAX_TIMEOUT)
                generated_text = response_rag.response
                _write_file(output_path, generated_text)
                print(f"生成完了: {output_path}")
            except concurrent.futures.TimeoutError:
                print(f"タイムアウト: idx={idx+1} → LLM フォールバック")
                response = Settings.llm.complete(prompt=combined_query)
                _write_file(output_path, response.text)
            except Exception as e:
                print(f"生成エラー: idx={idx+1}: {e} → LLM フォールバック")
                response = Settings.llm.complete(prompt=combined_query)
                _write_file(output_path, response.text)
        print(f"Run {run_number} 所要時間: {(time.time() - run_start_time)/3600:.2f} h")

    print("生成処理が完了しました。合計時間: {:.2f} h".format((time.time() - total_start_time)/3600))


def run_validation_and_analysis(
    cfg: Optional[Config] = None,
    *,
    mode_override: Optional[str] = None,
    input_txt_dir: Optional[str] = None,
    processed_mo_dir: Optional[str] = None,
    simulation_base_dir: Optional[str] = None,
    results_base_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """抽出→分類→検証→結果保存→集計→pass@k 計算までを実行。

    戻り値: 主要な出力ファイルパスなどの情報を返す辞書。
    """
    cfg = cfg or load_config()
    current_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    mode = mode_override or cfg.generation.mode

    # 入出力ディレクトリの解決（引数優先 → 設定）
    input_folder = os.path.join(current_folder, input_txt_dir or cfg.validation.input_txt_dir)
    output_folder = os.path.join(current_folder, processed_mo_dir or cfg.validation.processed_mo_dir)
    simu_base_dir = os.path.join(current_folder, simulation_base_dir or cfg.validation.simulation_base_dir)
    results_dir = os.path.join(current_folder, results_base_dir or cfg.validation.results_base_dir)
    os.makedirs(results_dir, exist_ok=True)

    # 1) テキストから .mo 抽出
    process_files(input_folder, output_folder, mode)
    # 2) バージョン毎に分類
    classify_files(output_folder)

    # 3) 依存ライブラリ設定を読み込み
    lib_files_dir = os.path.join(current_folder, cfg.libraries.libraries_root_dir)
    lib_files_json = os.path.join(current_folder, cfg.libraries.libraries_json)
    with open(lib_files_json, "r", encoding="utf-8") as f:
        lib_files_data = json.load(f)

    # 4) モデル検証（OMC セッション）
    omc = OMCSessionZMQ()
    mo_files_base_dir = output_folder
    simu_dir_by_version = os.path.join(simu_base_dir)
    os.makedirs(simu_dir_by_version, exist_ok=True)

    all_check_results = {}
    if mode == "model":
        for version, lib_files in lib_files_data.items():
            mo_files_dir = os.path.join(mo_files_base_dir, f"model-{version}")
            simu_dir = os.path.join(simu_dir_by_version, f"simulation-{version}")
            os.makedirs(simu_dir, exist_ok=True)
            load_libraries(lib_files, lib_files_dir, version, omc)
            model_results = process_version_model(
                version, mo_files_dir, simu_dir, all_check_results, lib_files, lib_files_dir, omc
            )
            omc.sendExpression("clear()")
        result_file = os.path.join(results_dir, f"all_check_results_by_model.json")
        with open(result_file, "w", encoding="utf-8") as wf:
            json.dump(model_results, wf, indent=4)
    else:  # instance
        simulation_durations_csv = os.path.join(current_folder, cfg.validation.reference_instance_csv)
        simulation_durations = load_simulation_durations(simulation_durations_csv)
        for version, lib_files in lib_files_data.items():
            mo_files_dir = os.path.join(mo_files_base_dir, f"model-{version}")
            simu_dir = os.path.join(simu_dir_by_version, f"simulation-{version}")
            os.makedirs(simu_dir, exist_ok=True)
            load_libraries1(lib_files, lib_files_dir, version, omc)
            model_results = process_version_instance(
                version,
                mo_files_dir,
                simu_dir,
                all_check_results,
                simulation_durations,
                lib_files,
                lib_files_dir,
                omc,
            )
            omc.sendExpression("clear()")
        result_file = os.path.join(results_dir, f"all_check_results_by_instance.json")
        with open(result_file, "w", encoding="utf-8") as wf:
            json.dump(model_results, wf, indent=4)

    # 5) 集計
    # 入力 .txt の総数カウント（pass@k でも使用）
    pattern = re.compile(f"{mode}_\\(\\d+\\)_response_\\d+\\.txt")
    total_files = 0
    file_counts = {}
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".txt"):
            m = pattern.match(file_name)
            if not m:
                continue
            model_number = m.group(1)
            model_key = f"{mode}_{model_number}"
            file_counts[model_key] = file_counts.get(model_key, 0) + 1
            total_files += 1

    total_txt_files = {}
    for key in sorted(file_counts.keys(), key=lambda k: int(k.split("_")[1])):
        total_txt_files[key] = {"txt_files": file_counts[key]}

    models_file = os.path.join(current_folder, "json_files/test_6_libraries_new.json")
    with open(models_file, "r", encoding="utf-8") as f:
        models_data = json.load(f)["model"]
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    analysis_results = analyze_relationship(data, total_files)
    formatted_results = {"results": analysis_results["model_summary"]}
    combined_results = {"results": {}}
    for model_key, result_data in formatted_results["results"].items():
        if model_key in total_txt_files:
            combined_results["results"][model_key] = {
                "txt_files": total_txt_files[model_key]["txt_files"],
                **result_data,
            }
        else:
            combined_results["results"][model_key] = result_data

    if mode == "model":
        combined_results["results"] = add_type_to_results(models_data, combined_results["results"])
    results = {
        "statistics": analysis_results["statistics"],
        "results": combined_results["results"],
    }
    output_file = os.path.join(results_dir, f"results_analysis_{mode}.json")
    with open(output_file, "w", encoding="utf-8") as wf:
        json.dump(results, wf, indent=4)
    print(f"集計結果を書き出しました: {output_file}")

    # 6) pass@k 計算
    with open(output_file, "r", encoding="utf-8") as f:
        results_loaded = json.load(f)

    if mode == "model":
        n = 129
        num_samples = [10 for _ in range(n)]
    else:
        n = 127
        num_samples = [5 for _ in range(n)]
    num_correct1 = [m["check_not_empty_simu_true"] for m in results_loaded["results"].values()]
    num_correct = num_correct1[:n] + [0] * (n - len(num_correct1))
    scenario = 5 if mode != "model" else 8
    pass_at_1_results = estimate_pass_at_k(num_samples, num_correct, 1)
    pass_at_k_results = estimate_pass_at_k(num_samples, num_correct, scenario)
    print("Average Pass@1:", float(sum(pass_at_1_results)) / len(pass_at_1_results))
    print(f"Average Pass@{scenario}:", float(sum(pass_at_k_results)) / len(pass_at_k_results))

    return {
        "result_file": result_file,
        "analysis_file": output_file,
        "processed_dir": output_folder,
        "simu_base_dir": simu_base_dir,
        "results_dir": results_dir,
    }

