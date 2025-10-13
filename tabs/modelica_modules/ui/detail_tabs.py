# ast_only/src/ui/detail_tabs.py
"""
段階的詳細表示タブシステム   
raw → noise_removed の2段階表示（元の表示品質を維持）
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QPlainTextEdit, QLabel, QPushButton, QComboBox,
    QSplitter, QGroupBox, QScrollArea, QFrame
)
import json
import re  # 修正：import追加

# content_filterのインポート
try:
    from tabs.modelica_modules.modelica.content_filter import ContentFilter, FilterRuleManager
    from tabs.modelica_modules.modelica.jsonl_exporter import JSONLExporter
    FILTER_MODULES_LOADED = True
    print("✓ フィルタモジュール読み込み成功")
except ImportError as e:
    print(f"✗ フィルタモジュールの読み込みに失敗: {e}")
    ContentFilter = None
    FilterRuleManager = None
    JSONLExporter = None
    FILTER_MODULES_LOADED = False

def _json_diff(a, b, path=""):
    """簡易diff計算"""
    added, removed, changed = [], [], []

    if isinstance(a, dict) and isinstance(b, dict):
        a_keys, b_keys = set(a.keys()), set(b.keys())
        for k in sorted(b_keys - a_keys):
            added.append((path + "." + k if path else k))
        for k in sorted(a_keys - b_keys):
            removed.append((path + "." + k if path else k))
        for k in sorted(a_keys & b_keys):
            subpath = path + "." + k if path else k
            sub_a, sub_b = a[k], b[k]
            if isinstance(sub_a, (dict, list)) and isinstance(sub_b, (dict, list)):
                d = _json_diff(sub_a, sub_b, subpath)
                added += d["added"]; removed += d["removed"]; changed += d["changed"]
            else:
                if sub_a != sub_b:
                    changed.append(subpath)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            changed.append((path or "$") + f" (list length {len(a)}→{len(b)})")
        for i in range(min(5, len(a), len(b))):
            if a[i] != b[i]:
                changed.append((path or "$") + f"[{i}]")
    else:
        if a != b:
            changed.append(path or "$")

    def _cap(lst): 
        return lst[:20] + (["..."] if len(lst) > 20 else [])
    return {"added": _cap(added), "removed": _cap(removed), "changed": _cap(changed)}


class StagePreviewWidget(QWidget):
    """単一段階のプレビュー表示ウィジェット（修正版：エラー対応）"""
    
    def __init__(self, stage_name: str, stage_description: str, parent=None):
        super().__init__(parent)
        self.stage_name = stage_name
        self.stage_description = stage_description
        self.current_record = None
        self.content_filter = ContentFilter() if FILTER_MODULES_LOADED else None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # ヘッダ
        header_layout = QHBoxLayout()
        
        stage_icon = self._get_stage_icon()
        stage_label = QLabel(f"{self.stage_description}")
        stage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(stage_label)
        
        header_layout.addStretch()
        
        # デバッグボタン
        self.debug_btn = QPushButton("デバッグ")
        self.debug_btn.setMaximumWidth(80)
        self.debug_btn.clicked.connect(self._show_debug_info)
        header_layout.addWidget(self.debug_btn)
        
        # JSONL プレビューボタン
        if JSONLExporter:
            self.jsonl_btn = QPushButton("JSONL")
            self.jsonl_btn.setMaximumWidth(80)
            self.jsonl_btn.clicked.connect(self._show_jsonl_preview)
            header_layout.addWidget(self.jsonl_btn)
        
        layout.addLayout(header_layout)
        
        # メインコンテンツエリア
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameStyle(QFrame.Box)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        
        self.content_area.setWidget(self.content_widget)
        layout.addWidget(self.content_area)
        
        self._show_empty_message()
    
    def _get_stage_icon(self) -> str:
        """段階に応じたアイコンを取得"""
        icons = {
            "raw": "📊",
            "noise_removed": "🧹"
        }
        return icons.get(self.stage_name, "📋")
    
    def _show_empty_message(self):
        """空の状態メッセージを表示"""
        self._clear_content()
        
        empty_label = QLabel("項目を選択してください")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #888; font-size: 16px;")
        self.content_layout.addWidget(empty_label)
    
    def _clear_content(self):
        """コンテンツエリアをクリア"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_content(self, record: Dict[str, Any]):
        print(f"📄 {self.stage_name} - コンテンツ更新開始")
        self.current_record = record
        self._clear_content()

        if not record:
            self._show_empty_message()
            return
        
        # 除外フラグをチェック
        is_excluded = record.get("_ui_excluded", False)
        if is_excluded and self.stage_name != "raw":
            exclusion_reason = record.get("_ui_exclusion_reason", "品質基準により除外")
            self._show_exclusion_message(exclusion_reason)
            return

        if not FILTER_MODULES_LOADED or not self.content_filter:
            self._show_error_message("フィルタモジュールが読み込まれていません")
            return

        try:
            # rawは真の生データをそのままJSON表示
            if self.stage_name == "raw":
                self._add_section("📋 段階", "元データ（無加工）")
                raw_text = json.dumps(record, indent=2, ensure_ascii=False)
                editor = QPlainTextEdit(raw_text)
                editor.setReadOnly(True)
                editor.setMaximumHeight(400)
                font = QFont("Consolas", 9)
                editor.setFont(font)
                self.content_layout.addWidget(editor)
                print("🎨 raw - 生JSON表示完了")
                return

            # noise_removedは差分表示を削除し、フィルタ適用後の内容のみ表示
            print(f"🎯 {self.stage_name} - フィルタ適用中...")
            filtered_record = self.content_filter.filter_record(record, self.stage_name)
            print(f"✅ {self.stage_name} - フィルタ適用完了")

            # 段階情報と各セクション表示（差分セクションは削除）
            self._add_stage_info(filtered_record)
            self._add_basic_info(filtered_record)
            self._add_documentation(filtered_record)
            self._add_parameters(filtered_record)
            self._add_physical_info(filtered_record)
            self._add_components(filtered_record)
            self._add_equations(filtered_record)
            self._add_connections(filtered_record)
            self._add_dependencies(filtered_record)

            print(f"🎨 {self.stage_name} - 表示完了")

        except Exception as e:
            print(f"⚠ {self.stage_name} - 表示エラー: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_message(f"表示エラー: {str(e)}")
    
    def _show_error_message(self, message: str):
        """エラーメッセージを表示"""
        error_label = QLabel(message)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        error_label.setWordWrap(True)
        self.content_layout.addWidget(error_label)
    
    def _add_stage_info(self, record: Dict[str, Any]):
        """段階情報を表示"""
        stage_info = record.get("stage_info", f"{self.stage_name} 段階")
        
        info_widget = QLabel(f"{stage_info}")
        info_widget.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 8px;
            margin: 4px;
            font-weight: bold;
            color: black;
        """)
        self.content_layout.addWidget(info_widget)
    
    def _add_section(self, title: str, content: Any, empty_message: str = "なし") -> QGroupBox:
        """セクションを追加"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: black;
            }
        """)
        group_layout = QVBoxLayout(group)
        
        if not content or (isinstance(content, (list, dict)) and len(content) == 0):
            label = QLabel(empty_message)
            label.setStyleSheet("color: #666; font-style: italic;")
            group_layout.addWidget(label)
        else:
            if isinstance(content, str):
                text_widget = QLabel(content)
                text_widget.setWordWrap(True)
                text_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
                group_layout.addWidget(text_widget)
            elif isinstance(content, (list, dict)):
                json_text = json.dumps(content, indent=2, ensure_ascii=False)
                text_widget = QPlainTextEdit(json_text)
                text_widget.setMaximumHeight(150)
                text_widget.setReadOnly(True)
                font = QFont("Consolas", 9)
                text_widget.setFont(font)
                group_layout.addWidget(text_widget)
        
        self.content_layout.addWidget(group)
        return group
    
    def _add_basic_info(self, record: Dict[str, Any]):
        """基本情報セクション"""
        info_parts = []
        info_parts.append(f"種類: {record.get('kind', '?')}")
        info_parts.append(f"名前: {record.get('name', '?')}")
        
        if "id" in record:
            info_parts.append(f"ID: {record['id']}")
        elif "fqn" in record:
            info_parts.append(f"FQN: {record['fqn']}")
        
        if record.get("package_path"):
            if isinstance(record["package_path"], list):
                package_str = ".".join(str(p) for p in record["package_path"])
            else:
                package_str = str(record["package_path"])
            info_parts.append(f"パッケージ: {package_str}")
        
        if record.get("meta", {}).get("filter_applied"):
            stage = record["meta"].get("processing_stage", self.stage_name)
            info_parts.append(f"処理段階: {stage}")
        
        info_text = "\n".join(info_parts)
        self._add_section("基本情報", info_text)
    
    def _add_documentation(self, record: Dict[str, Any]):
        """ドキュメントセクション"""
        doc = record.get("documentation") or record.get("docstring", "")
        
        if doc and len(str(doc).strip()) > 0:
            doc_text = str(doc)
            self._add_section("ドキュメント", doc_text)
        else:
            self._add_section("ドキュメント", "", "ドキュメントなし")
    
    def _add_parameters(self, record: Dict[str, Any]):
        """パラメータセクション"""
        params = record.get("parameters", [])
        
        if params and len(params) > 0:
            param_lines = []
            for i, param in enumerate(params):
                if isinstance(param, dict):
                    line = f"{i+1}. {param.get('name', '?')}"
                    if param.get('type'):
                        line += f": {param['type']}"
                    if param.get('default'):
                        line += f" = {param['default']}"
                    if param.get('description'):
                        line += f" - {param['description']}"
                    param_lines.append(line)
                else:
                    param_lines.append(f"{i+1}. {str(param)}")
            
            param_text = "\n".join(param_lines)
            self._add_section(f"パラメータ ({len(params)})", param_text)
        else:
            self._add_section("パラメータ", "", "パラメータなし")
    
    def _add_physical_info(self, record: Dict[str, Any]):
        """物理情報セクション"""
        phys_info = record.get("physical_quantities", {})
        
        if phys_info and len(phys_info) > 0:
            content_parts = []
            
            if "quantities" in phys_info:
                quantities = phys_info["quantities"]
                if quantities:
                    content_parts.append("物理量:")
                    for q in quantities:
                        if isinstance(q, dict):
                            line = f"  - {q.get('name', '?')}"
                            if q.get('unit'):
                                line += f" [{q['unit']}]"
                            content_parts.append(line)
                        else:
                            content_parts.append(f"  - {str(q)}")
            
            if "units" in phys_info:
                units = phys_info["units"]
                if units:
                    content_parts.append(f"\n単位: {', '.join(str(u) for u in units)}")
            
            if "domains" in phys_info:
                domains = phys_info["domains"]
                if domains:
                    content_parts.append(f"\nドメイン: {', '.join(str(d) for d in domains)}")
            
            content_text = "\n".join(content_parts) if content_parts else ""
            self._add_section("物理情報", content_text, "物理情報なし")
        else:
            self._add_section("物理情報", "", "物理情報なし")
    
    def _add_components(self, record: Dict[str, Any]):
        """コンポーネントセクション"""
        components = record.get("components", [])
        
        if components and len(components) > 0:
            comp_lines = []
            for i, comp in enumerate(components):
                if isinstance(comp, dict):
                    line = f"{i+1}. {comp.get('name', '?')}: {comp.get('type_name', comp.get('type', '?'))}"
                    
                    if comp.get('prefixes'):
                        prefixes = comp['prefixes']
                        if isinstance(prefixes, list):
                            line += f" [{', '.join(str(p) for p in prefixes)}]"
                        else:
                            line += f" [{prefixes}]"
                    
                    if comp.get('modifications'):
                        mods = comp['modifications']
                        if isinstance(mods, dict):
                            if len(mods) <= 3:
                                mod_strs = [f"{k}={v}" for k, v in mods.items()]
                                line += f" ({', '.join(mod_strs)})"
                            else:
                                line += f" ({len(mods)} modifications)"
                        else:
                            line += f" (modifications: {mods})"
                    
                    comp_lines.append(line)
                else:
                    comp_lines.append(f"{i+1}. {str(comp)}")
            
            comp_text = "\n".join(comp_lines)
            self._add_section(f"コンポーネント ({len(components)})", comp_text)
        else:
            self._add_section("コンポーネント", "", "コンポーネントなし")
    
    def _add_equations(self, record: Dict[str, Any]):
        """方程式セクション（修正：for文グループ化表示）"""
        equations = record.get("equations", [])
        
        if equations and len(equations) > 0:
            eq_lines = []            
            # 新しい形式のみを処理（セクション別）
            for eq_block in equations:
                if isinstance(eq_block, dict) and "section_type" in eq_block:
                    section_type = eq_block["section_type"]
                    section_equations = eq_block.get("equations", [])
                    
                    # セクションヘッダーを追加
                    if section_type == "initial_equation":
                        eq_lines.append(f"=== 初期方程式セクション ===")
                    elif section_type == "equation":
                        eq_lines.append(f"=== 方程式セクション ===")
                    elif section_type == "algorithm":
                        eq_lines.append(f"=== アルゴリズムセクション ===")
                    elif section_type == "initial_algorithm":
                        eq_lines.append(f"=== 初期アルゴリズムセクション ===")
                    
                    # セクション内の方程式を追加
                    eq_count = 0
                    for eq in section_equations:
                        eq_str = str(eq).strip()
                        
                        # フィルタリング条件
                        if (len(eq_str) > 5 and 
                            not eq_str.startswith('//') and 
                            not eq_str.startswith('/*') and
                            not eq_str.startswith('end ') and
                            eq_str not in ['equation', 'initial equation', 'algorithm', 'initial algorithm']):
                            
                            # 修正：for文の場合は特別な表示処理
                            if 'for ' in eq_str and 'loop' in eq_str and 'end for' in eq_str:
                                # for文全体をグループとして表示
                                eq_count += 1
                                
                                # for文の構造を解析して見やすく表示
                                formatted_for = self._format_for_loop_display(eq_str)
                                eq_lines.append(f"📋 {formatted_for}")
                                
                            elif 'for ' in eq_str and 'loop' in eq_str:
                                # 複数行のfor文処理（従来通り）
                                inner_equations = self._extract_loop_equations(eq_str)
                                for inner_eq in inner_equations:
                                    if inner_eq.startswith('📋'):
                                        # for文ヘッダー
                                        eq_count += 1
                                        eq_lines.append(f"{eq_count}. {inner_eq}")
                                    elif inner_eq.startswith('  •'):
                                        # for文内の方程式
                                        eq_lines.append(f"    {inner_eq}")
                                    elif inner_eq == 'end for':
                                        # for文終了
                                        eq_lines.append(f"    end for")
                                    else:
                                        eq_count += 1
                                        eq_lines.append(f"{eq_count}. {inner_eq}")
                            else:
                                # 通常の方程式
                                eq_count += 1
                                eq_lines.append(f"{eq_count}. {eq_str}")
                    
                    if eq_count == 0:
                        eq_lines.append("(方程式なし)")
                    
                    eq_lines.append("")  # セクション間の空行
            
            # 結果表示
            if eq_lines:
                actual_equations = [l for l in eq_lines if l and not l.startswith('===') and not l == "(方程式なし)" and l.strip()]
                eq_text = "\n".join(eq_lines)
                self._add_section(f"方程式 ({len(actual_equations)})", eq_text)
            else:
                self._add_section("方程式", "", "方程式なし")
        else:
            self._add_section("方程式", "", "方程式なし")

    def _format_for_loop_display(self, loop_str: str) -> str:
        """for文を見やすい形式で表示（新規メソッド）"""
        import re
        
        # for文の基本パターンマッチ
        match = re.search(r'for\s+(\w+)\s+in\s+([^l]+)loop\s+(.*?)\s+end\s+for', loop_str, re.DOTALL)
        
        if match:
            loop_var = match.group(1)
            loop_range = match.group(2).strip()
            loop_body = match.group(3).strip()
            
            # ループ内の文を分析
            statements = []
            current = ""
            paren_depth = 0
            
            for char in loop_body:
                current += char
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ';' and paren_depth == 0:
                    stmt = current.rstrip(';').strip()
                    if stmt and len(stmt) > 5:
                        statements.append(stmt)
                    current = ""
            
            if current.strip():
                stmt = current.strip().rstrip(';')
                if stmt and len(stmt) > 5:
                    statements.append(stmt)
            
            # 見やすい形式で組み立て
            if len(statements) == 1:
                return f"for {loop_var} in {loop_range}⟶ {statements[0]}"
            else:
                result = f"for {loop_var} in {loop_range}loop\n"
                for stmt in statements:
                    result += f"      • {stmt}\n"
                result += "    end for"
                return result
        
        # パターンマッチできない場合は元の文字列
        return loop_str

    def _extract_loop_equations(self, loop_str: str) -> List[str]:
        """forループ内の個別方程式を抽出（修正：グループ化表示）"""
        equations = []
        
        # forループの構造を解析
        import re
        loop_match = re.search(r'for\s+(\w+)\s+in\s+([^l]+)loop\s+(.*?)(?:\s+end\s+for|$)', loop_str, re.DOTALL)
        
        if loop_match:
            loop_var = loop_match.group(1)
            loop_range = loop_match.group(2).strip()
            loop_body = loop_match.group(3).strip()
            
            # ループ情報をヘッダーとして追加
            loop_header = f"for {loop_var} in {loop_range}"
            equations.append(f"{loop_header}")
            
            # セミコロンで分割して個別の方程式を取得
            individual_eqs = []
            current_eq = ""
            paren_depth = 0
            
            for char in loop_body:
                current_eq += char
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ';' and paren_depth == 0:
                    eq_clean = current_eq.rstrip(';').strip()
                    if eq_clean and len(eq_clean) > 5:
                        individual_eqs.append(eq_clean)
                    current_eq = ""
            
            # 最後の方程式（セミコロンで終わらない場合）
            if current_eq.strip():
                eq_clean = current_eq.strip().rstrip(';')
                if eq_clean and len(eq_clean) > 5:
                    individual_eqs.append(eq_clean)
            
            # インデント付きで各方程式を追加
            for eq in individual_eqs:
                equations.append(f"  • {eq}")
            
            equations.append("end for")
        
        # 分離できない場合は元の文をそのまま返す
        if len(equations) <= 1:
            equations = [loop_str]
        
        return equations
    
    def _add_connections(self, record: Dict[str, Any]):
        """接続セクション"""
        connections = record.get("connections", [])
        
        if connections and len(connections) > 0:
            conn_lines = []
            for i, conn in enumerate(connections):
                if isinstance(conn, dict):
                    from_conn = conn.get("from") or conn.get("from_connector", "?")
                    to_conn = conn.get("to") or conn.get("to_connector", "?")
                else:
                    from_conn = to_conn = str(conn)
                
                conn_lines.append(f"{i+1}. {from_conn} → {to_conn}")
            
            conn_text = "\n".join(conn_lines)
            self._add_section(f"接続 ({len(connections)})", conn_text)
        else:
            self._add_section("接続", "", "接続なし")
    
    def _add_dependencies(self, record: Dict[str, Any]):
        """依存関係セクション"""
        deps = record.get("dependencies", {})
        
        if deps and isinstance(deps, dict) and any(deps.values()):
            dep_lines = []
            
            if deps.get("extends"):
                extends_list = deps["extends"]
                if isinstance(extends_list, list):
                    dep_lines.append(f"継承: {', '.join(str(e) for e in extends_list)}")
                else:
                    dep_lines.append(f"継承: {extends_list}")
            
            if deps.get("imports"):
                imports_list = deps["imports"]
                if isinstance(imports_list, list):
                    dep_lines.append(f"インポート: {', '.join(str(i) for i in imports_list)}")
                else:
                    dep_lines.append(f"インポート: {imports_list}")
            
            if deps.get("component_instances"):
                comp_instances = deps["component_instances"]
                if comp_instances and isinstance(comp_instances, list):
                    dep_lines.append("コンポーネントインスタンス:")
                    for inst in comp_instances:
                        if isinstance(inst, dict):
                            dep_lines.append(f"  - {inst.get('instance_name', '?')}: {inst.get('type', '?')}")
                        else:
                            dep_lines.append(f"  - {str(inst)}")
            
            if deps.get("referenced_types"):
                ref_types = deps["referenced_types"]
                if ref_types and isinstance(ref_types, list):
                    dep_lines.append(f"参照型: {', '.join(str(r) for r in ref_types)}")
                elif ref_types:
                    dep_lines.append(f"参照型: {ref_types}")
            
            dep_text = "\n".join(dep_lines) if dep_lines else ""
            self._add_section("依存関係", dep_text, "依存関係なし")
        else:
            # 元の形式もチェック
            extends = record.get("extends", [])
            imports = record.get("imports", [])
            
            if extends or imports:
                dep_lines = []
                if extends:
                    if isinstance(extends, list):
                        dep_lines.append(f"継承: {', '.join(str(e) for e in extends)}")
                    else:
                        dep_lines.append(f"継承: {extends}")
                if imports:
                    if isinstance(imports, list):
                        dep_lines.append(f"インポート: {', '.join(str(i) for i in imports)}")
                    else:
                        dep_lines.append(f"インポート: {imports}")
                
                dep_text = "\n".join(dep_lines)
                self._add_section("依存関係", dep_text)
            else:
                self._add_section("依存関係", "", "依存関係なし")
    
    def _show_debug_info(self):
        """デバッグ情報を表示"""
        if not self.current_record:
            return
        
        # 新しいデバッグメソッドを呼び出し
        if FILTER_MODULES_LOADED and self.content_filter:
            debug_info = self.content_filter.debug_equation_extraction(self.current_record)
        else:
            debug_info = {"error": "Filter not available"}
        
        dialog = DebugInfoDialog(debug_info, f"{self.stage_name}_debug", self)
        dialog.show()
    
    def _show_jsonl_preview(self):
        """JSONLプレビューを表示"""
        if not self.current_record or not FILTER_MODULES_LOADED or not JSONLExporter:
            return
        
        try:
            exporter = JSONLExporter()
            jsonl_preview = exporter.preview_jsonl_record(self.current_record, self.stage_name)
            
            dialog = JSONLPreviewDialog(jsonl_preview, self.stage_name, self)
            dialog.show()
            
        except Exception as e:
            print(f"JSONLプレビューエラー: {e}")
            import traceback
            traceback.print_exc()

    def _show_exclusion_message(self, reason: str):
        """除外メッセージを表示"""
        print(f"🚫 DEBUG: StagePreviewWidget - 除外メッセージ表示 - {reason}")
        self._clear_content()
        
        exclusion_widget = QLabel(f"""🚫 品質選定により除外

    このレコードは品質選定により除外されています。

    除外理由: {reason}

    「選定解除」を実行すると通常の表示に戻ります。""")
        
        exclusion_widget.setStyleSheet("""
            QLabel {
                background-color: #3a2a2a; 
                border: 2px solid #ff6b6b; 
                border-radius: 8px; 
                padding: 16px; 
                margin: 8px;
                color: #ffcccc;
                font-size: 14px;
            }
        """)
        exclusion_widget.setWordWrap(True)
        exclusion_widget.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(exclusion_widget)

class DebugInfoDialog(QWidget):
    """デバッグ情報表示ダイアログ"""
    
    def __init__(self, debug_info: Dict[str, Any], stage_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"デバッグ情報 - {stage_name}")
        self.setWindowFlags(Qt.Window)
        self.resize(600, 400)
        self._setup_ui(debug_info)
    
    def _setup_ui(self, debug_info: Dict[str, Any]):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("デバッグ情報"))
        header_layout.addStretch()
        
        close_btn = QPushButton("✖ 閉じる")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        debug_text = QPlainTextEdit()
        debug_text.setPlainText(json.dumps(debug_info, indent=2, ensure_ascii=False))
        debug_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        debug_text.setFont(font)
        layout.addWidget(debug_text)


class JSONLPreviewDialog(QWidget):
    """JSONLプレビュー表示ダイアログ"""
    
    def __init__(self, jsonl_content: str, stage_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"JSONL プレビュー - {stage_name}")
        self.setWindowFlags(Qt.Window)
        self.resize(800, 600)
        self._setup_ui(jsonl_content)
    
    def _setup_ui(self, jsonl_content: str):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("JSONLフォーマットプレビュー"))
        header_layout.addStretch()
        
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(jsonl_content))
        header_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        self.jsonl_text = QPlainTextEdit(jsonl_content)
        self.jsonl_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        self.jsonl_text.setFont(font)
        layout.addWidget(self.jsonl_text)
    
    def _copy_to_clipboard(self, content: str):
        """クリップボードにコピー"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(content)


