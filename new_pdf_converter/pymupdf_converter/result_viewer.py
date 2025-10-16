# src/apps/pymupdf_converter/ui/result_viewer.py
import json
from pathlib import Path
from typing import List, Dict

from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .llm_models import ProcessedDocument, DocumentChunk

class ChunkDetailViewer(QWidget):
    """チャンク詳細表示ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # チャンク一覧
        self.chunk_list = QTableWidget()
        self.chunk_list.setColumnCount(6)
        self.chunk_list.setHorizontalHeaderLabels([
            "ID", "セクション", "タイプ", "文字数", "キーワード", "数式"
        ])
        self.chunk_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chunk_list.itemSelectionChanged.connect(self._on_chunk_selected)
        
        layout.addWidget(QLabel("チャンク一覧:"))
        layout.addWidget(self.chunk_list)
        
        # チャンク詳細
        detail_group = QGroupBox("チャンク詳細")
        detail_layout = QVBoxLayout(detail_group)
        
        self.chunk_detail = QTextEdit()
        self.chunk_detail.setReadOnly(True)
        self.chunk_detail.setFont(QFont("Courier", 10))
        detail_layout.addWidget(self.chunk_detail)
        
        layout.addWidget(detail_group)
        
    def display_chunks(self, chunks: List[DocumentChunk]):
        """チャンク一覧表示"""
        self.chunks = chunks
        self.chunk_list.setRowCount(len(chunks))
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.chunk_metadata
            
            # テーブル項目作成
            id_item = QTableWidgetItem(chunk.chunk_id[:8] + "...")
            section_item = QTableWidgetItem(metadata.section_title or "N/A")
            type_item = QTableWidgetItem(metadata.chunk_type)
            char_item = QTableWidgetItem(str(metadata.char_count))
            keyword_item = QTableWidgetItem(", ".join(metadata.keywords[:3]))
            formula_item = QTableWidgetItem("はい" if metadata.contains_formulas else "いいえ")
            
            self.chunk_list.setItem(i, 0, id_item)
            self.chunk_list.setItem(i, 1, section_item)
            self.chunk_list.setItem(i, 2, type_item)
            self.chunk_list.setItem(i, 3, char_item)
            self.chunk_list.setItem(i, 4, keyword_item)
            self.chunk_list.setItem(i, 5, formula_item)
    
    def _on_chunk_selected(self):
        """チャンク選択時の詳細表示"""
        current_row = self.chunk_list.currentRow()
        if current_row >= 0 and current_row < len(self.chunks):
            chunk = self.chunks[current_row]
            
            detail_text = f"ID: {chunk.chunk_id}\n\n"
            detail_text += f"内容:\n{'-'*40}\n"
            detail_text += chunk.content
            detail_text += f"\n\nメタデータ:\n{'-'*40}\n"
            
            metadata = chunk.chunk_metadata
            detail_text += f"セクション: {metadata.section_title}\n"
            detail_text += f"セクションレベル: {metadata.section_level}\n"
            detail_text += f"チャンクタイプ: {metadata.chunk_type}\n"
            detail_text += f"文字数: {metadata.char_count}\n"
            detail_text += f"トークン数: {metadata.token_count}\n"
            detail_text += f"数式含有: {'はい' if metadata.contains_formulas else 'いいえ'}\n"
            detail_text += f"テーブル含有: {'はい' if metadata.contains_tables else 'いいえ'}\n"
            detail_text += f"コード含有: {'はい' if metadata.contains_code else 'いいえ'}\n"
            detail_text += f"キーワード: {', '.join(metadata.keywords)}\n"
            
            self.chunk_detail.setPlainText(detail_text)

class StatisticsViewer(QWidget):
    """統計表示ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 基本統計
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        
        layout.addWidget(QLabel("処理統計:"))
        layout.addWidget(self.stats_text)
        
        # チャンクタイプ分布
        self.type_distribution_table = QTableWidget()
        self.type_distribution_table.setColumnCount(3)
        self.type_distribution_table.setHorizontalHeaderLabels(["チャンクタイプ", "件数", "割合"])
        self.type_distribution_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("📋 チャンクタイプ分布:"))
        layout.addWidget(self.type_distribution_table)
        
    def display_statistics(self, result: ProcessedDocument):
        """統計表示"""
        stats = result.processing_stats
        doc_meta = result.document_metadata
        
        # 基本統計テキスト
        stats_text = f"ファイル名: {doc_meta.filename}\n"
        stats_text += f"ファイルサイズ: {doc_meta.file_size:,} bytes\n"
        stats_text += f"処理日時: {doc_meta.processed_at}\n"
        stats_text += f"文書タイプ: {doc_meta.document_type}\n"
        stats_text += f"プロセッサ: {doc_meta.processor_version}\n\n"
        stats_text += f"総文字数: {stats['total_chars']:,}\n"
        stats_text += f"総チャンク数: {stats['total_chunks']}\n"
        stats_text += f"平均チャンクサイズ: {stats['avg_chunk_size']:.0f}文字\n"
        stats_text += f"数式チャンク: {stats['formula_chunks']}\n"
        stats_text += f"テーブルチャンク: {stats['table_chunks']}\n"
        stats_text += f"コードチャンク: {stats['code_chunks']}"
        
        self.stats_text.setPlainText(stats_text)
        
        # チャンクタイプ分布テーブル
        type_counts = stats['chunk_types']
        total_chunks = stats['total_chunks']
        
        self.type_distribution_table.setRowCount(len(type_counts))
        for i, (chunk_type, count) in enumerate(type_counts.items()):
            percentage = (count / total_chunks * 100) if total_chunks > 0 else 0
            
            self.type_distribution_table.setItem(i, 0, QTableWidgetItem(chunk_type))
            self.type_distribution_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.type_distribution_table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))

