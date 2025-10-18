"""
クエリ最適化テストプログラム

目的:
- ユーザークエリをVLM（SAIL-VL2-2B/Qwen3系）で最適化して、情報量の高い検索クエリ候補を生成する
- 生成したクエリ候補でベクトル検索（横断/再ランク対応）を実行する
- VLMが利用できない場合はヒューリスティック（簡易規則）で安全にフォールバックする

使用例:

  python scripts/query_optimize_test.py \
      --query "water tank temperature control" \
      --collections rag_documents_ast_packages rag_documents_ast_functions rag_documents_pdf \
      --topk 50 --finalk 20 --threshold 0.0 \
      --reranker "BAAI/bge-reranker-large" \
      --opt-preset qa --opt-candidates 3 --gpu

注意:
- Qdrant はローカルDB（vector_db）または環境変数 QDRANT_URL でHTTP接続が必要
- VLMはモデルサイズが大きいため、利用できない環境では自動でヒューリスティック最適化に切替
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Dict, Tuple, Any
from pathlib import Path

# リポジトリルートを import パスに追加（scripts/ から utils/ を見えるように）
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.vector_manager import VectorManager


def build_opt_prompt(user_query: str, focus: str, n: int = 3) -> str:
    """VLMに与える最適化プロンプトを作成（英語で簡潔に指示）
    重要: SQL/コード/JSONは出さない。厳密に n 行のキーワードクエリのみを返す。
    """
    focus_hint = {
        "functions": "AST functions (signatures, purpose, I/O, keywords)",
        "equations": "AST equations/algorithms (operators, identifiers, units)",
        "packages": "AST packages/namespaces (names, exports, brief)",
        "pdf": "PDF chunks (title, section, keyword anchors)",
    }.get(focus, "general RAG search")

    # 多領域のFew-shot（数学/ソフトウェア/API/生物/物理など）
    few_shot = (
        "Examples (input → 3 optimized queries):\n"
        # 数学（線形代数）
        "Input: fast matrix multiplication\n"
        "matrix multiplication algorithm Strassen complexity O(n^log2 7) cache blocking\n"
        "tensor contraction BLAS GEMM tiling vectorization\n"
        "numerical stability rounding error conditioning\n\n"
        # ソフトウェアAPI
        "Input: handle rate limiting in REST API\n"
        "HTTP 429 retry backoff exponential jitter client pagination\n"
        "rate limit headers X-RateLimit window token bucket leaky bucket\n"
        "idempotency key safety timeout circuit breaker\n\n"
        # 生物（光合成）
        "Input: improve photosynthesis efficiency\n"
        "photosynthesis electron transport chain chlorophyll reaction center\n"
        "Calvin cycle RuBisCO carboxylation stomata CO2 diffusion\n"
        "light intensity absorption spectrum quantum yield\n\n"
        # 物理（熱）
        "Input: refrigerator thermal model\n"
        "vapor compression cycle compressor evaporator condenser COP refrigerant\n"
        "energy balance dT/dt enthalpy mass flow Q_in Q_out Cp rho\n"
        "temperature control PID setpoint hysteresis anti-windup sensor\n\n"
    )
    return (
        f"You are a query optimizer for vector-based RAG (code/math domain).\n"
        f"Goal: Produce concise, high-signal keyword queries (8-20 words) for semantic search.\n"
        f"Focus: {focus_hint}.\n"
        f"Rules:\n"
        f"- Use English keywords plus domain identifiers (functions, units, operators).\n"
        f"- DO NOT output code, SQL, JSON, quotes, numbering, bullets, or explanations.\n"
        f"- Output plain queries only, one per line, with spaces only.\n"
        f"- Queries must be distinct in angle (purpose, mechanisms, equations, components, specs).\n"
        f"- Include at least one technical token (e.g., acronym, unit, operator, identifier).\n\n"
        f"{few_shot}"
        f"Input: {user_query}\n"
        f"Output: exactly {n} lines.\n"
    )

def _load_lexicons() -> List[Dict[str, Any]]:
    """外部レキシコン（scripts/lexicons/*.json）があれば読み込む（任意・汎用化のため）。"""
    import json, glob, os
    base = os.path.join(os.path.dirname(__file__), "lexicons")
    files = glob.glob(os.path.join(base, "*.json"))
    packs: List[Dict[str, Any]] = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                packs.append(json.load(fp))
        except Exception:
            continue
    return packs


def _extract_generic_terms(user_query: str) -> List[str]:
    """ドメイン非依存の技術語抽出（簡易）。大文字略語、コード識別子、数値+単位など。"""
    import re
    uq = user_query or ""
    terms: List[str] = []
    # 大文字略語
    terms += re.findall(r"\b[A-Z]{2,}\b", uq)
    # コード/識別子風（snake/camel/数字混在）
    terms += re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", uq)
    # 数値+単位
    terms += re.findall(r"\b\d+(?:\.\d+)?\s?(?:k?m|cm|mm|kg|g|s|ms|Hz|kHz|MHz|GHz|Pa|kPa|MPa|bar|°C|C|K|m/s|N|J|W|kW|MW)\b", uq)
    # 先頭大文字語（簡易な固有表現）
    terms += re.findall(r"\b[A-Z][a-z]{3,}\b", uq)
    # クリーニング
    stop = {"the","and","for","with","this","that","what","when","where","make","create","design","model"}
    cleaned = []
    seen = set()
    for t in terms:
        tl = t.lower()
        if tl in stop:
            continue
        if tl not in seen:
            seen.add(tl)
            cleaned.append(t)
    return cleaned[:12]


def _detect_domain_terms(user_query: str, focus: str) -> List[str]:
    """レキシコン（任意）と汎用抽出で技術語を集約。"""
    import re
    uq = user_query or ""
    added: List[str] = []
    # 外部レキシコン（任意）
    for pack in _load_lexicons():
        try:
            pattern = pack.get("pattern")
            if pattern and re.search(pattern, uq, flags=re.IGNORECASE):
                added.extend(pack.get("common", []))
                added.extend(pack.get(focus, []))
        except Exception:
            continue
    # 汎用抽出
    added.extend(_extract_generic_terms(uq))
    # 重複除去
    seen = set()
    uniq: List[str] = []
    for t in added:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq[:12]


def _enrich_queries_with_domain(queries: List[str], user_query: str, focus: str) -> List[str]:
    extras = _detect_domain_terms(user_query, focus)
    if not extras:
        return queries
    enriched: List[str] = []
    for i, q in enumerate(queries):
        take = extras[i % len(extras)] if extras else ""
        if take and take.lower() not in q.lower():
            enriched.append(f"{q} {take}")
        else:
            enriched.append(q)
    return enriched


def heuristic_optimize(user_query: str, focus: str, n: int = 3) -> List[str]:
    """VLMが使えないときの簡易クエリ最適化（英語キーワード寄せ＋用途語追加）"""
    base = user_query.strip()
    words = [w for w in base.replace("/", " ").replace(",", " ").split() if len(w) > 1]
    core = " ".join(words[:12])
    domain = _detect_domain_terms(user_query, focus)
    if focus == "functions":
        extras = [
            "function signature",
            "PID control setpoint",
            "parameters inputs outputs",
        ]
    elif focus == "equations":
        extras = [
            "equation dT/dt energy balance",
            "Cp rho heat transfer",
            "derivative differential",
        ]
    elif focus == "packages":
        extras = ["package namespace exports", "module library", "overview"]
    else:  # pdf
        extras = ["system overview", "algorithm section", "tuning procedure"]
    # ドメイン/汎用語彙を混ぜる
    extras = (domain[:3] if domain else []) + extras
    out = []
    for i in range(min(n, len(extras))):
        out.append(f"{core} {extras[i]}")
    while len(out) < n:
        out.append(core)
    return _enrich_queries_with_domain(out, user_query, focus)


def generate_queries_with_vlm(user_query: str, focus: str, preset: str, candidates: int) -> List[str]:
    """VLMでクエリ最適化（失敗時はヒューリスティックにフォールバック）"""
    try:
        from vlm.model_manager import ModelManager
    except Exception:
        return heuristic_optimize(user_query, focus, candidates)

    mm = ModelManager()
    ok = mm.setup_model(progress_callback=lambda m: print(f"[VLM] {m}"))  # 進捗を標準出力に表示
    if not ok:
        print("[VLM] セットアップ失敗のため、ヒューリスティック最適化に切替えます。")
        return heuristic_optimize(user_query, focus, candidates)

    prompt = build_opt_prompt(user_query, focus, candidates)
    try:
        text = mm.generate_response(prompt, preset=preset)
    except Exception as e:
        print(f"[VLM] 生成エラー: {e} → ヒューリスティック最適化に切替えます。")
        return heuristic_optimize(user_query, focus, candidates)
    finally:
        try:
            mm.cleanup_model()
        except Exception:
            pass

    lines = [ln.strip(" -\t") for ln in text.splitlines() if ln.strip()]
    # 余分な記号や先頭番号の除去、クエリらしくない行の排除
    cleaned: List[str] = []
    for ln in lines:
        if any(bad in ln.lower() for bad in ["select ", " from ", " where ", "{", "}", ":", ";"]):
            continue
        cleaned.append(ln)
    # 近似重複（同一2-gram）の除去
    def bigrams(s: str) -> set:
        toks = s.lower().split()
        return set(zip(toks, toks[1:]))
    uniq: List[str] = []
    seen_bg: List[set] = []
    for q in cleaned:
        b = bigrams(q)
        if any(len(b & sb) >= max(1, int(0.5*len(b))) for sb in seen_bg if b):
            continue
        uniq.append(q)
        seen_bg.append(b)
        if len(uniq) >= candidates:
            break
    # 足りない場合はヒューリスティックで補完
    if len(uniq) < candidates:
        extra = heuristic_optimize(user_query, focus, candidates - len(uniq))
        uniq.extend(extra)
    # ドメイン/汎用語彙で強化
    uniq = _enrich_queries_with_domain(uniq, user_query, focus)
    return uniq


def run_search(queries: List[str], collections: List[str], topk: int, finalk: int, threshold: float, reranker_model: str, use_gpu: bool) -> None:
    """最適化クエリ（複数）で横断検索→（任意）再ランク→結果表示"""
    vm = VectorManager()
    vm.use_gpu = use_gpu
    if not vm.initialize_model(use_gpu):
        print("[Search] 埋め込みモデル初期化に失敗しました。")
        return
    if reranker_model:
        ok = vm.initialize_reranker(reranker_model)
        if not ok:
            print("[Search] 再ランカ初期化に失敗。再ランク無しで継続します。")

    print(f"[Search] 対象コレクション: {collections}")
    for q in queries:
        print(f"\n[Query] {q}")
        results = vm.search_across_collections(
            query=q,
            collections=collections,
            initial_k=topk,
            final_k=finalk,
            similarity_threshold=threshold,
            use_reranker=True if vm.reranker_model else False,
            use_hybrid=False,
            dense_weight=1.0,
            sparse_weight=0.0,
        )
        for i, r in enumerate(results, 1):
            col = r.get("collection", "")
            score = r.get("score", 0.0)
            text = (r.get("text") or "")
            preview = (text[:160] + "…") if len(text) > 160 else text
            print(f"  {i:02d}. [{col}] {score:.3f}  {preview}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="クエリ最適化テスト（VLM/ヒューリスティック → 検索実行）")
    p.add_argument("--query", required=True, help="ユーザークエリ")
    p.add_argument("--focus", choices=["functions", "equations", "packages", "pdf"], default="functions", help="主に探したい対象")
    p.add_argument("--collections", nargs="+", default=["rag_documents_ast_functions"], help="検索対象コレクション（スペース区切り）")
    p.add_argument("--topk", type=int, default=50, help="Dense検索の候補数")
    p.add_argument("--finalk", type=int, default=20, help="最終的に返す件数（再ランク後）")
    p.add_argument("--threshold", type=float, default=0.0, help="Denseスコアの下限（0.0はフィルタ無し）")
    p.add_argument("--reranker", default="BAAI/bge-reranker-large", help="再ランクモデル（空なら再ランク無し）")
    p.add_argument("--gpu", action="store_true", help="GPUを使用する")
    # VLM オプション
    p.add_argument("--opt-preset", default="qa", help="VLMプリセット（qa/code/ocr/balanced/accurate など）")
    p.add_argument("--opt-candidates", type=int, default=3, help="生成する最適化クエリ候補数")
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    # Step1: Optimize queries
    queries = generate_queries_with_vlm(args.query, args.focus, args.opt_preset, args.opt_candidates)
    print("[Optimized Queries]")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    # Step2: Run searches
    run_search(queries, args.collections, args.topk, args.finalk, args.threshold, args.reranker, args.gpu)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
