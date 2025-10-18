from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from tabs.ast_validator.modelica_models import SymbolRecord


@dataclass
class RepoContext:
    repo: str = "local"
    commit: str = "WORKTREE"
    version: str = "1.0.0"


_EQ_VAR_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
_UNIT_IN_COMMENT = re.compile(r"\[(?P<unit>[^\]]+)\]")
_FQN_RE = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*$")


def _safe_unit(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _UNIT_IN_COMMENT.search(text)
    return match.group("unit") if match else None


def _clean_text(text: str, min_length: int = 0) -> str:
    cleaned = text.strip()
    if min_length and len(cleaned) < min_length:
        padding = " " * (min_length - len(cleaned))
        cleaned += padding
    return cleaned


def build_equation_items(equations: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for eq in equations:
        if not eq:
            continue
        eq_clean = eq.strip().rstrip(";")
        tokens = _EQ_VAR_RE.findall(eq_clean)
        vars_found = sorted({t for t in tokens if not t.isnumeric()})
        ops: List[str] = []
        for marker, op in (
            ("der(", "der"),
            ("pre(", "pre"),
            ("noEvent", "noEvent"),
            ("sample", "sample"),
            ("edge", "edge"),
        ):
            if marker in eq_clean:
                ops.append(op)
        guards: List[str] = []
        if " if " in eq_clean:
            guards.append("if")
        items.append({
            "str": eq_clean,
            "vars": vars_found,
            "guards": guards,
            "ops": ops,
            "phase": "initial" if eq_clean.lower().startswith("initial") else "runtime",
        })
    return items


def _line_range_from_span(span: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if span:
        return {
            "start": int(span.get("start_line", 1)),
            "end": int(span.get("end_line", span.get("start_line", 1))),
        }
    return {"start": 1, "end": 1}


def _component_entry(comp: Dict[str, Any]) -> Dict[str, Any]:
    prefixes = comp.get("prefixes") or []
    if isinstance(prefixes, str):
        prefixes = [prefixes]
    return {
        "name": comp.get("name"),
        "type": comp.get("type_name") or comp.get("type"),
        "prefixes": prefixes,
        "modifications": comp.get("modifications") or {},
        "array_dims": None,
        "comment": comp.get("comment"),
        "condition": None,
    }


def _parameter_entry(param: Dict[str, Any]) -> Dict[str, Any]:
    comment = param.get("description") or ""
    return {
        "name": param.get("name"),
        "type": param.get("type"),
        "default": param.get("default"),
        "unit": _safe_unit(comment),
        "displayUnit": None,
        "min": None,
        "max": None,
        "nominal": None,
        "quantity": None,
        "description": comment.strip() or None,
        "prefixes": ["parameter"] if "parameter" in comment.lower() else [],
    }


def _variable_entry(var: Dict[str, Any]) -> Dict[str, Any]:
    prefixes = var.get("prefixes") or []
    if isinstance(prefixes, str):
        prefixes = [prefixes]
    return {
        "name": var.get("name"),
        "type": var.get("type_name") or var.get("type"),
        "prefixes": prefixes,
        "start": None,
        "fixed": None,
        "binding_equation": var.get("binding_equation"),
        "attributes": var.get("attributes") or {},
    }


def _connections(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for conn in entries:
        out.append({
            "from_connector": conn.get("from_connector") or conn.get("from"),
            "to_connector": conn.get("to_connector") or conn.get("to"),
        })
    return out


def _physical_domain(meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    semantics = meta.get("physical_semantics") if meta else None
    if not isinstance(semantics, dict):
        return None
    domain = semantics.get("domain")
    if not domain:
        return None
    return {
        "domain": semantics.get("domain"),
        "ports": [],
        "quantities": [],
    }


def _statistics(ast_record: Dict[str, Any]) -> Dict[str, int]:
    return {
        "parameters_count": len(ast_record.get("parameters", [])),
        "components_count": len(ast_record.get("components", [])),
        "equations_count": len(ast_record.get("equations", [])),
        "connections_count": len(ast_record.get("connections", [])),
        "variables_count": len(ast_record.get("variables", [])),
        "code_lines": ast_record.get("metadata", {})
        .get("line_range", {})
        .get("end", 1)
        - ast_record.get("metadata", {})
        .get("line_range", {})
        .get("start", 1)
        + 1,
    }


def symbol_to_ast_record(symbol: Dict[str, Any], repo: RepoContext) -> Dict[str, Any]:
    code_text = symbol.get("code_text") or ""
    code_text = _clean_text(code_text, min_length=50)

    code_span = symbol.get("code_span")
    line_range = _line_range_from_span(code_span)
    file_path = (code_span or {}).get("file_path") or symbol.get("meta", {}).get("uid", "?")

    original_checksum = symbol.get("checksum")
    checksum = original_checksum or sha1(code_text.encode("utf-8")).hexdigest()
    fqn = symbol.get("fqn", "unknown")
    kind = symbol.get("kind", "unknown")
    line_start = line_range.get("start", 1)
    line_end = line_range.get("end", line_start)
    record_id = f"{fqn}|{kind}|{repo.version}|{checksum}|{line_start}-{line_end}"

    docstring = symbol.get("docstring") or ""

    extends = symbol.get("extends") or []
    imports = symbol.get("imports") or []

    parameters = [_parameter_entry(p) for p in symbol.get("parameters", [])]
    components = [_component_entry(c) for c in symbol.get("components", [])]
    variables = [_variable_entry(v) for v in symbol.get("variables", [])]

    eq_blocks: List[Dict[str, Any]] = []
    for block in symbol.get("equations", []):
        equations = block.get("equations", [])
        items = build_equation_items(equations)
        eq_blocks.append(
            {
                "section_type": "equation",
                "items": items,
                "location": _line_range_from_span(block.get("span")),
            }
        )
    if not eq_blocks:
        eq_blocks.append({"section_type": "equation", "items": [], "location": line_range})

    ast_record = {
        "id": record_id,
        "kind": kind,
        "name": symbol.get("name"),
        "fqn": fqn,
        "package_path": symbol.get("package_path", []),
        "metadata": {
            "file_path": file_path,
            "line_range": line_range,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checksum": checksum,
            "original_checksum": original_checksum or checksum,
            "version": repo.version,
        },
        "code_text": code_text,
        "inheritance": {
            "extends": [{"base_class": e, "modifications": {}} for e in extends],
            "imports": [
                {
                    "package": imp,
                    "kind": "qualified" if "." in imp else "unqualified",
                }
                for imp in imports
            ],
            "replaceables": [],
        },
        "resolved_modifiers": [],
        "components": components,
        "parameters": parameters,
        "variables": variables,
        "equations": eq_blocks,
        "connections": _connections(symbol.get("connections", [])),
        "stream_info": {
            "has_stream": False,
            "ops": [],
            "medium": None,
            "mixing_equations": False,
        },
        "annotations": {},
        "neighbors": {
            "uses": sorted(
                {
                    dep
                    for dep in (extends + imports + (symbol.get("dependencies") or []))
                    if dep and _FQN_RE.match(dep)
                }
            ),
            "used_by": [],
        },
        "provenance": {
            "repo": repo.repo,
            "commit": repo.commit,
            "file_path": file_path,
            "line_range": line_range,
            "version": repo.version,
            "hash": checksum,
        },
        "meta": {
            "split_policy": {"strategy": "none", "parts": 1, "index": 0},
        },
    }

    doc_clean = docstring.strip()
    if doc_clean:
        ast_record["documentation"] = {"info": doc_clean, "revisions": ""}

    physical_domain = _physical_domain(symbol.get("meta", {}))
    if physical_domain:
        ast_record["physical_domain"] = physical_domain

    ast_record["statistics"] = _statistics(ast_record)

    return ast_record


def make_jsonl_entry(symbol: Dict[str, Any], repo: RepoContext) -> Dict[str, Any]:
    ast_record = symbol_to_ast_record(symbol, repo)
    return {
        "collections": {
            "ast_record": ast_record,
        },
        "validation_rules": {
            "no_duplicate_id": True,
            "ast_required_nonempty": ["parameters", "components", "equations"],
            "require_provenance": True,
            "min_equation_vars": 2,
        },
    }


def compute_statistics(ast_record: Dict[str, Any]) -> Dict[str, int]:
    return _statistics(ast_record)

