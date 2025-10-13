# utils/agents/retriever_executor.py
"""
Retriever Executor - ベクトル検索エージェント（完全版）

KeyRegistry統合版。旧形式のキーは一切サポートしません。
クロスエンコーダ再ランク対応のベクトル検索を実行します。
"""

from typing import Dict, Any, List, Optional
import math
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry


class RetrieverExecutor(BaseAgentExecutor):
    """クロスエンコーダ再ランク対応検索エージェント（KeyRegistry完全対応）"""
    
    def __init__(self, log_manager, threshold_manager, vector_manager):
        super().__init__("retriever", log_manager, threshold_manager)
        self.vector_manager = vector_manager
        self._node_config = {"config": {}, "node_id": "unknown"}
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """クロスエンコーダ対応ベクトル検索実行"""
        node_id = node_id or self._node_config.get("node_id", "unknown")
        node_id_str = str(node_id)
        
        # 最適化された検索クエリを取得
        optimized_query = self._get_search_query(current_data, node_id_str)
        
        if not optimized_query:
            return self._create_error_result("検索クエリなし", node_id)
        
        # VERBOSEレベル判定
        log_name = f"retriever_{node_id_str}"
        is_verbose = (hasattr(self.log, '_agent_levels') and 
                     (self.log._agent_levels.get(log_name) == LogLevel.VERBOSE or
                      self.log._agent_levels.get('retriever') == LogLevel.VERBOSE))
        
        # ログ出力
        if is_verbose:
            self._log(LogLevel.VERBOSE, f"検索開始: {optimized_query}", node_id)
        else:
            self._log(LogLevel.MINIMAL, f"検索開始: {optimized_query[:30]}...", node_id)
        
        # 設定値取得
        use_reranker = self._get_reranker_config()
        initial_k = self._get_threshold("initial_k") if use_reranker else self._get_threshold("search_k")
        final_k = self._get_threshold("search_k")
        similarity_threshold = self._get_threshold("similarity_threshold")
        target_collections = self._determine_target_collections()
        
        if not target_collections:
            return self._create_error_result("利用可能なコレクションなし", node_id)
        
        # VERBOSEレベル時の設定値ログ
        if is_verbose:
            self._log(LogLevel.VERBOSE, "=== 検索設定 ===", node_id)
            self._log(LogLevel.VERBOSE, f"再ランク使用: {use_reranker}", node_id)
            self._log(LogLevel.VERBOSE, f"初期取得数: {initial_k}", node_id)
            self._log(LogLevel.VERBOSE, f"最終取得数: {final_k}", node_id)
            self._log(LogLevel.VERBOSE, f"類似度閾値: {similarity_threshold}", node_id)
            self._log(LogLevel.VERBOSE, f"対象コレクション: {target_collections}", node_id)
        
        # モデル初期化確認
        if not self.vector_manager.model:
            if is_verbose:
                self._log(LogLevel.VERBOSE, "Dense検索モデル初期化中", node_id)
            if not self.vector_manager.initialize_model():
                return self._create_error_result("Dense検索モデル初期化失敗", node_id)
        
        # 再ランクモデル初期化
        if use_reranker and not self.vector_manager.reranker_model:
            reranker_model = self._get_reranker_model()
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"再ランクモデル初期化中: {reranker_model}", node_id)
            if not self.vector_manager.initialize_reranker(reranker_model):
                if is_verbose:
                    self._log(LogLevel.VERBOSE, "再ランクモデル初期化失敗、Dense検索のみ実行", node_id)
                use_reranker = False
        
        # 各コレクションで統合検索実行
        all_results = []
        for collection_name in target_collections:
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"=== {collection_name} 統合検索実行 ===", node_id)
            
            results = self.vector_manager.search_with_rerank(
                query=optimized_query,
                collection_name=collection_name,
                initial_k=initial_k,
                final_k=final_k,
                similarity_threshold=similarity_threshold,
                use_reranker=use_reranker
            )
            
            # VERBOSEレベル時のみ検索結果詳細ログ
            if results and is_verbose:
                self._log(LogLevel.VERBOSE, f"{collection_name}: {len(results)}件取得", node_id)
                for i, result in enumerate(results):
                    self._log(LogLevel.VERBOSE, f"結果[{i+1}]: スコア={result['score']:.4f}, {result.get('text', '')[:100]}...", node_id)
            elif not results and is_verbose:
                self._log(LogLevel.VERBOSE, f"{collection_name}: 検索結果なし", node_id)
            
            all_results.extend(results)
        
        if not all_results:
            return self._create_error_result("検索結果なし", node_id)
        
        # 全コレクション結果の統合ソート
        all_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = all_results[:final_k]
        
        # VERBOSEレベル時のみ最終結果統計
        if is_verbose:
            self._log(LogLevel.VERBOSE, "=== 最終結果統計 ===", node_id)
            self._log(LogLevel.VERBOSE, f"総検索結果: {len(all_results)}件", node_id)
            self._log(LogLevel.VERBOSE, f"上位選択: {len(final_results)}件", node_id)
            scores = [r["score"] for r in final_results]
            if scores:
                self._log(LogLevel.VERBOSE, f"スコア範囲: {min(scores):.4f} - {max(scores):.4f}", node_id)
                self._log(LogLevel.VERBOSE, f"平均スコア: {sum(scores)/len(scores):.4f}", node_id)
        
        # 信頼度計算
        confidence = self._calculate_confidence(final_results, similarity_threshold)
        
        # KeyRegistryを使用して出力データ構築
        output_data = self._build_output_data(
            final_results,
            confidence,
            node_id_str,
            target_collections,
            use_reranker
        )
        
        # ログ出力
        search_type = "再ランク検索" if use_reranker else "Dense検索"
        self._log(LogLevel.MINIMAL, f"{search_type}完了: {len(final_results)}件, 信頼度={confidence:.2f}", node_id)
        
        return self._create_result(confidence=confidence, data=output_data)
    
    def _get_search_query(self, current_data: Dict[str, Any], node_id: str) -> str:
        """検索クエリを取得（KeyRegistry対応・優先順位付き）"""
        # 優先順位:
        # 1. optimized_search_query (共通キー - Analyzerから)
        # 2. optimized_query_{node_id} (Analyzerのノード固有キー)
        # 3. user_input (最終フォールバック)
        
        search_query_key = KeyRegistry.get_key_name("analyzer", "optimized_search_query")
        
        # Analyzerのoptimized_queryキーも試す
        try:
            analyzer_query_key = KeyRegistry.get_key_name("analyzer", "optimized_query", node_id)
        except:
            analyzer_query_key = None
        
        return (
            current_data.get(search_query_key) or
            (current_data.get(analyzer_query_key) if analyzer_query_key else None) or
            current_data.get("user_input", "")
        )
    
    def _build_output_data(
        self,
        search_results: List[Dict[str, Any]],
        confidence: float,
        node_id: str,
        target_collections: List[str],
        use_reranker: bool
    ) -> Dict[str, Any]:
        """出力データを構築（KeyRegistry使用・後方互換性なし）"""
        # KeyRegistryから各キー名を取得
        results_key = KeyRegistry.get_key_name("retriever", "search_results", node_id)
        confidence_key = KeyRegistry.get_key_name("retriever", "confidence", node_id)
        metadata_key = KeyRegistry.get_key_name("retriever", "retrieval_metadata", node_id)
        
        return {
            results_key: search_results,
            confidence_key: confidence,  # confidence_{node_id}
            metadata_key: {
                "total_results": len(search_results),
                "target_collections": target_collections,
                "reranker_used": use_reranker,
                "node_id": node_id
            }
        }
    
    def _get_reranker_config(self) -> bool:
        """再ランク設定取得"""
        try:
            return self._get_threshold("use_reranker")
        except KeyError:
            return False
    
    def _get_reranker_model(self) -> str:
        """再ランクモデル名取得"""
        try:
            return self._get_threshold("reranker_model")
        except KeyError:
            return "BAAI/bge-reranker-large"
    
    def _determine_target_collections(self) -> List[str]:
        """検索対象コレクション決定"""
        # NodeThresholdManagerから取得
        try:
            target_collections = self._get_threshold("target_collections")
            if target_collections and isinstance(target_collections, list):
                valid_collections = [c for c in target_collections if self._has_data(c)]
                if valid_collections:
                    return valid_collections
        except:
            pass
        
        # デフォルト: 利用可能な全コレクション
        available_collections = self.vector_manager.list_collections()
        return [c for c in available_collections if self._has_data(c)]
    
    def _has_data(self, collection_name: str) -> bool:
        """コレクションにデータが存在するか確認"""
        try:
            client = self.vector_manager.get_qdrant_client()
            collection_info = client.get_collection(collection_name)
            return collection_info.points_count > 0
        except:
            return False
    
    def _calculate_confidence(
        self,
        search_results: List[Dict[str, Any]],
        similarity_threshold: float
    ) -> float:
        """検索信頼度を計算（Sigmoid正規化対応）"""
        if not search_results:
            return 0.0
        
        # 上位3件の平均スコアを使用
        top_scores = [result.get("score", 0.0) for result in search_results[:3]]
        
        if not top_scores:
            return 0.0
        
        avg_score = sum(top_scores) / len(top_scores)
        
        # Sigmoid正規化でスコアを0～1に変換
        # クロスエンコーダのスコア（-10～+10程度）をロジットとして扱う
        confidence = self._sigmoid_normalize(avg_score)
        
        # 信頼度が高い場合（0.7以上）はそのまま使用
        # 中程度（0.5～0.7）は若干減衰
        # 低い場合（0.5未満）はさらに減衰
        if confidence >= 0.7:
            return min(1.0, confidence)
        elif confidence >= 0.5:
            return confidence * 0.9
        else:
            return confidence * 0.8
    
    def _sigmoid_normalize(self, score: float) -> float:
        """Sigmoid関数でスコアを0～1に正規化
        
        Args:
            score: クロスエンコーダのスコア（通常-10～+10）
        
        Returns:
            0～1の範囲に正規化された信頼度
        """
        try:
            return 1 / (1 + math.exp(-score))
        except OverflowError:
            # スコアが極端に小さい場合（例: -100以下）
            return 0.0 if score < 0 else 1.0
    
    def _create_error_result(self, error_message: str, node_id: Optional[str] = None) -> AgentResult:
        """エラー結果生成（KeyRegistry使用・後方互換性なし）"""
        node_id_str = str(node_id) if node_id else "unknown"
        
        error_data = {
            KeyRegistry.get_key_name("retriever", "search_results", node_id_str): [],
            KeyRegistry.get_key_name("retriever", "confidence", node_id_str): 0.0,
            KeyRegistry.get_key_name("retriever", "retrieval_metadata", node_id_str): {
                "error": error_message,
                "node_id": node_id_str
            }
        }
        
        return self._create_result(
            confidence=0.0,
            data=error_data,
            has_error=True,
            status="error"
        )