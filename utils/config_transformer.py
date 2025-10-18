# utils/config_transformer.py
"""
GUI形式(DearPyGUtest.json) ⇔ 実行形式(複雑テスト.json) の相互変換
"""
from typing import Dict, List, Any, Set
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 修正: 遅延インポートに変更 ==========
# Before (循環インポートの原因):
# from agent_designer.ui.agent_settings import get_execution_thresholds, get_default_node_config

# After (遅延インポート):
# 関数内で必要な時だけインポート
# ==============================================


class ConfigTransformer:
    """設定フォーマット変換器"""
    
    @staticmethod
    def to_execution_format(nodes: List[Dict], connections: List[Dict]) -> Dict[str, Any]:
        """GUI形式 → 実行形式に変換（新形式：node_thresholds生成）"""
        return {
            "system_specification": ConfigTransformer._generate_system_specification(nodes, connections),
            "nodes": ConfigTransformer._simplify_nodes(nodes),
            "connections": ConfigTransformer._expand_router_connections(nodes, ConfigTransformer._simplify_connections(connections)),
            "node_thresholds": ConfigTransformer._extract_node_thresholds(nodes),
            "logging": ConfigTransformer._generate_node_logging_config(nodes)
        }
    
    @staticmethod
    def from_execution_format(data: Dict[str, Any]) -> tuple:
        """実行形式 → GUI形式に変換（新形式：node_thresholdsからconfig復元）"""
        nodes = data.get("nodes", [])
        node_thresholds = data.get("node_thresholds", {})
        
        # ========== 遅延インポート ==========
        from agent_designer.ui.agent_settings import get_default_node_config
        # ==================================
        
        # node_thresholdsからconfigを復元
        for node in nodes:
            node_id = str(node["id"])
            node_type = node["type"]
            
            # デフォルト設定を取得
            default_config = get_default_node_config(node_type)
            
            # node_thresholdsから設定を読み込み
            if node_id in node_thresholds:
                for key, value_obj in node_thresholds[node_id].items():
                    if isinstance(value_obj, dict) and "value" in value_obj:
                        default_config[key] = value_obj["value"]
                    else:
                        default_config[key] = value_obj
            
            # logging設定を追加
            logging_config = data.get("logging", {})
            node_specific_levels = logging_config.get("node_specific_levels", {})
            if node_id in node_specific_levels:
                default_config["logging_level"] = node_specific_levels[node_id]
                default_config["log_level"] = node_specific_levels[node_id]
            
            node["config"] = default_config
        
        # 基本接続を取得
        base_connections = data.get("connections", [])
        
        # Router設定からも条件付き接続を復元
        router_connections = ConfigTransformer._reconstruct_router_connections_from_config(nodes)
        
        # 基本接続とRouter接続を統合
        all_connections = base_connections + router_connections
        
        # 接続情報を復元（線種情報を追加）
        connections = ConfigTransformer._restore_connection_types(all_connections, nodes)
        
        return nodes, connections
    
    @staticmethod
    def _extract_node_thresholds(nodes: List[Dict]) -> Dict[str, Any]:
        """
        nodes[].configからnode_thresholds形式を生成
        
        すべての設定値を{"value": ...}形式に変換します。
        log_level/logging_levelはloggingセクションで管理されるため除外します。
        """
        node_thresholds = {}
        
        for node in nodes:
            node_id = str(node["id"])
            config = node.get("config", {})
            
            if not config:
                continue
            
            node_thresholds[node_id] = {}
            
            for key, value in config.items():
                # log_levelとlogging_levelは除外（loggingセクションで管理）
                if key in ["log_level", "logging_level"]:
                    continue
                
                # 既に{"value": ...}形式の場合はそのまま
                if isinstance(value, dict) and "value" in value:
                    node_thresholds[node_id][key] = value
                else:
                    # それ以外は{"value": ...}でラップ
                    node_thresholds[node_id][key] = {"value": value}
        
        return node_thresholds
    
    @staticmethod
    def _simplify_nodes(nodes: List[Dict]) -> List[Dict]:
        """ノード情報を簡略化（新形式：id/type/posのみ、configは含めない）"""
        return [
            {
                "id": node["id"],
                "type": node["type"],
                "pos": node.get("pos", (100, 100))
            }
            for node in nodes
        ]
    
    @staticmethod
    def _simplify_connections(connections: List[Dict]) -> List[Dict]:
        """接続情報を簡略化（Routerの条件付き接続を除く）"""
        basic_connections = []
        
        for conn in connections:
            # Routerからの条件付き接続はスキップ（後で展開する）
            if conn.get('condition'):
                continue
            
            basic_connections.append({
                "from": conn["from"],
                "to": conn["to"]
            })
        
        return basic_connections
    
    @staticmethod
    def _expand_router_connections(nodes: List[Dict], basic_connections: List[Dict]) -> List[Dict]:
        """Router設定から条件付き接続を展開"""
        all_connections = basic_connections.copy()
        
        # Routerノードを探す
        for node in nodes:
            if node.get('type') != 'router':
                continue
            
            router_id = node['id']
            config = node.get('config', {})
            routing_rules = config.get('routing_rules', {})
            
            if not isinstance(routing_rules, dict):
                continue
            
            # routing_rules.valueがある場合とない場合の両方に対応
            if 'value' in routing_rules:
                # test2.json形式: routing_rules.value.conditions
                rules_data = routing_rules['value']
            else:
                # test3.json形式: routing_rules.conditions
                rules_data = routing_rules
            
            # conditions を展開（構造対応の修正）
            conditions = rules_data.get('conditions', {})
            if isinstance(conditions, dict):
                for condition_name, condition_data in conditions.items():
                    if isinstance(condition_data, dict):
                        # target または target_node どちらにも対応
                        target_node = condition_data.get('target') or condition_data.get('target_node')
                        
                        if target_node:
                            # target_nodeの文字列処理（"node_1" → 1）
                            if isinstance(target_node, str) and target_node.startswith('node_'):
                                try:
                                    target_node = int(target_node.replace('node_', ''))
                                except ValueError:
                                    pass
                            
                            conn = {
                                "from": router_id,
                                "to": target_node,
                                "condition": condition_name,
                                "condition_details": {
                                    "checks": condition_data.get('checks', []),
                                    "custom_expression": condition_data.get('custom_expression', ''),
                                    "description": condition_data.get('description', condition_name),
                                    "target_node": target_node
                                }
                            }
                            all_connections.append(conn)
            
            # default ルート
            default_route = rules_data.get('default', {})
            if isinstance(default_route, dict):
                target_node = default_route.get('target') or default_route.get('target_node')
                if target_node:
                    # target_nodeの文字列処理（"node_7" → 7）
                    if isinstance(target_node, str) and target_node.startswith('node_'):
                        try:
                            target_node = int(target_node.replace('node_', ''))
                        except ValueError:
                            pass
                    
                    conn = {
                        "from": router_id,
                        "to": target_node,
                        "condition": "default",
                        "condition_details": {
                            "description": default_route.get('description', 'Default route'),
                            "decision": default_route.get('decision', 'proceed_to_target'),
                            "target_node": target_node
                        }
                    }
                    all_connections.append(conn)
            
            # max_iterations_exceeded ルート
            max_iter_route = rules_data.get('max_iterations_exceeded', {})
            if isinstance(max_iter_route, dict):
                target_node = max_iter_route.get('target') or max_iter_route.get('target_node')
                if target_node:
                    # target_nodeの文字列処理（"node_7" → 7）
                    if isinstance(target_node, str) and target_node.startswith('node_'):
                        try:
                            target_node = int(target_node.replace('node_', ''))
                        except ValueError:
                            pass
                    
                    conn = {
                        "from": router_id,
                        "to": target_node,
                        "condition": "max_iterations_exceeded",
                        "condition_details": {
                            "description": max_iter_route.get('description', 'Max iterations exceeded'),
                            "decision": max_iter_route.get('decision', 'max_iterations_exceeded'),
                            "target_node": target_node
                        }
                    }
                    all_connections.append(conn)
        
        return all_connections
    
    @staticmethod
    def _reconstruct_router_connections_from_config(nodes: List[Dict]) -> List[Dict]:
        """Routerノード設定から条件付き接続を再構築（読み込み時用）"""
        router_connections = []
        
        for node in nodes:
            if node.get('type') != 'router':
                continue
            
            router_id = node['id']
            config = node.get('config', {})
            routing_rules = config.get('routing_rules', {})
            
            if not isinstance(routing_rules, dict):
                continue
            
            # routing_rules.valueがある場合とない場合の両方に対応
            if 'value' in routing_rules:
                # test2.json形式: routing_rules.value.conditions
                rules_data = routing_rules['value']
            else:
                # test3.json形式: routing_rules.conditions
                rules_data = routing_rules
            
            # conditions を展開
            conditions = rules_data.get('conditions', {})
            if isinstance(conditions, dict):
                for condition_name, condition_data in conditions.items():
                    if isinstance(condition_data, dict):
                        # target または target_node どちらにも対応
                        target_node = condition_data.get('target') or condition_data.get('target_node')
                        
                        if target_node:
                            # target_nodeの文字列処理（"node_1" → 1）
                            if isinstance(target_node, str) and target_node.startswith('node_'):
                                try:
                                    target_node = int(target_node.replace('node_', ''))
                                except ValueError:
                                    pass
                            
                            conn = {
                                "from": router_id,
                                "to": target_node,
                                "condition": condition_name,
                                "condition_details": {
                                    "checks": condition_data.get('checks', []),
                                    "custom_expression": condition_data.get('custom_expression', ''),
                                    "description": condition_data.get('description', condition_name),
                                    "target_node": target_node
                                }
                            }
                            router_connections.append(conn)
            
            # default ルート
            default_route = rules_data.get('default', {})
            if isinstance(default_route, dict):
                target_node = default_route.get('target') or default_route.get('target_node')
                if target_node:
                    # target_nodeの文字列処理（"node_7" → 7）
                    if isinstance(target_node, str) and target_node.startswith('node_'):
                        try:
                            target_node = int(target_node.replace('node_', ''))
                        except ValueError:
                            pass
                    
                    conn = {
                        "from": router_id,
                        "to": target_node,
                        "condition": "default",
                        "condition_details": {
                            "description": default_route.get('description', 'Default route'),
                            "decision": default_route.get('decision', 'proceed_to_target'),
                            "target_node": target_node
                        }
                    }
                    router_connections.append(conn)
            
            # max_iterations_exceeded ルート
            max_iter_route = rules_data.get('max_iterations_exceeded', {})
            if isinstance(max_iter_route, dict):
                target_node = max_iter_route.get('target') or max_iter_route.get('target_node')
                if target_node:
                    # target_nodeの文字列処理（"node_7" → 7）
                    if isinstance(target_node, str) and target_node.startswith('node_'):
                        try:
                            target_node = int(target_node.replace('node_', ''))
                        except ValueError:
                            pass
                    
                    conn = {
                        "from": router_id,
                        "to": target_node,
                        "condition": "max_iterations_exceeded",
                        "condition_details": {
                            "description": max_iter_route.get('description', 'Max iterations exceeded'),
                            "decision": max_iter_route.get('decision', 'max_iterations_exceeded'),
                            "target_node": target_node
                        }
                    }
                    router_connections.append(conn)
        
        return router_connections
    
    @staticmethod
    def _generate_node_logging_config(nodes: List[Dict]) -> Dict[str, Any]:
        """ノード個別ログ設定を生成"""
        node_levels = {}
        
        for node in nodes:
            node_id = str(node['id'])
            config = node.get('config', {})
            
            # ノードの設定にログレベルがあれば使用、なければVERBOSE
            log_level = config.get('log_level', config.get('logging_level', 'VERBOSE'))
            node_levels[node_id] = log_level
        
        return {
            "node_specific_levels": node_levels
        }
    
    @staticmethod
    def _generate_system_specification(nodes: List[Dict], connections: List[Dict]) -> Dict[str, str]:
        """system_specification セクションを自動生成"""
        node_types = [node["type"] for node in nodes]
        architecture_parts = []
        
        if "analyzer" in node_types:
            architecture_parts.append("analyzer")
        
        retriever_count = node_types.count("retriever")
        if retriever_count > 1:
            architecture_parts.append("parallel_retrievers")
        elif retriever_count == 1:
            architecture_parts.append("retriever")
        
        expert_count = node_types.count("domain_expert")
        if expert_count > 1:
            architecture_parts.append("parallel_domain_experts")
        elif expert_count == 1:
            architecture_parts.append("domain_expert")
        
        if "validator" in node_types:
            architecture_parts.append("validator")
        
        if "router" in node_types:
            architecture_parts.append("router")
            architecture_parts.append("(conditional_routing)")
        
        if "refiner" in node_types:
            architecture_parts.append("refiner")
        
        architecture = "->".join(architecture_parts)
        
        return {
            "name": "Multi-Agent RAG System",
            "version": "2.0",
            "architecture": architecture
        }
    
    # === Private: GUI形式への変換 ===
    
    @staticmethod
    def _expand_nodes_with_node_thresholds(simple_nodes: List[Dict], node_thresholds: Dict[str, Any], logging_config: Dict[str, Any] = {}) -> List[Dict]:
        """新形式：ノード個別設定でGUI用に展開（位置情報保持）"""
        # ========== 遅延インポート ==========
        from agent_designer.ui.agent_settings import get_default_node_config
        # ==================================
        
        expanded = []
        
        for i, node in enumerate(simple_nodes):
            node_id = str(node["id"])
            
            # 位置情報の処理
            if "pos" in node:
                pos_raw = node["pos"]
                if isinstance(pos_raw, list) and len(pos_raw) >= 2:
                    pos = (pos_raw[0], pos_raw[1])
                elif isinstance(pos_raw, tuple):
                    pos = pos_raw
                else:
                    pos = (100 + i * 150, 100 + (i % 3) * 100)
            else:
                pos = (100 + i * 150, 100 + (i % 3) * 100)
            
            expanded_node = {
                "id": node["id"],
                "type": node["type"],
                "pos": pos,
                "config": ConfigTransformer._restore_node_specific_config(
                    node, node_thresholds, logging_config, get_default_node_config
                )
            }
            expanded.append(expanded_node)
        
        return expanded
    
    @staticmethod
    def _restore_node_specific_config(
        node: Dict, 
        node_thresholds: Dict[str, Any], 
        logging_config: Dict[str, Any],
        get_default_node_config_func
    ) -> Dict:
        """ノード個別設定からGUI用configを復元"""
        node_id = str(node["id"])
        node_type = node["type"]
        
        # デフォルト設定
        default_config = get_default_node_config_func(node_type)
        full_config = default_config.copy()
        
        # ノード固有設定をマージ
        node_specific_config = node.get("config", {})
        full_config.update(node_specific_config)
        
        # node_thresholdsからの設定を追加
        if node_id in node_thresholds:
            node_threshold_config = node_thresholds[node_id]
            
            for key, config_obj in node_threshold_config.items():
                if isinstance(config_obj, dict) and "value" in config_obj:
                    full_config[key] = config_obj["value"]
                else:
                    full_config[key] = config_obj
        
        # ログ設定を追加
        node_specific_levels = logging_config.get("node_specific_levels", {})
        if node_id in node_specific_levels:
            full_config['logging_level'] = node_specific_levels[node_id]
            full_config['log_level'] = node_specific_levels[node_id]
        
        return full_config
    
    @staticmethod
    def _expand_nodes(simple_nodes: List[Dict], thresholds: Dict[str, Any] = {}, logging_config: Dict[str, Any] = {}) -> List[Dict]:
        """シンプルなノードをGUI用に展開(pos保持、config復元)"""
        # ========== 遅延インポート ==========
        from agent_designer.ui.agent_settings import get_default_node_config
        # ==================================
        
        expanded = []
        
        for i, node in enumerate(simple_nodes):
            expanded_node = {
                "id": node["id"],
                "type": node["type"],
                "pos": node.get("pos", (100 + i * 150, 100 + (i % 3) * 100)),
                "config": ConfigTransformer._restore_full_config(
                    node, thresholds, logging_config, get_default_node_config
                )
            }
            expanded.append(expanded_node)
        
        return expanded
    
    @staticmethod
    def _restore_full_config(
        node: Dict, 
        thresholds: Dict[str, Any], 
        logging_config: Dict[str, Any],
        get_default_node_config_func
    ) -> Dict:
        """ノードのフル設定を復元(thresholds + logging + ノード固有)"""       
        node_type = node["type"]
        default_config = get_default_node_config_func(node_type)
        node_specific_config = node.get("config", {})
        
        # デフォルト + ノード固有設定をマージ
        full_config = default_config.copy()
        full_config.update(node_specific_config)
        
        # thresholdsから設定を復元
        agent_thresholds = thresholds.get(node_type, {})
        
        if node_type == 'analyzer':
            if 'analysis_depth' in agent_thresholds:
                full_config['analysis_depth'] = agent_thresholds['analysis_depth'].get('value', 'comprehensive')
            
            if 'llm_prompts' in agent_thresholds:
                llm_prompts = agent_thresholds['llm_prompts']
                if isinstance(llm_prompts, dict) and 'value' in llm_prompts:
                    full_config['llm_prompts'] = llm_prompts['value']
                else:
                    full_config['llm_prompts'] = llm_prompts
        
        elif node_type == 'retriever':
            threshold_keys = ['search_k', 'initial_k', 'similarity_threshold', 'use_reranker']
            for key in threshold_keys:
                if key in agent_thresholds:
                    full_config[key] = agent_thresholds[key].get('value', full_config.get(key))
        
        # logging設定を復元
        agent_specific_levels = logging_config.get('agent_specific_levels', {})
        if node_type in agent_specific_levels:
            full_config['logging_level'] = agent_specific_levels[node_type]
        else:
            full_config['logging_level'] = 'VERBOSE'
        
        return full_config
    
    @staticmethod
    def _restore_connection_types(connections: List[Dict], nodes: List[Dict]) -> List[Dict]:
        """読み込み時にconnectionsの線種を復元"""
        node_types = {node['id']: node['type'] for node in nodes}
        
        restored_connections = []
        
        for conn in connections:
            restored_conn = conn.copy()
            
            if 'type' not in restored_conn:
                from_id = conn.get('from')
                from_type = node_types.get(from_id)
                
                if from_type == 'router':
                    restored_conn['type'] = 'conditional_flow'
                else:
                    restored_conn['type'] = 'data_flow'
            
            restored_connections.append(restored_conn)
        
        return restored_connections
