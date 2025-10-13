# agent_designer/ui/agent_settings/analyzer/settings_ui.py
"""
AnalyzerSettingsUI - DearPyGui版統合実装
AnalyzerConfigクラスとの完全統合による設定管理
"""

import dearpygui.dearpygui as dpg
from typing import Dict, Any, List
from .config import AnalyzerConfig


class AnalyzerSettingsUI:
    """DearPyGui版Analyzer設定UI管理（統合版）"""
    
    def __init__(self, parent_manager):
        self.parent_manager = parent_manager
        self.current_nodes = {}  # node_id -> config mapping
    
    def create_analyzer_settings_ui(self, node: Dict[str, Any], ui_config: Dict[str, Any]):
        """Analyzer設定UI作成（統合版）"""
        node_id = node['id']
        self.current_nodes[node_id] = ui_config
        
        # UI情報取得
        ui_info = AnalyzerConfig.get_ui_info()
        
        dpg.add_text(f"{ui_info['name']}詳細設定", color=(200, 200, 255))
        dpg.add_separator()
        
        # 設定項目を動的生成
        self._create_dynamic_settings_ui(node_id, ui_config)
        
        # バリデーション結果表示
        self._create_validation_display(node_id)
    
    def _create_dynamic_settings_ui(self, node_id: int, ui_config: Dict[str, Any]):
        """スキーマに基づく動的UI生成"""
        schema = AnalyzerConfig.get_settings_schema()
        
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
            
            dpg.add_spacing(count=2)
    
    def _get_section_for_field(self, field_name: str) -> str:
        """フィールドのセクションを取得"""
        if field_name == 'analysis_depth':
            return "1. 分析設定:"
        elif field_name in ['base_instruction', 'optimization_focus', 'output_format', 'quality_criteria', 'query_optimization_rules']:
            return "2. プロンプト設定:"
        elif field_name == 'final_prompt_template':
            return "3. 最終プロンプトテンプレート:"
        elif field_name == 'logging_level':
            return "4. ログ設定:"
        return ""
    
    def _create_field_widget(self, node_id: int, field_name: str, field_config: Dict[str, Any], ui_config: Dict[str, Any]):
        """フィールド用ウィジェット作成"""
        widget_type = field_config.get('type', 'entry')
        current_value = self._get_current_value(field_name, ui_config)
        
        # ラベル表示
        label_text = field_config.get('label', field_name)
        dpg.add_text(f"  {label_text}:")
        
        if widget_type == 'combo':
            # コンボボックス
            options = field_config.get('options', [])
            display_values = [option[1] for option in options]
            
            # 現在値に対応する表示値を見つける
            current_display = display_values[0] if display_values else ""
            for value, display in options:
                if value == current_value:
                    current_display = display
                    break
            
            dpg.add_combo(
                items=display_values,
                default_value=current_display,
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 200)
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
            
        elif widget_type in ['int', 'float']:
            # 数値入力
            if widget_type == 'int':
                dpg.add_input_int(
                    default_value=int(current_value) if current_value else 0,
                    tag=f"{field_name}_{node_id}",
                    width=field_config.get('width', 100),
                    min_value=field_config.get('min_value', 0),
                    max_value=field_config.get('max_value', 100)
                )
            else:  # float
                dpg.add_input_float(
                    default_value=float(current_value) if current_value else 0.0,
                    tag=f"{field_name}_{node_id}",
                    width=field_config.get('width', 100),
                    min_value=field_config.get('min_value', 0.0),
                    max_value=field_config.get('max_value', 1.0),
                    format=field_config.get('format', '%.2f')
                )
                
        elif widget_type == 'checkbox':
            # チェックボックス
            dpg.add_checkbox(
                label=label_text,
                default_value=bool(current_value),
                tag=f"{field_name}_{node_id}"
            )
            
        else:  # entry (default)
            # テキスト入力
            dpg.add_input_text(
                default_value=str(current_value),
                tag=f"{field_name}_{node_id}",
                width=field_config.get('width', 300)
            )
    
    def _get_current_value(self, field_name: str, ui_config: Dict[str, Any]) -> Any:
        """現在の設定値を取得"""
        # llm_promptsの場合は特別処理
        if field_name in ['base_instruction', 'optimization_focus', 'output_format', 
                         'quality_criteria', 'query_optimization_rules']:
            return ui_config.get('llm_prompts', {}).get(field_name, '')
        
        # その他の場合
        defaults = AnalyzerConfig.get_default_config()
        value = ui_config.get(field_name, defaults.get(field_name, ''))
        
        # 型変換: スキーマに基づいてint/float型フィールドを変換
        schema = AnalyzerConfig.get_settings_schema()
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
    
    def _create_validation_display(self, node_id: int):
        """バリデーション結果表示エリア"""
        dpg.add_text("", tag=f"analyzer_validation_{node_id}", color=(255, 100, 100))
    
    def get_analyzer_config_for_node(self, node_id: int) -> Dict[str, Any]:
        """指定ノードのAnalyzer設定を取得"""
        print(f"[DEBUG] get_analyzer_config_for_node開始: node_id={node_id}")
        
        # UIから現在の値を取得
        current_config = {}
        schema = AnalyzerConfig.get_settings_schema()
        
        for field_name, field_config in schema.items():
            tag = f"{field_name}_{node_id}"
            if dpg.does_item_exist(tag):
                widget_type = field_config.get('type', 'entry')
                value = dpg.get_value(tag)
                
                if widget_type == 'combo':
                    # 表示値から実際の値に変換
                    options = field_config.get('options', [])
                    for option_value, option_display in options:
                        if option_display == value:
                            value = option_value
                            break
                
                current_config[field_name] = value
                print(f"[DEBUG] {field_name}: {value}")
        
        # llm_promptsの統合
        llm_prompts = {}
        prompt_fields = ['base_instruction', 'optimization_focus', 'output_format', 
                        'quality_criteria', 'query_optimization_rules']
        
        for field in prompt_fields:
            if field in current_config:
                llm_prompts[field] = current_config.pop(field)
        
        if llm_prompts:
            current_config['llm_prompts'] = llm_prompts
        
        print(f"Analyzer設定取得: {len(current_config)}項目")
        return current_config
    
    def reset_to_defaults(self, node_id: int):
        """Analyzer設定をデフォルトに戻す"""
        try:
            # デフォルト設定を取得
            defaults = AnalyzerConfig.get_default_config()
            schema = AnalyzerConfig.get_settings_schema()
            
            print(f"[DEBUG] デフォルト設定を適用: node_{node_id}")
            
            for field_name, field_config in schema.items():
                tag = f"{field_name}_{node_id}"
                if dpg.does_item_exist(tag):
                    widget_type = field_config.get('type', 'entry')
                    
                    # デフォルト値の取得
                    if field_name in ['base_instruction', 'optimization_focus', 'output_format', 
                                     'quality_criteria', 'query_optimization_rules']:
                        default_value = defaults.get('llm_prompts', {}).get(field_name, '')
                    else:
                        default_value = defaults.get(field_name, '')
                    
                    # ウィジェットタイプに応じた設定
                    if widget_type == 'combo':
                        # 実際の値から表示値に変換
                        options = field_config.get('options', [])
                        for option_value, option_display in options:
                            if option_value == default_value:
                                dpg.set_value(tag, option_display)
                                break
                    else:
                        dpg.set_value(tag, default_value)
                    
                    print(f"[DEBUG] {field_name}設定: {default_value}")
            
            print(f"Analyzer設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"Analyzerデフォルト復元エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def validate_config(self, node_id: int) -> tuple[bool, List[str]]:
        """現在の設定をバリデーション"""
        try:
            current_config = self.get_analyzer_config_for_node(node_id)
            validation_result = AnalyzerConfig.validate_config(current_config)
            
            return validation_result['is_valid'], validation_result.get('errors', [])
            
        except Exception as e:
            print(f"バリデーションエラー: {e}")
            return False, [str(e)]


def create_analyzer_ui_instance() -> AnalyzerSettingsUI:
    """AnalyzerSettingsUIインスタンス作成"""
    return AnalyzerSettingsUI
    
    def _create_dynamic_widgets(self, parent):
        """スキーマに基づく動的ウィジェット生成"""
        schema = AnalyzerConfig.get_settings_schema()
        row = 0
        
        for field_name, field_config in schema.items():
            # ラベル作成
            label_text = field_config.get('label', field_name)
            ttk.Label(parent, text=f"{label_text}:").grid(
                row=row, column=0, sticky="nw", padx=(0, 10), pady=(5, 0)
            )
            
            # ウィジェット作成
            widget = self._create_widget(parent, field_name, field_config)
            widget.grid(row=row, column=1, sticky="ew", pady=(5, 0))
            
            # 説明テキスト
            if 'description' in field_config:
                desc_label = ttk.Label(
                    parent, 
                    text=field_config['description'], 
                    font=("Arial", 8),
                    foreground="gray"
                )
                desc_label.grid(row=row+1, column=1, sticky="ew", pady=(0, 5))
                row += 2
            else:
                row += 1
        
        # カラム幅調整
        parent.columnconfigure(1, weight=1)
    
    def _create_widget(self, parent, field_name, field_config):
        """フィールド設定に基づくウィジェット作成"""
        widget_type = field_config.get('type', 'entry')
        current_value = self._get_field_value(field_name)
        
        if widget_type == 'combo':
            widget = ttk.Combobox(parent, state="readonly")
            options = field_config.get('options', [])
            widget['values'] = [option[1] for option in options]
            
            # 現在値に対応する表示テキストを設定
            for value, display in options:
                if value == current_value:
                    widget.set(display)
                    break
            else:
                widget.set(options[0][1] if options else "")
            
            self.widgets[field_name] = widget
            
        elif widget_type == 'textarea':
            height = field_config.get('height', 80)
            widget_frame = ttk.Frame(parent)
            
            text_widget = scrolledtext.ScrolledText(
                widget_frame, 
                height=max(3, height // 20),
                wrap=tk.WORD,
                font=("Consolas", 9)
            )
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", str(current_value))
            
            # プレースホルダー情報があれば表示
            if 'placeholder_info' in field_config:
                info_label = ttk.Label(
                    widget_frame,
                    text=f"使用可能変数: {field_config['placeholder_info']}",
                    font=("Arial", 7),
                    foreground="blue"
                )
                info_label.pack(anchor="w", pady=(2, 0))
            
            self.widgets[field_name] = text_widget
            return widget_frame
            
        elif widget_type == 'entry':
            widget = ttk.Entry(parent)
            widget.insert(0, str(current_value))
            self.widgets[field_name] = widget
            
        else:
            # デフォルトはEntry
            widget = ttk.Entry(parent)
            widget.insert(0, str(current_value))
            self.widgets[field_name] = widget
        
        return widget
    
    def _get_field_value(self, field_name):
        """設定値から指定フィールドの値を取得"""
        # llm_prompts内の項目は直接参照
        if field_name in ['base_instruction', 'optimization_focus', 'output_format', 
                         'quality_criteria', 'query_optimization_rules']:
            return self.config.get('llm_prompts', {}).get(field_name, '')
        
        return self.config.get(field_name, '')
    
    def get_current_config(self):
        """現在のUI設定値を取得"""
        schema = AnalyzerConfig.get_settings_schema()
        config = {}
        
        for field_name, field_config in schema.items():
            widget = self.widgets.get(field_name)
            if not widget:
                continue
                
            widget_type = field_config.get('type', 'entry')
            
            if widget_type == 'combo':
                selected_display = widget.get()
                # 表示テキストから実際の値に変換
                for value, display in field_config.get('options', []):
                    if display == selected_display:
                        config[field_name] = value
                        break
                        
            elif widget_type == 'textarea':
                config[field_name] = widget.get("1.0", tk.END).strip()
                
            elif widget_type == 'entry':
                config[field_name] = widget.get().strip()
        
        return config
    
    def validate_current_config(self):
        """現在の設定をバリデーション"""
        current_config = self.get_current_config()
        validation_result = AnalyzerConfig.validate_config(current_config)
        
        # バリデーション結果を表示
        if validation_result['is_valid']:
            if validation_result['warnings']:
                warning_text = "警告: " + "; ".join(validation_result['warnings'])
                self.validation_label.config(text=warning_text, foreground="orange")
            else:
                self.validation_label.config(text="✓ 設定は有効です", foreground="green")
        else:
            error_text = "エラー: " + "; ".join(validation_result['errors'])
            self.validation_label.config(text=error_text, foreground="red")
        
        return validation_result
    
    def reset_to_defaults(self):
        """デフォルト値にリセット"""
        self.config = AnalyzerConfig.get_default_config()
        
        # ウィジェットの値を更新
        for field_name, widget in self.widgets.items():
            current_value = self._get_field_value(field_name)
            schema = AnalyzerConfig.get_settings_schema()
            field_config = schema.get(field_name, {})
            widget_type = field_config.get('type', 'entry')
            
            if widget_type == 'combo':
                options = field_config.get('options', [])
                for value, display in options:
                    if value == current_value:
                        widget.set(display)
                        break
                        
            elif widget_type == 'textarea':
                widget.delete("1.0", tk.END)
                widget.insert("1.0", str(current_value))
                
            elif widget_type == 'entry':
                widget.delete(0, tk.END)
                widget.insert(0, str(current_value))
        
        # バリデーション表示をクリア
        if self.validation_label:
            self.validation_label.config(text="")