# utils/agents/analyzer_executor.py
"""
Analyzer Executor - クエリ分析・最適化エージェント（完全版）

KeyRegistry統合版。旧形式のキーは一切サポートしません。
"""

from typing import Dict, Any, Optional
import json
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry


class AnalyzerExecutor(BaseAgentExecutor):
    """ユーザー入力の分析・最適化エージェント（KeyRegistry完全対応）"""
    
    def __init__(self, log_manager, threshold_manager, llm_manager):
        super().__init__("analyzer", log_manager, threshold_manager)
        self.llm_manager = llm_manager
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """クエリ分析・最適化実行"""
        try:
            user_input = current_data.get("user_input", "")
            iteration_count = current_data.get("iteration_count", 1)
            node_id = node_id or self._node_config.get("node_id", "unknown")
            node_id_str = str(node_id)
            
            # JSON設定値取得
            depth = self._get_threshold("analysis_depth")
            prompts = self._get_threshold("llm_prompts")
            
            # VERBOSEレベル判定（ノード別設定のみ反映）
            log_name = f"analyzer_{node_id_str}"
            is_verbose = self.log.should_log(log_name, LogLevel.VERBOSE)
            
            # ログ出力
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"分析開始: {user_input}", node_id)
                self._log(LogLevel.VERBOSE, "=== JSON設定閾値 ===", node_id)
                self._log(LogLevel.VERBOSE, f"分析深度: {depth}", node_id)
                
                # 累積情報の確認
                available_info = self._get_available_context_info(current_data)
                if available_info:
                    self._log(LogLevel.VERBOSE, f"利用可能累積情報: {available_info}", node_id)
            else:
                self._log(LogLevel.MINIMAL, f"分析開始: {user_input[:50]}...", node_id)
            
            # 分析プロンプト構築
            prompt = self._build_analysis_prompt(user_input, iteration_count, current_data)
            
            # LLM実行
            response = self.llm_manager.get_response(prompt)
            
            # VERBOSEレベル時のLLM応答ログ
            if is_verbose:
                self._log(LogLevel.VERBOSE, "=== LLM応答詳細 ===", node_id)
                self._log(LogLevel.VERBOSE, f"応答サイズ: {len(response)} 文字", node_id)
                self._log(LogLevel.VERBOSE, f"応答内容: {response}", node_id)
            
            # パース
            parsed_result = self._parse_llm_response(response)
            
            # VERBOSEレベル時のパラメータ詳細ログ
            if is_verbose:
                self._log(LogLevel.VERBOSE, "=== パース済みパラメータ ===", node_id)
                self._log(LogLevel.VERBOSE, f"パラメータ総数: {len(parsed_result)} 個", node_id)
                for key, value in parsed_result.items():
                    self._log(LogLevel.VERBOSE, f"{key}: {str(value)}", node_id)
            
            # KeyRegistryを使用して出力データ構築
            output_data = self._build_output_data(parsed_result, node_id_str, user_input, depth)
            
            # 信頼度取得
            confidence = parsed_result.get("confidence", 0.5)
            
            self._log(LogLevel.VERBOSE, f"分析完了: 深度={depth}, 信頼度={confidence:.2f}", node_id)
            
            return self._create_result(confidence=confidence, data=output_data)
            
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"分析エラー: {str(e)}", node_id)
            return self._create_error_result(str(e), node_id)
    
    def _build_output_data(
        self,
        parsed_result: Dict[str, Any],
        node_id: str,
        user_input: str,
        depth: str
    ) -> Dict[str, Any]:
        """出力データを構築（KeyRegistry使用・後方互換性なし）"""
        # KeyRegistryから各キー名を取得
        intent_key = KeyRegistry.get_key_name("analyzer", "intent", node_id)
        optimized_query_key = KeyRegistry.get_key_name("analyzer", "optimized_query", node_id)
        confidence_key = KeyRegistry.get_key_name("analyzer", "confidence", node_id)
        config_key = KeyRegistry.get_key_name("analyzer", "config", node_id)
        
        # Retriever互換キー（共通キー）
        search_query_key = KeyRegistry.get_key_name("analyzer", "optimized_search_query")
        
        return {
            intent_key: parsed_result.get("intent", "unknown"),
            optimized_query_key: parsed_result.get("optimized_query", user_input),
            confidence_key: parsed_result.get("confidence", 0.5),
            config_key: {
                "analysis_depth": depth,
                "node_id": node_id
            },
            # Retriever用の互換キー
            search_query_key: parsed_result.get("optimized_query", user_input)
        }
    
    def _get_available_context_info(self, current_data: Dict[str, Any]) -> str:
        """累積情報の可視化"""
        info_parts = []
        
        # Retriever結果の確認
        retriever_keys = [k for k in current_data.keys() if k.startswith("search_results_")]
        if retriever_keys:
            info_parts.append(f"検索結果: {len(retriever_keys)}件")
        
        # DomainExpert結果の確認
        expert_keys = [k for k in current_data.keys() if k.startswith("analysis_")]
        if expert_keys:
            info_parts.append(f"専門分析: {len(expert_keys)}件")
        
        return ", ".join(info_parts) if info_parts else "なし"
    
    def _build_analysis_prompt(
        self,
        user_input: str,
        iteration_count: int,
        current_data: Dict[str, Any]
    ) -> str:
        """分析プロンプト構築"""
        prompts = self._get_threshold("llm_prompts")
        system_prompt = prompts.get("system_prompt", "")
        analysis_instruction = prompts.get("analysis_instruction", "")
        output_format = prompts.get("output_format", "")
        
        # 累積情報を含める
        context_info = ""
        if iteration_count > 1:
            context_info = f"\n\n【累積情報】\nイテレーション回数: {iteration_count}\n"
            available_info = self._get_available_context_info(current_data)
            if available_info and available_info != "なし":
                context_info += f"利用可能データ: {available_info}\n"
        
        return f"""{system_prompt}

{analysis_instruction}{context_info}

ユーザー入力: "{user_input}"

{output_format}"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """LLM応答のパース"""
        try:
            # JSONブロック抽出
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # 信頼度の正規化
            if "confidence" in result:
                confidence = result["confidence"]
                if isinstance(confidence, str):
                    confidence = float(confidence.rstrip('%')) / 100 if '%' in confidence else float(confidence)
                result["confidence"] = max(0.0, min(1.0, confidence))
            
            return result
            
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"JSONパースエラー: {str(e)}")
            # フォールバック
            return {
                "intent": "query",
                "optimized_query": response[:200],
                "confidence": 0.5
            }
    
    def _create_error_result(self, error_message: str, node_id: Optional[str] = None) -> AgentResult:
        """エラー結果生成（KeyRegistry使用・後方互換性なし）"""
        node_id_str = str(node_id) if node_id else "unknown"
        
        error_data = {
            KeyRegistry.get_key_name("analyzer", "intent", node_id_str): "error",
            KeyRegistry.get_key_name("analyzer", "optimized_query", node_id_str): "",
            KeyRegistry.get_key_name("analyzer", "confidence", node_id_str): 0.0,
            KeyRegistry.get_key_name("analyzer", "config", node_id_str): {
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
