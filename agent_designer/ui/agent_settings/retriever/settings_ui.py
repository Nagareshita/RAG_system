# agent_designer/ui/node_settings/retriever/settings_ui.py
import dearpygui.dearpygui as dpg
from .config import RetrieverConfig


class RetrieverSettingsUI:
    """Retriever設定UI管理クラス（設定駆動型）"""
    
    def __init__(self, parent_manager):
        self.manager = parent_manager
        self.config = RetrieverConfig()
    
    def create_settings(self, node):
        """Retriever詳細設定UIを動的生成"""
        config = node['config']
        node_id = node['id']
        
        # ヘッダー
        dpg.add_text("Retriever詳細設定", color=(200, 200, 255))
        dpg.add_separator()
        
        # 設定項目を動的生成
        schema = self.config.get_settings_schema()
        
        for i, (key, setting_info) in enumerate(schema.items()):
            self._create_setting_ui(key, setting_info, config, node_id, i)
            
        # 初期状態の依存関係設定
        self._setup_dependencies(node_id)
    
    def _create_setting_ui(self, key, setting_info, config, node_id, index):
        """個別設定項目のUI生成"""
        current_value = config.get(key, self.config.DEFAULT_VALUES.get(key))
        
        # 型変換: int/float型フィールドを正しい型に変換
        if setting_info['type'] == 'int' and current_value is not None:
            try:
                current_value = int(current_value)
            except (ValueError, TypeError):
                current_value = self.config.DEFAULT_VALUES.get(key, 0)
        elif setting_info['type'] == 'float' and current_value is not None:
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                current_value = self.config.DEFAULT_VALUES.get(key, 0.0)
        
        # セクション番号とラベル
        dpg.add_text(f"{index}. {setting_info['label']}:", color=(255, 255, 150))
        
        if setting_info['type'] == 'combo':
            self._create_combo_setting(key, setting_info, current_value, node_id)
        elif setting_info['type'] == 'int':
            self._create_int_setting(key, setting_info, current_value, node_id)
        elif setting_info['type'] == 'float':
            self._create_float_setting(key, setting_info, current_value, node_id)
        elif setting_info['type'] == 'checkbox':
            self._create_checkbox_setting(key, setting_info, current_value, node_id)
        
        # 説明文
        if 'description' in setting_info:
            dpg.add_text(f"※{setting_info['description']}", color=(120, 120, 120))
        
        dpg.add_separator()
    
    def _create_combo_setting(self, key, setting_info, current_value, node_id):
        """コンボボックス設定項目の生成"""
        options = setting_info['options']
        items = [item[1] for item in options]
        
        # 現在値に対応する表示名を検索
        default_display = items[0]  # fallback
        for option_value, option_display in options:
            if (isinstance(current_value, list) and option_value in current_value) or current_value == option_value:
                default_display = option_display
                break
        
        dpg.add_combo(
            label=setting_info['label'],
            items=items,
            default_value=default_display,
            tag=f"{key}_{node_id}",
            width=300
        )
    
    def _create_int_setting(self, key, setting_info, current_value, node_id):
        """整数入力設定項目の生成"""
        with dpg.group(horizontal=True):
            dpg.add_input_int(
                default_value=current_value,
                tag=f"{key}_{node_id}",
                width=100,
                min_value=setting_info.get('min_value', 0),
                max_value=setting_info.get('max_value', 1000)
            )
            range_text = f"({setting_info.get('min_value', 0)}-{setting_info.get('max_value', 1000)})"
            dpg.add_text(range_text, color=(150, 150, 150))
    
    def _create_float_setting(self, key, setting_info, current_value, node_id):
        """浮動小数点入力設定項目の生成"""
        with dpg.group(horizontal=True):
            dpg.add_input_float(
                default_value=current_value,
                tag=f"{key}_{node_id}",
                width=100,
                format=setting_info.get('format', '%.2f'),
                min_value=setting_info.get('min_value', 0.0),
                max_value=setting_info.get('max_value', 1.0)
            )
            range_text = f"({setting_info.get('min_value', 0.0)}-{setting_info.get('max_value', 1.0)})"
            dpg.add_text(range_text, color=(150, 150, 150))
    
    def _create_checkbox_setting(self, key, setting_info, current_value, node_id):
        """チェックボックス設定項目の生成"""
        callback = None
        if 'affects' in setting_info:
            callback = lambda: self._handle_dependency_change(key, node_id, setting_info['affects'])
        
        dpg.add_checkbox(
            label=setting_info['label'],
            default_value=current_value,
            tag=f"{key}_{node_id}",
            callback=callback
        )
    
    def _handle_dependency_change(self, parent_key, node_id, affected_keys):
        """依存関係のある設定項目の表示/非表示制御"""
        parent_value = dpg.get_value(f"{parent_key}_{node_id}")
        
        for affected_key in affected_keys:
            target_tag = f"{affected_key}_{node_id}"
            if dpg.does_item_exist(target_tag):
                if parent_value:
                    dpg.show_item(target_tag)
                else:
                    dpg.hide_item(target_tag)
    
    def _setup_dependencies(self, node_id):
        """依存関係の初期状態設定"""
        schema = self.config.get_settings_schema()
        
        for key, setting_info in schema.items():
            if 'depends_on' in setting_info:
                parent_key = setting_info['depends_on']
                if dpg.does_item_exist(f"{parent_key}_{node_id}"):
                    parent_value = dpg.get_value(f"{parent_key}_{node_id}")
                    target_tag = f"{key}_{node_id}"
                    if dpg.does_item_exist(target_tag):
                        if parent_value:
                            dpg.show_item(target_tag)
                        else:
                            dpg.hide_item(target_tag)
    
    def extract_values(self, node_id):
        """UIから設定値を抽出"""
        values = {}
        schema = self.config.get_settings_schema()
        
        for key, setting_info in schema.items():
            tag = f"{key}_{node_id}"
            if dpg.does_item_exist(tag):
                raw_value = dpg.get_value(tag)
                
                # コンボボックスの場合は内部値に変換
                if setting_info['type'] == 'combo':
                    for option_value, option_display in setting_info['options']:
                        if raw_value == option_display:
                            values[key] = option_value
                            break
                else:
                    values[key] = raw_value
        
        return values
    
    def validate_values(self, values):
        """設定値のバリデーション"""
        return self.config.validate_config(values)
    
    def reset_to_defaults(self, node_id):
        """Retriever設定をデフォルトに戻す"""
        try:
            schema = self.config.get_settings_schema()
            defaults = self.config.DEFAULT_VALUES
            
            for key, setting_info in schema.items():
                tag = f"{key}_{node_id}"
                if dpg.does_item_exist(tag):
                    default_value = defaults.get(key)
                    
                    if setting_info['type'] == 'combo':
                        # コンボボックスの場合は表示名に変換
                        for option_value, option_display in setting_info['options']:
                            if option_value == default_value:
                                dpg.set_value(tag, option_display)
                                break
                    elif setting_info['type'] == 'int':
                        # int型は明示的に変換
                        dpg.set_value(tag, int(default_value))
                    elif setting_info['type'] == 'float':
                        # float型は明示的に変換
                        dpg.set_value(tag, float(default_value))
                    else:
                        dpg.set_value(tag, default_value)
            
            print(f"Retriever設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"Retrieverデフォルト復元エラー: {e}")
            import traceback
            traceback.print_exc()