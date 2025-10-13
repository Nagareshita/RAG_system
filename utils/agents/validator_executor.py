# utils/agents/validator_executor.py
"""
Validator Executor - 信頼度検証エージェント（完全版）

元の全機能を保持し、KeyRegistry対応のみを追加した完全版です。
削除された機能: なし
追加された機能: KeyRegistry統合のみ
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry  # ← 追加
import json


class ValidatorExecutor(BaseAgentExecutor):
    """段階間連携型信頼度検証エージェント（JSON設定完全対応+KeyRegistry統合）"""
    
    def __init__(self, log_manager, threshold_manager, llm_manager):
        super().__init__("validator", log_manager, threshold_manager)
        self.llm_manager = llm_manager
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """段階間連携信頼度検証実行（JSON設定完全依存版）"""
        try:
            node_id = node_id or self._node_config.get("node_id", "unknown")
            
            # JSON設定値取得（エラー時は即座に失敗）
            confidence_threshold = self._get_threshold("confidence_threshold")
            retriever_weight = self._get_threshold("retriever_weight")
            expert_weight = self._get_threshold("expert_weight")
            llm_weight = self._get_threshold("llm_weight")
            rule_weight = self._get_threshold("rule_weight")
            
            self._log(LogLevel.MINIMAL, "段階間連携検証開始", node_id)
            
            # 検証対象データ収集（統合データ使用）
            validation_data = self._collect_validation_data(current_data)
            
            if not validation_data["has_sufficient_data"]:
                return self._create_error_result("検証データ不足", node_id)
            
            # 前段階信頼度取得（修正版：実際の値を正確に取得）
            retriever_confidence = validation_data["retriever_confidence"]
            expert_confidence = validation_data["expert_confidence"]
            
            # VERBOSEレベル時のみ詳細ログ（キー名修正）
            validator_key = f"validator_{node_id}"
            is_verbose = (hasattr(self.log, '_agent_levels') and 
                         (self.log._agent_levels.get('validator') == LogLevel.VERBOSE or
                          self.log._agent_levels.get(validator_key) == LogLevel.VERBOSE))
            
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"前段階信頼度: Retriever={retriever_confidence:.3f}, Expert={expert_confidence:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"JSON設定重み: retriever={retriever_weight:.2f}, expert={expert_weight:.2f}, llm={llm_weight:.2f}, rule={rule_weight:.2f}", node_id)
                self._log(LogLevel.VERBOSE, f"信頼度閾値: {confidence_threshold:.2f}", node_id)
            
            # ルールベース検証
            rule_issues, rule_metrics = self._comprehensive_rule_validation(validation_data)
            
            # VERBOSEレベル時のみルール検証詳細
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"ルール検証: {len(rule_issues)}件問題, 引用整合率={rule_metrics['citation_integrity_rate']:.2f}", node_id)
            
            # LLM検証（JSON設定適用）
            llm_validation = self._llm_quality_assessment(validation_data)
            llm_confidence_raw = llm_validation.get("confidence", 0.7)
            
            # 段階間連携信頼度計算（JSON設定パラメータ使用）
            overall_confidence = self._calculate_cascaded_confidence(
                retriever_confidence, expert_confidence, llm_confidence_raw, 
                rule_metrics, len(rule_issues), retriever_weight, expert_weight, llm_weight, rule_weight
            )
            
            # 検証合格判定
            validation_passed = len(rule_issues) == 0 and overall_confidence >= confidence_threshold
            
            # 履歴レコード作成
            validation_record = {
                "node_id": node_id,
                "validation_passed": validation_passed,
                "overall_confidence": overall_confidence,
                "issues_count": len(rule_issues),
                "rule_metrics": rule_metrics,
                "timestamp": "current"
            }
            
            # 出力データ構築（KeyRegistry使用） ← 修正箇所
            output_data = self._build_validation_output(
                validation_passed, rule_issues, overall_confidence, 
                llm_validation.get("evidence_assessment", "中程度の証拠"), 
                confidence_threshold, rule_metrics, node_id
            )
            
            # 履歴追加
            output_data["validation_history"] = self._update_history(current_data, validation_record, "validation_history")
            
            self._log(LogLevel.MINIMAL, f"段階間連携検証完了: {'合格' if validation_passed else '不合格'}, 信頼度: {overall_confidence:.2f} (閾値: {confidence_threshold:.2f})", node_id)
            
            # VERBOSEレベル時のみ詳細ログ（デバッグ用）
            if is_verbose:
                retriever_impact = retriever_confidence * retriever_weight
                expert_impact = expert_confidence * expert_weight
                llm_impact = llm_confidence_raw * llm_weight
                rule_impact = rule_metrics.get("integrated_rule_score", 0.8) * rule_weight
                total_before_normalization = retriever_impact + expert_impact + llm_impact + rule_impact
                
                self._log(LogLevel.VERBOSE, f"信頼度計算詳細:", node_id)
                self._log(LogLevel.VERBOSE, f"  Retriever影響: {retriever_confidence:.3f} × {retriever_weight:.2f} = {retriever_impact:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"  Expert影響: {expert_confidence:.3f} × {expert_weight:.2f} = {expert_impact:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"  LLM検証: {llm_confidence_raw:.3f} × {llm_weight:.2f} = {llm_impact:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"  ルールスコア: {rule_metrics.get('integrated_rule_score', 0.8):.3f} × {rule_weight:.2f} = {rule_impact:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"  合計(正規化前): {total_before_normalization:.3f}", node_id)
                self._log(LogLevel.VERBOSE, f"  最終信頼度: {overall_confidence:.3f} (閾値: {confidence_threshold:.2f})", node_id)
                
                # 合格/不合格の判定理由
                if overall_confidence >= confidence_threshold:
                    self._log(LogLevel.VERBOSE, f"✅ 検証合格: 信頼度 {overall_confidence:.3f} >= 閾値 {confidence_threshold:.2f}", node_id)
                else:
                    shortage = confidence_threshold - overall_confidence
                    self._log(LogLevel.VERBOSE, f"❌ 検証不合格: 信頼度 {overall_confidence:.3f} < 閾値 {confidence_threshold:.2f} (不足: {shortage:.3f})", node_id)
                    
                    # 不合格要因の分析
                    low_factors = []
                    if retriever_impact < 0.1:
                        low_factors.append(f"Retriever影響低 ({retriever_impact:.3f})")
                    if expert_impact < 0.3:
                        low_factors.append(f"Expert影響低 ({expert_impact:.3f})")
                    if llm_impact < 0.15:
                        low_factors.append(f"LLM検証低 ({llm_impact:.3f})")
                    if rule_impact < 0.05:
                        low_factors.append(f"ルールスコア低 ({rule_impact:.3f})")
                    
                    if low_factors:
                        self._log(LogLevel.VERBOSE, f"  不合格要因: {'; '.join(low_factors)}", node_id)
                    
                    # 改善提案
                    improvement_suggestions = []
                    if retriever_confidence < 0.7:
                        improvement_suggestions.append("検索品質向上が必要")
                    if expert_confidence < 0.6:
                        improvement_suggestions.append("専門分析の品質向上が必要")
                    if len(rule_issues) > 0:
                        improvement_suggestions.append(f"ルール違反の修正が必要 ({len(rule_issues)}件)")
                    
                    if improvement_suggestions:
                        self._log(LogLevel.VERBOSE, f"  改善提案: {'; '.join(improvement_suggestions)}", node_id)
            
            return self._create_result(confidence=overall_confidence, data=output_data)
            
        except KeyError as e:
            error_msg = f"JSON設定不足: {str(e)}"
            self._log(LogLevel.MINIMAL, error_msg, node_id)
            return self._create_error_result(error_msg, node_id)
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"検証エラー: {str(e)}", node_id)
            return self._create_error_result(str(e), node_id)
    
    def _collect_validation_data(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """ノード固有キーからの統合データ収集（Expert信頼度修正版）"""
        all_facts = []
        all_insights = []
        all_recommendations = []
        search_results = []
        expert_confidences = []
        retriever_confidences = []
        latest_analysis = ""
        
        for key, value in current_data.items():
            if key.startswith("facts_") and isinstance(value, list):
                all_facts.extend(value)
            elif key.startswith("insights_") and isinstance(value, list):
                all_insights.extend(value)
            elif key.startswith("recommendations_") and isinstance(value, list):
                all_recommendations.extend(value)
            elif key.startswith("search_results_") and isinstance(value, list):
                search_results.extend(value)
            elif key.startswith("analysis_") and isinstance(value, str):
                latest_analysis = value
            elif key.startswith("confidence_") and isinstance(value, (int, float)):
                # ノードIDが2桁以上の場合も対応
                node_part = key[11:]  # "confidence_"以降
                if node_part and node_part.isdigit():
                    node_id = int(node_part)
                    if node_id >= 4:  # Expert範囲（Domain Expert）
                        expert_confidences.append(float(value))
                    elif node_id >= 2 and node_id <= 3:  # Retriever範囲
                        retriever_confidences.append(float(value))
        
        # 平均信頼度計算（フォールバック処理）
        avg_retriever_conf = sum(retriever_confidences) / len(retriever_confidences) if retriever_confidences else 0.5
        avg_expert_conf = sum(expert_confidences) / len(expert_confidences) if expert_confidences else 0.5
        
        # 引用情報の抽出（検索結果から）
        citations = []
        for i, result in enumerate(search_results):
            citations.append({
                "id": f"cite_{i}",
                "source": result.get("source", "unknown"),
                "content": result.get("content", "")[:100]
            })
        
        return {
            "facts": [{"statement": f, "cite_ids": []} for f in all_facts],
            "insights": all_insights,
            "recommendations": all_recommendations,
            "citations": citations,
            "search_results": search_results,
            "user_query": current_data.get("user_input", ""),
            "expert_analysis": latest_analysis,
            "retriever_confidence": avg_retriever_conf,
            "expert_confidence": avg_expert_conf,
            "has_sufficient_data": len(search_results) > 0 or len(all_facts) > 0
        }
    
    def _get_latest_expert_analysis(self, current_data: Dict[str, Any]) -> str:
        """最新のExpert分析を取得（ノードID順でソート）"""
        analysis_entries = []
        
        for key, value in current_data.items():
            if key.startswith("analysis_") and isinstance(value, str):
                node_id_str = key[9:]  # "analysis_"以降
                if node_id_str.isdigit():
                    analysis_entries.append((int(node_id_str), value))
        
        # ノードID順でソート、最新（最大ID）を取得
        if analysis_entries:
            analysis_entries.sort(key=lambda x: x[0], reverse=True)
            latest_analysis = analysis_entries[0][1]
            return latest_analysis
        
        # フォールバック：最新処理された分析が最新
        return latest_analysis or current_data.get("expert_analysis", "")
    
    def _comprehensive_rule_validation(self, data: Dict[str, Any]) -> tuple:
        """包括的ルールベース検証（定量メトリクス付き）"""
        issues = []
        metrics = {}
        
        # 引用整合性の定量評価
        citation_ids = {c.get("id", "") for c in data["citations"]}
        total_citations = sum(len(fact.get("cite_ids", [])) for fact in data["facts"])
        valid_citations = 0
        
        for fact in data["facts"]:
            for cite_id in fact.get("cite_ids", []):
                if cite_id in citation_ids:
                    valid_citations += 1
                else:
                    issues.append(f"引用ID不整合: {cite_id}")
        
        metrics["citation_integrity_rate"] = valid_citations / max(total_citations, 1)
        
        # 論理整合性評価（より厳格に）
        logical_consistency_score = 0.8  # デフォルトを低めに設定
        if not data["insights"] and data["recommendations"]:
            issues.append("根拠なし推奨事項")
            logical_consistency_score = 0.5
        elif len(data["facts"]) == 0:
            issues.append("事実情報不足")
            logical_consistency_score = 0.6
        elif len(data["insights"]) == 0 and len(data["facts"]) > 3:
            issues.append("事実に対する洞察不足")
            logical_consistency_score = 0.7
        
        metrics["logical_consistency_score"] = logical_consistency_score
        
        # 情報源充足率
        min_sources = self._get_threshold("minimum_source_count")
        actual_sources = len(data["search_results"])
        source_adequacy = min(actual_sources / min_sources, 1.0)
        
        if source_adequacy < 1.0:
            issues.append("情報源不足")
        
        metrics["source_adequacy_rate"] = source_adequacy
        
        self._log(LogLevel.VERBOSE, f"ルール検証詳細: 引用整合={metrics['citation_integrity_rate']:.2f}, 論理整合={metrics['logical_consistency_score']:.2f}, 情報源充足={metrics['source_adequacy_rate']:.2f}")
        
        return issues, metrics
    
    def _llm_quality_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """LLM品質評価（JSON設定完全依存）"""
        validation_prompt = self._build_validation_prompt(data)
        
        # VERBOSEレベル時のプロンプト表示
        validator_key = f"validator_{self._node_config.get('node_id', 'unknown')}"
        is_verbose = (hasattr(self.log, '_agent_levels') and 
                     (self.log._agent_levels.get('validator') == LogLevel.VERBOSE or
                      self.log._agent_levels.get(validator_key) == LogLevel.VERBOSE))
        
        if is_verbose:
            self._log(LogLevel.VERBOSE, "=== Validator LLMプロンプト ===")
            self._log(LogLevel.VERBOSE, f"プロンプト内容:\n{validation_prompt}")
            self._log(LogLevel.VERBOSE, "=== プロンプト終了 ===")
        
        try:
            llm_max_tokens = self._get_threshold("llm_max_tokens")
            llm_response = self.llm_manager.get_response(validation_prompt, max_tokens=llm_max_tokens)
            
            # VERBOSEレベル時のLLM応答表示
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"=== Validator LLM応答 ===")
                self._log(LogLevel.VERBOSE, f"応答内容:\n{llm_response}")
                self._log(LogLevel.VERBOSE, "=== 応答終了 ===")
            
            return self._parse_llm_validation(llm_response)
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"LLM検証エラー: {str(e)}")
            return {"issues": [], "confidence": 0.5, "evidence_assessment": "不明"}
    
    def _build_validation_prompt(self, data: Dict[str, Any]) -> str:
        """LLM検証プロンプト構築（最終プロンプトテンプレート対応版）"""
        
        # JSON設定から必須プロンプト要素取得（フォールバックなし）
        prompts = self._get_threshold("llm_prompts")
        
        # 最終プロンプトテンプレートが設定されている場合はそれを使用
        if "final_prompt_template" in prompts:
            final_template = prompts["final_prompt_template"]
            
            # テンプレート変数を置換
            facts_summary = "; ".join([f.get("statement", "")[:50] for f in data["facts"][:3]])
            insights_summary = "; ".join(data["insights"][:3])
            
            # 各プロンプト要素を取得
            validation_instruction = prompts.get("validation_instruction", "")
            evaluation_criteria = prompts.get("evaluation_criteria", "")
            output_format = prompts.get("output_format", "")
            confidence_calculation = prompts.get("confidence_calculation", "")
            
            # テンプレート内の変数を置換
            return final_template.format(
                validation_instruction=validation_instruction,
                evaluation_criteria=evaluation_criteria,
                output_format=output_format,
                confidence_calculation=confidence_calculation,
                user_query=data['user_query'][:100],
                facts_summary=facts_summary,
                insights_summary=insights_summary
            )
        else:
            # 従来のフォーマット（後方互換性）
            validation_instruction = prompts["validation_instruction"]
            evaluation_criteria = prompts["evaluation_criteria"]
            output_format = prompts["output_format"]
            confidence_calculation = prompts["confidence_calculation"]
            
            facts_summary = "; ".join([f.get("statement", "")[:50] for f in data["facts"][:3]])
            insights_summary = "; ".join(data["insights"][:3])
            
            return f"""{validation_instruction}

