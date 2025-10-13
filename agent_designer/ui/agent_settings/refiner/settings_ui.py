# agent_designer/ui/agent_settings/refiner/settings_ui_new.py
"""
Refiner設定UI（Analyzerパターン統合版 + 動的Section管理）
- Analyzerパターンベースの設定UI
- Section専用の動的管理UI（追加・削除・挿入）
- ネスト構造対応の柔軟な設計
- 統一されたデザインと操作性
"""

import dearpygui.dearpygui as dpg
from typing import Dict, Any, Callable, List, Optional
import logging

from .config import RefinerConfig, RefinerSection


class RefinerSettingsUI:
    """Refiner設定UI管理クラス（Analyzerパターン準拠 + Section管理）"""
    
    def __init__(self, 
                 parent_id: str,
                 config_values: Dict[str, Any],
                 on_change_callback: Callable[[str, Any], None] = None,
                 on_save_callback: Callable[[], None] = None):
        
        self.parent_id = parent_id
        self.config_values = config_values.copy()
        self.on_change_callback = on_change_callback
        self.on_save_callback = on_save_callback
        
        # UI要素のタグ管理
        self.main_group_id = f"{parent_id}_refiner_main"
        self.basic_settings_id = f"{parent_id}_basic_settings"
        self.format_settings_id = f"{parent_id}_format_settings"
        self.sections_group_id = f"{parent_id}_sections_group"
        self.sections_container_id = f"{parent_id}_sections_container"
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # デバッグ: config_valuesの内容を確認
        print(f"[DEBUG] RefinerUI初期化開始")
        print(f"[DEBUG] config_values keys: {list(self.config_values.keys())}")
        print(f"[DEBUG] 'sections' in config_values: {'sections' in self.config_values}")
        if 'sections' in self.config_values:
            print(f"[DEBUG] config_values['sections']: {self.config_values['sections']}")
        
        # Sectionsデータの初期化ロジック
        # 判定基準:
        # 1. sectionsキーが存在しない → 新規作成 → デフォルト3個
        # 2. sectionsキーが存在し、空リストでない → 既存データ読み込み
        # 3. sectionsキーが存在し、空リスト → ユーザーが意図的に削除 → 空のまま保持
        
        if 'sections' not in self.config_values:
            # 新規作成: デフォルトの3セクションを適用
            self.sections: List[RefinerSection] = RefinerConfig.get_default_sections()
            self.config_values['sections'] = [section.to_dict() for section in self.sections]
            print(f"[DEBUG] RefinerUI: 新規作成 - デフォルトsections適用 {len(self.sections)}個")
        
        elif isinstance(self.config_values['sections'], list) and len(self.config_values['sections']) > 0:
            # 既存データが存在: そのまま読み込み
            self.sections: List[RefinerSection] = RefinerConfig.sections_from_config(self.config_values)
            print(f"[DEBUG] RefinerUI: 既存sections読み込み {len(self.sections)}個")
        
        else:
            # 空リスト: ユーザーが意図的に削除したので空のまま保持
            self.sections: List[RefinerSection] = []
            print(f"[DEBUG] RefinerUI: 空リスト保持（ユーザーが削除済み） {len(self.sections)}個")
        
        print(f"[DEBUG] 最終的なself.sections数: {len(self.sections)}")
        
        # UIビルド
        self._build_ui()
    
    def _build_ui(self):
        """UI全体を構築"""
        try:
            # メインコンテナ
            with dpg.group(tag=self.main_group_id, parent=self.parent_id):
                
                # ヘッダー
                self._create_header()
                
                # 基本設定セクション
                self._create_basic_settings()
                
                # フォーマット設定セクション
                self._create_format_settings()
                
                # LLMプロンプト設定セクション
                self._create_llm_prompts_section()
                
                # セクション管理セクション
                self._create_sections_management()
                
                # 保存・検証ボタン
                self._create_action_buttons()
                
            self.logger.info("Refiner設定UI構築完了")
            
        except Exception as e:
            self.logger.error(f"UI構築エラー: {e}")
            raise
    
    def _create_header(self):
        """ヘッダー部分を作成"""
        ui_info = RefinerConfig.get_ui_info()
        
        with dpg.group(horizontal=True):
            # エージェント名とアイコン
            dpg.add_text(f"🔧 {ui_info['name']}", color=ui_info['color']['text'])
            dpg.add_text(f"- {ui_info['description']}", color=(200, 200, 200))
        
        dpg.add_separator()
    
    def _create_basic_settings(self):
        """基本設定セクションを作成"""
        with dpg.collapsing_header(label="基本設定", default_open=True):
            with dpg.group(tag=self.basic_settings_id):
                
                # 回答長設定
                with dpg.group(horizontal=True):
                    dpg.add_text("回答長設定:", color=(220, 220, 220))
                
                # 最小回答長（別行）
                with dpg.group(horizontal=True):
                    self._create_setting_widget('min_answer_length')
                    dpg.add_text("文字（最小）")
                
                # 最大回答長（別行）
                with dpg.group(horizontal=True):
                    self._create_setting_widget('max_answer_length')
                    dpg.add_text("文字（最大）")
                
                # その他基本設定
                self._create_setting_widget('enable_regeneration')
                self._create_setting_widget('logging_level')
    
    def _create_format_settings(self):
        """フォーマット設定セクションを作成"""
        with dpg.collapsing_header(label="フォーマット設定", default_open=True):
            with dpg.group():
                
                # フォーマット形式
                self._create_setting_widget('response_format')
                
                # フォーマットオプション
                with dpg.group():
                    dpg.add_text("フォーマットオプション:", color=(220, 220, 220))
                    self._create_setting_widget('use_code_blocks')
                    self._create_setting_widget('include_citations')
                    self._create_setting_widget('structure_with_headers')
                    self._create_setting_widget('expert_attribution')
                
                # 専門用語処理
                self._create_setting_widget('technical_terminology')
    
    def _create_llm_prompts_section(self):
        """LLMプロンプト設定セクションを作成"""
        with dpg.collapsing_header(label="LLMプロンプト設定", default_open=False):
            with dpg.group():
                
                llm_prompts = self.config_values.get('llm_prompts', RefinerConfig.DEFAULT_VALUES['llm_prompts'])
                
                # 新形式の5つのプロンプトキーのみを表示（順序固定）
                prompt_keys_order = [
                    'generation_instruction',
                    'section_instruction',
                    'output_format',
                    'integration_focus',
                    'code_generation_focus'
                ]
                
                # プロンプト名の日本語化
                prompt_labels = {
                    'generation_instruction': '生成指示プロンプト',
                    'section_instruction': 'セクション指示プロンプト',
                    'output_format': '出力形式プロンプト',
                    'integration_focus': '統合フォーカスプロンプト',
                    'code_generation_focus': 'コード生成フォーカスプロンプト'
                }
                
                for prompt_key in prompt_keys_order:
                    prompt_text = llm_prompts.get(prompt_key, '')
                    label = prompt_labels.get(prompt_key, prompt_key)
                    
                    dpg.add_text(f"{label}:")
                    
                    input_tag = f"{self.parent_id}_llm_prompt_{prompt_key}"
                    dpg.add_input_text(
                        tag=input_tag,
                        default_value=prompt_text,
                        multiline=True,
                        height=80,
                        width=-1,
                        callback=lambda sender, value, user_data=prompt_key: self._on_llm_prompt_change(user_data, value)
                    )
                    
                    dpg.add_spacing()
    
    def _create_sections_management(self):
        """セクション管理UIを作成（動的な追加・削除・挿入対応）"""
        with dpg.collapsing_header(label="📚 セクション管理", default_open=True, tag=self.sections_group_id):
            
            # セクション管理ヘッダー
            with dpg.group(horizontal=True):
                dpg.add_text("文書セクション構成:", color=(220, 220, 220))
                dpg.add_button(
                    label="+ 新規セクション",
                    callback=self._add_section_callback,
                    small=True,
                    tag=f"{self.sections_group_id}_add_btn"
                )
            
            dpg.add_separator()
            
            # セクションコンテナ
            with dpg.group(tag=self.sections_container_id):
                pass
            
            # セクション表示を更新
            self._refresh_sections_display()
    
    def _refresh_sections_display(self):
        """セクション表示を更新"""
        try:
            # 既存のセクション表示をクリア
            if dpg.does_item_exist(self.sections_container_id):
                dpg.delete_item(self.sections_container_id, children_only=True)
            
            # セクションが0個の場合は情報メッセージを表示
            if len(self.sections) == 0:
                with dpg.group(parent=self.sections_container_id):
                    dpg.add_text("ℹ️ セクションが設定されていません", color=(200, 200, 100))
                    dpg.add_text("  ※ セクション指定なしでも動作します（シンプルな回答生成）", color=(150, 150, 150))
                    dpg.add_spacer(height=10)
            else:
                # 各セクションのUIを作成
                for i, section in enumerate(self.sections):
                    self._create_section_ui(i, section)
                
            self.logger.debug(f"セクション表示更新完了: {len(self.sections)}個")
            
        except Exception as e:
            self.logger.error(f"セクション表示更新エラー: {e}")
    
    def _create_section_ui(self, index: int, section: RefinerSection):
        """個別セクションのUIを作成"""
        section_tag = f"{self.sections_container_id}_section_{index}"
        
        with dpg.group(tag=section_tag, parent=self.sections_container_id):
            
            # セクションヘッダー
            with dpg.group(horizontal=True):
                dpg.add_text(f"#{index + 1}", color=(100, 200, 100))
                
                # セクションタイトル入力
                title_tag = f"{section_tag}_title"
                dpg.add_input_text(
                    tag=title_tag,
                    default_value=section.title,
                    width=200,
                    hint="セクションタイトル",
                    callback=lambda sender, value, user_data=index: self._on_section_title_change(user_data, value)
                )
                
                # セクション操作ボタン
                dpg.add_button(
                    label="↑挿入",
                    callback=lambda: self._insert_section_callback(index),
                    small=True,
                    tag=f"{section_tag}_insert_btn"
                )
                
                dpg.add_button(
                    label="削除",
                    callback=lambda: self._remove_section_callback(index),
                    small=True,
                    tag=f"{section_tag}_remove_btn"
                )
            
            # セクション詳細設定
            with dpg.group(indent=20):
                
                # コンテンツタイプと長さ比率
                with dpg.group(horizontal=True):
                    # コンテンツタイプ
                    content_type_tag = f"{section_tag}_content_type"
                    dpg.add_combo(
                        items=["summary", "analysis", "conclusion", "implementation", "custom"],
                        default_value=section.content_type,
                        width=120,
                        tag=content_type_tag,
                        callback=lambda sender, value, user_data=index: self._on_section_content_type_change(user_data, value)
                    )
                    
                    dpg.add_text("長さ比率:")
                    
                    # 長さ比率
                    ratio_tag = f"{section_tag}_ratio"
                    dpg.add_input_int(
                        tag=ratio_tag,
                        default_value=section.target_length_ratio,
                        width=80,
                        min_value=1,
                        max_value=100,
                        callback=lambda sender, value, user_data=index: self._on_section_ratio_change(user_data, value)
                    )
                    
                    dpg.add_text("%")
                
                # 含有内容とトーン
                with dpg.group(horizontal=True):
                    dpg.add_text("含有内容:")
                    
                    includes_tag = f"{section_tag}_includes"
                    dpg.add_input_text(
                        tag=includes_tag,
                        default_value=", ".join(section.includes),
                        width=200,
                        hint="key_points, details, examples",
                        callback=lambda sender, value, user_data=index: self._on_section_includes_change(user_data, value)
                    )
                    
                    dpg.add_text("文体:")
                    
                    tone_tag = f"{section_tag}_tone"
                    dpg.add_combo(
                        items=["professional_concise", "technical_detailed", "professional_conclusive", "explanatory", "casual"],
                        default_value=section.tone,
                        width=150,
                        tag=tone_tag,
                        callback=lambda sender, value, user_data=index: self._on_section_tone_change(user_data, value)
                    )
                
                # データフォーカス
                with dpg.group(horizontal=True):
                    dpg.add_text("データ重点:")
                    
                    focus_tag = f"{section_tag}_focus"
                    dpg.add_combo(
                        items=["unified_analysis", "problem_definition", "technical_solution", "actionable_results", "comprehensive_overview"],
                        default_value=section.data_focus,
                        width=200,
                        tag=focus_tag,
                        callback=lambda sender, value, user_data=index: self._on_section_focus_change(user_data, value)
                    )
            
            dpg.add_separator()
    
    # ===== Section管理コールバック =====
    
    def _add_section_callback(self):
        """新規セクション追加"""
        try:
            new_section = RefinerSection(
                id=f"section_{len(self.sections) + 1}",
                title=f"新規セクション {len(self.sections) + 1}",
                content_type="summary",
                target_length_ratio=10,
                includes=["key_points"],
                tone="professional_concise",
                data_focus="unified_analysis"
            )
            
            self.sections.append(new_section)
            self._update_config_sections()
            self._refresh_sections_display()
            
            self.logger.info(f"新規セクション追加: {new_section.title}")
            
        except Exception as e:
            self.logger.error(f"セクション追加エラー: {e}")
    
    def _remove_section_callback(self, index: int):
        """セクション削除"""
        try:
            if 0 <= index < len(self.sections):
                removed_section = self.sections.pop(index)
                self._update_config_sections()
                self._refresh_sections_display()
                
                self.logger.info(f"セクション削除: {removed_section.title}")
                
        except Exception as e:
            self.logger.error(f"セクション削除エラー: {e}")
    
    def _insert_section_callback(self, index: int):
        """指定位置にセクション挿入"""
        try:
            new_section = RefinerSection(
                id=f"section_{len(self.sections) + 1}_insert",
                title=f"挿入セクション",
                content_type="summary",
                target_length_ratio=10,
                includes=["key_points"],
                tone="professional_concise",
                data_focus="unified_analysis"
            )
            
            self.sections.insert(index, new_section)
            self._update_config_sections()
            self._refresh_sections_display()
            
            self.logger.info(f"セクション挿入: 位置{index}, {new_section.title}")
            
        except Exception as e:
            self.logger.error(f"セクション挿入エラー: {e}")
    
    # ===== Section項目変更コールバック =====
    
    def _on_section_title_change(self, index: int, value: str):
        """セクションタイトル変更"""
        if 0 <= index < len(self.sections):
            self.sections[index].title = value
            self.sections[index].id = value.lower().replace(' ', '_').replace('　', '_')
            self._update_config_sections()
    
    def _on_section_content_type_change(self, index: int, value: str):
        """セクションコンテンツタイプ変更"""
        if 0 <= index < len(self.sections):
            self.sections[index].content_type = value
            self._update_config_sections()
    
    def _on_section_ratio_change(self, index: int, value: int):
        """セクション長さ比率変更"""
        if 0 <= index < len(self.sections):
            self.sections[index].target_length_ratio = value
            self._update_config_sections()
    
    def _on_section_includes_change(self, index: int, value: str):
        """セクション含有内容変更"""
        if 0 <= index < len(self.sections):
            includes = [item.strip() for item in value.split(',') if item.strip()]
            self.sections[index].includes = includes
            self._update_config_sections()
    
    def _on_section_tone_change(self, index: int, value: str):
        """セクション文体変更"""
        if 0 <= index < len(self.sections):
            self.sections[index].tone = value
            self._update_config_sections()
    
    def _on_section_focus_change(self, index: int, value: str):
        """セクションデータフォーカス変更"""
        if 0 <= index < len(self.sections):
            self.sections[index].data_focus = value
            self._update_config_sections()
    
    def _update_config_sections(self):
        """設定のSectionsを更新してコールバック通知"""
        try:
            sections_config = RefinerConfig.sections_to_config(self.sections)
            self.config_values['sections'] = sections_config
            
            if self.on_change_callback:
                self.on_change_callback('sections', sections_config)
                
        except Exception as e:
            self.logger.error(f"設定sections更新エラー: {e}")
    
    # ===== 通常設定項目のウィジェット作成 =====
    
    def _create_setting_widget(self, setting_key: str):
        """設定項目に対応するウィジェットを作成"""
        schema = RefinerConfig.get_settings_schema()
        
        if setting_key not in schema:
            self.logger.warning(f"未知の設定項目: {setting_key}")
            return
        
        setting_schema = schema[setting_key]
        setting_type = setting_schema['type']
        current_value = self.config_values.get(setting_key, RefinerConfig.DEFAULT_VALUES.get(setting_key))
        
        # 型変換: int/float型フィールドを正しい型に変換
        if setting_type == 'int' and current_value is not None:
            try:
                current_value = int(current_value)
            except (ValueError, TypeError):
                current_value = RefinerConfig.DEFAULT_VALUES.get(setting_key, 0)
        elif setting_type == 'float' and current_value is not None:
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                current_value = RefinerConfig.DEFAULT_VALUES.get(setting_key, 0.0)
        
        widget_tag = f"{self.parent_id}_{setting_key}"
        
        if setting_type == 'int':
            dpg.add_input_int(
                tag=widget_tag,
                label=setting_schema['label'],
                default_value=current_value or 0,
                min_value=setting_schema.get('min_value', 0),
                max_value=setting_schema.get('max_value', 100000),
                width=setting_schema.get('width', 150),
                callback=lambda sender, value, user_data=setting_key: self._on_setting_change(user_data, value)
            )
            
        elif setting_type == 'checkbox':
            dpg.add_checkbox(
                tag=widget_tag,
                label=setting_schema['label'],
                default_value=current_value or False,
                callback=lambda sender, value, user_data=setting_key: self._on_setting_change(user_data, value)
            )
            
        elif setting_type == 'combo':
            items = [option[0] for option in setting_schema['options']]
            dpg.add_combo(
                tag=widget_tag,
                label=setting_schema['label'],
                items=items,
                default_value=current_value or items[0],
                width=setting_schema.get('width', 200),
                callback=lambda sender, value, user_data=setting_key: self._on_setting_change(user_data, value)
            )
        
        # ヘルプテキスト追加
        if 'description' in setting_schema:
            dpg.add_text(f"  💡 {setting_schema['description']}", color=(150, 150, 150), wrap=400)
    
    def _on_setting_change(self, setting_key: str, value: Any):
        """設定値変更時のコールバック"""
        self.config_values[setting_key] = value
        
        if self.on_change_callback:
            self.on_change_callback(setting_key, value)
    
    def _on_llm_prompt_change(self, prompt_key: str, value: str):
        """LLMプロンプト変更時のコールバック"""
        if 'llm_prompts' not in self.config_values:
            self.config_values['llm_prompts'] = {}
        
        self.config_values['llm_prompts'][prompt_key] = value
        
        if self.on_change_callback:
            self.on_change_callback('llm_prompts', self.config_values['llm_prompts'])
    
    def _create_action_buttons(self):
        """アクションボタンを作成"""
        dpg.add_separator()
        # セクション総計表示のみを残す（保存・検証は親ダイアログで行う）
        with dpg.group(horizontal=True):
            total_ratio = sum(section.target_length_ratio for section in self.sections)
            dpg.add_text(f"セクション総長さ比率: {total_ratio}%", color=(200, 200, 200))
    
    def _validate_settings(self):
        """設定の検証を実行"""
        try:
            validation_result = RefinerConfig.validate_config(self.config_values)
            
            # 検証結果表示（簡易版）
            if validation_result['is_valid']:
                self.logger.info("設定検証: 正常")
                print("✅ 設定検証: 問題なし")
            else:
                self.logger.warning(f"設定検証エラー: {validation_result['errors']}")
                print(f"❌ 設定検証エラー: {validation_result['errors']}")
            
            if validation_result['warnings']:
                self.logger.info(f"設定検証警告: {validation_result['warnings']}")
                print(f"⚠️ 設定検証警告: {validation_result['warnings']}")
                
        except Exception as e:
            self.logger.error(f"設定検証失敗: {e}")
    
    def get_config_values(self) -> Dict[str, Any]:
        """現在の設定値を取得"""
        # 保存前に UI から最新値を強制同期
        self._sync_ui_to_config()
        return self.config_values.copy()
    
    def get_refiner_config_for_node(self, node_id: str) -> Dict[str, Any]:
        """ノード保存用の設定値を取得(node_settings.py互換)"""
        return self.get_config_values()
    
    def _sync_ui_to_config(self):
        """UI の全入力フィールドから最新値を強制取得して config に反映"""
        try:
            # 基本設定の同期
            for setting_key in ['min_answer_length', 'max_answer_length', 'enable_regeneration', 
                              'logging_level', 'response_format', 'use_code_blocks', 
                              'include_citations', 'structure_with_headers', 'expert_attribution', 
                              'technical_terminology']:
                tag = f"{self.parent_id}_{setting_key}"
                if dpg.does_item_exist(tag):
                    value = dpg.get_value(tag)
                    self.config_values[setting_key] = value
            
            # LLMプロンプトの同期（新形式：5つのプロンプト）
            llm_prompts = {}
            for prompt_key in ['generation_instruction', 'section_instruction', 'output_format', 
                             'integration_focus', 'code_generation_focus']:
                tag = f"{self.parent_id}_llm_prompt_{prompt_key}"
                if dpg.does_item_exist(tag):
                    value = dpg.get_value(tag)
                    llm_prompts[prompt_key] = value
                    print(f"[DEBUG] Refiner llm_prompt同期: {prompt_key} = {len(value)}文字")
            
            self.config_values['llm_prompts'] = llm_prompts
            print(f"[DEBUG] Refiner llm_prompts最終: {list(llm_prompts.keys())}")
            
            # セクション設定の同期（最重要）
            for index, section in enumerate(self.sections):
                section_tag = f"{self.sections_container_id}_section_{index}"
                
                # タイトル
                title_tag = f"{section_tag}_title"
                if dpg.does_item_exist(title_tag):
                    title = dpg.get_value(title_tag)
                    section.title = title
                    section.id = title.lower().replace(' ', '_').replace('　', '_')
                
                # コンテンツタイプ
                content_type_tag = f"{section_tag}_content_type"
                if dpg.does_item_exist(content_type_tag):
                    section.content_type = dpg.get_value(content_type_tag)
                
                # 長さ比率
                ratio_tag = f"{section_tag}_ratio"
                if dpg.does_item_exist(ratio_tag):
                    section.target_length_ratio = dpg.get_value(ratio_tag)
                
                # 含有内容
                includes_tag = f"{section_tag}_includes"
                if dpg.does_item_exist(includes_tag):
                    includes_str = dpg.get_value(includes_tag)
                    section.includes = [item.strip() for item in includes_str.split(',') if item.strip()]
                
                # 文体
                tone_tag = f"{section_tag}_tone"
                if dpg.does_item_exist(tone_tag):
                    section.tone = dpg.get_value(tone_tag)
                
                # データフォーカス
                focus_tag = f"{section_tag}_focus"
                if dpg.does_item_exist(focus_tag):
                    section.data_focus = dpg.get_value(focus_tag)
            
            # セクション設定を config に反映（空のリストも許可）
            sections_config = RefinerConfig.sections_to_config(self.sections)
            self.config_values['sections'] = sections_config
            
            print(f"[DEBUG] Refiner sections同期: {len(self.sections)}個のセクション")
            if len(self.sections) == 0:
                print("[DEBUG] セクション0個 - 空のリストとして保存します")
            
            self.logger.info("UI から設定への同期完了")
            
        except Exception as e:
            self.logger.error(f"UI 同期エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def reset_to_defaults(self, node_id: str):
        """設定をデフォルトに戻す（node_settings.py互換）"""
        try:
            default_config = RefinerConfig.get_default_config()
            self.update_config_values(default_config)
            
            # UI要素も明示的にデフォルトに戻す
            for setting_key in ['min_answer_length', 'max_answer_length', 'enable_regeneration', 
                              'logging_level', 'response_format', 'use_code_blocks', 
                              'include_citations', 'structure_with_headers', 'expert_attribution', 
                              'technical_terminology']:
                tag = f"{self.parent_id}_{setting_key}"
                if dpg.does_item_exist(tag):
                    default_value = default_config.get(setting_key)
                    dpg.set_value(tag, default_value)
                    print(f"[DEBUG] Refiner {setting_key}をデフォルト値に設定: {default_value}")
            
            # LLMプロンプトもデフォルトに戻す
            default_prompts = default_config.get('llm_prompts', {})
            for prompt_key in ['document_generation', 'content_refinement', 'quality_assurance', 
                             'formatting_rules', 'generation_instruction', 'section_instruction',
                             'output_format', 'integration_focus', 'code_generation_focus']:
                tag = f"{self.parent_id}_llm_prompt_{prompt_key}"
                if dpg.does_item_exist(tag) and prompt_key in default_prompts:
                    dpg.set_value(tag, default_prompts[prompt_key])
            
            print(f"Refiner設定をデフォルトに戻しました: node_{node_id}")
            
        except Exception as e:
            print(f"Refinerデフォルト復元エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def update_config_values(self, new_values: Dict[str, Any]):
        """設定値を更新"""
        self.config_values.update(new_values)
        
        # Sectionsデータも更新
        if 'sections' in new_values:
            self.sections = RefinerConfig.sections_from_config(self.config_values)
            self._refresh_sections_display()
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if dpg.does_item_exist(self.main_group_id):
                dpg.delete_item(self.main_group_id)
            self.logger.info("Refiner設定UIクリーンアップ完了")
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")


# ===== 統合テスト用の簡易関数 =====

def create_refiner_settings_ui(parent_id: str, 
                               config_values: Optional[Dict[str, Any]] = None,
                               on_change_callback: Optional[Callable] = None,
                               on_save_callback: Optional[Callable] = None) -> RefinerSettingsUI:
    """Refiner設定UIの作成ヘルパー関数"""
    
    if config_values is None:
        config_values = RefinerConfig.get_default_config()
    
    return RefinerSettingsUI(
        parent_id=parent_id,
        config_values=config_values,
        on_change_callback=on_change_callback,
        on_save_callback=on_save_callback
    )