from __future__ import annotations

from typing import List


def build_opt_prompt(user_query: str, focus: str, n: int = 1) -> str:
    """最適化プロンプトを作成（focusは常にgeneralに固定）"""
    # focus は検索対象に依存させず、常に general の規則で生成する
    _ = focus  # 入力focusは無視
    few_shot = (
        "Examples (input → 3 optimized queries):\n"
        "Input: water tank temperature control\n"
        "tank temperature control PID setpoint actuator sensor\n"
        "energy balance tank dT/dt Q_in Q_out Cp rho\n"
        "tuning procedure anti-windup hysteresis filtering\n\n"
        "Input: handle rate limiting in REST API\n"
        "HTTP 429 retry backoff exponential jitter\n"
        "rate limit headers X-RateLimit token bucket window\n"
        "idempotency key timeout circuit breaker\n\n"
    )
    focus_hint = "general keyword search for RAG (code/text/math)"
    return (
        f"You are a query optimizer for vector-based RAG.\n"
        f"Goal: Produce concise, high-signal keyword queries (<= 12 words).\n"
        f"Focus: {focus_hint}.\n"
        f"Rules: no code/SQL/JSON/quotes/bullets; one plain line per query.\n"
        f"Queries must be distinct and include at least one technical token.\n\n"
        f"{few_shot}"
        f"Input: {user_query}\n"
        f"Output: exactly {n} lines.\n"
    )


def heuristic_optimize_one(user_query: str, focus: str) -> str:
    """簡易ルール（focusは常にgeneralとして扱う）"""
    base = (user_query or "").replace("/", " ").replace(",", " ")
    words = [w for w in base.split() if len(w) > 1]
    core = " ".join(words[:8]) or base.strip()
    # general 向けの短い技術語セット（式/単位/識別子の軽い混入）
    tail = "keywords identifiers units operators"
    return f"{core} {tail}".strip()


def generate_query_with_vlm_strict(user_query: str, focus: str, preset: str) -> str:
    try:
        from vlm.model_manager import ModelManager
    except Exception as e:
        raise RuntimeError("VLMモデルが利用できません") from e

    # focus は常に general 固定
    prompt = build_opt_prompt(user_query, "general", 1)
    mm = ModelManager()
    if not mm.setup_model():
        raise RuntimeError("VLMモデルのセットアップに失敗しました")
    try:
        text = mm.generate_response(
            prompt,
            preset=preset,
            do_sample=False,
            num_beams=1,
            min_new_tokens=8,
            max_new_tokens=48,
            early_stopping=True,
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
    """外部API: focusは無視し、常にgeneral規則で生成/最適化する。"""
    if use_vlm:
        return generate_query_with_vlm_strict(user_query, "general", preset)
    return heuristic_optimize_one(user_query, "general")
