# src/modelica/ast_extractor.py
from __future__ import annotations
from typing import List, Dict, Any, Iterable, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import re
import os
from tree_sitter import Node
from tabs.modelica_modules.modelica.parser_loader import new_parser
from tabs.modelica_modules.modelica.models import (
    SymbolRecord, CodeSpan, EquationBlock, Parameter, Kind,
    ComponentDeclaration, Connection, VariableDeclaration, PhysicalQuantity
)
from tabs.modelica_modules.modelica.utils_text import file_bytes, sha1_text


# --- AST-first / grammar-agnostic (最小ヒューリスティクス) ---

SYMBOL_NODE_HINTS = (
    "class", "model", "block", "connector", "function", "record", "package", "type"
)
IDENT_NODE_NAMES = {"identifier", "name", "component_reference", "component_reference_name"}

HEADER_RE = re.compile(
    r"""(?ix)
    ^\s*
    (?:within\s+[A-Za-z0-9_.]+\s*;\s*)?   # optional 'within ...;'
    (?:partial\s+)?                       # optional 'partial'
    (?P<kind>package|class|model|block|connector|function|record|type)\s+
    (?P<name>[A-Za-z_]\w*)
    """, re.DOTALL,
)

WITHIN_RE = re.compile(r"(?m)^\s*within\s+([A-Za-z0-9_.]+)\s*;")
EXTENDS_RE = re.compile(r"\bextends\s+([A-Za-z0-9_.]+)")
IMPORT_RE  = re.compile(r"\bimport\s+([A-Za-z0-9_.]+)")

# 既存のparameter正規表現
PARAM_MODS = r"(?:final|constant|each|inner|outer|redeclare|replaceable)\s+"
PARAM_TYPE = r"[A-Za-z_][\w\.]*(?:\s*\[[^\]]+\])?"
PARAM_NAME = r"[A-Za-z_]\w*"
PARAM_DEFAULT = r"(?:=\s*([^;]*))?"

PARAM_RE_1 = re.compile(
    rf"(?m)^\s*parameter\s+(?:{PARAM_MODS})*({PARAM_TYPE})\s+({PARAM_NAME})\s*{PARAM_DEFAULT}\s*;\s*$"
)

PARAM_RE_MULTI = re.compile(
    rf"(?m)^\s*parameter\s+(?:{PARAM_MODS})*({PARAM_TYPE})\s+(.+?)\s*;\s*$"
)

# $D83C$DD95 新規追加：Component宣言の正規表現
COMPONENT_DECL_RE = re.compile(
    r"""(?mx)
    ^\s*
    (?P<prefixes>(?:(?:input|output|flow|stream|discrete|parameter|constant|final|inner|outer|replaceable|redeclare)\s+)*)
    (?P<type>[A-Za-z_][\w\.]*(?:\s*\[[^\]]*\])?)  # 型名（配列対応）
    \s+
    (?P<declarations>.+?)  # 宣言部（複数可能）
    \s*;
    """)

# $D83C$DD95 新規追加：Variable宣言の正規表現  
VARIABLE_DECL_RE = re.compile(
    r"""(?mx)
    ^\s*
    (?P<prefixes>(?:(?:input|output|flow|stream|discrete|final|inner|outer|protected)\s+)*)
    (?P<type>Real|Integer|Boolean|String|Time|Angle|Length|Mass|Force|Voltage|Current|Torque|SI\.\w+|[\w\.]+)
    \s+
    (?P<name>[A-Za-z_]\w*)(?!\s*=\s*if\b)  # ifキーワードを除外
    (?P<array_dims>\s*\[[^\]]*\])?
    (?P<attributes>\s*\([^)]*\))?
    (?P<binding>\s*=\s*[^;]*)?
    \s*(?P<comment>"[^"]*")?
    \s*;
    """)

# $D83C$DD95 新規追加：Connect文の正規表現
CONNECT_RE = re.compile(
    r"""(?mx)
    (?:^\s*(?:if\s+.+?\s+then\s+)?)?  # 条件文対応
    connect\s*\(\s*
    (?P<from>[^,]+?)
    \s*,\s*
    (?P<to>[^)]+?)
    \s*\)
    """)


def _node_text(src: bytes, node: Node) -> str:
    return src[node.start_byte: node.end_byte].decode("utf-8", errors="replace")


def _span_of(node: Node, file_path: str) -> CodeSpan:
    return CodeSpan(
        file_path=file_path,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        start_col=node.start_point[1] + 1,
        end_col=node.end_point[1] + 1,
    )


def _guess_kind(node_type: str) -> Kind:
    lt = node_type.lower()
    for k in SYMBOL_NODE_HINTS:
        if k in lt:
            return "class" if k == "class" else k
    return "unknown"


def _collect_identifiers(node: Node, src: bytes, limit: int = 50) -> List[str]:
    found = []
    stack = [node]
    while stack and len(found) < limit:
        cur = stack.pop()
        if cur.type in IDENT_NODE_NAMES and cur.is_named:
            t = _node_text(src, cur).strip()
            if t:
                found.append(t)
        for i in range(cur.child_count):
            stack.append(cur.child(i))
    seen = set(); uniq = []
    for s in found:
        if s not in seen:
            seen.add(s); uniq.append(s)
    return uniq


