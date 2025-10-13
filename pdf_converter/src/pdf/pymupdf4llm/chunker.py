# src/pdf/pymupdf4llm/chunker.py (ページ番号対応版)
import re
from typing import List, Dict
from .models import DocumentChunk, ChunkMetadata, DocumentMetadata

class MarkdownChunker:
    """Markdownチャンク分割器（ページ番号トラッキング対応版）"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        
        self.modelica_keywords = [
            'modelica', 'component', 'connector', 'model', 'class', 'package',
            'equation', 'algorithm', 'function', 'parameter', 'variable',
            'extends', 'import', 'annotation', 'derivative', 'integral'
        ]
    
    def chunk_markdown_with_page_boundaries(self, full_markdown: str, page_boundaries: List[Dict], 
                                             doc_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """ページ境界情報を使用したMarkdownチャンク分割
        
        Args:
            full_markdown: 全ページ統合のMarkdownテキスト
            page_boundaries: ページ境界情報のリスト
            doc_metadata: ドキュメントメタデータ
        """
        try:
            chunks = []
            
            # セクション解析（全文書から）
            sections = self._parse_sections(full_markdown)
            
            for i, section in enumerate(sections):
                try:
                    section_chunks = self._split_section_with_page_detection(
                        section, 
                        doc_metadata,
                        page_boundaries,
                        section_index=i
                    )
                    chunks.extend(section_chunks)
                except Exception as e:
                    print(f"⚠️ セクション{i+1} 処理エラー: {e}")
                    continue
            
            print(f"✅ チャンク分割完了: {len(chunks)}個のチャンク生成")
            return chunks
            
        except Exception as e:
            print(f"❌ チャンク分割で重大エラー: {e}")
            return self._create_fallback_chunk(full_markdown, doc_metadata)
    
    def _detect_page_number(self, char_position: int, page_boundaries: List[Dict]) -> int:
        """文字位置からページ番号を検出"""
        for boundary in page_boundaries:
            if boundary['start_char'] <= char_position < boundary['end_char']:
                return boundary['page_number']
        # デフォルト: 最後のページ
        return page_boundaries[-1]['page_number'] if page_boundaries else 1
    
    def _split_section_with_page_detection(self, section: Dict, doc_metadata: DocumentMetadata,
                                           page_boundaries: List[Dict], section_index: int = 0) -> List[DocumentChunk]:
        """ページ検出機能付きセクション分割"""
        try:
            content = section.get("content", "").strip()
            if not content:
                return []
            
            chunks = []
            
            # セクション開始位置を推定（簡易版）
            section_start_pos = 0  # 実際には全Markdown内の位置を計算すべき
            
            if len(content) <= self.max_chunk_size:
                page_num = self._detect_page_number(section_start_pos, page_boundaries)
                chunk = self._create_chunk_with_page(
                    content, section, doc_metadata, page_num, 0
                )
                if chunk:
                    chunks.append(chunk)
            else:
                paragraphs = content.split('\n\n')
                current_chunk = ""
                chunk_index = 0
                current_pos = section_start_pos
                
                for para in paragraphs:
                    if len(current_chunk + para) <= self.max_chunk_size:
                        current_chunk += para + '\n\n'
                    else:
                        if current_chunk:
                            page_num = self._detect_page_number(current_pos, page_boundaries)
                            chunk = self._create_chunk_with_page(
                                current_chunk.strip(), 
                                section, 
                                doc_metadata, 
                                page_num,
                                chunk_index
                            )
                            if chunk:
                                chunks.append(chunk)
                            chunk_index += 1
                        
                        current_chunk = para + '\n\n'
                    current_pos += len(para) + 2  # +2 for \n\n
                
                if current_chunk:
                    page_num = self._detect_page_number(current_pos, page_boundaries)
                    chunk = self._create_chunk_with_page(
                        current_chunk.strip(), 
                        section, 
                        doc_metadata, 
                        page_num,
                        chunk_index
                    )
                    if chunk:
                        chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ セクション分割エラー: {e}")
            return []
    
    def _create_chunk_with_page(self, content: str, section: Dict, 
                                 doc_metadata: DocumentMetadata, 
                                 page_number: int, chunk_index: int) -> DocumentChunk:
        """ページ番号付きチャンク作成"""
        try:
            if not content or not content.strip():
                return None
            
            contains_formulas = self._detect_formulas(content)
            contains_tables = self._detect_tables(content)
            contains_code = self._detect_code(content)
            chunk_type = self._determine_chunk_type(contains_code, contains_formulas, contains_tables)
            keywords = self._extract_keywords(content)
            
            token_count = len(content.split()) if content else 0
            char_count = len(content) if content else 0
            
            metadata = ChunkMetadata(
                section_title=section.get("title", ""),
                section_level=section.get("level", 0),
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                token_count=token_count,
                char_count=char_count,
                contains_formulas=contains_formulas,
                contains_tables=contains_tables,
                contains_code=contains_code,
                keywords=keywords,
                source_document=doc_metadata.filename,
                # ★ ページ番号設定
                page_number=page_number,
                page_numbers=[page_number]
            )
            
            return DocumentChunk(content=content, chunk_metadata=metadata)
            
        except Exception as e:
            print(f"❌ チャンク作成エラー: {e}")
            return None
    
    # 以下、既存メソッド（変更なし）
    
    def _parse_sections(self, text: str) -> List[Dict]:
        """セクション解析"""
        try:
            sections = []
            current_section = {"title": "", "content": "", "level": 0}
            
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                try:
                    if line.startswith('#'):
                        if current_section["content"].strip():
                            sections.append(current_section.copy())
                        
                        level = len(line) - len(line.lstrip('#'))
                        title = line.lstrip('#').strip()
                        current_section = {
                            "title": title,
                            "content": "",
                            "level": level
                        }
                    else:
                        current_section["content"] += line + '\n'
                        
                except Exception as e:
                    print(f"⚠️ 行 {line_num+1} の処理でエラー: {e}")
                    continue
            
            if current_section["content"].strip():
                sections.append(current_section)
            
            return sections
            
        except Exception as e:
            print(f"❌ セクション解析エラー: {e}")
            return [{"title": "Document Content", "content": text, "level": 1}]
    
    def _detect_formulas(self, content: str) -> bool:
        try:
            formula_patterns = [
                r'\$\$.*?\$\$',
                r'(?<!\\)\$.*?(?<!\\)\$',
                r'\\\[.*?\\\]',
                r'\\\((?:.|\n)*?\\\)',
                r'(?<!\w)(?:∫|∑|∂|√|≥|≤|±|≈|≠|∞|α|β|γ|δ|θ|λ|μ|π|σ|φ|ψ|ω)(?!\w)'
            ]
            return any(re.search(p, content, re.DOTALL) for p in formula_patterns)
        except Exception:
            return False
    
    def _detect_tables(self, content: str) -> bool:
        try:
            return '|' in content and content.count('|') >= 6
        except Exception:
            return False
    
    def _detect_code(self, content: str) -> bool:
        try:
            return '```' in content or content.count('`') >= 4
        except Exception:
            return False
    
    def _determine_chunk_type(self, has_code: bool, has_formulas: bool, has_tables: bool) -> str:
        if has_code:
            return "code"
        elif has_formulas:
            return "formula"
        elif has_tables:
            return "table"
        else:
            return "text"
    
    def _extract_keywords(self, content: str) -> List[str]:
        try:
            found_keywords = []
            content_lower = content.lower()
            
            for keyword in self.modelica_keywords:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            math_terms = ['equation', 'matrix', 'vector', 'differential', 'integral', 'derivative']
            for term in math_terms:
                if term in content_lower:
                    found_keywords.append(term)
            
            return list(set(found_keywords))
        except Exception:
            return []
    
    def _create_fallback_chunk(self, text: str, doc_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """フォールバックチャンク作成"""
        try:
            if not text or not text.strip():
                return []
            
            metadata = ChunkMetadata(
                section_title="Fallback Content",
                section_level=1,
                chunk_index=0,
                chunk_type="text",
                token_count=len(text.split()),
                char_count=len(text),
                contains_formulas=False,
                contains_tables=False,
                contains_code=False,
                keywords=[],
                source_document=doc_metadata.filename,
                page_number=1,
                page_numbers=[1]
            )
            
            chunk = DocumentChunk(content=text[:self.max_chunk_size], chunk_metadata=metadata)
            return [chunk]
            
        except Exception as e:
            print(f"❌ フォールバック作成も失敗: {e}")
            return []