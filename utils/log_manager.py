# utils/log_manager.py
from typing import Dict, Any, Optional
from enum import IntEnum
import logging
from datetime import datetime

class LogLevel(IntEnum):
    """ログレベル定義"""
    MINIMAL = 1
    VERBOSE = 5

class LogManager:
    """2段階ログレベル対応、エージェント別制御"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """ログ設定を初期化（新形式node_specific_levels対応）"""
        log_config = config_dict.get("logging", {})
        # デフォルトレベルは廃止（明示設定がない場合は出力しない）
        self._default_level = None
        
        # 新形式: node_specific_levels対応
        node_levels = log_config.get("node_specific_levels", {})
        agent_levels = log_config.get("agent_specific_levels", {})  # 旧形式互換
        
        self._agent_levels = self._parse_node_levels(config_dict, node_levels, agent_levels)
        self._max_length = log_config.get("max_message_length", {}).get("value", 500)
        self._truncate = log_config.get("truncate_long_content", True)
        self._setup_logger()
    
    def _parse_node_levels(self, config_dict: Dict[str, Any], node_levels: Dict[str, str], agent_levels: Dict[str, str]) -> Dict[str, LogLevel]:
        """ノード別ログレベルを解析（新形式対応）"""
        result = {}
        
        # 旧形式の agent_specific_levels
        for agent, level in agent_levels.items():
            result[agent] = LogLevel[level]
        
        # 新形式の node_specific_levels
        # 実際のノード情報を使用して正確にマッピング
        nodes = config_dict.get("nodes", [])
        for node in nodes:
            node_id = str(node.get("id"))
            node_type = node.get("type")
            
            if node_id in node_levels:
                agent_key = f"{node_type}_{node_id}"
                result[agent_key] = LogLevel[node_levels[node_id]]
        
        return result
    
    def _setup_logger(self) -> None:
        """ロガーを設定"""
        self._logger = logging.getLogger("MultiAgentRAG")
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def should_log(self, agent: str, target_level: LogLevel) -> bool:
        """指定レベルでログ出力すべきかを判定"""
        agent_level = self._agent_levels.get(agent)
        if agent_level is None:
            return False
        return target_level <= agent_level
    
    def log(self, agent: str, level: LogLevel, message: str, **kwargs) -> None:
        """エージェント別ログ出力（GUI統合版）"""
        # レベルの型チェックと変換
        if isinstance(level, str):
            # 文字列の場合はLogLevelに変換
            level_map = {
                "MINIMAL": LogLevel.MINIMAL,
                "INFO": LogLevel.MINIMAL,  # INFOはMINIMALとして扱う
                "VERBOSE": LogLevel.VERBOSE,
                "DEBUG": LogLevel.VERBOSE   # DEBUGはVERBOSEとして扱う
            }
            level = level_map.get(level, LogLevel.MINIMAL)
        
        if not self.should_log(agent, level):
            return
        
        # VERBOSEレベルでは切り詰めを完全に無効化
        if level == LogLevel.VERBOSE:
            full_message = f"[{agent}] {message}"
        else:
            # 通常レベルでは切り詰め処理
            if self._truncate and len(message) > self._max_length:
                message = message[:self._max_length] + "..."
            full_message = f"[{agent}] {message}"
        
        if kwargs:
            full_message += f" | {kwargs}"
        
        # 標準ログ出力（ERRORレベルは実際のエラー時のみ使用）
        if level <= LogLevel.MINIMAL:
            self._logger.info(full_message)  # MINIMALはINFOレベル
        else:
            self._logger.info(full_message)  # VERBOSEもINFOレベル
        
        # GUI統合出力（WorkflowWorkerがある場合）
        if hasattr(self, '_gui_callback') and self._gui_callback:
            self._gui_callback(full_message)

    def set_gui_callback(self, callback_func):
        """GUI出力コールバック設定"""
        self._gui_callback = callback_func
    
    def set_agent_level(self, agent: str, level: LogLevel) -> None:
        """エージェントのログレベルを動的変更"""
        self._agent_levels[agent] = level
