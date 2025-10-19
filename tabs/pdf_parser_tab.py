# tabs/pdf_parser_tab.py
"""
PDF解析タブ
pdf_converterフォルダのロジックを移植
"""

import sys
from pathlib import Path

# new_pdf_converter の依存関係をパスに追加
project_root = Path(__file__).resolve().parent.parent
new_pdf_converter_path = project_root / "new_pdf_converter"
sys.path.insert(0, str(new_pdf_converter_path))

import json
from PySide6.QtWidgets import QWidget, QHBoxLayout, QMessageBox, QSplitter
from PySide6.QtCore import QThread, Signal, Qt

from pymupdf_converter.llm_models import ProcessedDocument
from pymupdf_converter.control_panel import ControlPanel
from pymupdf_converter.result_viewer import ResultViewer

class PDFParserTab(QWidget):
    """PDF解析タブ"""
    
    def __init__(self):
        super().__init__()
        self.current_result = None
        self.worker = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI構築"""
        layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # コントロールパネル
        self.control_panel = ControlPanel()
        splitter.addWidget(self.control_panel)

        # 結果ビューアー
        self.result_viewer = ResultViewer()
        splitter.addWidget(self.result_viewer)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
    
    def _connect_signals(self):
        """シグナル接続"""
        self.control_panel.processing_requested.connect(self._start_processing)
        self.result_viewer.save_requested.connect(self._save_results)
    
    def _start_processing(self, settings: dict):
        """処理開始"""
        self.control_panel.set_processing_state(True)
        
        # ワーカー開始
        # 重い依存関係（pymupdf4llm / torch / transformers など）を
        # アプリ起動時ではなく実行時に読み込むため、ここで遅延インポートする
        from pymupdf_converter.pdf_processor import PDFProcessorWorker
        self.worker = PDFProcessorWorker(settings)
        self.worker.progress_updated.connect(self.control_panel.update_status)
        self.worker.processing_completed.connect(self._on_processing_completed)
        self.worker.error_occurred.connect(self._on_error_occurred)
        # VLM進捗を結果ビューへ反映
        try:
            self.worker.vlm_progress.connect(self._on_vlm_progress)
        except Exception:
            pass
        self.worker.start()

    def _on_vlm_progress(self, ev: dict):
        try:
            # キャプション開始のタイミングで自動的にVLMプログレスタブへ切り替え
            if ev.get('stage') == 'caption_start':
                if hasattr(self.result_viewer, 'focus_vlm_tab'):
                    self.result_viewer.focus_vlm_tab()
        except Exception:
            pass
        # 逐次行追加
        try:
            self.result_viewer.append_vlm_event(ev)
        except Exception:
            pass
    
    def _on_processing_completed(self, result: ProcessedDocument):
        """処理完了"""
        self.current_result = result
        
        self.control_panel.set_processing_state(False)
        self.control_panel.update_status("✅ 処理完了")
        
        self.result_viewer.display_results(result)
        
        QMessageBox.information(
            self, "処理完了",
            f"変換が完了しました！\n\n"
            f"総チャンク数: {result.processing_stats['total_chunks']}\n"
            f"平均チャンクサイズ: {result.processing_stats['avg_chunk_size']:.0f}文字"
        )
    
    def _on_error_occurred(self, error_message: str):
        """エラー発生"""
        self.control_panel.set_processing_state(False)
        self.control_panel.update_status("❌ エラー発生")
        
        QMessageBox.critical(self, "処理エラー", error_message)
    
    def _save_results(self, save_type: str, file_path: str):
        """結果保存"""
        if not self.current_result:
            return
        
        try:
            if save_type == "json":
                # ProcessedDocumentをdict変換
                data = {
                    "document_metadata": self.current_result.document_metadata.__dict__,
                    "chunks": [
                        {
                            "chunk_id": chunk.chunk_id,
                            "content": chunk.content,
                            "chunk_metadata": chunk.chunk_metadata.__dict__
                        }
                        for chunk in self.current_result.chunks
                    ],
                    "processing_stats": self.current_result.processing_stats
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
            elif save_type == "markdown":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_result.raw_markdown)
            
            QMessageBox.information(self, "保存完了", f"ファイルを保存しました:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "保存エラー", f"保存に失敗しました:\n{e}")
    
    def closeEvent(self, event):
        """タブ終了時のクリーンアップ"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)
        event.accept()
