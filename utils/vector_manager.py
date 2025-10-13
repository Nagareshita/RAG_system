# utils/vector_manager.py
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import hashlib
import threading

class VectorManager:
    """ベクトル検索とクロスエンコーダ再ランク統合管理（Thread-Safe シングルトン）"""
    
    _instance = None
    _initialized = False
    _lock = threading.Lock()  # スレッドセーフ用のロック
    
    def __new__(cls, db_path: str = "vector_db", model_name: str = "BAAI/bge-m3"):
        with cls._lock:  # ロックで保護
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = "vector_db", model_name: str = "BAAI/bge-m3"):
        # 初期化は一度だけ実行（スレッドセーフ）
        with VectorManager._lock:
            if not VectorManager._initialized:
                self.db_path = db_path
                self.model_name = model_name
                self.model = None
                self.reranker_model = None
                self.client = None
                self.use_gpu = True
                VectorManager._initialized = True
    
    @classmethod
    def reset_instance(cls):
        """インスタンスをリセット（テスト用）"""
        with cls._lock:  # ロックで保護
            if cls._instance:
                if hasattr(cls._instance, 'client') and cls._instance.client:
                    try:
                        cls._instance.client.close()
                    except:
                        pass
                cls._instance = None
                cls._initialized = False
    
    def initialize_model(self, use_gpu: bool = True) -> bool:
        """BGE-M3モデル初期化（スレッドセーフ）"""
        with VectorManager._lock:  # ロックで保護
            # 既に初期化済みの場合はスキップ
            if self.model is not None:
                return True
                
            try:
                from FlagEmbedding import BGEM3FlagModel
                import os
                
                self.use_gpu = use_gpu
                device = 'cuda' if use_gpu else 'cpu'
                
                # 既存モデルのクリーンアップ
                if self.model is not None:
                    del self.model
                    self.model = None
                
                self.model = BGEM3FlagModel(
                    self.model_name, 
                    use_fp16=use_gpu,
                    device=device
                )
                return True
            except Exception as e:
                print(f"モデル初期化エラー: {e}")
                return False
    
    def initialize_reranker(self, reranker_model: str = "BAAI/bge-reranker-large") -> bool:
        """クロスエンコーダ再ランクモデル初期化（スレッドセーフ）"""
        with VectorManager._lock:  # ロックで保護
            try:
                from FlagEmbedding import FlagReranker
                
                # 既に初期化済みなら再初期化不要
                if self.reranker_model is not None:
                    return True
                
                self.reranker_model = FlagReranker(
                        reranker_model,
                        use_fp16=self.use_gpu,
                        cache_dir="model_cache"
                    )
                return True
            except Exception as e:
                print(f"再ランクモデル初期化エラー: {e}")
                return False
    
    def get_qdrant_client(self) -> QdrantClient:
        """Qdrantクライアント取得"""
        if self.client is None:
            self.client = QdrantClient(path=self.db_path)
        return self.client
    
    def force_reinitialize_models(self):
        """モデルを強制的に再初期化"""
        if self.model:
            del self.model
            self.model = None
        if self.reranker_model:
            del self.reranker_model
            self.reranker_model = None
        
        # クライアントも再初期化
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
    
    # 既存のメソッドはそのまま維持
    def search_with_rerank(self, query: str, collection_name: str, 
                          initial_k: int = 20, final_k: int = 5,
                          similarity_threshold: float = 0.0, 
                          use_reranker: bool = True) -> List[Dict[str, Any]]:
        """Dense検索 + クロスエンコーダ再ランク統合検索"""
        initial_results = self._dense_search(query, collection_name, initial_k, max(similarity_threshold, 0.0))
        
        if not initial_results or not use_reranker:
            return initial_results[:final_k]
        
        if self.reranker_model is None:
            return initial_results[:final_k]
        
        reranked_results = self._rerank_results(query, initial_results)
        return reranked_results[:final_k]
    
    def _dense_search(self, query: str, collection_name: str, 
                    limit: int, score_threshold: float) -> List[Dict[str, Any]]:
        """Dense検索実行"""
        try:
            if not self.model:
                return []
            
            query_result = self.model.encode([query])
            
            if isinstance(query_result, dict) and 'dense_vecs' in query_result:
                query_vector = query_result['dense_vecs'][0]
            else:
                query_vector = query_result[0] if isinstance(query_result, list) else query_result
            
            client = self.get_qdrant_client()
            search_result = client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for hit in search_result:
                entry_id = hit.payload.get("entry_id", 0)
                chunk_id = f"chunk:{collection_name.replace('rag_documents_', '')}:{entry_id}"
                
                results.append({
                    "chunk_id": chunk_id,
                    "text": hit.payload.get("text", ""),
                    "score": float(hit.score),
                    "source_file": hit.payload.get("source_file", ""),
                    "metadata": hit.payload.get("metadata", {}),
                    "entry_id": entry_id,
                    "collection": collection_name
                })
            
            return results
            
        except Exception as e:
            return []
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """クロスエンコーダによる結果再ランク"""
        try:
            if not self.reranker_model or not results:
                return results
            
            query_text_pairs = []
            for result in results:
                text = result.get("text", "")[:512]
                query_text_pairs.append([query, text])
            
            rerank_scores = self.reranker_model.compute_score(query_text_pairs)
            
            if hasattr(rerank_scores, 'tolist'):
                rerank_scores = rerank_scores.tolist()
            
            for i, result in enumerate(results):
                if i < len(rerank_scores):
                    result["rerank_score"] = float(rerank_scores[i])
                    result["original_score"] = result["score"]
                    result["score"] = float(rerank_scores[i])
            
            results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return results
            
        except Exception as e:
            return results
    
    def create_collection(self, collection_name: str, vector_size: int = 1024):
        """コレクション作成"""
        client = self.get_qdrant_client()
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            return True
        except Exception as e:
            return False
    
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """ドキュメント追加"""
        if not self.model:
            if not self.initialize_model(self.use_gpu):
                return False
        
        client = self.get_qdrant_client()
        points = []
        
        # バッチでベクトル化
        texts = [doc.get("text", "") for doc in documents if doc.get("text", "")]
        if not texts:
            return False
        
        encode_result = self.model.encode(texts)
        
        if isinstance(encode_result, dict) and 'dense_vecs' in encode_result:
            vectors = encode_result['dense_vecs']
        else:
            vectors = encode_result if isinstance(encode_result, list) else [encode_result]
        
        for i, doc in enumerate(documents):
            if i < len(vectors):
                vector = vectors[i].tolist() if hasattr(vectors[i], 'tolist') else vectors[i]
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": doc.get("text", ""),
                        "source_file": doc.get("source_file", ""),
                        "entry_id": doc.get("entry_id", i),
                        "metadata": doc.get("metadata", {}),
                        "file_hash": doc.get("file_hash", "")
                    }
                )
                points.append(point)
        
        try:
            client.upsert(collection_name=collection_name, points=points)
            return True
        except Exception as e:
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """コレクション情報取得"""
        try:
            client = self.get_qdrant_client()
            collection_info = client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": collection_info.status
            }
        except Exception:
            return None
    
    def list_collections(self) -> List[str]:
        """コレクション一覧取得"""
        try:
            client = self.get_qdrant_client()
            collections = client.get_collections().collections
            return [c.name for c in collections]
        except Exception:
            return []

    def analyze_file_structure(self, file_path: str) -> Dict[str, Any]:
        """ファイル構造解析"""
        file_ext = os.path.splitext(file_path)[1].lower()
        structure_info = {
            "file_path": file_path,
            "file_type": file_ext,
            "text_fields": [],
            "sample_data": None,
            "total_entries": 0,
            "file_hash": self.calculate_file_hash(file_path)
        }
        
        try:
            if file_ext == '.jsonl':
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if first_line.strip():
                        sample_data = json.loads(first_line)
                        structure_info["sample_data"] = sample_data
                        structure_info["text_fields"] = self._find_text_fields(sample_data)
                    
                    f.seek(0)
                    structure_info["total_entries"] = sum(1 for _ in f)
                        
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict) and 'chunks' in data:
                        structure_info["total_entries"] = len(data['chunks'])
                        structure_info["text_fields"] = ['chunks[].content']
                        structure_info["sample_data"] = data
                    elif isinstance(data, list) and data:
                        structure_info["sample_data"] = data[0]
                        structure_info["text_fields"] = self._find_text_fields(data[0])
                        structure_info["total_entries"] = len(data)
                    elif isinstance(data, dict):
                        structure_info["sample_data"] = data
                        structure_info["text_fields"] = self._find_text_fields(data)
                        structure_info["total_entries"] = 1
                        
        except Exception as e:
            structure_info["error"] = str(e)
            
        return structure_info

    def _find_text_fields(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """テキストフィールド検出"""
        text_fields = []
        
        for key, value in data.items():
            current_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, str) and len(value) > 10:
                text_fields.append(current_key)
            elif isinstance(value, dict):
                text_fields.extend(self._find_text_fields(value, current_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                text_fields.extend(self._find_text_fields(value[0], f"{current_key}[0]"))
                
        return text_fields

    def extract_texts_from_structure(self, file_path: str, text_fields: List[str]) -> List[Dict[str, Any]]:
        """テキスト抽出"""
        file_ext = os.path.splitext(file_path)[1].lower()
        extracted_texts = []
        
        try:
            if file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict) and 'chunks' in data:
                        for idx, chunk in enumerate(data['chunks']):
                            if 'content' in chunk and chunk['content'].strip():
                                extracted_texts.append({
                                    "source_file": file_path,
                                    "entry_id": idx + 1,
                                    "text": chunk['content'].strip(),
                                    "metadata": {
                                        **data.get('document_metadata', {}),
                                        **chunk.get('chunk_metadata', {}),
                                        "chunk_id": chunk.get('chunk_id', f'chunk_{idx}')
                                    }
                                })
                    else:
                        text_content = self._extract_text_from_data(data, text_fields)
                        if text_content:
                            extracted_texts.append({
                                "source_file": file_path,
                                "entry_id": 1,
                                "text": text_content,
                                "metadata": self._extract_metadata(data)
                            })
            
            elif file_ext == '.jsonl':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        if line.strip():
                            data = json.loads(line)
                            text_content = self._extract_text_from_data(data, text_fields)
                            if text_content:
                                extracted_texts.append({
                                    "source_file": file_path,
                                    "entry_id": line_no,
                                    "text": text_content,
                                    "metadata": self._extract_metadata(data)
                                })
                            
        except Exception as e:
            print(f"テキスト抽出エラー ({file_path}): {e}")
            
        return extracted_texts

    def _extract_text_from_data(self, data: Dict[str, Any], text_fields: List[str]) -> str:
        """テキスト抽出"""
        texts = []
        for field in text_fields:
            value = self._get_nested_value(data, field)
            if value and isinstance(value, str):
                texts.append(value)
        return " ".join(texts) if texts else ""

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """ネスト値取得"""
        try:
            keys = field_path.split('.')
            current = data
            
            for key in keys:
                if '[' in key and ']' in key:
                    field_name = key.split('[')[0]
                    current = current[field_name]
                    if isinstance(current, list) and current:
                        current = current[0]
                else:
                    current = current[key]
                    
            return current
        except (KeyError, IndexError, TypeError):
            return None

    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メタデータ抽出"""
        metadata = {}
        
        def extract_all_metadata(obj: Any, prefix: str = "") -> Dict[str, Any]:
            result = {}
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, (str, int, float, bool)):
                        if not (isinstance(value, str) and len(value) > 100):
                            result[current_key] = value
                    elif isinstance(value, dict):
                        nested = extract_all_metadata(value, current_key)
                        result.update(nested)
                            
            return result
        
        metadata = extract_all_metadata(data)
        metadata["_original_structure"] = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        return metadata

    def calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュ計算"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception:
            return None

    def vectorize_documents(self, file_structures: List[Dict[str, Any]], 
                          progress_callback=None, log_callback=None,
                          batch_size=128, encode_batch_size=64, max_text_length=1500,
                          collection_type="mixed") -> bool:
        """ベクトル化処理"""
        try:
            if not self.model:
                if log_callback:
                    log_callback("モデルを初期化しています...")
                if not self.initialize_model(self.use_gpu):
                    return False
            
            if collection_type == "分離":
                return self._process_separated_collections(
                    file_structures, progress_callback, log_callback, 
                    batch_size, encode_batch_size, max_text_length
                )
            else:
                collection_name = "rag_documents_mixed"
                self.create_collection(collection_name)
                return self._process_single_collection(
                    collection_name, file_structures, progress_callback, 
                    log_callback, batch_size, encode_batch_size, max_text_length
                )
                
        except Exception as e:
            if log_callback:
                log_callback(f"ベクトル化エラー: {e}")
            return False

    def _process_separated_collections(self, file_structures, progress_callback, log_callback, 
                                     batch_size, encode_batch_size, max_text_length):
        """分離処理"""
        ast_files = [f for f in file_structures if f['file_path'].endswith('.jsonl')]
        pdf_files = [f for f in file_structures if f['file_path'].endswith('.json')]
        
        success_count = 0
        
        if ast_files:
            if log_callback:
                log_callback(f"AST専用コレクションを処理中... ({len(ast_files)}ファイル)")
            self.create_collection("rag_documents_ast")
            if self._process_single_collection("rag_documents_ast", ast_files, progress_callback, 
                                             log_callback, batch_size, encode_batch_size, max_text_length):
                success_count += 1
        
        if pdf_files:
            if log_callback:
                log_callback(f"PDF専用コレクションを処理中... ({len(pdf_files)}ファイル)")
            self.create_collection("rag_documents_pdf")
            if self._process_single_collection("rag_documents_pdf", pdf_files, progress_callback,
                                             log_callback, batch_size, encode_batch_size, max_text_length):
                success_count += 1
        
        return success_count > 0

    def _process_single_collection(self, collection_name, file_structures, progress_callback, 
                                 log_callback, batch_size, encode_batch_size, max_text_length):
        """単一コレクション処理"""
        try:
            total_vectors = 0
            total_entries = sum(s.get('total_entries', 0) for s in file_structures)
            processed_entries = 0
            
            for file_idx, structure in enumerate(file_structures):
                file_path = structure['file_path']
                text_fields = structure.get('text_fields', [])
                file_entries = structure.get('total_entries', 0)
                file_hash = structure.get('file_hash', '')
                
                if log_callback:
                    log_callback(f"処理中: {os.path.basename(file_path)} ({file_entries}エントリー)")
                
                extracted_texts = self.extract_texts_from_structure(file_path, text_fields)
                
                if not extracted_texts:
                    if log_callback:
                        log_callback(f"警告: {os.path.basename(file_path)} からテキストが抽出されませんでした")
                    continue
                
                for text_data in extracted_texts:
                    text_data['file_hash'] = file_hash
                
                file_vectors = 0
                
                for i in range(0, len(extracted_texts), batch_size):
                    batch = extracted_texts[i:i + batch_size]
                    
                    texts = []
                    valid_docs = []
                    for item in batch:
                        text = item['text'].strip()
                        if text:
                            if len(text) > max_text_length:
                                text = text[:max_text_length] + "..."
                            texts.append(text)
                            valid_docs.append(item)
                    
                    if not texts:
                        continue
                    
                    if log_callback:
                        log_callback(f"ベクトル化中: {len(texts)}件 ({i+1}-{min(i+len(texts), len(extracted_texts))})")
                    
                    try:
                        docs_to_add = []
                        for j, doc in enumerate(valid_docs):
                            docs_to_add.append({
                                "text": texts[j],
                                "source_file": doc["source_file"],
                                "entry_id": doc["entry_id"],
                                "metadata": doc["metadata"],
                                "file_hash": doc.get("file_hash", "")
                            })
                        
                        if self.add_documents(collection_name, docs_to_add):
                            file_vectors += len(texts)
                            total_vectors += len(texts)
                            processed_entries += len(texts)
                        
                        if progress_callback and total_entries > 0:
                            progress_percent = int((processed_entries / total_entries) * 70) + 30
                            progress_callback(progress_percent)
                        
                    except Exception as batch_error:
                        if log_callback:
                            log_callback(f"バッチ処理エラー: {batch_error}")
                        continue
                
                if log_callback:
                    log_callback(f"{os.path.basename(file_path)} 完了: {file_vectors}ベクトル")
            
            if log_callback:
                log_callback(f"ベクトル化完了: 総計 {total_vectors} ベクトル")
            
            return total_vectors > 0
            
        except Exception as e:
            if log_callback:
                log_callback(f"処理エラー: {e}")
            return False