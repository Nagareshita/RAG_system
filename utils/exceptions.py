# utils/exceptions.py
"""
ワークフロー設定エラーの例外クラス定義

このモジュールは、設定管理システムで発生する各種エラーに対応する
カスタム例外クラスを提供します。
"""


class WorkflowConfigError(Exception):
    """ワークフロー設定エラーの基底クラス"""
    pass


class LegacyFormatError(WorkflowConfigError):
    """
    旧形式（thresholds）使用時のエラー
    
    新形式（node_thresholds）への移行を強制するための例外。
    旧形式の設定ファイルを検出した場合に発生します。
    """
    def __init__(self, message=None):
        if message is None:
            message = (
                "Legacy 'thresholds' format is no longer supported. "
                "Please use 'node_thresholds' format only. "
                "Convert your configuration file to the new format."
            )
        super().__init__(message)


class NodeNotFoundError(WorkflowConfigError):
    """
    指定されたノードIDが見つからない
    
    Attributes:
        node_id (str): 見つからなかったノードID
    """
    def __init__(self, node_id: str):
        super().__init__(f"Node ID '{node_id}' not found in configuration")
        self.node_id = node_id


class ConfigKeyError(WorkflowConfigError):
    """
    設定キーが見つからない
    
    指定されたノードに対して、要求された設定キーが存在しない場合に発生。
    デフォルト値の設定を促すメッセージを含みます。
    
    Attributes:
        node_id (str): ノードID
        key (str): 見つからなかった設定キー
        node_type (str): ノードタイプ（オプション）
    """
    def __init__(self, node_id: str, key: str, node_type: str = None):
        message = f"Setting '{key}' not found for node {node_id}."
        if node_type:
            message += (
                f"\n\nPlease check agent_settings/{node_type}/config.py "
                f"to ensure '{key}' is defined in DEFAULT_VALUES."
            )
        else:
            message += (
                "\n\nPlease ensure the setting is defined in the "
                "corresponding agent's config.py DEFAULT_VALUES."
            )
        super().__init__(message)
        self.node_id = node_id
        self.key = key
        self.node_type = node_type


class ThresholdValidationError(WorkflowConfigError):
    """
    閾値バリデーションエラー
    
    設定値が指定された範囲（min/max）や選択肢（options）の
    制約を満たさない場合に発生します。
    """
    def __init__(self, node_id: str, key: str, value, constraint_type: str, constraint_value):
        message = (
            f"Validation failed for node {node_id}.{key}: "
            f"value={value}, {constraint_type}={constraint_value}"
        )
        super().__init__(message)
        self.node_id = node_id
        self.key = key
        self.value = value
        self.constraint_type = constraint_type
        self.constraint_value = constraint_value