class DetailTabsWidget(QWidget):
    """段階的詳細表示のメインウィジェット（3タブ構成：raw + noise_removed + jsonl_preview）"""
    
    stage_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_record = None
        self.stage_widgets = {}
        self._setup_ui()
        print("DetailTabsWidget 初期化完了")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # 制御パネル
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("表示段階:"))
        
        self.stage_combo = QComboBox()
        if FILTER_MODULES_LOADED:
            stages = ["raw", "noise_removed", "jsonl_preview"]
            descriptions = {
                "raw": "元データ（無加工）",
                "noise_removed": "ノイズ除去後",
                "jsonl_preview": "JSONL出力プレビュー"
            }
            
            for stage in stages:
                description = descriptions.get(stage, stage)
                self.stage_combo.addItem(f"{stage} - {description}", stage)
            print(f"✓ {len(stages)} 個の段階を読み込み")
        else:
            self.stage_combo.addItem("モジュール未読み込み", "error")
            print("✗ フィルタモジュールが利用できません")
        
        self.stage_combo.currentTextChanged.connect(self._on_stage_changed)
        control_layout.addWidget(self.stage_combo)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        if FILTER_MODULES_LOADED:
            stages_info = [
                ("raw", "元データ（無加工）"),
                ("noise_removed", "ノイズ除去後"),
                ("jsonl_preview", "JSONL出力プレビュー")
            ]
            
            for stage, description in stages_info:
                if stage == "jsonl_preview":
                    stage_widget = JSONLPreviewTabWidget()
                else:
                    stage_widget = StagePreviewWidget(stage, description)
                
                self.stage_widgets[stage] = stage_widget
                self.tab_widget.addTab(stage_widget, self._get_stage_icon(stage) + " " + stage)
            
            print(f"✓ {len(self.stage_widgets)} 個のタブを作成")
        else:
            error_widget = QLabel("フィルタモジュールが読み込まれていません\n\ncontent_filter.py の配置を確認してください")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("color: red; font-size: 14px;")
            self.tab_widget.addTab(error_widget, "⚠ エラー")
        
        layout.addWidget(self.tab_widget)
    
    def _get_stage_icon(self, stage: str) -> str:
        """段階に応じたアイコンを取得"""
        icons = {
            "raw": "",
            "noise_removed": "",
            "jsonl_preview": ""
        }
        return icons.get(stage, "")
    
    def update_content(self, record: Dict[str, Any]):
        """コンテンツを更新（修正版）"""
        self.current_record = record
        
        if not record:
            # 全てのタブに空状態を設定
            for stage_name, widget in self.stage_widgets.items():
                if hasattr(widget, 'update_content'):
                    widget.update_content({})
            return
        
        # 各段階のタブウィジェットにレコードを渡して更新
        for stage_name, widget in self.stage_widgets.items():
            if hasattr(widget, 'update_content'):
                widget.update_content(record)
        
        print(f"DetailTabsWidget - 全タブ更新完了: {record.get('name', '?')}")
    
    def _on_stage_changed(self):
        """段階選択変更時の処理"""
        current_data = self.stage_combo.currentData()
        if current_data and current_data != "error":
            self.stage_changed.emit(current_data)
            print(f" 段階変更: {current_data}")

