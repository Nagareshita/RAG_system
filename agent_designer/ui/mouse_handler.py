# ui/mouse_handler.py
import dearpygui.dearpygui as dpg
import time

class MouseHandler:
    def __init__(self, parent_designer):
        self.designer = parent_designer
        self.last_click_time = 0
        self.last_clicked_node = None
    
    def on_mouse_click(self, sender, app_data):
        """マウスクリック処理 - 接続線右クリック削除対応版"""
        drawing_mouse_pos = dpg.get_drawing_mouse_pos()
        
        if drawing_mouse_pos is not None and dpg.is_item_hovered("canvas"):
            canvas_pos = drawing_mouse_pos
            
            # 接続モード確認
            self.designer.connection_mode = dpg.get_value("connection_mode")
            
            # ノード検索
            clicked_node = self.designer.canvas_manager.get_node_at_pos(canvas_pos)
            
            # 右クリック処理
            if app_data == 1:  # 右クリック
                if clicked_node:
                    self.show_context_menu(clicked_node, canvas_pos)
                else:
                    # 接続線上での右クリックチェック
                    clicked_connection = self.designer.canvas_manager.get_connection_at_pos(canvas_pos)
                    if clicked_connection:
                        self.show_connection_context_menu(clicked_connection, canvas_pos)
                    else:
                        # 空白部分の右クリック
                        if dpg.does_item_exist("context_menu"):
                            dpg.delete_item("context_menu")
                return
            
            # 左クリック処理（既存ロジック維持）
            if clicked_node:
                if dpg.does_item_exist("context_menu"):
                    dpg.delete_item("context_menu")
                
                # ダブルクリック検出
                current_time = time.time()
                
                if hasattr(self, 'last_click_time') and hasattr(self, 'last_clicked_node'):
                    time_diff = current_time - self.last_click_time
                    if time_diff < 0.5 and self.last_clicked_node == clicked_node:
                        self.designer.settings_manager.open_node_settings(clicked_node)
                        return
                
                self.last_click_time = current_time
                self.last_clicked_node = clicked_node
                
                if self.designer.connection_mode:
                    self.handle_connection_click(clicked_node)
                else:
                    self.designer.selected_node = clicked_node
                    self.designer.canvas_manager.dragging = True
                    self.designer.canvas_manager.drag_offset = (canvas_pos[0] - clicked_node['pos'][0], 
                                    canvas_pos[1] - clicked_node['pos'][1])
                    dpg.set_value("selected_info", f"ID:{clicked_node['id']} {clicked_node['type']}")
            else:
                # 空白エリアクリック
                if dpg.does_item_exist("context_menu"):
                    dpg.delete_item("context_menu")
                
                if not self.designer.connection_mode:
                    self.designer.selected_node = None
                    self.designer.canvas_manager.dragging = False
                    dpg.set_value("selected_info", "なし")
                
                self.designer.connection_start_node = None
            
            self.designer.canvas_manager.refresh_canvas()

    def on_mouse_drag(self, sender, app_data):
        """マウスドラッグイベント（デバッグ出力削除版）"""
        if self.designer.canvas_manager.dragging and self.designer.selected_node:
            drawing_mouse_pos = dpg.get_drawing_mouse_pos()
            
            if drawing_mouse_pos is not None:
                # ドラッグオフセットを考慮してノード位置を更新
                new_x = max(0, min(800, drawing_mouse_pos[0] - self.designer.canvas_manager.drag_offset[0]))
                new_y = max(0, min(600, drawing_mouse_pos[1] - self.designer.canvas_manager.drag_offset[1]))
                
                self.designer.selected_node['pos'] = (new_x, new_y)
                self.designer.canvas_manager.refresh_canvas()

    def on_mouse_release(self, sender, app_data):
        """マウスリリースイベント"""
        self.designer.canvas_manager.dragging = False

    def handle_connection_click(self, clicked_node):
        """接続モードでのクリック処理 - Router対応版"""
        if self.designer.connection_start_node is None:
            # 接続開始ノード設定
            self.designer.connection_start_node = clicked_node
            dpg.set_value("selected_info", f"接続開始: ID:{clicked_node['id']}")
        else:
            # 接続終了ノードとして接続検証
            if clicked_node != self.designer.connection_start_node:
                from_node = self.designer.connection_start_node
                to_node = clicked_node
                
                # 通常の接続検証
                validation = self.designer.connection_engine.validate_connection(
                    from_node['type'],
                    to_node['type'],
                    self.designer.connections
                )
                
                if validation.is_valid:
                    if validation.auto_select:
                        # 単一線種の場合は自動的に接続
                        line_type = validation.available_line_types[0]
                        self.create_connection_with_type(from_node, to_node, line_type)
                    else:
                        # 複数線種の場合は選択メニュー表示
                        self.show_line_type_selection_menu(
                            from_node, 
                            to_node, 
                            validation.available_line_types
                        )
                else:
                    # 接続不可の場合はエラーメッセージ表示
                    self.show_connection_error(validation.error_message)
            else:
                dpg.set_value("selected_info", "同じノードには接続できません")
            
            # 接続モードリセット
            self.designer.connection_start_node = None

    def show_context_menu(self, node, pos):
        """右クリックコンテキストメニュー"""
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")
        
        mouse_pos = dpg.get_mouse_pos()
        
        menu_width = 140
        menu_height = 100
        menu_x = mouse_pos[0] + 300
        menu_y = mouse_pos[1] + 5
        
        # 画面端での調整
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        
        if menu_x + menu_width > viewport_width:
            menu_x = mouse_pos[0] - menu_width - 5
        
        if menu_y + menu_height > viewport_height:
            menu_y = mouse_pos[1] - menu_height - 5
        
        with dpg.window(
            label="",
            width=menu_width,
            height=menu_height,
            pos=(int(menu_x), int(menu_y)),
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_scrollbar=True,
            tag="context_menu"
        ):
            dpg.add_button(
                label="ノード設定",
                callback=lambda: self.open_node_settings_from_menu(node),
                width=120
            )
            dpg.add_separator()
            dpg.add_button(
                label="ノード削除",
                callback=lambda: self.delete_node(node),
                width=120
            )
            dpg.add_separator()
            dpg.add_button(
                label="キャンセル",
                callback=lambda: dpg.delete_item("context_menu"),
                width=120
            )

    def show_connection_context_menu(self, connection, pos):
        """接続線用の右クリックコンテキストメニュー"""
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")
        
        mouse_pos = dpg.get_mouse_pos()
        
        menu_width = 120
        menu_height = 80
        menu_x = mouse_pos[0] + 300
        menu_y = mouse_pos[1] + 5
        
        # 画面端での調整
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        
        if menu_x + menu_width > viewport_width:
            menu_x = mouse_pos[0] - menu_width - 5
        
        if menu_y + menu_height > viewport_height:
            menu_y = mouse_pos[1] - menu_height - 5
        
        with dpg.window(
            label="",
            width=menu_width,
            height=menu_height,
            pos=(int(menu_x), int(menu_y)),
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_scrollbar=True,
            tag="context_menu"
        ):
            dpg.add_text(f"接続 {connection['from']} to {connection['to']}")
            dpg.add_separator()
            dpg.add_button(
                label="接続削除",
                callback=lambda: self.delete_connection(connection),
                width=100
            )
            dpg.add_button(
                label="キャンセル",
                callback=lambda: dpg.delete_item("context_menu"),
                width=100
            )

    def show_line_type_selection_menu(self, from_node, to_node, available_line_types):
        """線種選択コンテキストメニュー表示（通常版）"""
        if dpg.does_item_exist("line_type_menu"):
            dpg.delete_item("line_type_menu")
        
        mouse_pos = dpg.get_mouse_pos()
        
        with dpg.window(
            label="接続線種の選択",
            width=200,
            height=len(available_line_types) * 30 + 80,
            pos=(int(mouse_pos[0]), int(mouse_pos[1])),
            no_title_bar=True,
            modal=True,
            tag="line_type_menu"
        ):
            dpg.add_text("線種を選択してください:")
            dpg.add_separator()
            
            for line_type in available_line_types:
                line_info = self.designer.connection_engine.get_line_type_info(line_type)
                dpg.add_button(
                    label=f"{line_type}: {line_info['description']}",
                    callback=lambda sender, data, lt=line_type: self.create_connection_with_type(from_node, to_node, lt),
                    width=180
                )
            
            dpg.add_separator()
            dpg.add_button(
                label="キャンセル",
                callback=lambda: dpg.delete_item("line_type_menu"),
                width=100
            )

    def show_connection_error(self, error_message):
        """接続エラーメッセージ表示"""
        dpg.set_value("selected_info", f"接続エラー: {error_message}")
        if dpg.does_item_exist("line_type_menu"):
            dpg.delete_item("line_type_menu")

    def create_connection_with_type(self, from_node, to_node, line_type):
        """指定された線種で接続作成"""
        from_node_type = from_node.get('type', '')
        
        # Routerからの接続はconditional_flowに強制変更
        if from_node_type == 'router':
            line_type = 'conditional_flow'
            dpg.set_value("selected_info", "Router接続: conditional_flowに変更")
        
        # Routerへの接続はdata_flowに強制変更
        to_node_type = to_node.get('type', '')
        if to_node_type == 'router':
            line_type = 'data_flow'
            dpg.set_value("selected_info", "Routerへの接続: data_flowに変更")
        
        # 既存接続の完全重複チェックとクリーンアップ
        self._remove_duplicate_connections(from_node['id'], to_node['id'], from_node_type)
        
        new_connection = {
            'from': from_node['id'],
            'to': to_node['id'],
            'type': line_type
        }
        
        # Routerからの接続の場合はデフォルト条件を追加
        if from_node_type == 'router':
            new_connection['condition'] = 'default'
            new_connection['condition_details'] = {
                'description': f'Default route to: node_{to_node["id"]}',
                'decision': 'proceed_to_target'
            }
        
        self.designer.connections.append(new_connection)
        print(f"接続作成: {from_node['id']} → {to_node['id']} ({line_type})")
        
        # 線種選択メニューを閉じる
        if dpg.does_item_exist("line_type_menu"):
            dpg.delete_item("line_type_menu")
        
        # キャンバス更新
        self.designer.canvas_manager.refresh_canvas()
        
        dpg.set_value("selected_info", f"接続完了: {line_type}")
    
    def _remove_duplicate_connections(self, from_id, to_id, from_node_type):
        """指定されたfrom-toペアの重複接続を除去"""
        removed_count = 0
        
        if from_node_type == 'router':
            # Routerの場合は条件なしの接続のみ除去（条件付きは別途管理）
            before_count = len(self.designer.connections)
            self.designer.connections = [
                conn for conn in self.designer.connections 
                if not (conn['from'] == from_id and conn['to'] == to_id and not conn.get('condition'))
            ]
            removed_count = before_count - len(self.designer.connections)
        else:
            # 一般ノードの場合は同じfrom-toのすべての接続を除去
            before_count = len(self.designer.connections)
            self.designer.connections = [
                conn for conn in self.designer.connections 
                if not (conn['from'] == from_id and conn['to'] == to_id)
            ]
            removed_count = before_count - len(self.designer.connections)
        
        if removed_count > 0:
            print(f"重複接続を{removed_count}件除去: {from_id} → {to_id}")

    def show_connection_error(self, error_message):
        """接続エラーメッセージ表示"""
        dpg.set_value("selected_info", f"接続不可: {error_message}")

    def open_node_settings_from_menu(self, node):
        """コンテキストメニューからノード設定を開く"""
        dpg.delete_item("context_menu")
        self.designer.settings_manager.open_node_settings(node)

    def delete_node(self, node):
        """指定ノードを削除"""
        node_id = node['id']
        node_type = node['type']
        
        # ノードを削除
        self.designer.nodes = [n for n in self.designer.nodes if n['id'] != node_id]
        
        # 関連する接続も削除
        removed_connections = []
        remaining_connections = []
        
        for conn in self.designer.connections:
            if conn['from'] == node_id or conn['to'] == node_id:
                removed_connections.append(conn)
            else:
                remaining_connections.append(conn)
        
        self.designer.connections = remaining_connections
        
        # 選択状態をクリア
        if self.designer.selected_node == node:
            self.designer.selected_node = None
            dpg.set_value("selected_info", "なし")
        
        # コンテキストメニューを閉じる
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")
        
        # キャンバスを更新
        self.designer.canvas_manager.refresh_canvas()

    def delete_connection(self, connection):
        """指定された接続を削除"""
        from_id = connection['from']
        to_id = connection['to']
        condition = connection.get('condition')
        conn_type = connection.get('type', '')
        
        print(f"接続削除要求: {from_id} → {to_id} (condition: {condition}, type: {conn_type})")
        
        # 接続を正確にマッチングして削除
        before_count = len(self.designer.connections)
        self.designer.connections = [
            conn for conn in self.designer.connections 
            if not self._is_same_connection(conn, from_id, to_id, condition, conn_type)
        ]
        after_count = len(self.designer.connections)
        removed_count = before_count - after_count
        
        print(f"削除された接続数: {removed_count}")
        
        # Routerからの条件付き接続の場合、Router設定からも削除
        if condition and condition != 'default':
            self._remove_router_condition_setting(from_id, condition, to_id)
        elif condition == 'default':
            self._remove_router_default_setting(from_id, to_id)
        
        # コンテキストメニューを閉じる
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")
        
        # キャンバスを更新
        self.designer.canvas_manager.refresh_canvas()
    
    def _is_same_connection(self, conn, from_id, to_id, condition, conn_type):
        """接続が同一かどうかを正確に判定"""
        # 基本的なfrom-toペアが同じ
        if conn['from'] != from_id or conn['to'] != to_id:
            return False
        
        # conditionの正確な比較（None, '', 空文字列を统一処理）
        conn_condition = conn.get('condition') or None
        target_condition = condition or None
        
        # typeの比較
        conn_conn_type = conn.get('type', '')
        
        # 同じ条件とタイプの場合のみ同一と判定
        return conn_condition == target_condition and conn_conn_type == conn_type
    
    def _remove_router_condition_setting(self, router_id, condition_name, target_id):
        """指定された条件をRouter設定から削除"""
        try:
            # Routerノードを検索
            router_node = next((node for node in self.designer.nodes if node['id'] == router_id), None)
            if not router_node or router_node.get('type') != 'router':
                return
            
            # Router設定から条件を削除
            thresholds = router_node.get('thresholds', {})
            routing_rules = thresholds.get('routing_rules', {}).get('value', {})
            conditions = routing_rules.get('conditions', {})
            
            if condition_name in conditions:
                del conditions[condition_name]
                print(f"Router設定から条件削除: {condition_name}")
                
        except Exception as e:
            print(f"Router条件設定削除エラー: {e}")
    
    def _remove_router_default_setting(self, router_id, target_id):
        """デフォルトルートをRouter設定から削除"""
        try:
            # Routerノードを検索
            router_node = next((node for node in self.designer.nodes if node['id'] == router_id), None)
            if not router_node or router_node.get('type') != 'router':
                return
            
            # Router設定からデフォルトをクリア（対象ターゲットのみ）
            thresholds = router_node.get('thresholds', {})
            routing_rules = thresholds.get('routing_rules', {}).get('value', {})
            default_rule = routing_rules.get('default', {})
            
            if default_rule.get('target') == f'node_{target_id}':
                routing_rules['default'] = {}
                print(f"Router設定からデフォルトルート削除: node_{target_id}")
                
        except Exception as e:
            print(f"Routerデフォルト設定削除エラー: {e}")