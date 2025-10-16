# src/apps/pymupdf_converter/main_app.py (修正版)
import sys
import json
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QMessageBox, QSplitter
from PySide6.QtCore import QThread, Signal, Qt

from .llm_models import ProcessedDocument
from .control_panel import ControlPanel
from .result_viewer import ResultViewer
from .pdf_processor import PDFProcessorWorker

class PyMuPDFConverterApp(QMainWindow):
    """メインアプリケーション"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📄 PDF to JSON Converter (PyMuPDF4LLM)")
        self.setMinimumSize(1400, 900)
        
        self.current_result = None
        self.worker = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI構築"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # スプリッター（左: 設定 / 右: 結果）
        splitter = QSplitter(Qt.Horizontal)

        # コントロールパネル
        self.control_panel = ControlPanel()
        self.control_panel.setMinimumWidth(480)
        splitter.addWidget(self.control_panel)

        # 結果ビューアー
        self.result_viewer = ResultViewer()
        splitter.addWidget(self.result_viewer)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setHandleWidth(8)
        splitter.setSizes([600, 900])

        layout.addWidget(splitter)
    
    def _connect_signals(self):
        """シグナル接続"""
        self.control_panel.processing_requested.connect(self._start_processing)
        self.result_viewer.save_requested.connect(self._save_results)
    
    def _start_processing(self, settings: dict):
        """処理開始"""
        self.control_panel.set_processing_state(True)
        
        # ワーカー開始
        self.worker = PDFProcessorWorker(settings)
        self.worker.progress_updated.connect(self.control_panel.update_status)
        self.worker.processing_completed.connect(self._on_processing_completed)
        self.worker.error_occurred.connect(self._on_error_occurred)
        self.worker.start()
    
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
        """アプリ終了時のクリーンアップ"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)
        event.accept()

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    app.setApplicationName("PDF to JSON Converter")
    app.setApplicationVersion("1.0")
    
    window = PyMuPDFConverterApp()
    window.show()
    
    print("🚀 PDF to JSON Converter 起動")
    print("=" * 50)
    print("📄 PyMuPDF4LLM → 構造化JSON変換")
    print("🎯 ベクトル化に最適化されたチャンク分割")
    print("💡 Modelica文書対応")
    print("=" * 50)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
