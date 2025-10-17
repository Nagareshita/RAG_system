# agent_designer/ui/node_settings.py
import dearpygui.dearpygui as dpg

# defaults.py から設定を読み込み
import sys
from copy import deepcopy
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from agent_designer.ui.agent_settings import get_default_node_config, get_gui_metadata

# 分離された設定UIをインポート
from .agent_settings.retriever import RetrieverSettingsUI
from .agent_settings.analyzer import AnalyzerSettingsUI
from .agent_settings.domain_expert import DomainExpertSettingsUI
from .agent_settings.validator import ValidatorSettingsUI
from .agent_settings.refiner import RefinerSettingsUI
from .agent_settings.refiner import RefinerConfig
from .agent_settings.router import RouterSettingsUI
from .agent_settings.vlm.settings_ui import VLMSettingsUI
from .agent_settings.analyzer import AnalyzerConfig
from .agent_settings.domain_expert import DomainExpertConfig
from .agent_settings.validator import ValidatorConfig
from .agent_settings.router import RouterConfig
from .agent_settings.vlm.config import VLMConfig


class NodeSettingsManager:
    def __init__(self, parent_designer):
        self.designer = parent_designer
        # 分離された設定UIのインスタンス
        self.retriever_settings = RetrieverSettingsUI(self)
        self.analyzer_settings = AnalyzerSettingsUI(self)
        self.domain_expert_settings = DomainExpertSettingsUI(self)
        self.validator_settings = ValidatorSettingsUI(self)
        self.refiner_settings = None  # 動的に作成
        self.router_settings = RouterSettingsUI(self)
        self.vlm_settings = VLMSettingsUI(self)
        self.vlm_settings = VLMSettingsUI(self)

    def open_node_settings(self, node):
        """ノード設定ダイアログを開く"""
        node_type = node['type']
        
        # 既存のダイアログがあれば削除
        if dpg.does_item_exist("node_settings_window"):
            dpg.delete_item("node_settings_window")
        
        # ダイアログのサイズと位置（Refiner対応でさらに高さを増加）
        dialog_width = 520
        dialog_height = 850 if node_type == 'refiner' else 600
        
        with dpg.window(
            label=f"ノード設定 - {node_type} (ID: {node['id']})",
            width=dialog_width,
            height=dialog_height,
            pos=(300, 100),
            modal=True,
            tag="node_settings_window"
        ):
            # 基本情報
            dpg.add_text(f"ノードタイプ: {node_type}")
            dpg.add_text(f"ノードID: {node['id']}")
            dpg.add_separator()
            
            # スクロール可能なエリアで設定項目を囲む
            with dpg.child_window(height=dialog_height-120, tag="settings_scroll_area"):
                # エージェントタイプ別の設定
                self.create_agent_settings(node)
            
            dpg.add_separator()
            
            # ボタン
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="保存",
                    callback=lambda: self.save_node_settings(node),
                    width=100
                )
                dpg.add_button(
                    label="キャンセル",
                    callback=lambda: dpg.delete_item("node_settings_window"),
                    width=100
                )
                dpg.add_button(
                    label="デフォルトに戻す",
                    callback=lambda: self.reset_node_settings(node),
                    width=120
                )

    def create_agent_settings(self, node):
        """エージェント設定UIを作成（共通化版）"""
        node_type = node['type']
        config = node['config']
        
        # メタデータを取得
        try:
            metadata = get_gui_metadata(node_type)
            description = metadata['description']
        except (KeyError, ValueError):
            description = "設定なし"
        
        # Refiner以外は説明文とLLM設定を表示
        if node_type != 'refiner':
            dpg.add_text(f"説明: {description}", color=(180, 180, 180))
            dpg.add_separator()
            
            # LLM設定情報表示（Retriever以外）
            if node_type != 'retriever':
                dpg.add_text("LLM設定", color=(200, 200, 255))
                current_llm = self.get_current_llm_config()
                dpg.add_text(f"使用モデル: {current_llm}", color=(150, 200, 150))
                dpg.add_text("LLMモデルの変更はログインタブで行ってください", color=(180, 180, 180))
                dpg.add_separator()
        
        # エージェント固有の設定UI
        if node_type == 'retriever':
            self.retriever_settings.create_settings(node)
        elif node_type == 'analyzer':
            self.create_analyzer_settings(node)
        elif node_type == 'domain_expert':
            self.create_domain_expert_settings(node)
        elif node_type == 'validator':
            self.create_validator_settings(node)
        elif node_type == 'refiner':
            self.create_refiner_settings(node)
        elif node_type == 'router':
            self.create_router_settings(node)
        elif node_type == 'vlm':
            self.create_vlm_settings(node)

    def get_current_llm_config(self):
        """ログインタブで設定されたLLM設定を取得"""
        try:
            import json
            import os
            
            config_file = os.path.join("configs", "llm_config.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    llm_config = json.load(f)
                
                provider = llm_config.get('provider', 'Unknown')
                
                if provider == "Azure OpenAI API" or provider == "Azure OpenAI CLI":
                    model = llm_config.get('deployment_name', 'Unknown')
                elif provider == "AWS Bedrock":
                    model = llm_config.get('model_id', 'Unknown')
                else:
                    model = llm_config.get('model', 'Unknown')
                
                return f"{provider}: {model}"
            else:
                return "LLM設定ファイルなし"
                
        except Exception:
            return "ログインタブで設定してください"

    # === Analyzer設定 ===
    
    def create_analyzer_settings(self, node):
        """Analyzer詳細設定UI（統合版）"""
        config = node['config']
        ui_config = self._convert_node_config_to_analyzer_ui(config)
        self.analyzer_settings.create_analyzer_settings_ui(node, ui_config)

    # === DomainExpert設定 ===
    
    def create_domain_expert_settings(self, node):
        """Domain Expert詳細設定UI（統合版）"""
        config = node['config']
        ui_config = self._convert_node_config_to_domain_expert_ui(config)
        self.domain_expert_settings.create_domain_expert_settings_ui(node, ui_config)

    # === Validator設定 ===
    
    def create_validator_settings(self, node):
        """Validator詳細設定UI（統合版）"""
        config = node['config']
        ui_config = self._convert_node_config_to_validator_ui(config)
        self.validator_settings.create_validator_settings_ui(node, ui_config)

    # === Refiner設定 ===
    
    def create_refiner_settings(self, node):
        """Refiner詳細設定UI（RefinerSettingsUIに完全委譲）"""
        config = node['config']
        ui_config = self._convert_node_config_to_refiner_ui(config)
        parent_id = "settings_scroll_area"
        
        # RefinerSettingsUIを作成（重複を避けるためクリーンアップしてから作成）
        if self.refiner_settings is not None:
            try:
                self.refiner_settings.cleanup()
            except:
                pass
        
        self.refiner_settings = RefinerSettingsUI(
            parent_id=parent_id,
            config_values=ui_config,
            on_change_callback=lambda key, value: self._on_refiner_config_change(node, key, value),
            on_save_callback=lambda: self._save_refiner_config(node)
        )

    # === Router設定 ===
    
    def create_router_settings(self, node):
        """Router詳細設定UI（統合版）"""
        config = node['config']
        ui_config = self._convert_node_config_to_router_ui(config)
        self.router_settings.create_router_settings_ui(node, ui_config)

    # === VLM設定 ===
    
    def create_vlm_settings(self, node):
        """VLM詳細設定UI（統合版）"""
        config = node['config']
        ui_config = self._convert_node_config_to_vlm_ui(config)
        self.vlm_settings.create_vlm_settings_ui(node, ui_config)

    # === 保存処理（統合版） ===
    
    def save_node_settings(self, node):
        """ノード設定を保存（統合版）"""
        node_id = node['id']
        node_type = node['type']
        
        try:
            # エージェント固有の保存処理
            if node_type == 'retriever':
                self._save_retriever_config(node)
            elif node_type == 'analyzer':
                self._save_analyzer_config(node)
            elif node_type == 'domain_expert':
                self._save_domain_expert_config(node)
            elif node_type == 'validator':
                self._save_validator_config(node)
            elif node_type == 'refiner':
                self._save_refiner_config(node)
            elif node_type == 'router':
                self._save_router_config(node)
            elif node_type == 'vlm':
                self._save_vlm_config(node)
            
            # ダイアログを閉じる
            if dpg.does_item_exist("node_settings_window"):
                dpg.delete_item("node_settings_window")
            
            # 選択中ノード情報を更新
            if dpg.does_item_exist("selected_info"):
                dpg.set_value("selected_info", f"ID:{node_id} {node_type} (設定更新済み)")
            
            # キャンバスを更新
            if hasattr(self.designer, 'canvas_manager'):
                self.designer.canvas_manager.refresh_canvas()
            
            print(f"ノード設定保存完了: {node_type} ID={node_id}")
            
        except Exception as e:
            print(f"ノード設定保存エラー: {node_type} ID={node_id} - {e}")
            import traceback
            traceback.print_exc()
            
            # エラーが発生してもダイアログを閉じる
            if dpg.does_item_exist("node_settings_window"):
                dpg.delete_item("node_settings_window")

    def _save_retriever_config(self, node):
        """Retriever設定を保存（統合UI対応版）"""
        node_id = node['id']
        
        try:
            config_data = self.retriever_settings.extract_values(node_id)
            node['config'].update(config_data)
            
            print(f"Retriever設定保存完了: ID={node_id}")
            print(f"  - 設定項目数: {len(config_data)}")
            for key, value in config_data.items():
                print(f"  - {key}: {value}")
                
        except Exception as e:
            print(f"Retriever設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
            self._save_retriever_fallback(node)
    
    def _save_retriever_fallback(self, node):
        """Retriever設定フォールバック保存"""
        node_id = node['id']
        
        try:
            if dpg.does_item_exist(f"target_collections_{node_id}"):
                collection_text = dpg.get_value(f"target_collections_{node_id}")
                # コレクション名をそのまま使用（新しい3つのASTコレクションにも対応）
                if collection_text:
                    # テキストから実際のコレクション名を抽出
                    if "rag_documents_pdf" in collection_text:
                        target_collection = 'rag_documents_pdf'
                    elif "rag_documents_ast_packages" in collection_text:
                        target_collection = 'rag_documents_ast_packages'
                    elif "rag_documents_ast_functions" in collection_text:
                        target_collection = 'rag_documents_ast_functions'
                    elif "rag_documents_ast_equations" in collection_text:
                        target_collection = 'rag_documents_ast_equations'
                    else:
                        # デフォルト
                        target_collection = 'rag_documents_pdf'
                else:
                    target_collection = 'rag_documents_pdf'
                
                node['config']['target_collections'] = [target_collection]
            
            if dpg.does_item_exist(f"search_k_{node_id}"):
                node['config']['search_k'] = dpg.get_value(f"search_k_{node_id}")
            if dpg.does_item_exist(f"similarity_threshold_{node_id}"):
                node['config']['similarity_threshold'] = dpg.get_value(f"similarity_threshold_{node_id}")
            if dpg.does_item_exist(f"use_reranker_{node_id}"):
                node['config']['use_reranker'] = dpg.get_value(f"use_reranker_{node_id}")
            if dpg.does_item_exist(f"initial_k_{node_id}"):
                node['config']['initial_k'] = dpg.get_value(f"initial_k_{node_id}")
            
            if dpg.does_item_exist(f"logging_level_{node_id}"):
                logging_text = dpg.get_value(f"logging_level_{node_id}")
                logging_level = "VERBOSE" if logging_text and "VERBOSE" in logging_text else "MINIMAL"
                node['config']['logging_level'] = logging_level
            
            print(f"Retriever基本設定のみ保存: ID={node_id}")
            
        except Exception as e:
            print(f"Retrieverフォールバック保存エラー: {e}")

    def _save_analyzer_config(self, node):
        """Analyzer設定を保存（修正版）"""
        node_id = node['id']
        
        try:
            config_data = self.analyzer_settings.get_analyzer_config_for_node(node_id)
            
            if 'logging_level' in config_data:
                config_data['log_level'] = config_data['logging_level']
            
            node['config'].update(config_data)
            
            print(f"Analyzer設定保存完了: ID={node_id}")
            print(f"  - 設定項目数: {len(config_data)}")
        except Exception as e:
            print(f"Analyzer設定保存エラー: {e}")
            self._save_analyzer_fallback(node)
    
    def _save_analyzer_fallback(self, node):
        """Analyzer設定保存のフォールバック処理"""
        node_id = node['id']
        
        try:
            if dpg.does_item_exist(f"analysis_depth_{node_id}"):
                node['config']['analysis_depth'] = dpg.get_value(f"analysis_depth_{node_id}")
            
            print(f"Analyzer設定フォールバック保存完了: ID={node_id}")
        except Exception as e:
            print(f"Analyzer設定フォールバック保存エラー: {e}")

    def _save_domain_expert_config(self, node):
        """DomainExpert設定を保存（修正版）"""
        node_id = node['id']
        
        try:
            config_data = self.domain_expert_settings.get_domain_expert_config_for_node(node_id)
            
            if 'log_level' in config_data:
                config_data['logging_level'] = config_data['log_level']
            
            node['config'].update(config_data)
            
            print(f"DomainExpert設定保存完了: ID={node_id}")
            print(f"  - 設定項目数: {len(config_data)}")
            print(f"  - min_facts_count: {config_data.get('min_facts_count', 'なし')}")
            print(f"  - min_insights_count: {config_data.get('min_insights_count', 'なし')}")
                
        except Exception as e:
            print(f"DomainExpert設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
            self._save_domain_expert_fallback(node)
    
    def _save_domain_expert_fallback(self, node):
        """DomainExpert設定フォールバック保存"""
        node_id = node['id']
        
        try:
            if dpg.does_item_exist(f"expertise_domain_{node_id}"):
                node['config']['expertise_domain'] = dpg.get_value(f"expertise_domain_{node_id}")
            
            if dpg.does_item_exist(f"max_context_chars_{node_id}"):
                node['config']['max_context_chars'] = dpg.get_value(f"max_context_chars_{node_id}")
            
            if dpg.does_item_exist(f"log_level_{node_id}"):
                node['config']['log_level'] = dpg.get_value(f"log_level_{node_id}")
            
            print(f"DomainExpert基本設定のみ保存: ID={node_id}")
            
        except Exception as e:
            print(f"DomainExpertフォールバック保存エラー: {e}")

    def _save_validator_config(self, node):
        """Validator設定を保存（修正版）"""
        node_id = node['id']
        
        try:
            config_data = self.validator_settings.get_validator_config_for_node(node_id)
            
            if 'logging_level' in config_data:
                config_data['log_level'] = config_data['logging_level']
            
            node['config'].update(config_data)
            
            print(f"Validator設定保存完了: ID={node_id}")
            print(f"  - 設定項目数: {len(config_data)}")
        except Exception as e:
            print(f"Validator設定保存エラー: {e}")
            self._save_validator_fallback(node)
    
    def _save_validator_fallback(self, node):
        """Validator設定保存のフォールバック処理"""
        node_id = node['id']
        
        try:
            if dpg.does_item_exist(f"confidence_threshold_{node_id}"):
                node['config']['confidence_threshold'] = dpg.get_value(f"confidence_threshold_{node_id}")
            
            print(f"Validator設定フォールバック保存完了: ID={node_id}")
        except Exception as e:
            print(f"Validator設定フォールバック保存エラー: {e}")

    def _save_refiner_config(self, node):
        """Refiner設定を保存（修正版）"""
        try:
            if self.refiner_settings:
                # UIから最新値を強制取得（重要！）
                current_config = self.refiner_settings.get_config_values()
                print(f"[DEBUG] Refiner current_config keys: {list(current_config.keys())}")
                print(f"[DEBUG] Refiner sections: {len(current_config.get('sections', []))}個")
                print(f"[DEBUG] Refiner llm_prompts keys: {list(current_config.get('llm_prompts', {}).keys())}")
                
                # 基本設定を直接保存
                for key in ['min_answer_length', 'max_answer_length', 'enable_regeneration']:
                    if key in current_config:
                        node['config'][key] = current_config[key]
                
                # ログレベル
                if 'logging_level' in current_config:
                    node['config']['logging_level'] = current_config['logging_level']
                    node['config']['log_level'] = current_config['logging_level']
                
                # フォーマット設定（トップレベル）
                for key in ['response_format', 'use_code_blocks', 'include_citations', 
                           'structure_with_headers', 'expert_attribution', 'technical_terminology']:
                    if key in current_config:
                        node['config'][key] = current_config[key]
                
                # output_structure構築
                node['config']['output_structure'] = {
                    'response_format': current_config.get('response_format', 'technical_documentation'),
                    'sections': current_config.get('sections', []),  # 空リストも保存
                    'formatting_rules': {
                        'use_code_blocks': current_config.get('use_code_blocks', True),
                        'include_citations': current_config.get('include_citations', True),
                        'structure_with_headers': current_config.get('structure_with_headers', True),
                        'expert_attribution': current_config.get('expert_attribution', True),
                        'technical_terminology': current_config.get('technical_terminology', 'preserve')
                    }
                }
                
                # llm_prompts保存
                if 'llm_prompts' in current_config:
                    node['config']['llm_prompts'] = current_config['llm_prompts']
                
                print("Refiner設定保存完了")
                print(f"  - sections保存: {len(node['config']['output_structure']['sections'])}個")
                print(f"  - llm_prompts保存: {list(node['config'].get('llm_prompts', {}).keys())}")
                
        except Exception as e:
            print(f"Refiner設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
            self._save_refiner_fallback(node)
    
    def _save_refiner_fallback(self, node):
        """Refiner設定フォールバック保存"""
        node_id = node['id']
        
        try:
            if dpg.does_item_exist(f"min_answer_length_{node_id}"):
                node['config']['min_answer_length'] = dpg.get_value(f"min_answer_length_{node_id}")
            
            if dpg.does_item_exist(f"max_answer_length_{node_id}"):
                node['config']['max_answer_length'] = dpg.get_value(f"max_answer_length_{node_id}")
                
            if dpg.does_item_exist(f"log_level_{node_id}"):
                node['config']['log_level'] = dpg.get_value(f"log_level_{node_id}")
            
            print(f"Refiner基本設定のみ保存: ID={node_id}")
            
        except Exception as e:
            print(f"Refinerフォールバック保存エラー: {e}")

    def _save_router_config(self, node):
        """Router設定を保存（修正版 - 接続情報から自動構築）"""
        node_id = node['id']
        
        try:
            if self.router_settings:
                # UIから現在の設定値を取得
                current_config = self.router_settings.get_ui_config(node_id)
                
                # 基本設定を直接保存
                if 'max_iterations' in current_config:
                    max_iter_value = current_config['max_iterations']
                    if isinstance(max_iter_value, dict) and 'value' in max_iter_value:
                        node['config']['max_iterations'] = max_iter_value['value']
                    else:
                        node['config']['max_iterations'] = max_iter_value
                
                if 'logging_level' in current_config:
                    node['config']['logging_level'] = current_config['logging_level']
                    node['config']['log_level'] = current_config['logging_level']
                
                # routing_rules を保存（接続情報から構築）
                if 'routing_rules' in current_config:
                    routing_rules = current_config['routing_rules']
                    
                    # 空のtargetがある場合は接続情報から補完
                    if 'default' in routing_rules and not routing_rules['default'].get('target'):
                        # 接続先ノードを取得
                        connected_nodes = self._get_connected_target_nodes(node_id)
                        if connected_nodes:
                            routing_rules['default']['target'] = connected_nodes[0]
                            routing_rules['default']['description'] = f'Default route to: {connected_nodes[0]}'
                    
                    if 'max_iterations_exceeded' in routing_rules and not routing_rules['max_iterations_exceeded'].get('target'):
                        connected_nodes = self._get_connected_target_nodes(node_id)
                        if connected_nodes:
                            routing_rules['max_iterations_exceeded']['target'] = connected_nodes[0]
                            routing_rules['max_iterations_exceeded']['description'] = f'Max iterations exceeded route to: {connected_nodes[0]}'
                    
                    node['config']['routing_rules'] = routing_rules
                    print(f"Router routing_rules保存: {routing_rules}")
                
                print(f"Router設定保存完了: ID={node_id}")
                
        except Exception as e:
            print(f"Router設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_connected_target_nodes(self, node_id: int) -> list:
        """Routerノードから接続している先のノードIDリストを取得"""
        try:
            connected_nodes = []
            
            if hasattr(self.designer, 'connections'):
                for connection in self.designer.connections:
                    from_node = connection.get('from')
                    to_node = connection.get('to')
                    
                    # このRouterノードから出ている接続のみを対象
                    if from_node == node_id and to_node:
                        target_node = f"node_{to_node}"
                        if target_node not in connected_nodes:
                            connected_nodes.append(target_node)
            
            return connected_nodes
            
        except Exception as e:
            print(f"接続先ノード取得エラー: {e}")
            return []
    
    def _save_vlm_config(self, node):
        """VLM設定を保存（全パラメータ対応版）"""
        node_id = node['id']
        
        try:
            if self.vlm_settings:
                # UIから現在の設定値を取得
                current_config = self.vlm_settings.get_ui_config(node_id)
                
                # すべてのVLM生成パラメータを保存
                vlm_params = [
                    'preset', 'temperature', 'top_p', 'top_k', 'do_sample',
                    'max_new_tokens', 'min_new_tokens', 'repetition_penalty',
                    'no_repeat_ngram_size', 'num_beams', 'length_penalty',
                    'diversity_penalty', 'early_stopping'
                ]
                
                for param in vlm_params:
                    if param in current_config:
                        node['config'][param] = current_config[param]
                
                # ログレベル保存
                if 'logging_level' in current_config:
                    node['config']['logging_level'] = current_config['logging_level']
                    node['config']['log_level'] = current_config['logging_level']
                
                print(f"VLM設定保存完了: ID={node_id}")
                print(f"  - 保存されたパラメータ数: {len([p for p in vlm_params if p in current_config])}")
                if 'preset' in current_config:
                    print(f"  - プリセット: {current_config['preset']}")
                
        except Exception as e:
            print(f"VLM設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def reset_node_settings(self, node):
        """ノード設定をデフォルトに戻す（統合UI対応版）"""
        try:
            node_type = node['type']
            node_id = node['id']
            
            if node_type == 'retriever':
                self.retriever_settings.reset_to_defaults(node_id)
            elif node_type == 'analyzer':
                if hasattr(self.analyzer_settings, 'reset_to_defaults'):
                    self.analyzer_settings.reset_to_defaults(node_id)
                else:
                    self._reset_analyzer_fallback(node, node_id)
            elif node_type == 'domain_expert':
                self.domain_expert_settings.reset_to_defaults(node_id)
            elif node_type == 'validator':
                if hasattr(self.validator_settings, 'reset_to_defaults'):
                    self.validator_settings.reset_to_defaults(node_id)
                else:
                    self._reset_validator_fallback(node, node_id)
            elif node_type == 'refiner':
                self.refiner_settings.reset_to_defaults(node_id)
            elif node_type == 'router':
                if hasattr(self.router_settings, 'reset_to_defaults'):
                    self.router_settings.reset_to_defaults(node_id)
                else:
                    self._reset_router_fallback(node, node_id)
            elif node_type == 'vlm':
                if hasattr(self.vlm_settings, 'reset_to_defaults'):
                    self.vlm_settings.reset_to_defaults(node_id)
                else:
                    self._reset_vlm_fallback(node, node_id)
            
            print(f"{node_type}設定をデフォルトにリセットしました")
            
        except Exception as e:
            print(f"デフォルトリセットエラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _reset_analyzer_fallback(self, node, node_id):
        """Analyzerデフォルトリセット（フォールバック）"""
        try:
            default_config = get_default_node_config('analyzer')
            
            if dpg.does_item_exist(f"analysis_depth_{node_id}"):
                dpg.set_value(f"analysis_depth_{node_id}", default_config.get('analysis_depth', 'COMPREHENSIVE'))
            if dpg.does_item_exist(f"logging_level_{node_id}"):
                dpg.set_value(f"logging_level_{node_id}", default_config.get('logging_level', 'VERBOSE'))
        except Exception as e:
            print(f"Analyzerフォールバックリセットエラー: {e}")
    
    def _reset_validator_fallback(self, node, node_id):
        """Validatorデフォルトリセット（フォールバック）"""
        try:
            default_config = get_default_node_config('validator')
            
            if dpg.does_item_exist(f"confidence_threshold_{node_id}"):
                dpg.set_value(f"confidence_threshold_{node_id}", default_config.get('confidence_threshold', 0.8))
            if dpg.does_item_exist(f"logging_level_{node_id}"):
                dpg.set_value(f"logging_level_{node_id}", default_config.get('logging_level', 'VERBOSE'))
        except Exception as e:
            print(f"Validatorフォールバックリセットエラー: {e}")
    
    def _reset_router_fallback(self, node, node_id):
        """Routerデフォルトリセット（フォールバック）"""
        try:
            if dpg.does_item_exist(f"max_iterations_{node_id}"):
                dpg.set_value(f"max_iterations_{node_id}", 1)
        except Exception as e:
            print(f"Routerフォールバックリセットエラー: {e}")
    
    def _reset_vlm_fallback(self, node, node_id):
        """VLMデフォルトリセット（フォールバック）"""
        try:
            default_config = VLMConfig.get_default_config()
            
            # すべてのパラメータをデフォルトに戻す
            all_keys = [
                'preset', 'temperature', 'top_p', 'top_k', 'do_sample',
                'max_new_tokens', 'min_new_tokens', 'repetition_penalty',
                'no_repeat_ngram_size', 'num_beams', 'length_penalty',
                'diversity_penalty', 'early_stopping', 'logging_level'
            ]
            
            for key in all_keys:
                tag = f"{key}_{node_id}"
                if dpg.does_item_exist(tag):
                    default_value = default_config.get(key)
                    
                    # プリセットの場合は表示名に変換
                    if key == 'preset' and default_value is None:
                        default_value = 'なし（カスタム設定）'
                    
                    dpg.set_value(tag, default_value)
                
                # ノード設定も更新
                if key in default_config:
                    node['config'][key] = default_config[key]
            
        except Exception as e:
            print(f"VLMフォールバックリセットエラー: {e}")

    # === 統合設定変換メソッド ===
    
    def _convert_node_config_to_analyzer_ui(self, node_config):
        """ノード設定をAnalyzer UI用設定に変換"""
        default_config = AnalyzerConfig.get_default_config()
        ui_config = deepcopy(default_config)
        
        if 'analysis_depth' in node_config:
            analysis_depth_value = node_config['analysis_depth']
            if isinstance(analysis_depth_value, dict) and 'value' in analysis_depth_value:
                ui_config['analysis_depth'] = analysis_depth_value['value']
            else:
                ui_config['analysis_depth'] = analysis_depth_value
        
        if 'llm_prompts' in node_config:
            llm_prompts = node_config['llm_prompts']
            if isinstance(llm_prompts, dict) and 'value' in llm_prompts:
                llm_prompts = llm_prompts['value']
            
            if isinstance(llm_prompts, dict):
                for key, value in llm_prompts.items():
                    if key in ['base_instruction', 'optimization_focus', 'output_format', 
                              'quality_criteria', 'query_optimization_rules']:
                        ui_config[key] = value
                
                ui_config['llm_prompts'] = llm_prompts
        
        if 'final_prompt_template' in node_config:
            ui_config['final_prompt_template'] = node_config['final_prompt_template']
        
        if 'logging_level' in node_config:
            ui_config['logging_level'] = node_config['logging_level']
        
        return ui_config
    
    def _convert_node_config_to_domain_expert_ui(self, node_config):
        """ノード設定をDomain Expert UI用設定に変換"""
        default_config = DomainExpertConfig.get_default_config()
        ui_config = deepcopy(default_config)
        
        if 'expertise_domain' in node_config:
            ui_config['expertise_domain'] = node_config['expertise_domain']
        
        if 'expert_profile' in node_config:
            expert_profile = node_config['expert_profile']
            if isinstance(expert_profile, dict):
                ui_config['specialization'] = expert_profile.get('specialization', '')
                
                knowledge_areas = expert_profile.get('knowledge_areas', [])
                if isinstance(knowledge_areas, list):
                    ui_config['knowledge_areas'] = ', '.join(knowledge_areas)
                else:
                    ui_config['knowledge_areas'] = str(knowledge_areas)
                
                ui_config['analysis_focus'] = expert_profile.get('analysis_focus', '')
                ui_config['expert_profile'] = expert_profile
        
        if 'max_context_chars' in node_config:
            ui_config['max_context_chars'] = str(node_config['max_context_chars'])
        
        if 'log_level' in node_config:
            ui_config['log_level'] = node_config['log_level']
        
        if 'llm_prompts' in node_config:
            llm_prompts = node_config['llm_prompts']
            if isinstance(llm_prompts, dict) and 'value' in llm_prompts:
                llm_prompts = llm_prompts['value']
            
            if isinstance(llm_prompts, dict):
                for key, value in llm_prompts.items():
                    if key in ['expert_identity', 'analysis_instruction', 'output_format', 
                              'confidence_guidance', 'quality_focus', 'content_constraints']:
                        ui_config[key] = value
                
                if 'final_prompt_template' in llm_prompts:
                    ui_config['final_prompt_template'] = llm_prompts['final_prompt_template']
                
                ui_config['llm_prompts'] = llm_prompts
        
        return ui_config
    
    def _convert_node_config_to_refiner_ui(self, node_config):
        """ノード設定をRefiner UI用設定に変換"""
        print(f"[DEBUG] _convert_node_config_to_refiner_ui開始")
        print(f"[DEBUG] node_config keys: {list(node_config.keys())}")
        
        # 重要: DEFAULT_VALUESを使用（sectionsを含まない基本設定のみ）
        import copy
        ui_config = copy.deepcopy(RefinerConfig.DEFAULT_VALUES)
        
        # sectionsキーは初期状態では存在しない（UIで初回表示時に判断）
        if 'sections' in ui_config:
            del ui_config['sections']
        
        print(f"[DEBUG] デフォルトconfig初期化完了（sectionsなし）")
        
        try:
            # 基本設定の読み込み
            if 'min_answer_length' in node_config:
                ui_config['min_answer_length'] = node_config['min_answer_length']
            if 'max_answer_length' in node_config:
                ui_config['max_answer_length'] = node_config['max_answer_length']
            if 'enable_regeneration' in node_config:
                ui_config['enable_regeneration'] = node_config['enable_regeneration']
            if 'log_level' in node_config:
                ui_config['logging_level'] = node_config['log_level']
            if 'logging_level' in node_config:
                ui_config['logging_level'] = node_config['logging_level']
            
            # フォーマット設定の読み込み（トップレベル + output_structure内の両方をチェック）
            if 'response_format' in node_config:
                ui_config['response_format'] = node_config['response_format']
            if 'use_code_blocks' in node_config:
                ui_config['use_code_blocks'] = node_config['use_code_blocks']
            if 'include_citations' in node_config:
                ui_config['include_citations'] = node_config['include_citations']
            if 'structure_with_headers' in node_config:
                ui_config['structure_with_headers'] = node_config['structure_with_headers']
            if 'expert_attribution' in node_config:
                ui_config['expert_attribution'] = node_config['expert_attribution']
            if 'technical_terminology' in node_config:
                ui_config['technical_terminology'] = node_config['technical_terminology']
            
            # sectionsの読み込み優先順位と処理
            sections_found = False
            sections_data = None
            
            # 1. output_structure内のsectionsを優先
            if 'output_structure' in node_config:
                output_structure = node_config['output_structure']
                
                # output_structure内のresponse_format
                if 'response_format' in output_structure:
                    ui_config['response_format'] = output_structure['response_format']
                
                # formatting_rules内の設定を読み込み
                if 'formatting_rules' in output_structure:
                    formatting_rules = output_structure['formatting_rules']
                    if isinstance(formatting_rules, dict):
                        if 'use_code_blocks' in formatting_rules:
                            ui_config['use_code_blocks'] = formatting_rules['use_code_blocks']
                        if 'include_citations' in formatting_rules:
                            ui_config['include_citations'] = formatting_rules['include_citations']
                        if 'structure_with_headers' in formatting_rules:
                            ui_config['structure_with_headers'] = formatting_rules['structure_with_headers']
                        if 'expert_attribution' in formatting_rules:
                            ui_config['expert_attribution'] = formatting_rules['expert_attribution']
                        if 'technical_terminology' in formatting_rules:
                            ui_config['technical_terminology'] = formatting_rules['technical_terminology']
                
                # output_structure内のsections
                if 'sections' in output_structure:
                    sections_data = output_structure['sections']
                    sections_found = True
                    print(f"[DEBUG] output_structure.sections発見: {len(sections_data) if isinstance(sections_data, list) else '不正'}個")
            
            # 2. トップレベルのsectionsをチェック（output_structureに無い場合）
            if not sections_found and 'sections' in node_config:
                sections_data = node_config['sections']
                sections_found = True
                print(f"[DEBUG] トップレベルsections発見: {len(sections_data) if isinstance(sections_data, list) else '不正'}個")
            
            # 3. sectionsデータの処理
            if sections_found and isinstance(sections_data, list):
                # sectionsが見つかった場合
                if len(sections_data) > 0:
                    # データあり: そのまま使用
                    ui_config['sections'] = sections_data
                    print(f"[DEBUG] sections読み込み: {len(sections_data)}個")
                else:
                    # 空リスト: ユーザーが削除したので空を保持
                    ui_config['sections'] = []
                    print(f"[DEBUG] sections空リスト保持（削除済み）")
            else:
                # sectionsキーが存在しない: デフォルトを維持（get_default_config()で設定済み）
                print(f"[DEBUG] sections未保存、デフォルト{len(ui_config.get('sections', []))}個を維持")
            
            # llm_promptsの読み込み
            if 'llm_prompts' in node_config:
                # llm_promptsが存在し、かつ空でない場合のみ上書き
                if isinstance(node_config['llm_prompts'], dict) and node_config['llm_prompts']:
                    ui_config['llm_prompts'] = node_config['llm_prompts']
                # 空の場合はデフォルトを使用（すでにget_default_config()で設定済み）
                
            print(f"Refiner UI設定変換成功: {len(ui_config)}項目")
            print(f"  - sections: {len(ui_config.get('sections', []))}個")
            print(f"  - llm_prompts: {list(ui_config.get('llm_prompts', {}).keys())}")
            print(f"  - use_code_blocks: {ui_config.get('use_code_blocks')}")
            print(f"  - response_format: {ui_config.get('response_format')}")
            return ui_config
            
        except Exception as e:
            print(f"RefinerConfig変換エラー: {e}")
            import traceback
            traceback.print_exc()
            return ui_config
    
    def _convert_node_config_to_router_ui(self, node_config):
        """ノード設定をRouter UI用設定に変換"""
        default_config = RouterConfig.get_default_config()
        ui_config = deepcopy(default_config)
        
        for field in ['max_iterations', 'logging_level', 'routing_rules']:
            if field in node_config:
                ui_config[field] = node_config[field]
        
        if 'log_level' in node_config:
            ui_config['logging_level'] = node_config['log_level']
        
        return ui_config
    
    def _convert_node_config_to_vlm_ui(self, node_config):
        """ノード設定をVLM UI用設定に変換（全パラメータ対応版）"""
        default_config = VLMConfig.get_default_config()
        ui_config = deepcopy(default_config)
        
        # VLMのすべての生成パラメータを変換
        vlm_params = [
            'preset', 'temperature', 'top_p', 'top_k', 'do_sample',
            'max_new_tokens', 'min_new_tokens', 'repetition_penalty',
            'no_repeat_ngram_size', 'num_beams', 'length_penalty',
            'diversity_penalty', 'early_stopping', 'logging_level'
        ]
        
        for field in vlm_params:
            if field in node_config:
                ui_config[field] = node_config[field]
        
        # log_levelの互換性処理
        if 'log_level' in node_config and 'logging_level' not in node_config:
            ui_config['logging_level'] = node_config['log_level']
        
        return ui_config
    
    def _on_refiner_config_change(self, node, key, value):
        """Refiner設定変更時のコールバック（リアルタイム更新用）"""
        try:
            if key == 'sections':
                # セクション変更は即座にログ出力のみ（保存は保存ボタン時）
                print(f"Refiner sections変更: {len(value) if isinstance(value, list) else '不明'}個")
            else:
                print(f"Refiner設定変更: {key}")
            
            # 変更フラグを立てる
            if hasattr(self.designer, 'mark_modified'):
                self.designer.mark_modified()
                
        except Exception as e:
            print(f"Refiner設定変更コールバックエラー: {e}")
    
    def _convert_node_config_to_validator_ui(self, node_config):
        """ノード設定をValidator UI用設定に変換"""
        default_config = ValidatorConfig.get_default_config()
        ui_config = deepcopy(default_config)

        for field in ['confidence_threshold', 'llm_max_tokens', 'minimum_source_count', 'logging_level']:
            if field in node_config:
                ui_config[field] = node_config[field]

        if 'llm_prompts' in node_config:
            llm_prompts = node_config['llm_prompts']
            if isinstance(llm_prompts, dict) and 'value' in llm_prompts:
                llm_prompts = llm_prompts['value']

            if isinstance(llm_prompts, dict):
                for key, value in llm_prompts.items():
                    if key in ['validation_instruction', 'evaluation_criteria', 'output_format', 'confidence_calculation']:
                        ui_config[key] = value

                if 'final_prompt_template' in llm_prompts:
                    ui_config['final_prompt_template'] = llm_prompts['final_prompt_template']

                ui_config['llm_prompts'] = llm_prompts

        return ui_config
