# agent_designer/ui/agent_settings/router/settings_ui_new.py
"""
RouterSettingsUI - クリーンな新規実装
Analyzerパターンに完全準拠、DearPyGui推奨方式使用、KeyRegistry統合
"""

import dearpygui.dearpygui as dpg
from typing import Dict, Any, List
from .config import RouterConfig
from utils.key_registry import KeyRegistry


class RouterSettingsUI:
    """DearPyGui版Router設定UI管理（Analyzerパターン準拠）"""
    
    def __init__(self, parent_manager):
        self.parent_manager = parent_manager
        self.current_nodes = {}  # node_id -> config mapping
        self.condition_data = {}  # node_id -> conditions data
    
    def create_router_settings_ui(self, node: Dict[str, Any], ui_config: Dict[str, Any]):
        """Router設定UI作成（統合版）"""
        node_id = node['id']
        self.current_nodes[node_id] = ui_config
        
        print(f"Debug: Creating router UI for node {node_id}")
        print(f"Debug: parent_manager type: {type(self.parent_manager)}")
        print(f"Debug: parent_manager attributes: {dir(self.parent_manager)}")
        
        # UI情報取得
        ui_info = RouterConfig.get_ui_info()
        
        dpg.add_text(f"{ui_info['name']}詳細設定", color=(200, 200, 255))
        dpg.add_separator()
        
        # 基本設定項目
        self._create_basic_settings_ui(node_id, ui_config)
        
        # 条件設定セクション
        dpg.add_separator()
        dpg.add_text("ルーティング条件設定", color=(255, 255, 150))
        dpg.add_spacer(height=5)  # 間隔を調整
        
        # 条件設定エリア
        self._create_conditions_section(node_id, ui_config)
    
    def _create_basic_settings_ui(self, node_id: int, ui_config: Dict[str, Any]):
        """基本設定UI生成（Analyzerパターン準拠）"""
        schema = RouterConfig.get_settings_schema()
        
        for field_name, field_config in schema.items():
            if field_name == 'routing_rules':  # 条件設定は別セクションで処理
                continue
                
            # ウィジェット作成
            self._create_field_widget(node_id, field_name, field_config, ui_config)
            
            # 説明テキスト
            if 'description' in field_config:
                dpg.add_text(f"  {field_config['description']}", color=(180, 180, 180))
            
            dpg.add_spacer(height=5)
        
        # ルーティング設定は常に表示
        dpg.add_separator()
        dpg.add_text("ルーティング設定", color=(255, 255, 150))
        dpg.add_spacer(height=10)
        
        # 接続先ノードの情報を取得
        connected_nodes = self._get_router_connected_nodes(node_id)
        
        # デフォルトノード設定
        dpg.add_text("デフォルトノード（条件を満たさない場合）:")
        routing_rules = ui_config.get('routing_rules', {})
        # 新形式（default.target）と旧形式（default_node）の両方に対応
        if 'default' in routing_rules and isinstance(routing_rules['default'], dict):
            current_default = routing_rules['default'].get('target', connected_nodes[0] if connected_nodes else 'node_1')
        else:
            current_default = routing_rules.get('default_node', connected_nodes[0] if connected_nodes else 'node_1')
        
        dpg.add_combo(
            items=connected_nodes if connected_nodes else ['node_1'],
            default_value=current_default if current_default in (connected_nodes if connected_nodes else ['node_1']) else (connected_nodes[0] if connected_nodes else 'node_1'),
            tag=f"default_node_{node_id}",
            width=200,
            callback=lambda sender, app_data: self._on_node_selection_change(node_id, 'default_node', app_data)
        )
        dpg.add_spacer(height=5)
        
        # 繰返数超過時進行ノード設定
        dpg.add_text("繰返数超過時進行ノード:")
        # 新形式（max_iterations_exceeded.target）と旧形式（max_iterations_node）の両方に対応
        if 'max_iterations_exceeded' in routing_rules and isinstance(routing_rules['max_iterations_exceeded'], dict):
            current_max_iter = routing_rules['max_iterations_exceeded'].get('target', connected_nodes[0] if connected_nodes else 'node_1')
        else:
            current_max_iter = routing_rules.get('max_iterations_node', connected_nodes[0] if connected_nodes else 'node_1')
        
        dpg.add_combo(
            items=connected_nodes if connected_nodes else ['node_1'],
            default_value=current_max_iter if current_max_iter in (connected_nodes if connected_nodes else ['node_1']) else (connected_nodes[0] if connected_nodes else 'node_1'),
            tag=f"max_iterations_node_{node_id}",
            width=200,
            callback=lambda sender, app_data: self._on_node_selection_change(node_id, 'max_iterations_node', app_data)
        )
        dpg.add_spacer(height=10)
    
    def _get_available_fields_from_connected_nodes(self, node_id: int) -> List[tuple]:
        """KeyRegistryから全ノードの数値フィールドを動的に取得（ノードID付き）"""
        try:
            fields = []
            
            # デザイナーからノード情報を取得
            if not (hasattr(self.parent_manager, 'designer') and 
                   hasattr(self.parent_manager.designer, 'nodes')):
                print("Debug: Designer not found")
                return [("no_designer", "デザイナー未検出")]
            
            print(f"Debug: Getting numeric fields for Router {node_id}")
            
            # 全ノードから数値フィールドを取得
            for node in self.parent_manager.designer.nodes:
                node_num = node.get('id')
                node_type = node.get('type')
                
                # Routerノード自身はスキップ
                if node_num == node_id:
                    continue
                
                # KeyRegistryからノードタイプ別のキーを取得
                try:
                    node_keys = KeyRegistry.get_keys_for_node_type(node_type)
                except Exception as e:
                    print(f"Debug: Failed to get keys for node type '{node_type}': {e}")
                    continue
                
                # 各キーをチェックして数値型のみを抽出
                for key_base, key_def in node_keys.items():
                    # 数値型（float/int）のキーのみを抽出
                    if key_def.data_type in ['float', 'int']:
                        try:
                            # KeyRegistryのパターンでキー名を生成
                            full_key = KeyRegistry.get_key_name(node_type, key_base, str(node_num))
                            
                            # ユーザーフレンドリーな表示名を生成
                            # 例: "Analyzer Node 1: confidence"
                            #     "Retriever Node 2: confidence"
                            #     "Validator Node 6: validation_confidence"
                            display_text = f"{node_type.capitalize()} Node {node_num}: {key_base}"
                            fields.append((full_key, display_text))
                            print(f"Debug: Added field: {full_key} ({display_text})")
                        except Exception as e:
                            print(f"Debug: Failed to generate key for {node_type}.{key_base}: {e}")
                            continue
            
            if not fields:
                print("Debug: No numeric fields found from any nodes")
                return [("no_fields", "数値フィールドなし（ノードを追加してください）")]
            
            # ノードID順にソート（見やすくするため）
            fields.sort(key=lambda x: (int(x[0].rsplit('_', 1)[-1]) if x[0].rsplit('_', 1)[-1].isdigit() else 999, x[0]))
            
            print(f"Debug: Total {len(fields)} numeric fields found for router {node_id}")
            return fields
                
        except Exception as e:
            print(f"Debug: Error getting available fields from KeyRegistry: {e}")
            import traceback
            traceback.print_exc()
            return [("error", f"エラー: {str(e)}")]

    def _get_router_connected_nodes(self, node_id: int) -> List[str]:
        """Routerノードから接続している先のノードのみを取得"""
        try:
            connected_nodes = []
            
            # parent_manager.designer.connections経由で接続情報を取得
            if hasattr(self.parent_manager, 'designer') and hasattr(self.parent_manager.designer, 'connections'):
                connections = self.parent_manager.designer.connections
                print(f"Debug: Checking router connections for node {node_id}")
                print(f"Debug: Available connections: {connections}")
                
                for connection in connections:
                    from_node = connection.get('from')
                    to_node = connection.get('to')
                    
                    # このRouterノードから出ている接続のみを対象
                    if from_node == node_id and to_node:
                        target_node = f"node_{to_node}"
                        if target_node not in connected_nodes:
                            connected_nodes.append(target_node)
                            print(f"Debug: Added router connected node: {target_node}")
            
            print(f"Debug: Router {node_id} connected nodes: {connected_nodes}")
            return connected_nodes if connected_nodes else ['node_1']  # デフォルト値
            
        except Exception as e:
            print(f"Debug: Error getting router connected nodes: {e}")
            return ['node_1']
    
    def _get_node_type(self, node_id: int) -> str:
        """ノードタイプを取得"""
        try:
            if hasattr(self.parent_manager, 'designer'):
                designer = self.parent_manager.designer
                if hasattr(designer, 'nodes'):
                    for node in designer.nodes:
                        if node.get('id') == node_id:
                            return node.get('type', 'unknown')
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _on_node_selection_change(self, node_id: int, setting_type: str, selected_node: str):
        """ノード選択変更時の処理"""
        # 必要に応じて設定を保存
        pass
    
    def _create_field_widget(self, node_id: int, field_name: str, field_config: Dict[str, Any], ui_config: Dict[str, Any]):
        """フィールド用ウィジェット作成"""
        widget_type = field_config.get('type', 'entry')
        current_value = self._get_current_value(field_name, ui_config)
        
        # ラベル表示
        label_text = field_config.get('label', field_name)
        dpg.add_text(f"{label_text}:")
        
        if widget_type == 'int':
            default_val = int(current_value) if current_value else field_config.get('default', 1)
            dpg.add_input_int(
                default_value=default_val,
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 100),
                callback=lambda sender, app_data: self._on_value_change(node_id, field_name, app_data)
            )
            
        elif widget_type == 'combo':
            options = field_config.get('options', [])
            option_items = [display_text for _, display_text in options]
            
            # 現在の値に対応する表示テキストを取得
            current_display = ""
            for value, display in options:
                if value == current_value:
                    current_display = display
                    break
            
            dpg.add_combo(
                items=option_items,
                default_value=current_display,
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 200),
                callback=lambda sender, app_data: self._on_combo_change(node_id, field_name, app_data, options)
            )
    
    def _create_conditions_section(self, node_id: int, ui_config: Dict[str, Any]):
        """条件設定セクション作成"""
        # 現在の条件データを取得または初期化
        routing_rules = ui_config.get('routing_rules', {})
        conditions = routing_rules.get('conditions', {})
        
        # 条件データを初期化
        if node_id not in self.condition_data:
            if conditions:
                self.condition_data[node_id] = conditions
            else:
                # 利用可能フィールドと接続先ノードがある場合のみデフォルト条件を作成
                available_fields = self._get_available_fields_from_connected_nodes(node_id)
                connected_nodes = self._get_router_connected_nodes(node_id)
                
                if available_fields and connected_nodes:
                    default_field = available_fields[0][0] if available_fields else "confidence"
                    default_target = connected_nodes[0]  # 接続先ノードを使用
                    
                    self.condition_data[node_id] = {
                        "condition_1": {
                            "checks": [
                                {
                                    "field": default_field,
                                    "operator": "lt", 
                                    "threshold": "0.6"
                                }
                            ],
                            "target": default_target,
                            "description": "条件1",
                            "custom_expression": "[1]"
                        }
                    }
                else:
                    # フィールドがない場合は空の条件データ
                    self.condition_data[node_id] = {}
        
        # 条件表示エリア
        with dpg.group(tag=f"conditions_area_{node_id}"):
            self._display_conditions(node_id)
        
        # 新しい条件追加ボタン
        dpg.add_spacer(height=10)
        dpg.add_button(
            label="+ 新しい条件を追加",
            callback=lambda: self._add_new_condition(node_id),
            tag=f"add_condition_btn_{node_id}"
        )
    
    def _display_conditions(self, node_id: int):
        """全ての条件を表示"""
        conditions = self.condition_data.get(node_id, {})
        
        for condition_name, condition_data in conditions.items():
            self._display_single_condition(node_id, condition_name, condition_data)
    
    def _display_single_condition(self, node_id: int, condition_name: str, condition_data: Dict[str, Any]):
        """単一条件の表示"""
        # 条件ヘッダー
        dpg.add_text(f"条件: {condition_data.get('description', condition_name)}", color=(200, 255, 200))
        
        # チェック項目表示
        checks = condition_data.get('checks', [])
        for i, check in enumerate(checks):
            self._display_check_item(node_id, condition_name, i, check)
        
        # 論理式表示（2個以上のチェックがある場合）
        if len(checks) >= 2:
            dpg.add_text("  論理式 (例: [1] and [2], [1] or [2]):", color=(200, 200, 255))
            expression = condition_data.get('custom_expression', '[1]')
            dpg.add_input_text(
                default_value=expression,
                tag=f"expression_{node_id}_{condition_name}",
                width=200,
                callback=lambda sender, app_data: self._update_expression(node_id, condition_name, app_data)
            )
            dpg.add_text("    ※ [1], [2], [3]... でチェック番号を指定", color=(150, 150, 150))
        
        # 対象ノード（接続先ノードから選択）
        dpg.add_text("  対象ノード:")
        target = condition_data.get('target', 'node_1')
        
        # Routerの接続先ノードのみを取得
        connected_nodes = self._get_router_connected_nodes(node_id)
        
        if connected_nodes:
            dpg.add_combo(
                items=connected_nodes,
                default_value=target if target in connected_nodes else connected_nodes[0],
                tag=f"target_{node_id}_{condition_name}",
                width=150,
                callback=lambda sender, app_data: self._update_target(node_id, condition_name, app_data)
            )
        else:
            dpg.add_text("接続先ノードなし", color=(255, 200, 200))
        
        # 条件操作ボタン
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="+ チェック追加",
                callback=lambda: self._add_check(node_id, condition_name),
                tag=f"add_check_{node_id}_{condition_name}"
            )
            dpg.add_button(
                label="条件削除",
                callback=lambda: self._remove_condition(node_id, condition_name),
                tag=f"remove_condition_{node_id}_{condition_name}"
            )
        
        dpg.add_spacer(height=8)
    
    def _display_check_item(self, node_id: int, condition_name: str, check_index: int, check: Dict[str, Any]):
        """チェック項目の表示"""
        with dpg.group(horizontal=True):
            # チェック番号を表示（論理式で使用）
            check_number = check_index + 1  # 1から開始
            dpg.add_text(f"[{check_number}]", color=(150, 255, 150))
            
            # フィールド選択（動的に取得）
            field_options = self._get_available_fields_from_connected_nodes(node_id)
            
            field_items = [display for _, display in field_options]
            current_field = check.get('field', 'confidence_6')
            current_display = ""
            for value, display in field_options:
                if value == current_field:
                    current_display = display
                    break
            
            dpg.add_combo(
                items=field_items,
                default_value=current_display,
                tag=f"field_{node_id}_{condition_name}_{check_index}",
                width=120,
                callback=lambda sender, app_data: self._update_check_field(node_id, condition_name, check_index, app_data, field_options)
            )
            
            # 演算子選択
            op_options = [
                ("lt", "<"),
                ("le", "<="),
                ("eq", "=="),
                ("ge", ">="), 
                ("gt", ">"),
                ("ne", "!=")
            ]
            
            op_items = [display for _, display in op_options]
            current_op = check.get('operator', 'lt')
            current_op_display = ""
            for value, display in op_options:
                if value == current_op:
                    current_op_display = display
                    break
            
            dpg.add_combo(
                items=op_items,
                default_value=current_op_display,
                tag=f"operator_{node_id}_{condition_name}_{check_index}",
                width=60,
                callback=lambda sender, app_data: self._update_check_operator(node_id, condition_name, check_index, app_data, op_options)
            )
            
            # 閾値入力
            threshold = check.get('threshold', '0.6')
            dpg.add_input_text(
                default_value=str(threshold),
                tag=f"threshold_{node_id}_{condition_name}_{check_index}",
                width=80,
                callback=lambda sender, app_data: self._update_check_threshold(node_id, condition_name, check_index, app_data)
            )
            
            # 削除ボタン
            dpg.add_button(
                label="-",
                callback=lambda: self._remove_check(node_id, condition_name, check_index),
                tag=f"remove_check_{node_id}_{condition_name}_{check_index}",
                width=30
            )
    
    def _refresh_conditions_ui(self, node_id: int):
        """条件UI全体を再描画"""
        # 条件エリアをクリア
        area_tag = f"conditions_area_{node_id}"
        if dpg.does_item_exist(area_tag):
            dpg.delete_item(area_tag)
        
        # 新しい条件エリアを作成
        with dpg.group(tag=area_tag, before=f"add_condition_btn_{node_id}"):
            self._display_conditions(node_id)
    
    # イベントハンドラー
    def _add_new_condition(self, node_id: int):
        """新しい条件を追加"""
        available_fields = self._get_available_fields_from_connected_nodes(node_id)
        
        # Routerの接続先ノードのみを取得
        connected_nodes = self._get_router_connected_nodes(node_id)
        
        if not available_fields or not connected_nodes:
            print("利用可能フィールドまたは接続先ノードがありません")
            return
        
        conditions = self.condition_data.get(node_id, {})
        condition_count = len(conditions) + 1
        new_condition_name = f"condition_{condition_count}"
        
        default_field = available_fields[0][0]
        default_target = connected_nodes[0]
        
        conditions[new_condition_name] = {
            "checks": [
                {
                    "field": default_field,
                    "operator": "lt",
                    "threshold": "0.6"
                }
            ],
            "target": default_target,
            "description": f"条件{condition_count}",
            "custom_expression": "[1]"
        }
        
        self._refresh_conditions_ui(node_id)
    
    def _add_check(self, node_id: int, condition_name: str):
        """チェック項目を追加"""
        available_fields = self._get_available_fields_from_connected_nodes(node_id)
        
        if not available_fields:
            print("利用可能フィールドがありません")
            return
        
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions:
            checks = conditions[condition_name]['checks']
            default_field = available_fields[0][0]
            
            new_check = {
                "field": default_field,
                "operator": "lt",
                "threshold": "0.6"
            }
            checks.append(new_check)
            
            # 論理式を自動更新（より分かりやすく）
            check_count = len(checks)
            if check_count == 2:
                conditions[condition_name]['custom_expression'] = "[1] and [2]"
            elif check_count > 2:
                # 新しいチェック番号を追加（and で結合）
                conditions[condition_name]['custom_expression'] = " and ".join([f"[{i+1}]" for i in range(check_count)])
            
            self._refresh_conditions_ui(node_id)
    
    def _remove_condition(self, node_id: int, condition_name: str):
        """条件を削除"""
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions and len(conditions) > 1:  # 最後の1つは削除不可
            del conditions[condition_name]
            self._refresh_conditions_ui(node_id)
    
    def _remove_check(self, node_id: int, condition_name: str, check_index: int):
        """チェック項目を削除"""
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions:
            checks = conditions[condition_name]['checks']
            if len(checks) > 1 and 0 <= check_index < len(checks):  # 最後の1つは削除不可
                checks.pop(check_index)
                
                # 論理式を更新
                check_count = len(checks)
                if check_count == 1:
                    conditions[condition_name]['custom_expression'] = "[1]"
                else:
                    # 簡単な論理式を再生成
                    expr_parts = [f"[{i+1}]" for i in range(check_count)]
                    conditions[condition_name]['custom_expression'] = " and ".join(expr_parts)
                
                self._refresh_conditions_ui(node_id)
    
    def _update_expression(self, node_id: int, condition_name: str, expression: str):
        """論理式を更新"""
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions:
            conditions[condition_name]['custom_expression'] = expression
    
    def _update_target(self, node_id: int, condition_name: str, target: str):
        """対象ノードを更新"""
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions:
            conditions[condition_name]['target'] = target
    
    def _update_check_field(self, node_id: int, condition_name: str, check_index: int, display_value: str, field_options: List):
        """チェック項目のフィールドを更新"""
        field_value = None
        for value, display in field_options:
            if display == display_value:
                field_value = value
                break
        
        if field_value:
            conditions = self.condition_data.get(node_id, {})
            if condition_name in conditions:
                checks = conditions[condition_name]['checks']
                if 0 <= check_index < len(checks):
                    checks[check_index]['field'] = field_value
    
    def _update_check_operator(self, node_id: int, condition_name: str, check_index: int, display_value: str, op_options: List):
        """チェック項目の演算子を更新"""
        op_value = None
        for value, display in op_options:
            if display == display_value:
                op_value = value
                break
        
        if op_value:
            conditions = self.condition_data.get(node_id, {})
            if condition_name in conditions:
                checks = conditions[condition_name]['checks']
                if 0 <= check_index < len(checks):
                    checks[check_index]['operator'] = op_value
    
    def _update_check_threshold(self, node_id: int, condition_name: str, check_index: int, threshold: str):
        """チェック項目の閾値を更新"""
        conditions = self.condition_data.get(node_id, {})
        if condition_name in conditions:
            checks = conditions[condition_name]['checks']
            if 0 <= check_index < len(checks):
                checks[check_index]['threshold'] = threshold
    
    def _on_value_change(self, node_id: int, field_name: str, value):
        """基本設定値変更時の処理"""
        # 設定更新処理（必要に応じて実装）
        pass
    
    def _on_combo_change(self, node_id: int, field_name: str, display_value: str, options: List):
        """コンボボックス変更時の処理"""
        # 設定更新処理（必要に応じて実装）
        pass
    
    def _get_current_value(self, field_name: str, ui_config: Dict[str, Any]):
        """現在の設定値を取得"""
        # ネストした設定から値を取得
        if field_name == 'max_iterations':
            max_iter = ui_config.get('max_iterations', 1)
            if isinstance(max_iter, dict):
                value = max_iter.get('value', 1)
            else:
                value = max_iter
            # int型に変換
            try:
                return int(value)
            except (ValueError, TypeError):
                return 1
        elif field_name == 'logging_level':
            return ui_config.get('logging_level', 'VERBOSE')
        
        value = ui_config.get(field_name)
        
        # 型変換: スキーマに基づいてint/float型フィールドを変換
        schema = RouterConfig.get_settings_schema()
        if field_name in schema:
            field_type = schema[field_name].get('type')
            if field_type == 'int' and value is not None:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = schema[field_name].get('default', 0)
            elif field_type == 'float' and value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = schema[field_name].get('default', 0.0)
        
        return value
    
    def get_router_config_for_node(self, node_id: int) -> Dict[str, Any]:
        """ノード用Router設定を取得（node_settings.pyとの互換性）"""
        return self.get_ui_config(node_id)
    
    def get_ui_config(self, node_id: int) -> Dict[str, Any]:
        """現在のUI設定を取得"""
        default_target = self._get_widget_value(f"default_node_{node_id}", "node_1")
        max_iter_target = self._get_widget_value(f"max_iterations_node_{node_id}", "node_1")
        
        config = {
            'routing_rules': {
                'conditions': self.condition_data.get(node_id, {}),
                'default': {
                    'target': default_target,
                    'decision': 'proceed_to_target',
                    'description': f'Default route to: {default_target}'
                },
                'max_iterations_exceeded': {
                    'target': max_iter_target,
                    'decision': 'max_iterations_exceeded',
                    'description': f'Max iterations exceeded route to: {max_iter_target}'
                }
            }
        }
        
        # 基本設定を追加
        schema = RouterConfig.get_settings_schema()
        for field_name in schema:
            if field_name != 'routing_rules':
                widget_tag = f"{field_name}_{node_id}"
                if dpg.does_item_exist(widget_tag):
                    value = dpg.get_value(widget_tag)
                    field_config = schema[field_name]
                    
                    # comboの場合は表示値から実際の値に変換（Analyzerパターン）
                    if field_config.get('type') == 'combo':
                        options = field_config.get('options', [])
                        for option_value, option_display in options:
                            if option_display == value:
                                value = option_value
                                break
                    
                    if field_name == 'max_iterations':
                        config['max_iterations'] = {'value': value}
                    else:
                        config[field_name] = value
        
        return config
    
    def _get_widget_value(self, tag: str, default_value: Any = None):
        """ウィジェットの値を安全に取得"""
        if dpg.does_item_exist(tag):
            return dpg.get_value(tag)
        return default_value
    
    def reset_to_defaults(self, node_id: int):
        """Router設定をデフォルトに戻す"""
        try:
            # デフォルト設定を取得
            defaults = RouterConfig.get_default_config()
            schema = RouterConfig.get_settings_schema()
            
            print(f"[DEBUG] Routerデフォルト設定を適用: node_{node_id}")
            
            # 基本設定をデフォルトに戻す
            for field_name, field_config in schema.items():
                tag = f"{field_name}_{node_id}"
                if dpg.does_item_exist(tag):
                    default_value = defaults.get(field_name)
                    
                    if field_config.get('type') == 'combo':
                        # コンボボックスの場合は表示名に変換
                        options = field_config.get('options', [])
                        for option_value, option_display in options:
                            if option_value == default_value:
                                dpg.set_value(tag, option_display)
                                break
                    elif field_config.get('type') == 'int':
                        dpg.set_value(tag, int(default_value))
                    else:
                        dpg.set_value(tag, default_value)
            
            # ルーティング設定をデフォルトに戻す
            default_routing = defaults.get('routing_rules', {})
            
            # 接続先ノードを取得
            connected_nodes = self._get_router_connected_nodes(node_id)
            default_node = connected_nodes[0] if connected_nodes else 'node_1'
            
            # デフォルトノードを設定
            if dpg.does_item_exist(f"default_node_{node_id}"):
                dpg.set_value(f"default_node_{node_id}", default_node)
            
            # 繰返数超過時ノードを設定
            if dpg.does_item_exist(f"max_iterations_node_{node_id}"):
                dpg.set_value(f"max_iterations_node_{node_id}", default_node)
            
            # 条件データを初期化（デフォルトの条件に戻す）
            available_fields = self._get_available_fields_from_connected_nodes(node_id)
            
            if available_fields and connected_nodes:
                default_field = available_fields[0][0]
                default_target = connected_nodes[0]
                
                self.condition_data[node_id] = {
                    "condition_1": {
                        "checks": [
                            {
                                "field": default_field,
                                "operator": "lt",
                                "threshold": "0.6"
                            }
                        ],
                        "target": default_target,
                        "description": "条件1",
                        "custom_expression": "[1]"
                    }
                }
            else:
                self.condition_data[node_id] = {}
            
            # 条件UIを再描画
            self._refresh_conditions_ui(node_id)
            
            print(f"Router設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"Routerデフォルト復元エラー: {e}")
            import traceback
            traceback.print_exc()
    
