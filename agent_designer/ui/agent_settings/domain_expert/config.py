# agent_designer/ui/agent_settings/domain_expert/config.py
"""
Domain Expert設定の完全統合（デフォルト値完全版）

このモジュールは、Domain Expertエージェントの全設定を一元管理します。
UI表示情報、デフォルト設定値、プロンプトテンプレートを含みます。
"""


class DomainExpertConfig:
    @classmethod
    def get_reference_values(cls):
        """固定参照値（編集不可）を返却"""
        return {
            'max_boost_over_retriever': cls.DEFAULT_VALUES['max_boost_over_retriever'],
            'max_expert_confidence': cls.DEFAULT_VALUES['max_expert_confidence'],
            'min_facts_for_bonus': cls.DEFAULT_VALUES['min_facts_for_bonus'],
            'facts_bonus': cls.DEFAULT_VALUES['facts_bonus'],
            'citation_rate_threshold': cls.DEFAULT_VALUES['citation_rate_threshold'],
            'citation_bonus': cls.DEFAULT_VALUES['citation_bonus'],
            'min_recommendations_for_bonus': cls.DEFAULT_VALUES['min_recommendations_for_bonus'],
            'recommendations_bonus': cls.DEFAULT_VALUES['recommendations_bonus']
        }
    @classmethod
    def validate_config(cls, config: dict):
        """設定の妥当性を検証（グローバル関数をラップ）"""
        return validate_config(config)
    @classmethod
    def get_settings_schema(cls):
        """設定項目のスキーマを返却"""
        return cls.get_ui_fields()
    @classmethod
    def get_ui_info(cls):
        """UI表示用の情報を返却"""
        return cls.UI_INFO
    @classmethod
    def get_default_config(cls):
        """DomainExpertノードのデフォルト設定を返す"""
        return cls.DEFAULT_VALUES
    """Domain Expert設定の統合管理クラス"""
    
    # ==================== UI表示情報 ====================
    UI_INFO = {
        'name': 'Domain Expert',
        'description': 'Modelica専門分析エージェント',
        'color': {
            'fill': (180, 120, 180, 200),
            'border': (220, 160, 220),
            'text': (255, 255, 255)
        }
    }
    
    # ==================== デフォルト設定値（完全版） ====================
    DEFAULT_VALUES = {
        # ---------- 基本設定 ----------
        'expertise_domain': 'Modelicaライブラリ',
        'log_level': 'VERBOSE',
        
        # ---------- 専門家プロファイル ----------
        'expert_profile': {
            'specialization': '標準ライブラリ・カスタムライブラリ・コンポーネント設計・パッケージ構造',
            'knowledge_areas': [
                "MSL",
                "Buildings",
                "PowerSystems",
                "Fluid",
                "Thermal",
                "Electrical",
                "Mechanics"
            ],
            'analysis_focus': 'ライブラリ活用・コンポーネント選択・モデル構築・パラメータ設定'
        },
        
        # ---------- コンテキスト管理 ----------
        'max_context_chars': 12000,
        
        # ========== Phase 3 追加: 出力品質制御 ==========
        'min_facts_count': 3,        # 最小事実数（品質保証）
        'min_insights_count': 2,     # 最小洞察数（品質保証）
        # ==============================================
        
        # ---------- 信頼度計算パラメータ（固定参照値・編集不可） ----------
        'max_boost_over_retriever': 0.25,  # Retriever信頼度からの最大上昇幅
        'max_expert_confidence': 0.92,     # 専門家信頼度の上限
        
        # ボーナス設定
        'min_facts_for_bonus': 7,          # ボーナス適用の最小事実数
        'facts_bonus': 0.08,               # 事実数ボーナス
        'citation_rate_threshold': 0.7,    # 引用率閾値
        'citation_bonus': 0.08,            # 引用整合性ボーナス
        'min_recommendations_for_bonus': 6,  # ボーナス適用の最小推奨数
        'recommendations_bonus': 0.08,     # 推奨事項ボーナス
        
        # ---------- LLMプロンプト設定 ----------
        'llm_prompts': {
            'expert_identity': (
                'あなたは{expertise_domain}の専門家です。'
                '{specialization}を専門とし、{knowledge_areas}の知識領域で'
                '{analysis_focus}に焦点を当てた分析を行います。'
            ),
            'analysis_instruction': (
                'AST構造データとPDF文献の両方の検索結果を基に、'
                '専門的観点から構造化された分析を実施してください。'
                '実装可能性と技術的正確性を最重視し、'
                '前回の実行結果があれば品質向上に活用してください。'
            ),
            'output_format': (
                'JSON形式で answer(600字以内), facts(10件以内), '
                'insights(10件以内), recommendations(10件以内), '
                'gaps(10件以内), citations, confidence を必須出力してください。'
            ),
            'confidence_guidance': (
                '前段階の検索品質を基準とし、'
                '最大{max_boost_over_retriever}の上乗せで信頼度を設定してください。'
                '前回の結果がある場合は改善度も考慮してください。'
            ),
            'quality_focus': (
                '事実の正確性、引用の整合性、推奨事項の実装可能性、'
                '技術洞察の深度、AST・PDF情報の統合品質、'
                '前回指摘事項の改善を最重視してください。'
            ),
            'content_constraints': (
                '文字数制限: answer<=600字、facts<=10件、insights<=10件、'
                'recommendations<=10件、gaps<=10件を厳守してください。'
            )
        },
        
        # ---------- プロンプトテンプレート ----------
        'final_prompt_template': (
            '{expert_identity}\n\n'
            '{analysis_instruction}\n\n'
            '質問: "{query}"\n\n'
            '検索結果:\n{search_context}\n\n'
            '【信頼度指針】\n{confidence_guidance}\n\n'
            '【品質重点】\n{quality_focus}\n\n'
            '【制約事項】\n{content_constraints}\n\n'
            '【引用整合性重要】\n'
            'facts の cite_ids には必ず検索結果の [引用ID: chunk:xxx:123] の形式で記載してください。\n'
            'citations には検索結果に実際に存在する chunk_id のみを記載してください。\n\n'
            '{output_format}:\n'
            '{{\n'
            '  "answer": "簡潔な回答（≤600字）",\n'
            '  "facts": [\n'
            '    {{"statement": "主要な事実", "cite_ids": ["chunk:ast:123"]}}\n'
            '  ],\n'
            '  "insights": ["重要な洞察や因果関係"],\n'
            '  "recommendations": ["具体的な推奨事項"],\n'
            '  "gaps": ["不足している情報"],\n'
            '  "citations": ["chunk:ast:123"],\n'
            '  "confidence": 0.85\n'
            '}}'
        )
    }
    
    # ==================== UI設定フィールド定義 ====================
    @staticmethod
    def get_ui_fields():
        """
        GUI設定パネルで編集可能なフィールドを定義
        
        Returns:
            編集可能フィールドの定義リスト
        """
        return [
            # ===== 1. 基本設定 =====
            {
                'key': 'expertise_domain',
                'label': '専門分野',
                'type': 'text',
                'default': DomainExpertConfig.DEFAULT_VALUES['expertise_domain'],
                'description': '専門家の領域（例: Modelicaライブラリ）'
            },
            {
                'key': 'log_level',
                'label': 'ログ出力レベル',
                'type': 'combo',
                'options': [
                    ('VERBOSE', 'VERBOSE'),
                    ('MINIMAL', 'MINIMAL')
                ],
                'default': DomainExpertConfig.DEFAULT_VALUES['log_level'],
                'description': 'ログの詳細度'
            },
            {
                'key': 'max_context_chars',
                'label': '最大コンテキスト文字数',
                'type': 'int',
                'default': DomainExpertConfig.DEFAULT_VALUES['max_context_chars'],
                'min': 5000,
                'max': 20000,
                'description': 'LLMに送信する検索結果の最大文字数'
            },
            
            # ===== 2. 専門家プロファイル =====
            {
                'key': 'specialization',
                'label': '専門領域',
                'type': 'text',
                'default': DomainExpertConfig.DEFAULT_VALUES['expert_profile']['specialization'],
                'description': '専門とする技術領域'
            },
            {
                'key': 'knowledge_areas',
                'label': '知識領域',
                'type': 'text',
                'default': ', '.join(DomainExpertConfig.DEFAULT_VALUES['expert_profile']['knowledge_areas']),
                'description': '対応する知識分野（カンマ区切り）'
            },
            {
                'key': 'analysis_focus',
                'label': '分析焦点',
                'type': 'text',
                'default': DomainExpertConfig.DEFAULT_VALUES['expert_profile']['analysis_focus'],
                'description': '分析時の重点項目'
            },
            
            # ===== 3. LLMプロンプト設定 =====
            {
                'key': 'expert_identity',
                'label': '専門家アイデンティティ',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['expert_identity'],
                'description': '専門家としての自己紹介'
            },
            {
                'key': 'analysis_instruction',
                'label': '分析指示',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['analysis_instruction'],
                'description': '分析方法の指示'
            },
            {
                'key': 'output_format',
                'label': '出力フォーマット指示',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['output_format'],
                'description': '出力形式の指定'
            },
            {
                'key': 'confidence_guidance',
                'label': '信頼度指針',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['confidence_guidance'],
                'description': '信頼度設定の指針'
            },
            {
                'key': 'quality_focus',
                'label': '品質重点項目',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['quality_focus'],
                'description': '品質確保の重点事項'
            },
            {
                'key': 'content_constraints',
                'label': 'コンテンツ制約',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['llm_prompts']['content_constraints'],
                'description': 'コンテンツ制約事項'
            },
            
            # ===== 4. 最終プロンプトテンプレート =====
            {
                'key': 'final_prompt_template',
                'label': '最終プロンプトテンプレート',
                'type': 'textarea',
                'default': DomainExpertConfig.DEFAULT_VALUES['final_prompt_template'],
                'description': '最終的なプロンプトテンプレート'
            },
            
            # ===== 品質保証設定 =====
            {
                'key': 'min_facts_count',
                'label': '最小事実数',
                'type': 'int',
                'default': DomainExpertConfig.DEFAULT_VALUES['min_facts_count'],
                'min': 1,
                'max': 10,
                'description': '出力に含めるべき最小事実数（品質保証）'
            },
            {
                'key': 'min_insights_count',
                'label': '最小洞察数',
                'type': 'int',
                'default': DomainExpertConfig.DEFAULT_VALUES['min_insights_count'],
                'min': 1,
                'max': 10,
                'description': '出力に含めるべき最小洞察数（品質保証）'
            }
        ]
    
    # ==================== 固定参照値（編集不可） ====================
    @staticmethod
    def get_reference_values():
        """
        信頼度計算に使用される固定参照値
        
        これらの値はシステムの信頼度計算ロジックで使用され、
        ユーザーによる編集は推奨されません。
        
        Returns:
            固定参照値の辞書
        """
        return {
            'max_boost_over_retriever': DomainExpertConfig.DEFAULT_VALUES['max_boost_over_retriever'],
            'max_expert_confidence': DomainExpertConfig.DEFAULT_VALUES['max_expert_confidence'],
            'min_facts_for_bonus': DomainExpertConfig.DEFAULT_VALUES['min_facts_for_bonus'],
            'facts_bonus': DomainExpertConfig.DEFAULT_VALUES['facts_bonus'],
            'citation_rate_threshold': DomainExpertConfig.DEFAULT_VALUES['citation_rate_threshold'],
            'citation_bonus': DomainExpertConfig.DEFAULT_VALUES['citation_bonus'],
            'min_recommendations_for_bonus': DomainExpertConfig.DEFAULT_VALUES['min_recommendations_for_bonus'],
            'recommendations_bonus': DomainExpertConfig.DEFAULT_VALUES['recommendations_bonus']
        }


