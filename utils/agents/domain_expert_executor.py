# utils/agents/domain_expert_executor.py
"""
DomainExpert Executor - 専門分析エージェント（完全版）

KeyRegistry統合版。旧形式のキーは一切サポートしません。
検索結果に基づいて専門的な分析を行います。
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry


class DomainExpertExecutor(BaseAgentExecutor):
    """段階間連携対応専門分析エージェント（KeyRegistry完全対応）"""
    
    def __init__(self, log_manager, threshold_manager, llm_manager):
        super().__init__("domain_expert", log_manager, threshold_manager)
        self.llm_manager = llm_manager
        self._node_config = {"config": {}, "node_id": "unknown"}
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """段階間連携専門分析実行"""
        try:
            node_id = node_id or self._node_config.get("node_id", "unknown")
            node_id_str = str(node_id)
            
            # 統合された検索結果を取得
            search_results = self._collect_search_results(current_data)
            original_query = current_data.get("user_input", "")
            
            if not search_results or not original_query:
                return self._create_error_result("分析データ不足", node_id)
            
            # VERBOSEレベル判定
            log_name = f"domain_expert_{node_id_str}"
            is_verbose = (hasattr(self.log, '_agent_levels') and 
                         (self.log._agent_levels.get(log_name) == LogLevel.VERBOSE or
                          self.log._agent_levels.get('domain_expert') == LogLevel.VERBOSE))
            
            # 専門分野設定取得
            domain = self._get_threshold_safe("expertise_domain", "一般技術")
            expert_profile = self._get_threshold_safe("expert_profile", "技術専門家")
            min_facts = self._get_threshold_safe("min_facts_count", 3)
            min_insights = self._get_threshold_safe("min_insights_count", 2)
            
            # ログ出力
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"専門分析開始: {domain}", node_id)
                self._log(LogLevel.VERBOSE, f"検索結果数: {len(search_results)}", node_id)
            else:
                self._log(LogLevel.MINIMAL, f"専門分析開始: {domain}", node_id)
            
            # プロンプト構築
            prompt = self._build_expert_prompt(
                original_query,
                search_results,
                domain,
                expert_profile,
                min_facts,
                min_insights
            )
            
            # LLM実行
            response = self.llm_manager.get_response(prompt)
            
            # VERBOSEレベル時のLLM応答ログ
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"LLM応答サイズ: {len(response)} 文字", node_id)
            
            # パース
            parsed_result = self._parse_expert_response(response)
            
            # 信頼度計算
            confidence = self._calculate_confidence(parsed_result, min_facts, min_insights)
            
            # KeyRegistryを使用して出力データ構築（後方互換性なし）
            output_data = self._build_output_data(parsed_result, confidence, node_id_str, domain)
            
            self._log(
                LogLevel.MINIMAL,
                f"専門分析完了: 信頼度={confidence:.2f}",
                node_id
            )
            
            return self._create_result(confidence=confidence, data=output_data)
            
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"専門分析エラー: {str(e)}", node_id)
            return self._create_error_result(str(e), node_id)
    
    def _collect_search_results(self, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """全Retrieverからの検索結果を統合収集"""
        search_results = []
        
        # search_results_{node_id} パターンのキーを検索
        for key, value in current_data.items():
            if key.startswith("search_results_") and isinstance(value, list):
                search_results.extend(value)
        
        return search_results
    
    def _build_output_data(
        self,
        parsed_result: Dict[str, Any],
        confidence: float,
        node_id: str,
        domain: str
    ) -> Dict[str, Any]:
        """出力データを構築（KeyRegistry使用・後方互換性完全削除）"""
        # KeyRegistryから各キー名を取得
        analysis_key = KeyRegistry.get_key_name("domain_expert", "analysis", node_id)
        facts_key = KeyRegistry.get_key_name("domain_expert", "facts", node_id)
        insights_key = KeyRegistry.get_key_name("domain_expert", "insights", node_id)
        recommendations_key = KeyRegistry.get_key_name("domain_expert", "recommendations", node_id)
        confidence_key = KeyRegistry.get_key_name("domain_expert", "confidence", node_id)
        gaps_key = KeyRegistry.get_key_name("domain_expert", "gaps", node_id)
        
        # 後方互換性は完全削除 - KeyRegistryのみ
        return {
            analysis_key: parsed_result.get("analysis", ""),
            facts_key: parsed_result.get("facts", []),
            insights_key: parsed_result.get("insights", []),
            recommendations_key: parsed_result.get("recommendations", []),
            confidence_key: confidence,
            gaps_key: parsed_result.get("gaps", [])
        }
    
    def _get_threshold_safe(self, key: str, default: Any) -> Any:
        """閾値取得（エラー時はデフォルト値を返す）"""
        try:
            return self._get_threshold(key)
        except KeyError:
            return default
    
    def _build_expert_prompt(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        domain: str,
        expert_profile: str,
        min_facts: int,
        min_insights: int
    ) -> str:
        """専門分析プロンプト構築"""
        prompts = self._get_threshold("llm_prompts")
        system_prompt = prompts.get("system_prompt", "")
        analysis_instruction = prompts.get("analysis_instruction", "")
        output_format = prompts.get("output_format", "")
        
        # 検索結果を整形
        context = self._format_search_results(search_results[:10])
        
        return f"""{system_prompt}

