import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """環境変数を取得（未設定時は default を返す）。"""
    return os.environ.get(name, default)


@dataclass
class OMCConfig:
    """OpenModelica 関連の設定。

    - use_loadModel: 標準ライブラリを loadModel で読み込むかどうか
    - modelica_stdlib_version: 使用する Modelica 標準ライブラリのバージョン
    - modelica_stdlib_package_template: loadModel を使わない場合の package.mo パスのテンプレート
      例: "C:/OpenModelica/share/omlibrary/Modelica {version}/package.mo"
    - extra_library_paths: 追加のライブラリ検索パス（setModelicaPath 用）
    """
    use_loadModel: bool = True
    modelica_stdlib_version: str = "4.0.0"
    modelica_stdlib_package_template: Optional[str] = None
    extra_library_paths: List[str] = field(default_factory=list)


@dataclass
class LibrariesConfig:
    """依存 Modelica ライブラリの配置と定義ファイル。"""
    libraries_root_dir: str = "library-OM"
    libraries_json: str = "json_files/libraries.json"


@dataclass
class GenerationConfig:
    """生成（RAG/LLM）に関する設定。"""
    enable_rag: bool = True
    docs_dir: str = "GRAG/docs"
    rag_persist_dir: str = "GRAG/storage_Pgraph_modelica_all-4"
    embed_model: str = "local:/xxx/GRAG/BAAI/bge-large-en-v1.5"  # local: 形式やプロバイダ依存表記に対応
    llm_provider: str = "local_hf"  # local_hf | openai | azure_openai
    llm_model: str = "CodeLlama-7b-Instruct-hf"  # API のモデル名またはローカル HF モデル名
    llm_model_path: Optional[str] = None  # local_hf 利用時のローカルパス
    temperature: float = 0.3
    max_new_tokens: int = 800
    num_runs: int = 1
    mode: str = "model"  # or "instance"
    output_dir_template: str = "generation_example/{mode}_result/codellama/output-{model_size}b-Grag"
    model_size_label: str = "7"  # 出力パス上のラベル用途

    # OpenAI/Azure OpenAI 関連
    openai_api_base: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_api_version: Optional[str] = None
    openai_deployment: Optional[str] = None  # Azure OpenAI のデプロイ名
    # APIM 経由の追加ヘッダ（任意）
    apim_subscription_key_header: Optional[str] = None
    apim_subscription_key: Optional[str] = None


@dataclass
class ValidationConfig:
    """検証パイプラインの入出力設定。"""
    input_txt_dir: str = "generation_example/result_instance/starcoder2/7B/output-7b"
    processed_mo_dir: str = "generation_example/result_instance/starcoder2/7B/model-7b"
    simulation_base_dir: str = "generation_example/result_instance/starcoder2/7B/simulation"
    results_base_dir: str = "generation_example/result_instance/starcoder2/7B"
    reference_instance_csv: str = "reference_instance/simulation_durations.csv"


@dataclass
class Config:
    """ModiGen の全体設定。環境変数・JSON で上書き可。"""
    omc: OMCConfig = field(default_factory=OMCConfig)
    libraries: LibrariesConfig = field(default_factory=LibrariesConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)


