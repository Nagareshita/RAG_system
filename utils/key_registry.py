# utils/key_registry.py
"""
キー名の一元管理レジストリ

全ノードタイプが生成・消費するキーを一元管理し、
命名規則の統一と新規ノード追加の簡易化を実現します。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class KeyDefinition:
    """キー定義データクラス"""
    key_pattern: str              # 例: "{key_name}_{node_id}" or "key_name"
    description: str              # キーの説明
    data_type: str                # データ型（str, float, int, list, dict, bool）
    required: bool = False        # 必須キーかどうか
    generated_by: List[str] = field(default_factory=list)  # 生成元ノードタイプ
    consumed_by: List[str] = field(default_factory=list)   # 消費先ノードタイプ
    
    def format_key(self, node_id: Optional[str] = None) -> str:
        """
        キーパターンから実際のキー名を生成
        
        Args:
            node_id: ノードID（パターンに{node_id}がある場合に必要）
        
        Returns:
            フォーマットされたキー名
        """
        if "{node_id}" in self.key_pattern:
            if node_id is None:
                raise ValueError(f"node_id is required for pattern: {self.key_pattern}")
            return self.key_pattern.format(node_id=node_id)
        return self.key_pattern


class KeyRegistry:
    """
    キー名の一元管理レジストリ
    
    全ノードタイプで使用されるキーを定義し、
    統一的な命名規則とキーの可視化を提供します。
    """
    
    # ========================================
    # よく使用されるキーの定数定義（コード補完用）
    # ========================================
    USER_QUERY = "user_input"
    IMAGE_PATH = "image_path"
    VLM_ANSWER = "vlm_answer"
    REFINED_ANSWER = "refined_answer"
    
    # ========================================
    # システム全体で共通のキー
    # ========================================
    COMMON_KEYS = {
        "user_input": KeyDefinition(
            key_pattern="user_input",
            description="ユーザーの入力テキスト（システムが設定）",
            data_type="str",
            required=True,
            generated_by=["system"],
            consumed_by=["analyzer", "retriever", "domain_expert", "validator", "router", "refiner", "vlm"]
        ),
        "image_path": KeyDefinition(
            key_pattern="image_path",
            description="画像ファイルのパス（VLM用、オプション）",
            data_type="str",
            required=False,
            generated_by=["system"],
            consumed_by=["vlm"]
        ),
        "iteration_count": KeyDefinition(
            key_pattern="iteration_count",
            description="イテレーション回数（システムが管理）",
            data_type="int",
            required=True,
            generated_by=["system"],
            consumed_by=["router"]
        ),
        "execution_count": KeyDefinition(
            key_pattern="execution_count",
            description="ワークフロー実行回数カウンター",
            data_type="int",
            required=False,
            generated_by=["router"],
            consumed_by=["router"]
        ),
        "execution_history": KeyDefinition(
            key_pattern="execution_history",
            description="実行履歴リスト（最大10件保持）",
            data_type="list",
            required=False,
            generated_by=["router"],
            consumed_by=["router"]
        )
    }
    
    # ========================================
    # ノードタイプ別のキー定義
    # ========================================
    NODE_TYPE_KEYS = {
        # ----------------------------------------
        # Analyzer: クエリ分析・最適化
        # ----------------------------------------
        "analyzer": {
            "intent": KeyDefinition(
                key_pattern="intent_{node_id}",
                description="分析されたユーザーの意図",
                data_type="str",
                generated_by=["analyzer"],
                consumed_by=["retriever", "domain_expert", "router"]
            ),
            "optimized_query": KeyDefinition(
                key_pattern="optimized_query_{node_id}",
                description="最適化された検索クエリ",
                data_type="str",
                generated_by=["analyzer"],
                consumed_by=["retriever"]
            ),
            "confidence": KeyDefinition(
                key_pattern="confidence_{node_id}",
                description="分析の信頼度（0.0-1.0）",
                data_type="float",
                generated_by=["analyzer"],
                consumed_by=["router", "validator"]
            ),
            "config": KeyDefinition(
                key_pattern="config_{node_id}",
                description="分析設定情報",
                data_type="dict",
                generated_by=["analyzer"],
                consumed_by=[]
            ),
            # Retriever互換キー（後方互換性のため）
            "optimized_search_query": KeyDefinition(
                key_pattern="optimized_search_query",
                description="検索エンジン用の最適化クエリ（共通キー）",
                data_type="str",
                generated_by=["analyzer"],
                consumed_by=["retriever"]
            )
        },
        
        # ----------------------------------------
        # Retriever: ベクトル検索
        # ----------------------------------------
        "retriever": {
            "search_results": KeyDefinition(
                key_pattern="search_results_{node_id}",
                description="検索結果のリスト",
                data_type="list",
                generated_by=["retriever"],
                consumed_by=["domain_expert", "validator"]
            ),
            "confidence": KeyDefinition(
                key_pattern="confidence_{node_id}",
                description="検索の信頼度（0.0-1.0）",
                data_type="float",
                generated_by=["retriever"],
                consumed_by=["validator", "router"]
            ),
            "retrieval_metadata": KeyDefinition(
                key_pattern="retrieval_metadata_{node_id}",
                description="検索のメタデータ（コレクション名、再ランク情報など）",
                data_type="dict",
                generated_by=["retriever"],
                consumed_by=["validator"]
            )
        },
        
        # ----------------------------------------
        # DomainExpert: 専門分析
        # ----------------------------------------
        "domain_expert": {
            "analysis": KeyDefinition(
                key_pattern="analysis_{node_id}",
                description="専門家による分析結果",
                data_type="str",
                generated_by=["domain_expert"],
                consumed_by=["refiner", "validator"]
            ),
            "facts": KeyDefinition(
                key_pattern="facts_{node_id}",
                description="抽出された事実のリスト",
                data_type="list",
                generated_by=["domain_expert"],
                consumed_by=["refiner"]
            ),
            "insights": KeyDefinition(
                key_pattern="insights_{node_id}",
                description="得られた洞察のリスト",
                data_type="list",
                generated_by=["domain_expert"],
                consumed_by=["refiner"]
            ),
            "recommendations": KeyDefinition(
                key_pattern="recommendations_{node_id}",
                description="推奨事項のリスト",
                data_type="list",
                generated_by=["domain_expert"],
                consumed_by=["refiner"]
            ),
            "confidence": KeyDefinition(
                key_pattern="confidence_{node_id}",
                description="分析の信頼度（0.0-1.0）",
                data_type="float",
                generated_by=["domain_expert"],
                consumed_by=["validator", "router"]
            ),
            "gaps": KeyDefinition(
                key_pattern="gaps_{node_id}",
                description="情報ギャップのリスト",
                data_type="list",
                generated_by=["domain_expert"],
                consumed_by=["refiner"]
            )
        },
        
        # ----------------------------------------
        # Validator: 信頼度検証
        # ----------------------------------------
        "validator": {
            "validation_result": KeyDefinition(
                key_pattern="validation_result_{node_id}",
                description="検証結果の詳細",
                data_type="dict",
                generated_by=["validator"],
                consumed_by=["router", "refiner"]
            ),
            "validation_confidence": KeyDefinition(
                key_pattern="validation_confidence_{node_id}",
                description="総合信頼度（0.0-1.0）",
                data_type="float",
                generated_by=["validator"],
                consumed_by=["router"]
            ),
            "validation_passed": KeyDefinition(
                key_pattern="validation_passed_{node_id}",
                description="検証合格フラグ",
                data_type="bool",
                generated_by=["validator"],
                consumed_by=["router"]
            ),
            "validation_details": KeyDefinition(
                key_pattern="validation_details_{node_id}",
                description="検証の詳細情報（各指標の内訳）",
                data_type="dict",
                generated_by=["validator"],
                consumed_by=["refiner"]
            )
        },
        
        # ----------------------------------------
        # Router: 条件分岐
        # ----------------------------------------
        "router": {
            "router_decision": KeyDefinition(
                key_pattern="router_decision_{node_id}",
                description="ルーティング判定結果（LangGraphが使用）",
                data_type="str",
                generated_by=["router"],
                consumed_by=["system"]
            ),
            "target_node": KeyDefinition(
                key_pattern="target_node_{node_id}",
                description="次に実行するノードID",
                data_type="str",
                generated_by=["router"],
                consumed_by=["system"]
            ),
            "routing_metadata": KeyDefinition(
                key_pattern="routing_metadata_{node_id}",
                description="ルーティングのメタデータ",
                data_type="dict",
                generated_by=["router"],
                consumed_by=[]
            )
        },
        
        # ----------------------------------------
        # Refiner: 統合・整形
        # ----------------------------------------
        "refiner": {
            "refined_answer": KeyDefinition(
                key_pattern="refined_answer",
                description="最終統合回答（共通キー）",
                data_type="str",
                generated_by=["refiner"],
                consumed_by=["system"]
            ),
            "refined_answer_node": KeyDefinition(
                key_pattern="refined_answer_{node_id}",
                description="ノード固有の統合回答",
                data_type="str",
                generated_by=["refiner"],
                consumed_by=["system"]
            ),
            "refiner_metadata": KeyDefinition(
                key_pattern="refiner_metadata_{node_id}",
                description="統合処理のメタデータ",
                data_type="dict",
                generated_by=["refiner"],
                consumed_by=[]
            ),
            "generation_confidence": KeyDefinition(
                key_pattern="generation_confidence_{node_id}",
                description="生成の信頼度（0.0-1.0）",
                data_type="float",
                generated_by=["refiner"],
                consumed_by=[]
            )
        },
        
        # ----------------------------------------
        # VLM: Vision Language Model
        # ----------------------------------------
        "vlm": {
            "vlm_answer": KeyDefinition(
                key_pattern="vlm_answer",
                description="VLMによる画像認識・質問応答結果（共通キー）",
                data_type="str",
                generated_by=["vlm"],
                consumed_by=["system", "refiner", "validator"]
            ),
            "vlm_answer_node": KeyDefinition(
                key_pattern="vlm_answer_{node_id}",
                description="ノード固有のVLM応答",
                data_type="str",
                generated_by=["vlm"],
                consumed_by=["system"]
            )
        }
    }
    
    # ========================================
    # クラスメソッド
    # ========================================
    
    @classmethod
    def get_key_name(cls, node_type: str, key_base: str, node_id: Optional[str] = None) -> str:
        """
        キー名を生成
        
        Args:
            node_type: ノードタイプ（analyzer, retriever, domain_expert, validator, router, refiner）
            key_base: 基本キー名（intent, search_results, analysis, etc.）
            node_id: ノードID（パターンに{node_id}がある場合に必要）
        
        Returns:
            完全なキー名
        
        Raises:
            ValueError: 未定義のノードタイプまたはキー名の場合
        """
        # 共通キーを確認
        if key_base in cls.COMMON_KEYS:
            return cls.COMMON_KEYS[key_base].format_key(node_id)
        
        # ノードタイプ別キーを確認
        if node_type not in cls.NODE_TYPE_KEYS:
            raise ValueError(f"Unknown node type: {node_type}")
        
        node_keys = cls.NODE_TYPE_KEYS[node_type]
        if key_base not in node_keys:
            raise ValueError(f"Unknown key '{key_base}' for node type '{node_type}'")
        
        return node_keys[key_base].format_key(node_id)
    
    @classmethod
    def get_keys_for_node_type(cls, node_type: str) -> Dict[str, KeyDefinition]:
        """
        指定ノードタイプが生成するキー一覧を取得
        
        Args:
            node_type: ノードタイプ
        
        Returns:
            キー定義の辞書
        """
        return cls.NODE_TYPE_KEYS.get(node_type, {})
    
    @classmethod
    def get_all_node_types(cls) -> List[str]:
        """
        定義されている全ノードタイプを取得
        
        Returns:
            ノードタイプのリスト
        """
        return list(cls.NODE_TYPE_KEYS.keys())
    
    @classmethod
    def validate_key_usage(cls, node_type: str, keys_to_generate: List[str]) -> List[str]:
        """
        キー使用の妥当性を検証
        
        Args:
            node_type: ノードタイプ
            keys_to_generate: 生成しようとしているキーのリスト
        
        Returns:
            警告メッセージのリスト（問題がない場合は空リスト）
        """
        warnings = []
        defined_keys = cls.get_keys_for_node_type(node_type)
        
        for key in keys_to_generate:
            # ノードID付きキーの場合、ベース名を抽出
            base_key = key
            
            if '_' in key:
                parts = key.rsplit('_', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    # 最後が数字の場合、それより前がベース名
                    base_key = parts[0]
                else:
                    # 数字で終わらない場合はそのまま
                    base_key = key
            
            # 共通キーまたはノードタイプ別キーに定義されているか確認
            if base_key not in cls.COMMON_KEYS and base_key not in defined_keys:
                warnings.append(
                    f"未定義キー: {key} (ノードタイプ: {node_type}, ベース名: {base_key})"
                )
        
        return warnings
    
    @classmethod
    def export_to_json(cls) -> Dict[str, Any]:
        """
        agents_designer用にJSON形式でエクスポート
        
        Returns:
            キー定義を含む辞書
        """
        export_data = {
            "version": "1.0",
            "common_keys": {},
            "node_type_keys": {}
        }
        
        # 共通キーのエクスポート
        for key_name, definition in cls.COMMON_KEYS.items():
            export_data["common_keys"][key_name] = {
                "pattern": definition.key_pattern,
                "description": definition.description,
                "type": definition.data_type,
                "required": definition.required,
                "generated_by": definition.generated_by,
                "consumed_by": definition.consumed_by
            }
        
        # ノードタイプ別キーのエクスポート
        for node_type, keys in cls.NODE_TYPE_KEYS.items():
            export_data["node_type_keys"][node_type] = {}
            for key_name, definition in keys.items():
                export_data["node_type_keys"][node_type][key_name] = {
                    "pattern": definition.key_pattern,
                    "description": definition.description,
                    "type": definition.data_type,
                    "required": definition.required,
                    "generated_by": definition.generated_by,
                    "consumed_by": definition.consumed_by
                }
        
        return export_data
    
    @classmethod
    def get_key_info(cls, key_name: str) -> Optional[KeyDefinition]:
        """
        キー名から定義情報を取得
        
        Args:
            key_name: キー名（完全なキー名またはベース名）
        
        Returns:
            KeyDefinition または None
        """
        # 共通キーを確認
        if key_name in cls.COMMON_KEYS:
            return cls.COMMON_KEYS[key_name]
        
        # ノードID付きキーの場合、ベース名を抽出
        # 例: "intent_1" -> "intent", "search_results_2" -> "search_results"
        base_key = key_name
        if '_' in key_name:
            parts = key_name.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                # 最後が数字の場合、それより前がベース名
                base_key = parts[0]
        
        # 全ノードタイプを検索
        for node_type, keys in cls.NODE_TYPE_KEYS.items():
            if base_key in keys:
                return keys[base_key]
        
        return None


# ========================================
# ユーティリティ関数
# ========================================

def get_key_documentation() -> str:
    """
    全キー定義のドキュメントを生成
    
    Returns:
        マークダウン形式のドキュメント文字列
    """
    doc_lines = ["# LangGraph Workflow Key Registry\n"]
    doc_lines.append("## Common Keys (System-wide)\n")
    
    for key_name, definition in KeyRegistry.COMMON_KEYS.items():
        doc_lines.append(f"### `{definition.key_pattern}`")
        doc_lines.append(f"- **Description**: {definition.description}")
        doc_lines.append(f"- **Type**: `{definition.data_type}`")
        doc_lines.append(f"- **Required**: {definition.required}")
        doc_lines.append(f"- **Generated by**: {', '.join(definition.generated_by)}")
        doc_lines.append(f"- **Consumed by**: {', '.join(definition.consumed_by)}\n")
    
    doc_lines.append("\n## Node Type Keys\n")
    
    for node_type in KeyRegistry.get_all_node_types():
        doc_lines.append(f"\n### {node_type.capitalize()}\n")
        keys = KeyRegistry.get_keys_for_node_type(node_type)
        
        for key_name, definition in keys.items():
            doc_lines.append(f"#### `{definition.key_pattern}`")
            doc_lines.append(f"- **Description**: {definition.description}")
            doc_lines.append(f"- **Type**: `{definition.data_type}`")
            doc_lines.append(f"- **Generated by**: {', '.join(definition.generated_by)}")
            doc_lines.append(f"- **Consumed by**: {', '.join(definition.consumed_by)}\n")
    
    return "\n".join(doc_lines)