from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass
class VLMParamSet:
    # Core generation params
    preset: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    do_sample: bool | None = None
    max_new_tokens: int | None = None
    min_new_tokens: int | None = None
    repetition_penalty: float | None = None
    no_repeat_ngram_size: int | None = None
    num_beams: int | None = None
    length_penalty: float | None = None
    diversity_penalty: float | None = None
    early_stopping: bool | None = None

    def to_clean_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


# Common language policy: force Japanese only, forbid Simplified/Traditional Chinese
LANGUAGE_POLICY_SUFFIX = (
    " 日本語のみで回答してください。日本語の漢字と仮名を用い、"
    "簡体字・繁体字の漢字は使用しないでください。必要に応じて英数字は使用可。"
)

# Default mapping from detected type -> parameter set + prompt template
DEFAULT_TYPE_MAP: Dict[str, Dict[str, Any]] = {
    # Tables: emphasize accuracy, longer output allowed, beam search
    "table": {
        "params": VLMParamSet(
            preset="ocr", do_sample=False, num_beams=5,
            length_penalty=1.1, no_repeat_ngram_size=4,
            repetition_penalty=1.05, min_new_tokens=80, max_new_tokens=1600,
            temperature=0.2, top_p=0.6, top_k=10
        ),
        "prompt": (
            "次の画像は表です。内容を1-2文で簡潔に説明してください。"
            "表の列や主要な変数を要約し、具体的な単位や範囲が見える場合は盛り込んでください。"
            "表そのものの再現や改変は行わないでください。"
        ) + LANGUAGE_POLICY_SUFFIX,
    },
    # Analysis charts
    "contour_plot": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=240, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "等高線/等値線図です。軸と値の意味、等値線の高低や重要な領域を1-2文で説明してください。",
    },
    "vector_field_plot": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=240, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "ベクトル場（矢印）を示す図です。向きと大きさの傾向、特徴的な領域を1-2文で説明してください。",
    },
    # Technical diagrams: block/circuit/mechanical/flow/P&ID
    "technical_diagram": {
        "params": VLMParamSet(
            preset="qa", do_sample=False, num_beams=5,
            temperature=0.2, top_p=0.7, top_k=20,
            min_new_tokens=64, max_new_tokens=360,
            no_repeat_ngram_size=4, repetition_penalty=1.06,
        ),
        "prompt": (
            "次の画像は技術的な図（ブロック図/回路図/機械図/配管図など）です。"
            "主要な要素とその関係・信号/流れの向きを1-2文で説明してください。"
            "数値や単位が明確な場合のみ触れ、推測は避けてください。"
        ) + LANGUAGE_POLICY_SUFFIX
    },
    # Plots / charts: axes, variables, trends
    "plot_graph": {
        "params": VLMParamSet(
            preset="qa", do_sample=False, num_beams=4,
            min_new_tokens=64, max_new_tokens=800,
            no_repeat_ngram_size=3, repetition_penalty=1.03,
            temperature=0.3, top_p=0.7, top_k=20
        ),
        "prompt": (
            "次の画像はグラフ/チャートです。軸・変数・傾向を1-2文で説明してください。"
            "目立つピーク・増減・相関があれば指摘してください。"
        ) + LANGUAGE_POLICY_SUFFIX
    },
    # Natural photos / illustrations
    "natural_image": {
        "params": VLMParamSet(
            preset="balanced", do_sample=True,
            temperature=0.7, top_p=0.85, top_k=30,
            min_new_tokens=32, max_new_tokens=256
        ),
        "prompt": (
            "次の画像の内容を1-2文のキャプションとして簡潔に説明してください。"
            "主要な物体、場面の特徴、動作があれば含めてください。"
        ) + LANGUAGE_POLICY_SUFFIX
    },
    # Strict OCR transcription
    "text_ocr": {
        "params": VLMParamSet(
            preset="ocr", do_sample=False, num_beams=5,
            min_new_tokens=100, max_new_tokens=2000,
            no_repeat_ngram_size=4, repetition_penalty=1.05,
        ),
        "prompt": (
            "次の画像から読み取れる文字列を厳密に転記してください。"
            "改行とスペースを可能な限り保持し、説明や補足は記載しないでください。"
            "テキストのみ出力。"
        ) + LANGUAGE_POLICY_SUFFIX
    },
    # Formulas to LaTeX
    "formula": {
        "params": VLMParamSet(
            preset="ocr", do_sample=False, num_beams=6,
            min_new_tokens=80, max_new_tokens=800,
            no_repeat_ngram_size=4, repetition_penalty=1.05,
        ),
        "prompt": (
            "画像内の数式をLaTeXで記述してください。各数式は $ で囲んでください。"
            "複数ある場合は行を分けて列挙し、説明文は不要です。"
        ) + LANGUAGE_POLICY_SUFFIX
    },
    # Handwriting OCR
    "handwriting_note": {
        "params": VLMParamSet(preset="ocr", do_sample=False, num_beams=6, min_new_tokens=100, max_new_tokens=2000, no_repeat_ngram_size=4, repetition_penalty=1.05),
        "prompt": "手書き文字を可能な範囲で厳密に転記してください。読み取れない箇所は[?]で示し、説明は不要。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Specific charts
    "bar_chart": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=48, max_new_tokens=320, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "棒グラフの軸と項目、差が大きいカテゴリを簡潔に述べてください。1-2文で要約。" + LANGUAGE_POLICY_SUFFIX,
    },
    "line_chart": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=48, max_new_tokens=320, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "折れ線グラフの軸と変化の傾向、ピークや増減を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "pie_chart": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=200, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "円グラフの主要な構成比を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "heatmap": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.3, top_p=0.75, top_k=30, min_new_tokens=48, max_new_tokens=256, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "ヒートマップの軸と高/低の集中領域、目立つパターンを簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "network_graph": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.3, top_p=0.75, top_k=30, min_new_tokens=48, max_new_tokens=256, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "ネットワーク図の主要ノードやクラスタ、強い接続を簡潔に述べてください。" + LANGUAGE_POLICY_SUFFIX,
    },
    "timeline": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=240),
        "prompt": "タイムライン上の重要な出来事の順序と要点を1-2文で要約。" + LANGUAGE_POLICY_SUFFIX,
    },
    "infographic": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.4, top_p=0.8, top_k=30, min_new_tokens=48, max_new_tokens=256),
        "prompt": "インフォグラフィックの主題と主要ポイントを簡潔にまとめてください。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Subtypes of technical
    "flowchart": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=48, max_new_tokens=280, repetition_penalty=1.06),
        "prompt": "フローチャートの開始/終了と主要な分岐・処理の流れを1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "circuit_diagram": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, no_repeat_ngram_size=4, repetition_penalty=1.06),
        "prompt": "回路図の主要素（電源/抵抗/コイル/スイッチ等）と接続関係を簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "block_diagram": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, repetition_penalty=1.06),
        "prompt": "ブロック図の主要コンポーネントと信号の入出力関係を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "p_and_id_diagram": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, repetition_penalty=1.06),
        "prompt": "配管計装図の主要機器と流体の流れ/接続関係を簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "thermal_circuit": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, no_repeat_ngram_size=4, repetition_penalty=1.06),
        "prompt": "熱回路の要素（熱源/熱抵抗/容量）と熱流の方向関係を1-2文で説明してください。" + LANGUAGE_POLICY_SUFFIX,
    },
    "fluid_circuit": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, no_repeat_ngram_size=4, repetition_penalty=1.06),
        "prompt": "流体回路（配管）の主要機器/バルブと流れの向き・接続関係を1-2文で説明してください。" + LANGUAGE_POLICY_SUFFIX,
    },
    "floorplan_architecture": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=240),
        "prompt": "建築図/フロアプラン。主な部屋、壁・扉の配置、特徴的な区画を簡潔に説明してください。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Screens / documents
    "code_snippet_screenshot": {
        "params": VLMParamSet(preset="code", do_sample=False, num_beams=4, min_new_tokens=64, max_new_tokens=512, no_repeat_ngram_size=4, repetition_penalty=1.07),
        "prompt": "画像内のコードの目的や言語の手掛かりを1-2文で説明（転記ではなく要約）。" + LANGUAGE_POLICY_SUFFIX,
    },
    "ui_screenshot": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, min_new_tokens=40, max_new_tokens=240),
        "prompt": "UIスクリーンショットの画面種別と主な要素/状態を簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "webpage_screenshot": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, min_new_tokens=48, max_new_tokens=256),
        "prompt": "Webページの種類（記事/一覧/トップ等）と主要要素を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "scanned_document_page": {
        "params": VLMParamSet(preset="ocr", do_sample=False, num_beams=5, min_new_tokens=80, max_new_tokens=1200, no_repeat_ngram_size=4, repetition_penalty=1.05),
        "prompt": "スキャン文書のページ。章題や段組などの構成を簡潔に説明（転記は不要）。" + LANGUAGE_POLICY_SUFFIX,
    },
    "form_document": {
        "params": VLMParamSet(preset="ocr", do_sample=False, num_beams=5, min_new_tokens=80, max_new_tokens=800),
        "prompt": "フォーム/申請書の種別と入力欄の特徴を1-2文で説明（個人情報は生成しない）。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Maps / geo
    "map_geographical": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, min_new_tokens=40, max_new_tokens=240),
        "prompt": "地図または地理図。対象地域や強調されている要素を簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Chemistry
    "chemical_diagram": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=4, temperature=0.25, top_p=0.7, top_k=20, min_new_tokens=40, max_new_tokens=240, no_repeat_ngram_size=3, repetition_penalty=1.03),
        "prompt": "化学反応式/分子構造の図。主要な分子や反応の関係を1-2文で要約してください（推測は避ける）。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Modelica diagrams (annotation/diagram view)
    "modelica_diagram": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=5, temperature=0.2, top_p=0.7, top_k=20, min_new_tokens=64, max_new_tokens=360, no_repeat_ngram_size=4, repetition_penalty=1.06),
        "prompt": (
            "Modelica のダイアグラム/アノテーション図です。"
            "アイコン/コンポーネント名（読み取れる範囲）と接続線の流れや方向、主な入出力を1-2文で説明してください。"
            "内部動作の推測は避け、見える要素だけを簡潔に要約してください。"
        ) + LANGUAGE_POLICY_SUFFIX,
    },
    # Org / mind maps
    "org_mind_map": {
        "params": VLMParamSet(preset="qa", do_sample=False, num_beams=3, temperature=0.3, top_p=0.8, top_k=30, min_new_tokens=40, max_new_tokens=240),
        "prompt": "組織図/マインドマップ。主要ノードの階層関係やグループ化を1-2文で説明してください。" + LANGUAGE_POLICY_SUFFIX,
    },
    # Natural photo subtypes
    "landscape": {
        "params": VLMParamSet(preset="balanced", do_sample=True, temperature=0.6, top_p=0.85, top_k=30, min_new_tokens=32, max_new_tokens=200),
        "prompt": "風景写真の主要な景観要素（山/海/街並みなど）と雰囲気を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "person_portrait": {
        "params": VLMParamSet(preset="balanced", do_sample=True, temperature=0.6, top_p=0.85, top_k=30, min_new_tokens=32, max_new_tokens=200),
        "prompt": "人物写真の特徴（年齢層/姿勢/表情/服装など）を推測しすぎずに簡潔に説明。" + LANGUAGE_POLICY_SUFFIX,
    },
    "animal_wildlife": {
        "params": VLMParamSet(preset="balanced", do_sample=True, temperature=0.6, top_p=0.85, top_k=30, min_new_tokens=32, max_new_tokens=200),
        "prompt": "動物の種類が分かる範囲で、姿勢や環境を1-2文で説明（特定/推測は控えめに）。" + LANGUAGE_POLICY_SUFFIX,
    },
    "object_product": {
        "params": VLMParamSet(preset="balanced", do_sample=True, temperature=0.6, top_p=0.85, top_k=30, min_new_tokens=32, max_new_tokens=200),
        "prompt": "物体/製品の外観や用途の手掛かりを1-2文で説明（ブランド名の推測は避ける）。" + LANGUAGE_POLICY_SUFFIX,
    },
    "vehicle_transport": {
        "params": VLMParamSet(preset="balanced", do_sample=True, temperature=0.6, top_p=0.85, top_k=30, min_new_tokens=32, max_new_tokens=200),
        "prompt": "乗り物の種類（車/列車/船/航空機など）と状況を1-2文で説明。" + LANGUAGE_POLICY_SUFFIX,
    },
}


