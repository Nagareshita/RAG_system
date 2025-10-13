# agent_designer/ui/agent_settings/__init__.py
"""
エージェント設定モジュールの初期化

全エージェントタイプのデフォルト設定とGUIメタデータを提供する統合インターフェース
"""

from typing import Dict, Any, Optional

# サポートされるエージェントタイプのリスト
CONFIG_CLASSES = [
    "analyzer",
    "retriever",
    "domain_expert",
    "validator",
    "refiner",
    "router",
    "vlm"
]


def get_default_node_config(node_type: str) -> Dict[str, Any]:
    """
    指定されたノードタイプのデフォルト設定を取得
    
    Args:
        node_type: エージェントタイプ
            - "analyzer"
            - "retriever"
            - "domain_expert"
            - "validator"
            - "refiner"
            - "router"
    
    Returns:
        デフォルト設定の辞書
    
    Raises:
        ImportError: 該当する設定モジュールが見つからない場合
    """
    try:
        if node_type == "analyzer":
            from .analyzer.config import AnalyzerConfig
            return AnalyzerConfig.DEFAULT_VALUES
        
        elif node_type == "retriever":
            from .retriever.config import RetrieverConfig
            return RetrieverConfig.DEFAULT_VALUES
        
        elif node_type == "domain_expert":
            from .domain_expert.config import DomainExpertConfig
            return DomainExpertConfig.DEFAULT_VALUES
        
        elif node_type == "validator":
            from .validator.config import ValidatorConfig
            return ValidatorConfig.DEFAULT_VALUES
        
        elif node_type == "refiner":
            from .refiner.config import RefinerConfig
            # 注意: sectionsは含まない基本設定のみを返す
            # sectionsはUI初回表示時にのみデフォルト適用される
            return RefinerConfig.DEFAULT_VALUES.copy()
        
        elif node_type == "router":
            from .router.config import RouterConfig
            return RouterConfig.DEFAULT_VALUES
        
        elif node_type == "vlm":
            from .vlm.config import VLMConfig
            return VLMConfig.DEFAULT_VALUES.copy()
        
        else:
            # 未知のエージェントタイプ
            return {}
    
    except ImportError as e:
        # 設定ファイルが見つからない場合は空辞書
        # デバッグ用に警告を出力（オプション）
        import warnings
        warnings.warn(
            f"Could not import config for node_type '{node_type}': {e}",
            ImportWarning
        )
        return {}


def get_gui_metadata(node_type: str) -> Optional[Dict[str, Any]]:
    """
    指定されたノードタイプのGUIメタデータを取得
    
    GUIメタデータには、ノードの表示名、説明、色情報などが含まれます。
    
    Args:
        node_type: エージェントタイプ
    
    Returns:
        GUIメタデータの辞書、または見つからない場合はNone
    
    Example:
        >>> metadata = get_gui_metadata("analyzer")
        >>> print(metadata['name'])  # "Analyzer"
        >>> print(metadata['color']['fill'])  # (100, 150, 200, 200)
    """
    try:
        if node_type == "analyzer":
            from .analyzer.config import AnalyzerConfig
            return AnalyzerConfig.UI_INFO
        
        elif node_type == "retriever":
            from .retriever.config import RetrieverConfig
            return RetrieverConfig.UI_INFO
        
        elif node_type == "domain_expert":
            from .domain_expert.config import DomainExpertConfig
            return DomainExpertConfig.UI_INFO
        
        elif node_type == "validator":
            from .validator.config import ValidatorConfig
            return ValidatorConfig.UI_INFO
        
        elif node_type == "refiner":
            from .refiner.config import RefinerConfig
            return RefinerConfig.UI_INFO
        
        elif node_type == "router":
            from .router.config import RouterConfig
            return RouterConfig.UI_INFO
        
        elif node_type == "vlm":
            from .vlm.config import VLMConfig
            return VLMConfig.UI_INFO
        
        else:
            # 未知のエージェントタイプ: デフォルトメタデータを返す
            return {
                'name': node_type.title(),
                'description': f'{node_type} agent',
                'color': {
                    'fill': (128, 128, 128, 200),
                    'border': (160, 160, 160),
                    'text': (255, 255, 255)
                }
            }
    
    except ImportError:
        # 設定ファイルが見つからない場合はデフォルトメタデータ
        return {
            'name': node_type.title(),
            'description': f'{node_type} agent',
            'color': {
                'fill': (128, 128, 128, 200),
                'border': (160, 160, 160),
                'text': (255, 255, 255)
            }
        }
    except AttributeError:
        # UI_INFO属性がない場合もデフォルト
        return {
            'name': node_type.title(),
            'description': f'{node_type} agent',
            'color': {
                'fill': (128, 128, 128, 200),
                'border': (160, 160, 160),
                'text': (255, 255, 255)
            }
        }


def get_ui_fields(node_type: str) -> list:
    """
    指定されたノードタイプのUI設定フィールドを取得
    
    UI設定フィールドには、GUIで編集可能なパラメータの定義が含まれます。
    
    Args:
        node_type: エージェントタイプ
    
    Returns:
        UI設定フィールドのリスト
    
    Example:
        >>> fields = get_ui_fields("domain_expert")
        >>> for field in fields:
        ...     print(f"{field['key']}: {field['type']}")
    """
    try:
        if node_type == "analyzer":
            from .analyzer.config import AnalyzerConfig
            return AnalyzerConfig.get_ui_fields()
        
        elif node_type == "retriever":
            from .retriever.config import RetrieverConfig
            return RetrieverConfig.get_ui_fields()
        
        elif node_type == "domain_expert":
            from .domain_expert.config import DomainExpertConfig
            return DomainExpertConfig.get_ui_fields()
        
        elif node_type == "validator":
            from .validator.config import ValidatorConfig
            return ValidatorConfig.get_ui_fields()
        
        elif node_type == "refiner":
            from .refiner.config import RefinerConfig
            return RefinerConfig.get_ui_fields()
        
        elif node_type == "router":
            from .router.config import RouterConfig
            return RouterConfig.get_ui_fields()
        
        elif node_type == "vlm":
            from .vlm.config import VLMConfig
            return VLMConfig.get_ui_fields()
        
        else:
            return []
    
    except (ImportError, AttributeError):
        return []


__all__ = [
    'get_default_node_config',
    'get_gui_metadata',
    'get_ui_fields',
    'CONFIG_CLASSES'
]