def _leading_comment(src: bytes, node: Node) -> str:
    parent = node.parent
    if not parent:
        return ""
    idx = 0
    for i in range(parent.child_count):
        if parent.child(i).id == node.id:
            idx = i; break
    comments = []
    j = idx - 1
    while j >= 0:
        sib = parent.child(j)
        if sib.type.lower().find("comment") >= 0:
            comments.append(_node_text(src, sib)); j -= 1; continue
        txt = _node_text(src, sib).strip()
        if txt == "":
            j -= 1; continue
        break
    comments.reverse()
    return "\n".join(comments).strip()


def _contains_equation_like(node_type: str) -> bool:
    lt = node_type.lower()
    return ("equation" in lt) or ("algorithm" in lt) or ("when" in lt)


def _collect_equations(node: Node, src: bytes, file_path: str) -> List[EquationBlock]:
    blocks: List[EquationBlock] = []
    stack = [node]
    while stack:
        cur = stack.pop()
        if _contains_equation_like(cur.type):
            span = _span_of(cur, file_path)
            text = _node_text(src, cur)
            # 素朴にセミコロン分割（重複は post-process 側で除去）
            eqs = [e.strip() for e in re.split(r";\s*", text) if e.strip()]
            blocks.append(EquationBlock(equations=eqs, span=span))
        for i in range(cur.child_count):
            stack.append(cur.child(i))
    return blocks


def _is_symbol_definition(node: Node, src: bytes) -> tuple[Kind, str] | None:
    # 本物の定義ヘッダのみを許可（最初の ~400 文字で判定）
    t = _node_text(src, node)
    m = HEADER_RE.search(t[:400])
    if not m:
        return None
    kind = m.group("kind").lower()
    name = m.group("name")
    k: Kind = kind if kind in {"package","class","model","block","connector","function","record","type"} else "unknown"
    return (k, name)


def _make_fqn(package_stack: List[str], name: str) -> str:
    parts = [p for p in package_stack if p] + ([name] if name else [])
    return ".".join(parts)


def _parse_within_header(src: bytes) -> List[str]:
    head = src[:4000].decode("utf-8", errors="replace")
    m = WITHIN_RE.search(head)
    if not m:
        return []
    return [p for p in m.group(1).split(".") if p]


