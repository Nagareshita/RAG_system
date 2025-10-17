from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

from tabs.ast_validator.record_builder import RepoContext, make_jsonl_entry


@dataclass
class ExportReport:
    written: int = 0
    skipped_unknown_kind: int = 0


ALLOWED_KINDS = {
    "package",
    "model",
    "block",
    "connector",
    "function",
    "record",
    "type",
    "class",
}


def build_jsonl_lines(raw_records: List[Dict[str, object]], repo: RepoContext | None = None) -> Tuple[List[str], ExportReport]:
    repo = repo or RepoContext()
    lines: List[str] = []
    report = ExportReport()

    for rec in raw_records:
        kind = rec.get("kind", "unknown")
        if kind not in ALLOWED_KINDS:
            report.skipped_unknown_kind += 1
            continue
        entry = make_jsonl_entry(rec, repo)
        lines.append(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))
        report.written += 1

    return lines, report