あなたは{domain}の専門家（{expert_profile}）です。

{analysis_instruction}

【要求事項】
- 事実: 最低{min_facts}件
- 洞察: 最低{min_insights}件

質問: "{query}"

【検索結果】
{context}

{output_format}"""
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """検索結果を整形"""
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.get("content", result.get("text", ""))
            score = result.get("score", 0.0)
            formatted.append(f"{i}. [スコア: {score:.3f}] {content[:300]}")
        return "\n\n".join(formatted)
    
    def _parse_expert_response(self, response: str) -> Dict[str, Any]:
        """専門家応答のパース"""
        import json
        
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
            
            # デフォルト値設定
            result.setdefault("analysis", "")
            result.setdefault("facts", [])
            result.setdefault("insights", [])
            result.setdefault("recommendations", [])
            result.setdefault("gaps", [])
            
            return result
            
        except Exception as e:
            # パース失敗時のフォールバック
            return {
                "analysis": response[:1000],
                "facts": [],
                "insights": [],
                "recommendations": [],
                "gaps": ["JSONパース失敗"]
            }
    
    def _calculate_confidence(
        self,
        parsed_result: Dict[str, Any],
        min_facts: int,
        min_insights: int
    ) -> float:
        """信頼度計算"""
        facts_count = len(parsed_result.get("facts", []))
        insights_count = len(parsed_result.get("insights", []))
        has_analysis = bool(parsed_result.get("analysis", "").strip())
        
        # 基本信頼度
        confidence = 0.3
        
        # 分析内容がある
        if has_analysis:
            confidence += 0.2
        
        # 事実の充足度
        if facts_count >= min_facts:
            confidence += 0.25
        elif facts_count > 0:
            confidence += 0.25 * (facts_count / min_facts)
        
        # 洞察の充足度
        if insights_count >= min_insights:
            confidence += 0.25
        elif insights_count > 0:
            confidence += 0.25 * (insights_count / min_insights)
        
        return min(1.0, confidence)
    
    def _create_error_result(self, error_message: str, node_id: Optional[str] = None) -> AgentResult:
        """エラー結果生成（KeyRegistry使用・後方互換性完全削除）"""
        node_id_str = str(node_id) if node_id else "unknown"
        
        # 後方互換性は完全削除 - KeyRegistryのみ
        error_data = {
            KeyRegistry.get_key_name("domain_expert", "analysis", node_id_str): f"エラー: {error_message}",
            KeyRegistry.get_key_name("domain_expert", "facts", node_id_str): [],
            KeyRegistry.get_key_name("domain_expert", "insights", node_id_str): [],
            KeyRegistry.get_key_name("domain_expert", "recommendations", node_id_str): [],
            KeyRegistry.get_key_name("domain_expert", "confidence", node_id_str): 0.0,
            KeyRegistry.get_key_name("domain_expert", "gaps", node_id_str): [error_message]
        }
        
        return self._create_result(
            confidence=0.0,
            data=error_data,
            has_error=True,
            status="error"
        )