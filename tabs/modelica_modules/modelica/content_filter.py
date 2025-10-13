# ast_only/src/modelica/content_filter.py
"""
緻密なコンテンツフィルタリングシステム
Modelica専門知識でのRAG検索を実現するための詳細フィルタ
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Union
import re  # 修正：import追加
import json
import copy

@dataclass
class FilterCriteria:
    """フィルタ基準の定義"""
    # 除外対象（ノイズ）
    exclude_visual: bool = True
    exclude_layout: bool = True
    exclude_gui_metadata: bool = True
    exclude_empty_values: bool = True
    
    # 含有対象（重要情報）
    include_physical_domains: bool = True
    include_port_interfaces: bool = True
    include_parameters_with_units: bool = True
    include_equations: bool = True
    include_connections: bool = True
    include_dependencies: bool = True
    include_inheritance: bool = True
    include_documentation: bool = True
    
    # 詳細制御 - 上限数を設定可能に（-1は無制限）
    max_parameters: int = -1
    max_components: int = -1
    max_equations: int = -1
    max_connections: int = -1
    max_dependencies: int = -1
    
    parameter_filters: Dict[str, Any] = field(default_factory=dict)
    equation_filters: Dict[str, Any] = field(default_factory=dict)
    component_filters: Dict[str, Any] = field(default_factory=dict)
    
    # LLM拡張用余地
    llm_enhancement_enabled: bool = False
    llm_context_fields: List[str] = field(default_factory=list)

@dataclass 
class ProcessingStage:
    """処理段階の定義"""
    name: str
    description: str
    filters: FilterCriteria
    output_preview: Optional[str] = None

class ContentFilter:
    """緻密なコンテンツフィルタリングエンジン"""
    
    def __init__(self):
        self.stages = self._define_processing_stages()
        self.noise_patterns = self._define_noise_patterns()
        self.important_patterns = self._define_important_patterns()
    
    def _define_processing_stages(self) -> List[ProcessingStage]:
        """処理段階を定義（修正：rag_optimizedでの切り捨てを最小化）"""
        return [
            ProcessingStage(
                name="raw",
                description="生データ（ノイズ除去前）",
                filters=FilterCriteria(
                    exclude_visual=False,
                    exclude_layout=False,
                    exclude_gui_metadata=False,
                    exclude_empty_values=False
                )
            ),
            ProcessingStage(
                name="noise_removed", 
                description="ノイズ除去後",
                filters=FilterCriteria(
                    exclude_visual=True,
                    exclude_layout=True,
                    exclude_gui_metadata=True,
                    exclude_empty_values=True,
                    max_parameters=-1,      # 無制限（修正：省略なし）
                    max_components=-1,      # 無制限（修正：省略なし）
                    max_equations=-1,       # 無制限（修正：省略なし）
                    max_connections=-1,     # 無制限（修正：省略なし）
                    max_dependencies=-1     # 無制限（修正：省略なし）
                )
            ),
            ProcessingStage(
                name="rag_optimized",
                description="RAG最適化後（情報保持重視）", 
                filters=FilterCriteria(
                    exclude_visual=True,
                    exclude_layout=True,
                    exclude_gui_metadata=True,
                    exclude_empty_values=True,
                    include_physical_domains=True,
                    include_port_interfaces=True,
                    include_parameters_with_units=True,
                    # 修正：制限を大幅緩和して情報保持を重視
                    max_parameters=50,      # 20→50
                    max_components=30,      # 15→30  
                    max_equations=50,       # 10→50
                    max_connections=40,     # 20→40
                    max_dependencies=30     # 10→30
                )
            )
        ]
    
    def _define_noise_patterns(self) -> Dict[str, List[str]]:
        """ノイズパターンを定義"""
        return {
            "visual_annotations": [
                "Icon", "Diagram", "graphics", "coordinateSystem",
                "Placement", "transformation", "extent", "rotation",
                "iconTransformation", "iconVisible", "annotation"
            ],
            "layout_properties": [
                "origin", "points", "smooth", "color", "pattern",
                "thickness", "arrow", "fillColor", "fillPattern",
                "lineColor", "textColor", "fontSize", "fontName"
            ],
            "gui_metadata": [
                "__Dymola_", "__OpenModelica_", "experiment",
                "simulationSetup", "choices", "choicesAllMatching",
                "connectorSizing", "Dialog"
            ],
            "empty_defaults": [
                '""', "0", "false", "{}", "[]", "()", "null", "", None
            ]
        }
    
    def _define_important_patterns(self) -> Dict[str, List[str]]:
        """重要パターンを定義"""
        return {
            "physical_domains": [
                "electrical", "mechanical", "thermal", "fluid", 
                "translational", "rotational", "magnetic", "chemical"
            ],
            "port_types": [
                "Pin", "Flange", "HeatPort", "FluidPort", "Port",
                "Connector", "RealInput", "RealOutput", "BooleanInput"
            ],
            "parameter_units": [
                "unit=", "displayUnit=", "quantity=", "min=", "max=",
                "nominal=", "start=", "fixed="
            ],
            "equation_keywords": [
                "der(", "when", "if", "then", "else", "initial",
                "algorithm", "equation"
                # 注意：connect( は除外（別途処理）
            ]
        }
    
    def filter_record(self, record: Dict[str, Any], stage: str = "rag_optimized") -> Dict[str, Any]:
        """レコードを指定段階でフィルタリング（修正：古いequationsデータを完全除去）"""
        filtered = copy.deepcopy(record)

        # raw は本当に無改変で返す
        if stage == "raw":
            return filtered

        # 段階設定を取得
        stage_config = next((s for s in self.stages if s.name == stage), self.stages[1])
        criteria = stage_config.filters

        # 基本メタ情報を追加（raw以外のみ）
        if "meta" not in filtered:
            filtered["meta"] = {}
        filtered["meta"]["processing_stage"] = stage
        filtered["meta"]["filter_applied"] = True

        if stage == "noise_removed":
            # 【追加修正】古いequationsデータを完全に削除してから新しい抽出を実行
            if "equations" in filtered:
                del filtered["equations"]
            
            filtered = self._apply_noise_removal(filtered, criteria)
            filtered["stage_info"] = "視覚的ノイズと不要メタデータを除去"

        elif stage == "rag_optimized":
            # 【追加修正】古いequationsデータを完全に削除してから新しい抽出を実行
            if "equations" in filtered:
                del filtered["equations"]
                
            filtered = self._apply_noise_removal(filtered, criteria)
            filtered = self._apply_rag_optimization(filtered, criteria)
            filtered["stage_info"] = "RAG検索用に重要情報のみ残す"

        return filtered
    
    def _apply_noise_removal(self, record: Dict[str, Any], criteria: FilterCriteria) -> Dict[str, Any]:
        """ノイズ除去処理（修正：パラメータ抽出強化）"""
        if not criteria.exclude_visual:
            return record
        
        # code_textから視覚的ノイズを除去
        if "code_text" in record and record["code_text"]:
            cleaned_code = self._clean_code_text(record["code_text"])
            record["code_text"] = cleaned_code
            
            # パラメータを追加抽出
            extracted_params = self._extract_parameters_from_code(record["code_text"])
            if extracted_params:
                existing_params = record.get("parameters", [])
                
                # 既存パラメータと抽出パラメータをマージ（重複除去）
                param_names = {p.get("name") for p in existing_params if isinstance(p, dict)}
                for param in extracted_params:
                    if param["name"] not in param_names:
                        existing_params.append(param)
                
                record["parameters"] = existing_params
            
            # 【修正】既存のequationsを完全に置き換え（古いシステムを無効化）
            extracted_equations = self._extract_equations_from_code(record["code_text"])
            if extracted_equations:
                record["equations"] = extracted_equations
        
        # docstringからHTMLタグ等を除去
        if "docstring" in record and record["docstring"]:
            record["docstring"] = self._clean_docstring(record["docstring"])
        
        # metaからノイズ情報を除去
        if "meta" in record and isinstance(record["meta"], dict):
            cleaned_meta = {}
            for key, value in record["meta"].items():
                if not self._is_noise_metadata(key):
                    cleaned_meta[key] = value
            record["meta"] = cleaned_meta
        
        # componentsから視覚関連の変更を除去
        if "components" in record:
            record["components"] = self._clean_components(record["components"], criteria)
        
        # connectionsのannotation除去を強化
        if "connections" in record:
            record["connections"] = self._clean_connections(record["connections"], criteria)
        
        # 依存関係の拡張
        record = self._extract_comprehensive_dependencies(record)
        
        # 空値の除去
        if criteria.exclude_empty_values:
            record = self._remove_empty_values(record)
        
        return record
    
    def _extract_parameters_from_code(self, code_text: str) -> List[Dict[str, Any]]:
        """code_textから追加のパラメータを抽出"""
        if not code_text:
            return []
        
        parameters = []
        
        # パラメータ宣言のパターン（複数行対応）
        parameter_pattern = re.compile(
            r'parameter\s+([A-Za-z][A-Za-z0-9_.\[\]]*(?:\([^)]*\))?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*(?:=\s*([^;"]+))?\s*(?:"([^"]*)")?',
            re.MULTILINE | re.DOTALL
        )
        
        matches = parameter_pattern.findall(code_text)
        
        for match in matches:
            param_type, param_name, default_value, description = match
            
            # 型とデフォルト値をクリーンアップ
            param_type = param_type.strip()
            param_name = param_name.strip()
            default_value = default_value.strip() if default_value else ""
            description = description.strip() if description else ""
            
            # 複数行にわたるデフォルト値の処理
            if default_value:
                # annotationを除去
                default_value = re.sub(r'\s*annotation\s*\([^)]*\)', '', default_value, flags=re.IGNORECASE)
                default_value = re.sub(r'\s+', ' ', default_value).strip()
                # 末尾のセミコロンを除去
                default_value = default_value.rstrip(';')
            
            param_dict = {
                "name": param_name,
                "type": param_type,
            }
            
            if default_value:
                param_dict["default"] = default_value
            if description:
                param_dict["description"] = description
            
            parameters.append(param_dict)
        
        return parameters


    def _clean_equations(self, equations: List[Dict], criteria: FilterCriteria) -> List[Dict]:
        """方程式の清潔化（構造保持＋厳密重複除去）"""
        if not equations:
            return equations
        
        cleaned_equations = []
        seen_equations = set()
        max_count = criteria.max_equations if criteria.max_equations > 0 else float('inf')
        total_count = 0
        
        for eq_block in equations:
            if total_count >= max_count:
                break
            
            if not isinstance(eq_block, dict):
                continue
            
            block_equations = eq_block.get("equations", [])
            cleaned_block_equations = []
            section_type = eq_block.get("section_type", "equation")
            
            for eq in block_equations:
                if total_count >= max_count:
                    break
                
                eq_str = str(eq).strip()
                
                # 基本フィルタ
                if len(eq_str) <= 5:
                    continue
                
                # connectステートメントを除外
                if "connect(" in eq_str.lower():
                    continue
                
                # 正規化
                eq_normalized = re.sub(r'\s+', ' ', eq_str.strip())
                
                # annotationを除去
                if "annotation" in eq_normalized:
                    eq_normalized = re.sub(
                        r'\s+annotation\s*\([^()]*(?:\([^()]*(?:\([^()]*\)[^()]*)*\)[^()]*)*\)',
                        '',
                        eq_normalized,
                        flags=re.DOTALL | re.IGNORECASE
                    )
                    eq_normalized = re.sub(r'\s+', ' ', eq_normalized).strip()
                
                # 厳密な重複チェック
                if eq_normalized not in seen_equations and len(eq_normalized) > 5:
                    seen_equations.add(eq_normalized)
                    total_count += 1
                    cleaned_block_equations.append(eq_normalized)
            
            if cleaned_block_equations:
                cleaned_eq_block = dict(eq_block)
                cleaned_eq_block["equations"] = cleaned_block_equations
                cleaned_equations.append(cleaned_eq_block)
        
        return cleaned_equations


    def _preprocess_code(self, code_text: str) -> str:
        """コードの前処理：コメント除去と正規化（修正：コメント除去強化）"""
        # 複数行コメントを除去
        cleaned = re.sub(r'/\*.*?\*/', '', code_text, flags=re.DOTALL)
        
        # 単行コメントを除去（ただし文字列内は保護）
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 文字列内のコメントを保護するため、簡易的に処理
            in_string = False
            quote_char = None
            comment_pos = -1
            
            for i, char in enumerate(line):
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                elif char == '/' and i < len(line) - 1 and line[i+1] == '/' and not in_string:
                    comment_pos = i
                    break
            
            if comment_pos >= 0:
                line = line[:comment_pos]
            
            # 【修正】完全に空行やコメントのみの行を除外
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('//'):
                cleaned_lines.append(line.rstrip())
        
        return '\n'.join(cleaned_lines)

    def _identify_sections(self, code_text: str) -> List[Dict[str, Any]]:
        """コード内のセクション境界を特定"""
        sections = []
        lines = code_text.split('\n')
        current_section = None
        current_content = []
        
        section_keywords = {
            'initial equation': 'initial_equation',
            'initial algorithm': 'initial_algorithm',
            'equation': 'equation',
            'algorithm': 'algorithm'
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                if current_section:
                    current_content.append('')
                i += 1
                continue
            
            # セクション開始の検出
            section_found = None
            for keyword, section_type in section_keywords.items():
                # より正確なキーワード検出
                pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
                if re.match(pattern, line, re.IGNORECASE):
                    section_found = section_type
                    break
            
            if section_found:
                # 前のセクションを保存
                if current_section and current_content:
                    sections.append({
                        'type': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # 新しいセクション開始
                current_section = section_found
                current_content = []
            
            # end文の検出（モデル終了など）
            elif re.match(r'\s*end\s+\w+', line, re.IGNORECASE):
                if current_section and current_content:
                    sections.append({
                        'type': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_section = None
                    current_content = []
            
            # その他の行はセクション内容として追加
            elif current_section:
                current_content.append(line)
            
            i += 1
        
        # 最後のセクションを保存
        if current_section and current_content:
            sections.append({
                'type': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        return sections

    def _extract_equations_from_section(self, section: Dict[str, Any]) -> List[str]:
        """セクションから構造を保持して方程式を抽出"""
        content = section['content']
        if not content:
            return []
        
        equations = []
        content_lines = content.split('\n')
        
        i = 0
        while i < len(content_lines):
            # 構造ブロックを検出・抽出
            block_result = self._extract_structural_block(content_lines, i)
            
            if block_result['block']:
                equations.append(block_result['block'])
                i = block_result['next_index']
            else:
                # 単一行の方程式を処理
                single_eq = self._extract_single_equation(content_lines, i)
                if single_eq['equation']:
                    equations.append(single_eq['equation'])
                i = single_eq['next_index']
        
        return equations

    def _extract_structural_block(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """構造ブロック（for, if, assert等）を抽出"""
        if start_index >= len(lines):
            return {'block': None, 'next_index': start_index + 1}
        
        line = lines[start_index].strip()
        
        # forループの検出
        if re.match(r'\s*for\s+\w+\s+in\s+.*?:', line, re.IGNORECASE):
            return self._extract_for_loop(lines, start_index)
        
        # ifブロックの検出
        if re.match(r'\s*if\s+.*\s+then\s*$', line, re.IGNORECASE):
            return self._extract_if_block(lines, start_index)
        
        # assertの検出
        if 'assert(' in line.lower():
            return self._extract_assert_statement(lines, start_index)
        
        return {'block': None, 'next_index': start_index}

    def _extract_for_loop(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """forループ全体を抽出"""
        loop_lines = []
        i = start_index
        found_loop_keyword = False
        brace_depth = 0
        
        while i < len(lines):
            line = lines[i].strip()
            loop_lines.append(line)
            
            # loopキーワードの検出
            if not found_loop_keyword and 'loop' in line.lower():
                found_loop_keyword = True
            
            # end forの検出
            if found_loop_keyword and re.match(r'\s*end\s+for\s*;?\s*$', line, re.IGNORECASE):
                # forループ全体を1つの文として結合
                full_loop = ' '.join(loop_lines)
                # 不要な空白を整理
                full_loop = re.sub(r'\s+', ' ', full_loop).strip()
                return {'block': full_loop, 'next_index': i + 1}
            
            i += 1
        
        # end forが見つからない場合も、現在までを返す
        if loop_lines:
            full_loop = ' '.join(loop_lines)
            full_loop = re.sub(r'\s+', ' ', full_loop).strip()
            return {'block': full_loop, 'next_index': i}
        
        return {'block': None, 'next_index': start_index + 1}

    def _extract_if_block(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """ifブロック全体を抽出"""
        if_lines = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if_lines.append(line)
            
            # end ifの検出
            if re.match(r'\s*end\s+if\s*;?\s*$', line, re.IGNORECASE):
                full_if = ' '.join(if_lines)
                full_if = re.sub(r'\s+', ' ', full_if).strip()
                return {'block': full_if, 'next_index': i + 1}
            
            i += 1
        
        # end ifが見つからない場合
        if if_lines:
            full_if = ' '.join(if_lines)
            full_if = re.sub(r'\s+', ' ', full_if).strip()
            return {'block': full_if, 'next_index': i}
        
        return {'block': None, 'next_index': start_index + 1}

    def _extract_assert_statement(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """assert文を抽出（複数行対応）"""
        assert_lines = []
        i = start_index
        paren_depth = 0
        
        while i < len(lines):
            line = lines[i].strip()
            assert_lines.append(line)
            
            # 括弧の深度を追跡
            paren_depth += line.count('(') - line.count(')')
            
            # セミコロンで終わるか、括弧が閉じた場合は終了
            if line.endswith(';') or (paren_depth <= 0 and 'assert' in assert_lines[0].lower()):
                full_assert = ' '.join(assert_lines)
                full_assert = re.sub(r'\s+', ' ', full_assert).strip()
                full_assert = full_assert.rstrip(';')
                return {'block': full_assert, 'next_index': i + 1}
            
            i += 1
        
        # 不完全なassert
        if assert_lines:
            full_assert = ' '.join(assert_lines)
            full_assert = re.sub(r'\s+', ' ', full_assert).strip()
            return {'block': full_assert, 'next_index': i}
        
        return {'block': None, 'next_index': start_index + 1}

    def _extract_single_equation(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """単一の方程式を抽出（修正：algorithm用代入文対応）"""
        if start_index >= len(lines):
            return {'equation': None, 'next_index': start_index + 1}
        
        equation_lines = []
        i = start_index
        paren_depth = 0
        brace_depth = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 空行とコメント行を完全にスキップ
            if not line or line.startswith('//') or line.startswith('/*'):
                i += 1
                continue
            
            equation_lines.append(line)
            
            # 括弧の深度を追跡
            paren_depth += line.count('(') - line.count(')')
            brace_depth += line.count('{') - line.count('}')
            
            # 方程式の終了判定
            if (line.endswith(';') or 
                (paren_depth == 0 and brace_depth == 0 and ('=' in ' '.join(equation_lines) or ':=' in ' '.join(equation_lines)))):
                
                full_equation = ' '.join(equation_lines)
                full_equation = re.sub(r'\s+', ' ', full_equation).strip()
                full_equation = full_equation.rstrip(';')
                
                # 【修正】代入文（:=）も含めて方程式として認識
                if (len(full_equation) > 5 and 
                    ('=' in full_equation or ':=' in full_equation or 'when' in full_equation.lower()) and
                    not full_equation.strip().endswith('=') and
                    not full_equation.strip().endswith(':=') and
                    not full_equation.startswith('//') and
                    'annotation' not in full_equation.lower()):
                    return {'equation': full_equation, 'next_index': i + 1}
                else:
                    return {'equation': None, 'next_index': i + 1}
            
            i += 1
        
        # 方程式が不完全な場合
        return {'equation': None, 'next_index': i}

    def _extract_equations_from_code(self, code_text: str) -> List[Dict[str, Any]]:
        """構造認識による方程式抽出（完全リニューアル）"""
        if not code_text:
            return []
        
        # Step 1: コメントを除去してブロック構造を特定
        cleaned_code = self._preprocess_code(code_text)
        
        # Step 2: セクション境界を特定
        sections = self._identify_sections(cleaned_code)
        
        # Step 3: 各セクションから方程式を抽出
        extracted_equations = []
        for section in sections:
            # 【修正】algorithmとinitial_algorithmも処理対象に追加
            if section['type'] in ['initial_equation', 'equation', 'algorithm', 'initial_algorithm']:
                equations = self._extract_equations_from_section(section)
                if equations:
                    extracted_equations.append({
                        "section_type": section['type'],
                        "equations": equations
                    })
        
        return extracted_equations



    def _extract_comprehensive_dependencies(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """修正：包括的な依存関係抽出（辞書ハッシュエラー対応）"""
        dependencies = {
            "extends": record.get("extends", []),
            "imports": record.get("imports", []),
            "component_instances": [],  # 新規：コンポーネントインスタンス
            "referenced_types": []      # 新規：参照される型
        }
        
        # 既存のextends/importsに加えて、コンポーネントからの依存関係を抽出
        if "components" in record:
            seen_types = set()
            for comp in record["components"]:
                if isinstance(comp, dict):
                    comp_type = comp.get("type_name", comp.get("type", ""))
                    if comp_type and comp_type not in seen_types:
                        seen_types.add(comp_type)
                        # ライブラリタイプかどうか判定（ドット記法で判定）
                        if "." in comp_type:
                            dependencies["component_instances"].append({
                                "instance_name": comp.get("name", ""),
                                "type": comp_type,
                                "library": comp_type.split(".")[0] if "." in comp_type else ""
                            })
                        else:
                            dependencies["referenced_types"].append(comp_type)
        
        # code_textからの追加依存関係抽出
        if "code_text" in record and record["code_text"]:
            additional_deps = self._extract_dependencies_from_code(record["code_text"])
            for key in additional_deps:
                if key in dependencies and isinstance(dependencies[key], list):
                    # 修正：辞書を含むリストの重複除去を安全に行う
                    if key == "component_instances":
                        # 辞書のリストは型と名前の組み合わせで重複チェック
                        seen_instances = set()
                        for inst in additional_deps[key]:
                            if isinstance(inst, dict):
                                inst_key = f"{inst.get('type', '')}:{inst.get('instance_name', '')}"
                                if inst_key not in seen_instances:
                                    seen_instances.add(inst_key)
                                    dependencies[key].append(inst)
                            else:
                                dependencies[key].append(inst)
                    else:
                        # 文字列のリストは通常のset処理
                        combined = dependencies[key] + additional_deps[key]
                        dependencies[key] = list(set(combined))  # 文字列なのでset()が使用可能
        
        # 空の項目を除去
        dependencies = {k: v for k, v in dependencies.items() if v}
        
        if dependencies:
            record["dependencies"] = dependencies
            
        return record
    
    def _extract_dependencies_from_code(self, code_text: str) -> Dict[str, List[str]]:
        """コードテキストから追加の依存関係を抽出"""
        dependencies = {
            "extends": [],
            "imports": [],
            "component_instances": [],
            "referenced_types": []
        }
        
        # extends文の抽出
        extends_matches = re.findall(r'extends\s+([A-Za-z][A-Za-z0-9_.]*)', code_text, re.IGNORECASE)
        dependencies["extends"].extend(extends_matches)
        
        # import文の抽出
        import_matches = re.findall(r'import\s+([A-Za-z][A-Za-z0-9_.]*)', code_text, re.IGNORECASE)
        dependencies["imports"].extend(import_matches)
        
        # 型宣言からの抽出（より包括的）
        type_matches = re.findall(r'([A-Z][A-Za-z0-9_.]+)\s+\w+\s*[;(]', code_text)
        dependencies["referenced_types"].extend(type_matches)
        
        return dependencies
    
    def _clean_code_text(self, code_text: str) -> str:
        """コードテキストからノイズを除去"""
        if not code_text:
            return code_text
        
        cleaned = code_text
        
        # 段階的にannotationを除去
        for _ in range(3):
            old_length = len(cleaned)
            cleaned = re.sub(r'\bannotation\s*\([^()]*(?:\([^()]*(?:\([^()]*\)[^()]*)*\)[^()]*)*\)\s*;?', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
            if len(cleaned) == old_length:
                break
        
        # 視覚要素キーワードの行を除去
        lines = cleaned.split('\n')
        cleaned_lines = []
        visual_keywords = ['Icon', 'Diagram', 'Placement', 'transformation', 'graphics', 'coordinateSystem', 
                          'extent', 'rotation', 'lineColor', 'fillColor', 'points', 'smooth']
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and not any(keyword in line_clean for keyword in visual_keywords):
                if line_clean and not re.match(r'^\s*[,;{}\[\]()]\s*$', line_clean):
                    cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
        
        return result.strip()
    
    def _clean_connections(self, connections: List[Dict], criteria: FilterCriteria) -> List[Dict]:
        """接続リストから視覚要素とannotationを除去"""
        if not connections:
            return connections
        
        cleaned_connections = []
        max_count = criteria.max_connections if criteria.max_connections > 0 else len(connections)
        seen_connections = set()
        
        for i, conn in enumerate(connections):
            if i >= max_count:
                break
                
            if not isinstance(conn, dict):
                continue
            
            cleaned_conn = {}
            
            for key, value in conn.items():
                if key in ["from_connector", "to_connector", "from", "to"]:
                    cleaned_conn[key] = value
                elif key == "annotation":
                    continue  # annotation完全除外
                elif key == "comment" and value and str(value).strip():
                    cleaned_conn[key] = value
                elif not any(noise in key.lower() for noise in self.noise_patterns["visual_annotations"]):
                    if value not in self.noise_patterns["empty_defaults"]:
                        cleaned_conn[key] = value
            
            # 重複チェック
            if cleaned_conn:
                conn_key = f"{cleaned_conn.get('from_connector', cleaned_conn.get('from', ''))}->{cleaned_conn.get('to_connector', cleaned_conn.get('to', ''))}"
                if conn_key not in seen_connections:
                    seen_connections.add(conn_key)
                    cleaned_connections.append(cleaned_conn)
        
        return cleaned_connections
    
    def _apply_rag_optimization(self, record: Dict[str, Any], criteria: FilterCriteria) -> Dict[str, Any]:
        """RAG最適化処理（修正：情報保持を最大化）"""
        optimized = {
            "id": record.get("fqn", record.get("name", "unknown")),
            "kind": record.get("kind", "unknown"),
            "name": record.get("name", ""),
            "stage": "rag_optimized"
        }
        
        # パッケージパス（必須）
        if "package_path" in record:
            optimized["package_path"] = record["package_path"]
        
        # ドキュメント（重要）- 切り捨て制限を緩和
        if criteria.include_documentation and "docstring" in record:
            doc = record["docstring"]
            if doc and len(str(doc).strip()) > 10:
                # 修正：1000文字まで許容（500→1000）
                optimized["documentation"] = str(doc)[:1000] + "..." if len(str(doc)) > 1000 else str(doc)
        
        # パラメータ（修正：制限を大幅緩和）
        if criteria.include_parameters_with_units and "parameters" in record:
            max_params = criteria.max_parameters if criteria.max_parameters > 0 else len(record["parameters"])
            # 修正：最大50個まで許容（20→50）
            max_params = min(max_params, 50) if criteria.max_parameters > 0 else len(record["parameters"])
            params = self._filter_important_parameters(record["parameters"], max_params)
            if params:
                optimized["parameters"] = params
        
        # 物理量（RAGで重要）
        if criteria.include_physical_domains and "physical_quantities" in record:
            pq = self._extract_physical_summary(record["physical_quantities"])
            if pq:
                optimized["physical_quantities"] = pq
        
        # コンポーネント（修正：制限を大幅緩和）
        if "components" in record:
            max_comps = criteria.max_components if criteria.max_components > 0 else len(record["components"])
            # 修正：最大30個まで許容（15→30）
            max_comps = min(max_comps, 30) if criteria.max_components > 0 else len(record["components"])
            comps = self._filter_important_components(record["components"], max_comps)
            if comps:
                optimized["components"] = comps
        
        # 方程式（修正：制限を大幅緩和）
        if criteria.include_equations and "equations" in record:
            max_eqs = criteria.max_equations if criteria.max_equations > 0 else 999
            # 修正：最大50個まで許容（10→50）
            max_eqs = min(max_eqs, 50) if criteria.max_equations > 0 else 999
            eqs = self._filter_important_equations_for_rag(record["equations"], max_eqs)
            if eqs:
                optimized["equations"] = eqs
        
        # 接続（修正：制限を緩和）
        if criteria.include_connections and "connections" in record:
            conns = record["connections"]
            if conns:
                max_conn = criteria.max_connections if criteria.max_connections > 0 else len(conns)
                # 修正：最大40個まで許容（20→40）
                max_conn = min(max_conn, 40) if criteria.max_connections > 0 else len(conns)
                optimized_conns = []
                seen_conns = set()
                
                for c in conns[:max_conn]:
                    if isinstance(c, dict):
                        from_conn = c.get("from_connector", c.get("from", ""))
                        to_conn = c.get("to_connector", c.get("to", ""))
                        conn_key = f"{from_conn}->{to_conn}"
                        
                        if conn_key not in seen_conns and from_conn and to_conn:
                            seen_conns.add(conn_key)
                            optimized_conns.append({
                                "from": from_conn,
                                "to": to_conn
                            })
                
                if optimized_conns:
                    optimized["connections"] = optimized_conns
        
        # 依存関係（修正：制限を緩和）
        if criteria.include_dependencies and "dependencies" in record:
            deps = record["dependencies"]
            max_dep = criteria.max_dependencies if criteria.max_dependencies > 0 else 999
            # 修正：最大30個まで許容（10→30）
            max_dep = min(max_dep, 30) if criteria.max_dependencies > 0 else 999
            
            filtered_deps = {}
            for dep_type, dep_list in deps.items():
                if dep_list:
                    if isinstance(dep_list, list):
                        filtered_deps[dep_type] = dep_list[:max_dep]
                    else:
                        filtered_deps[dep_type] = dep_list
            
            if filtered_deps:
                optimized["dependencies"] = filtered_deps
        
        # 修正：noise_removedと同等の重要フィールドを確実に保持
        important_fields = ["code_text", "docstring", "meta", "extends", "imports"]
        for field in important_fields:
            if field in record and field not in optimized:
                optimized[field] = record[field]
        
        return optimized
    
    def _filter_important_equations_for_rag(self, equations: List[Dict], max_count: int = -1) -> List[str]:
        """RAG用の重要な方程式フィルタ（connect文は完全に除外）"""
        if not equations:
            return []
        
        important_eqs = []
        limit = max_count if max_count > 0 else 999
        seen_eqs = set()
        
        for eq_block in equations:
            if len(important_eqs) >= limit:
                break
                
            if not isinstance(eq_block, dict):
                continue
                
            block_equations = eq_block.get("equations", [])
            for eq in block_equations:
                if len(important_eqs) >= limit:
                    break
                    
                eq_str = str(eq).strip()
                
                # connect文は完全に除外
                if "connect(" in eq_str.lower():
                    continue
                
                # 意味のある方程式のみ
                if len(eq_str) > 5:
                    if not eq_str.startswith("//") and not eq_str.startswith("/*"):
                        
                        # annotation部分を除去
                        if "annotation" in eq_str:
                            eq_str = re.sub(
                                r'\s+annotation\s*\([^()]*(?:\([^()]*(?:\([^()]*\)[^()]*)*\)[^()]*)*\)',
                                '',
                                eq_str,
                                flags=re.DOTALL | re.IGNORECASE
                            )
                            eq_str = re.sub(r'\s+', ' ', eq_str).strip()
                        
                        # 重要キーワードを含むものを優先
                        is_important = any(kw in eq_str for kw in self.important_patterns["equation_keywords"])
                        has_meaningful_content = len([c for c in eq_str if c.isalpha()]) > 3
                        
                        if is_important or (has_meaningful_content and "=" in eq_str):
                            eq_normalized = re.sub(r'\s+', ' ', eq_str.strip())
                            if eq_normalized not in seen_eqs and len(eq_normalized) > 5:
                                seen_eqs.add(eq_normalized)
                                important_eqs.append(eq_str[:200])
        
        return important_eqs
    
    # 以下、既存のヘルパーメソッドは省略（変更なし）
    def _clean_docstring(self, docstring: str) -> str:
        if not docstring:
            return docstring
        cleaned = re.sub(r'<[^>]+>', '', str(docstring))
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _is_noise_metadata(self, key: str) -> bool:
        noise_keys = ["node_type", "checksum", "uid"]
        return key in noise_keys or key.startswith("__")
    
    def _clean_components(self, components: List[Dict], criteria: FilterCriteria) -> List[Dict]:
        if not components:
            return components
        
        cleaned_components = []
        max_count = criteria.max_components if criteria.max_components > 0 else len(components)
        seen_components = set()
        
        for i, comp in enumerate(components):
            if i >= max_count:
                break
                
            if not isinstance(comp, dict):
                continue
                
            cleaned_comp = {
                "name": comp.get("name", ""),
                "type_name": comp.get("type_name", "")
            }
            
            if "prefixes" in comp:
                important_prefixes = [p for p in comp["prefixes"] if p in ["input", "output", "flow", "parameter"]]
                if important_prefixes:
                    cleaned_comp["prefixes"] = important_prefixes
            
            if "modifications" in comp and isinstance(comp["modifications"], dict):
                clean_mods = {}
                for mod_key, mod_val in comp["modifications"].items():
                    if not any(noise in mod_key.lower() for noise in self.noise_patterns["visual_annotations"]):
                        if mod_val not in self.noise_patterns["empty_defaults"]:
                            clean_mods[mod_key] = mod_val
                if clean_mods:
                    cleaned_comp["modifications"] = clean_mods
            
            if "comment" in comp and comp["comment"]:
                cleaned_comp["comment"] = comp["comment"]
            
            comp_key = f"{cleaned_comp['name']}:{cleaned_comp['type_name']}"
            if comp_key not in seen_components:
                seen_components.add(comp_key)
                cleaned_components.append(cleaned_comp)
        
        return cleaned_components
    
    def _remove_empty_values(self, record: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(record, dict):
            return record
        
        cleaned = {}
        for key, value in record.items():
            if isinstance(value, dict):
                cleaned_value = self._remove_empty_values(value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                cleaned_list = [item for item in value if item not in self.noise_patterns["empty_defaults"]]
                if cleaned_list:
                    cleaned[key] = cleaned_list
            elif value not in self.noise_patterns["empty_defaults"]:
                cleaned[key] = value
        
        return cleaned
    
    def _filter_important_parameters(self, parameters: List[Dict], max_count: int = -1) -> List[Dict]:
        if not parameters:
            return []
        
        important_params = []
        limit = max_count if max_count > 0 else len(parameters)
        seen_params = set()
        
        for param in parameters:
            if len(important_params) >= limit:
                break
                
            if not isinstance(param, dict):
                continue
                
            param_name = param.get("name", "")
            if param_name in seen_params:
                continue
                
            has_unit = any(key in str(param) for key in self.important_patterns["parameter_units"])
            has_meaningful_default = param.get("default") not in self.noise_patterns["empty_defaults"]
            has_description = param.get("description") and len(str(param["description"]).strip()) > 0
            
            if has_unit or has_meaningful_default or has_description:
                clean_param = {
                    "name": param_name,
                    "type": param.get("type", "")
                }
                
                if param.get("default") not in self.noise_patterns["empty_defaults"]:
                    clean_param["default"] = param["default"]
                    
                if param.get("description"):
                    clean_param["description"] = str(param["description"])[:200]
                
                seen_params.add(param_name)
                important_params.append(clean_param)
        
        return important_params
    
    def _extract_physical_summary(self, physical_quantities: List[Dict]) -> Dict[str, Any]:
        if not physical_quantities:
            return {}
        
        summary = {
            "quantities": [],
            "units": set(),
            "domains": set()
        }
        
        for pq in physical_quantities:
            if not isinstance(pq, dict):
                continue
                
            if pq.get("unit"):
                summary["units"].add(pq["unit"])
                
            if pq.get("name") and pq.get("unit"):
                summary["quantities"].append({
                    "name": pq["name"],
                    "unit": pq["unit"]
                })
        
        for unit in summary["units"]:
            for domain in self.important_patterns["physical_domains"]:
                if domain in unit.lower():
                    summary["domains"].add(domain)
        
        summary["units"] = list(summary["units"])
        summary["domains"] = list(summary["domains"])
        
        return summary if summary["quantities"] or summary["units"] else {}
    
    def debug_equation_extraction(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """デバッグ用：方程式抽出の全過程を表示"""
        if "code_text" not in record:
            return {"error": "No code_text found"}
        
        debug_info = {}
        code_text = record["code_text"]
        
        # Step 1: 元のコード
        debug_info["1_original_length"] = len(code_text)
        debug_info["1_original_sample"] = code_text[:500] + "..." if len(code_text) > 500 else code_text
        
        # Step 2: 前処理後
        try:
            cleaned = self._preprocess_code(code_text)
            debug_info["2_cleaned_length"] = len(cleaned)
            debug_info["2_cleaned_sample"] = cleaned[:500] + "..." if len(cleaned) > 500 else cleaned
        except Exception as e:
            debug_info["2_preprocess_error"] = str(e)
            return debug_info
        
        # Step 3: セクション識別
        try:
            sections = self._identify_sections(cleaned)
            debug_info["3_sections_found"] = len(sections)
            debug_info["3_section_types"] = [s['type'] for s in sections]
            for i, section in enumerate(sections):
                debug_info[f"3_section_{i}"] = {
                    "type": section['type'],
                    "content_length": len(section['content']),
                    "content_preview": section['content'][:200] + "..." if len(section['content']) > 200 else section['content']
                }
        except Exception as e:
            debug_info["3_sections_error"] = str(e)
            return debug_info
        
        # Step 4: 方程式抽出
        try:
            equations = self._extract_equations_from_code(code_text)
            debug_info["4_equation_blocks"] = len(equations)
            for i, eq_block in enumerate(equations):
                debug_info[f"4_block_{i}"] = {
                    "section_type": eq_block.get("section_type"),
                    "equation_count": len(eq_block.get("equations", [])),
                    "equations": eq_block.get("equations", [])[:3]  # 最初の3つだけ
                }
        except Exception as e:
            debug_info["4_extraction_error"] = str(e)
        
        return debug_info

    def _filter_important_components(self, components: List[Dict], max_count: int = -1) -> List[Dict]:
        if not components:
            return []
        
        important_comps = []
        limit = max_count if max_count > 0 else len(components)
        seen_comps = set()
        
        for comp in components:
            if len(important_comps) >= limit:
                break
                
            if not isinstance(comp, dict):
                continue
                
            comp_name = comp.get("name", "")
            comp_type = comp.get("type_name", "")
            comp_key = f"{comp_name}:{comp_type}"
            
            if comp_key in seen_comps:
                continue
                
            type_name = comp_type.lower()
            is_physical = any(domain in type_name for domain in self.important_patterns["physical_domains"])
            has_modifications = comp.get("modifications") and len(comp["modifications"]) > 0
            
            if is_physical or has_modifications or comp.get("prefixes"):
                clean_comp = {
                    "name": comp_name,
                    "type": comp_type
                }
                
                if comp.get("prefixes"):
                    clean_comp["prefixes"] = comp["prefixes"]
                    
                if has_modifications:
                    important_mods = {}
                    for key, val in comp["modifications"].items():
                        if not any(noise in key.lower() for noise in self.noise_patterns["visual_annotations"]):
                            if len(str(val).strip()) > 0:
                                important_mods[key] = str(val)[:50]
                    if important_mods:
                        clean_comp["modifications"] = important_mods
                
                if comp.get("comment"):
                    clean_comp["comment"] = comp["comment"]
                
                seen_comps.add(comp_key)
                important_comps.append(clean_comp)
        
        return important_comps

class FilterRuleManager:
    """フィルタルールの保存・読み込み管理"""
    
    def __init__(self):
        self.filter = ContentFilter()
    
    def save_filter_config(self, config: FilterCriteria, path: str):
        """フィルタ設定をJSONで保存"""
        config_dict = {
            "exclude_visual": config.exclude_visual,
            "exclude_layout": config.exclude_layout,
            "exclude_gui_metadata": config.exclude_gui_metadata,
            "exclude_empty_values": config.exclude_empty_values,
            "include_physical_domains": config.include_physical_domains,
            "include_port_interfaces": config.include_port_interfaces,
            "include_parameters_with_units": config.include_parameters_with_units,
            "include_equations": config.include_equations,
            "include_connections": config.include_connections,
            "include_dependencies": config.include_dependencies,
            "include_inheritance": config.include_inheritance,
            "include_documentation": config.include_documentation,
            "max_parameters": config.max_parameters,
            "max_components": config.max_components,
            "max_equations": config.max_equations,
            "max_connections": config.max_connections,
            "max_dependencies": config.max_dependencies,
            "parameter_filters": config.parameter_filters,
            "equation_filters": config.equation_filters,
            "component_filters": config.component_filters,
            "llm_enhancement_enabled": config.llm_enhancement_enabled,
            "llm_context_fields": config.llm_context_fields
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def load_filter_config(self, path: str) -> FilterCriteria:
        """フィルタ設定をJSONから読み込み"""
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return FilterCriteria(**config_dict)
    
    def get_stage_names(self) -> List[str]:
        """利用可能な処理段階名を取得"""
        return [stage.name for stage in self.filter.stages]
    
    def get_stage_description(self, stage_name: str) -> str:
        """処理段階の説明を取得"""
        stage = next((s for s in self.filter.stages if s.name == stage_name), None)
        return stage.description if stage else ""