def _strip_annotations(text: str) -> str:
    """RAGに不要な可視化・配置情報を徹底的に除去"""
    # 既存のannotation除去
    out = []
    i = 0; n = len(text)
    while i < n:
        if text.startswith("annotation", i):
            j = i + len("annotation")
            # 空白をスキップ
            while j < n and text[j].isspace(): j += 1
            if j < n and text[j] == "(":
                depth = 0; k = j
                while k < n:
                    ch = text[k]
                    if ch == "(": depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            k += 1  # ')' の次へ
                            break
                    k += 1
                # 末尾の空白とセミコロンをスキップ
                while k < n and text[k].isspace(): k += 1
                if k < n and text[k] == ";": k += 1
                i = k
                continue
        out.append(text[i]); i += 1
    
    cleaned_text = "".join(out)
    
    # Icon/Diagram情報の除去
    cleaned_text = re.sub(r'\bIcon\s*\([^(]*(?:\([^)]*\)[^(]*)*\)\s*,?\s*graphics\s*=\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = re.sub(r'\bDiagram\s*\([^(]*(?:\([^)]*\)[^(]*)*\)\s*,?\s*graphics\s*=\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', cleaned_text, flags=re.DOTALL)
    
    # Documentation内のHTMLを保持しつつ、Placement等の配置情報を除去
    cleaned_text = re.sub(r'Placement\s*\([^)]*\)', '', cleaned_text)
    cleaned_text = re.sub(r'transformation\s*\([^)]*\)', '', cleaned_text)
    cleaned_text = re.sub(r'coordinateSystem\s*\([^)]*\)', '', cleaned_text)
    
    return cleaned_text


def _clean_default(d: str, limit: int = 180) -> str:
    d = " ".join((d or "").split())
    return d[:limit]


def _split_decl_names(s: str) -> list[tuple[str, str]]:
    """
    'a=1, b, c[3]={1,2,3}' のような部分から [(name, default), ...] を素朴に取り出す。
    括弧/波括弧/角括弧のネストだけは数えて安全にカンマ分割する。
    """
    out=[]; buf=[]; depth_round=depth_square=depth_curly=0
    def flush():
        t="".join(buf).strip()
        if not t: return
        if "=" in t:
            n, d = t.split("=", 1)
            out.append((n.strip(), d.strip()))
        else:
            out.append((t.strip(), ""))
        buf.clear()

    for ch in s:
        if ch == "(": depth_round += 1
        elif ch == ")": depth_round = max(0, depth_round-1)
        elif ch == "[": depth_square += 1
        elif ch == "]": depth_square = max(0, depth_square-1)
        elif ch == "{": depth_curly += 1
        elif ch == "}": depth_curly = max(0, depth_curly-1)

        if ch == "," and (depth_round==depth_square==depth_curly==0):
            flush()
        else:
            buf.append(ch)
    flush()
    return out


# $D83C$DD95 新規ヘルパー関数群

def _parse_component_declarations(declarations_str: str) -> List[Dict[str, Any]]:
    """カンマ区切りのコンポーネント宣言を解析
    
    例: "R1(R=100), C1, L1(L=0.1)" -> [{"name": "R1", "modifications": {"R": "100"}}, ...]
    """
    results = []
    
    # 括弧のネストを考慮したカンマ分割
    decls = _smart_comma_split(declarations_str)
    
    for decl in decls:
        decl = decl.strip()
        if not decl:
            continue
            
        # name(modification) "comment" pattern を解析
        match = re.match(r'([A-Za-z_]\w*)(\s*\[[^\]]*\])?(\([^)]*\))?\s*(?:"([^"]*)")?', decl)
        if match:
            result = {
                "name": match.group(1),
                "array_dims": match.group(2),
                "modifications": _parse_modifications(match.group(3) or ""),
                "comment": match.group(4)
            }
            results.append(result)
    
    return results


def _parse_modifications(mod_str: str) -> Dict[str, str]:
    """(R=100, L=0.1, redeclare package Medium = Water) 形式の変更を解析"""
    if not mod_str or not mod_str.strip("()"):
        return {}
    
    content = mod_str.strip("()")
    modifications = {}
    
    # redeclare文の処理
    redeclare_matches = re.findall(r'redeclare\s+([^,)]+)', content)
    for i, redecl in enumerate(redeclare_matches):
        modifications[f"redeclare_{i}"] = redecl.strip()
    
    # name=value 形式を抽出
    for match in re.finditer(r'([A-Za-z_]\w*)\s*=\s*([^,)]+)', content):
        key = match.group(1).strip()
        value = match.group(2).strip()
        # 既にredeclareで処理済みでない場合のみ
        if not any(redecl for redecl in redeclare_matches if key in redecl):
            modifications[key] = value
    
    return modifications


def _parse_attributes(attr_str: str) -> Dict[str, str]:
    """(unit="V", start=0, min=-10, max=10) 形式の属性を解析"""
    if not attr_str:
        return {}
    
    content = attr_str.strip("()")
    attributes = {}
    
    # より詳細な属性解析
    patterns = [
        (r'unit\s*=\s*"([^"]*)"', "unit"),
        (r'displayUnit\s*=\s*"([^"]*)"', "displayUnit"), 
        (r'quantity\s*=\s*"([^"]*)"', "quantity"),
        (r'start\s*=\s*([^,)]+)', "start"),
        (r'min\s*=\s*([^,)]+)', "min"),
        (r'max\s*=\s*([^,)]+)', "max"),
        (r'nominal\s*=\s*([^,)]+)', "nominal"),
        (r'fixed\s*=\s*([^,)]+)', "fixed"),
        (r'stateSelect\s*=\s*([^,)]+)', "stateSelect")
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, content)
        if match:
            attributes[key] = match.group(1).strip()
    
    return attributes


def _smart_comma_split(text: str) -> List[str]:
    """括弧のネストを考慮してカンマで分割"""
    parts = []
    current = ""
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    
    for char in text:
        if char == '(':
            depth_paren += 1
        elif char == ')':
            depth_paren -= 1
        elif char == '[':
            depth_bracket += 1
        elif char == ']':
            depth_bracket -= 1
        elif char == '{':
            depth_brace += 1
        elif char == '}':
            depth_brace -= 1
        elif char == ',' and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
            parts.append(current.strip())
            current = ""
            continue
        
        current += char
    
    if current.strip():
        parts.append(current.strip())
    
    return parts


# 予約語リストを定義
MODELICA_KEYWORDS = {
    'algorithm', 'and', 'annotation', 'assert', 'block', 'break', 'class', 
    'connect', 'connector', 'constant', 'constrainedby', 'der', 'discrete',
    'each', 'else', 'elseif', 'elsewhen', 'end', 'enumeration', 'equation',
    'expandable', 'extends', 'external', 'false', 'final', 'flow', 'for',
    'function', 'if', 'import', 'impure', 'in', 'initial', 'inner', 'input',
    'loop', 'model', 'not', 'operator', 'or', 'outer', 'output', 'package',
    'parameter', 'partial', 'protected', 'public', 'pure', 'record', 'redeclare',
    'replaceable', 'return', 'stream', 'then', 'true', 'type', 'when', 'while', 'within'
}

def _is_valid_component_type(type_name: str) -> bool:
    """コンポーネント型が有効かチェック"""
    # 基本的な予約語チェック
    if type_name.lower() in MODELICA_KEYWORDS:
        return False
    
    # 単語境界での予約語チェック
    base_type = type_name.split('.')[0] if '.' in type_name else type_name
    if base_type.lower() in MODELICA_KEYWORDS:
        return False
    
    # 有効な型名パターン（修飾名または基本型）
    if not re.match(r'^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$', type_name):
        return False
    
    return True

def _extract_components(node: Node, src: bytes, code_text: str) -> List[ComponentDeclaration]:
    """コンポーネント宣言の抽出（予約語フィルタリング付き）"""
    components = []
    
    # annotation除去版のテキストで処理
    clean_text = _strip_annotations(code_text)
    
    for match in COMPONENT_DECL_RE.finditer(clean_text):
        prefixes_str = match.group("prefixes") or ""
        prefixes = [p.strip() for p in prefixes_str.split() if p.strip()]
        type_name = match.group("type").strip()
        declarations = match.group("declarations")
        
        # $D83D$DD25 重要：予約語チェック
        if not _is_valid_component_type(type_name):
            continue
            
        # parameterプレフィックスがある場合はスキップ
        if "parameter" in prefixes:
            continue
            
        # カンマ区切りの複数宣言を解析
        for decl in _parse_component_declarations(declarations):
            comp = ComponentDeclaration(
                name=decl["name"],
                type_name=type_name,
                prefixes=prefixes,
                modifications=decl.get("modifications", {}),
                array_dims=decl.get("array_dims"),
                comment=decl.get("comment")
            )
            components.append(comp)
    
    return components

def _extract_enhanced_parameters(code_text: str) -> List[Parameter]:
    """強化されたパラメータ抽出"""
    parameters = []
    
    # 1. 従来のparameter宣言
    clean_text = _strip_annotations(code_text)
    
    # より包括的なパラメータパターン
    ENHANCED_PARAM_PATTERNS = [
        # 基本的なparameter宣言
        r'parameter\s+([A-Za-z_][\w\.]*(?:\[[^\]]*\])?)\s+([A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*(?:=\s*([^;]+))?\s*(?:"([^"]*)")?\s*;',
        
        # constant宣言（パラメータ的扱い）
        r'constant\s+([A-Za-z_][\w\.]*(?:\[[^\]]*\])?)\s+([A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*=\s*([^;]+)\s*(?:"([^"]*)")?\s*;',
        
        # final parameter
        r'final\s+parameter\s+([A-Za-z_][\w\.]*(?:\[[^\]]*\])?)\s+([A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*(?:=\s*([^;]+))?\s*(?:"([^"]*)")?\s*;',
    ]
    
    for pattern in ENHANCED_PARAM_PATTERNS:
        for match in re.finditer(pattern, clean_text, re.MULTILINE):
            param_type = match.group(1)
            param_name = match.group(2) 
            param_default = match.group(3) if len(match.groups()) > 2 and match.group(3) else ""
            param_desc = match.group(4) if len(match.groups()) > 3 and match.group(4) else ""
            
            parameters.append(Parameter(
                name=param_name,
                type=param_type,
                default=param_default.strip() if param_default else "",
                description=param_desc.strip() if param_desc else None
            ))
    
    # 2. 属性付きパラメータの詳細解析
    for match in re.finditer(
        r'parameter\s+([A-Za-z_][\w\.]*)\s+([A-Za-z_]\w*)\s*\(([^)]+)\)\s*(?:=\s*([^;]+))?\s*;',
        clean_text
    ):
        param_type = match.group(1)
        param_name = match.group(2)
        attributes = match.group(3)
        param_default = match.group(4) if match.group(4) else ""
        
        # 属性から詳細情報を抽出
        unit_match = re.search(r'unit\s*=\s*"([^"]*)"', attributes)
        min_match = re.search(r'min\s*=\s*([^,)]+)', attributes)
        max_match = re.search(r'max\s*=\s*([^,)]+)', attributes)
        
        param = Parameter(
            name=param_name,
            type=param_type,
            default=param_default.strip() if param_default else "",
            description=None
        )
        
        # メタデータに属性情報を追加
        if hasattr(param, 'meta'):
            param.meta = {}
        else:
            param.meta = {}
            
        if unit_match:
            param.meta['unit'] = unit_match.group(1)
        if min_match:
            param.meta['min'] = min_match.group(1).strip()
        if max_match:
            param.meta['max'] = max_match.group(1).strip()
            
        parameters.append(param)
    
    return parameters


def _extract_comprehensive_physical_quantities(variables: List[VariableDeclaration], 
                                               code_text: str) -> List[PhysicalQuantity]:
    """包括的な物理量抽出"""
    quantities = []
    
    # 1. 変数の属性から抽出（既存）
    for var in variables:
        if "unit" in var.attributes or "quantity" in var.attributes:
            quantities.append(PhysicalQuantity(
                name=var.name,
                unit=var.attributes.get("unit"),
                display_unit=var.attributes.get("displayUnit"),
                quantity=var.attributes.get("quantity"),
                nominal=var.attributes.get("nominal")
            ))
    
    # 2. SI型からの自動抽出
    SI_UNITS_MAP = {
        'SI.Voltage': {'unit': 'V', 'quantity': 'ElectricPotential'},
        'SI.Current': {'unit': 'A', 'quantity': 'ElectricCurrent'},
        'SI.Resistance': {'unit': 'Ohm', 'quantity': 'ElectricResistance'},
        'SI.Power': {'unit': 'W', 'quantity': 'Power'},
        'SI.Energy': {'unit': 'J', 'quantity': 'Energy'},
        'SI.Force': {'unit': 'N', 'quantity': 'Force'},
        'SI.Torque': {'unit': 'N.m', 'quantity': 'Torque'},
        'SI.Temperature': {'unit': 'K', 'quantity': 'ThermodynamicTemperature'},
        'SI.Pressure': {'unit': 'Pa', 'quantity': 'Pressure'},
        'SI.Density': {'unit': 'kg/m3', 'quantity': 'Density'},
        'SI.Velocity': {'unit': 'm/s', 'quantity': 'Velocity'},
        'SI.Acceleration': {'unit': 'm/s2', 'quantity': 'Acceleration'},
        'SI.Length': {'unit': 'm', 'quantity': 'Length'},
        'SI.Mass': {'unit': 'kg', 'quantity': 'Mass'},
        'SI.Time': {'unit': 's', 'quantity': 'Time'},
        'SI.Frequency': {'unit': 'Hz', 'quantity': 'Frequency'},
        'SI.AngularVelocity': {'unit': 'rad/s', 'quantity': 'AngularVelocity'},
    }
    
    # SI型の変数を検索
    for var in variables:
        if var.type_name in SI_UNITS_MAP:
            si_info = SI_UNITS_MAP[var.type_name]
            # 重複チェック
            if not any(q.name == var.name for q in quantities):
                quantities.append(PhysicalQuantity(
                    name=var.name,
                    unit=si_info['unit'],
                    quantity=si_info['quantity'],
                    display_unit=var.attributes.get("displayUnit"),
                    nominal=var.attributes.get("nominal")
                ))
    
    # 3. コメントからの単位抽出
    unit_comment_pattern = r'([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*"[^"]*\[([^\]]+)\]'
    for match in re.finditer(unit_comment_pattern, code_text):
        var_name = match.group(1)
        unit_str = match.group(2)
        if not any(q.name == var_name for q in quantities):
            quantities.append(PhysicalQuantity(
                name=var_name,
                unit=unit_str,
                quantity=None,  # コメントからは推定困難
                display_unit=None,
                nominal=None
            ))
    
    return quantities

def _extract_connections(code_text: str) -> List[Connection]:
    """Connect文の抽出
    
    例: "connect(R1.p, C1.p);" -> Connection(from_connector="R1.p", to_connector="C1.p")
    """
    connections = []
    
    for match in CONNECT_RE.finditer(code_text):
        conn = Connection(
            from_connector=match.group("from").strip(),
            to_connector=match.group("to").strip()
        )
        connections.append(conn)
    
    return connections


def _extract_variables(code_text: str) -> List[VariableDeclaration]:
    """変数宣言の抽出（制御構文除外強化版）"""
    variables = []
    
    # annotationー除去版のテキストで処理
    clean_text = _strip_annotations(code_text)
    
    # 制御構文キーワードの定義
    CONTROL_KEYWORDS = {
        'if', 'then', 'else', 'elseif', 'end', 'for', 'while', 'when', 
        'equation', 'algorithm', 'initial', 'terminal', 'discrete',
        'loop', 'break', 'return', 'assert'
    }
    
    # Modelica予約語の定義
    RESERVED_WORDS = {
        'and', 'or', 'not', 'true', 'false', 'der', 'initial', 'terminal',
        'noEvent', 'smooth', 'min', 'max', 'abs', 'sign', 'sqrt', 'exp', 
        'log', 'sin', 'cos', 'tan', 'within', 'import', 'extends', 'public',
        'protected', 'partial', 'final', 'each', 'replaceable', 'redeclare'
    }
    
    for match in VARIABLE_DECL_RE.finditer(clean_text):
        prefixes_str = match.group("prefixes") or ""
        prefixes = [p.strip() for p in prefixes_str.split() if p.strip()]
        
        # parameterプレフィックスがある場合はスキップ
        if "parameter" in prefixes:
            continue
        
        name = match.group("name")
        type_name = match.group("type")
        
        # 基本的な除外チェック
        if not name or not type_name:
            continue
        
        # 制御キーワードを除外
        if name.lower() in CONTROL_KEYWORDS:
            continue
        
        # 予約語を除外
        if name.lower() in RESERVED_WORDS:
            continue
        
        # 型名も制御キーワードでないことを確認
        if type_name.lower() in CONTROL_KEYWORDS:
            continue
        
        # コンテキストチェック：制御構文の一部でないことを確認
        start_pos = match.start()
        end_pos = match.end()
        
        # 前後の文脈を取得（行の境界を考慮）
        line_start = clean_text.rfind('\n', 0, start_pos) + 1
        line_end = clean_text.find('\n', end_pos)
        if line_end == -1:
            line_end = len(clean_text)
        
        line_text = clean_text[line_start:line_end].strip()
        
        # 制御構文パターンを除外
        control_patterns = [
            r'\bif\s+.*\bthen\b',
            r'\belse\s*$',
            r'\belseif\s+.*\bthen\b',
            r'\bend\s+if\b',
            r'\bfor\s+.*\bloop\b',
            r'\bwhile\s+.*\bloop\b',
            r'\bwhen\s+.*\bthen\b',
            r'^\s*equation\s*$',
            r'^\s*algorithm\s*$'
        ]
        
        is_control_structure = False
        for pattern in control_patterns:
            if re.search(pattern, line_text, re.IGNORECASE):
                is_control_structure = True
                break
        
        if is_control_structure:
            continue
        
        # より大きなコンテキストでの除外チェック
        context_start = max(0, start_pos - 100)
        context_end = min(len(clean_text), end_pos + 100)
        context = clean_text[context_start:context_end]
        
        # if-then-else文の中にある場合は除外
        if_then_pattern = r'\bif\s+[^;]*?' + re.escape(name) + r'[^;]*?\bthen\b'
        if re.search(if_then_pattern, context, re.IGNORECASE | re.DOTALL):
            continue
        
        # 関数呼び出しの引数として使われている場合は除外
        func_call_pattern = r'\w+\s*\([^)]*\b' + re.escape(name) + r'\b[^)]*\)'
        if re.search(func_call_pattern, context):
            continue
        
        # 有効な変数宣言として処理
        attributes = _parse_attributes(match.group("attributes") or "")
        binding = match.group("binding")
        if binding:
            binding = binding.strip().lstrip("=").strip()
            
            # バインディング式も制御構文でないことを確認
            if any(keyword in binding.lower() for keyword in ['if ', 'then ', 'else ', 'end ']):
                # 制御構文を含むバインディングは簡略化
                if len(binding) > 50:
                    binding = binding[:47] + "..."
        
        comment = match.group("comment")
        if comment:
            comment = comment.strip('"')
        
        # 型名の検証
        valid_type_patterns = [
            r'^Real$', r'^Integer$', r'^Boolean$', r'^String$',
            r'^SI\.\w+$', r'^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$'
        ]
        
        is_valid_type = any(re.match(pattern, type_name) for pattern in valid_type_patterns)
        if not is_valid_type:
            continue
        
        # 変数宣言として追加
        var = VariableDeclaration(
            name=name,
            type_name=type_name, 
            prefixes=prefixes,
            attributes=attributes,
            binding_equation=binding,
            comment=comment
        )
        variables.append(var)
    
    # 重複除去（名前ベース）
    seen_names = set()
    unique_variables = []
    for var in variables:
        if var.name not in seen_names:
            seen_names.add(var.name)
            unique_variables.append(var)
    
    return unique_variables


def _extract_physical_quantities(variables: List[VariableDeclaration]) -> List[PhysicalQuantity]:
    """変数から物理量情報を抽出"""
    quantities = []
    
    for var in variables:
        if "unit" in var.attributes or "quantity" in var.attributes:
            quant = PhysicalQuantity(
                name=var.name,
                unit=var.attributes.get("unit"),
                display_unit=var.attributes.get("displayUnit"),
                quantity=var.attributes.get("quantity"),
                nominal=var.attributes.get("nominal")
            )
            quantities.append(quant)
    
    return quantities


def _extract_dependencies(code_text: str) -> List[str]:
    deps = set()
    
    # import文の直接抽出
    for match in re.finditer(r'import\s+([A-Za-z_][\w\.]*)', code_text):
        deps.add(match.group(1))
    
    # 修飾名での型・関数参照（ビルトインを除外）
    builtin_funcs = {'exp', 'sin', 'cos', 'log', 'sqrt', 'abs', 'max', 'min', 'sum', 
                     'zeros', 'identity', 'fill', 'size', 'scalar', 'transpose', 'matrix'}
    
    for match in re.finditer(r'\b([A-Za-z_][\w\.]*\.[A-Za-z_]\w*)', code_text):
        qualified_name = match.group(1)
        base_name = qualified_name.split('.')[-1]
        if base_name not in builtin_funcs and '.' in qualified_name:
            # パッケージ部分を抽出
            package = '.'.join(qualified_name.split('.')[:-1])
            deps.add(package)
    
    return sorted(list(deps))


def _build_inheritance_chain(extends_list: List[str], package_path: List[str]) -> List[str]:
    """継承チェーンを構築（簡易版・後で拡張可能）"""
    # 現在は単純にextends_listを返すが、後で完全なチェーン解決に拡張可能
    return extends_list


# メイン抽出関数

def extract_symbols_from_file(file_path: str) -> List[SymbolRecord]:
    """ファイルからシンボルを抽出する（RAG最適化版）"""
    src = file_bytes(file_path)
    parser = new_parser()
    tree = parser.parse(src)
    root = tree.root_node

    # within ヘッダを最優先。無ければパス由来のヒント（従来互換）
    base_pkg = _parse_within_header(src)
    if not base_pkg:
        base_pkg = []

    symbols: List[SymbolRecord] = []
    stack: List[Tuple[Node, List[str]]] = [(root, base_pkg)]

    while stack:
        node, pkg = stack.pop()

        # 型ヒントに引っかかったもの だけを重めのヘッダ判定へ
        if _guess_kind(node.type) != "unknown":
            defn = _is_symbol_definition(node, src)
            if defn:
                kind, name = defn
                fqn = _make_fqn(pkg, name)
                span = _span_of(node, file_path)
                code_text = _node_text(src, node)
                doc = _leading_comment(src, node)
                
                # RAG用にクリーンアップされたテキストを生成
                clean_code_text = _strip_annotations(code_text)
                
                equations = _collect_equations(node, src, file_path)

                # 新機能：インターフェース情報を抽出
                interfaces = _extract_interfaces(clean_code_text)
                
                # 新機能：Documentation内容を抽出
                doc_content = _extract_documentation_content(code_text)
                enhanced_docstring = doc_content or doc

                # 強化された抽出処理
                components = _extract_components(node, src, clean_code_text)
                connections = _extract_connections(clean_code_text)  
                variables = _extract_variables(clean_code_text)
                physical_quantities = _extract_comprehensive_physical_quantities(variables, clean_code_text)
                dependencies = _extract_dependencies(clean_code_text)
                
                # extends/importsの抽出（既存）
                extends_list = list(dict.fromkeys(EXTENDS_RE.findall(clean_code_text)))
                imports_list = list(dict.fromkeys(IMPORT_RE.findall(clean_code_text)))
                inheritance_chain = _build_inheritance_chain(extends_list, pkg)

                # 強化されたパラメータ抽出
                enhanced_parameters = _extract_enhanced_parameters(clean_code_text)

                rec = SymbolRecord(
                    fqn=fqn, kind=kind, name=name, package_path=pkg,
                    extends=extends_list, imports=imports_list, parameters=[], equations=equations,
                    docstring=enhanced_docstring,  # 強化されたdocstring
                    code_span=span, code_text=clean_code_text, checksum=sha1_text(clean_code_text),  # クリーンアップ版を使用
                    
                    # 新規フィールド
                    components=components,
                    connections=connections,
                    variables=variables, 
                    physical_quantities=physical_quantities,
                    dependencies=dependencies,
                    inheritance_chain=inheritance_chain,
                    
                    meta={
                        "node_type": node.type,
                        "uid": f"{span.file_path}:{span.start_line}-{span.end_line}",
                        "interfaces": interfaces,  # 新規：インターフェース情報
                        "rag_optimized": True,     # RAG最適化フラグ
                    }
                )
                
                # 物理的意味情報を抽出して追加
                physical_semantics = _extract_physical_semantics(rec)
                if physical_semantics:
                    rec.meta["physical_semantics"] = physical_semantics

                # 既存のparameterの抽出（そのまま維持）
                ps = []
                text_no_anno = clean_code_text

                # 1) 単一宣言
                for typ, name_p, default in PARAM_RE_1.findall(text_no_anno):
                    ps.append(Parameter(name=name_p, type=(typ or None), default=_clean_default(default or "")))

                # 2) 複数宣言（カンマ区切り）
                for typ, names_blob in PARAM_RE_MULTI.findall(text_no_anno):
                    for name_p, default in _split_decl_names(names_blob):
                        ps.append(Parameter(name=name_p, type=(typ or None), default=_clean_default(default or "")))

                rec.parameters = ps

                symbols.append(rec)

                # スコープ拡張：本物の定義にだけ適用
                next_pkg = pkg + [name]
            else:
                next_pkg = pkg
        else:
            next_pkg = pkg

        for i in range(node.child_count):
            stack.append((node.child(i), next_pkg))

    return symbols


def extract_dir(directory_path: Path, progress_callback=None) -> List[SymbolRecord]:
    """ディレクトリからシンボルを抽出（進捗コールバック対応）"""
    records = []
    
    if progress_callback:
        progress_callback("ディレクトリスキャン中...", 10)
    
    # 既存の処理を維持しつつ、進捗を更新
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.mo'):
                file_path = Path(root) / file
                try:
                    file_records = extract_symbols_from_file(str(file_path))
                    records.extend(file_records)
                    
                    if progress_callback:
                        # 進捗を更新（例: ファイル数に基づく）
                        progress = min(90, len(records) * 10)  # 仮の計算
                        progress_callback(f"処理中: {file_path.name}", progress)
                        
                except Exception as e:
                    print(f"ファイル処理エラー: {file_path} - {e}")
    
    if progress_callback:
        progress_callback("抽出完了", 100)
    
    return records

def _extract_interfaces(code_text: str) -> List[Dict[str, Any]]:
    """物理インターフェース（ポート、入力等）の抽出"""
    interfaces = []
    
    # 制御インターフェース（RealInput, RealOutput等）
    control_patterns = [
        (r'(\w+\.)*RealInput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'RealInput'),
        (r'(\w+\.)*RealOutput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'RealOutput'),
        (r'(\w+\.)*BooleanInput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'BooleanInput'),
        (r'(\w+\.)*BooleanOutput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'BooleanOutput'),
        (r'(\w+\.)*IntegerInput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'IntegerInput'),
        (r'(\w+\.)*IntegerOutput\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'IntegerOutput'),
    ]
    
    # 物理ポート
    port_patterns = [
        (r'(\w+\.)*HeatPort_[ab]\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'HeatPort'),
        (r'(\w+\.)*FluidPort_[ab]\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'FluidPort'),
        (r'(\w+\.)*ElectricalPin\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'ElectricalPin'),
        (r'(\w+\.)*PositivePin\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'ElectricalPin'),
        (r'(\w+\.)*NegativePin\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'ElectricalPin'),
        (r'(\w+\.)*Pin\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'ElectricalPin'),
        (r'(\w+\.)*Flange_[ab]\s+(\w+)(?:\([^)]*\))?\s*(?:"([^"]*)")?', 'MechanicalFlange'),
    ]
    
    # 制御インターフェースを抽出
    for pattern, interface_type in control_patterns:
        for match in re.finditer(pattern, code_text):
            interfaces.append({
                "name": match.group(2),
                "type": "control",
                "subtype": interface_type,
                "description": match.group(3) if len(match.groups()) > 2 and match.group(3) else None,
                "direction": "input" if "Input" in interface_type else "output"
            })
    
    # 物理ポートを抽出
    for pattern, interface_type in port_patterns:
        for match in re.finditer(pattern, code_text):
            interfaces.append({
                "name": match.group(2),
                "type": "physical",
                "subtype": interface_type,
                "description": match.group(3) if len(match.groups()) > 2 and match.group(3) else None,
                "direction": "bidirectional"
            })
    
    return interfaces


def _extract_documentation_content(code_text: str) -> str:
    """Documentation内のHTMLから有用なテキストを抽出"""
    # Documentation(info="...") パターンを検索
    doc_pattern = r'Documentation\s*\(\s*info\s*=\s*"(.*?)"(?:\s*,|\s*\))'
    doc_match = re.search(doc_pattern, code_text, re.DOTALL)
    
    if not doc_match:
        return None
    
    html_content = doc_match.group(1)
    
    # HTMLタグを除去してプレーンテキストを抽出
    # <p>, <a>, <br>等のタグを適切に処理
    text = re.sub(r'<br\s*/?>', ' ', html_content)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<a[^>]*href="[^"]*"[^>]*>', '', text)
    text = re.sub(r'</a>', '', text)
    text = re.sub(r'<[^>]+>', '', text)  # 残りのHTMLタグを除去
    
    # HTML entities の処理
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    
    # 複数の空白・改行を整理
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text and len(text) > 10 else None


def _extract_physical_semantics(record) -> Dict[str, Any]:
    """物理的意味・用途を抽出（修正版）"""
    semantics = {}
    
    if not record.name:
        return semantics
    
    name_lower = record.name.lower()
    
    # ドメインの推定（まずドメインを確定）
    domain = None
    if any(word in name_lower for word in ['heat', 'thermal', 'temperature', 'convect']):
        domain = 'thermal'
    elif any(word in name_lower for word in ['electric', 'electrical', 'voltage', 'current', 'resistor', 'capacitor']):
        domain = 'electrical'
    elif any(word in name_lower for word in ['rotational', 'mechanical', 'torque', 'force', 'motion', 'backlash', 'spring', 'damper']):
        domain = 'mechanical'
    elif any(word in name_lower for word in ['fluid', 'hydraulic', 'pneumatic', 'flow']):
        domain = 'fluid'
    
    # パッケージパスからもドメインを推定
    if hasattr(record, 'package_path') and record.package_path:
        package_str = '.'.join(record.package_path).lower()
        if 'thermal' in package_str:
            domain = 'thermal'
        elif 'electrical' in package_str:
            domain = 'electrical'
        elif 'rotational' in package_str or 'translational' in package_str:
            domain = 'mechanical'
        elif 'fluid' in package_str:
            domain = 'fluid'
    
    if domain:
        semantics['domain'] = domain
    
    # ドメインに基づいて物理現象を推定
    if domain == 'mechanical':
        if any(word in name_lower for word in ['spring', 'elastic']):
            semantics['phenomenon'] = 'elasticity'
            semantics['physical_law'] = 'hookes_law'
        elif any(word in name_lower for word in ['damper', 'friction']):
            semantics['phenomenon'] = 'damping'
            semantics['physical_law'] = 'viscous_damping'
        elif 'backlash' in name_lower:
            semantics['phenomenon'] = 'backlash'
            semantics['physical_law'] = 'nonlinear_contact'
    elif domain == 'thermal':
        if any(word in name_lower for word in ['convect', 'convection']):
            semantics['phenomenon'] = 'convection'
            semantics['physical_law'] = 'heat_convection'
        elif any(word in name_lower for word in ['conduct', 'conduction']):
            semantics['phenomenon'] = 'conduction'
            semantics['physical_law'] = 'heat_conduction'
    elif domain == 'electrical':
        if any(word in name_lower for word in ['resistor', 'resistance']):
            semantics['phenomenon'] = 'resistance'
            semantics['physical_law'] = 'ohms_law'
    
    return semantics