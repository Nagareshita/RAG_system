# utils/agents/router_executor.py
"""
Router Executor - 条件分岐エージェント(完全版)

KeyRegistry統合版。旧形式のキーは一切サポートしません。
全機能を保持し、KeyRegistry対応のみを追加した完全版です。
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry


class RouterExecutor(BaseAgentExecutor):
    """JSON駆動型条件分岐Router(KeyRegistry完全対応)"""
    
    def __init__(self, log_manager, threshold_manager, llm_manager=None):
        super().__init__("router", log_manager, threshold_manager)
        self._node_type_mapping = self._build_node_type_mapping()
    
    def _build_node_type_mapping(self) -> Dict[str, str]:
        """JSON設定からノードID→タイプのマッピングを構築"""
        try:
            system_config = self.thresholds.get_system_config()
            nodes = system_config.get("nodes", [])
            
            mapping = {}
            for node in nodes:
                node_id = str(node.get("id", ""))
                node_type = node.get("type", "")
                if node_id and node_type:
                    mapping[node_id] = node_type
            
            self._log(LogLevel.VERBOSE, f"ノードマッピング構築: {mapping}")
            return mapping
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"ノードマッピング構築エラー: {str(e)}")
            return {}
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """条件分岐判定実行"""
        try:
            node_id = node_id or "router"
            # ノードID付きで設定を取得
            routing_rules = self._get_threshold("routing_rules", node_id=node_id)
            max_iterations = self._get_threshold("max_iterations", node_id=node_id)

            self._log(LogLevel.MINIMAL, "Router分岐判定開始", node_id)

            execution_count = current_data.get("execution_count", 0)
            execution_history = current_data.get("execution_history", [])

            # max_iterations超過判定
            if max_iterations is not None and execution_count >= max_iterations:
                # max_iterations_exceededルートを探す
                exceeded_route = None
                if isinstance(routing_rules, list):
                    for route in routing_rules:
                        if route.get("condition") == "max_iterations_exceeded":
                            exceeded_route = route
                            break
                elif isinstance(routing_rules, dict):
                    exceeded_route = routing_rules.get("max_iterations_exceeded")
                if exceeded_route:
                    route_name = exceeded_route.get("condition", "max_iterations_exceeded")
                    target_node = str(exceeded_route.get("condition_details", {}).get("target_node", ""))
                    decision_key = KeyRegistry.get_key_name("router", "router_decision", node_id)
                    target_key = KeyRegistry.get_key_name("router", "target_node", node_id)
                    metadata_key = KeyRegistry.get_key_name("router", "routing_metadata", node_id)
                    output_data = {
                        decision_key: route_name,
                        target_key: target_node,
                        metadata_key: {
                            "route_name": route_name,
                            "execution_count": execution_count,
                            "conditions_matched": 0
                        },
                        "execution_count": execution_count,
                        "execution_history": execution_history,
                        "next_node": target_node
                    }
                    self._log(LogLevel.MINIMAL, f"max_iterations超過: {execution_count}/{max_iterations} → {route_name} → Node {target_node}", node_id)
                    return self._create_result(
                        confidence=1.0,
                        data=output_data
                    )
                else:
                    self._log(LogLevel.MINIMAL, f"max_iterations超過だがmax_iterations_exceededルートが未定義", node_id)
                    # fallback: デフォルトルート
                    pass
            # VERBOSEレベル時のみ詳細状況ログ
            if hasattr(self.log, '_agent_levels') and self.log._agent_levels.get('router') == LogLevel.VERBOSE:
                self._log(LogLevel.VERBOSE, f"現在の実行回数: {execution_count}/{max_iterations}", node_id)
                self._log(LogLevel.VERBOSE, f"実行履歴件数: {len(execution_history)}", node_id)


            # routing_rulesがdictの場合はconnections構造に合わせてroute dictを生成
            if isinstance(routing_rules, dict):
                routing_rules = []
                system_config = self.thresholds.get_system_config()
                connections = system_config.get("connections", [])
                for conn in connections:
                    if str(conn.get("from")) == str(node_id):
                        routing_rules.append(conn)

            # ルーティングルール評価
            for route in routing_rules:
                route_name = route.get("condition", "unnamed")
                target_node = str(route.get("condition_details", {}).get("target_node", ""))
                conditions = route.get("condition_details", {}).get("checks", [])
                custom_expression = route.get("condition_details", {}).get("custom_expression", "")

                # VERBOSE: ルート情報
                if hasattr(self.log, '_agent_levels') and self.log._agent_levels.get('router') == LogLevel.VERBOSE:
                    self._log(LogLevel.VERBOSE, f"ルート評価: {route_name}, target_node={target_node}, 条件数={len(conditions)}", node_id)

                # 条件評価
                if self._evaluate_conditions(conditions, custom_expression, current_data, node_id):
                    self._log(LogLevel.MINIMAL, f"ルート決定: {route_name} → Node {target_node}", node_id)
                    if hasattr(self.log, '_agent_levels') and self.log._agent_levels.get('router') == LogLevel.VERBOSE:
                        self._log(LogLevel.VERBOSE, f"条件一致: {route_name}, target_node={target_node}", node_id)

                    # 実行カウンター更新
                    new_execution_count = execution_count + 1

                    # 実行履歴更新（最大10件）
                    new_history = execution_history.copy()
                    history_entry = {
                        "iteration": new_execution_count,
                        "route": route_name,
                        "target_node": target_node
                    }
                    new_history.append(history_entry)
                    if len(new_history) > 10:
                        new_history = new_history[-10:]

                    # KeyRegistryを使用して出力キー生成
                    decision_key = KeyRegistry.get_key_name("router", "router_decision", node_id)
                    target_key = KeyRegistry.get_key_name("router", "target_node", node_id)
                    metadata_key = KeyRegistry.get_key_name("router", "routing_metadata", node_id)

                    output_data = {
                        decision_key: route_name,  # 条件名を設定（LangGraphが条件マッピングに使用）
                        target_key: target_node,
                        metadata_key: {
                            "route_name": route_name,
                            "execution_count": new_execution_count,
                            "conditions_matched": len(conditions)
                        },
                        "execution_count": new_execution_count,
                        "execution_history": new_history,
                        "next_node": target_node
                    }
                    return self._create_result(
                        confidence=1.0,
                        data=output_data
                    )

            # どのルートにも一致しない場合
            self._log(LogLevel.MINIMAL, "どの条件にも一致せず: デフォルトルート", node_id)
            if hasattr(self.log, '_agent_levels') and self.log._agent_levels.get('router') == LogLevel.VERBOSE:
                self._log(LogLevel.VERBOSE, f"デフォルトルート選択: {routing_rules[0].get('condition', 'default')} → Node {routing_rules[0].get('condition_details', {}).get('target_node', '')}", node_id)

            # デフォルトルートを設定（routing_rulesの最初のtarget_nodeを使用）
            default_target = str(routing_rules[0].get("condition_details", {}).get("target_node", "")) if routing_rules else ""

            decision_key = KeyRegistry.get_key_name("router", "router_decision", node_id)
            target_key = KeyRegistry.get_key_name("router", "target_node", node_id)
            metadata_key = KeyRegistry.get_key_name("router", "routing_metadata", node_id)

            output_data = {
                decision_key: "default",  # 条件名 "default" を設定（LangGraphが条件マッピングに使用）
                target_key: default_target,
                metadata_key: {
                    "route_name": "default",
                    "execution_count": execution_count,
                    "conditions_matched": 0
                },
                "execution_count": execution_count,
                "execution_history": execution_history,
                "next_node": default_target
            }
            return self._create_result(
                confidence=1.0,
                data=output_data
            )

        except Exception as e:
            self._log(LogLevel.MINIMAL, f"Router実行エラー: {str(e)}", node_id)
            return self._create_error_result(str(e), node_id)
    def _create_error_result(self, error_message: str, node_id: Optional[str] = None) -> AgentResult:
        """Router用エラー結果生成"""
        decision_key = KeyRegistry.get_key_name("router", "router_decision", node_id or "router")
        target_key = KeyRegistry.get_key_name("router", "target_node", node_id or "router")
        metadata_key = KeyRegistry.get_key_name("router", "routing_metadata", node_id or "router")
        output_data = {
            decision_key: None,
            target_key: None,
            metadata_key: {
                "error": error_message
            },
            "execution_count": 0,
            "execution_history": [],
            "next_node": None
        }
        return self._create_result(
            confidence=0.0,
            data=output_data
        )
    
    def _evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        custom_expression: str,
        current_data: Dict[str, Any],
        node_id: str
    ) -> bool:
        """条件リスト評価（論理式対応）"""
        if not conditions:
            return True
        
        check_results = []
        
        for condition in conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "==")
            threshold = condition.get("threshold")
            
            # フィールド値取得
            value = self._get_field_value(field, current_data)
            
            if value is None:
                self._log(LogLevel.VERBOSE, f"フィールド '{field}' が見つかりません", node_id)
                check_results.append(False)
                continue
            
            # VERBOSEレベル時のみ詳細ログ
            if hasattr(self.log, '_agent_levels') and self.log._agent_levels.get('router') == LogLevel.VERBOSE:
                self._log(LogLevel.VERBOSE, f"条件評価: {field}={value} {operator} {threshold}", node_id)
            
            # 条件評価
            result = self._evaluate_condition(value, operator, threshold)
            check_results.append(result)
        
        # 論理式がある場合は論理式を評価、ない場合はAND演算
        if custom_expression:
            return self._evaluate_logical_expression(custom_expression, check_results)
        else:
            # デフォルトはAND演算（全ての条件が真）
            return all(check_results)
    
    def _evaluate_logical_expression(self, expression: str, check_results: List[bool]) -> bool:
        """論理式評価（[1] or ([2] and [3]) 形式）"""
        try:
            # [N] を check_results[N-1] に置換
            eval_expression = expression
            for i in range(len(check_results)):
                placeholder = f"[{i+1}]"
                result_value = "True" if check_results[i] else "False"
                eval_expression = eval_expression.replace(placeholder, result_value)
            
            self._log(LogLevel.VERBOSE, f"論理式評価: {expression} → {eval_expression}")
            
            # スペースを正規化
            eval_expression = eval_expression.strip()
            
            # シンプルなトークンチェック（文字列分割）
            import re
            # 不要なスペースを正規化
            normalized = re.sub(r'\s+', ' ', eval_expression)
            
            # 安全でないトークンをチェック
            safe_tokens = r'^[TrueFalse andornot() ]+$'
            if not re.match(safe_tokens, normalized):
                self._log(LogLevel.MINIMAL, f"論理式に不正な文字が含まれています: {normalized}")
                return False
            
            # 論理式評価実行
            result = eval(normalized)
            self._log(LogLevel.VERBOSE, f"論理式結果: {result}")
            return bool(result)
            
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"論理式評価エラー: {expression} - {e}")
            return False
    
    def _get_field_value(self, field: str, current_data: Dict[str, Any]) -> Optional[Any]:
        """フィールド値取得（ノードID付きキーとベース名両対応）"""
        # 直接キーで取得を試みる
        if field in current_data:
            return current_data[field]
        
        # ノードID付きキーを探索
        for key, value in current_data.items():
            if key == field or key.startswith(f"{field}_"):
                return value
        
        return None
    
    def _evaluate_condition(self, value: Any, operator: str, threshold: Any) -> bool:
        """単一条件評価"""
        try:
            # 演算子の正規化（UIで使用される形式を内部形式に変換）
            operator_map = {
                "lt": "<",
                "le": "<=",
                "eq": "==",
                "ge": ">=",
                "gt": ">",
                "ne": "!="
            }
            normalized_op = operator_map.get(operator, operator)
            
            if normalized_op == "==":
                return value == threshold
            elif normalized_op == "!=":
                return value != threshold
            elif normalized_op == ">":
                return float(value) > float(threshold)
            elif normalized_op == ">=":
                return float(value) >= float(threshold)
            elif normalized_op == "<":
                return float(value) < float(threshold)
            elif normalized_op == "<=":
                return float(value) <= float(threshold)
            elif normalized_op == "in":
                return value in threshold if isinstance(threshold, (list, tuple)) else False
            elif normalized_op == "not in":
                return value not in threshold if isinstance(threshold, (list, tuple)) else True
            else:
                self._log(LogLevel.MINIMAL, f"未対応の演算子: {operator} (正規化後: {normalized_op})")
                return False
        except (ValueError, TypeError) as e:
            self._log(LogLevel.MINIMAL, f"条件評価エラー: {e}")
            return False