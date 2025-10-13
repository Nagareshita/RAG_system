# tabs/modelica_analyzer_tab.py
"""
Modelica AST解析ツールタブ（main.py統合版）
段階的フィルタリング（raw → noise_removed → rag_optimized）とプレビュー機能を提供
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QLabel, QSplitter, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QAction, QColor

# 新システムのインポート
from tabs.modelica_modules.modelica.ast_extractor import extract_symbols_from_file, extract_dir
from tabs.modelica_modules.modelica.content_filter import ContentFilter, FilterRuleManager
from tabs.modelica_modules.modelica.jsonl_exporter import JSONLExporter
from tabs.modelica_modules.ui.components import apply_dark_style
from tabs.modelica_modules.ui.tree_builder import TreeBuilder
from tabs.modelica_modules.ui.detail_tabs import DetailTabsWidget


class ExtractionWorker(QThread):
    """抽出処理ワーカー（新システム対応）"""
    
    progress_updated = Signal(str, int, int)
    extraction_completed = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, path: Path, is_directory: bool = False):
        super().__init__()
        self.path = path
        self.is_directory = is_directory
        self._stop_requested = False
    
    def run(self):
        """抽出実行"""
        try:
            self.progress_updated.emit("抽出開始...", 0, 100)
            
            if self.is_directory:
                self.progress_updated.emit("ディレクトリスキャン中...", 10, 100)
                # extract_dir に進捗コールバックを渡す（ast_extractor.py を修正する必要あり）
                records = extract_dir(self.path, progress_callback=self._update_progress)
            else:
                self.progress_updated.emit("ファイル解析中...", 50, 100)
                records = extract_symbols_from_file(str(self.path))
            
            if self._stop_requested:
                return
            
            # SymbolRecordを辞書形式に変換
            dict_records = []
            for record in records:
                if hasattr(record, 'to_dict'):
                    dict_records.append(record.to_dict())
                else:
                    # 既に辞書の場合
                    dict_records.append(record)
            
            self.progress_updated.emit("抽出完了", 100, 100)
            self.extraction_completed.emit(dict_records)
            
        except Exception as e:
            self.error_occurred.emit(f"抽出エラー: {str(e)}")
    
    def stop(self):
        """停止要求"""
        self._stop_requested = True

    def _update_progress(self, message: str, value: int):
        """進捗更新コールバック"""
        self.progress_updated.emit(message, value, 100)

class ProgressDialog(QWidget):
    """プログレス表示用ダイアログ"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setFixedSize(400, 120)
        self._setup_ui()
        
        # 親ウィンドウの中央に配置
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.message_label = QLabel("処理中...")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.detail_label)
    
    def update_progress(self, message: str, value: int = 0, maximum: int = 0, detail: str = ""):
        """プログレス更新"""
        from PySide6.QtWidgets import QApplication
        self.message_label.setText(message)
        if maximum > 0:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)
        else:
            self.progress_bar.setMaximum(0)  # 不定期間
        self.detail_label.setText(detail)
        QApplication.processEvents()


