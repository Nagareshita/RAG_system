# src/pdf/pymupdf4llm/models.py
"""Local datamodels for PyMuPDF4LLM (flattened)."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

@dataclass
class DocumentMetadata:
    """文書メタデータ"""
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_hash: str = ""
    processor_version: str = "pymupdf4llm_v1.0"
    document_type: str = "general"
    language: str = "en"

@dataclass
class ChunkMetadata:
    """チャンクメタデータ"""
    section_title: str = ""
    section_level: int = 0
    # 追加: ページ番号（contentに混在させず、明示フィールドに格納）
    page: Optional[int] = None
    chunk_index: int = 0
    chunk_type: str = "text"  # text, formula, table, code
    token_count: int = 0
    char_count: int = 0
    contains_formulas: bool = False
    contains_tables: bool = False
    contains_code: bool = False
    keywords: List[str] = field(default_factory=list)
    source_document: str = ""

@dataclass
class DocumentChunk:
    """文書チャンク"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    chunk_metadata: ChunkMetadata = field(default_factory=ChunkMetadata)

@dataclass
class ProcessedDocument:
    """処理済み文書"""
    document_metadata: DocumentMetadata
    chunks: List[DocumentChunk]
    raw_markdown: str = ""
    processing_stats: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingSettings:
    """処理設定"""
    chunk_size: int = 1000
    overlap_size: int = 100
    preserve_tables: bool = True
    extract_keywords: bool = True
    # 追加: PyMuPDF4LLMへの引数 / RAGメタ設定
    pymupdf_kwargs: dict = field(default_factory=dict)
    rag_settings: dict = field(default_factory=dict)
    # 追加: 画像キャプション自動生成（write_imagesが有効時のみ）
    generate_captions: bool = False
