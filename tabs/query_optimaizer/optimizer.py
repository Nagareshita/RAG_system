from __future__ import annotations

from typing import List


def build_opt_prompt(user_query: str, focus: str, n: int = 1) -> str:
    """最適化プロンプトを作成（短文・長文両対応、AST/PDF両対応）"""
    
    # focusに応じたヒント
    if focus in ["packages", "functions", "equations"]:
        focus_hint = "Modelica/code search (functions, equations, packages, identifiers)"
        domain_terms = "function names, package names, equation keywords, physical quantities, units, parameters"
    else:  # pdf or general
        focus_hint = "technical documentation search (PDF, specifications, manuals)"
        domain_terms = "technical terms, component names, physical phenomena, numerical values, units, concepts"
    
    few_shot = (
        "Examples (adapt output length to input complexity):\n\n"
        
        "# Short/vague input → expand with relevant keywords\n"
        "Input: 冷蔵庫のモデル\n"
        "Output: 冷蔵庫 refrigerator 冷却 cooling 温度制御 temperature control "
        "熱交換器 heat exchanger 圧縮機 compressor エネルギー消費 energy consumption "
        "断熱 insulation 冷媒 refrigerant\n\n"
        
        "Input: water tank model\n"
        "Output: water tank model thermal dynamics heat transfer temperature control "
        "liquid level volume flow rate inlet outlet energy balance dT/dt Q_in Q_out "
        "Cp rho fluid dynamics storage\n\n"
        
        "# Detailed/long input → extract and structure key information\n"
        "Input: （FSI）に詳しいModelica専門エンジニアです。配管振動モデル（Pipe Vibration Model）を作成。"
        "鋼管：長さ2m、内径30mm、外径34mm。片持ち支持。内部流体：20°Cの水、平均流速2m/s。"
        "配管の構造振動、内部流体の圧力・運動による壁面への励起、材料減衰および流体抵抗。"
        "固有振動数とモード形状、時間応答、応力分布を出力。\n"
        "Output: pipe vibration model FSI fluid-structure interaction steel pipe "
        "2m length 30mm inner 34mm outer diameter cantilever support water 20°C 2m/s flow "
        "structural dynamics beam vibration Euler-Bernoulli Timoshenko pressure excitation "
        "wall coupling material damping fluid resistance natural frequency mode shape "
        "time response stress distribution modal analysis\n\n"
        
        "Input: REST APIでrate limitingを実装。429エラー、リトライロジック、exponential backoff、"
        "jitter追加、X-RateLimitヘッダー、token bucket方式。\n"
        "Output: REST API rate limiting HTTP 429 error retry logic exponential backoff "
        "jitter X-RateLimit headers token bucket algorithm sliding window "
        "idempotency circuit breaker timeout queue throttling\n\n"
    )
    
    return (
        f"You are a query optimizer for RAG search (code/AST and technical documents).\n\n"
        f"Goal: Optimize queries for vector search in technical database.\n"
        f"Focus: {focus_hint}\n\n"
        f"Strategy:\n"
        f"- Short/vague query (< 20 words): EXPAND with {domain_terms} (output: 15-30 words)\n"
        f"- Long/detailed query (≥ 20 words): EXTRACT key {domain_terms}, add related terms (output: 25-60 words)\n"
        f"- Keep: numbers, units, symbols, identifiers, technical terms\n"
        f"- Add: synonyms, related concepts, domain-specific keywords\n"
        f"- Remove: conversational phrases, politeness, meta-commentary\n\n"
        f"Output format: single line, plain text, no quotes/bullets/code blocks\n\n"
        f"{few_shot}"
        f"Input: {user_query}\n\n"
        f"Output:\n"
    )


def heuristic_optimize_one(user_query: str, focus: str) -> str:
    """簡易ルール（短文は拡張、長文は要約+キーワード追加）"""
    base = (user_query or "").replace("/", " ").replace(",", " ")
    words = [w for w in base.split() if len(w) > 1]
    
    if len(words) < 20:
        # 短文: キーワード拡張
        core = " ".join(words)
        if focus in ["packages", "functions", "equations"]:
            tail = "model function equation parameter variable component system"
        else:
            tail = "technical specification component system process method"
        return f"{core} {tail}".strip()
    else:
        # 長文: 重要語句抽出（先頭50%程度）
        core = " ".join(words[:max(15, len(words)//2)])
        return core.strip()


def generate_query_with_vlm_strict(user_query: str, focus: str, preset: str) -> str:
    try:
        from vlm.model_manager import ModelManager
    except Exception as e:
        raise RuntimeError("VLMモデルが利用できません") from e

    # focusをそのまま使用（AST/PDF対応）
    prompt = build_opt_prompt(user_query, focus, 1)
    
    mm = ModelManager()
    if not mm.setup_model():
        raise RuntimeError("VLMモデルのセットアップに失敗しました")
    try:
        # トークン制限を緩和: 256トークン（約180-200単語相当）
        # プリセットの設定を活かしつつ、max_new_tokensのみ調整
        text = mm.generate_response(
            prompt,
            preset=preset,
            max_new_tokens=256,  # 48→256に拡大
            min_new_tokens=10,   # 最低限のキーワードは必須
        )
    finally:
        try:
            mm.cleanup_model()
        except Exception:
            pass
    
    # 出力を行単位で評価し、最初に妥当な候補を返す（1件）
    lines = [ln.strip(" -\t") for ln in (text or "").splitlines() if ln.strip()]
    
    # SQL/コード風のみを弾き、記号は許容（自然文を落とさない）
    bad_tokens = ["select ", " from ", " where ", "{", "}"]
    for ln in lines:
        low = ln.lower()
        if any(bt in low for bt in bad_tokens):
            continue
        if len(ln.split()) < 2:
            continue
        return ln
    
    raise RuntimeError("VLMから有効な最適化クエリが得られませんでした")


def optimize_query(user_query: str, focus: str = "functions", preset: str = "qa", use_vlm: bool = False) -> str:
    """
    外部API: クエリを検索用に最適化
    
    Args:
        user_query: ユーザーの入力クエリ
        focus: 検索対象 ("packages", "functions", "equations", "pdf", "general")
        preset: VLMプリセット ("qa", "accurate", "balanced", etc.)
        use_vlm: VLMを使用するか（Falseの場合はヒューリスティック）
    
    Returns:
        最適化されたクエリ
    """
    if use_vlm:
        return generate_query_with_vlm_strict(user_query, focus, preset)
    return heuristic_optimize_one(user_query, focus)