# ==================== 便利関数 ====================
def get_default_node_config(node_type: str = None):
    """
    指定されたノードタイプのデフォルト設定を取得
    
    Args:
        node_type: ノードタイプ（"domain_expert" など）
    
    Returns:
        デフォルト設定の辞書
    """
    if node_type == "domain_expert" or node_type is None:
        return DomainExpertConfig.DEFAULT_VALUES
    return {}


def validate_config(config: dict) -> tuple[bool, list]:
    """
    設定の妥当性を検証
    
    Args:
        config: 検証する設定辞書
    
    Returns:
        (is_valid, errors): 妥当性フラグとエラーリスト
    """
    errors = []
    
    # 必須キーのチェック
    required_keys = ['expertise_domain', 'max_context_chars', 'expert_profile']
    for key in required_keys:
        if key not in config:
            errors.append(f"必須キー '{key}' が見つかりません")
    
    # 数値範囲のチェック
    if 'max_context_chars' in config:
        value = config['max_context_chars']
        if not isinstance(value, int) or value < 5000 or value > 20000:
            errors.append(f"max_context_chars は 5000-20000 の範囲である必要があります（現在: {value}）")
    
    if 'min_facts_count' in config:
        value = config['min_facts_count']
        if not isinstance(value, int) or value < 1 or value > 10:
            errors.append(f"min_facts_count は 1-10 の範囲である必要があります（現在: {value}）")
    
    if 'min_insights_count' in config:
        value = config['min_insights_count']
        if not isinstance(value, int) or value < 1 or value > 10:
            errors.append(f"min_insights_count は 1-10 の範囲である必要があります（現在: {value}）")
    
    return (len(errors) == 0, errors)