# agent_designer/designer_gui.py
import dearpygui.dearpygui as dpg
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_designer.ui.canvas_manager import CanvasManager
from copy import deepcopy
from agent_designer.ui.mouse_handler import MouseHandler
from agent_designer.ui.node_settings import NodeSettingsManager
from agent_designer.ui.file_operations import FileOperations
from agent_designer.ui.agent_settings import get_gui_metadata, get_default_node_config, CONFIG_CLASSES
from utils.connection_engine import ConnectionRuleEngine

class AgentDesigner:
    def __init__(self):
        # 基本的な初期化
        self.nodes = []
        self.connections = []
        self.selected_node = None
        self.connection_mode = False
        self.connection_start_node = None
        self.node_counter = 1
        
        # 各種マネージャーの初期化
        self.canvas_manager = CanvasManager(self)
        self.mouse_handler = MouseHandler(self)
        self.settings_manager = NodeSettingsManager(self)
        self.file_operations = FileOperations(self)
        self.connection_engine = ConnectionRuleEngine()

    def setup_gui(self):
        dpg.create_context()
        
        # 日本語フォント設定
        with dpg.font_registry():
            with dpg.font("C:/Windows/Fonts/meiryo.ttc", 16) as japanese_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
                dpg.add_font_range(0x0020, 0x00FF)
                dpg.add_font_range(0x3040, 0x309F)
                dpg.add_font_range(0x30A0, 0x30FF)
                dpg.add_font_range(0x4E00, 0x9FAF)
        
        dpg.create_viewport(title="Multi-Agent Designer", width=1200, height=800)
        
        with dpg.window(label="Multi-Agent Designer", width=1180, height=750, pos=(10, 10), tag="main_window"):
            
            with dpg.menu_bar():
                with dpg.menu(label="ファイル"):
                    dpg.add_menu_item(label="新規作成", callback=self.file_operations.new_design)
                    dpg.add_menu_item(label="保存", callback=self.file_operations.save_design)
                    dpg.add_menu_item(label="読み込み", callback=self.file_operations.load_design)
            
            with dpg.group(horizontal=True):
                # 左側：ツールパネル
                with dpg.child_window(width=250, height=700, tag="tool_panel"):
                    dpg.add_text("マルチエージェントタイプ", color=(200, 200, 255))
                    
                    # 【修正】エージェントタイプボタンを正しく作成
                    self.create_agent_buttons()
                    
                    dpg.add_separator()
                    dpg.add_text("接続", color=(200, 200, 255))
                    dpg.add_checkbox(label="接続モード", tag="connection_mode")
                    
                    dpg.add_separator()
                    dpg.add_text("使用可能キー", color=(200, 200, 255))
                    dpg.add_button(label="キー一覧表示", callback=self.show_available_keys, width=220)
                    
                    dpg.add_separator()
                    dpg.add_text("選択中のノード:", color=(150, 255, 150))
                    dpg.add_text("なし", tag="selected_info")
                
                # 右側：設計キャンバス
                with dpg.child_window(width=900, height=700, tag="canvas_window"):
                    with dpg.drawlist(width=890, height=690, tag="canvas") as canvas:
                        self.canvas_manager.setup_canvas(canvas)
                        dpg.draw_text(pos=(350, 340), text="設計キャンバス", color=(180, 180, 180), parent=canvas)
            
            # グローバルマウスハンドラー
            with dpg.handler_registry():
                dpg.add_mouse_click_handler(callback=self.mouse_handler.on_mouse_click)
                dpg.add_mouse_drag_handler(callback=self.mouse_handler.on_mouse_drag)
                dpg.add_mouse_release_handler(callback=self.mouse_handler.on_mouse_release)
                dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=self.delete_selected)
        
        # フォントをバインド
        dpg.bind_font(japanese_font)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_agent_buttons(self):
        """エージェントタイプボタンを正しく作成（クロージャー問題回避）"""
        dpg.add_button(label="Analyzer（解析）", callback=lambda: self.add_agent_node('analyzer'), width=200)
        dpg.add_button(label="Retriever（検索）", callback=lambda: self.add_agent_node('retriever'), width=200)
        dpg.add_button(label="Domain Expert（専門家）", callback=lambda: self.add_agent_node('domain_expert'), width=200)
        dpg.add_button(label="Validator（検証）", callback=lambda: self.add_agent_node('validator'), width=200)
        dpg.add_button(label="Refiner（整形）", callback=lambda: self.add_agent_node('refiner'), width=200)
        dpg.add_button(label="Router（分岐）", callback=lambda: self.add_agent_node('router'), width=200)
        dpg.add_button(label="VLM（画像認識）", callback=lambda: self.add_agent_node('vlm'), width=200)



    def add_agent_node(self, agent_type):
        """新しいエージェントタイプのノードを追加"""
        print(f"ノード追加が呼ばれました: {agent_type}")  # デバッグ用
        
        if agent_type not in CONFIG_CLASSES:
            print(f"エラー: 未知のエージェントタイプ {agent_type}")
            return
        
        node_id = self.node_counter
        self.node_counter += 1
        
        default_config = get_default_node_config(agent_type)
        new_node = {
            'id': node_id,
            'type': agent_type,
            'pos': (100 + len(self.nodes) * 30, 100 + len(self.nodes) * 30),
            'config': deepcopy(default_config)
        }
        
        self.nodes.append(new_node)
        print(f"ノード追加完了: ID={node_id}, Type={agent_type}")  # デバッグ用
        self.canvas_manager.refresh_canvas()

    def delete_selected(self):
        """選択されたノードまたは接続を削除"""
        # ダイアログが開いている場合は削除処理をスキップ
        if dpg.does_item_exist("node_settings_window"):
            return
        
        if dpg.does_item_exist("validation_window") or dpg.does_item_exist("context_menu"):
            return
        
        # キャンバスにフォーカスがない場合はスキップ
        if not dpg.is_item_focused("canvas") and not dpg.is_item_hovered("canvas"):
            return
        
        if self.selected_node:
            node_id = self.selected_node['id']
            
            # ノードを削除
            self.nodes = [n for n in self.nodes if n['id'] != node_id]
            
            # 関連する接続も削除
            removed_connections = []
            remaining_connections = []
            
            for conn in self.connections:
                if conn['from'] == node_id or conn['to'] == node_id:
                    removed_connections.append(conn)
                else:
                    remaining_connections.append(conn)
            
            self.connections = remaining_connections
            
            # 選択状態をクリア
            self.selected_node = None
            dpg.set_value("selected_info", "なし")
            
            # キャンバスを更新
            self.canvas_manager.refresh_canvas()

    def show_available_keys(self):
        """使用可能キー一覧を表示（エンコーディング修正版）"""
        # 既存のキー表示ウィンドウがあれば削除
        if dpg.does_item_exist("available_keys_window"):
            dpg.delete_item("available_keys_window")
        
        # 全ノードから生成される可能性のあるキーを収集
        available_keys = self._collect_available_keys()
        
        with dpg.window(
            label="Available Keys List",  # 英語ラベルに変更
            width=400,
            height=500,
            pos=(100, 100),
            modal=False,
            tag="available_keys_window"
        ):
            dpg.add_text("Available Keys in Workflow:", color=(200, 200, 255))
            dpg.add_separator()
            
            if not available_keys:
                dpg.add_text("No nodes placed yet", color=(180, 180, 180))
            else:
                for node_id, keys in available_keys.items():
                    dpg.add_text(f"Node: {node_id}", color=(150, 200, 150))
                    for key in keys:
                        # 日本語文字を含むキーは安全な形式で表示
                        safe_key = key.encode('ascii', 'replace').decode('ascii')
                        dpg.add_text(f"  - {safe_key}", color=(200, 200, 200))
                    dpg.add_separator()
            
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("available_keys_window"))

    def _collect_available_keys(self):
        """全ノードから使用可能キーを収集"""
        available_keys = {}
        
        # 各エージェントタイプから生成されるキーを定義
        key_patterns = {
            'retriever': [
                'retrieved_documents',
                'retriever_confidence',
                'search_metadata',
                'document_count',
                'similarity_scores'
            ],
            'analyzer': [
                'analysis_result',
                'analyzer_confidence',
                'query_type',
                'complexity_score',
                'optimization_suggestions'
            ],
            'domain_expert': [
                'expert_analysis',
                'expert_confidence',
                'domain_insights',
                'technical_recommendations',
                'expertise_level'
            ],
            'validator': [
                'validation_result',
                'validator_confidence',
                'quality_score',
                'error_count',
                'recommendations'
            ],
            'refiner': [
                'refined_output',
                'refiner_confidence',
                'final_document',
                'generation_metadata',
                'section_results'
            ],
            'router': [
                'routing_decision',
                'router_confidence',
                'condition_matches',
                'next_target',
                'iteration_count'
            ]
        }
        
        # 配置されたノードから実際に使用可能なキーを収集
        for node in self.nodes:
            node_type = node['type']
            node_id = node['id']
            
            if node_type in key_patterns:
                available_keys[f"{node_type}_{node_id}"] = key_patterns[node_type]
        
        return available_keys

    def run(self):
        """アプリケーションを実行（単一ウィンドウモード）"""
        self.setup_gui()
        dpg.set_primary_window("main_window", True)  # メインウィンドウをプライマリに設定
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    designer = AgentDesigner()
    designer.run()
