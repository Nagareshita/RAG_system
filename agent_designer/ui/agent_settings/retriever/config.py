# agent_designer/ui/node_settings/retriever/config.py
"""
Retriever設定の完全統合
- UI表示情報（色、説明）
- デフォルト設定値
- 実行用thresholds形式
- 設定検証ルール
"""

class RetrieverConfig:
    """Retriever設定の統合管理クラス"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'Retriever',
        'description': 'ベクトルDB検索エージェント',
        'color': {
                # 青系: 視認性を高める
                'fill': (70, 130, 200, 200),
                'border': (100, 160, 220),
                'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        'target_collections': 'rag_documents_pdf',  # 文字列形式（実行時に配列に変換）
        'search_k': 6,
        'initial_k': 50,
        'similarity_threshold': 0.2,
        'use_reranker': True,
        'reranker_model': 'BAAI/bge-reranker-large',
        'logging_level': 'VERBOSE'
    }
    
    # 設定項目の定義（UI生成とバリデーション用）
    SETTINGS_SCHEMA = {
        'target_collections': {
            'type': 'combo',
            'label': '検索対象コレクション',
            'options': [
                ('rag_documents_pdf', 'rag_documents_pdf（PDF検索）'),
                ('rag_documents_ast', 'rag_documents_ast（AST検索）')
            ],
            'description': '検索対象のベクトルDBコレクション'
        },
        'search_k': {
            'type': 'int',
            'label': '最終取得件数',
            'min_value': 1,
            'max_value': 100,
            'description': '最終的に取得する検索結果の件数'
        },
        'similarity_threshold': {
            'type': 'float',
            'label': '類似度閾値',
            'min_value': 0.0,
            'max_value': 1.0,
            'format': '%.2f',
            'description': '検索結果フィルタリングの類似度閾値'
        },
        'use_reranker': {
            'type': 'checkbox',
            'label': '再ランクモデルを使用する',
            'description': '検索結果の再ランキングを実行',
            'affects': ['initial_k']  # この設定が影響する他の設定
        },
        'initial_k': {
            'type': 'int',
            'label': '初期検索数',
            'min_value': 10,
            'max_value': 200,
            'description': '再ランク使用時の初期候補数',
            'depends_on': 'use_reranker'  # この設定が依存する設定
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログ出力レベル',
            'options': [
                ('VERBOSE', 'VERBOSE（詳細）'),
                ('MINIMAL', 'MINIMAL（最小限）')
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
        # target_collectionsを必ず配列として処理
        target_collections = config_values.get('target_collections', cls.DEFAULT_VALUES['target_collections'])
        if isinstance(target_collections, str):
            # 文字列の場合は配列にラップ
            target_collections = [target_collections]
        elif not isinstance(target_collections, list):
            # リストでない場合はデフォルト値を使用
            target_collections = cls.DEFAULT_VALUES['target_collections']
        
        return {
            "search_k": {"value": config_values.get('search_k', cls.DEFAULT_VALUES['search_k'])},
            "initial_k": {"value": config_values.get('initial_k', cls.DEFAULT_VALUES['initial_k'])},
            "similarity_threshold": {"value": config_values.get('similarity_threshold', cls.DEFAULT_VALUES['similarity_threshold'])},
            "use_reranker": {"value": config_values.get('use_reranker', cls.DEFAULT_VALUES['use_reranker'])},
            "target_collections": {"value": target_collections},
            "reranker_model": {"value": config_values.get('reranker_model', cls.DEFAULT_VALUES['reranker_model'])}
        }
    
    @classmethod
    def validate_config(cls, config_values):
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # search_k validation
        search_k = config_values.get('search_k', cls.DEFAULT_VALUES['search_k'])
        if not (1 <= search_k <= 100):
            errors.append("最終取得件数は1-100の範囲で設定してください")
        
        # similarity_threshold validation
        threshold = config_values.get('similarity_threshold', cls.DEFAULT_VALUES['similarity_threshold'])
        if not (0.0 <= threshold <= 1.0):
            errors.append("類似度閾値は0.0-1.0の範囲で設定してください")
        
        # initial_k validation (use_reranker=trueの場合のみ)
        use_reranker = config_values.get('use_reranker', cls.DEFAULT_VALUES['use_reranker'])
        if use_reranker:
            initial_k = config_values.get('initial_k', cls.DEFAULT_VALUES['initial_k'])
            if not (10 <= initial_k <= 200):
                errors.append("初期検索数は10-200の範囲で設定してください")
            elif initial_k < search_k:
                warnings.append(f"初期検索数({initial_k})が最終取得件数({search_k})より小さいです")
        
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