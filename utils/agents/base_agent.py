# utils/agents/base_agent.py
"""
全エージェントの共通基底クラス（新形式専用版）

このモジュールは、すべてのエージェント実装の基底クラスを提供します。
旧形式（thresholds）対応は完全に廃止され、新形式（node_thresholds）のみをサポートします。

主な機能:
- 設定値の取得（新形式専用）
- ログ出力の簡便メソッド
- 結果オブジェクトの生成
- ノード固有設定の管理
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from utils.log_manager import LogManager, LogLevel
from utils.node_threshold_manager import NodeThresholdManager
from utils.exceptions import ConfigKeyError


@dataclass
class AgentResult:
    """
    エージェント実行結果の統一フォーマット
    
    全エージェントは execute() メソッドでこのフォーマットの結果を返します。
    
    Attributes:
        confidence (float): 実行結果の信頼度（0.0-1.0、または負値）
        data (Dict[str, Any]): 結果データ（キー名はKeyRegistryに従う）
        status (str): 実行ステータス（"success", "error", "warning"）
        has_error (bool): エラー発生フラグ
        metadata (Optional[Dict]): メタデータ（オプション）
    """
    confidence: float
    data: Dict[str, Any]
    status: str  # "success", "error", "warning"
    has_error: bool
    metadata: Optional[Dict[str, Any]] = None


class BaseAgentExecutor(ABC):
    """
    全エージェントの共通基底クラス（新形式専用・旧形式対応完全削除版）
    
    このクラスを継承して、各エージェント固有の実行ロジックを実装します。
    設定管理、ログ出力、結果生成などの共通機能を提供します。
    """
    
    def __init__(
        self,
        agent_name: str,
        log_manager: LogManager,
        threshold_manager: NodeThresholdManager
    ):
        """
        基底クラスの初期化
        
        Args:
            agent_name: エージェント名（"analyzer", "retriever", etc.）
            log_manager: ログマネージャー
            threshold_manager: 閾値管理マネージャー（新形式専用）
        """
        self.name = agent_name
        self.log = log_manager
        self.thresholds = threshold_manager
        self._node_config = {
            "config": {},
            "node_id": "unknown"
        }
    
    @abstractmethod
    def execute(
        self,
        current_data: Dict[str, Any],
        node_id: Optional[str] = None,
        **kwargs
    ) -> AgentResult:
        """
        エージェント固有の実行処理（サブクラスで実装必須）
        
        Args:
            current_data: ワークフローの現在のデータ状態
            node_id: 実行するノードID
            **kwargs: 追加パラメータ
        
        Returns:
            AgentResult: 実行結果
        """
        pass
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        node_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        ログ出力の簡便メソッド（ノードID対応）
        
        Args:
            level: ログレベル
            message: ログメッセージ
            node_id: ノードID（指定すると "agent_name_node_id" 形式になる）
            **kwargs: 追加のログパラメータ
        """
        log_name = f"{self.name}_{node_id}" if node_id else self.name
        self.log.log(log_name, level, message, **kwargs)
    
    def _get_threshold(
        self,
        key: str,
        node_id: Optional[str] = None
    ) -> Any:
        """
        設定値取得の簡便メソッド（新形式専用・旧形式対応完全削除）
        
        このメソッドは NodeThresholdManager.get_value() のラッパーです。
        旧形式へのフォールバック処理は完全に削除されました。
        
        Args:
            key: 設定キー名
            node_id: ノードID（省略時は _node_config から取得）
        
        Returns:
            設定値（任意の型）
        
        Raises:
            ConfigKeyError: 設定キーが見つからない場合
        
        Example:
            >>> depth = self._get_threshold("analysis_depth", "1")
            >>> # 設定が存在しない場合は ConfigKeyError が発生
        """
        # ノードIDが指定されていない場合は _node_config から取得
        if node_id is None:
            node_id = self._node_config.get("node_id", "unknown")
        
        try:
            return self.thresholds.get_value(str(node_id), key)
        except ConfigKeyError as e:
            # 詳細なエラーメッセージでログ出力
            self._log(
                LogLevel.MINIMAL,
                f"設定キー '{key}' が見つかりません。"
                f"agent_settings/{self.name}/config.py の DEFAULT_VALUES を確認してください。",
                node_id
            )
            # 例外を再送出（呼び出し元でキャッチ可能）
            raise
    
    def _get_threshold_safe(
        self,
        key: str,
        default: Any = None,
        node_id: Optional[str] = None
    ) -> Any:
        """
        設定値取得（デフォルト値付き・例外を発生させない）
        
        設定が存在しない場合、例外を発生させずにデフォルト値を返します。
        オプション設定の取得に使用します。
        
        Args:
            key: 設定キー名
            default: デフォルト値（設定が存在しない場合に返される）
            node_id: ノードID
        
        Returns:
            設定値またはデフォルト値
        
        Example:
            >>> optional_param = self._get_threshold_safe("optional_key", default=0)
        """
        try:
            return self._get_threshold(key, node_id)
        except ConfigKeyError:
            # 設定が見つからない場合はデフォルト値を返す
            return default
    
    def _create_result(
        self,
        confidence: float,
        data: Dict[str, Any],
        has_error: bool = False,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        結果オブジェクト生成の簡便メソッド
        
        Args:
            confidence: 信頼度（0.0-1.0、または負値）
            data: 結果データ
            has_error: エラー発生フラグ
            status: 実行ステータス（"success", "error", "warning"）
            metadata: メタデータ（オプション）
        
        Returns:
            AgentResult: 結果オブジェクト
        """
        return AgentResult(
            confidence=confidence,
            data=data,
            has_error=has_error,
            status=status,
            metadata=metadata
        )
    
    def _create_error_result(
        self,
        error_message: str,
        node_id: Optional[str] = None,
        confidence: float = 0.0
    ) -> AgentResult:
        """
        エラー結果オブジェクトの生成
        
        Args:
            error_message: エラーメッセージ
            node_id: ノードID
            confidence: 信頼度（デフォルト: 0.0）
        
        Returns:
            AgentResult: エラー結果オブジェクト
        """
        self._log(LogLevel.MINIMAL, f"エラー発生: {error_message}", node_id)
        
        return AgentResult(
            confidence=confidence,
            data={"error": error_message},
            has_error=True,
            status="error",
            metadata={"node_id": node_id}
        )
    
    def set_node_config(self, node_config: Dict[str, Any], node_id: str) -> None:
        """
        ノード固有設定を設定
        
        このメソッドは WorkflowFactory から呼び出され、
        各エージェントインスタンスに固有のノード設定を注入します。
        
        Args:
            node_config: ノード固有の設定辞書
            node_id: ノードID
        """
        self._node_config = {
            "config": node_config,
            "node_id": str(node_id)
        }
    
    def _update_history(
        self,
        current_data: Dict[str, Any],
        record: Dict[str, Any],
        history_key: str
    ) -> list:
        """
        履歴更新の共通メソッド
        
        指定されたキーの履歴リストに新しいレコードを追加し、
        最新10件のみを保持します。
        
        Args:
            current_data: 現在のワークフローデータ
            record: 追加するレコード
            history_key: 履歴を保存するキー名
        
        Returns:
            更新された履歴リスト（最新10件）
        
        Example:
            >>> history = self._update_history(
            ...     current_data,
            ...     {"iteration": 1, "result": "success"},
            ...     "execution_history"
            ... )
        """
        history = current_data.get(history_key, [])
        
        if isinstance(history, list):
            history.append(record)
            return history[-10:]  # 最新10件を保持
        else:
            # 履歴が正しい形式でない場合は新規作成
            return [record]
    
    def _get_previous_iteration_data(
        self,
        current_data: Dict[str, Any],
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        前回実行時のデータを取得（ループバック対応）
        
        Router による再実行（ループバック）の際、
        前回の実行結果を取得して改善に活用します。
        
        Args:
            current_data: 現在のワークフローデータ
            node_id: ノードID
        
        Returns:
            前回の実行データ（存在しない場合はNone）
        """
        history_key = f"execution_history_{node_id}"
        history = current_data.get(history_key, [])
        
        if isinstance(history, list) and len(history) > 0:
            return history[-1]  # 最新の履歴を返す
        
        return None
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        node_id = self._node_config.get("node_id", "unknown")
        return f"{self.__class__.__name__}(name='{self.name}', node_id='{node_id}')"