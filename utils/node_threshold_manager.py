# utils/node_threshold_manager.py
"""
ノード個別設定対応閾値管理システム（新形式専用・デフォルト値自動適用版）

このモジュールは、ワークフロー設定の新形式（node_thresholds）専用の
管理システムを提供します。旧形式（thresholds）は完全に廃止されています。

主な機能:
- ノード個別設定の管理
- デフォルト値の自動適用
- 設定値のバリデーション
- 動的な設定変更のサポート
"""

from typing import Dict, Any, Union, Optional
from dataclasses import dataclass
from utils.exceptions import (
    LegacyFormatError,
    NodeNotFoundError,
    ConfigKeyError,
    ThresholdValidationError
)


@dataclass
class ThresholdConfig:
    """
    閾値設定データクラス
    
    Attributes:
        value: 設定値（任意の型）
        min: 最小値制約（数値型の場合）
        max: 最大値制約（数値型の場合）
        options: 選択肢リスト（列挙型の場合）
        description: 設定の説明文
    """
    value: Union[str, int, float, bool, dict, list]
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    options: Optional[list] = None
    description: Optional[str] = None


class NodeThresholdManager:
    """
    ノード個別設定対応閾値管理システム（新形式専用）
    
    このクラスは、各ノードの設定値を管理し、デフォルト値の自動適用、
    バリデーション、動的な設定変更をサポートします。
    
    旧形式（thresholds）は完全に廃止され、新形式（node_thresholds）のみをサポートします。
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        設定辞書からノード個別閾値管理を初期化
        
        Args:
            config_dict: 設計辞書（nodes, node_thresholds を含む）
        
        Raises:
            LegacyFormatError: 旧形式（thresholds）が検出された場合
        """
        self._config_dict = config_dict
        
        # 旧形式を検出したら即エラー（後方互換性なし）
        if "thresholds" in config_dict and "node_thresholds" not in config_dict:
            raise LegacyFormatError(
                "Legacy 'thresholds' format detected in configuration. "
                "This format is no longer supported. "
                "Please convert your configuration to use 'node_thresholds' format. "
                "Refer to the documentation for migration instructions."
            )
        
        # 新形式の読み込みとデフォルト値の自動適用
        self._node_thresholds = self._load_with_defaults(
            config_dict.get("node_thresholds", {})
        )
        
        # 全設定の妥当性を検証
        self._validate_all_thresholds()
    
    def _load_with_defaults(self, node_thresholds: Dict) -> Dict[str, Dict[str, ThresholdConfig]]:
        """
        ノード設定にデフォルト値を自動適用
        
        各ノードに対して、エージェントタイプ別のデフォルト設定を適用し、
        ユーザー設定で上書きします。
        
        Args:
            node_thresholds: ユーザー設定のnode_thresholds辞書
        
        Returns:
            デフォルト値とユーザー設定をマージした完全な設定辞書
        """
        result = {}
        
        for node in self._config_dict.get("nodes", []):
            node_id = str(node["id"])
            node_type = node["type"]
            
            # エージェントタイプ別のデフォルト設定をロード
            defaults = self._get_defaults_for_type(node_type)
            
            # ユーザー設定で上書き（デフォルト < ユーザー設定の優先順位）
            user_config = node_thresholds.get(node_id, {})
            merged = {**defaults, **user_config}
            
            # ThresholdConfigオブジェクトに変換
            result[node_id] = {}
            for key, config_value in merged.items():
                if isinstance(config_value, dict) and "value" in config_value:
                    # {"value": ..., "min": ..., "max": ..., ...} 形式
                    result[node_id][key] = ThresholdConfig(**config_value)
                else:
                    # 直接値の場合（後方互換性のため）
                    result[node_id][key] = ThresholdConfig(value=config_value)
        
        return result
    
    def _get_defaults_for_type(self, node_type: str) -> Dict[str, Any]:
        """
        エージェントタイプ別デフォルト値を取得
        
        agent_designer.ui.agent_settings から各エージェントタイプの
        デフォルト設定を動的に読み込みます。
        
        Args:
            node_type: "analyzer", "retriever", "domain_expert", etc.
        
        Returns:
            デフォルト設定の辞書（{"value": ...} 形式に変換済み）
        """
        import sys
        from pathlib import Path
        
        # agent_designer.ui.agent_settings をインポートパスに追加
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            from agent_designer.ui.agent_settings import get_default_node_config
            defaults = get_default_node_config(node_type)
            
            print(f"[DEBUG] ノードタイプ '{node_type}' のデフォルト値取得成功: {len(defaults)} 項目")
            print(f"[DEBUG] デフォルト値のキー: {list(defaults.keys())}")
            
            # {"value": ...} 形式に変換
            return {
                key: {"value": value} if not isinstance(value, dict) else value
                for key, value in defaults.items()
            }
        except ImportError as e:
            # agent_settingsが見つからない場合は空辞書（フォールバック）
            print(f"[DEBUG] ImportError for node_type '{node_type}': {e}")
            return {}
        except Exception as e:
            # その他のエラーも空辞書で処理
            print(f"[DEBUG] Exception for node_type '{node_type}': {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        システム全体の設定を取得
        
        Returns:
            完全な設定辞書
        """
        return self._config_dict
    
    def get_value(self, node_id: str, key: str) -> Union[str, int, float, bool, dict, list]:
        """
        指定ノードの設定値を取得
        
        Args:
            node_id: ノードID
            key: 設定キー
        
        Returns:
            設定値
        
        Raises:
            NodeNotFoundError: ノードIDが存在しない
            ConfigKeyError: 設定キーが存在しない
        """
        node_id = str(node_id)
        
        if node_id not in self._node_thresholds:
            raise NodeNotFoundError(node_id)
        
        if key not in self._node_thresholds[node_id]:
            node_type = self._get_node_type(node_id)
            raise ConfigKeyError(node_id, key, node_type)
        
        return self._node_thresholds[node_id][key].value
    
    def _get_node_type(self, node_id: str) -> Optional[str]:
        """
        指定ノードのタイプを取得
        
        Args:
            node_id: ノードID
        
        Returns:
            ノードタイプ（見つからない場合はNone）
        """
        for node in self._config_dict.get("nodes", []):
            if str(node.get("id")) == str(node_id):
                return node.get("type")
        return None
    
    def set_value(self, node_id: str, key: str, value: Any) -> bool:
        """
        閾値を動的に変更
        
        Args:
            node_id: ノードID
            key: 設定キー
            value: 新しい値
        
        Returns:
            成功した場合True、バリデーション失敗の場合False
        
        Raises:
            ThresholdValidationError: 値が制約を満たさない場合
        """
        node_id = str(node_id)
        if node_id not in self._node_thresholds:
            self._node_thresholds[node_id] = {}
        
        if key not in self._node_thresholds[node_id]:
            # 新しいキーの場合
            self._node_thresholds[node_id][key] = ThresholdConfig(value=value)
        else:
            # 既存キーの更新（バリデーション付き）
            config = self._node_thresholds[node_id][key]
            validation_result = self._validate_value(value, config)
            if validation_result is not True:
                constraint_type, constraint_value = validation_result
                raise ThresholdValidationError(
                    node_id, key, value, constraint_type, constraint_value
                )
            config.value = value
        
        return True
    
    def _validate_value(self, value: Any, config: ThresholdConfig) -> Union[bool, tuple]:
        """
        値の妥当性を検証
        
        Args:
            value: 検証する値
            config: 設定オブジェクト
        
        Returns:
            True（成功）または (constraint_type, constraint_value) タプル（失敗）
        """
        # 最小値チェック
        if isinstance(value, (int, float)) and config.min is not None:
            if value < config.min:
                return ("min", config.min)
        
        # 最大値チェック
        if isinstance(value, (int, float)) and config.max is not None:
            if value > config.max:
                return ("max", config.max)
        
        # 選択肢チェック
        if config.options is not None and value not in config.options:
            return ("options", config.options)
        
        return True
    
    def _validate_all_thresholds(self):
        """
        全閾値の妥当性を検証
        
        Raises:
            ThresholdValidationError: 不正な設定値が見つかった場合
        """
        for node_id, node_settings in self._node_thresholds.items():
            for key, config in node_settings.items():
                validation_result = self._validate_value(config.value, config)
                if validation_result is not True:
                    constraint_type, constraint_value = validation_result
                    raise ThresholdValidationError(
                        node_id, key, config.value, constraint_type, constraint_value
                    )
    
    def has_node_config(self, node_id: str) -> bool:
        """
        指定ノードに設定があるかチェック
        
        Args:
            node_id: ノードID
        
        Returns:
            設定が存在する場合True
        """
        return str(node_id) in self._node_thresholds
    
    def get_node_config(self, node_id: str) -> Dict[str, Any]:
        """
        指定ノードの全設定を取得
        
        Args:
            node_id: ノードID
        
        Returns:
            ノードの全設定辞書（キー: 値のペア）
        """
        node_id = str(node_id)
        if node_id not in self._node_thresholds:
            return {}
        
        return {key: config.value for key, config in self._node_thresholds[node_id].items()}
    
    def get_all_node_ids(self) -> list:
        """
        設定されているノードIDの一覧を取得
        
        Returns:
            ノードIDのリスト
        """
        return list(self._node_thresholds.keys())
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        現在の設定を辞書形式でエクスポート
        
        JSONシリアライズ可能な形式で全設定をエクスポートします。
        
        Returns:
            設定辞書（node_thresholds形式）
        """
        result = {}
        for node_id, node_settings in self._node_thresholds.items():
            result[node_id] = {}
            for key, config in node_settings.items():
                # 制約情報がある場合は完全な設定を含める
                if config.min is not None or config.max is not None or config.options is not None:
                    result[node_id][key] = {
                        "value": config.value,
                        "min": config.min,
                        "max": config.max,
                        "options": config.options,
                        "description": config.description
                    }
                    # None値を除去してクリーンな辞書に
                    result[node_id][key] = {
                        k: v for k, v in result[node_id][key].items() if v is not None
                    }
                else:
                    # 単純な値のみの場合
                    result[node_id][key] = {"value": config.value}
        return result
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        node_count = len(self._node_thresholds)
        return f"NodeThresholdManager(nodes={node_count}, ids={list(self._node_thresholds.keys())})"