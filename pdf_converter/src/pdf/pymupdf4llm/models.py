# src/pdf/pymupdf4llm/models.py (ページ番号対応版)
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
    """チャンクメタデータ（ページ番号対応版）"""
    section_title: str = ""
    section_level: int = 0
    chunk_index: int = 0
    chunk_type: str = "text"
    token_count: int = 0
    char_count: int = 0
    contains_formulas: bool = False
    contains_tables: bool = False
    contains_code: bool = False
    keywords: List[str] = field(default_factory=list)
    source_document: str = ""
    
    # ★ 新規追加: ページ番号情報
    page_number: int = 0  # チャンクが含まれるページ番号
    page_numbers: List[int] = field(default_factory=list)  # 複数ページにまたがる場合

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
    include_formulas: bool = True
    preserve_tables: bool = True
    extract_keywords: bool = True