class PreviewViewer(QWidget):
    """プレビュー表示ウィジェット"""
    
    def __init__(self, title: str, read_only: bool = True):
        super().__init__()
        self.title = title
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(self.title))
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Courier", 9))
        
        layout.addWidget(self.text_display)
        
    def set_content(self, content: str):
        """コンテンツ設定"""
        self.text_display.setPlainText(content)

class ResultViewer(QTabWidget):
    """結果表示ウィジェット"""
    
    save_requested = Signal(str, str)  # save_type, file_path
    
    def __init__(self):
        super().__init__()
        self.current_result = None
        self._setup_ui()
        
    def _setup_ui(self):
        """UI構築"""
        # 統計情報タブ
        self.stats_viewer = StatisticsViewer()
        self.addTab(self.stats_viewer, "統計")
        
        # チャンク表示タブ  
        self.chunk_viewer = ChunkDetailViewer()
        self.addTab(self.chunk_viewer, "チャンク")
        
        # Markdownプレビュータブ
        self.markdown_viewer = PreviewViewer("元のMarkdown:")
        self.addTab(self.markdown_viewer, "Markdown")
        
        # JSONプレビュータブ
        self.json_viewer = PreviewViewer("生成されたJSON:")
        self.addTab(self.json_viewer, "JSON")
        
        # 保存タブ
        save_tab = self._create_save_tab()
        self.addTab(save_tab, "保存")
    
    def _create_save_tab(self):
        """保存タブ作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 説明
        info_label = QLabel(
            "処理結果を保存できます。\n\n"
            "- JSON: ベクトル化に適した構造化データ\n"
            "- Markdown: 変換結果テキスト"
        )
        layout.addWidget(info_label)
        
        # 保存ボタン
        save_group = QGroupBox("ファイル保存")
        save_layout = QVBoxLayout(save_group)

        self.save_json_btn = QPushButton("JSON形式で保存")
        self.save_json_btn.setEnabled(False)
        self.save_json_btn.clicked.connect(self._save_json)

        self.save_markdown_btn = QPushButton("Markdown形式で保存")
        self.save_markdown_btn.setEnabled(False)
        self.save_markdown_btn.clicked.connect(self._save_markdown)

        # 横方向にコンパクト配置
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.save_json_btn)
        btn_row.addWidget(self.save_markdown_btn)
        btn_row.addStretch(1)
        save_layout.addLayout(btn_row)
        
        layout.addWidget(save_group)
        layout.addStretch()
        
        return widget
    
    def display_results(self, result: ProcessedDocument):
        """結果表示"""
        self.current_result = result
        
        # 各タブに結果表示
        self.stats_viewer.display_statistics(result)
        self.chunk_viewer.display_chunks(result.chunks)
        self.markdown_viewer.set_content(result.raw_markdown)
        
        # JSON表示（整形済み）
        json_data = {
            "document_metadata": result.document_metadata.__dict__,
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "chunk_metadata": chunk.chunk_metadata.__dict__
                }
                for chunk in result.chunks
            ],
            "processing_stats": result.processing_stats
        }
        json_text = json.dumps(json_data, ensure_ascii=False, indent=2)
        self.json_viewer.set_content(json_text)
        
        # 保存ボタン有効化
        self.save_json_btn.setEnabled(True)
        self.save_markdown_btn.setEnabled(True)
    
    def _save_json(self):
        """JSON保存"""
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSON保存", 
            f"{Path(self.current_result.document_metadata.filename).stem}_vectorized.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.save_requested.emit("json", file_path)
    
    def _save_markdown(self):
        """Markdown保存"""
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Markdown保存",
            f"{Path(self.current_result.document_metadata.filename).stem}_original.md", 
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            self.save_requested.emit("markdown", file_path)