class JSONLPreviewTabWidget(QWidget):
    """JSONL出力プレビュー専用のタブウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_record = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # ヘッダ
        header_layout = QHBoxLayout()
        header_label = QLabel("JSONL出力プレビュー（実際の出力データ）")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # ステージ選択
        stage_layout = QHBoxLayout()
        stage_layout.addWidget(QLabel("出力ステージ:"))
        
        self.jsonl_stage_combo = QComboBox()
        self.jsonl_stage_combo.addItem("noise_removed", "noise_removed")
        self.jsonl_stage_combo.addItem("rag_optimized", "rag_optimized")
        self.jsonl_stage_combo.currentIndexChanged.connect(self._refresh_jsonl)
        stage_layout.addWidget(self.jsonl_stage_combo)
        
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_btn.setMaximumWidth(80)
        stage_layout.addWidget(copy_btn)
        
        header_layout.addLayout(stage_layout)
        layout.addLayout(header_layout)
        
        # JSONL表示エリア
        self.jsonl_text = QPlainTextEdit()
        self.jsonl_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        self.jsonl_text.setFont(font)
        layout.addWidget(self.jsonl_text)
        
        # 初期状態
        self._show_empty_message()
    
    def _show_empty_message(self):
        """空の状態を表示"""
        self.jsonl_text.setPlainText("項目を選択してください")
    
    def update_content(self, record: Dict[str, Any]):
        """コンテンツを更新（除外判定対応）"""
        self.current_record = record
        
        if not record:
            self._show_empty_message()
            return
        
        # 除外フラグをチェック
        is_excluded = record.get("_ui_excluded", False)
        if is_excluded:
            exclusion_reason = record.get("_ui_exclusion_reason", "品質基準により除外")
            self._show_exclusion_message(exclusion_reason)
            return
        
        # 通常の処理
        # スタイルをリセット
        self.jsonl_text.setStyleSheet("")
        self._refresh_jsonl()
       
    def _refresh_jsonl(self):
        """JSONL内容を更新"""
        if not self.current_record or not FILTER_MODULES_LOADED or not JSONLExporter:
            self.jsonl_text.setPlainText("JSONLExporter が利用できません")
            return
        
        try:
            stage = self.jsonl_stage_combo.currentData()
            exporter = JSONLExporter()
            jsonl_content = exporter.preview_jsonl_record(self.current_record, stage)
            self.jsonl_text.setPlainText(jsonl_content)
        except Exception as e:
            self.jsonl_text.setPlainText(f"JSONL生成エラー: {str(e)}")
            print(f"JSONL生成エラー詳細: {e}")
            import traceback
            traceback.print_exc()
    
    def _copy_to_clipboard(self):
        """クリップボードにコピー"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.jsonl_text.toPlainText())
        print("📋 JSONLをクリップボードにコピーしました")

    def _show_exclusion_message(self, reason: str):
        """除外メッセージを表示"""
        print(f"DEBUG: JSONLPreviewTabWidget - 除外メッセージ表示 - {reason}")
        
        exclusion_text = f"""品質選定により除外

    このレコードは品質選定により除外されています。

    除外理由: {reason}

    「選定解除」を実行すると通常の表示に戻ります。"""
        
        self.jsonl_text.setPlainText(exclusion_text)
        
        # テキストエリアの背景色を変更
        self.jsonl_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #3a2a2a; 
                border: 2px solid #ff6b6b; 
                color: #ffcccc;
            }
        """)