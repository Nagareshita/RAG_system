# ast_only/src/modelica/models.py
"""
データモデル定義
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal

Kind = Literal["package", "class", "model", "block", "connector", "function", "record", "type", "unknown"]

@dataclass
class CodeSpan:
    file_path: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int

@dataclass
class Parameter:
    name: str
    type: Optional[str] = None
    default: str = ""
    description: Optional[str] = None

@dataclass
class EquationBlock:
    equations: List[str] = field(default_factory=list)
    span: Optional[CodeSpan] = None

@dataclass
class ComponentDeclaration:
    name: str
    type_name: str
    prefixes: List[str] = field(default_factory=list)
    modifications: Dict[str, str] = field(default_factory=dict)
    array_dims: Optional[str] = None
    comment: Optional[str] = None

@dataclass
class Connection:
    from_connector: str
    to_connector: str

@dataclass
class VariableDeclaration:
    name: str
    type_name: str
    prefixes: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    binding_equation: Optional[str] = None
    comment: Optional[str] = None

@dataclass
class PhysicalQuantity:
    name: str
    unit: Optional[str] = None
    display_unit: Optional[str] = None
    quantity: Optional[str] = None
    nominal: Optional[str] = None

@dataclass
class SymbolRecord:
    fqn: str
    kind: Kind
    name: str
    package_path: List[str] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    equations: List[EquationBlock] = field(default_factory=list)
    docstring: Optional[str] = None
    code_span: Optional[CodeSpan] = None
    code_text: Optional[str] = None
    checksum: Optional[str] = None
    components: List[ComponentDeclaration] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    variables: List[VariableDeclaration] = field(default_factory=list)
    physical_quantities: List[PhysicalQuantity] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    inheritance_chain: List[str] = field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "fqn": self.fqn,
            "kind": self.kind,
            "name": self.name,
            "package_path": self.package_path,
            "extends": self.extends,
            "imports": self.imports,
            "docstring": self.docstring,
            "dependencies": self.dependencies,
            "inheritance_chain": self.inheritance_chain,
            "meta": self.meta or {}
        }
        
        # リスト型フィールドを辞書化
        result["parameters"] = [
            {
                "name": p.name,
                "type": p.type,
                "default": p.default,
                "description": p.description
            } for p in self.parameters
        ]
        
        result["components"] = [
            {
                "name": c.name,
                "type_name": c.type_name,
                "prefixes": c.prefixes,
                "modifications": c.modifications,
                "array_dims": c.array_dims,
                "comment": c.comment
            } for c in self.components
        ]
        
        result["connections"] = [
            {
                "from_connector": c.from_connector,
                "to_connector": c.to_connector
            } for c in self.connections
        ]
        
        result["variables"] = [
            {
                "name": v.name,
                "type_name": v.type_name,
                "prefixes": v.prefixes,
                "attributes": v.attributes,
                "binding_equation": v.binding_equation,
                "comment": v.comment
            } for v in self.variables
        ]
        
        result["physical_quantities"] = [
            {
                "name": pq.name,
                "unit": pq.unit,
                "display_unit": pq.display_unit,
                "quantity": pq.quantity,
                "nominal": pq.nominal
            } for pq in self.physical_quantities
        ]
        
        result["equations"] = [
            {
                "equations": eq.equations,
                "span": {
                    "file_path": eq.span.file_path,
                    "start_line": eq.span.start_line,
                    "end_line": eq.span.end_line,
                    "start_col": eq.span.start_col,
                    "end_col": eq.span.end_col
                } if eq.span else None
            } for eq in self.equations
        ]
        
        # CodeSpan
        if self.code_span:
            result["code_span"] = {
                "file_path": self.code_span.file_path,
                "start_line": self.code_span.start_line,
                "end_line": self.code_span.end_line,
                "start_col": self.code_span.start_col,
                "end_col": self.code_span.end_col
            }
        
        result["code_text"] = self.code_text
        result["checksum"] = self.checksum
        
        return result