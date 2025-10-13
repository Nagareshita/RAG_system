# src/pdf/pymupdf4llm/processor.py (改善版)
import hashlib
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple
import traceback

import pymupdf4llm

from .models import ProcessedDocument, DocumentMetadata, ProcessingSettings
from .chunker import MarkdownChunker

class PyMuPDFProcessor:
    """PyMuPDF4LLM処理器（ページ番号対応版）"""
    
    def __init__(self, settings: ProcessingSettings = None):
        self.settings = settings or ProcessingSettings()
        self.chunker = MarkdownChunker(
            max_chunk_size=self.settings.chunk_size,
            overlap_size=self.settings.overlap_size
        )
    
    def process_pdf(self, pdf_path: str) -> ProcessedDocument:
        """PDF処理メイン（ページ番号トラッキング対応）"""
        print(f"🔄 PDF処理開始: {pdf_path}")
        
        try:
            # 1. Markdown変換（全ページ統合 + ページ境界情報）
            print("📄 Markdown変換中...")
            full_markdown, page_boundaries = self._convert_with_page_tracking(pdf_path)
            
            if not full_markdown or not full_markdown.strip():
                raise ValueError("PDFからテキストを抽出できませんでした")
            
            print(f"✅ Markdown変換完了: {len(full_markdown):,}文字")
            
            # 2. メタデータ作成
            print("📋 メタデータ作成中...")
            doc_metadata = self._create_metadata(pdf_path)
            
            # 3. チャンク分割（ページ境界情報を渡す）
            print("✂️ チャンク分割中...")
            chunks = self.chunker.chunk_markdown_with_page_boundaries(
                full_markdown, 
                page_boundaries,
                doc_metadata
            )
            
            if not chunks:
                print("⚠️ チャンクが生成されませんでした。フォールバック実行中...")
                chunks = self.chunker._create_fallback_chunk(full_markdown, doc_metadata)
            
            # 4. 統計計算
            print("📊 統計計算中...")
            stats = self._calculate_stats_safe(full_markdown, chunks)
            
            result = ProcessedDocument(
                document_metadata=doc_metadata,
                chunks=chunks,
                raw_markdown=full_markdown,
                processing_stats=stats
            )
            
            print(f"✅ PDF処理完了: {len(chunks)}個のチャンク生成")
            return result
            
        except Exception as e:
            print(f"❌ PDF処理エラー: {e}")
            print(f"📍 エラー詳細:\n{traceback.format_exc()}")
            return self._create_error_fallback(pdf_path, str(e))
    
    def _convert_with_page_tracking(self, pdf_path: str) -> tuple:
        """ページ番号をトラッキングしながらMarkdown変換
        
        Returns:
            tuple: (full_markdown, page_map)
                - full_markdown: 全ページ統合のMarkdown
                - page_map: 各行のページ番号マッピング
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 方式1: 全ページ一括変換でセクション構造を保持
            print("📄 全ページ一括Markdown変換中...")
            full_markdown = pymupdf4llm.to_markdown(
                pdf_path,
                page_chunks=False,
                write_images=False,
                margins=(10, 50, 10, 50),
                dpi=150
            )
            
            # 方式2: ページ別変換で各ページの文字数を取得
            print("📊 ページ境界を計算中...")
            page_boundaries = []
            cumulative_chars = 0
            
            for page_num in range(total_pages):
                try:
                    page_markdown = pymupdf4llm.to_markdown(
                        pdf_path,
                        pages=[page_num],
                        page_chunks=False,
                        write_images=False,
                        margins=(10, 50, 10, 50),
                        dpi=150
                    )
                    
                    page_char_count = len(page_markdown.strip())
                    page_boundaries.append({
                        'page_number': page_num + 1,
                        'start_char': cumulative_chars,
                        'end_char': cumulative_chars + page_char_count,
                        'char_count': page_char_count
                    })
                    cumulative_chars += page_char_count
                    
                except Exception as page_error:
                    print(f"⚠️ ページ {page_num + 1} スキップ: {page_error}")
                    continue
            
            doc.close()
            
            print(f"✅ 変換完了: {total_pages}ページ、{len(full_markdown):,}文字")
            return full_markdown, page_boundaries
            
        except Exception as e:
            print(f"❌ PDF変換失敗: {e}")
            # フォールバック: 一括変換のみ
            try:
                markdown = pymupdf4llm.to_markdown(pdf_path)
                return markdown, [{'page_number': 1, 'start_char': 0, 'end_char': len(markdown)}]
            except:
                raise ValueError(f"PDF変換完全失敗: {e}")
    
    def _create_metadata(self, pdf_path: str) -> DocumentMetadata:
        """メタデータ作成"""
        file_path = Path(pdf_path)
        
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        return DocumentMetadata(
            filename=file_path.name,
            file_path=str(file_path.absolute()),
            file_size=file_path.stat().st_size,
            source_hash=file_hash,
            document_type=self._detect_document_type(file_path.name)
        )
    
    def _detect_document_type(self, filename: str) -> str:
        """文書タイプ検出"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['manual', 'guide', 'handbook']):
            return "manual"
        elif any(word in filename_lower for word in ['paper', 'journal', 'conference']):
            return "technical_paper"
        elif any(word in filename_lower for word in ['api', 'reference', 'doc']):
            return "reference"
        elif 'modelica' in filename_lower:
            return "modelica_document"
        else:
            return "general"
    
    def _calculate_stats_safe(self, markdown_text: str, chunks) -> Dict:
        """統計計算（安全版）"""
        try:
            total_chunks = len(chunks) if chunks else 0
            total_chars = len(markdown_text) if markdown_text else 0
            
            if total_chunks > 0:
                avg_chunk_size = sum(c.chunk_metadata.char_count for c in chunks if c and hasattr(c, 'chunk_metadata')) / total_chunks
                chunk_types = self._count_chunk_types(chunks)
                formula_chunks = sum(1 for c in chunks if c and hasattr(c, 'chunk_metadata') and c.chunk_metadata.contains_formulas)
                table_chunks = sum(1 for c in chunks if c and hasattr(c, 'chunk_metadata') and c.chunk_metadata.contains_tables)
                code_chunks = sum(1 for c in chunks if c and hasattr(c, 'chunk_metadata') and c.chunk_metadata.contains_code)
            else:
                avg_chunk_size = 0
                chunk_types = {}
                formula_chunks = 0
                table_chunks = 0
                code_chunks = 0
            
            return {
                "total_chunks": total_chunks,
                "total_chars": total_chars,
                "avg_chunk_size": avg_chunk_size,
                "chunk_types": chunk_types,
                "formula_chunks": formula_chunks,
                "table_chunks": table_chunks,
                "code_chunks": code_chunks
            }
            
        except Exception as e:
            print(f"⚠️ 統計計算エラー: {e}")
            return {
                "total_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "chunk_types": {},
                "formula_chunks": 0,
                "table_chunks": 0,
                "code_chunks": 0,
                "error": str(e)
            }
    
    def _count_chunk_types(self, chunks) -> Dict[str, int]:
        """チャンクタイプ集計"""
        try:
            type_counts = {}
            for chunk in chunks:
                if chunk and hasattr(chunk, 'chunk_metadata'):
                    chunk_type = chunk.chunk_metadata.chunk_type
                    type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            return type_counts
        except Exception:
            return {}
    
    def _create_error_fallback(self, pdf_path: str, error_message: str) -> ProcessedDocument:
        """エラー時のフォールバック"""
        try:
            doc_metadata = self._create_metadata(pdf_path)
            doc_metadata.processor_version += " (ERROR_FALLBACK)"
            
            error_content = f"PDF処理中にエラーが発生しました。\n\nエラー内容: {error_message}\n\n対象ファイル: {pdf_path}"
            error_chunk = self.chunker._create_fallback_chunk(error_content, doc_metadata)
            
            return ProcessedDocument(
                document_metadata=doc_metadata,
                chunks=error_chunk,
                raw_markdown=error_content,
                processing_stats={"error": True, "error_message": error_message}
            )
        except Exception as e:
            print(f"❌ フォールバック作成も失敗: {e}")
            raise