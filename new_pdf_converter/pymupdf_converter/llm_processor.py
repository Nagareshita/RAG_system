# src/pdf/pymupdf4llm/processor.py (修正版)
import hashlib
from pathlib import Path
from typing import Dict
import traceback

import pymupdf4llm

from .llm_models import ProcessedDocument, DocumentMetadata, ProcessingSettings
from .llm_chunker import MarkdownChunker

class PyMuPDFProcessor:
    """PyMuPDF4LLM処理器（エラーハンドリング強化版）"""
    
    def __init__(self, settings: ProcessingSettings = None):
        self.settings = settings or ProcessingSettings()
        self.chunker = MarkdownChunker(
            max_chunk_size=self.settings.chunk_size,
            overlap_size=self.settings.overlap_size,
            rag_emit_page=(self.settings.rag_settings or {}).get("emit_page_number", True)
        )
    
    def process_pdf(self, pdf_path: str) -> ProcessedDocument:
        """PDF処理メイン（エラーハンドリング強化）"""
        print(f"🔄 PDF処理開始: {pdf_path}")
        
        try:
            # 1. Markdown変換（プログレス表示付き）
            print("📄 Markdown変換中...")
            markdown_text = self._safe_markdown_conversion(pdf_path)
            
            if not markdown_text or not markdown_text.strip():
                raise ValueError("PDFからテキストを抽出できませんでした")
            
            print(f"✅ Markdown変換完了: {len(markdown_text):,}文字")
            
            # 2. メタデータ作成
            print("📋 メタデータ作成中...")
            doc_metadata = self._create_metadata(pdf_path)
            
            # 3. チャンク分割（安全実行）
            print("✂️ チャンク分割中...")
            chunks = self.chunker.chunk_markdown(markdown_text, doc_metadata)

            if not chunks:
                print("⚠️ チャンクが生成されませんでした。フォールバック実行中...")
                chunks = self.chunker._create_fallback_chunk(markdown_text, doc_metadata)

            # 3.5 RAGメタ設定の反映（軽量）
            self._apply_rag_metadata(chunks, doc_metadata)
            
            # 4. 統計計算（安全版）
            print("📊 統計計算中...")
            stats = self._calculate_stats_safe(markdown_text, chunks)
            
            result = ProcessedDocument(
                document_metadata=doc_metadata,
                chunks=chunks,
                raw_markdown=markdown_text,
                processing_stats=stats
            )
            
            print(f"✅ PDF処理完了: {len(chunks)}個のチャンク生成")
            return result
            
        except Exception as e:
            print(f"❌ PDF処理エラー: {e}")
            print(f"📍 エラー詳細:\n{traceback.format_exc()}")
            
            # エラー時のフォールバック処理
            return self._create_error_fallback(pdf_path, str(e))
    
    def _safe_markdown_conversion(self, pdf_path: str) -> str:
        """安全なMarkdown変換"""
        try:
            # バージョン情報（デバッグ）
            try:
                import importlib.metadata as _md
                _ver_pymupdf4llm = _md.version("pymupdf4llm")
            except Exception:
                _ver_pymupdf4llm = "unknown"
            try:
                import fitz as _fz
                _ver_pymupdf = getattr(_fz, "__doc__", "").split("PyMuPDF")[-1].strip() or "unknown"
            except Exception:
                _ver_pymupdf = "unknown"
            print(f"🧩 pymupdf4llm={_ver_pymupdf4llm}, pymupdf={_ver_pymupdf}")

            raw_kwargs = dict(self.settings.pymupdf_kwargs or {})
            print("🔧 PyMuPDF4LLM kwargs (raw):", raw_kwargs)

            # スキーマベースのkwargsを適用（未対応キーは除外）
            kwargs = self._filter_supported_kwargs(raw_kwargs)
            print("✅ PyMuPDF4LLM kwargs (effective):", kwargs)

            result = pymupdf4llm.to_markdown(pdf_path, **kwargs)
            # デバッグ: page_chunksの有効性
            requested_page_chunks = bool(kwargs.get("page_chunks"))
            if isinstance(result, list):
                print(f"🧪 to_markdown returned list (pages) — count={len(result)}; page_chunks requested={requested_page_chunks}")
                # 追加デバッグ: ページ配列の要素構造を確認
                self._debug_inspect_page_chunks(result)
            else:
                print(f"🧪 to_markdown returned str — length={len(result) if isinstance(result, str) else 'n/a'}; page_chunks requested={requested_page_chunks}")
                if requested_page_chunks:
                    print("⚠️ page_chunks=True が要求されましたが、戻り値は文字列でした。ライブラリの仕様/バージョン差異の可能性。")
            # page_chunks=True の場合はリストが返る可能性があるので統一
            return self._normalize_markdown_result(result)
            
        except Exception as first_error:
            print(f"⚠️ 標準変換失敗: {first_error}")
            
            try:
                # ページ指定で少しずつ処理
                print("🔄 ページ別変換を試行中...")
                import fitz
                doc = fitz.open(pdf_path)
                total_pages = len(doc)
                
                markdown_parts = []
                
                for page_num in range(total_pages):
                    try:
                        print(f"📄 ページ {page_num + 1}/{total_pages} 処理中...")
                        kwargs = self._filter_supported_kwargs(self.settings.pymupdf_kwargs or {})
                        # 個別ページ処理
                        page_md = pymupdf4llm.to_markdown(pdf_path, pages=[page_num], **kwargs)
                        if isinstance(page_md, list):
                            print(f"🧪 page {page_num+1}: list returned (len={len(page_md)})")
                            self._debug_inspect_page_chunks(page_md, label=f"page {page_num+1}")
                        elif isinstance(page_md, str):
                            print(f"🧪 page {page_num+1}: str returned (len={len(page_md)})")
                        page_text = self._normalize_markdown_result(page_md, page_number=page_num+1)
                        if page_text and page_text.strip():
                            markdown_parts.append(page_text)
                    except Exception as page_error:
                        print(f"⚠️ ページ {page_num + 1} スキップ: {page_error}")
                        continue
                
                doc.close()
                
                if markdown_parts:
                    result = "\n\n---\n\n".join(markdown_parts)
                    print(f"✅ ページ別変換完了: {len(markdown_parts)}ページ処理")
                    return result
                else:
                    raise ValueError("全ページの変換に失敗しました")
                    
            except Exception as second_error:
                print(f"❌ ページ別変換も失敗: {second_error}")
                raise ValueError(f"PDF変換失敗: {first_error}")

    def _filter_supported_kwargs(self, kwargs: dict) -> dict:
        """to_markdownのシグネチャから受理される引数だけを抽出"""
        try:
            import inspect
            sig = inspect.signature(pymupdf4llm.to_markdown)
            accepted = set(sig.parameters.keys())
            provided = set((kwargs or {}).keys())
            rejected = sorted(provided - accepted)
            if rejected:
                print("⚠️ 未対応のpymupdf4llm引数を除外:", ", ".join(rejected))
            filtered = {k: v for k, v in (kwargs or {}).items() if k in accepted}
            # marginsの型を強制（float or 長さ1/2/4のtuple[float]）
            if "margins" in filtered:
                ok, coerced = self._coerce_margins(filtered.get("margins"))
                if ok:
                    filtered["margins"] = coerced
                else:
                    print("⚠️ margins を無効化（形式不正）:", filtered.get("margins"))
                    filtered.pop("margins", None)
            return filtered
        except Exception:
            # 失敗時はそのまま返す（下流でTypeErrorが出た場合は上位で処理）
            return dict(kwargs or {})

    def _coerce_margins(self, val):
        """marginsを to_markdown が期待する形式へ矯正"""
        try:
            # 単一数値
            if isinstance(val, (int, float)):
                return True, float(val)
            # 文字列（例: "20,15"）
            if isinstance(val, str):
                parts = [p.strip() for p in val.split(',') if p.strip()]
                if len(parts) == 1:
                    return True, float(parts[0])
                if len(parts) in (2, 4):
                    return True, tuple(float(x) for x in parts)
                return False, None
            # 配列/タプル
            if isinstance(val, (list, tuple)):
                if len(val) == 1:
                    return True, float(val[0])
                if len(val) in (2, 4):
                    return True, tuple(float(x) for x in val)
                return False, None
            return False, None
        except Exception:
            return False, None

    def _normalize_markdown_result(self, result, page_number: int = None) -> str:
        """pymupdf4llmの戻り値（文字列 or ページ辞書リスト）をMarkdown文字列に正規化"""
        try:
            if isinstance(result, str):
                return result
            # 期待構造: list[dict] で各要素に 'markdown' or 'text'、'page_number' など
            parts = []
            for idx, item in enumerate(result or []):
                md = (item.get('markdown') if isinstance(item, dict) else None) or \
                     (item.get('text') if isinstance(item, dict) else None) or ""
                # ページ番号が提供されない場合はリストの並び順から補完（1-based）
                pg = None
                if isinstance(item, dict):
                    pg = item.get('page_number')
                    if pg is None:
                        # 他の候補キー（ライブラリ差異の保険）
                        pg = item.get('page') or item.get('number') or item.get('page_no')
                if pg is None:
                    pg = page_number if page_number is not None else (idx + 1)
                if pg is not None:
                    parts.append(f"# Page {int(pg)}\n\n{md}")
                else:
                    parts.append(md)
            return "\n\n".join(parts)
        except Exception:
            # 予期しない構造はそのまま文字列化
            return str(result)

    def _debug_inspect_page_chunks(self, pages, label: str = "to_markdown"):
        """ページ配列の要素構造を簡易ダンプして、page_number等の存在を確認する"""
        try:
            if not isinstance(pages, list) or not pages:
                print(f"🧪 [{label}] inspect: pages is empty or not a list")
                return
            sample_idx = [0, min(1, len(pages)-1), len(pages)-1]
            seen_keys = set()
            found_page_id = False
            for i in sample_idx:
                item = pages[i]
                if isinstance(item, dict):
                    keys = list(item.keys())
                    seen_keys.update(keys)
                    pg = item.get('page_number') or item.get('page') or item.get('number') or item.get('page_no')
                    if pg is not None:
                        found_page_id = True
                    md = item.get('markdown') or item.get('text')
                    md_len = len(md) if isinstance(md, str) else 0
                    has_words = 'words' in item and isinstance(item.get('words'), (list, tuple))
                    has_images = 'images' in item and isinstance(item.get('images'), (list, tuple))
                    has_tables = 'tables' in item and isinstance(item.get('tables'), (list, tuple))
                    print(f"🔎 [{label}] sample idx={i+1}: keys={keys[:8]}... md_len={md_len} page_id={pg} words={has_words} images={has_images} tables={has_tables}")
                else:
                    print(f"🔎 [{label}] sample idx={i+1}: non-dict item type={type(item)}")
            print(f"🔎 [{label}] aggregate keys(sampled)={sorted(list(seen_keys))[:12]} ...; page_id_found={found_page_id}")
        except Exception as e:
            print(f"⚠️ debug inspect failed: {e}")
    
    def _create_error_fallback(self, pdf_path: str, error_message: str) -> ProcessedDocument:
        """エラー時のフォールバック処理結果作成"""
        try:
            doc_metadata = self._create_metadata(pdf_path)
            doc_metadata.processor_version += " (ERROR_FALLBACK)"
            
            error_content = f"PDF処理エラーが発生しました。\n\nエラー: {error_message}\n\nファイル: {pdf_path}"
            
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
    
    def _calculate_stats_safe(self, markdown_text: str, chunks) -> Dict:
        """統計計算（安全版・ゼロ除算対策）"""
        try:
            total_chunks = len(chunks) if chunks else 0
            total_chars = len(markdown_text) if markdown_text else 0
            
            # ゼロ除算対策
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
    
    # 残りのメソッドは既存のまま...
    def _create_metadata(self, pdf_path: str) -> DocumentMetadata:
        """メタデータ作成"""
        file_path = Path(pdf_path)
        
        # ファイルハッシュ
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
    
    def _count_chunk_types(self, chunks) -> Dict[str, int]:
        """チャンクタイプ集計（安全版）"""
        try:
            type_counts = {}
            for chunk in chunks:
                if chunk and hasattr(chunk, 'chunk_metadata'):
                    chunk_type = chunk.chunk_metadata.chunk_type
                    type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            return type_counts
        except Exception:
            return {}

    def _apply_rag_metadata(self, chunks, doc_metadata: DocumentMetadata):
        """RAGメタ設定を簡易的にチャンクへ反映"""
        try:
            rag = self.settings.rag_settings or {}
            emit_source_title = rag.get("emit_source_title", True)
            emit_page_number = rag.get("emit_page_number", True)
            emit_toc_section = rag.get("emit_toc_section", True)

            for ch in chunks or []:
                md = getattr(ch, 'chunk_metadata', None)
                if not md:
                    continue
                # source title
                if emit_source_title and doc_metadata and doc_metadata.filename:
                    if doc_metadata.filename not in md.keywords:
                        md.keywords.append(doc_metadata.filename)
                # page number（セクションタイトルが"Page N"のとき）
                if emit_page_number and md.section_title:
                    st = md.section_title.strip().lower()
                    if st.startswith('page '):
                        try:
                            pg = int(st.split(' ', 1)[1].split()[0])
                            tag = f"page:{pg}"
                            if tag not in md.keywords:
                                md.keywords.append(tag)
                        except Exception:
                            pass
                # toc section
                if emit_toc_section and md.section_title:
                    tag = f"toc:{md.section_title}"
                    if tag not in md.keywords:
                        md.keywords.append(tag)
        except Exception:
            return
