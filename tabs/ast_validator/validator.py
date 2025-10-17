from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
import hashlib
import json
from pathlib import Path

try:
    from jsonschema import Draft7Validator  # type: ignore
except ImportError:  # pragma: no cover
    Draft7Validator = None


@dataclass
class ValidationIssue:
    level: str  # info|warn|error
    code: str
    message: str
    target_id: str | None = None


class JSONLQualityValidator:
    """Validate intermediate symbol records before JSONL変換."""

    def __init__(self,
                 max_content_len: int = 8000,
                 warn_content_len: int = 4000,
                 max_params: int = 200,
                 max_components: int = 200,
                 max_equations: int = 200):
        self.max_content_len = max_content_len
        self.warn_content_len = warn_content_len
        self.max_params = max_params
        self.max_components = max_components
        self.max_equations = max_equations

    def _content_estimate(self, rec: Dict[str, Any]) -> int:
        # Rough estimate: name+doc+counts
        doc = rec.get("documentation") or rec.get("docstring") or ""
        params = rec.get("parameters", [])
        comps = rec.get("components", [])
        eqs = rec.get("equations", [])
        base = len((rec.get("kind", "") + rec.get("name", "")).encode("utf-8"))
        extra = len((doc if isinstance(doc, str) else str(doc)).encode("utf-8"))
        # assume average item footprint
        return base + extra + 80 * (len(params) + len(comps)) + 120 * len(eqs)

    def _hash_signature(self, rec: Dict[str, Any]) -> str:
        # Signature based on kind+fqn+counts+lightweight doc
        doc = rec.get("documentation") or rec.get("docstring") or ""
        doc_snip = doc[:512] if isinstance(doc, str) else str(doc)[:512]
        s = "\u001f".join([
            rec.get("kind", ""),
            rec.get("fqn", rec.get("name", "")),
            str(len(rec.get("parameters", []))),
            str(len(rec.get("components", []))),
            str(len(rec.get("equations", []))),
            doc_snip,
        ])
        return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

    def validate(self, records: List[Dict[str, Any]]) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        issues: List[ValidationIssue] = []
        stats = {
            "total": len(records),
            "kinds": {},
            "max_estimated_len": 0,
            "over_warn": 0,
            "over_max": 0,
            "dupe_ids": 0,
            "dupe_signatures": 0,
        }

        id_counts: Dict[str, int] = {}
        sig_counts: Dict[str, int] = {}

        for rec in records:
            kind = rec.get("kind", "unknown")
            stats["kinds"][kind] = stats["kinds"].get(kind, 0) + 1

            fqn = rec.get("fqn") or rec.get("name") or ""
            if not fqn or kind == "unknown":
                issues.append(ValidationIssue("error", "MISSING_CORE", "Record missing fqn/kind", fqn or "<unknown>"))

            est = self._content_estimate(rec)
            stats["max_estimated_len"] = max(stats["max_estimated_len"], est)
            if est > self.warn_content_len:
                stats["over_warn"] += 1
            if est > self.max_content_len:
                stats["over_max"] += 1
                issues.append(ValidationIssue("warn", "OVERSIZE", f"Estimated content {est} exceeds {self.max_content_len}", fqn))

            # Section size sanity
            if len(rec.get("parameters", [])) > self.max_params:
                issues.append(ValidationIssue("warn", "MANY_PARAMS", "Too many parameters", fqn))
            if len(rec.get("components", [])) > self.max_components:
                issues.append(ValidationIssue("warn", "MANY_COMPONENTS", "Too many components", fqn))
            if len(rec.get("equations", [])) > self.max_equations:
                issues.append(ValidationIssue("info", "MANY_EQUATIONS", "Many equations blocks", fqn))

            # Collect dup candidates
            id_counts[fqn] = id_counts.get(fqn, 0) + 1
            sig = self._hash_signature(rec)
            sig_counts[sig] = sig_counts.get(sig, 0) + 1

        # Aggregate dup results
        dupe_ids = sum(1 for n in id_counts.values() if n > 1)
        dupe_sigs = sum(1 for n in sig_counts.values() if n > 1)
        stats["dupe_ids"] = dupe_ids
        stats["dupe_signatures"] = dupe_sigs

        if dupe_ids:
            issues.append(ValidationIssue("warn", "DUPLICATE_IDS", f"Duplicate ids across {dupe_ids} keys"))
        if dupe_sigs:
            issues.append(ValidationIssue("info", "DUPLICATE_CONTENT", f"Duplicate-like content across {dupe_sigs} signatures"))

        return issues, stats


class SchemaValidator:
    """Validate final JSON objects against a JSON Schema."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.validator = None
        if Draft7Validator is not None and schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.validator = Draft7Validator(schema)

    def validate_lines(self, json_lines: List[str]) -> List[ValidationIssue]:
        if self.validator is None:
            return []
        issues: List[ValidationIssue] = []
        for idx, line in enumerate(json_lines, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(ValidationIssue("error", "JSON_PARSE", f"line {idx}: {exc}"))
                continue
            for error in self.validator.iter_errors(obj):
                issues.append(
                    ValidationIssue(
                        "error",
                        "SCHEMA",
                        f"line {idx}: {error.message}",
                    )
                )
        return issues

