# utils/connection_engine.py
import json
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ConnectionValidationResult:
    """接続検証結果"""
    is_valid: bool
    available_line_types: List[str]
    auto_select: bool = False 
    error_message: Optional[str] = None
    warnings: List[str] = None


class ConnectionRuleEngine:
    def __init__(self, rules_file: str = "configs/connection_rules.json"):
        """接続ルールエンジンを初期化"""
        self.rules_file = rules_file
        self.rules = self._load_rules()
        self.agents = self.rules.get("agents", {})
        self.line_types = self.rules.get("line_types", {})
        self.global_constraints = self.rules.get("global_constraints", {})
        
    def _load_rules(self) -> Dict:
        """ルールファイルを読み込み"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: ルールファイル {self.rules_file} が見つかりません")
            return {"agents": {}, "line_types": {}, "global_constraints": {}}
        except json.JSONDecodeError as e:
            print(f"エラー: ルールファイルの解析に失敗: {e}")
            return {"agents": {}, "line_types": {}, "global_constraints": {}}
    
    def validate_connection(self, from_agent: str, to_agent: str, 
                        existing_connections: List[Dict] = None) -> ConnectionValidationResult:
        """接続の妥当性を検証（単一線種自動選択対応版）"""
        existing_connections = existing_connections or []
        
        # 基本的な接続可能性チェック
        if from_agent not in self.agents:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message=f"未知の送信元エージェント: {from_agent}"
            )
        
        if to_agent not in self.agents:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message=f"未知の受信先エージェント: {to_agent}"
            )
        
        # 自己接続チェック
        if from_agent == to_agent:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message="自分自身への接続は許可されていません"
            )
        
        # 送信元の出力許可チェック
        from_agent_config = self.agents[from_agent]
        allowed_outputs = from_agent_config.get("allowed_outputs", {})
        
        if to_agent not in allowed_outputs:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message=f"{from_agent} から {to_agent} への接続は許可されていません"
            )
        
        # 受信先の入力許可チェック
        to_agent_config = self.agents[to_agent]
        allowed_inputs = to_agent_config.get("allowed_inputs", {})
        
        if allowed_inputs and from_agent not in allowed_inputs:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message=f"{to_agent} は {from_agent} からの入力を受け付けません"
            )
        
        # 利用可能な線種を取得
        available_line_types = allowed_outputs[to_agent]
        
        # 受信先の入力制約も考慮
        if allowed_inputs and from_agent in allowed_inputs:
            input_line_types = allowed_inputs[from_agent]
            # 送信側と受信側の両方で許可された線種のみ
            available_line_types = list(set(available_line_types) & set(input_line_types))
        
        if not available_line_types:
            return ConnectionValidationResult(
                is_valid=False,
                available_line_types=[],
                error_message=f"{from_agent} と {to_agent} 間に互換性のある線種がありません"
            )
        
        # 既存接続との競合チェック
        warnings = []
        duplicate_connections = [
            conn for conn in existing_connections 
            if conn.get('from') == from_agent and conn.get('to') == to_agent
        ]
        
        if duplicate_connections:
            warnings.append(f"{from_agent} から {to_agent} への接続が既に存在します")
        
        # フィードバックループの制約チェック
        if self._creates_excessive_feedback_loop(from_agent, to_agent, existing_connections):
            warnings.append("フィードバックループの上限に近づいています")
        
        # 単一線種の場合は自動選択
        auto_select = len(available_line_types) == 1
        
        return ConnectionValidationResult(
            is_valid=True,
            available_line_types=available_line_types,
            auto_select=auto_select,
            warnings=warnings if warnings else None
        )
    
    def _creates_excessive_feedback_loop(self, from_agent: str, to_agent: str, 
                                       existing_connections: List[Dict]) -> bool:
        """過度なフィードバックループの検出"""
        # 簡易版: feedback線種の数をカウント
        feedback_count = sum(
            1 for conn in existing_connections 
            if conn.get('type') == 'feedback'
        )
        
        max_feedback = self.global_constraints.get('max_total_loops', 10)
        return feedback_count >= max_feedback - 1
    
    def get_line_type_info(self, line_type: str) -> Dict:
        """線種の視覚的情報を取得"""
        # edge_typesから情報を取得
        edge_types = self.rules.get("edge_types", {})
        return edge_types.get(line_type, {
            "color": [128, 128, 128],
            "thickness": 2,
            "style": "solid",
            "description": "未定義の線種"
        })
    
    def validate_workflow_graph(self, nodes: List[Dict], connections: List[Dict]) -> Dict:
        """ワークフロー全体の妥当性を検証"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        # 開始点の検証
        required_start_agents = set(self.global_constraints.get("required_start_agents", []))
        existing_start_agents = {
            node['type'] for node in nodes 
            if not any(conn['to'] == node['id'] for conn in connections)
        }
        
        missing_start_agents = required_start_agents - existing_start_agents
        if missing_start_agents:
            validation_result["errors"].append(
                f"必要な開始エージェントが不足: {list(missing_start_agents)}"
            )
            validation_result["is_valid"] = False
        
        # 終了点の検証
        required_end_agents = set(self.global_constraints.get("required_end_agents", []))
        existing_end_agents = {
            node['type'] for node in nodes 
            if not any(conn['from'] == node['id'] for conn in connections)
        }
        
        if required_end_agents and not (required_end_agents & existing_end_agents):
            validation_result["warnings"].append(
                f"推奨される終了エージェントがありません: {list(required_end_agents)}"
            )
        
        # 循環参照の検出
        cycles = self._detect_cycles(nodes, connections)
        if cycles:
            for cycle in cycles:
                if not self._is_valid_feedback_cycle(cycle, connections):
                    validation_result["errors"].append(f"不正な循環参照: {' -> '.join(cycle)}")
                    validation_result["is_valid"] = False
        
        # 統計情報
        validation_result["statistics"] = {
            "total_nodes": len(nodes),
            "total_connections": len(connections),
            "line_types_used": list(set(conn.get('type', 'unknown') for conn in connections)),
            "feedback_loops": len([conn for conn in connections if conn.get('type') == 'feedback'])
        }
        
        return validation_result
    
    def _detect_cycles(self, nodes: List[Dict], connections: List[Dict]) -> List[List[str]]:
        """グラフ内の循環を検出"""
        # DFSによる循環検出の簡易実装
        node_types = {node['id']: node['type'] for node in nodes}
        graph = {}
        
        for node in nodes:
            graph[node['id']] = []
        
        for conn in connections:
            if conn['from'] in graph:
                graph[conn['from']].append(conn['to'])
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node_id, path):
            if node_id in rec_stack:
                # 循環発見
                cycle_start = path.index(node_id)
                cycle = [node_types[nid] for nid in path[cycle_start:] + [node_id]]
                cycles.append(cycle)
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                dfs(neighbor, path + [node_id])
            
            rec_stack.remove(node_id)
        
        for node_id in graph:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def _is_valid_feedback_cycle(self, cycle: List[str], connections: List[Dict]) -> bool:
        """フィードバック循環が妥当かチェック"""
        # フィードバック線を含む循環は許可
        return any(
            conn.get('type') == 'feedback' for conn in connections
        )
    
    def get_agent_constraints(self, agent_type: str) -> Dict:
        """エージェントの制約情報を取得"""
        return self.agents.get(agent_type, {}).get("constraints", {})
    
    def suggest_connections(self, from_agent: str) -> List[Tuple[str, List[str]]]:
        """推奨接続先を提案"""
        if from_agent not in self.agents:
            return []
        
        allowed_outputs = self.agents[from_agent].get("allowed_outputs", {})
        suggestions = []
        
        for to_agent, line_types in allowed_outputs.items():
            suggestions.append((to_agent, line_types))
        
        return suggestions