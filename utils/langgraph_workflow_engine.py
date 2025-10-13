from typing import Dict, Any, List, Optional
from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from utils.log_manager import LogManager, LogLevel
from utils.node_threshold_manager import NodeThresholdManager
from pathlib import Path

# 並列実行対応マージ関数定義
def merge_dict(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """辞書のマージ処理（並列書き込み対応）"""
    result = left.copy() if left else {}
    if right:
        result.update(right)
    return result

def merge_list(left: List[str], right: List[str]) -> List[str]:
    """リストのマージ処理（並列書き込み対応）"""
    return (left or []) + (right or [])

def merge_str(left: str, right: str) -> str:
    """文字列のマージ処理（最新値優先）"""
    return right if right else (left or "")

def merge_int(left: int, right: int) -> int:
    """整数のマージ処理（最大値優先）"""
    return max(left or 0, right or 0)

class WorkflowState(TypedDict):
    """LangGraph 0.2.38完全準拠ワークフロー状態定義"""
    # 安全フィールド（単一書き込みのみ）
    user_input: str
    iteration_count: int
    
    # 並列競合解決フィールド（LangGraph仕様準拠）
    current_data: Annotated[Dict[str, Any], merge_dict]
    execution_log: Annotated[List[str], merge_list]
    node_results: Annotated[Dict[str, Any], merge_dict]
    parallel_results: Annotated[List[str], merge_list]
    node_history: Annotated[List[str], merge_list]
    last_key: Annotated[str, merge_str]
    error: Annotated[Optional[str], merge_str]

class LangGraphWorkflowEngine:
    """LangGraph 0.2.38完全対応ワークフローエンジン（並列・Router対応修正版）"""
    
    def __init__(self, agents: Dict[str, Any], log_manager: LogManager, 
                 threshold_manager: NodeThresholdManager, config_dict: Dict[str, Any]):
        self.agents = agents
        self.log_manager = log_manager
        self.threshold_manager = threshold_manager
        self.nodes = {node["id"]: node for node in config_dict.get("nodes", [])}
        self.connections = config_dict.get("connections", [])
        
        # VLM ModelManager初期化（VLMノードが存在する場合のみ）
        self.vlm_model_manager = None
        if self._has_vlm_node():
            self._initialize_vlm_model()
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """ワークフロー構築（並列・Router完全対応）"""
        workflow = StateGraph(WorkflowState)
        
        # 全ノード追加
        for node_id, node_config in self.nodes.items():
            node_type = node_config["type"]
            agent_key = f"{node_type}_{node_id}"
            
            if agent_key in self.agents:
                node_func = self._create_node_function(agent_key, str(node_id))
                workflow.add_node(f"node_{node_id}", node_func)
        
        # 接続構築（並列・Router完全対応）
        self._build_connections(workflow)
        return workflow.compile()
    
    def _create_node_function(self, agent_key: str, node_id: str):
        """ノード実行関数生成"""
        def node_function(state: WorkflowState) -> WorkflowState:
            return self._execute_node_agent_parallel_safe(agent_key, node_id, state)
        return node_function
    
    def _execute_node_agent_parallel_safe(self, agent_key: str, node_id: str, state: WorkflowState) -> WorkflowState:
        """並列実行完全対応版ノード実行"""
        # 入力データ作成
        input_data = {
            "user_input": state["user_input"],
            "iteration_count": state["iteration_count"]
        }
        
        # 既存データ追加
        if state.get("current_data"):
            input_data.update(state["current_data"])
        
        # エージェント実行
        agent = self.agents[agent_key]
        result = agent.execute(input_data, node_id=node_id)
        
        # 並列実行対応返却値構築
        return_data = {
            # 並列安全フィールドのみ返却（競合回避）
            "current_data": result.data,
            "parallel_results": [f"{agent_key}:実行完了:信頼度{result.confidence:.2f}"],
            "node_history": [f"{agent_key}"],
            "last_key": f"{agent_key}_result",
            "execution_log": [f"{agent_key}: {result.status}, 信頼度: {result.confidence:.2f}"],
            "node_results": {
                agent_key: {
                    "confidence": result.confidence,
                    "status": result.status,
                    "has_error": result.has_error,
                    "node_id": node_id
                }
            }
        }
        
        # エラー時のみerrorフィールドを設定
        if result.has_error:
            return_data["error"] = f"{agent_key}実行エラー"
        
        return return_data
    
    def _build_connections(self, workflow: StateGraph):
        """接続構築（並列・Router完全対応修正版）"""
        start_nodes = self._find_start_nodes()
        router_nodes = self._find_router_nodes()
        
        # 開始ノード接続
        for start_node in start_nodes:
            workflow.add_edge(START, f"node_{start_node}")
        
        # Router条件分岐処理
        for router_node in router_nodes:
            # Router発の条件分岐を設定
            router_targets = self._get_router_targets(router_node)
            
            if router_targets:
                # LangGraphが認識できるようにターゲット辞書をそのまま渡す
                workflow.add_conditional_edges(
                    f"node_{router_node}",
                    self._create_router_condition_function(router_node),
                    router_targets  # 直接辞書を渡す
                )
        
        # 通常の接続処理（並列対応修正）
        processed_connections = set()
        
        for conn in self.connections:
            from_node = conn['from']
            to_node = conn['to']
            connection_key = (from_node, to_node)
            
            # Router発の接続はスキップ（既に条件分岐で処理済み）
            if from_node in router_nodes:
                continue
                
            # 重複接続の回避
            if connection_key in processed_connections:
                continue
                
            # 通常の接続を追加
            workflow.add_edge(f"node_{from_node}", f"node_{to_node}")
            processed_connections.add(connection_key)
        
        # 終了ノード接続（Router以外）
        end_nodes = self._find_end_nodes()
        for end_node in end_nodes:
            if end_node not in router_nodes:
                workflow.add_edge(f"node_{end_node}", END)
    
    def _find_router_nodes(self) -> List[int]:
        """Routerノードを特定"""
        router_nodes = []
        for node_id, node_config in self.nodes.items():
            if node_config.get("type") == "router":
                router_nodes.append(node_id)
        return router_nodes
    
    def _get_router_targets(self, router_node_id: int) -> Dict[str, str]:
        """Router条件マッピング取得"""
        targets = {}
        
        # Router発の接続を取得
        for conn in self.connections:
            if conn.get('from') == router_node_id:
                condition = conn.get('condition', 'default')
                target_node = conn.get('to')
                targets[condition] = f"node_{target_node}"
        
        # 終了条件の追加
        if not targets:
            targets['default'] = END
        
        return targets
    
    def _create_router_condition_function(self, router_node_id: int):
        """Router条件判定関数生成"""
        def router_condition(state: WorkflowState) -> str:
            # Router実行結果から条件を取得
            current_data = state.get("current_data", {})
            router_decision = current_data.get(f"router_decision_{router_node_id}", "default")
            
            # Router設定から条件マッピングを取得
            targets = self._get_router_targets(router_node_id)
            
            # router_decisionがtargetsのキーに存在する場合、そのキーを返す
            if router_decision in targets:
                return router_decision
            
            # デフォルトフォールバック
            return "default" if "default" in targets else list(targets.keys())[0] if targets else "default"
        
        return router_condition
    
    def execute(self, user_input: str, initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """ワークフロー実行（完全クリーンスタート）"""
        # 新規実行時に既存データを完全クリア
        self.log_manager.log(
            "langgraph_workflow_engine", 
            LogLevel.MINIMAL, 
            f"ワークフロー新規実行開始 - 既存状態をクリア: {user_input[:50]}..."
        )
        
        # 完全に新しい初期状態を生成（古いexpertデータの混入を防止）
        state = WorkflowState(
            user_input=user_input,
            current_data=initial_state.copy() if initial_state else {},  # initial_stateがあればマージ
            execution_log=[],
            node_results={},
            iteration_count=1,
            error=None,
            # 並列実行用フィールド初期化
            parallel_results=[],
            node_history=[],
            last_key=""
        )
        
        # 実行前のデバッグログ
        self.log_manager.log(
            "langgraph_workflow_engine", 
            LogLevel.VERBOSE, 
            f"初期状態設定完了 - current_data: {state['current_data']}"
        )
        
        final_state = self.workflow.invoke(state)
        return self._format_result(final_state)
    
    def _format_result(self, final_state: WorkflowState) -> Dict[str, Any]:
        """結果フォーマット（DomainExpert最終回答対応版）"""
        
        # 最終ノードの特定とDomainExpert回答の抽出
        final_answer = self._extract_final_answer(final_state["current_data"])
        
        # 結果辞書の基本構造
        result = {
            # 新しい統一形式
            "refined_answer": final_answer,  # メインの回答（優先表示）
            "execution_summary": {
                "total_iterations": final_state["iteration_count"],
                "nodes_executed": list(final_state["node_results"].keys()),
                "processing_status": "completed" if not final_state.get("error") else "error",
                "final_node_type": self._get_final_node_type()
            },
            "workflow_metadata": {
                "router_decisions": self._extract_router_decisions(final_state["current_data"]),
                "parallel_execution_log": final_state.get("parallel_results", []),
                "node_history": final_state.get("node_history", [])
            },
            # 下位互換性のため（将来削除予定）
            "final_result": final_state["current_data"],
            "multi_agent_response": final_answer,
            "execution_log": final_state["execution_log"],
            "node_results": final_state["node_results"], 
            "current_data": final_state["current_data"],
            "has_error": bool(final_state.get("error")),
            "error_message": final_state.get("error"),
            "parallel_results": final_state.get("parallel_results", []),
            "node_history": final_state.get("node_history", [])
        }
        
        # VLM単体時はvlm_answerを追加
        from utils.key_registry import KeyRegistry
        if KeyRegistry.VLM_ANSWER in final_state["current_data"]:
            result["vlm_answer"] = final_state["current_data"][KeyRegistry.VLM_ANSWER]
        
        return result
    
    def _extract_router_decisions(self, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Router判定履歴を抽出"""
        decisions = []
        for key, value in current_data.items():
            if key.startswith("routing_metadata_"):
                decisions.append(value)
        return decisions
    
    def _extract_final_answer(self, current_data: Dict[str, Any]) -> str:
        """最終回答を抽出（Refiner優先、フォールバック対応）"""
        # 最終ノードを特定
        end_nodes = self._find_end_nodes()
        
        # PRIORITY 0: VLMノードの回答（VLM単体時）
        from utils.key_registry import KeyRegistry
        if KeyRegistry.VLM_ANSWER in current_data:
            for node_id in end_nodes:
                node_info = self.nodes.get(int(node_id), {})
                if node_info.get("type") == "vlm":
                    return current_data[KeyRegistry.VLM_ANSWER]
        
        # PRIORITY 1: Refinerの統合回答を最優先で探す
        for node_id in end_nodes:
            node_info = self.nodes.get(int(node_id), {})
            if node_info.get("type") == "refiner":
                # 新しい形式のRefined Answer
                if "refined_answer" in current_data:
                    return current_data["refined_answer"]
                    
                # ノード固有のRefined Answer
                if f"refined_answer_{node_id}" in current_data:
                    return current_data[f"refined_answer_{node_id}"]
                    
                # 旧フォーマット互換性
                if f"final_answer_{node_id}" in current_data:
                    return current_data[f"final_answer_{node_id}"]
                    
                if f"refined_response_{node_id}" in current_data:
                    return current_data[f"refined_response_{node_id}"]
        
        # PRIORITY 2: すべてのDomainExpertノードの詳細分析結果を収集（Refinerがない場合）
        domain_expert_analyses = []
        
        # 実行されたすべてのDomainExpertを検索
        for key, value in current_data.items():
            if key.startswith("analysis_") and isinstance(value, str) and value:
                node_id = key.split("_")[1]
                node_info = self.nodes.get(int(node_id), {})
                
                if node_info.get("type") == "domain_expert":
                    # DomainExpertの詳細データを収集
                    expert_data = self._collect_domain_expert_data(current_data, node_id)
                    if expert_data:
                        domain_expert_analyses.append(expert_data)
        
        # DomainExpertの分析結果が存在する場合
        if domain_expert_analyses:
            return self._format_multi_domain_expert_response(domain_expert_analyses)
        
        # PRIORITY 3: その他の最終ノードをチェック
        for node_id in end_nodes:
            
            # Analyzerの回答
            if f"optimized_query_{node_id}" in current_data:
                return current_data[f"optimized_query_{node_id}"]
                
            # 汎用的な分析結果
            if f"analysis_{node_id}" in current_data:
                return current_data[f"analysis_{node_id}"]
        
        # フォールバック: 任意の意味のある回答を探す
        for key, value in current_data.items():
            if isinstance(value, str) and len(value) > 50 and not key.startswith("error"):
                return value
        
        return "回答が生成されませんでした。"
    
    def _collect_domain_expert_data(self, current_data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """特定のDomainExpertノードの全データを収集"""
        expert_data = {}
        
        # 基本データ
        analysis_key = f"analysis_{node_id}"
        if analysis_key in current_data and current_data[analysis_key]:
            expert_data["answer"] = current_data[analysis_key]
        
        # 詳細データ
        facts_key = f"facts_{node_id}"
        if facts_key in current_data:
            expert_data["facts"] = current_data[facts_key]
        
        insights_key = f"insights_{node_id}"
        if insights_key in current_data:
            expert_data["insights"] = current_data[insights_key]
        
        recommendations_key = f"recommendations_{node_id}"
        if recommendations_key in current_data:
            expert_data["recommendations"] = current_data[recommendations_key]
        
        gaps_key = f"gaps_{node_id}"
        if gaps_key in current_data:
            expert_data["gaps"] = current_data[gaps_key]
        
        citations_key = f"citations_{node_id}"
        if citations_key in current_data:
            expert_data["citations"] = current_data[citations_key]
        
        confidence_key = f"confidence_{node_id}"
        if confidence_key in current_data:
            expert_data["confidence"] = current_data[confidence_key]
        
        # ノード情報
        node_info = self.nodes.get(int(node_id), {})
        node_config = node_info.get("config", {})
        expert_data["node_id"] = node_id
        
        # expertise_domainをthreshold_managerから取得
        try:
            expertise_domain = self.threshold_manager.get_value(node_id, "expertise_domain")
            expert_data["expertise_domain"] = expertise_domain if expertise_domain else "不明な専門分野"
        except:
            # フォールバック: node_configから取得を試行（{"value": "..."} 形式に対応）
            expertise_domain_config = node_config.get("expertise_domain", "不明な専門分野")
            if isinstance(expertise_domain_config, dict) and "value" in expertise_domain_config:
                expert_data["expertise_domain"] = expertise_domain_config["value"]
            else:
                expert_data["expertise_domain"] = expertise_domain_config
        
        return expert_data if expert_data.get("answer") else None
    
    def _format_multi_domain_expert_response(self, analyses: List[Dict[str, Any]]) -> str:
        """複数DomainExpertの分析結果を統合フォーマット"""
        if not analyses:
            return "DomainExpert分析結果がありません。"
        
        # ヘッダー
        response_parts = []
        if len(analyses) == 1:
            response_parts.append(f"# 専門分析結果（{analyses[0]['expertise_domain']}）\n")
        else:
            domains = [analysis['expertise_domain'] for analysis in analyses]
            response_parts.append(f"# 複合専門分析結果（{len(analyses)}専門分野: {', '.join(domains)}）\n")
        
        # 各DomainExpertの分析結果
        for i, analysis in enumerate(analyses, 1):
            if len(analyses) > 1:
                response_parts.append(f"\n## {i}. {analysis['expertise_domain']}専門家分析（ノードID: {analysis['node_id']}）\n")
            
            # 回答
            if analysis.get("answer"):
                response_parts.append(f"### 回答\n{analysis['answer']}\n")
            
            # 事実
            facts = analysis.get("facts", [])
            if facts:
                response_parts.append("### 主要な事実\n")
                for j, fact in enumerate(facts, 1):
                    if isinstance(fact, dict):
                        statement = fact.get("statement", str(fact))
                        cite_ids = fact.get("cite_ids", [])
                        if cite_ids:
                            response_parts.append(f"{j}. {statement} [引用: {', '.join(cite_ids)}]\n")
                        else:
                            response_parts.append(f"{j}. {statement}\n")
                    else:
                        response_parts.append(f"{j}. {fact}\n")
                response_parts.append("\n")
            
            # 洞察
            insights = analysis.get("insights", [])
            if insights:
                response_parts.append("### 技術的洞察\n")
                for j, insight in enumerate(insights, 1):
                    response_parts.append(f"{j}. {insight}\n")
                response_parts.append("\n")
            
            # 推奨事項
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                response_parts.append("### 推奨事項\n")
                for j, rec in enumerate(recommendations, 1):
                    response_parts.append(f"{j}. {rec}\n")
                response_parts.append("\n")
            
            # 不足情報
            gaps = analysis.get("gaps", [])
            if gaps:
                response_parts.append("### 不足している情報\n")
                for j, gap in enumerate(gaps, 1):
                    response_parts.append(f"{j}. {gap}\n")
                response_parts.append("\n")
            
            # 引用情報
            citations = analysis.get("citations", [])
            if citations:
                response_parts.append("### 引用情報\n")
                for j, citation in enumerate(citations, 1):
                    if isinstance(citation, dict):
                        cite_id = citation.get("id", "不明")
                        source = citation.get("source", "不明")
                        score = citation.get("score", 0.0)
                        response_parts.append(f"{j}. {cite_id} (出典: {source}, スコア: {score:.3f})\n")
                    else:
                        response_parts.append(f"{j}. {citation}\n")
                response_parts.append("\n")
            
            # 信頼度
            confidence = analysis.get("confidence")
            if confidence is not None:
                response_parts.append(f"**信頼度:** {confidence:.3f}\n")
            
            # 分析間の区切り
            if i < len(analyses):
                response_parts.append("\n" + "="*50 + "\n")
        
        return "".join(response_parts)
    
    def _get_final_node_type(self) -> str:
        """最終ノードのタイプを取得"""
        end_nodes = self._find_end_nodes()
        if end_nodes:
            final_node = end_nodes[0]  # 最初の最終ノード
            return self.nodes.get(final_node, {}).get("type", "unknown")
        return "unknown"
    
    def _find_start_nodes(self) -> List[int]:
        """開始ノード特定"""
        all_nodes = set(self.nodes.keys())
        target_nodes = set(conn["to"] for conn in self.connections)
        return list(all_nodes - target_nodes) or [min(self.nodes.keys())]
    
    def _find_end_nodes(self) -> List[int]:
        """終了ノード特定"""
        all_nodes = set(self.nodes.keys())
        source_nodes = set(conn["from"] for conn in self.connections)
        end_candidates = list(all_nodes - source_nodes)
        
        # Routerノードは除外
        router_nodes = self._find_router_nodes()
        return [node for node in end_candidates if node not in router_nodes] or [max(self.nodes.keys())]
    
    def _has_vlm_node(self) -> bool:
        """ワークフローにVLMノードが存在するかチェック"""
        for node_config in self.nodes.values():
            if node_config.get("type") == "vlm":
                return True
        return False
    
    def _initialize_vlm_model(self):
        """VLM ModelManagerを初期化（ワークフロー開始時に1回だけ）"""
        try:
            self.log_manager.log("vlm", LogLevel.MINIMAL, "VLM ModelManager初期化開始")
            
            # vlm.model_managerをインポート
            from vlm.model_manager import ModelManager
            
            # ModelManagerインスタンス作成
            model_path = Path("./vlm/SAIL-VL2-2B")
            self.vlm_model_manager = ModelManager(model_path=str(model_path))
            
            # モデルセットアップ
            def progress_callback(msg: str):
                self.log_manager.log("vlm", LogLevel.VERBOSE, f"  {msg}")
            
            success = self.vlm_model_manager.setup_model(progress_callback=progress_callback)
            
            if success:
                # デバイス情報取得
                device_info = self.vlm_model_manager.get_device_info()
                if device_info["cuda_available"]:
                    self.log_manager.log("vlm", LogLevel.MINIMAL, 
                        f"VLM初期化完了: {device_info['gpu_name']} "
                        f"(VRAM: {device_info['gpu_memory_allocated']:.1f}GB / {device_info['gpu_memory_total']:.1f}GB)")
                else:
                    self.log_manager.log("vlm", LogLevel.MINIMAL, "VLM初期化完了: CPU")
                
                # VLMエージェントにModelManagerを設定
                for agent_key, agent in self.agents.items():
                    if agent_key.startswith("vlm_"):
                        agent.set_model_manager(self.vlm_model_manager)
                        self.log_manager.log("vlm", LogLevel.VERBOSE, f"{agent_key}にModelManager設定完了")
            else:
                self.log_manager.log("vlm", LogLevel.MINIMAL, "警告: VLM初期化に失敗しました")
                self.vlm_model_manager = None
        
        except Exception as e:
            self.log_manager.log("vlm", LogLevel.MINIMAL, f"VLM初期化エラー: {e}")
            self.vlm_model_manager = None
            import traceback
            self.log_manager.log("vlm", LogLevel.VERBOSE, traceback.format_exc())