質問: "{data['user_query'][:100]}"
事実: {facts_summary}
洞察: {insights_summary}

【評価基準】
{evaluation_criteria}

【信頼度計算指針】
{confidence_calculation}

{output_format}:
{{
"issues": ["品質問題があれば記述、問題なければ空配列"],
"confidence": 0.75,
"evidence_assessment": "強い証拠|中程度の証拠|弱い証拠"
}}"""
    
    def _parse_llm_validation(self, response: str) -> Dict[str, Any]:
        """LLM応答解析"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                result = json.loads(response[start:end])
                return {
                    "issues": result.get("issues", []),
                    "confidence": float(result.get("confidence", 0.7)),
                    "evidence_assessment": result.get("evidence_assessment", "中程度の証拠")
                }
        except:
            pass
        
        return {"issues": [], "confidence": 0.7, "evidence_assessment": "中程度の証拠"}
    
    def _calculate_cascaded_confidence(self, retriever_conf: float, expert_conf: float, 
                                    llm_conf: float, rule_metrics: Dict[str, float], 
                                    issue_count: int, retriever_weight: float, expert_weight: float,
                                    llm_weight: float, rule_weight: float) -> float:
        """段階間連携信頼度計算（修正版：計算透明性確保）"""
        # ルールメトリクスから統合スコア計算
        citation_integrity = rule_metrics.get("citation_integrity_rate", 0.0)
        logical_consistency = rule_metrics.get("logical_consistency_score", 0.0)
        source_adequacy = rule_metrics.get("source_adequacy_rate", 0.0)
        
        rule_score = (citation_integrity * 0.4 + logical_consistency * 0.3 + source_adequacy * 0.3)
        
        # 問題件数による減点
        issue_penalty = min(issue_count * 0.05, 0.3)
        rule_score = max(rule_score - issue_penalty, 0.0)
        
        # 統合計算（JSON設定の重みを正確に使用）
        weighted_confidence = (
            retriever_conf * retriever_weight +
            expert_conf * expert_weight + 
            llm_conf * llm_weight +
            rule_score * rule_weight
        )
        
        # メトリクスに統合ルールスコアを保存（ログ用）
        rule_metrics["integrated_rule_score"] = rule_score
        
        return max(min(weighted_confidence, 1.0), 0.0)
    
    def _build_validation_output(self, passed: bool, issues: List[str], confidence: float, 
                            evidence: str, threshold: float, metrics: Dict[str, float], node_id: str) -> Dict[str, Any]:
        """完全ノード固有化検証結果出力（KeyRegistry使用）"""  # ← 修正箇所
        node_id_str = str(node_id)
        
        # KeyRegistryから各キー名を取得
        result_key = KeyRegistry.get_key_name("validator", "validation_result", node_id_str)
        confidence_key = KeyRegistry.get_key_name("validator", "validation_confidence", node_id_str)
        passed_key = KeyRegistry.get_key_name("validator", "validation_passed", node_id_str)
        details_key = KeyRegistry.get_key_name("validator", "validation_details", node_id_str)
        
        return {
            # KeyRegistry使用の新形式キー
            result_key: {
                "passed": passed,
                "confidence": confidence,
                "threshold": threshold,
                "evidence_assessment": evidence
            },
            confidence_key: confidence,
            passed_key: passed,
            details_key: {
                "issues": issues,
                "metrics": metrics,
                "threshold": threshold
            },
            
            # 後方互換性キー（将来削除予定だが機能喪失を避けるため保持）
            "validation_passed": passed,
            "identified_issues": issues,
            "missing_information": [i for i in issues if "不足" in i],
            "improvement_suggestions": self._generate_improvement_suggestions(confidence, metrics, issues),
            "overall_confidence": confidence,
            "validation_scores": {
                "citation_integrity": metrics.get("citation_integrity_rate", 0.0),
                "logical_consistency": metrics.get("logical_consistency_score", 0.0),
                "source_adequacy": metrics.get("source_adequacy_rate", 0.0),
                "integrated_score": metrics.get("integrated_rule_score", 0.0)
            },
            "validation_method": "cascaded",
            "evidence_assessment": evidence,
            "validator_has_error": False,
            "validator_config": {
                "node_id": node_id_str,
                "threshold": threshold
            }
        }
    
    def _generate_improvement_suggestions(self, confidence: float, metrics: Dict[str, float], issues: List[str]) -> List[str]:
        """改善提案生成"""
        suggestions = []
        
        if confidence < 0.5:
            suggestions.append("全体的な品質向上が必要")
        
        if metrics.get("citation_integrity_rate", 1.0) < 0.7:
            suggestions.append("引用の整合性を改善")
        
        if metrics.get("logical_consistency_score", 1.0) < 0.6:
            suggestions.append("論理的一貫性を強化")
        
        if metrics.get("source_adequacy_rate", 1.0) < 0.8:
            suggestions.append("より多くの情報源を追加")
        
        if len(issues) > 3:
            suggestions.append(f"検出された{len(issues)}件の問題を優先的に修正")
        
        return suggestions if suggestions else ["品質は許容範囲内"]
    
    def _create_error_result(self, error_msg: str, node_id: str = "unknown") -> AgentResult:
        """エラー結果生成（ノードID対応版+KeyRegistry使用）"""  # ← 修正箇所
        node_id_str = str(node_id)
        
        error_data = {
            # KeyRegistry使用の新形式キー
            KeyRegistry.get_key_name("validator", "validation_result", node_id_str): {
                "passed": False,
                "confidence": 0.0,
                "error": error_msg
            },
            KeyRegistry.get_key_name("validator", "validation_confidence", node_id_str): 0.0,
            KeyRegistry.get_key_name("validator", "validation_passed", node_id_str): False,
            KeyRegistry.get_key_name("validator", "validation_details", node_id_str): {
                "error": error_msg
            },
            
            # 後方互換性キー（機能喪失を避けるため保持）
            "validation_passed": False,
            "identified_issues": [f"検証エラー: {error_msg}"],
            "missing_information": ["検証処理"],
            "improvement_suggestions": ["システム管理者に問い合わせてください"],
            "overall_confidence": 0.0,
            "validation_scores": {
                "citation_integrity": 0.0,
                "logical_consistency": 0.0,
                "source_adequacy": 0.0,
                "integrated_score": 0.0
            },
            "validation_method": "error",
            "evidence_assessment": "不明",
            "validator_has_error": True,
            "validation_history": [],
            "validator_config": {
                "node_id": node_id_str,
                "error": error_msg
            }
        }
        return self._create_result(0.0, error_data, has_error=True, status="error")