class ModelicaAnalyzerTab(QWidget):
    """Modelica AST解析ツールタブ（main.py統合版）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # データ管理
        self.raw_records: List[Dict[str, Any]] = []
        self.filtered_records: List[Dict[str, Any]] = []
        self.extraction_worker: Optional[ExtractionWorker] = None
        
        # コンポーネント初期化
        self.content_filter = ContentFilter()
        self.filter_manager = FilterRuleManager()
        
        self._setup_ui()
        self._setup_toolbar()
        
    print("Modelica AST解析タブ初期化完了（新システム）")
    
    def _set_tree_styles(self) -> None:
        """ツリーのスタイル設定"""
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QTreeWidget::item {
                color: black;
                padding: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #e0e0e0;
            }
        """)
    
    def _setup_ui(self):
        """UIセットアップ（2分割レイアウト + 閾値選定機能）"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # デフォルトフォントを他タブと揃える（軽微な調整）
        default_font = QFont()
        default_font.setPointSize(10)
        self.setFont(default_font)

    # ツールバーエリア（他タブに合わせて高さを揃える）
        self.toolbar_container = QWidget()
        self.toolbar_container.setFixedHeight(42)
        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(8)
        main_layout.addWidget(self.toolbar_container)

        # コンテンツエリア（左右スプリッター）
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(8)

        # 左側：ツリー表示 + 閾値選定
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # ツリーヘッダー（ツリー部分は絵文字を残す）
        tree_header = QLabel("ライブラリ構造")
        tree_header.setFont(QFont("", 12, QFont.Weight.Bold))
        left_layout.addWidget(tree_header)

        # 閾値選定UI
        threshold_group = QGroupBox("JSONL品質選定")
        threshold_layout = QFormLayout()
        threshold_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        threshold_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self.content_length_threshold = QSpinBox()
        self.content_length_threshold.setRange(100, 10000)
        self.content_length_threshold.setValue(5000)
        self.content_length_threshold.setSuffix(" 文字")
        threshold_layout.addRow("コンテンツ長閾値:", self.content_length_threshold)

        # 選定実行ボタン（絵文字を削除）
        threshold_buttons = QHBoxLayout()
        self.apply_threshold_btn = QPushButton("選定実行")
        self.apply_threshold_btn.clicked.connect(self._apply_threshold_selection)
        self.clear_selection_btn = QPushButton("選定解除")
        self.clear_selection_btn.clicked.connect(self._clear_threshold_selection)
        threshold_buttons.addWidget(self.apply_threshold_btn)
        threshold_buttons.addWidget(self.clear_selection_btn)
        threshold_layout.addRow(threshold_buttons)

        # 選定結果表示
        self.selection_status = QLabel("選定未実行")
        self.selection_status.setStyleSheet("color: #888; font-style: italic;")
        threshold_layout.addRow("選定状況:", self.selection_status)

        threshold_group.setLayout(threshold_layout)
        left_layout.addWidget(threshold_group)

        # 見た目調整：ボタン最小サイズを他タブに合わせる
        self.apply_threshold_btn.setMinimumWidth(110)
        self.clear_selection_btn.setMinimumWidth(110)

        # ツリーウィジェット
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名前", "種類"])
        self.tree_widget.itemClicked.connect(self._on_tree_item_clicked)
        
        # 名前列の幅を広げる（デフォルトより広く）
        self.tree_widget.setColumnWidth(0, 180)  # 名前列を180pxに設定
        
        left_layout.addWidget(self.tree_widget)

        self._set_tree_styles()

        # ツリービルダー
        self.tree_builder = TreeBuilder(self.tree_widget)

        # 右側：詳細表示（段階的タブ）
        self.detail_tabs = DetailTabsWidget()

        # スプリッター配置
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(self.detail_tabs)
        content_splitter.setSizes([300, 900])
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 4)

        # ステータスラベル（下段をドラッグ可能にするために縦スプリッターに配置）
        self.status_label = QLabel("準備完了 - 新システム")
        self.status_label.setStyleSheet("color: #888; font-style: italic; padding: 4px; background: white;")
        self.status_label.setMinimumHeight(20)
        self.status_label.setMaximumHeight(100)

        # 縦スプリッター（content_splitter と status_label を上下に配置）
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.addWidget(content_splitter)
        vertical_splitter.addWidget(self.status_label)
        vertical_splitter.setSizes([800, 30])  # 上を広く、下を狭く
        vertical_splitter.setHandleWidth(6)
        
        main_layout.addWidget(vertical_splitter)

        # 選定データ管理
        self.selected_records = []
        self.threshold_applied = False
    
    def _setup_toolbar(self):
        """ツールバーセットアップ（ディレクトリ選択のみ + プログレスバー）"""
        toolbar_layout = self.toolbar_container.layout()

        # ディレクトリ選択
        open_dir_btn = QPushButton("ディレクトリ選択")
        open_dir_btn.clicked.connect(self._open_directory)
        toolbar_layout.addWidget(open_dir_btn)

        toolbar_layout.addStretch()

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumHeight(20)
        toolbar_layout.addWidget(self.progress_bar)

        # 停止ボタン
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop_extraction)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMaximumWidth(60)
        toolbar_layout.addWidget(self.stop_btn)

        # 選定JSONL出力
        export_selected_btn = QPushButton("選定JSONL出力")
        export_selected_btn.clicked.connect(self._export_selected_jsonl)
        toolbar_layout.addWidget(export_selected_btn)

        # 全データJSONL出力
        export_all_btn = QPushButton("JSONL出力")
        export_all_btn.clicked.connect(self._export_all_jsonl)
        toolbar_layout.addWidget(export_all_btn)

        # 統計表示
        stats_btn = QPushButton("統計")
        stats_btn.clicked.connect(self._show_statistics)
        toolbar_layout.addWidget(stats_btn)
    
    def _open_directory(self):
        """ディレクトリ選択"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Modelicaディレクトリを選択"
        )
        
        if dir_path:
            self._start_extraction(Path(dir_path), True)
    
    def _start_extraction(self, path: Path, is_directory: bool):
        """抽出開始（プログレスダイアログ表示）"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            QMessageBox.warning(self, "警告", "既に抽出処理が実行中です")
            return
        
        # プログレスダイアログを表示
        self.progress_dialog = ProgressDialog("データ読み込み中", self)
        self.progress_dialog.show()
        self.progress_dialog.update_progress(f"読み込み開始: {path.name}")
        
        self.status_label.setText(f"読み込み中: {path.name}")
        self.stop_btn.setEnabled(True)
        
        # ワーカー開始
        self.extraction_worker = ExtractionWorker(path, is_directory)
        self.extraction_worker.progress_updated.connect(self._on_progress_updated)
        self.extraction_worker.extraction_completed.connect(self._on_extraction_completed)
        self.extraction_worker.error_occurred.connect(self._on_extraction_error)
        self.extraction_worker.start()
    
    def _stop_extraction(self):
        """抽出停止"""
        if self.extraction_worker:
            self.extraction_worker.stop()
            self.extraction_worker.wait(3000)
        
        self._reset_progress()
        self.status_label.setText("抽出を停止しました")
    
    def _on_progress_updated(self, message: str, value: int, maximum: int):
        """進捗更新（プログレスダイアログ対応）"""
        self.status_label.setText(message)
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            detail = f"({value}/{maximum})" if maximum > 0 else ""
            self.progress_dialog.update_progress(message, value, maximum, detail)
    
    def _on_extraction_completed(self, records: List[Dict[str, Any]]):
        """抽出完了（プログレスダイアログ終了）"""
        self.raw_records = records
        
        # プログレスダイアログを閉じる
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self._reset_progress()
        self.status_label.setText(f"抽出完了: {len(records)} 件のレコード")
        
        # フィルタ適用とツリー構築
        self._apply_current_filter()
        
        print(f"抽出完了: {len(records)} 件")
    
    def _on_extraction_error(self, error_message: str):
        """抽出エラー（プログレスダイアログ終了）"""
        # プログレスダイアログを閉じる
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self._reset_progress()
        self.status_label.setText("抽出エラー")
        QMessageBox.critical(self, "抽出エラー", error_message)
    
    def _reset_progress(self):
        """進捗リセット"""
        self.progress_bar.setVisible(False)
        self.stop_btn.setEnabled(False)
    
    def _apply_current_filter(self):
        """現在のフィルタ設定を適用"""
        if not self.raw_records:
            return
        
        try:
            # 簡略化：noise_removedステージで固定フィルタ適用
            self.filtered_records = []
            for record in self.raw_records:
                filtered_record = self.content_filter.filter_record(record, "noise_removed")
                self.filtered_records.append(filtered_record)
            
            # ツリー更新
            self.tree_builder.build_tree_from_records(self.filtered_records)
            
            # 統計更新
            self.status_label.setText(f"フィルタ適用完了: {len(self.filtered_records)} 件")
            
            # 選定状態をリセット
            self._clear_threshold_selection()
            
        except Exception as e:
            QMessageBox.critical(self, "フィルタエラー", f"フィルタ適用に失敗しました:\n{str(e)}")
    
    def _apply_threshold_selection(self):
        """閾値に基づいてレコードを選定してツリーを視覚化"""
        if not self.filtered_records:
            QMessageBox.warning(self, "警告", "選定するデータがありません")
            return
        
        print(f"🎯 DEBUG: 閾値選定開始 - 対象レコード数: {len(self.filtered_records)}")
        
        content_threshold = self.content_length_threshold.value()
        print(f"🎯 DEBUG: 設定閾値: {content_threshold}文字")
        
        # プログレスダイアログ表示
        progress_dialog = ProgressDialog("品質選定中", self)
        progress_dialog.show()
        
        self.selected_records = []
        self.excluded_records = []  # 閾値以上のレコード
        selected_count = 0
        
        # threshold_appliedフラグを先に設定
        self.threshold_applied = True
        print(f"🎯 DEBUG: threshold_applied = {self.threshold_applied}")
        
        for i, record in enumerate(self.filtered_records):
            progress_dialog.update_progress(
                "閾値適用中...", i + 1, len(self.filtered_records), 
                f"{record.get('name', '?')}"
            )
            
            is_selected = self._evaluate_record_quality(record, content_threshold)
            record_name = record.get('name', '?')
            
            if is_selected:
                self.selected_records.append(record)
                selected_count += 1
                print(f"✅ DEBUG: 選定 - {record_name}")
            else:
                self.excluded_records.append(record)
                print(f"❌ DEBUG: 除外 - {record_name}")
        
        progress_dialog.close()
        
        print(f"🎯 DEBUG: 選定結果 - 選定: {len(self.selected_records)}, 除外: {len(self.excluded_records)}")
        
        # ツリーの視覚化更新
        print(f"🌳 DEBUG: ツリー更新開始")
        self._update_tree_based_on_selection()
        
        # ステータス更新
        excluded_count = len(self.excluded_records)
        self.selection_status.setText(f"選定済み: {selected_count}件 / 除外: {excluded_count}件")
        self.selection_status.setStyleSheet("color: #4a9eff; font-weight: bold;")
        
        self.status_label.setText(f"選定完了: {selected_count}件（{content_threshold}文字以下）を選定")
        
        print(f"🎯 DEBUG: 閾値選定完了 - threshold_applied = {self.threshold_applied}")
    
    def _evaluate_record_quality(self, record: Dict[str, Any], content_threshold: int) -> bool:
        """レコードの品質を評価（JSONLタブと同じ文字数で判定）"""
        try:
            # JSONLタブと同じ方法でJSONL文字列を生成
            exporter = JSONLExporter()
            jsonl_content = exporter.preview_jsonl_record(record, "noise_removed")
            content_length = len(jsonl_content)
            
            # 閾値以下（短い）のレコードを選定
            return content_length <= content_threshold
            
        except Exception as e:
            print(f"品質評価エラー: {record.get('name', '?')} - {e}")
            return False
    
    def _update_tree_based_on_selection(self):
        """選定結果に基づいてツリーの表示を更新"""
        print(f"🌳 DEBUG: ツリー更新開始")
        
        if not self.selected_records and not hasattr(self, 'excluded_records'):
            print(f"❌ DEBUG: 選定データなし")
            return
        
        # 選定・除外レコードのFQNセットを作成
        selected_fqns = {record.get("fqn", record.get("name", "")) for record in self.selected_records}
        excluded_fqns = {record.get("fqn", record.get("name", "")) for record in getattr(self, 'excluded_records', [])}
        
        print(f"🌳 DEBUG: 選定FQN: {list(selected_fqns)[:5]}...")
        print(f"🌳 DEBUG: 除外FQN: {list(excluded_fqns)[:5]}...")
        
        items_updated = 0
        
        def update_item_appearance(item):
            nonlocal items_updated
            
            data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if data and isinstance(data, dict):
                # このアイテムのレコードをチェック
                item_records = []
                if "records" in data and data["records"]:
                    item_records = data["records"]
                elif "kind" in data:
                    # 単一レコードの場合
                    item_records = [data]
                
                if item_records:
                    record = item_records[0]  # 最初のレコードで判定
                    record_fqn = record.get("fqn", record.get("name", ""))
                    
                    if record_fqn in excluded_fqns:
                        # 除外対象：グレー表示
                        gray_color = QColor(100, 100, 100)
                        item.setForeground(0, gray_color)
                        item.setForeground(1, gray_color)
                        
                        bg_color = QColor(50, 50, 50)
                        item.setBackground(0, bg_color)
                        item.setBackground(1, bg_color)
                        
                        jsonl_content = self._get_record_jsonl_content(record)
                        item.setToolTip(0, f"閾値以上のため除外: {len(jsonl_content)} 文字")
                        items_updated += 1
                        print(f"🚫 DEBUG: 除外表示適用 - {record_fqn}")
                        
                    elif record_fqn in selected_fqns:
                        # 選定対象：ハイライト表示（白背景）
                        black_color = QColor(0, 0, 0)
                        white_bg = QColor(255, 255, 255)
                        
                        item.setForeground(0, black_color)
                        item.setForeground(1, black_color)
                        item.setBackground(0, white_bg)
                        item.setBackground(1, white_bg)
                        
                        jsonl_content = self._get_record_jsonl_content(record)
                        item.setToolTip(0, f"選定済み: {len(jsonl_content)} 文字")
                        items_updated += 1
                        print(f"✅ DEBUG: 選定表示適用 - {record_fqn}")
                        
                    else:
                        # 該当なし：通常表示にリセット
                        white_color = QColor(255, 255, 255)
                        transparent_color = QColor(0, 0, 0, 0)
                        
                        item.setForeground(0, white_color)
                        item.setForeground(1, white_color)
                        item.setBackground(0, transparent_color)
                        item.setBackground(1, transparent_color)
                        item.setToolTip(0, "")
                else:
                    # レコードがないパッケージ等：通常表示
                    white_color = QColor(255, 255, 255)
                    transparent_color = QColor(0, 0, 0, 0)
                    
                    item.setForeground(0, white_color)
                    item.setForeground(1, white_color)
                    item.setBackground(0, transparent_color)
                    item.setBackground(1, transparent_color)
                    item.setToolTip(0, "")
            
            # 子アイテムも再帰的にチェック
            for i in range(item.childCount()):
                update_item_appearance(item.child(i))
        
        # ツリーの全アイテムをチェック
        top_level_count = self.tree_widget.topLevelItemCount()
        print(f"🌳 DEBUG: トップレベルアイテム数: {top_level_count}")
        
        for i in range(top_level_count):
            update_item_appearance(self.tree_widget.topLevelItem(i))
        
        print(f"🌳 DEBUG: ツリー更新完了 - {items_updated}件のアイテムを更新")
    
    def _get_record_jsonl_content(self, record: Dict[str, Any]) -> str:
        """レコードのJSONL内容を取得"""
        try:
            exporter = JSONLExporter()
            return exporter.preview_jsonl_record(record, "noise_removed")
        except:
            return ""
    
    def _clear_threshold_selection(self):
        """閾値選定を解除"""
        self.selected_records = []
        if hasattr(self, 'excluded_records'):
            self.excluded_records = []
        self.threshold_applied = False
        
        # ツリーの表示をリセット
        self._reset_tree_appearance()
        
        # ステータス更新
        self.selection_status.setText("選定解除")
        self.selection_status.setStyleSheet("color: #888; font-style: italic;")
        self.status_label.setText("選定解除済み")
    
    def _reset_tree_appearance(self):
        """ツリーの表示をリセット"""
        def reset_item(item):
            white_color = QColor(255, 255, 255)
            transparent_color = QColor(0, 0, 0, 0)
            
            item.setForeground(0, white_color)
            item.setForeground(1, white_color)
            item.setBackground(0, transparent_color)
            item.setBackground(1, transparent_color)
            item.setToolTip(0, "")
            
            for i in range(item.childCount()):
                reset_item(item.child(i))
        
        for i in range(self.tree_widget.topLevelItemCount()):
            reset_item(self.tree_widget.topLevelItem(i))
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """ツリーアイテムクリック（閾値除外判定対応）"""
        print(f"🖱️ DEBUG: ツリーアイテムクリック - {item.text(0)}")
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        print(f"🖱️ DEBUG: data type: {type(data)}")
        
        if data:
            print(f"🖱️ DEBUG: data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            
            # 閾値適用済みで除外されているかチェック
            is_excluded = False
            exclusion_reason = ""
            
            if self.threshold_applied and hasattr(self, 'excluded_records'):
                print(f"🖱️ DEBUG: 閾値適用済み - 除外レコード数: {len(self.excluded_records)}")
                
                # このアイテムのレコードが除外リストにあるかチェック
                item_records = []
                if isinstance(data, dict):
                    if "records" in data and data["records"]:
                        item_records = data["records"]
                    else:
                        # 単一レコードの場合
                        item_records = [data]
                
                print(f"🖱️ DEBUG: チェック対象レコード数: {len(item_records)}")
                
                # 除外レコードのFQNセットを作成
                excluded_fqns = {record.get("fqn", record.get("name", "")) for record in self.excluded_records}
                print(f"🖱️ DEBUG: 除外FQN例: {list(excluded_fqns)[:3]}")
                
                # このアイテムのレコードが除外リストに含まれているかチェック
                for record in item_records:
                    record_fqn = record.get("fqn", record.get("name", ""))
                    print(f"🖱️ DEBUG: レコードFQNチェック: {record_fqn}")
                    if record_fqn in excluded_fqns:
                        is_excluded = True
                        exclusion_reason = f"コンテンツ長が{self.content_length_threshold.value()}文字を超過"
                        print(f"🚫 DEBUG: 除外判定 - {record_fqn}")
                        break
            else:
                print(f"🖱️ DEBUG: 閾値未適用")
            
            # 除外フラグを追加してデータを更新
            display_data = data.copy() if isinstance(data, dict) else data
            if isinstance(display_data, dict):
                display_data["_ui_excluded"] = is_excluded
                if is_excluded:
                    display_data["_ui_exclusion_reason"] = exclusion_reason
                    print(f"🚫 DEBUG: 除外データ設定 - {exclusion_reason}")
            
            print(f"📋 DEBUG: 詳細タブに送信 - _ui_excluded: {display_data.get('_ui_excluded', False) if isinstance(display_data, dict) else False}")
            
            # 詳細タブに表示
            self.detail_tabs.update_content(display_data)
        else:
            print(f"⚠️ DEBUG: データなし")
    
    def _export_selected_jsonl(self):
        """選定されたレコードのみをJSONL出力"""
        if not self.selected_records:
            QMessageBox.warning(self, "警告", "選定されたデータがありません\n先に「選定実行」を行ってください")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "選定JSONL出力", "selected_modelica_data.jsonl", "JSONL Files (*.jsonl);;All Files (*)"
        )
        
        if file_path:
            try:
                exporter = JSONLExporter()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    for record in self.selected_records:
                        jsonl_line = exporter.preview_jsonl_record(record, "noise_removed")
                        f.write(jsonl_line + '\n')
                
                QMessageBox.information(
                    self, "出力完了", 
                    f"選定JSONL出力が完了しました\n"
                    f"ファイル: {file_path}\n"
                    f"レコード数: {len(self.selected_records)}"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "出力エラー", f"選定JSONL出力に失敗しました:\n{str(e)}")
    
    def _export_all_jsonl(self):
        """全データをJSONL出力（閾値選定結果を考慮）"""
        # 出力対象データを決定
        output_records = []
        output_description = ""
        
        if self.threshold_applied and self.selected_records:
            # 閾値選定が適用されている場合は選定レコードのみ
            output_records = self.selected_records
            excluded_count = len(getattr(self, 'excluded_records', []))
            output_description = f"選定データ（{len(output_records)}件、{excluded_count}件除外済み）"
        elif self.filtered_records:
            # 閾値選定が未適用の場合は全フィルタ済みデータ
            output_records = self.filtered_records
            output_description = f"全データ（{len(output_records)}件）"
        else:
            QMessageBox.warning(self, "警告", "出力するデータがありません")
            return
        
        print(f"📤 DEBUG: JSONL出力対象 - {output_description}")
        print(f"📤 DEBUG: threshold_applied: {self.threshold_applied}")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSONL出力", "modelica_data.jsonl", "JSONL Files (*.jsonl);;All Files (*)"
        )
        
        if file_path:
            try:
                exporter = JSONLExporter()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    for record in output_records:
                        jsonl_line = exporter.preview_jsonl_record(record, "noise_removed")
                        f.write(jsonl_line + '\n')
                
                success_message = f"""JSONL出力が完了しました

