# utils/agents/refiner_executor.py
"""
Refiner Executor - 統合回答生成エージェント(完全版)

KeyRegistry統合版。旧形式のキーは一切サポートしません。
全機能を保持し、KeyRegistry対応のみを追加した完全版です。
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgentExecutor, AgentResult
from utils.log_manager import LogLevel
from utils.key_registry import KeyRegistry
import json


class RefinerExecutor(BaseAgentExecutor):
    def _create_error_result(self, error_message: str, node_id: Optional[str] = None) -> AgentResult:
        """Refiner用エラー結果生成"""
        refined_answer_key = KeyRegistry.get_key_name("refiner", "refined_answer")
        refined_answer_node_key = KeyRegistry.get_key_name("refiner", "refined_answer_node", node_id or "refiner")
        metadata_key = KeyRegistry.get_key_name("refiner", "refiner_metadata", node_id or "refiner")
        output_data = {
            refined_answer_key: None,
            refined_answer_node_key: None,
            metadata_key: {
                "error": error_message
            },
            "next_node": None
        }
        return self._create_result(
            confidence=0.0,
            data=output_data
        )
    """汎用統合回答生成エージェント(KeyRegistry完全対応)"""
    
    def __init__(self, log_manager, threshold_manager, llm_manager):
        super().__init__("refiner", log_manager, threshold_manager)
        self.llm_manager = llm_manager
    
    def _get_node_type(self, node_id: str) -> Optional[str]:
        """指定ノードのタイプを取得"""
        try:
            system_config = self.thresholds.get_system_config()
            nodes = system_config.get("nodes", [])
            for node in nodes:
                if str(node.get("id")) == str(node_id):
                    return node.get("type")
            return None
        except Exception:
            return None
    
    def _get_domain_expert_node_ids(self) -> List[str]:
        """DomainExpertタイプのノードIDリストを取得"""
        try:
            system_config = self.thresholds.get_system_config()
            nodes = system_config.get("nodes", [])
            domain_expert_ids = []
            for node in nodes:
                if node.get("type") == "domain_expert":
                    domain_expert_ids.append(str(node.get("id")))
            return domain_expert_ids
        except Exception:
            return []
    
    def execute(self, current_data: Dict[str, Any], node_id: Optional[str] = None, **kwargs) -> AgentResult:
        """全DomainExpert出力統合型回答生成"""
        try:
            node_id = node_id or self._node_config.get("node_id", "unknown")
            user_input = current_data.get("user_input", "")
            
            self._log(LogLevel.MINIMAL, "統合回答生成開始", node_id)
            
            # JSON設定値取得
            min_length = self._get_threshold("min_answer_length")
            max_length = self._get_threshold("max_answer_length")
            output_structure = self._get_threshold("output_structure")
            llm_prompts = self._get_threshold("llm_prompts")
            
            # formatting_rulesはoutput_structure内に含まれている
            formatting_rules = output_structure.get("formatting_rules", {}) if isinstance(output_structure, dict) else {}
            
            # DomainExpertノード出力を統合収集
            expert_outputs = self._collect_expert_outputs(current_data)
            
            if not expert_outputs:
                self._log(LogLevel.MINIMAL, "専門家データなし: 基本回答生成", node_id)
                return self._generate_basic_answer(user_input, node_id)
            
            # VERBOSEレベル判定
            log_name = f"refiner_{node_id}"
            is_verbose = self.log.should_log(log_name, LogLevel.VERBOSE)
            
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"収集した専門家数: {len(expert_outputs)}", node_id)
                self._log(LogLevel.VERBOSE, f"出力構造: {output_structure}", node_id)
            
            # プロンプト構築
            prompt = self._build_refinement_prompt(
                user_input,
                expert_outputs,
                min_length,
                max_length,
                output_structure,
                formatting_rules,
                llm_prompts
            )
            
            if is_verbose:
                self._log(LogLevel.VERBOSE, f"生成プロンプト長: {len(prompt)} 文字", node_id)
            
            # LLM呼び出し
            llm_response = self.llm_manager.get_response(prompt, max_tokens=max_length)
            
            if not llm_response:
                return self._create_error_result("LLM応答なし", node_id)
            
            self._log(LogLevel.MINIMAL, f"統合回答生成完了: {len(llm_response)} 文字", node_id)
            
            # KeyRegistryを使用して出力キー生成
            refined_answer_key = KeyRegistry.get_key_name("refiner", "refined_answer")
            refined_answer_node_key = KeyRegistry.get_key_name("refiner", "refined_answer_node", node_id)
            metadata_key = KeyRegistry.get_key_name("refiner", "refiner_metadata", node_id)
            
            output_data = {
                refined_answer_key: llm_response,
                refined_answer_node_key: llm_response,
                metadata_key: {
                    "expert_count": len(expert_outputs),
                    "answer_length": len(llm_response),
                    "structure_type": output_structure.get("type", "unknown")
                }
            }
            
            return self._create_result(confidence=1.0, data=output_data)
            
        except Exception as e:
            self._log(LogLevel.MINIMAL, f"統合生成エラー: {str(e)}", node_id)
            return self._create_error_result(str(e), node_id)
    
    def _collect_expert_outputs(self, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """全DomainExpert出力を収集(KeyRegistry対応)"""
        expert_outputs = []
        
        # DomainExpertノードIDを取得
        expert_node_ids = self._get_domain_expert_node_ids()
        
        for expert_id in expert_node_ids:
            # KeyRegistryを使用して各キーを取得
            analysis_key = KeyRegistry.get_key_name("domain_expert", "analysis", expert_id)
            facts_key = KeyRegistry.get_key_name("domain_expert", "facts", expert_id)
            insights_key = KeyRegistry.get_key_name("domain_expert", "insights", expert_id)
            recommendations_key = KeyRegistry.get_key_name("domain_expert", "recommendations", expert_id)
            confidence_key = KeyRegistry.get_key_name("domain_expert", "confidence", expert_id)
            gaps_key = KeyRegistry.get_key_name("domain_expert", "gaps", expert_id)
            
            # データが存在するか確認
            if analysis_key in current_data:
                expert_data = {
                    "node_id": expert_id,
                    "analysis": current_data.get(analysis_key, ""),
                    "facts": current_data.get(facts_key, []),
                    "insights": current_data.get(insights_key, []),
                    "recommendations": current_data.get(recommendations_key, []),
                    "confidence": current_data.get(confidence_key, 0.0),
                    "gaps": current_data.get(gaps_key, [])
                }
                expert_outputs.append(expert_data)
        
        return expert_outputs
    
    def _build_refinement_prompt(
        self,
        user_input: str,
        expert_outputs: List[Dict[str, Any]],
        min_length: int,
        max_length: int,
        output_structure: Dict[str, Any],
        formatting_rules: Dict[str, Any],
        llm_prompts: Dict[str, Any]
    ) -> str:
        """統合プロンプト構築"""
        # 基本指示
        base_instruction = llm_prompts.get("document_generation", "包括的な技術文書を生成してください。")
        quality_focus = llm_prompts.get("content_refinement", "内容の質を重視してください。")
        format_instruction = llm_prompts.get("formatting_rules", "適切な形式で出力してください。")
        
        # 専門家データ統合
        expert_content = self._format_expert_outputs(expert_outputs)
        
        # フォーマットルール
        format_rules = self._build_formatting_rules(formatting_rules)
        
        # 出力構造指示
        structure_instruction = self._build_structure_instruction(output_structure)
        
        prompt = f"""{base_instruction}

