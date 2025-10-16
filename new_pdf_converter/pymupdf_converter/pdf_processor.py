# src/apps/pymupdf_converter/workers/pdf_processor.py (修正版)
from PySide6.QtCore import QThread, Signal
import traceback

from .llm_processor import PyMuPDFProcessor
from .llm_models import ProcessingSettings, ProcessedDocument

class PDFProcessorWorker(QThread):
    """PDF処理ワーカースレッド（エラーハンドリング強化版）"""
    
    progress_updated = Signal(str)
    processing_completed = Signal(ProcessedDocument)
    error_occurred = Signal(str)
    
    def __init__(self, settings: dict):
        super().__init__()
        self.pdf_path = settings['pdf_path']
        self.processing_settings = ProcessingSettings(
            chunk_size=settings.get('chunk_size', 1000),
            overlap_size=settings.get('overlap_size', 100),
            pymupdf_kwargs=settings.get('pymupdf_kwargs', {}),
            rag_settings=settings.get('rag_settings', {}),
        )
        
    def run(self):
        """ワーカー実行（詳細ログ付き）"""
        try:
            self.progress_updated.emit("PDFを読み込み中...")
            
            # プロセッサ初期化
            processor = PyMuPDFProcessor(self.processing_settings)
            
            self.progress_updated.emit("Markdownに変換中...")
            
            # PDF処理実行
            result = processor.process_pdf(self.pdf_path)
            
            # エラーチェック
            if hasattr(result, 'processing_stats') and result.processing_stats.get('error'):
                error_msg = result.processing_stats.get('error_message', 'Unknown error')
                self.error_occurred.emit(f"処理エラー: {error_msg}")
                return
            
            self.progress_updated.emit("処理完了")
            self.processing_completed.emit(result)
            
        except Exception as e:
            error_detail = f"処理エラー: {str(e)}\n\n詳細:\n{traceback.format_exc()}"
            self.error_occurred.emit(error_detail)
