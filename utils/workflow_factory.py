# utils/workflow_factory.py
"""
ワークフローファクトリー

設計辞書（JSON）からLangGraphワークフローエンジンを動的に構築します。
CodeGeneratorは削除され、サポートされるノードタイプは以下の6種類です：
- analyzer: クエリ分析・最適化
- retriever: ベクトル検索
- domain_expert: 専門分析
- validator: 信頼度検証
- router: 条件分岐
- refiner: 統合・整形
"""

from typing import Dict, Any
from .langgraph_workflow_engine import LangGraphWorkflowEngine
from .log_manager import LogManager
from .node_threshold_manager import NodeThresholdManager
from utils.agents.analyzer_executor import AnalyzerExecutor
from utils.agents.retriever_executor import RetrieverExecutor
from utils.agents.domain_expert_executor import DomainExpertExecutor
from utils.agents.validator_executor import ValidatorExecutor
from utils.agents.refiner_executor import RefinerExecutor
from utils.agents.router_executor import RouterExecutor
from utils.agents.vlm_executor import VLMExecutor


class WorkflowFactory:
    """
    完全動的ワークフローファクトリー
    
    設計辞書からワークフローエンジンを構築し、
    ノードタイプに応じたエージェントインスタンスを生成します。
    """
    
    # サポートされるノードタイプとエージェントクラスのマッピング
    SUPPORTED_NODE_TYPES = {
        "analyzer": AnalyzerExecutor,
        "retriever": RetrieverExecutor,
        "domain_expert": DomainExpertExecutor,
        "validator": ValidatorExecutor,
        "refiner": RefinerExecutor,
        "router": RouterExecutor,
        "vlm": VLMExecutor
    }
    
    @staticmethod
    def create_workflow_engine(
        config_dict: Dict[str, Any],
        llm_manager,
        vector_manager
    ) -> LangGraphWorkflowEngine:
        """
        設計辞書からワークフローエンジンを構築
        
        Args:
            config_dict: 設計辞書（nodes, connections, node_thresholds, logging を含む）
            llm_manager: LLM管理インスタンス
            vector_manager: ベクトルDB管理インスタンス
        
        Returns:
            LangGraphWorkflowEngine: 構築されたワークフローエンジン
        
        Raises:
            ValueError: サポートされていないノードタイプが含まれている場合
        """
        # 管理インスタンス生成
        log_manager = LogManager(config_dict)
        threshold_manager = NodeThresholdManager(config_dict)
        
        # ノードID別エージェントインスタンス生成
        agent_instances = WorkflowFactory._create_node_specific_agents(
            config_dict,
            log_manager,
            threshold_manager,
            llm_manager,
            vector_manager
        )
        
        # ワークフローエンジン生成
        return LangGraphWorkflowEngine(
            agent_instances,
            log_manager,
            threshold_manager,
            config_dict
        )
    
    @staticmethod
    def _create_node_specific_agents(
        config_dict: Dict[str, Any],
        log_manager: LogManager,
        threshold_manager: NodeThresholdManager,
        llm_manager,
        vector_manager
    ) -> Dict[str, Any]:
        """
        ノードID別エージェントインスタンス生成
        
        Args:
            config_dict: 設計辞書
            log_manager: ログ管理インスタンス
            threshold_manager: 閾値管理インスタンス
            llm_manager: LLM管理インスタンス
            vector_manager: ベクトルDB管理インスタンス
        
        Returns:
            Dict[str, Any]: エージェントインスタンスの辞書（キー: "{node_type}_{node_id}"）
        
        Raises:
            ValueError: サポートされていないノードタイプが含まれている場合
        """
        agent_instances = {}
        nodes = config_dict.get("nodes", [])
        
        for node in nodes:
            node_type = node.get("type")
            node_id = str(node.get("id"))
            node_config = node.get("config", {})
            
            # サポートされていないノードタイプの検出
            if node_type not in WorkflowFactory.SUPPORTED_NODE_TYPES:
                raise ValueError(
                    f"Unsupported node type '{node_type}' at node ID {node_id}. "
                    f"Supported types: {list(WorkflowFactory.SUPPORTED_NODE_TYPES.keys())}"
                )
            
            # エージェントクラスを取得
            agent_class = WorkflowFactory.SUPPORTED_NODE_TYPES[node_type]
            
            # エージェントインスタンス生成（ノードタイプ別の初期化）
            agent_instance = WorkflowFactory._create_agent_instance(
                agent_class,
                node_type,
                log_manager,
                threshold_manager,
                llm_manager,
                vector_manager
            )
            
            # ノード固有設定を適用
            agent_instance.set_node_config(node_config, node_id)
            
            # エージェントキー生成とインスタンス登録
            agent_key = f"{node_type}_{node_id}"
            agent_instances[agent_key] = agent_instance
        
        return agent_instances
    
    @staticmethod
    def _create_agent_instance(
        agent_class,
        node_type: str,
        log_manager: LogManager,
        threshold_manager: NodeThresholdManager,
        llm_manager,
        vector_manager
    ):
        """
        エージェントインスタンスを生成
        
        Args:
            agent_class: エージェントクラス
            node_type: ノードタイプ
            log_manager: ログ管理インスタンス
            threshold_manager: 閾値管理インスタンス
            llm_manager: LLM管理インスタンス
            vector_manager: ベクトルDB管理インスタンス
        
        Returns:
            エージェントインスタンス
        """
        # Retrieverは vector_manager を必要とする
        if node_type == "retriever":
            return agent_class(log_manager, threshold_manager, vector_manager)
        
        # VLMは model_manager を必要とする（後でワークフローエンジンで設定）
        elif node_type == "vlm":
            return agent_class(log_manager, threshold_manager, model_manager=None)
        
        # その他のエージェント（analyzer, domain_expert, validator, refiner, router）は
        # llm_manager を必要とする
        else:
            return agent_class(log_manager, threshold_manager, llm_manager)
    
    @staticmethod
    def validate_workflow_config(config_dict: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        ワークフロー設計辞書を検証
        
        Args:
            config_dict: 設計辞書
        
        Returns:
            tuple[bool, list[str]]: (検証成功フラグ, エラーメッセージリスト)
        """
        errors = []
        
        # 必須フィールドの確認
        if "nodes" not in config_dict:
            errors.append("Missing 'nodes' field in config")
        if "connections" not in config_dict:
            errors.append("Missing 'connections' field in config")
        if "node_thresholds" not in config_dict:
            errors.append("Missing 'node_thresholds' field in config")
        
        if errors:
            return False, errors
        
        # ノードの検証
        nodes = config_dict.get("nodes", [])
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            
            if node_id is None:
                errors.append(f"Node missing 'id' field: {node}")
                continue
            
            if node_type is None:
                errors.append(f"Node {node_id} missing 'type' field")
                continue
            
            # サポートされていないノードタイプの検出
            if node_type not in WorkflowFactory.SUPPORTED_NODE_TYPES:
                errors.append(
                    f"Unsupported node type '{node_type}' at node {node_id}. "
                    f"Supported: {list(WorkflowFactory.SUPPORTED_NODE_TYPES.keys())}"
                )
        
        # 接続の検証
        connections = config_dict.get("connections", [])
        node_ids = {node.get("id") for node in nodes}
        
        for conn in connections:
            from_node = conn.get("from")
            to_node = conn.get("to")
            
            if from_node not in node_ids:
                errors.append(f"Connection references non-existent 'from' node: {from_node}")
            
            if to_node not in node_ids:
                errors.append(f"Connection references non-existent 'to' node: {to_node}")
        
        return len(errors) == 0, errors