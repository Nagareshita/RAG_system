# agent_designer/ui/agent_settings/validator/config.py
"""
Validator設定の完全統合
- UI表示情報（色、説明）
- デフォルト設定値
- 信頼度閾値・重み設定管理
- LLMプロンプト管理
- 実行用thresholds形式
- 設定検証ルール
"""

class ValidatorConfig:
    """Validator設定の統合管理クラス"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'Validator',
        'description': '品質検証・評価エージェント',
        'color': {
            'fill': (220, 180, 120, 200),
            'border': (255, 220, 160),
            'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        'confidence_threshold': 0.80,
        'llm_max_tokens': 600,
        'minimum_source_count': 6,
        'logging_level': 'VERBOSE',
        # 固定重み設定（編集不可）
        'retriever_weight': 0.15,
        'expert_weight': 0.50,
        'llm_weight': 0.25,
        'rule_weight': 0.10,
        'llm_prompts': {
            'validation_instruction': '以下のModelica専門分析の品質を客観的に評価してください。AST・PDF両方の情報源を活用した統合分析の論理整合性、事実の正確性、引用の妥当性を重点的に検証してください。',
            'evaluation_criteria': '引用整合性、論理的一貫性、情報源の充足性、技術的妥当性、実装可能性、AST・PDF情報の統合品質を厳格に評価してください。',
            'output_format': 'JSON形式で issues(問題点配列), confidence(0.0-1.0), evidence_assessment(強い証拠|中程度の証拠|弱い証拠), improvement_suggestions(改善提案配列) を必須出力してください。',
            'confidence_calculation': '段階間連携信頼度計算により、前段階の品質を反映した最終評価を行ってください。'
        },
        'final_prompt_template': '''{validation_instruction}

質問: "{user_query}"
事実: {facts_summary}
洞察: {insights_summary}

【評価基準】
{evaluation_criteria}

【信頼度計算指針】
{confidence_calculation}

{output_format}:
{{
"issues": ["品質問題があれば記述、問題なければ空配列"],
"confidence": 0.75,
"evidence_assessment": "強い証拠|中程度の証拠|弱い証拠",
"improvement_suggestions": ["改善提案があれば記述"]
}}'''
    }
    
    # 設定項目の定義（UI生成とバリデーション用）
    SETTINGS_SCHEMA = {
        'confidence_threshold': {
            'type': 'float',
            'label': '信頼度閾値',
            'min_value': 0.0,
            'max_value': 1.0,
            'format': '%.2f',
            'description': '検証合格の最小信頼度 (0.0-1.0)'
        },
        'llm_max_tokens': {
            'type': 'int',
            'label': 'LLM最大トークン数',
            'min_value': 1,
            'description': 'LLM検証時の最大生成トークン数'
        },
        'minimum_source_count': {
            'type': 'int',
            'label': '最小ソース数',
            'min_value': 1,
            'description': '検証に必要な最小情報源数'
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログ出力レベル',
            'options': [
                ('VERBOSE', '詳細 (VERBOSE)'),
                ('MINIMAL', '最小限 (MINIMAL)')
            ],
            'description': 'ログ出力の詳細度'
        },
        'validation_instruction': {
            'type': 'textarea',
            'label': '検証指示',
            'height': 100,
            'description': '品質評価の基本指示'
        },
        'evaluation_criteria': {
            'type': 'textarea',
            'label': '評価基準',
            'height': 80,
            'description': '品質評価で重視する基準'
        },
        'output_format': {
            'type': 'textarea',
            'label': '出力フォーマット指示',
            'height': 80,
            'description': '出力形式の指定'
        },
        'confidence_calculation': {
            'type': 'textarea',
            'label': '信頼度計算指針',
            'height': 60,
            'description': '信頼度計算の方針'
        },
        'final_prompt_template': {
            'type': 'textarea',
            'label': '最終プロンプトテンプレート',
            'height': 200,
            'description': '実行時に使用される完全なプロンプトテンプレート',
            'placeholder_info': '{validation_instruction}, {user_query}, {facts_summary}, {insights_summary}等の変数が使用可能'
        }
    }
    
    @classmethod
    def get_default_config(cls):
        """GUIで使用するデフォルト設定を返却"""
        return cls.DEFAULT_VALUES.copy()
    
    @classmethod
    def get_execution_thresholds(cls, config_values):
        """実行用のthresholds形式に変換"""
        # llm_prompts構築
        llm_prompts = config_values.get('llm_prompts', cls.DEFAULT_VALUES['llm_prompts'].copy())
        
        # 個別プロンプト項目をまとめてllm_promptsに統合
        if any(key in config_values for key in ['validation_instruction', 'evaluation_criteria', 'output_format', 'confidence_calculation']):
            llm_prompts = {
                'validation_instruction': config_values.get('validation_instruction', llm_prompts.get('validation_instruction', '')),
                'evaluation_criteria': config_values.get('evaluation_criteria', llm_prompts.get('evaluation_criteria', '')),
                'output_format': config_values.get('output_format', llm_prompts.get('output_format', '')),
                'confidence_calculation': config_values.get('confidence_calculation', llm_prompts.get('confidence_calculation', '')),
                'final_prompt_template': config_values.get('final_prompt_template', llm_prompts.get('final_prompt_template', cls.DEFAULT_VALUES['final_prompt_template']))
            }
        
        return {
            "confidence_threshold": {"value": float(config_values.get('confidence_threshold', cls.DEFAULT_VALUES['confidence_threshold']))},
            "retriever_weight": {"value": cls.DEFAULT_VALUES['retriever_weight']},
            "expert_weight": {"value": cls.DEFAULT_VALUES['expert_weight']},
            "llm_weight": {"value": cls.DEFAULT_VALUES['llm_weight']},
            "rule_weight": {"value": cls.DEFAULT_VALUES['rule_weight']},
            "llm_max_tokens": {"value": int(config_values.get('llm_max_tokens', cls.DEFAULT_VALUES['llm_max_tokens']))},
            "minimum_source_count": {"value": int(config_values.get('minimum_source_count', cls.DEFAULT_VALUES['minimum_source_count']))},
            "llm_prompts": {"value": llm_prompts}
        }
    
    @classmethod
    def validate_config(cls, config_values):
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # confidence_threshold validation
        try:
            confidence_threshold = float(config_values.get('confidence_threshold', cls.DEFAULT_VALUES['confidence_threshold']))
            if confidence_threshold < 0.0 or confidence_threshold > 1.0:
                errors.append("信頼度閾値は0.0から1.0の範囲で入力してください")
        except (ValueError, TypeError):
            errors.append("信頼度閾値は数値を入力してください")
        
        # llm_max_tokens validation
        try:
            llm_max_tokens = int(config_values.get('llm_max_tokens', cls.DEFAULT_VALUES['llm_max_tokens']))
            if llm_max_tokens <= 0:
                errors.append("LLM最大トークン数は正の整数を入力してください")
            elif llm_max_tokens > 4000:
                warnings.append("LLM最大トークン数が大きすぎます（推奨: 4000以下）")
        except (ValueError, TypeError):
            errors.append("LLM最大トークン数は整数を入力してください")
        
        # minimum_source_count validation
        try:
            minimum_source_count = int(config_values.get('minimum_source_count', cls.DEFAULT_VALUES['minimum_source_count']))
            if minimum_source_count <= 0:
                errors.append("最小ソース数は正の整数を入力してください")
            elif minimum_source_count > 20:
                warnings.append("最小ソース数が大きすぎます（推奨: 20以下）")
        except (ValueError, TypeError):
            errors.append("最小ソース数は整数を入力してください")
        
        # logging_level validation
        logging_level = config_values.get('logging_level', cls.DEFAULT_VALUES['logging_level'])
        valid_levels = ['VERBOSE', 'MINIMAL']
        if logging_level not in valid_levels:
            errors.append(f"ログレベルは {', '.join(valid_levels)} のいずれかを選択してください")
        
        # プロンプト項目の必須チェック
        required_prompts = ['validation_instruction', 'evaluation_criteria', 'output_format']
        for prompt_key in required_prompts:
            if not config_values.get(prompt_key, '').strip():
                warnings.append(f"{cls.SETTINGS_SCHEMA[prompt_key]['label']}が空です")
        
        # 最終プロンプトテンプレートのチェック
        final_template = config_values.get('final_prompt_template', '')
        if final_template:
            required_vars = ['{validation_instruction}', '{user_query}', '{output_format}']
            missing_vars = [var for var in required_vars if var not in final_template]
            if missing_vars:
                warnings.append(f"最終プロンプトテンプレートに必要な変数が不足: {', '.join(missing_vars)}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_ui_info(cls):
        """UI表示用の情報を返却"""
        return cls.UI_INFO.copy()
    
    @classmethod
    def get_settings_schema(cls):
        """設定項目のスキーマを返却"""
        return cls.SETTINGS_SCHEMA.copy()
    
    # ===== 統合アクセスメソッド（agent_types廃止後の互換） =====
    
    @classmethod
    def get_default_node_config(cls):
        """
        デフォルトノード設定を返却（agent_types.defaults互換）
        GUI内部で使用される形式
        """
        return cls.DEFAULT_VALUES.copy()
    
    @classmethod
    def get_gui_metadata(cls):
        """
        GUI表示用メタデータを返却（agent_types互換）
        色情報、名前、説明を含む
        """
        return {
            'name': cls.UI_INFO['name'],
            'description': cls.UI_INFO['description'],
            'color': cls.UI_INFO['color'].copy()
        }
    
    @classmethod
    def get_weight_settings(cls):
        """重み設定（固定値）を返却"""
        return {
            'retriever_weight': cls.DEFAULT_VALUES['retriever_weight'],
            'expert_weight': cls.DEFAULT_VALUES['expert_weight'],
            'llm_weight': cls.DEFAULT_VALUES['llm_weight'],
            'rule_weight': cls.DEFAULT_VALUES['rule_weight']
        }
    
    @classmethod
    def get_reference_values(cls):
        """参照値（編集不可）を返却"""
        return {
            'retriever_weight': cls.DEFAULT_VALUES['retriever_weight'],
            'expert_weight': cls.DEFAULT_VALUES['expert_weight'],
            'llm_weight': cls.DEFAULT_VALUES['llm_weight'],
            'rule_weight': cls.DEFAULT_VALUES['rule_weight']
        }