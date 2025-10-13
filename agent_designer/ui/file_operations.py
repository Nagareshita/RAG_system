# agent_designer/ui/file_operations.py
import dearpygui.dearpygui as dpg
import json
import os
from datetime import datetime

# === 追加: ConfigTransformer のインポート ===
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from utils.config_transformer import ConfigTransformer


class FileOperations:
    def __init__(self, parent_designer):
        self.designer = parent_designer

    def new_design(self):
        """新しい設計を作成"""
        self.designer.nodes = []
        self.designer.connections = []
        self.designer.selected_node = None
        self.designer.canvas_manager.refresh_canvas()
        dpg.set_value("selected_info", "なし")

    def save_design(self):
        """設計をファイル名指定で保存"""
        # 既存のダイアログをすべて削除
        if dpg.does_item_exist("save_dialog"):
            dpg.delete_item("save_dialog")
        if dpg.does_item_exist("overwrite_dialog"):
            dpg.delete_item("overwrite_dialog")
        
        # デフォルトファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"agent_design_{timestamp}.json"
        
        # designs フォルダを作成
        designs_dir = os.path.join("configs", "designs")
        os.makedirs(designs_dir, exist_ok=True)
        
        # ファイル名入力ダイアログを表示
        with dpg.window(
            label="設計保存",
            width=400,
            height=200,
            pos=(400, 300),
            modal=True,
            tag="save_dialog",
            no_resize=True
        ):
            dpg.add_text("設計ファイル名を入力してください:")
            dpg.add_input_text(
                default_value=default_name,
                tag="save_filename",
                width=350
            )
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=100)
                dpg.add_button(
                    label="保存",
                    callback=self._execute_save,
                    width=80
                )
                dpg.add_spacer(width=20)
                dpg.add_button(
                    label="キャンセル",
                    callback=lambda: dpg.delete_item("save_dialog"),
                    width=80
                )

    def _execute_save(self):
        """実際の保存処理を実行（上書き確認付き）"""
        print("[DEBUG] _execute_save 開始")
        filename = dpg.get_value("save_filename")
        print(f"[DEBUG] ファイル名: {filename}")
        
        if not filename.strip():
            print("[DEBUG] ファイル名が空です")
            return
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        designs_dir = os.path.join("configs", "designs")
        file_path = os.path.join(designs_dir, filename)
        print(f"[DEBUG] 保存パス: {file_path}")
        
        # 上書き確認
        if os.path.exists(file_path):
            print("[DEBUG] ファイルが既に存在します - 上書き確認を表示")
            # 既存のダイアログを閉じる
            if dpg.does_item_exist("save_dialog"):
                dpg.delete_item("save_dialog")
            self._show_overwrite_confirm(file_path, filename)
            return
        
        print("[DEBUG] 新規保存")
        self._save_to_file(file_path)
    
    def _show_overwrite_confirm(self, file_path, filename):
        """上書き確認ダイアログを表示"""
        print(f"[DEBUG] 上書き確認ダイアログ表示: {filename}")
        
        # 既存のダイアログを削除
        if dpg.does_item_exist("overwrite_dialog"):
            print("[DEBUG] 既存のoverwrite_dialogを削除")
            dpg.delete_item("overwrite_dialog")
        
        print("[DEBUG] 新しいoverwrite_dialogを作成")
        
        # フォーカスを確実にするため、少し待つ
        def create_dialog():
            with dpg.window(
                label="上書き確認",
                width=450,
                height=180,
                pos=(400, 300),
                modal=True,
                tag="overwrite_dialog",
                no_resize=True,
                no_collapse=True,
                show=True
            ):
                dpg.add_spacer(height=10)
                dpg.add_text(f"ファイル '{filename}' は既に存在します。", wrap=400)
                dpg.add_spacer(height=5)
                dpg.add_text("上書きしますか？", wrap=400)
                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=10)
                
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=80)
                    if dpg.add_button(
                        label="上書き",
                        width=100,
                        height=30,
                        tag="overwrite_yes_btn"
                    ):
                        dpg.set_item_callback("overwrite_yes_btn", lambda: self._confirm_overwrite(file_path))
                    
                    dpg.add_spacer(width=30)
                    if dpg.add_button(
                        label="キャンセル",
                        width=100,
                        height=30,
                        tag="overwrite_no_btn"
                    ):
                        dpg.set_item_callback("overwrite_no_btn", lambda: self._cancel_overwrite())
            
            print("[DEBUG] overwrite_dialog作成完了")
            # ダイアログを最前面に持ってくる
            dpg.focus_item("overwrite_dialog")
        
        # DearPyGuiのレンダリング後に実行
        dpg.split_frame()
        create_dialog()
    
    def _cancel_overwrite(self):
        """上書きをキャンセル"""
        print("[DEBUG] 上書きキャンセル")
        if dpg.does_item_exist("overwrite_dialog"):
            dpg.delete_item("overwrite_dialog")
    
    def _confirm_overwrite(self, file_path):
        """上書きを実行"""
        print("[DEBUG] 上書き実行")
        if dpg.does_item_exist("overwrite_dialog"):
            dpg.delete_item("overwrite_dialog")
        self._save_to_file(file_path)
    
    def _save_to_file(self, file_path):
        """ファイルに保存"""
        try:
            # 保存前に接続の重複除去を実行
            self._cleanup_duplicate_connections()
            
            # Router ノードの routing_rules を接続情報から構築
            # ※ 無効化: ノード設定UIで既にrouting_rulesが保存されているため、
            #   接続情報から再構築すると条件付きルーティングが消失する
            # self._build_router_rules_from_connections()
            
            execution_format = ConfigTransformer.to_execution_format(
                self.designer.nodes,
                self.designer.connections
            )
            
            # デバッグ: 簡潔な保存情報
            print(f"[DEBUG] 保存: {len(self.designer.nodes)}ノード, {len(self.designer.connections)}接続")
            
            # === 修正: インデントを1に変更（より圧縮） ===
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(execution_format, f, ensure_ascii=False, indent=1)
            
            # 保存ダイアログを閉じる
            if dpg.does_item_exist("save_dialog"):
                dpg.delete_item("save_dialog")
            
            print(f"✓ 設計を保存しました: {file_path}")
            
        except Exception as e:
            print(f"保存エラー: {e}")
            # エラー時もダイアログを閉じる
            if dpg.does_item_exist("save_dialog"):
                dpg.delete_item("save_dialog")
            import traceback
            traceback.print_exc()

    def load_design(self):
        """設計ファイル選択ダイアログを表示"""
        designs_dir = os.path.join("configs", "designs")
        
        # designsフォルダが存在しない場合は作成
        if not os.path.exists(designs_dir):
            os.makedirs(designs_dir, exist_ok=True)
            return
        
        # .jsonファイル一覧を取得
        json_files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]
        
        if not json_files:
            return
        
        # ファイル選択ダイアログを表示
        if dpg.does_item_exist("load_dialog"):
            dpg.delete_item("load_dialog")
        
        with dpg.window(
            label="設計読み込み",
            width=600,
            height=400,
            pos=(300, 200),
            modal=True,
            tag="load_dialog"
        ):
            dpg.add_text("読み込む設計ファイルを選択してください:")
            
            # ファイル一覧表示
            with dpg.child_window(height=250, tag="file_list_window"):
                for idx, file in enumerate(json_files):
                    file_path = os.path.join(designs_dir, file)
                    try:
                        # ファイルの簡易情報を表示
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # === 修正: 実行形式とGUI形式の両方に対応 ===
                        if "system_specification" in data:
                            # 実行形式（複雑テスト.json）
                            node_count = len(data.get('nodes', []))
                            connection_count = len(data.get('connections', []))
                            file_info = f"{file} [実行形式] (ノード:{node_count}, 接続:{connection_count})"
                        else:
                            # GUI形式（DearPyGUtest.json）
                            node_count = len(data.get('nodes', []))
                            connection_count = len(data.get('connections', []))
                            file_info = f"{file} [GUI形式] (ノード:{node_count}, 接続:{connection_count})"
                        
                        with dpg.group(horizontal=True):
                            # 読み込みボタン
                            button_tag = f"load_button_{idx}"
                            dpg.add_button(
                                label=file_info,
                                callback=self._create_load_callback(file),
                                width=420,
                                tag=button_tag
                            )
                            
                            # 削除ボタン
                            delete_button_tag = f"delete_button_{idx}"
                            dpg.add_button(
                                label="削除",
                                callback=self._on_delete_button_click,
                                width=60,
                                tag=delete_button_tag,
                                user_data=file
                            )
                            
                    except Exception as e:
                        # エラーファイルの場合
                        with dpg.group(horizontal=True):
                            button_tag = f"load_button_error_{idx}"
                            dpg.add_button(
                                label=f"{file} (読み込みエラー)",
                                callback=self._create_load_callback(file),
                                width=420,
                                tag=button_tag
                            )
                            
                            delete_button_tag = f"delete_button_error_{idx}"
                            dpg.add_button(
                                label="削除",
                                callback=self._on_delete_button_click,
                                width=60,
                                tag=delete_button_tag,
                                user_data=file
                            )
            
            dpg.add_separator()
            dpg.add_button(
                label="キャンセル",
                callback=lambda: dpg.delete_item("load_dialog"),
                width=100
            )

    def _on_delete_button_click(self, sender, app_data, user_data):
        """削除ボタンクリック時の処理"""
        filename = user_data
        self._show_delete_confirmation(filename)

    def _create_load_callback(self, filename):
        """ファイル読み込み用のコールバック関数を生成"""
        def callback():
            self._execute_load(filename)
        return callback

    def _execute_load(self, filename):
        """実際の読み込み処理を実行（修正版: 両形式に対応）"""
        designs_dir = os.path.join("configs", "designs")
        file_path = os.path.join(designs_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                design_data = json.load(f)
            
            # === 修正: 形式を自動判定して読み込み ===
            if "system_specification" in design_data:
                # 実行形式（複雑テスト.json）→ GUI形式に変換
                print(f"実行形式を検出: {filename}")
                nodes, connections = ConfigTransformer.from_execution_format(design_data)
                self.designer.nodes = nodes
                self.designer.connections = connections
            else:
                # GUI形式（DearPyGUtest.json）→ そのまま読み込み
                print(f"GUI形式を検出: {filename}")
                self.designer.nodes = design_data.get('nodes', [])
                self.designer.connections = design_data.get('connections', [])
            
            # ノードカウンターを更新
            if self.designer.nodes:
                max_id = max(node['id'] for node in self.designer.nodes)
                self.designer.node_counter = max_id + 1
            
            self.designer.canvas_manager.refresh_canvas()
            dpg.delete_item("load_dialog")
            print(f"設計を読み込みました: {filename}")
            
        except Exception as e:
            print(f"読み込みエラー: {e}")
            import traceback
            traceback.print_exc()

    def _show_delete_confirmation(self, filename):
        """削除確認ダイアログを表示"""
        if dpg.does_item_exist("delete_confirmation"):
            dpg.delete_item("delete_confirmation")
        
        with dpg.window(
            label="削除確認",
            width=400,
            height=150,
            pos=(450, 300),
            modal=False,
            tag="delete_confirmation",
            no_close=True,
            no_collapse=True
        ):
            dpg.add_text(f"ファイル '{filename}' を削除しますか？")
            dpg.add_text("この操作は取り消せません。", color=(255, 200, 200))
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="削除",
                    callback=lambda: self._execute_delete(filename),
                    width=100
                )
                dpg.add_button(
                    label="キャンセル",
                    callback=lambda: self._close_delete_confirmation(),
                    width=100
                )

    def _close_delete_confirmation(self):
        """削除確認ダイアログを閉じる"""
        if dpg.does_item_exist("delete_confirmation"):
            dpg.delete_item("delete_confirmation")

    def _execute_delete(self, filename):
        """実際のファイル削除処理を実行"""
        designs_dir = os.path.join("configs", "designs")
        file_path = os.path.join(designs_dir, filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"設計ファイルを削除しました: {filename}")
                
                # 確認ダイアログを閉じる
                if dpg.does_item_exist("delete_confirmation"):
                    dpg.delete_item("delete_confirmation")
                
                # 読み込みダイアログを閉じて再表示（ファイル一覧を更新）
                if dpg.does_item_exist("load_dialog"):
                    dpg.delete_item("load_dialog")
                
                # ファイル一覧を更新して再表示
                self.load_design()
            else:
                print(f"エラー: ファイルが見つかりません: {file_path}")
                self._show_delete_error(f"ファイルが見つかりません: {filename}")
            
        except Exception as e:
            print(f"ファイル削除エラー: {e}")
            self._show_delete_error(str(e))

    def _show_delete_error(self, error_message):
        """削除エラーダイアログを表示"""
        if dpg.does_item_exist("delete_error"):
            dpg.delete_item("delete_error")
        
        with dpg.window(
            label="削除エラー",
            width=400,
            height=150,
            pos=(450, 300),
            modal=True,
            tag="delete_error"
        ):
            dpg.add_text("ファイル削除中にエラーが発生しました:", color=(255, 150, 150))
            dpg.add_text(error_message, color=(255, 200, 200))
            dpg.add_separator()
            
            dpg.add_button(
                label="OK",
                callback=lambda: dpg.delete_item("delete_error"),
                width=100
            )

    def _cleanup_duplicate_connections(self):
        """重複接続の完全除去"""
        original_count = len(self.designer.connections)
        
        # 重複除去処理
        seen_connections = set()
        unique_connections = []
        
        for conn in self.designer.connections:
            # 接続の一意キーを生成（from, to, condition, typeの組み合わせ）
            condition = conn.get('condition') or ''
            conn_type = conn.get('type', '')
            connection_key = (conn['from'], conn['to'], condition, conn_type)
            
            if connection_key not in seen_connections:
                seen_connections.add(connection_key)
                unique_connections.append(conn)
            else:
                print(f"重複接続を除去: {conn['from']} → {conn['to']} (condition: {condition}, type: {conn_type})")
        
        self.designer.connections = unique_connections
        
        removed_count = original_count - len(unique_connections)
        if removed_count > 0:
            print(f"保存前クリーンアップ: {removed_count}件の重複接続を除去")
            # キャンバス更新
            self.designer.canvas_manager.refresh_canvas()
    
    def _build_router_rules_from_connections(self):
        """接続情報からRouterノードのrouting_rulesを構築"""
        try:
            for node in self.designer.nodes:
                if node['type'] != 'router':
                    continue
                
                node_id = node['id']
                print(f"[DEBUG] Routerノード {node_id} の routing_rules を接続情報から構築")
                
                # 接続情報からルーティング条件を抽出
                conditions = {}
                default_target = None
                max_iter_target = None
                
                for conn in self.designer.connections:
                    if conn['from'] != node_id:
                        continue
                    
                    to_node = f"node_{conn['to']}"
                    condition = conn.get('condition')
                    condition_details = conn.get('condition_details', {})
                    
                    if condition and condition.startswith('condition_'):
                        # 条件付きルーティング
                        conditions[condition] = {
                            'checks': condition_details.get('checks', []),
                            'custom_expression': condition_details.get('custom_expression', '[1]'),
                            'target': to_node,
                            'description': condition_details.get('description', condition)
                        }
                    elif condition == 'default':
                        # デフォルトルート
                        default_target = to_node
                    elif condition == 'max_iterations_exceeded':
                        # 繰返数超過ルート
                        max_iter_target = to_node
                
                # routing_rulesを構築
                routing_rules = {
                    'conditions': conditions,
                    'default': {
                        'target': default_target or 'node_7',
                        'decision': 'proceed_to_target',
                        'description': f'Default route to: {default_target or "node_7"}'
                    },
                    'max_iterations_exceeded': {
                        'target': max_iter_target or 'node_7',
                        'decision': 'max_iterations_exceeded',
                        'description': f'Max iterations exceeded route to: {max_iter_target or "node_7"}'
                    }
                }
                
                # ノード設定に反映
                node['config']['routing_rules'] = routing_rules
                
                print(f"[DEBUG] Router {node_id} routing_rules構築完了:")
                print(f"  - 条件数: {len(conditions)}")
                print(f"  - デフォルト: {default_target}")
                print(f"  - 繰返数超過: {max_iter_target}")
                
        except Exception as e:
            print(f"[ERROR] Router routing_rules構築エラー: {e}")
            import traceback
            traceback.print_exc()