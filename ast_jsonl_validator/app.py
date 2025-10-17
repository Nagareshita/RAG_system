from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

# Ensure repository root on sys.path when run directly
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QPlainTextEdit, QMessageBox, QProgressBar, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
import json

from ast_jsonl_validator.modelica_raw_extractor import (
    extract_symbols_from_file,
    extract_dir,
)
from ast_jsonl_validator.validator import JSONLQualityValidator, SchemaValidator
from ast_jsonl_validator.record_builder import RepoContext, make_jsonl_entry
from ast_jsonl_validator.split_exporter import write_split_outputs, build_split_outputs


class ValidatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modelica AST JSONL Validator")
        self.setGeometry(120, 120, 1200, 800)

        self.records: List[Dict[str, Any]] = []
        self.repo_context = RepoContext()
        schema_path = Path(__file__).resolve().parent / "AST_schema.json"
        self.schema_validator = SchemaValidator(schema_path)

        self._setup_ui()

        # worker/進捗用ハンドル
        self._worker: Optional[QThread] = None
        self._progress_dialog: Optional[QWidget] = None

    # ---- 進捗UI ----
    class _Progress(QDialog):
        def __init__(self, title: str, parent=None):
            super().__init__(parent)
            self.setWindowTitle(title)
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
            self.setModal(True)
            self.setFixedSize(450, 120)
            lay = QVBoxLayout(self)
            
            self.label = QLabel("処理中...")
            lay.addWidget(self.label)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            lay.addWidget(self.progress_bar)
            
            self.detail_label = QLabel("")
            self.detail_label.setStyleSheet("color: gray; font-size: 9pt;")
            lay.addWidget(self.detail_label)

        def update(self, message: str, value: int, maximum: int = 100):
            self.label.setText(message)
            pct = int((value / maximum) * 100) if maximum else 0
            self.progress_bar.setValue(pct)
            self.detail_label.setText(f"{value} / {maximum}")

    class _ExtractWorker(QThread):
        progress = Signal(str, int, int)  # message, current, total
        done = Signal(list)
        error = Signal(str)

        def __init__(self, path: Path, is_dir: bool):
            super().__init__()
            self.path = path
            self.is_dir = is_dir

        def _on_progress(self, message: str, current: int, total: int):
            self.progress.emit(message, current, total)

        def run(self):
            try:
                if self.is_dir:
                    recs = extract_dir(self.path, progress_callback=self._on_progress)
                else:
                    recs = extract_symbols_from_file(str(self.path))
                dicts = [r.to_dict() if hasattr(r, 'to_dict') else r for r in recs]
                self.done.emit(dicts)
            except Exception as e:
                self.error.emit(str(e))

    def _setup_ui(self):
        cw = QWidget()
        root = QVBoxLayout(cw)
        self.setCentralWidget(cw)

        # Toolbar
        bar = QHBoxLayout()
        self.btn_open_file = QPushButton("ファイル読込")
        self.btn_open_dir = QPushButton("ディレクトリ読込")
        self.btn_validate_raw = QPushButton("分割前検証")
        self.btn_validate_split = QPushButton("分割後検証")
        self.btn_export = QPushButton("JSONL出力")
        self.btn_validate_jsonl = QPushButton("JSONL検証")
        bar.addWidget(self.btn_open_file)
        bar.addWidget(self.btn_open_dir)
        bar.addStretch()
        bar.addWidget(self.btn_validate_raw)
        bar.addWidget(self.btn_validate_split)
        bar.addWidget(self.btn_export)
        bar.addWidget(self.btn_validate_jsonl)
        root.addLayout(bar)

        # Main splitter with hierarchy tree and detail tabs
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ライブラリ構造"])
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        splitter.addWidget(self.tree)

        self.detail_tabs = QTabWidget()
        splitter.addWidget(self.detail_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.preview_view = QPlainTextEdit()
        self.preview_view.setReadOnly(True)
        self.detail_tabs.addTab(self.preview_view, "JSONLプレビュー")

        self.detail_view = QPlainTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_tabs.addTab(self.detail_view, "構造サマリ")

        self.validation_view = QPlainTextEdit()
        self.validation_view.setReadOnly(True)
        self.detail_tabs.addTab(self.validation_view, "検証結果")

        # Connections
        self.btn_open_file.clicked.connect(self._load_file)
        self.btn_open_dir.clicked.connect(self._load_dir)
        self.btn_validate_raw.clicked.connect(self._run_validation_raw)
        self.btn_validate_split.clicked.connect(self._run_validation_split)
        self.btn_export.clicked.connect(self._export_jsonl)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection)
        self.btn_validate_jsonl.clicked.connect(self._validate_jsonl_file)

    # Actions
    def _load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Modelicaファイル選択", "", "Modelica (*.mo);;All files (*)")
        if not file_path:
            return
        try:
            self._start_extraction(Path(file_path), is_dir=False)
        except Exception as e:
            QMessageBox.critical(self, "抽出エラー", str(e))

    def _load_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Modelicaディレクトリ選択")
        if not dir_path:
            return
        try:
            self._start_extraction(Path(dir_path), is_dir=True)
        except Exception as e:
            QMessageBox.critical(self, "抽出エラー", str(e))

    def _start_extraction(self, path: Path, is_dir: bool):
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "情報", "抽出処理が実行中です")
            return
        # 進捗ダイアログ
        self._progress_dialog = self._Progress("データ抽出中", self)
        self._progress_dialog.show()
        QApplication.processEvents()

        self._worker = self._ExtractWorker(path, is_dir)
        self._worker.progress.connect(self._on_extract_progress)
        self._worker.done.connect(self._on_extract_done)
        self._worker.error.connect(self._on_extract_error)
        self._worker.start()

    def _on_extract_progress(self, message: str, current: int, total: int):
        if self._progress_dialog:
            try:
                self._progress_dialog.update(message, current, total)
            except Exception:
                pass
        QApplication.processEvents()

    def _on_extract_done(self, records: List[Dict[str, Any]]):
        try:
            self._set_records(records)
        finally:
            self._finish_progress()

    def _on_extract_error(self, err: str):
        try:
            QMessageBox.critical(self, "抽出エラー", err)
        finally:
            self._finish_progress()

    def _finish_progress(self):
        if self._worker:
            self._worker.quit()
            self._worker.wait(200)
            self._worker = None
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

    def _set_records(self, records: List[Dict[str, Any]]):
        self.records = records
        self._build_tree()
        self.validation_view.setPlainText("")
        self.preview_view.setPlainText("")
        self.detail_view.setPlainText("")

    def _build_tree(self):
        self.tree.clear()
        path_items: Dict[Tuple[str, ...], QTreeWidgetItem] = {}

        for idx, rec in enumerate(self.records):
            package = tuple(rec.get("package_path", []))
            parent_item = None
            current_path: Tuple[str, ...] = ()
            for part in package:
                current_path = current_path + (part,)
                if current_path not in path_items:
                    item = QTreeWidgetItem([part])
                    item.setData(0, Qt.UserRole, {"type": "package", "path": current_path})
                    if parent_item is None:
                        self.tree.addTopLevelItem(item)
                    else:
                        parent_item.addChild(item)
                    item.setExpanded(True)
                    path_items[current_path] = item
                parent_item = path_items[current_path]

            label = f"{rec.get('kind', '?')}: {rec.get('name', rec.get('fqn', 'unknown'))}"
            symbol_item = QTreeWidgetItem([label])
            symbol_item.setData(0, Qt.UserRole, {"type": "symbol", "index": idx})
            parent = path_items.get(package)
            if parent is None:
                self.tree.addTopLevelItem(symbol_item)
            else:
                parent.addChild(symbol_item)

        self.tree.expandToDepth(1)
        first_symbol = self._find_first_symbol_item()
        if first_symbol:
            self.tree.setCurrentItem(first_symbol)

    def _find_first_symbol_item(self) -> Optional[QTreeWidgetItem]:
        def visit(item: QTreeWidgetItem) -> Optional[QTreeWidgetItem]:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict) and data.get("type") == "symbol":
                return item
            for i in range(item.childCount()):
                found = visit(item.child(i))
                if found:
                    return found
            return None

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            found = visit(item)
            if found:
                return found
        return None

    def _on_tree_selection(self):
        items = self.tree.selectedItems()
        if not items:
            return

        data = items[0].data(0, Qt.UserRole) or {}
        node_type = data.get("type")

        if node_type == "symbol":
            idx = data.get("index")
            if idx is None or idx >= len(self.records):
                return
            rec = self.records[idx]
            entry = make_jsonl_entry(rec, self.repo_context)
            self.preview_view.setPlainText(json.dumps(entry, ensure_ascii=False, indent=2))
            self.detail_view.setPlainText(self._build_symbol_summary(rec))
            self.detail_tabs.setCurrentWidget(self.preview_view)
        elif node_type == "package":
            path = tuple(data.get("path", ()))
            self.preview_view.setPlainText("")
            self.detail_view.setPlainText(self._build_package_summary(path))
            self.detail_tabs.setCurrentWidget(self.detail_view)
        else:
            self.preview_view.setPlainText("")
            self.detail_view.setPlainText("")

    def _build_symbol_summary(self, rec: Dict[str, Any]) -> str:
        lines: List[str] = []
        pkg = ".".join(rec.get("package_path", [])) or "<root>"
        lines.append(f"FQN: {rec.get('fqn', '')}")
        lines.append(f"種別: {rec.get('kind', '')}")
        lines.append(f"パッケージ: {pkg}")
        lines.append(f"extends: {', '.join(rec.get('extends', [])) or '-'}")
        lines.append(f"imports: {', '.join(rec.get('imports', [])) or '-'}")

        parameters = rec.get("parameters", [])
        components = rec.get("components", [])
        equations = rec.get("equations", [])

        lines.append("")
        lines.append(f"パラメータ ({len(parameters)}):")
        for param in parameters[:10]:
            p_name = param.get("name")
            p_type = param.get("type")
            default = param.get("default")
            lines.append(f"  - {p_name} : {p_type or '?'}{f' = {default}' if default else ''}")
        if len(parameters) > 10:
            lines.append(f"  ... 他 {len(parameters) - 10} 件")

        lines.append("")
        lines.append(f"コンポーネント ({len(components)}):")
        for comp in components[:10]:
            c_name = comp.get("name")
            c_type = comp.get("type_name") or comp.get("type") or "?"
            prefixes = comp.get("prefixes") or []
            prefix_str = f" [{' '.join(prefixes)}]" if prefixes else ""
            lines.append(f"  - {c_name}: {c_type}{prefix_str}")
        if len(components) > 10:
            lines.append(f"  ... 他 {len(components) - 10} 件")

        eq_count = sum(len(block.get("equations", [])) for block in equations)
        lines.append("")
        lines.append(f"方程式ブロック: {len(equations)} （式合計 {eq_count}）")

        doc = rec.get("docstring") or ""
        if doc:
            lines.append("")
            lines.append("ドキュメント抜粋:")
            snippet = doc.strip()
            if len(snippet) > 600:
                snippet = snippet[:600] + "..."
            lines.append(snippet)

        return "\n".join(lines)

    def _build_package_summary(self, path: Tuple[str, ...]) -> str:
        prefix_len = len(path)
        subset = [
            rec for rec in self.records
            if tuple(rec.get("package_path", []))[:prefix_len] == path
        ]

        name = ".".join(path) if path else "<root>"
        lines: List[str] = []
        lines.append(f"パッケージ: {name}")
        lines.append(f"記号数: {len(subset)}")

        kind_counts = Counter(rec.get("kind", "unknown") for rec in subset)
        if kind_counts:
            lines.append("種別内訳:")
            for kind, count in kind_counts.most_common():
                lines.append(f"  - {kind}: {count}")

        if subset:
            next_level = Counter()
            for rec in subset:
                pkg = rec.get("package_path", [])
                if len(pkg) > prefix_len:
                    next_level[pkg[prefix_len]] += 1
            if next_level:
                lines.append("サブパッケージ:")
                for child, count in next_level.most_common():
                    lines.append(f"  - {child}: {count}")

        lines.append("")
        lines.append("代表的な記号:")
        for rec in subset[:10]:
            lines.append(f"  - {rec.get('kind', '?')}: {rec.get('name', rec.get('fqn', 'unknown'))}")
        if len(subset) > 10:
            lines.append(f"  ... 他 {len(subset) - 10} 件")

        return "\n".join(lines)

    def _run_validation_raw(self):
        """分割前の生データを検証"""
        if not self.records:
            QMessageBox.information(self, "情報", "検証するデータがありません")
            return
        
        validator = JSONLQualityValidator()
        issues, stats = validator.validate(self.records)
        
        lines: List[str] = []
        lines.append("===== 分割前データの検証 =====")
        lines.append(f"総レコード数: {stats['total']}")
        lines.append(f"最大推定長: {stats['max_estimated_len']}")
        lines.append(f"警告閾超: {stats['over_warn']} / 上限超: {stats['over_max']}")
        lines.append(f"ID重複: {stats['dupe_ids']} / 内容重複: {stats['dupe_signatures']}")
        lines.append("\n種別内訳:")
        for k, v in sorted(stats["kinds"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k}: {v}")
        
        if issues:
            lines.append("\n検出問題:")
            for iss in issues[:500]:
                lines.append(f"- [{iss.level}] {iss.code}: {iss.message} {('('+iss.target_id+')') if iss.target_id else ''}")
            if len(issues) > 500:
                lines.append(f"... 他 {len(issues)-500} 件")
        else:
            lines.append("\n問題は見つかりませんでした。")
        
        self.validation_view.setPlainText("\n".join(lines))
        self.detail_tabs.setCurrentWidget(self.validation_view)
    
    def _run_validation_split(self):
        """分割後のデータを検証（実際に保存される形式）"""
        if not self.records:
            QMessageBox.information(self, "情報", "検証するデータがありません")
            return
        
        try:
            # メモリ上で分割処理を実行
            packages, functions, equations, split_stats = build_split_outputs(
                self.records, self.repo_context
            )
            
            # 分割後の各カテゴリを検証
            lines: List[str] = []
            lines.append("===== 分割後データの検証 =====")
            lines.append(f"パッケージレコード: {len(packages)}")
            lines.append(f"関数レコード: {len(functions)}")
            lines.append(f"方程式レコード: {len(equations)}")
            lines.append(f"総レコード数: {len(packages) + len(functions) + len(equations)}")
            
            # ID重複チェック
            all_ids = [r.get('id') for r in packages + functions + equations]
            id_counts = Counter(all_ids)
            duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
            lines.append(f"\nID重複: {len(duplicate_ids)}")
            if duplicate_ids:
                lines.append("重複ID一覧:")
                for dup_id, count in list(duplicate_ids.items())[:10]:
                    lines.append(f"  - {dup_id}: {count}回")
                if len(duplicate_ids) > 10:
                    lines.append(f"  ... 他 {len(duplicate_ids)-10} 件")
            
            # 各カテゴリのサイズ統計
            lines.append("\n===== パッケージレコードのサイズ統計 =====")
            pkg_sizes = [len(r.get('code_text', '')) for r in packages]
            if pkg_sizes:
                lines.append(f"最小: {min(pkg_sizes)} / 最大: {max(pkg_sizes)} / 平均: {sum(pkg_sizes)//len(pkg_sizes)}")
                over_limit = sum(1 for s in pkg_sizes if s > 10000)
                lines.append(f"10KB超過: {over_limit} 件")
            
            lines.append("\n===== 関数レコードのサイズ統計 =====")
            func_sizes = [len(r.get('code_text', '')) for r in functions]
            if func_sizes:
                lines.append(f"最小: {min(func_sizes)} / 最大: {max(func_sizes)} / 平均: {sum(func_sizes)//len(func_sizes)}")
                over_limit = sum(1 for s in func_sizes if s > 10000)
                lines.append(f"10KB超過: {over_limit} 件")
            
            lines.append("\n===== 方程式レコードのサイズ統計 =====")
            eq_sizes = [len(str(r.get('equation', ''))) for r in equations]
            if eq_sizes:
                lines.append(f"最小: {min(eq_sizes)} / 最大: {max(eq_sizes)} / 平均: {sum(eq_sizes)//len(eq_sizes)}")
            
            # 分割統計
            lines.append("\n===== 分割統計 =====")
            split_packages = [r for r in packages if r.get('meta', {}).get('split_policy', {}).get('strategy') != 'none']
            split_functions = [r for r in functions if r.get('meta', {}).get('split_policy', {}).get('strategy') != 'none']
            lines.append(f"分割されたパッケージ: {len(split_packages)}")
            lines.append(f"分割された関数: {len(split_functions)}")
            
            if duplicate_ids:
                lines.append("\n⚠️ 警告: ID重複が検出されました！")
            else:
                lines.append("\n✓ ID重複なし: 検証成功")
            
            self.validation_view.setPlainText("\n".join(lines))
            self.detail_tabs.setCurrentWidget(self.validation_view)
            
        except Exception as e:
            QMessageBox.critical(self, "検証エラー", f"分割後検証中にエラーが発生しました:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _export_jsonl(self):
        if not self.records:
            QMessageBox.information(self, "情報", "出力するデータがありません")
            return
        
        # デフォルトの出力先を data/ast に設定
        default_dir = Path(__file__).resolve().parents[1] / "data" / "ast"
        
        # ディレクトリ選択ダイアログを表示
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "JSONL出力先ディレクトリを選択", 
            str(default_dir)
        )
        
        # キャンセルされた場合は処理を中止
        if not dir_path:
            return
        
        output_dir = Path(dir_path)
        
        try:
            # 出力ディレクトリを作成（存在しない場合）
            output_dir.mkdir(parents=True, exist_ok=True)
            
            stats = write_split_outputs(self.records, self.repo_context, output_dir)
            QMessageBox.information(
                self,
                "出力完了",
                (
                    f"出力先: {output_dir}\n"
                    f"ast_packages.jsonl: {stats['packages']} 行\n"
                    f"ast_functions.jsonl: {stats['functions']} 行\n"
                    f"ast_equations.jsonl: {stats['equations']} 行\n"
                    f"重複ID: {stats['duplicate_ids']}"
                ),
            )
        except Exception as e:
            QMessageBox.critical(self, "出力エラー", str(e))

    def _validate_jsonl_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "検証するJSONLを選択", "", "JSONL (*.jsonl);;All files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_lines = [line.rstrip("\n") for line in f if line.strip()]

            parsed: List[Dict[str, Any]] = []
            parse_errors = 0
            parse_messages: List[str] = []
            for idx, line in enumerate(raw_lines, start=1):
                try:
                    parsed.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    parse_errors += 1
                    parse_messages.append(f"[error] PARSE_FAIL line {idx}: {exc}")

            schema_issues = self.schema_validator.validate_lines(raw_lines)

            ast_records: List[Dict[str, Any]] = []
            for obj in parsed:
                ast = (obj.get("collections") or {}).get("ast_record") if isinstance(obj, dict) else None
                if isinstance(ast, dict):
                    ast_records.append(ast)

            code_lengths = [len(ast.get("code_text", "")) for ast in ast_records]
            max_code = max(code_lengths) if code_lengths else 0
            avg_code = sum(code_lengths) / len(code_lengths) if code_lengths else 0
            kinds = Counter(ast.get("kind", "unknown") for ast in ast_records)
            packages = Counter(".".join(ast.get("package_path", [])) for ast in ast_records)

            ids = [ast.get("id") for ast in ast_records]
            id_counts = Counter(ids)
            dup_ids = {k: v for k, v in id_counts.items() if v > 1 and k is not None}

            report_lines: List[str] = []
            report_lines.append(f"ファイル: {Path(path).name}")
            report_lines.append(f"総行数: {len(raw_lines)} / 有効ASTレコード: {len(ast_records)} / 解析エラー: {parse_errors}")
            report_lines.append(f"code_text 最大長: {max_code} / 平均: {avg_code:.1f}")
            report_lines.append("種類内訳: " + ", ".join(f"{k}:{v}" for k, v in kinds.most_common()))
            report_lines.append("パッケージ内訳: " + ", ".join(f"{k or '<root>'}:{v}" for k, v in packages.most_common(5)))
            report_lines.append(f"重複ID: {len(dup_ids)}")

            if dup_ids:
                sample = list(dup_ids.items())[:5]
                report_lines.append(f"  例: {sample}")

            if parse_messages:
                report_lines.append("\n解析エラー詳細:")
                report_lines.extend(parse_messages)

            if schema_issues:
                report_lines.append("\nスキーマ検証結果:")
                for issue in schema_issues[:50]:
                    report_lines.append(f"- [{issue.level}] {issue.code}: {issue.message}")
                if len(schema_issues) > 50:
                    report_lines.append(f"... 他 {len(schema_issues) - 50} 件")

            if not parse_messages and not schema_issues and not dup_ids:
                report_lines.append("\n問題は見つかりませんでした。")
            self.validation_view.setPlainText("\n".join(report_lines))
            self.detail_tabs.setCurrentWidget(self.validation_view)
        except Exception as e:
            QMessageBox.critical(self, "検証エラー", str(e))


def main():
    app = QApplication(sys.argv)
    w = ValidatorApp()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
