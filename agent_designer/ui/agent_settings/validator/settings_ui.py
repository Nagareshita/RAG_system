# agent_designer/ui/agent_settings/validator/settings_ui.py
"""
Validator設定UI（DearPyGUI統合版）
- Analyzerパターンに準拠
- SETTINGS_SCHEMAに基づく動的UI生成
- 設定保存・復元機能
- ログレベル選択機能
"""

import dearpygui.dearpygui as dpg
from typing import Dict, Any, List
from .config import ValidatorConfig


class ValidatorSettingsUI:
    def __init__(self, node_settings_instance):
        self.node_settings = node_settings_instance
        self.current_nodes = {}  # node_id -> ui_config

    def create_validator_settings_ui(self, node: Dict[str, Any], ui_config: Dict[str, Any]):
        """Validator設定UI作成（統合版）"""
        node_id = node['id']
        self.current_nodes[node_id] = ui_config
        
        # UI情報取得
        ui_info = ValidatorConfig.get_ui_info()
        
        dpg.add_text(f"{ui_info['name']}詳細設定", color=(200, 200, 255))
        dpg.add_separator()
        
        # 設定項目を動的生成
        self._create_dynamic_settings_ui(node_id, ui_config)
        
        # 参照値表示
        self._create_reference_values_display()
    
    def _create_dynamic_settings_ui(self, node_id: int, ui_config: Dict[str, Any]):
        """スキーマに基づく動的UI生成"""
        schema = ValidatorConfig.get_settings_schema()
        
        current_section = None
        for field_name, field_config in schema.items():
            # セクションヘッダー
            section = self._get_section_for_field(field_name)
            if section != current_section:
                if current_section is not None:
                    dpg.add_separator()
                dpg.add_text(section, color=(255, 255, 150))
                current_section = section
            
            # ウィジェット作成
            self._create_field_widget(node_id, field_name, field_config, ui_config)
            
            # 説明テキスト
            if 'description' in field_config:
                dpg.add_text(f"  {field_config['description']}", color=(180, 180, 180))
            
            dpg.add_spacer(height=5)
    
    def _get_section_for_field(self, field_name: str) -> str:
        """フィールドのセクション分類"""
        if field_name in ['confidence_threshold', 'llm_max_tokens', 'minimum_source_count', 'logging_level']:
            return "1. 基本設定"
        elif field_name in ['validation_instruction', 'evaluation_criteria', 'confidence_calculation', 'output_format', 'final_prompt_template']:
            return "2. プロンプト設定"
        else:
            return "3. その他設定"
    
    def _create_field_widget(self, node_id: int, field_name: str, field_config: Dict[str, Any], ui_config: Dict[str, Any]):
        """フィールド用ウィジェット作成"""
        widget_type = field_config.get('type', 'entry')
        current_value = self._get_current_value(field_name, ui_config)
        
        # ラベル表示
        label_text = field_config.get('label', field_name)
        dpg.add_text(f"  {label_text}:")
        
        if widget_type == 'entry':
            # テキスト入力
            dpg.add_input_text(
                default_value=str(current_value),
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 300)
            )
            
        elif widget_type == 'textarea':
            # テキストエリア
            dpg.add_input_text(
                multiline=True,
                default_value=str(current_value),
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 460),
                height=field_config.get('height', 100)
            )
            
        elif widget_type == 'combo':
            # コンボボックス（ドロップダウン）
            options = field_config.get('options', [])
            option_items = [display_text for _, display_text in options]
            
            # 現在の値に対応するインデックスを取得
            current_index = 0
            for i, (value, _) in enumerate(options):
                if value == current_value:
                    current_index = i
                    break
            
            dpg.add_combo(
                items=option_items,
                default_value=option_items[current_index] if option_items else "",
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 200)
            )
            
        elif widget_type in ['int', 'float']:
            # 数値入力
            if widget_type == 'int':
                try:
                    default_val = int(current_value) if current_value else 0
                except (ValueError, TypeError):
                    default_val = 0
                dpg.add_input_int(
                    default_value=default_val,
                    tag=f"{field_name}_{node_id}",
                    width=field_config.get('width', 100)
                )
            else:  # float
                try:
                    default_val = float(current_value) if current_value else 0.0
                except (ValueError, TypeError):
                    default_val = 0.0
                dpg.add_input_float(
                    default_value=default_val,
                    tag=f"{field_name}_{node_id}",
                    width=field_config.get('width', 100),
                    format=field_config.get('format', '%.2f')
                )
    
    def _get_current_value(self, field_name: str, ui_config: Dict[str, Any]) -> Any:
        """現在の設定値を取得"""
        # llm_promptsの場合は特別処理（final_prompt_templateも含む）
        if field_name in ['validation_instruction', 'evaluation_criteria', 'confidence_calculation', 'output_format', 'final_prompt_template']:
            # まずui_configのllm_promptsから取得を試行
            llm_prompts_value = ui_config.get('llm_prompts', {}).get(field_name, '')
            if llm_prompts_value:
                return llm_prompts_value
            
            # なければui_configの直接の値を確認（final_prompt_templateの場合）
            if field_name == 'final_prompt_template':
                direct_value = ui_config.get(field_name, '')
                if direct_value:
                    return direct_value
            
            # デフォルト値から取得
            defaults = ValidatorConfig.get_default_config()
            if field_name == 'final_prompt_template':
                return defaults.get('final_prompt_template', '')
            else:
                return defaults.get('llm_prompts', {}).get(field_name, '')
        
        # その他の場合
        defaults = ValidatorConfig.get_default_config()
        value = ui_config.get(field_name, defaults.get(field_name, ''))
        
        # 型変換: スキーマに基づいてint/float型フィールドを変換
        schema = ValidatorConfig.get_settings_schema()
        if field_name in schema:
            field_type = schema[field_name].get('type')
            if field_type == 'int' and value is not None:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = defaults.get(field_name, 0)
            elif field_type == 'float' and value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = defaults.get(field_name, 0.0)
        
        return value
    
    def _create_reference_values_display(self):
        """参照値表示セクション"""
        dpg.add_separator()
        dpg.add_text("3. 重み設定（固定値）:", color=(255, 255, 150))
        
        ref_values = ValidatorConfig.get_reference_values()
        for key, value in ref_values.items():
            dpg.add_text(f"  {key}: {value}", color=(200, 200, 200))
    
    def get_validator_config_for_node(self, node_id: int) -> Dict[str, Any]:
        """指定ノードのValidator設定を取得"""
        print(f"[DEBUG] get_validator_config_for_node開始: node_id={node_id}")
        
        # UIから現在の値を取得
        current_config = {}
        schema = ValidatorConfig.get_settings_schema()
        
        for field_name, field_config in schema.items():
            tag = f"{field_name}_{node_id}"
            if dpg.does_item_exist(tag):
                value = dpg.get_value(tag)
                
                # comboboxの場合は表示テキストから実際の値に変換
                if field_config.get('type') == 'combo':
                    options = field_config.get('options', [])
                    for actual_value, display_text in options:
                        if display_text == value:
                            value = actual_value
                            break
                
                current_config[field_name] = value
                print(f"[DEBUG] {field_name}: {value}")
        
        # llm_promptsの統合
        llm_prompts = {}
        prompt_fields = ['validation_instruction', 'evaluation_criteria', 'confidence_calculation', 'output_format', 'final_prompt_template']
        
        for field in prompt_fields:
            if field in current_config:
                llm_prompts[field] = current_config.pop(field)
        
        if llm_prompts:
            current_config['llm_prompts'] = llm_prompts
        
        print(f"Validator設定取得: {len(current_config)}項目")
        return current_config
    
    def reset_to_defaults(self, node_id: int):
        """Validator設定をデフォルトに戻す"""
        try:
            # デフォルト設定を取得
            defaults = ValidatorConfig.get_default_config()
            schema = ValidatorConfig.get_settings_schema()
            
            print(f"[DEBUG] Validatorデフォルト設定を適用: node_{node_id}")
            
            for field_name, field_config in schema.items():
                tag = f"{field_name}_{node_id}"
                if dpg.does_item_exist(tag):
                    # デフォルト値の取得
                    if field_name in ['validation_instruction', 'evaluation_criteria', 'confidence_calculation', 'output_format']:
                        default_value = defaults.get('llm_prompts', {}).get(field_name, '')
                    elif field_name == 'final_prompt_template':
                        # final_prompt_templateは独立したフィールド
                        default_value = defaults.get('final_prompt_template', '')
                    else:
                        default_value = defaults.get(field_name, '')
                    
                    # comboboxの場合は値を表示テキストに変換
                    if field_config.get('type') == 'combo':
                        options = field_config.get('options', [])
                        for actual_value, display_text in options:
                            if actual_value == default_value:
                                default_value = display_text
                                break
                    
                    dpg.set_value(tag, default_value)
                    print(f"[DEBUG] {field_name}設定: {len(str(default_value))}文字")
            
            print(f"Validator設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"Validatorデフォルト復元エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def validate_config(self, node_id: int) -> tuple[bool, List[str]]:
        """現在の設定をバリデーション"""
        try:
            current_config = self.get_validator_config_for_node(node_id)
            validation_result = ValidatorConfig.validate_config(current_config)
            
            return validation_result['is_valid'], validation_result.get('errors', [])
            
        except Exception as e:
            print(f"バリデーションエラー: {e}")
            return False, [str(e)]