# Parameters for stage-1 classification (default)
# User-preferred fast/greedy setting
CLASSIFIER_PARAMS = VLMParamSet(
    preset=None,
    temperature=0.0,
    top_p=1.0,
    top_k=20,
    do_sample=False,
    max_new_tokens=96,
    min_new_tokens=16,
    repetition_penalty=1.02,
    no_repeat_ngram_size=3,
    num_beams=1,
    length_penalty=1.0,
    diversity_penalty=0.0,
    early_stopping=False,
)


def build_classifier_prompt(labels: List[str]) -> str:
    labels_txt = ", ".join(labels)
    guidance = (
        "注意: plot_graphは軸や数値のあるグラフ。"
        "technical_diagram/flowchart/circuit_diagram/block_diagram/p_and_id_diagram/modelica_diagramは技術図。"
        "text_ocr/handwriting_noteは厳密な転記対象。"
    )
    return (
        "以下の画像の主な種類を1つ選択して返してください。"
        f"候補: [{labels_txt}].\n"
        f"{guidance}\n"
        "必ず次のJSONのみを出力: {\"type\": <候補のいずれか>, \"confidence\": <0-1>, \"reason\": <短い理由>}\n"
        "reason も日本語のみで記載し、簡体字・繁体字は使用しないでください。"
    )


CLASSIFIER_PROMPT = build_classifier_prompt(list(DEFAULT_TYPE_MAP.keys()))
