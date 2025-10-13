# agent_designer/ui/agent_settings/analyzer/config.py
"""
Analyzer設定の完全統合
- UI表示情報（色、説明）
- デフォルト設定値
- LLMプロンプト管理
- 実行用thresholds形式
- 設定検証ルール
"""

class AnalyzerConfig:
    """Analyzer設定の統合管理クラス"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'Analyzer',
        'description': 'クエリ解析・最適化エージェント',
        'color': {
            'fill': (120, 180, 120, 200),
            'border': (160, 220, 160),
            'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        'analysis_depth': 'comprehensive',
        'logging_level': 'VERBOSE',
        'llm_prompts': {
            'base_instruction': '以下のユーザー入力を分析し、Modelica技術検索に最適化されたクエリを生成してください。実行履歴がある場合は前回の結果を改善してください。',
            'optimization_focus': 'Modelica専門用語の保持、技術コンテキストの明確化、AST・PDF両方での検索効率最大化、前回の不備改善を重視してください。',
            'output_format': 'JSON形式で intent, complexity, optimized_query, sources, confidence, improvement_applied を必須出力してください。',
            'quality_criteria': '技術的正確性、検索適合性、実装可能性、前回フィードバック反映を最優先に分析してください。',
            'query_optimization_rules': '1. 元の質問の核心的な意味とニュアンスを保持\n2. 冗長な依頼語を除去し、技術用語は保持\n3. 技術文脈・対象範囲を自然に表現\n4. 固有名詞・API/クラス/関数名を保持\n5. AST・PDF両方に適応するキーワードを埋め込む\n6. 前回の不備や推奨改善点を反映'
        },
        'final_prompt_template': '''{base_instruction}

{optimization_focus}

{quality_criteria}

【クエリ最適化ルール】
{query_optimization_rules}

分析深度: {analysis_depth}
{context_section}

ユーザー入力: "{user_input}"

{output_format}:
{{
"intent": "質問の意図",
"complexity": "simple/medium/complex", 
"optimized_query": "検索最適化されたクエリ",
"sources": ["ast_data: プログラム構造", "pdf_documents: 文献", "both: 両方"],
"confidence": 0.0-1.0の信頼度
}}'''
    }
    
    # 設定項目の定義（UI生成とバリデーション用）
    SETTINGS_SCHEMA = {
        'analysis_depth': {
            'type': 'combo',
            'label': '分析深度',
            'options': [
                ('basic', '基本 (basic)'),
                ('detailed', '詳細 (detailed)'),
                ('comprehensive', '包括的 (comprehensive)')
            ],
            'description': 'クエリ分析の詳細度'
        },
        'base_instruction': {
            'type': 'textarea',
            'label': '基本指示',
            'height': 100,
            'description': 'エージェントの基本的な動作指示'
        },
        'optimization_focus': {
            'type': 'textarea',
            'label': '最適化重点項目',
            'height': 80,
            'description': '最適化で重視する要素'
        },
        'output_format': {
            'type': 'textarea',
            'label': '出力フォーマット指示',
            'height': 60,
            'description': '出力形式の指定'
        },
        'quality_criteria': {
            'type': 'textarea',
            'label': '品質基準',
            'height': 60,
            'description': '品質評価の基準'
        },
        'query_optimization_rules': {
            'type': 'textarea',
            'label': 'クエリ最適化ルール',
            'height': 120,
            'description': 'クエリ最適化の具体的ルール'
        },
        'final_prompt_template': {
            'type': 'textarea',
            'label': '最終プロンプトテンプレート',
            'height': 200,
            'description': '実行時に使用される完全なプロンプトテンプレート',
            'placeholder_info': '{user_input}, {analysis_depth}, {context_section}等の変数が使用可能'
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログ出力レベル',
            'options': [
                ('VERBOSE', '詳細 (VERBOSE)'),
                ('MINIMAL', '最小限 (MINIMAL)')
            ],
            'description': 'ログ出力の詳細度'
        }
    }
    
    @classmethod
    def get_default_config(cls):
        """GUIで使用するデフォルト設定を返却"""
        return cls.DEFAULT_VALUES.copy()
    
    @classmethod
    def get_execution_thresholds(cls, config_values):
        """実行用のthresholds形式に変換"""
        llm_prompts = config_values.get('llm_prompts', cls.DEFAULT_VALUES['llm_prompts'].copy())
        
        # 個別プロンプト項目をまとめてllm_promptsに統合
        if any(key in config_values for key in ['base_instruction', 'optimization_focus', 'output_format', 'quality_criteria', 'query_optimization_rules']):
            llm_prompts = {
                'base_instruction': config_values.get('base_instruction', llm_prompts.get('base_instruction', '')),
                'optimization_focus': config_values.get('optimization_focus', llm_prompts.get('optimization_focus', '')),
                'output_format': config_values.get('output_format', llm_prompts.get('output_format', '')),
                'quality_criteria': config_values.get('quality_criteria', llm_prompts.get('quality_criteria', '')),
                'query_optimization_rules': config_values.get('query_optimization_rules', llm_prompts.get('query_optimization_rules', ''))
            }
        
        return {
            "analysis_depth": {"value": config_values.get('analysis_depth', cls.DEFAULT_VALUES['analysis_depth'])},
            "llm_prompts": {"value": llm_prompts}
        }
    
    @classmethod
    def validate_config(cls, config_values):
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # analysis_depth validation
        analysis_depth = config_values.get('analysis_depth', cls.DEFAULT_VALUES['analysis_depth'])
        valid_depths = ['basic', 'detailed', 'comprehensive']
        if analysis_depth not in valid_depths:
            errors.append(f"分析深度は {', '.join(valid_depths)} のいずれかを選択してください")
        
        # プロンプト項目の必須チェック
        required_prompts = ['base_instruction', 'optimization_focus', 'output_format', 'quality_criteria']
        for prompt_key in required_prompts:
            if not config_values.get(prompt_key, '').strip():
                warnings.append(f"{cls.SETTINGS_SCHEMA[prompt_key]['label']}が空です")
        
        # 最終プロンプトテンプレートのチェック
        final_template = config_values.get('final_prompt_template', '')
        if final_template and '{user_input}' not in final_template:
            warnings.append("最終プロンプトテンプレートに{user_input}変数が含まれていません")
        
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