def _merge_env(cfg: Config) -> None:
    """環境変数で設定を上書き（必要な項目のみ）。"""
    # OMC
    if _env("MODIGEN_USE_LOADMODEL") is not None:
        cfg.omc.use_loadModel = _env("MODIGEN_USE_LOADMODEL").lower() in ("1", "true", "yes")
    cfg.omc.modelica_stdlib_version = _env("MODIGEN_MODELICA_VERSION", cfg.omc.modelica_stdlib_version)
    cfg.omc.modelica_stdlib_package_template = _env(
        "MODIGEN_MODELICA_STDLIB_TEMPLATE", cfg.omc.modelica_stdlib_package_template
    )
    extra_paths = _env("MODIGEN_EXTRA_LIBRARY_PATHS")
    if extra_paths:
        cfg.omc.extra_library_paths = [p for p in extra_paths.split(os.pathsep) if p]

    # Libraries
    cfg.libraries.libraries_root_dir = _env(
        "MODIGEN_LIBRARIES_ROOT", cfg.libraries.libraries_root_dir
    )
    cfg.libraries.libraries_json = _env(
        "MODIGEN_LIBRARIES_JSON", cfg.libraries.libraries_json
    )

    # Generation
    if _env("MODIGEN_ENABLE_RAG") is not None:
        cfg.generation.enable_rag = _env("MODIGEN_ENABLE_RAG").lower() in ("1", "true", "yes")
    cfg.generation.docs_dir = _env("MODIGEN_DOCS_DIR", cfg.generation.docs_dir)
    cfg.generation.rag_persist_dir = _env("MODIGEN_RAG_PERSIST_DIR", cfg.generation.rag_persist_dir)
    cfg.generation.embed_model = _env("MODIGEN_EMBED_MODEL", cfg.generation.embed_model)
    cfg.generation.llm_provider = _env("MODIGEN_LLM_PROVIDER", cfg.generation.llm_provider)
    cfg.generation.llm_model = _env("MODIGEN_LLM_MODEL", cfg.generation.llm_model)
    cfg.generation.llm_model_path = _env("MODIGEN_LLM_MODEL_PATH", cfg.generation.llm_model_path)
    cfg.generation.mode = _env("MODIGEN_MODE", cfg.generation.mode)
    cfg.generation.model_size_label = _env("MODIGEN_MODEL_SIZE_LABEL", cfg.generation.model_size_label)
    if _env("MODIGEN_TEMPERATURE") is not None:
        try:
            cfg.generation.temperature = float(_env("MODIGEN_TEMPERATURE"))
        except Exception:
            pass
    if _env("MODIGEN_MAX_NEW_TOKENS") is not None:
        try:
            cfg.generation.max_new_tokens = int(_env("MODIGEN_MAX_NEW_TOKENS"))
        except Exception:
            pass
    if _env("MODIGEN_NUM_RUNS") is not None:
        try:
            cfg.generation.num_runs = int(_env("MODIGEN_NUM_RUNS"))
        except Exception:
            pass

    # OpenAI/Azure
    cfg.generation.openai_api_base = _env("OPENAI_API_BASE", cfg.generation.openai_api_base)
    cfg.generation.openai_api_key = _env("OPENAI_API_KEY", cfg.generation.openai_api_key)
    cfg.generation.openai_api_version = _env("OPENAI_API_VERSION", cfg.generation.openai_api_version)
    cfg.generation.openai_deployment = _env("OPENAI_DEPLOYMENT", cfg.generation.openai_deployment)
    cfg.generation.apim_subscription_key_header = _env(
        "APIM_SUBSCRIPTION_KEY_HEADER", cfg.generation.apim_subscription_key_header
    )
    cfg.generation.apim_subscription_key = _env(
        "APIM_SUBSCRIPTION_KEY", cfg.generation.apim_subscription_key
    )

    # Validation
    cfg.validation.input_txt_dir = _env("MODIGEN_INPUT_TXT_DIR", cfg.validation.input_txt_dir)
    cfg.validation.processed_mo_dir = _env("MODIGEN_PROCESSED_MO_DIR", cfg.validation.processed_mo_dir)
    cfg.validation.simulation_base_dir = _env("MODIGEN_SIMU_BASE_DIR", cfg.validation.simulation_base_dir)
    cfg.validation.results_base_dir = _env("MODIGEN_RESULTS_BASE_DIR", cfg.validation.results_base_dir)
    cfg.validation.reference_instance_csv = _env(
        "MODIGEN_REFERENCE_INSTANCE_CSV", cfg.validation.reference_instance_csv
    )


def load_config(config_path: Optional[str] = None) -> Config:
    """設定をロードして返す。config_path > 環境変数 MODIGEN_CONFIG > デフォルト。"""
    cfg = Config()
    # JSON ファイルでの上書き（簡易実装）
    path = config_path or _env("MODIGEN_CONFIG")
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Very light manual merge
        for section in ("omc", "libraries", "generation", "validation"):
            if section in data and isinstance(data[section], dict):
                sect_obj = getattr(cfg, section)
                for k, v in data[section].items():
                    if hasattr(sect_obj, k):
                        setattr(sect_obj, k, v)

    _merge_env(cfg)
    return cfg


def resolve_output_dir(cfg: Config) -> str:
    """生成結果の出力ディレクトリを設定テンプレートから解決。"""
    return cfg.generation.output_dir_template.format(
        mode=cfg.generation.mode,
        model_size=cfg.generation.model_size_label,
        model_size_label=cfg.generation.model_size_label,
    )