ファイル: {file_path}
出力内容: {output_description}
レコード数: {len(output_records)}

{f'除外されたレコード: {len(getattr(self, "excluded_records", []))}件' if self.threshold_applied else ''}"""
                
                QMessageBox.information(self, "出力完了", success_message)
                print(f"✅ JSONL出力完了: {len(output_records)}件")
                
            except Exception as e:
                QMessageBox.critical(self, "出力エラー", f"JSONL出力に失敗しました:\n{str(e)}")
                print(f"❌ JSONL出力エラー: {e}")
    
    def _show_statistics(self):
        """統計表示"""
        if not self.filtered_records:
            QMessageBox.information(self, "統計", "表示するデータがありません")
            return
        
        # 統計計算
        kind_counts = {}
        total_components = 0
        total_parameters = 0
        total_variables = 0
        
        for record in self.filtered_records:
            kind = record.get("kind", "unknown")
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            
            total_components += len(record.get("components", []))
            total_parameters += len(record.get("parameters", []))
            total_variables += len(record.get("variables", []))
        
        # 統計メッセージ
        msg_parts = [
            f"総レコード数: {len(self.filtered_records)}",
            f"総コンポーネント数: {total_components}",
            f"総パラメータ数: {total_parameters}",
            f"総変数数: {total_variables}",
            "",
            "種類別統計:"
        ]
        
        for kind, count in sorted(kind_counts.items()):
            msg_parts.append(f"  {kind}: {count}")
        
        QMessageBox.information(self, "統計情報", "\n".join(msg_parts))
