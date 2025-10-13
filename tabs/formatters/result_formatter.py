# tabs/result_formatter.py
import re
import os
import zipfile
import urllib.request
from pathlib import Path
from typing import Dict, Any, Union
from markdown import markdown as md_to_html


class ResultFormatter:
    """結果フォーマット処理クラス"""
    
    def __init__(self):
        self.data_path = Path("data")
        self.assets_path = self.data_path / "assets"
        
    def format_refined_result(self, result_dict: Dict[str, Any]) -> str:
        """ワークフロー結果を整形（新しい統一形式）"""
        if not result_dict:
            return "エラー: 結果が空です。"
        
        if "error" in result_dict:
            return f"エラー: {result_dict['error']}"
        
        # VLM単体時の対応（vlm_answerがある場合）
        execution_summary = result_dict.get("execution_summary", {})
        final_node_type = execution_summary.get("final_node_type", "unknown")
        
        if final_node_type == "vlm" and "vlm_answer" in result_dict:
            header = f"## VLM回答（Vision Language Model）\n\n"
            return header + result_dict["vlm_answer"]
        
        # 新しい統一形式（優先）
        if "refined_answer" in result_dict:
            header = f"## マルチエージェント回答（最終ノード: {final_node_type}）\n\n"
            return header + result_dict["refined_answer"]
        
        # 一時的な下位互換性（将来削除）
        elif "multi_agent_response" in result_dict:
            execution_summary = result_dict.get("execution_summary", {})
            final_node_type = execution_summary.get("final_node_type", "unknown")
            header = f"## マルチエージェント回答（最終ノード: {final_node_type}）\n\n"
            return header + result_dict["multi_agent_response"]
        
        # その他の形式
        elif "validator_result" in result_dict:
            return self._format_validator_result(result_dict["validator_result"])
        elif "combined_experts" in result_dict:
            return self._format_experts_result(result_dict["combined_experts"])
        elif any(key.startswith("expert_") for key in result_dict.keys()):
            return self._format_single_expert_result(result_dict)
        
        # フォールバック
        else:
            return f"未知の結果形式です。\n\n{str(result_dict)}"
    
    def _format_refined_answer(self, refined_answer: str) -> str:
        """精錬された回答の表示"""
        return refined_answer
    
    def _format_validator_result(self, validator_result: Dict[str, Any]) -> str:
        """バリデーター結果の表示"""
        content = []
        
        if "final_answer" in validator_result:
            content.append(validator_result["final_answer"])
        
        if "validation_feedback" in validator_result:
            feedback = validator_result["validation_feedback"]
            content.append(f"\n## 検証結果\n")
            content.append(f"信頼度: {feedback.get('confidence', 'N/A')}")
            
            if feedback.get('issues'):
                content.append("\n### 検出された問題:")
                for issue in feedback['issues']:
                    content.append(f"- {issue}")
            
            if feedback.get('improvement_suggestions'):
                content.append("\n### 改善提案:")
                for suggestion in feedback['improvement_suggestions']:
                    content.append(f"- {suggestion}")
        
        return "\n".join(content)
    
    def _format_experts_result(self, combined_experts: Dict[str, Any]) -> str:
        """複数専門家結果の表示"""
        content = []
        
        if "summary" in combined_experts:
            content.append(f"## 統合分析結果\n{combined_experts['summary']}")
        
        for expert_key, expert_data in combined_experts.items():
            if expert_key != "summary" and isinstance(expert_data, dict):
                expert_name = expert_key.replace("expert_", "").replace("_", " ").title()
                content.append(f"\n## {expert_name}の分析")
                content.append(self._format_expert_content(expert_data))
        
        return "\n".join(content)
    
    def _format_single_expert_result(self, result_dict: Dict[str, Any]) -> str:
        """単一専門家結果の表示"""
        content = []
        
        for key, value in result_dict.items():
            if key.startswith("expert_") and isinstance(value, dict):
                expert_name = key.replace("expert_", "").replace("_", " ").title()
                content.append(f"## {expert_name}の分析")
                content.append(self._format_expert_content(value))
        
        return "\n".join(content)
    
    def _format_expert_content(self, expert_data: Dict[str, Any]) -> str:
        """専門家データの内容フォーマット"""
        content = []
        
        if "answer" in expert_data:
            content.append(f"### 回答\n{expert_data['answer']}")
        
        if "facts" in expert_data:
            content.append("\n### 主要事実")
            facts = expert_data["facts"]
            if isinstance(facts, list):
                content.extend(self._format_list_content(facts))
            else:
                content.append(str(facts))
        
        if "insights" in expert_data:
            content.append("\n### 洞察")
            insights = expert_data["insights"]
            if isinstance(insights, list):
                for insight in insights:
                    content.append(f"- {insight}")
            else:
                content.append(str(insights))
        
        if "recommendations" in expert_data:
            content.append("\n### 推奨事項")
            recommendations = expert_data["recommendations"]
            if isinstance(recommendations, list):
                for rec in recommendations:
                    content.append(f"- {rec}")
            else:
                content.append(str(recommendations))
        
        if "confidence" in expert_data:
            content.append(f"\n**信頼度**: {expert_data['confidence']}")
        
        return "\n".join(content)
    
    def _format_nested_content(self, content_dict: Dict[str, Any]) -> str:
        """ネストされたコンテンツのフォーマット"""
        if not isinstance(content_dict, dict):
            return str(content_dict)
        
        formatted_parts = []
        for key, value in content_dict.items():
            if isinstance(value, dict):
                formatted_parts.append(f"**{key}**: {self._format_nested_content(value)}")
            elif isinstance(value, list):
                formatted_parts.append(f"**{key}**: {self._format_list_content(value)}")
            else:
                formatted_parts.append(f"**{key}**: {value}")
        
        return "; ".join(formatted_parts)
    
    def _format_list_content(self, content_list: list) -> list:
        """リストコンテンツのフォーマット"""
        formatted_items = []
        for item in content_list:
            if isinstance(item, dict):
                formatted_items.append(f"- {self._format_nested_content(item)}")
            else:
                formatted_items.append(f"- {item}")
        return formatted_items
    
    def _format_legacy_result(self, result_dict: Dict[str, Any]) -> str:
        """従来形式の結果を整形（元のユーザータブロジックから移行）"""
        formatted_lines = []
        
        # === 追加: Retrieverが最終ノードの場合の検索結果表示 ===
        retriever_results = {}
        for key, value in result_dict.items():
            if key.startswith("search_results_") and isinstance(value, list):
                node_id = key.split("_")[-1]
                retriever_results[node_id] = value
        
        # Retrieverが最終ノードの場合、検索結果を詳細表示
        if retriever_results and not any(key.startswith("final_answer_") for key in result_dict.keys()):
            formatted_lines.append("【RAG検索結果】")
            formatted_lines.append("") 
            
            for node_id, search_results in retriever_results.items():
                formatted_lines.append(f"リトリーバー{node_id}の検索結果（{len(search_results)}件）:")
                formatted_lines.append("")
                
                for i, result in enumerate(search_results[:5], 1):  # 上位5件を表示
                    score = result.get("score", 0)
                    content = result.get("content", "")
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                    
                    formatted_lines.append(f"  {i}. スコア: {score:.4f}")
                    formatted_lines.append(f"     内容: {content_preview}")
                    
                    metadata = result.get("metadata", {})
                    if metadata:
                        formatted_lines.append(f"     メタデータ: {metadata}")
                    formatted_lines.append("")
            
            return "\n".join(formatted_lines)
        
        # === 既存のRefiner結果表示 ===
        # 最終回答の表示
        final_answer = None
        final_confidence = 0.0
        answer_structure = None
        
        for key, value in result_dict.items():
            if key.startswith("final_answer_") and isinstance(value, str):
                final_answer = value
            elif key.startswith("confidence_") and isinstance(value, (int, float)):
                final_confidence = max(final_confidence, float(value))
            elif key.startswith("answer_structure_") and isinstance(value, dict):
                answer_structure = value
        
        if final_answer:
            formatted_lines.append("【最終回答】")
            formatted_lines.append(final_answer)
            formatted_lines.append("")
        
        # Retriever詳細情報の表示
        retriever_tracking = None
        for key, value in result_dict.items():
            if key.startswith("retriever_tracking_") and isinstance(value, dict):
                retriever_tracking = value
                break
        
        if retriever_tracking:
            formatted_lines.append("【参照データソース詳細】")
            
            ast_info = retriever_tracking.get("ast_retriever", {})
            pdf_info = retriever_tracking.get("pdf_retriever", {})
            
            if ast_info:
                formatted_lines.append(f"AST構造検索（ノード{ast_info.get('node_id', '?')}）:")
                formatted_lines.append(f"  - 取得件数: {ast_info.get('results_count', 0)}件")
                formatted_lines.append(f"  - 信頼度: {ast_info.get('confidence', 0):.3f}")
                formatted_lines.append(f"  - コレクション: {ast_info.get('collection', 'unknown')}")
                formatted_lines.append(f"  - 再ランク処理: {'使用' if ast_info.get('reranker_used') else '未使用'}")
            
            if pdf_info:
                formatted_lines.append(f"PDF文献検索（ノード{pdf_info.get('node_id', '?')}）:")
                formatted_lines.append(f"  - 取得件数: {pdf_info.get('results_count', 0)}件")
                formatted_lines.append(f"  - 信頼度: {pdf_info.get('confidence', 0):.3f}")
                formatted_lines.append(f"  - コレクション: {pdf_info.get('collection', 'unknown')}")
                formatted_lines.append(f"  - 再ランク処理: {'使用' if pdf_info.get('reranker_used') else '未使用'}")
            
            formatted_lines.append("")
        
        # 統合品質情報（修正版）
        if answer_structure:
            formatted_lines.append("【統合品質情報】")
            formatted_lines.append(f"最終信頼度: {final_confidence:.1%}")
            
            actual_length = answer_structure.get("actual_length", 0)
            min_target = answer_structure.get("min_target", 0)
            max_target = answer_structure.get("max_target", 0)
            
            if min_target > 0 and max_target > 0:
                formatted_lines.append(f"回答長: {actual_length}文字 / 目標: {min_target}-{max_target}文字")
            else:
                target_range = answer_structure.get("target_range", "不明")
                formatted_lines.append(f"回答長: {actual_length}文字 / 目標: {target_range}文字")
            
            content_summary = answer_structure.get("content_summary", "")
            if content_summary:
                formatted_lines.append(f"データ活用: {content_summary}")
        
        return '\n'.join(formatted_lines) if formatted_lines else "処理完了"
    
    def output_html_template(self, body_html: str, mathjax_tag: str) -> str:
        """HTMLテンプレート生成"""
        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
    --fg: #111;
    --muted: #666;
    --bg-code: #f6f8fa;
    --border: #e5e7eb;
    --maxw: 980px;
}}
html, body {{ height: 100%; }}
body {{
    font-family: -apple-system, Segoe UI, Roboto, 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
    line-height: 1.7; color: var(--fg);
    margin: 0; padding: 16px 12px; background: #fff;
}}
.container {{ margin: 0 auto; max-width: var(--maxw); }}
h1,h2,h3 {{ margin: 1.1em 0 .6em; }}
h2 {{ font-size: 1.3rem; border-bottom: 1px solid var(--border); padding-bottom: .3em; }}
p {{ margin: .6em 0; }}
ul,ol {{ padding-left: 1.4em; }}
pre, code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace;
    font-size: .95em;
}}
pre {{
    background: var(--bg-code); padding: 12px; border-radius: 8px;
    overflow: auto; border: 1px solid var(--border);
}}
table {{
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
    table-layout: auto;
}}
th, td {{
    border: 1px solid var(--border);
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
}}
thead th {{
    background: #fafafa;
    font-weight: bold;
}}
tr:nth-child(even) td {{
    background: #fcfcfc;
}}
hr {{ border: none; border-top: 1px solid var(--border); margin: 1.2em 0; }}
</style>
<!-- MathJax 設定 -->
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['\\\\(', '\\\\)'], ['$', '$']],
    displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']],
    processEscapes: true,
    processEnvironments: true
  }},
  svg: {{
    fontCache: 'global'
  }},
  startup: {{
    ready: () => {{
      console.log('MathJax is loaded and ready');
      console.log('MathJax config:', window.MathJax);
      MathJax.startup.defaultReady();
      MathJax.startup.promise.then(() => {{
        console.log('MathJax typesetting complete');
      }});
    }}
  }}
}};
</script>
{mathjax_tag}
</head>
<body>
<div class="container">
{body_html}
</div>
</body>
</html>"""

    def set_output_html(self, text: str) -> str:
        """
        LLM 出力を Markdown に通す前に数式を抜き出して退避し、
        変換後に元の TeX デリミタごと復元する安全ルート。
        対応デリミタ: \\(...\\), \\[...\\], $...$, $$...$$
        """
        # 余計な見出し削除のみ
        cleaned = text.replace("=== マルチエージェント最終回答 ===", "").lstrip()

        # --- 1) 数式を一時退避（順番が大事: $$..$$ → \[..\] → $..$ → \(..\)） ---
        tokens = []
        def _store(m, with_delims=True):
            s = m.group(0) if with_delims else m.group(1)
            tokens.append(s)
            return f"§MATH{len(tokens)-1}§"

        # 数式パターンの処理（優先順位: ディスプレイ数式 → インライン数式）
        # $$...$$ (display math with $$)
        cleaned = re.sub(r"\$\$(.+?)\$\$", lambda m: _store(m, True), cleaned, flags=re.DOTALL)
        # \[...\] (display math with \[)
        cleaned = re.sub(r"\\\[(.+?)\\\]", lambda m: _store(m, True), cleaned, flags=re.DOTALL)
        # $...$ (inline math with $, 単独の$のみ)
        cleaned = re.sub(r"(?<![\\$])\$([^\$\n]+?)\$(?![\\$])", lambda m: _store(m, True), cleaned)
        # \(...\) (inline math with \()
        cleaned = re.sub(r"\\\((.+?)\\\)", lambda m: _store(m, True), cleaned, flags=re.DOTALL)
        
        # デバッグ: 抽出した数式トークンを確認
        if tokens:
            print(f"[MathJax] 抽出した数式: {len(tokens)}個")
            for i, token in enumerate(tokens[:5]):  # 最初の5個のみ表示
                print(f"  [{i}] {token[:50]}{'...' if len(token) > 50 else ''}")

        # --- 2) Markdown 変換 ---
        try:
            html_body = md_to_html(cleaned, extensions=["tables", "fenced_code", "nl2br"])
        except Exception as e:
            html_body = f"<p>Markdown変換エラー: {e}</p><pre>{cleaned}</pre>"

        # --- 3) 数式復元 ---
        for i, token in enumerate(tokens):
            html_body = html_body.replace(f"§MATH{i}§", token)
        
        # デバッグ: 数式が正しく復元されているか確認
        if tokens:
            restored_count = sum(1 for token in tokens if token in html_body)
            print(f"[MathJax] 復元された数式: {restored_count}/{len(tokens)}個")

        # --- 4) MathJax読み込み & HTMLテンプレート ---
        # ローカルMathJaxを使用（オフライン環境対応）
        mathjax_src = self._get_mathjax_src()
        mathjax_tag = self._build_mathjax_tag(mathjax_src)
        final_html = self.output_html_template(html_body, mathjax_tag)
        
        # デバッグ: HTMLを一時ファイルに保存
        try:
            debug_path = Path("data") / "debug_output.html"
            debug_path.write_text(final_html, encoding="utf-8")
            print(f"[MathJax] デバッグHTML保存: {debug_path}")
        except Exception as e:
            print(f"[MathJax] デバッグHTML保存失敗: {e}")
        
        return final_html

    def _get_mathjax_src(self) -> str:
        """MathJaxスクリプトソース取得（オフライン対応・相対パス）"""
        local_path = self.assets_path / "mathjax"
        # ダウンロード後の実際のパス: MathJax-3.2.2/es5/tex-svg.js
        script_path = local_path / "MathJax-3.2.2" / "es5" / "tex-svg.js"
        
        if script_path.exists():
            # HTMLファイルは data/ に保存されるため、相対パスで参照
            # data/ から assets/mathjax/MathJax-3.2.2/es5/tex-svg.js への相対パス
            relative_path = "assets/mathjax/MathJax-3.2.2/es5/tex-svg.js"
            print(f"[MathJax] ローカルファイルを使用（相対パス）: {relative_path}")
            return relative_path
        else:
            # 初回のみダウンロード
            self._download_mathjax(str(local_path))
            if script_path.exists():
                relative_path = "assets/mathjax/MathJax-3.2.2/es5/tex-svg.js"
                print(f"[MathJax] ダウンロード後のローカルファイルを使用（相対パス）: {relative_path}")
                return relative_path
            else:
                # ダウンロード失敗時のフォールバック（CDN）
                print("警告: MathJaxローカルファイルが見つからないため、CDNを使用します")
                return "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"

    def _download_mathjax(self, local_path: str):
        """MathJaxダウンロード"""
        try:
            url = "https://github.com/mathjax/MathJax/archive/refs/tags/3.2.2.zip"
            zip_path = Path(local_path) / "mathjax.zip"
            os.makedirs(local_path, exist_ok=True)
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(local_path)
            
            os.remove(zip_path)
        except Exception as e:
            print(f"MathJax ダウンロードエラー: {e}")

    def _build_mathjax_tag(self, script_src: str) -> str:
        """MathJaxタグ構築"""
        return f'<script id="MathJax-script" async src="{script_src}"></script>'