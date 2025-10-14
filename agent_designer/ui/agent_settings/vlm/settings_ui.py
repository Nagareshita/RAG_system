# agent_designer/ui/agent_settings/vlm/settings_ui.py
"""
VLM設定UI
Vision Language Model エージェントの設定画面
"""

import dearpygui.dearpygui as dpg
from typing import Dict, Any, Callable
import logging

from .config import VLMConfig


class VLMSettingsUI:
    """VLM設定UI管理クラス"""
    
    def __init__(self, parent_manager):
        self.parent_manager = parent_manager
        self.current_nodes = {}  # node_id -> config mapping
        self.logger = logging.getLogger(__name__)
    
    def create_vlm_settings_ui(self, node: Dict[str, Any], ui_config: Dict[str, Any]):
        """VLM設定UI作成（統合版）"""
        node_id = node['id']
        self.current_nodes[node_id] = ui_config
        
        # UI情報取得
        ui_info = VLMConfig.get_ui_info()
        
        with dpg.group(horizontal=True):
            dpg.add_text(f"🖼️ {ui_info['name']}", color=ui_info['color']['text'])
            dpg.add_text(f"- {ui_info['description']}", color=(200, 200, 200))
        
        dpg.add_separator()
        
        # プリセット設定
        self._create_preset_settings(node_id, ui_config)
        
        dpg.add_separator()
        
        # 基本パラメータ設定
        self._create_basic_settings(node_id, ui_config)
        
        # トークン制御設定
        self._create_token_settings(node_id, ui_config)
        
        # 繰り返し制御設定
        self._create_repetition_settings(node_id, ui_config)
        
        # ビームサーチ設定
        self._create_beam_settings(node_id, ui_config)
        
        # ログレベル設定
        self._create_log_settings(node_id, ui_config)
    
    def _create_preset_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """プリセット設定セクションを作成"""
        with dpg.collapsing_header(label="📋 プリセット設定", default_open=True):
            with dpg.group():
                dpg.add_text("タスク別の推奨パラメータを一括設定できます", color=(180, 180, 180))
                self._create_setting_widget(node_id, 'preset', ui_config)
                dpg.add_text("プリセットを選択後、個別パラメータで微調整も可能です", color=(150, 150, 150), wrap=450)
    
    def _create_basic_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """基本パラメータ設定セクションを作成"""
        with dpg.collapsing_header(label="⚙️ 基本パラメータ", default_open=True):
            with dpg.group():
                # Temperature
                self._create_setting_widget(node_id, 'temperature', ui_config)
                
                # Top-p
                self._create_setting_widget(node_id, 'top_p', ui_config)
                
                # Top-k
                self._create_setting_widget(node_id, 'top_k', ui_config)
                
                # Do Sample
                self._create_setting_widget(node_id, 'do_sample', ui_config)
    
    def _create_token_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """トークン制御設定セクションを作成"""
        with dpg.collapsing_header(label="📏 トークン数制御", default_open=False):
            with dpg.group():
                # Max tokens
                self._create_setting_widget(node_id, 'max_new_tokens', ui_config)
                
                # Min tokens
                self._create_setting_widget(node_id, 'min_new_tokens', ui_config)
    
    def _create_repetition_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """繰り返し制御設定セクションを作成"""
        with dpg.collapsing_header(label="🔁 繰り返し制御", default_open=False):
            with dpg.group():
                # Repetition Penalty
                self._create_setting_widget(node_id, 'repetition_penalty', ui_config)
                
                # No-Repeat N-gram Size
                self._create_setting_widget(node_id, 'no_repeat_ngram_size', ui_config)
    
    def _create_beam_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """ビームサーチ設定セクションを作成"""
        with dpg.collapsing_header(label="🔍 ビームサーチ", default_open=False):
            with dpg.group():
                # Num Beams
                self._create_setting_widget(node_id, 'num_beams', ui_config)
                
                # Length Penalty
                self._create_setting_widget(node_id, 'length_penalty', ui_config)
                
                # Diversity Penalty
                self._create_setting_widget(node_id, 'diversity_penalty', ui_config)
                
                # Early Stopping
                self._create_setting_widget(node_id, 'early_stopping', ui_config)
    
    def _create_log_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """ログ設定セクションを作成"""
        with dpg.collapsing_header(label="📝 ログ設定", default_open=False):
            with dpg.group():
                self._create_setting_widget(node_id, 'logging_level', ui_config)
    
    def _create_setting_widget(self, node_id: int, setting_key: str, ui_config: Dict[str, Any]):
        """設定項目に対応するウィジェットを作成"""
        schema = VLMConfig.get_settings_schema()
        
        if setting_key not in schema:
            self.logger.warning(f"未知の設定項目: {setting_key}")
            return
        
        setting_schema = schema[setting_key]
        setting_type = setting_schema['type']
        current_value = ui_config.get(setting_key, VLMConfig.DEFAULT_VALUES.get(setting_key))
        
        # 型変換
        if setting_type == 'int' and current_value is not None:
            try:
                current_value = int(current_value)
            except (ValueError, TypeError):
                current_value = VLMConfig.DEFAULT_VALUES.get(setting_key, 0)
        elif setting_type == 'float' and current_value is not None:
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                current_value = VLMConfig.DEFAULT_VALUES.get(setting_key, 0.0)
        
        widget_tag = f"{setting_key}_{node_id}"
        
        if setting_type == 'int':
            dpg.add_input_int(
                tag=widget_tag,
                label=setting_schema['label'],
                default_value=current_value or 0,
                min_value=setting_schema.get('min_value', 0),
                max_value=setting_schema.get('max_value', 100000),
                width=setting_schema.get('width', 150),
                callback=lambda sender, value: self._on_setting_change(node_id, setting_key, value)
            )
        
        elif setting_type == 'float':
            dpg.add_input_float(
                tag=widget_tag,
                label=setting_schema['label'],
                default_value=current_value or 0.0,
                min_value=setting_schema.get('min_value', 0.0),
                max_value=setting_schema.get('max_value', 1.0),
                step=setting_schema.get('step', 0.01),
                width=setting_schema.get('width', 150),
                callback=lambda sender, value: self._on_setting_change(node_id, setting_key, value)
            )
        
        elif setting_type == 'bool':
            dpg.add_checkbox(
                tag=widget_tag,
                label=setting_schema['label'],
                default_value=current_value if current_value is not None else False,
                callback=lambda sender, value: self._on_setting_change(node_id, setting_key, value)
            )
        
        elif setting_type == 'combo':
            items = [option[0] for option in setting_schema['options']]
            display_items = [option[1] for option in setting_schema['options']]
            
            # プリセット設定の場合は特別処理
            if setting_key == 'preset':
                # 現在値がNoneの場合は「なし（カスタム設定）」を選択
                if current_value is None or current_value == '' or current_value == 'None':
                    display_value = 'なし（カスタム設定）'
                else:
                    # 現在値に対応する表示名を検索
                    display_value = next(
                        (display for value, display in setting_schema['options'] if value == current_value),
                        'なし（カスタム設定）'
                    )
                
                dpg.add_combo(
                    tag=widget_tag,
                    label=setting_schema['label'],
                    items=display_items,
                    default_value=display_value,
                    width=setting_schema.get('width', 200),
                    callback=lambda sender, app_data: self._on_preset_change(node_id, app_data, items, display_items)
                )
            else:
                dpg.add_combo(
                    tag=widget_tag,
                    label=setting_schema['label'],
                    items=items,
                    default_value=current_value or items[0],
                    width=setting_schema.get('width', 200),
                    callback=lambda sender, value: self._on_setting_change(node_id, setting_key, value)
                )
        
        # ヘルプテキスト追加
        if 'description' in setting_schema:
            dpg.add_text(f"  💡 {setting_schema['description']}", color=(150, 150, 150), wrap=450)
    
    def _on_setting_change(self, node_id: int, setting_key: str, value: Any):
        """設定値変更時のコールバック"""
        if node_id in self.current_nodes:
            self.current_nodes[node_id][setting_key] = value
    
    def _on_preset_change(self, node_id: int, display_value: str, items: list, display_items: list):
        """プリセット変更時のコールバック（表示名から実際の値に変換）"""
        try:
            # 表示名から実際の値に変換
            if display_value == 'なし（カスタム設定）':
                preset_value = None
            else:
                # display_itemsのインデックスからitemsの値を取得
                index = display_items.index(display_value)
                preset_value = items[index]
            
            # プリセット値を保存
            if node_id in self.current_nodes:
                self.current_nodes[node_id]['preset'] = preset_value
            
            # プリセットが選択された場合、対応するパラメータを自動設定
            if preset_value is not None:
                self._apply_preset_parameters(node_id, preset_value)
            
        except Exception as e:
            self.logger.error(f"プリセット変更エラー: {e}")
    
    def _apply_preset_parameters(self, node_id: int, preset_name: str):
        """プリセットに対応するパラメータを自動設定"""
        try:
            # model_managerのプリセット定義を取得（仮の定義、実際はmodel_managerから取得すべき）
            preset_params = self._get_preset_parameters(preset_name)
            
            if preset_params:
                # UIとconfigを更新
                for key, value in preset_params.items():
                    tag = f"{key}_{node_id}"
                    if dpg.does_item_exist(tag):
                        dpg.set_value(tag, value)
                    
                    if node_id in self.current_nodes:
                        self.current_nodes[node_id][key] = value
                
                self.logger.info(f"プリセット '{preset_name}' を適用しました")
        
        except Exception as e:
            self.logger.error(f"プリセット適用エラー: {e}")
    
    def _get_preset_parameters(self, preset_name: str) -> Dict[str, Any]:
        """プリセット名に対応するパラメータを取得（model_managerのTASK_PRESETSと一致）"""
        presets = {
            'accurate': {
                'do_sample': False,
                'num_beams': 4,
                'length_penalty': 1.05,
                'min_new_tokens': 64,
                'max_new_tokens': 1024,
                'no_repeat_ngram_size': 3,
                'repetition_penalty': 1.08,
                'temperature': 0.1,
                'top_p': 0.5,
                'top_k': 10,
            },
            'balanced': {
                'do_sample': True,
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 20,
                'min_new_tokens': 32,
                'max_new_tokens': 512,
                'repetition_penalty': 1.0,
                'num_beams': 1,
                'length_penalty': 1.0,
            },
            'ocr': {
                'do_sample': False,
                'num_beams': 5,
                'length_penalty': 1.1,
                'min_new_tokens': 120,
                'max_new_tokens': 2048,
                'no_repeat_ngram_size': 4,
                'repetition_penalty': 1.05,
                'temperature': 0.1,
                'top_p': 0.5,
            },
            'qa': {
                'do_sample': False,
                'num_beams': 4,
                'min_new_tokens': 64,
                'max_new_tokens': 1024,
                'no_repeat_ngram_size': 4,
                'repetition_penalty': 1.05,
                'temperature': 0.2,
                'top_p': 0.7,
            },
            'code': {
                'do_sample': False,
                'num_beams': 4,
                'length_penalty': 0.98,
                'min_new_tokens': 128,
                'max_new_tokens': 2048,
                'no_repeat_ngram_size': 6,
                'repetition_penalty': 1.08,
                'temperature': 0.1,
                'top_p': 0.5,
            },
            'creative': {
                'do_sample': True,
                'temperature': 0.9,
                'top_p': 0.92,
                'min_new_tokens': 80,
                'max_new_tokens': 1024,
                'repetition_penalty': 1.02,
                'num_beams': 1,
            },
            'summary': {
                'do_sample': False,
                'num_beams': 3,
                'length_penalty': 0.95,
                'min_new_tokens': 80,
                'max_new_tokens': 800,
                'no_repeat_ngram_size': 4,
                'temperature': 0.2,
            },
            'json': {
                'do_sample': False,
                'num_beams': 6,
                'min_new_tokens': 80,
                'max_new_tokens': 1600,
                'no_repeat_ngram_size': 4,
                'repetition_penalty': 1.05,
                'temperature': 0.1,
            }
        }
        return presets.get(preset_name, {})
    
    def get_ui_config(self, node_id: int) -> Dict[str, Any]:
        """現在の設定値を取得"""
        self._sync_ui_to_config(node_id)
        return self.current_nodes.get(node_id, {}).copy()
    
    def _sync_ui_to_config(self, node_id: int):
        """UIの全入力フィールドから最新値を強制取得してconfigに反映"""
        try:
            if node_id not in self.current_nodes:
                return
            
            # すべての設定キーを同期
            all_keys = [
                'preset', 'temperature', 'top_p', 'top_k', 'do_sample',
                'max_new_tokens', 'min_new_tokens', 'repetition_penalty',
                'no_repeat_ngram_size', 'num_beams', 'length_penalty',
                'diversity_penalty', 'early_stopping', 'logging_level'
            ]
            
            for setting_key in all_keys:
                tag = f"{setting_key}_{node_id}"
                if dpg.does_item_exist(tag):
                    value = dpg.get_value(tag)
                    
                    # プリセットの場合は表示名から値に変換
                    if setting_key == 'preset':
                        schema = VLMConfig.get_settings_schema()['preset']
                        display_items = [option[1] for option in schema['options']]
                        items = [option[0] for option in schema['options']]
                        
                        if value in display_items:
                            index = display_items.index(value)
                            value = items[index]
                    
                    self.current_nodes[node_id][setting_key] = value
            
            self.logger.debug("UIから設定への同期完了")
            
        except Exception as e:
            self.logger.error(f"UI同期エラー: {e}")
    
    def reset_to_defaults(self, node_id: int):
        """設定をデフォルトに戻す"""
        try:
            default_config = VLMConfig.get_default_config()
            self.current_nodes[node_id] = default_config.copy()
            
            # すべてのUI要素を明示的にデフォルトに戻す
            all_keys = [
                'preset', 'temperature', 'top_p', 'top_k', 'do_sample',
                'max_new_tokens', 'min_new_tokens', 'repetition_penalty',
                'no_repeat_ngram_size', 'num_beams', 'length_penalty',
                'diversity_penalty', 'early_stopping', 'logging_level'
            ]
            
            for setting_key in all_keys:
                tag = f"{setting_key}_{node_id}"
                if dpg.does_item_exist(tag):
                    default_value = default_config.get(setting_key)
                    
                    # プリセットの場合は表示名に変換
                    if setting_key == 'preset':
                        if default_value is None:
                            default_value = 'なし（カスタム設定）'
                        else:
                            schema = VLMConfig.get_settings_schema()['preset']
                            default_value = next(
                                (display for value, display in schema['options'] if value == default_value),
                                'なし（カスタム設定）'
                            )
                    
                    dpg.set_value(tag, default_value)
            
            print(f"VLM設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"VLMデフォルト復元エラー: {e}")
