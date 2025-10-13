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
        
        # 生成パラメータ設定
        self._create_generation_settings(node_id, ui_config)
    
    def _create_generation_settings(self, node_id: int, ui_config: Dict[str, Any]):
        """生成パラメータ設定セクションを作成"""
        with dpg.collapsing_header(label="生成パラメータ", default_open=True):
            with dpg.group():
                # Temperature
                self._create_setting_widget(node_id, 'temperature', ui_config)
                
                # Top-p
                self._create_setting_widget(node_id, 'top_p', ui_config)
                
                # Top-k
                self._create_setting_widget(node_id, 'top_k', ui_config)
                
                # Max tokens
                self._create_setting_widget(node_id, 'max_new_tokens', ui_config)
    
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
        
        elif setting_type == 'combo':
            items = [option[0] for option in setting_schema['options']]
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
            dpg.add_text(f"  💡 {setting_schema['description']}", color=(150, 150, 150), wrap=400)
    
    def _on_setting_change(self, node_id: int, setting_key: str, value: Any):
        """設定値変更時のコールバック"""
        if node_id in self.current_nodes:
            self.current_nodes[node_id][setting_key] = value
    
    def get_ui_config(self, node_id: int) -> Dict[str, Any]:
        """現在の設定値を取得"""
        self._sync_ui_to_config(node_id)
        return self.current_nodes.get(node_id, {}).copy()
    
    def _sync_ui_to_config(self, node_id: int):
        """UIの全入力フィールドから最新値を強制取得してconfigに反映"""
        try:
            if node_id not in self.current_nodes:
                return
                
            for setting_key in ['temperature', 'top_p', 'top_k', 'max_new_tokens']:
                tag = f"{setting_key}_{node_id}"
                if dpg.does_item_exist(tag):
                    value = dpg.get_value(tag)
                    self.current_nodes[node_id][setting_key] = value
            
            self.logger.debug("UIから設定への同期完了")
            
        except Exception as e:
            self.logger.error(f"UI同期エラー: {e}")
    
    def reset_to_defaults(self, node_id: int):
        """設定をデフォルトに戻す"""
        try:
            default_config = VLMConfig.get_default_config()
            self.current_nodes[node_id] = default_config.copy()
            
            # UI要素も明示的にデフォルトに戻す
            for setting_key in ['temperature', 'top_p', 'top_k', 'max_new_tokens']:
                tag = f"{setting_key}_{node_id}"
                if dpg.does_item_exist(tag):
                    default_value = default_config.get(setting_key)
                    dpg.set_value(tag, default_value)
            
            print(f"VLM設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"VLMデフォルト復元エラー: {e}")
