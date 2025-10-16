# src/pdf/pymupdf4llm/chunker.py (修正版)
import re
from typing import List, Dict
from .llm_models import DocumentChunk, ChunkMetadata, DocumentMetadata

class MarkdownChunker:
    """Markdownチャンク分割器（エラーハンドリング強化版）"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 100, rag_emit_page: bool = True):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.rag_emit_page = rag_emit_page
        
        # Modelica特化キーワード
        self.modelica_keywords = [
            'modelica', 'component', 'connector', 'model', 'class', 'package',
            'equation', 'algorithm', 'function', 'parameter', 'variable',
            'extends', 'import', 'annotation', 'derivative', 'integral'
        ]
    
    def chunk_markdown(self, markdown_text: str, doc_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Markdownをチャンク分割（エラーハンドリング強化）"""
        try:
            if not markdown_text or not markdown_text.strip():
                print("⚠️ 警告: 空のMarkdownテキストです")
                return []
            
            sections = self._parse_sections(markdown_text)
            chunks = []
            
            for i, section in enumerate(sections):
                try:
                    section_chunks = self._split_section(section, doc_metadata, section_index=i)
                    chunks.extend(section_chunks)
                except Exception as e:
                    print(f"⚠️ セクション {i+1} の処理でエラー: {e}")
                    # エラーが発生したセクションをスキップして続行
                    continue
            
            print(f"✅ チャンク分割完了: {len(chunks)}個のチャンク生成")
            return chunks
            
        except Exception as e:
            print(f"❌ チャンク分割で重大エラー: {e}")
            # フォールバック：最低限のチャンクを作成
            return self._create_fallback_chunk(markdown_text, doc_metadata)
    
    def _create_fallback_chunk(self, text: str, doc_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """エラー時のフォールバックチャンク作成"""
        try:
            if not text or not text.strip():
                return []
            
            # 安全に単一チャンクを作成
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
                source_document=doc_metadata.filename
            )
            
            chunk = DocumentChunk(content=text[:self.max_chunk_size], chunk_metadata=metadata)
            return [chunk]
            
        except Exception as e:
            print(f"❌ フォールバック作成も失敗: {e}")
            return []
    
    def _parse_sections(self, text: str) -> List[Dict]:
        """セクション解析（エラーハンドリング強化）"""
        try:
            sections = []
            current_section = {"title": "", "content": "", "level": 0, "page": None}
            current_page = None
            
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                try:
                    if line.startswith('#'):
                        # 新しい見出し行を検出
                        level = len(line) - len(line.lstrip('#'))
                        title = line.lstrip('#').strip()

                        # ページ見出しかを判定
                        m = re.match(r"^\s*page\s+(\d+)\b", title, flags=re.IGNORECASE)
                        if m:
                            # 直前のセクションを確定（必要なら）
                            if current_section.get("title") or current_section["content"].strip():
                                sections.append(current_section.copy())

                            # 現在ページを更新
                            try:
                                current_page = int(m.group(1))
                            except Exception:
                                pass

                            # ページマーカーはチャンク化しない。以降の本文はページ番号のみ保持した無題セクションとして蓄積
                            current_section = {"title": "", "content": "", "level": 0, "page": current_page}
                        else:
                            # 直前のセクションを本文有無に関わらず確定（タイトルがあれば見出しのみでも保持）
                            if current_section.get("title") or current_section["content"].strip():
                                sections.append(current_section.copy())

                            # 通常の見出し開始
                            current_section = {
                                "title": title,
                                "content": "",
                                "level": level,
                                "page": current_page
                            }
                    else:
                        current_section["content"] += line + '\n'
                        
                except Exception as e:
                    print(f"⚠️ 行 {line_num+1} の処理でエラー: {e}")
                    continue
            
            # 最終セクションも確定（見出しのみでも保持）
            if current_section.get("title") or current_section["content"].strip():
                sections.append(current_section)
            
            return sections
            
        except Exception as e:
            print(f"❌ セクション解析エラー: {e}")
            # フォールバック：全テキストを単一セクションとして扱う
            return [{"title": "Document Content", "content": text, "level": 1}]
    
    def _split_section(self, section: Dict, doc_metadata: DocumentMetadata, section_index: int = 0) -> List[DocumentChunk]:
        """セクション内分割（安全版）"""
        try:
            raw_content = section.get("content", "").strip()
            title = (section.get("title") or "").strip()
            level = int(section.get("level") or 0)

            # 見出しを必ずコンテンツ先頭へプレフィックスして欠落を防止
            heading = ("#" * max(1, level) + f" {title}") if title else ""
            if heading:
                content = (heading + "\n\n" + raw_content).strip()
            else:
                content = raw_content
            # 見出しも本文も無ければスキップ
            if not content:
                return []
            
            chunks = []
            
            if len(content) <= self.max_chunk_size:
                chunk = self._create_chunk(content, section, doc_metadata, 0)
                if chunk:  # Noneチェック
                    chunks.append(chunk)
            else:
                # 段落分割での処理
                paragraphs = content.split('\n\n')
                current_chunk = ""
                chunk_index = 0
                
                for para_num, para in enumerate(paragraphs):
                    try:
                        if len(current_chunk + para) <= self.max_chunk_size:
                            current_chunk += para + '\n\n'
                        else:
                            if current_chunk:
                                chunk = self._create_chunk(current_chunk.strip(), section, doc_metadata, chunk_index)
                                if chunk:
                                    chunks.append(chunk)
                                chunk_index += 1
                            
                            current_chunk = para + '\n\n'
                    except Exception as e:
                        print(f"⚠️ セクション {section_index+1}, 段落 {para_num+1} でエラー: {e}")
                        continue
                
                if current_chunk:
                    chunk = self._create_chunk(current_chunk.strip(), section, doc_metadata, chunk_index)
                    if chunk:
                        chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ セクション分割エラー: {e}")
            return []
    
    def _create_chunk(self, content: str, section: Dict, doc_metadata: DocumentMetadata, chunk_index: int) -> DocumentChunk:
        """チャンク作成（安全版）"""
        try:
            if not content or not content.strip():
                return None
            
            # 特徴検出（安全版）
            contains_formulas = self._detect_formulas(content)
            contains_tables = self._detect_tables(content)
            contains_code = self._detect_code(content)
            
            # チャンクタイプ判定
            chunk_type = self._determine_chunk_type(contains_code, contains_formulas, contains_tables)
            
            # キーワード抽出（無効化: RAGメタ付与を廃止）
            keywords = []
            
            # トークンカウント（安全版）
            token_count = len(content.split()) if content else 0
            char_count = len(content) if content else 0
            
            # メタデータ作成
            metadata = ChunkMetadata(
                section_title=section.get("title", ""),
                section_level=section.get("level", 0),
                page=section.get("page"),
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                token_count=token_count,
                char_count=char_count,
                contains_formulas=contains_formulas,
                contains_tables=contains_tables,
                contains_code=contains_code,
                keywords=keywords,
                source_document=doc_metadata.filename
            )
            # RAGメタ付与（page/toc/sourceなど）は削除
            
            return DocumentChunk(content=content, chunk_metadata=metadata)
            
        except Exception as e:
            print(f"❌ チャンク作成エラー: {e}")
            return None
    
    def _detect_formulas(self, content: str) -> bool:
        try:
            flags = re.DOTALL
            formula_patterns = [
                r'\$\$.*?\$\$',          # $$ display math $$
                r'(?<!\\)\$.*?(?<!\\)\$',# inline $ ... $（エスケープ$は除外）
                r'\\\[.*?\\\]',          # \[ ... \]
                r'\\\((?:.|\n)*?\\\)',   # \( ... \)
                r'(?<!\w)(?:∫|∑|∂|√|≥|≤|±|≈|≠|∞|α|β|γ|δ|θ|λ|μ|π|σ|φ|ψ|ω)(?!\w)'
            ]
            return any(re.search(p, content, flags) for p in formula_patterns)
        except Exception:
            return False
    
    def _detect_tables(self, content: str) -> bool:
        """テーブル検出（安全版）"""
        try:
            return '|' in content and content.count('|') >= 6
        except Exception:
            return False
    
    def _detect_code(self, content: str) -> bool:
        """コード検出（安全版）"""
        try:
            return '```' in content or content.count('`') >= 4
        except Exception:
            return False
    
    def _determine_chunk_type(self, has_code: bool, has_formulas: bool, has_tables: bool) -> str:
        """チャンクタイプ判定"""
        if has_code:
            return "code"
        elif has_formulas:
            return "formula"
        elif has_tables:
            return "table"
        else:
            return "text"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（安全版）"""
        try:
            found_keywords = []
            content_lower = content.lower()
            
            # Modelicaキーワード
            for keyword in self.modelica_keywords:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            # 数学用語
            math_terms = ['equation', 'matrix', 'vector', 'differential', 'integral', 'derivative']
            for term in math_terms:
                if term in content_lower:
                    found_keywords.append(term)
            
            return list(set(found_keywords))
        except Exception:
            return []