【質問】
{user_input}

【専門家分析結果】
{expert_content}

【品質要件】
{quality_focus}

【出力構造】
{structure_instruction}

【フォーマット規則】
{format_rules}
{format_instruction}

【文字数制約】
最小: {min_length}文字
最大: {max_length}文字

上記の全ての情報を統合し、構造化された包括的な回答を生成してください。
"""
        return prompt
    
    def _format_expert_outputs(self, expert_outputs: List[Dict[str, Any]]) -> str:
        """専門家出力をフォーマット"""
        if not expert_outputs:
            return "専門家データなし"
        
        content_lines = []
        
        for i, data in enumerate(expert_outputs, 1):
            node_id = data.get("node_id", "unknown")
            content_lines.append(f"\n=== 専門家 {i} (Node {node_id}) ===")
            
            # 分析内容
            if "analysis" in data and data["analysis"]:
                content_lines.append(f"\n【分析】\n{data['analysis']}")
            
            # 事実
            if "facts" in data and data["facts"]:
                content_lines.append("\n【事実】")
                for j, fact in enumerate(data["facts"][:10], 1):
                    content_lines.append(f"{j}. {fact}")
            
            # 洞察
            if "insights" in data and data["insights"]:
                content_lines.append("\n【洞察】")
                for j, insight in enumerate(data["insights"][:10], 1):
                    content_lines.append(f"{j}. {insight}")
            
            # 推奨事項
            if "recommendations" in data and data["recommendations"]:
                content_lines.append("\n【推奨事項】")
                for j, rec in enumerate(data["recommendations"][:10], 1):
                    content_lines.append(f"{j}. {rec}")
            
            # 不足情報
            if "gaps" in data and data["gaps"]:
                content_lines.append("\n【不足情報】")
                for j, gap in enumerate(data["gaps"][:5], 1):
                    content_lines.append(f"{j}. {gap}")
            
            # 信頼度
            if "confidence" in data:
                content_lines.append(f"\n【信頼度】{data['confidence']:.2f}")
            
            content_lines.append("")
        
        return "\n".join(content_lines)
    
    def _build_formatting_rules(self, formatting_rules: Dict[str, Any]) -> str:
        """フォーマット規則文字列生成"""
        rules = []
        
        if formatting_rules.get("use_code_blocks", False):
            rules.append("- コードブロックを適切に使用")
        
        if formatting_rules.get("include_citations", False):
            rules.append("- 引用情報を適切に含める")
        
        if formatting_rules.get("structure_with_headers", False):
            rules.append("- ヘッダーで構造化")
        
        terminology = formatting_rules.get("technical_terminology", "preserve")
        if terminology == "preserve":
            rules.append("- 技術用語を保持")
        elif terminology == "simplify":
            rules.append("- 技術用語を簡単に説明")
        
        if formatting_rules.get("expert_attribution", False):
            rules.append("- 専門家の分析結果を適切に帰属")
        
        return "\n".join(rules) if rules else "標準フォーマット"
    
    def _build_structure_instruction(self, output_structure: Dict[str, Any]) -> str:
        """出力構造指示生成"""
        structure_type = output_structure.get("type", "standard")
        sections = output_structure.get("sections", [])
        
        if not sections:
            return f"タイプ: {structure_type}（セクション指定なし）"
        
        instruction_lines = [f"タイプ: {structure_type}", "\n【セクション構成】"]
        
        for section in sections:
            section_id = section.get("id", "unknown")
            title = section.get("title", "無題")
            content_type = section.get("content_type", "summary")
            target_ratio = section.get("target_length_ratio", 10)
            
            instruction_lines.append(
                f"- {title} ({section_id}): {content_type}形式、長さ比率{target_ratio}%"
            )
        
        return "\n".join(instruction_lines)
    
    def _generate_basic_answer(self, user_input: str, node_id: str) -> AgentResult:
        """基本回答生成（DomainExpert不在時も設定を活用）
        
        DomainExpertが不在の場合でも、以下の設定を活用してプロンプトを構築：
        - llm_prompts（5つのプロンプト）
        - output_structure（セクション構成）
        - formatting_rules（フォーマット規則）
        - 文字数制約
        
        これにより、DomainExpert不在でもユーザー設定が機能します。
        """
        # 設定値を取得
        min_length = self._get_threshold("min_answer_length")
        max_length = self._get_threshold("max_answer_length")
        output_structure = self._get_threshold("output_structure")
        llm_prompts = self._get_threshold("llm_prompts")
        formatting_rules = output_structure.get("formatting_rules", {}) if isinstance(output_structure, dict) else {}
        
        # 新形式のllm_promptsから指示を取得（空でも許可）
        generation_instruction = llm_prompts.get("generation_instruction", "")
        section_instruction = llm_prompts.get("section_instruction", "")
        output_format = llm_prompts.get("output_format", "")
        integration_focus = llm_prompts.get("integration_focus", "")
        code_generation_focus = llm_prompts.get("code_generation_focus", "")
        
        # 出力構造指示を構築（既存メソッドを再利用）
        structure_instruction = self._build_structure_instruction(output_structure)
        
        # フォーマット規則を構築（既存メソッドを再利用）
        format_rules = self._build_formatting_rules(formatting_rules)
        
        # プロンプト構築（設定を活用）
        prompt_parts = []
        
        # 基本生成指示（設定されていればそれを使用、なければデフォルト）
        if generation_instruction:
            prompt_parts.append(generation_instruction)
        else:
            prompt_parts.append("以下の質問に対して、詳細で構造化された回答を生成してください。")
        
        # 質問セクション
        prompt_parts.append(f"\n\n【質問】\n{user_input}\n")
        
        # セクション構成指示（設定されていれば追加）
        if section_instruction:
            prompt_parts.append(f"【セクション構成指示】\n{section_instruction}\n")
        
        # 出力構造指示（セクション情報を含む）
        if structure_instruction:
            prompt_parts.append(f"【出力構造】\n{structure_instruction}\n")
        
        # フォーマット規則（設定されていれば追加）
        if format_rules:
            prompt_parts.append(f"【フォーマット規則】\n{format_rules}\n")
        
        # 出力形式指示（設定されていれば追加）
        if output_format:
            prompt_parts.append(f"【出力形式】\n{output_format}\n")
        
        # 統合フォーカス（設定されていれば追加）
        if integration_focus:
            prompt_parts.append(f"【統合フォーカス】\n{integration_focus}\n")
        
        # コード生成フォーカス（設定されていれば追加）
        if code_generation_focus:
            prompt_parts.append(f"【コード生成フォーカス】\n{code_generation_focus}\n")
        
        # 文字数制約
        prompt_parts.append(f"【文字数制約】\n最小: {min_length}文字\n最大: {max_length}文字\n")
        
        # 最終指示
        prompt_parts.append("\n専門家の分析データは利用できませんが、上記の指示に従って包括的で構造化された回答を提供してください。")
        
        basic_prompt = "".join(prompt_parts)
        
        # LLM呼び出し
        llm_response = self.llm_manager.get_response(basic_prompt, max_tokens=max_length)
        
        if not llm_response:
            return self._create_error_result("基本回答生成失敗", node_id)
        
        # KeyRegistryを使用して出力キー生成
        refined_answer_key = KeyRegistry.get_key_name("refiner", "refined_answer")
        refined_answer_node_key = KeyRegistry.get_key_name("refiner", "refined_answer_node", node_id)
        metadata_key = KeyRegistry.get_key_name("refiner", "refiner_metadata", node_id)
        
        output_data = {
            refined_answer_key: llm_response,
            refined_answer_node_key: llm_response,
            metadata_key: {
                "expert_count": 0,
                "answer_length": len(llm_response),
                "structure_type": output_structure.get("type", "basic") if isinstance(output_structure, dict) else "basic",
                "mode": "direct_generation"  # DomainExpert不在モード
            }
        }
        
        return self._create_result(confidence=0.8, data=output_data)
