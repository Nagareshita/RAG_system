from __future__ import annotations

import json
import re
from collections import defaultdict
from copy import deepcopy
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tabs.ast_validator.record_builder import (
    RepoContext,
    build_equation_items,
    compute_statistics,
    symbol_to_ast_record,
)

SOFT_LIMIT = 6000
HARD_LIMIT = 10000

FUNCTION_BLOCK_RE = re.compile(r"(?ms)^\s*function\s+([A-Za-z_]\w*)\b.*?end\s+\1\s*;")
RESERVED_WORDS = {
    "if",
    "then",
    "else",
    "elseif",
    "end",
    "for",
    "while",
    "loop",
    "algorithm",
    "in",
    "and",
    "or",
}
IDENT_RE = re.compile(r"^[A-Za-z_]\w*$")
FQN_RE = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*$")
PART_SUFFIX_RE = re.compile(r"_part(\d+)$")


def _ensure_min_length(text: str, min_length: int = 50) -> str:
    if len(text) >= min_length:
        return text
    padding = " " * (min_length - len(text))
    return text + "\n" + padding


def _strip_function_blocks(code_text: str) -> str:
    if not code_text:
        return code_text
    return FUNCTION_BLOCK_RE.sub("// function extracted\n", code_text)


def _filter_vars(vars_list: List[str]) -> List[str]:
    filtered: List[str] = []
    for token in vars_list:
        if not token:
            continue
        if token in RESERVED_WORDS:
            continue
        if IDENT_RE.match(token) or FQN_RE.match(token):
            filtered.append(token)
    return filtered


def _loc_start(loc: Dict[str, int], default: int) -> int:
    return int(loc.get("line_start", loc.get("start", default)))


def _loc_end(loc: Dict[str, int], default: int) -> int:
    return int(loc.get("line_end", loc.get("end", default)))


def _chunk_code_text(text: str, start_line: int) -> List[Tuple[int, int, str]]:
    if not text:
        return [(start_line, start_line, text)]
    if len(text) <= HARD_LIMIT:
        line_count = max(len(text.splitlines()), 1)
        return [(start_line, start_line + line_count - 1, text)]

    lines = text.splitlines()
    chunks: List[Tuple[int, int, str]] = []
    cur_lines: List[str] = []
    cur_len = 0
    cur_start = start_line

    for line in lines:
        candidate = line + "\n"
        if cur_lines and cur_len + len(candidate) > SOFT_LIMIT:
            chunk_text = "\n".join(cur_lines).rstrip("\n")
            chunk_end = cur_start + max(len(cur_lines), 1) - 1
            if chunk_text:
                chunks.append((cur_start, chunk_end, chunk_text))
            cur_lines = []
            cur_len = 0
            cur_start = chunk_end + 1
        cur_lines.append(line)
        cur_len += len(candidate)

    if cur_lines:
        chunk_text = "\n".join(cur_lines).rstrip("\n")
        chunk_end = cur_start + max(len(cur_lines), 1) - 1
        chunks.append((cur_start, chunk_end, chunk_text))

    safe_chunks: List[Tuple[int, int, str]] = []
    for start, end, chunk_text in chunks:
        if len(chunk_text) <= HARD_LIMIT:
            safe_chunks.append((start, end, chunk_text))
            continue
        sub_lines = chunk_text.splitlines()
        sub_start = start
        buf: List[str] = []
        buf_len = 0
        for sub in sub_lines:
            candidate = sub + "\n"
            if buf and buf_len + len(candidate) > HARD_LIMIT:
                sub_text = "\n".join(buf).rstrip("\n")
                sub_end = sub_start + max(len(buf), 1) - 1
                safe_chunks.append((sub_start, sub_end, sub_text))
                buf = []
                buf_len = 0
                sub_start = sub_end + 1
            buf.append(sub)
            buf_len += len(candidate)
        if buf:
            sub_text = "\n".join(buf).rstrip("\n")
            sub_end = sub_start + max(len(buf), 1) - 1
            safe_chunks.append((sub_start, sub_end, sub_text))
    return [chunk for chunk in safe_chunks if chunk[2]]


def _compute_package_chunks(record: Dict[str, Any]) -> List[Tuple[int, int, str]]:
    text = record.get("code_text", "") or ""
    metadata = record["metadata"]
    base_start = int(metadata.get("line_range", {}).get("start", 1))
    if len(text) <= HARD_LIMIT:
        lines = text.splitlines()
        end_line = base_start + max(len(lines), 1) - 1
        return [(base_start, end_line, text)]

    equations = record.get("equations", []) or []
    eq_ranges: List[Tuple[int, int]] = []
    for block in equations:
        loc = block.get("location", {})
        start = _loc_start(loc, base_start)
        end = _loc_end(loc, start)
        if end < start:
            end = start
        eq_ranges.append((start, end))
    eq_ranges.sort()

    if not eq_ranges:
        return _chunk_code_text(text, base_start)

    lines = text.splitlines()
    chunks: List[Tuple[int, int, str]] = []
    current_start_idx = 0
    current_len = 0
    last_eq_end = None
    eq_index = 0
    total_lines = len(lines)

    for idx, line in enumerate(lines):
        line_num = base_start + idx
        current_len += len(line) + 1

        while eq_index < len(eq_ranges) and line_num >= eq_ranges[eq_index][1]:
            last_eq_end = eq_ranges[eq_index][1]
            eq_index += 1

        should_cut = False
        cut_line = None
        if current_len >= SOFT_LIMIT and last_eq_end and last_eq_end > base_start + current_start_idx:
            should_cut = True
            cut_line = last_eq_end
        elif current_len >= HARD_LIMIT:
            should_cut = True
            cut_line = line_num

        if should_cut:
            cut_idx = max(cut_line - base_start, current_start_idx)
            chunk_lines = lines[current_start_idx : cut_idx + 1]
            chunk_text = "\n".join(chunk_lines).rstrip("\n")
            if chunk_text:
                chunk_start_line = base_start + current_start_idx
                chunk_end_line = base_start + cut_idx
                chunks.append((chunk_start_line, chunk_end_line, chunk_text))
            current_start_idx = cut_idx + 1
            current_len = 0
            last_eq_end = None

    if current_start_idx < total_lines:
        chunk_lines = lines[current_start_idx:]
        chunk_text = "\n".join(chunk_lines).rstrip("\n")
        if chunk_text:
            chunk_start_line = base_start + current_start_idx
            chunk_end_line = base_start + total_lines - 1
            chunks.append((chunk_start_line, chunk_end_line, chunk_text))

    return [chunk for chunk in chunks if chunk[2]] or _chunk_code_text(text, base_start)


def _filter_equations_for_chunk(
    equations: List[Dict[str, Any]], chunk_start: int, chunk_end: int
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for block in equations or []:
        block_copy = deepcopy(block)
        loc = block_copy.get("location", {})
        block_start = _loc_start(loc, chunk_start)
        block_end = _loc_end(loc, chunk_end)
        if block_start > chunk_end or block_end < chunk_start:
            continue
        items = block_copy.get("items", [])
        if items:
            new_items = []
            for item in items:
                item_copy = deepcopy(item)
                item_loc = item_copy.get("location", {})
                item_start = _loc_start(item_loc, block_start)
                item_end = _loc_end(item_loc, block_end)
                if item_start > chunk_end or item_end < chunk_start:
                    continue
                new_items.append(item_copy)
            if not new_items:
                continue
            block_copy["items"] = new_items
        block_copy["location"] = {
            "line_start": max(block_start, chunk_start),
            "line_end": min(block_end, chunk_end),
        }
        filtered.append(block_copy)
    return filtered


def _exclude_child_equations(
    equations: List[Dict[str, Any]], child_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if not equations or not child_records:
        return equations

    child_ranges: List[Tuple[int, int]] = []
    for child in child_records:
        meta = child.get("metadata", {})
        lr = meta.get("line_range", {}) or {}
        start = int(lr.get("start", -1))
        end = int(lr.get("end", -1))
        if start >= 0 and end >= start:
            child_ranges.append((start, end))
    if not child_ranges:
        return equations

    filtered_blocks: List[Dict[str, Any]] = []
    for block in equations:
        loc = block.get("location", {}) or {}
        block_start = _loc_start(loc, 0)
        block_end = _loc_end(loc, block_start)
        overlap = False
        for start, end in child_ranges:
            if start <= block_end and end >= block_start:
                overlap = True
                break
        if not overlap:
            filtered_blocks.append(block)
    return filtered_blocks


def _get_part_suffix(record_id: str) -> str:
    match = PART_SUFFIX_RE.search(record_id)
    return "" if not match else f"_part{match.group(1)}"


def _split_record_if_needed(
    record: Dict[str, Any],
    repo: RepoContext,
    strategy: str,
) -> List[Dict[str, Any]]:
    return _split_record_custom_chunks(
        record,
        repo,
        strategy,
        None,
    )


def _split_record_custom_chunks(
    record: Dict[str, Any],
    repo: RepoContext,
    strategy: str,
    custom_chunks: List[Tuple[int, int, str]] | None,
) -> List[Dict[str, Any]]:
    text = record.get("code_text", "") or ""
    line_range = record["metadata"]["line_range"]
    base_start = int(line_range.get("start", 1))
    if custom_chunks is not None:
        chunks = custom_chunks
    else:
        chunks = _chunk_code_text(text, base_start)
    total_parts = len(chunks)
    base_equations = deepcopy(record.get("equations", []))
    split_records: List[Dict[str, Any]] = []

    for index, (chunk_start, chunk_end, chunk_text) in enumerate(chunks):
        new_record = deepcopy(record)
        chunk_text = _ensure_min_length(chunk_text)
        checksum = sha1(chunk_text.encode("utf-8")).hexdigest()
        part_suffix = "" if total_parts == 1 else f"_part{index}"
        new_id = (
            f"{record['fqn']}|{record['kind']}|{repo.version}|{checksum}|"
            f"{chunk_start}-{chunk_end}{part_suffix}"
        )

        split_policy = {
            "strategy": strategy if total_parts > 1 else "none",
            "parts": total_parts,
            "index": index,
        }

        new_record["id"] = new_id
        new_record["code_text"] = chunk_text
        new_record["metadata"]["line_range"] = {"start": chunk_start, "end": chunk_end}
        new_record["metadata"]["checksum"] = checksum
        if "original_checksum" not in new_record["metadata"]:
            new_record["metadata"]["original_checksum"] = record["metadata"].get("original_checksum", checksum)
        new_record["metadata"]["split_policy"] = split_policy
        new_record["provenance"]["line_range"] = {"start": chunk_start, "end": chunk_end}
        new_record["provenance"]["hash"] = checksum
        new_record["meta"] = new_record.get("meta", {})
        new_record["meta"]["split_part"] = index
        new_record["meta"]["split_policy"] = split_policy
        new_record["equations"] = _filter_equations_for_chunk(
            base_equations, chunk_start, chunk_end
        )
        stats_dict = compute_statistics(new_record)
        stats_dict["split_parts"] = total_parts
        stats_dict["split_index"] = index
        original_stats = record.get("statistics", {})
        for key in ("contained_functions", "child_classes", "child_class_count", "child_classes_removed"):
            if key in original_stats:
                stats_dict[key] = original_stats[key]
        new_record["statistics"] = stats_dict
        split_records.append(new_record)

    return split_records


def _extract_equation_records(record: Dict[str, Any], repo: RepoContext) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    part_suffix = _get_part_suffix(record["id"])
    metadata = record["metadata"]
    provenance = record["provenance"]
    equations = record.get("equations", [])
    seen_keys: Dict[Tuple[str, str, int, int, str], int] = defaultdict(int)
    for block in equations:
        section_type = block.get("section_type", "equation")
        block_loc = block.get("location", {})
        block_start = _loc_start(block_loc, metadata["line_range"]["start"])
        block_end = _loc_end(block_loc, metadata["line_range"]["end"])
        for item in block.get("items", []):
            eq_text = item.get("str", "")
            if not eq_text:
                continue
            eq_loc = item.get("location", {})
            line_start = _loc_start(eq_loc, block_start)
            line_end = _loc_end(eq_loc, block_end)
            checksum = sha1(eq_text.encode("utf-8")).hexdigest()
            key = (record["fqn"], checksum, line_start, line_end, part_suffix)
            seq = seen_keys[key]
            seen_keys[key] += 1
            seq_suffix = "" if seq == 0 else f"#{seq}"
            eq_id = (
                f"{record['fqn']}|equation|{repo.version}|{checksum}|"
                f"{line_start}-{line_end}{part_suffix}{seq_suffix}"
            )
            results.append(
                {
                    "id": eq_id,
                    "fqn": record["fqn"],
                    "kind": "equation",
                    "owner_fqn": record["fqn"],
                    "equation": eq_text,
                    "vars": _filter_vars(item.get("vars", [])),
                    "section_type": section_type,
                    "ops": item.get("ops", []),
                    "location": {"line_start": line_start, "line_end": line_end},
                    "metadata": {
                        "file_path": metadata["file_path"],
                        "line_range": {"start": line_start, "end": line_end},
                        "timestamp": metadata["timestamp"],
                        "checksum": checksum,
                        "version": repo.version,
                    },
                    "provenance": {
                        "repo": provenance["repo"],
                        "commit": provenance["commit"],
                        "file_path": provenance["file_path"],
                        "line_range": {"start": line_start, "end": line_end},
                        "version": provenance["version"],
                        "hash": checksum,
                    },
                    "neighbors": {"uses": [], "used_by": []},
                }
            )
    return results


def _remove_child_class_definitions(code_text: str, child_records: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    if not child_records or not code_text:
        return code_text, []

    removed: List[str] = []
    # 長い順に置換すると安定して除去できる
    for child in sorted(child_records, key=lambda c: len(c.get("code_text", "") or ""), reverse=True):
        child_text = (child.get("code_text") or "").strip()
        if not child_text:
            continue
        pattern = child_text
        if pattern in code_text:
            marker = f"// child class extracted: {child.get('fqn', '')}\n"
            code_text = code_text.replace(pattern, marker, 1)
            removed.append(child.get("fqn", ""))
    return code_text, removed


def _process_package(
    symbol: Dict[str, Any],
    base_record: Dict[str, Any],
    repo: RepoContext,
    child_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    record = deepcopy(base_record)
    original_code = symbol.get("code_text") or record.get("code_text", "")
    cleaned = _strip_function_blocks(original_code)
    child_fqns = [child.get("fqn", "") for child in child_records if child.get("fqn")]
    cleaned, removed_children = _remove_child_class_definitions(cleaned, child_records)
    record["code_text"] = _ensure_min_length(cleaned)
    record["equations"] = _exclude_child_equations(record.get("equations", []), child_records)
    record["statistics"] = compute_statistics(record)
    record["statistics"]["contained_functions"] = 0
    record["statistics"]["child_classes"] = child_fqns
    record["statistics"]["child_class_count"] = len(child_fqns)
    record["statistics"]["child_classes_removed"] = removed_children
    custom_chunks = _compute_package_chunks(record)
    return _split_record_custom_chunks(record, repo, "equation_grouping", custom_chunks)


def _process_function(symbol: Dict[str, Any], base_record: Dict[str, Any], repo: RepoContext) -> List[Dict[str, Any]]:
    record = deepcopy(base_record)
    original_code = symbol.get("code_text") or record.get("code_text", "")
    record["code_text"] = _ensure_min_length(original_code)

    record["components"] = [
        comp
        for comp in record.get("components", [])
        if any(prefix in ("input", "output") for prefix in comp.get("prefixes", []))
    ]

    extends_entries = record.setdefault("inheritance", {}).setdefault("extends", [])
    if not any(entry.get("base_class") == "Modelica.Icons.Function" for entry in extends_entries):
        extends_entries.append({"base_class": "Modelica.Icons.Function", "modifications": {}})

    algorithm_items: List[Dict[str, Any]] = []
    metadata = record["metadata"]

    for block in symbol.get("equations", []):
        equations = block.get("equations", [])
        span = block.get("span") or {}
        line_cursor = span.get("start_line", metadata["line_range"]["start"])
        for eq in equations:
            eq_text = (eq or "").rstrip()
            if not eq_text:
                continue
            items = build_equation_items([eq_text])
            if not items:
                continue
            item = items[0]
            line_start = line_cursor
            line_end = line_start + eq_text.count("\n")
            line_cursor = line_end + 1
            item["section_type"] = "algorithm"
            item["location"] = {"line_start": line_start, "line_end": line_end}
            item["vars"] = _filter_vars(item.get("vars", []))
            algorithm_items.append(item)

    record["equations"] = [
        {
            "section_type": "algorithm",
            "items": algorithm_items,
            "location": metadata["line_range"],
        }
    ]
    record["statistics"] = compute_statistics(record)
    return _split_record_if_needed(record, repo, "function_split")


def build_split_outputs(
    symbols: List[Dict[str, Any]],
    repo: RepoContext,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    package_records: List[Dict[str, Any]] = []
    function_records: List[Dict[str, Any]] = []
    function_counts: defaultdict[Tuple[str, ...], int] = defaultdict(int)

    base_records = [symbol_to_ast_record(symbol, repo) for symbol in symbols]
    base_by_fqn = {base["fqn"]: base for base in base_records}
    child_map: defaultdict[str, List[str]] = defaultdict(list)
    for base in base_records:
        pkg_path = base.get("package_path", [])
        if pkg_path:
            parent_fqn = ".".join(pkg_path)
            child_map[parent_fqn].append(base["fqn"])

    for symbol, base in zip(symbols, base_records):
        kind = base.get("kind", "unknown")
        if kind == "function":
            chunks = _process_function(symbol, base, repo)
            function_records.extend(chunks)
            pkg_path = tuple(base.get("package_path", []))
            function_counts[pkg_path] += 1
        else:
            child_fqns = child_map.get(base["fqn"], [])
            child_records = [deepcopy(base_by_fqn[f]) for f in child_fqns if f in base_by_fqn]
            chunks = _process_package(symbol, base, repo, child_records)
            package_records.extend(chunks)

    for pkg_record in package_records:
        pkg_path = tuple(pkg_record.get("package_path", []))
        pkg_record.setdefault("statistics", {})
        pkg_record["statistics"]["contained_functions"] = function_counts.get(pkg_path, 0)

    equation_records: List[Dict[str, Any]] = []
    for record in package_records + function_records:
        equation_records.extend(_extract_equation_records(record, repo))

    stats = {
        "packages": len(package_records),
        "functions": len(function_records),
        "equations": len(equation_records),
    }
    return package_records, function_records, equation_records, stats


def write_split_outputs(
    symbols: List[Dict[str, Any]],
    repo: RepoContext,
    output_dir: Path,
) -> Dict[str, Any]:
    packages, functions, equations, stats = build_split_outputs(symbols, repo)
    output_dir.mkdir(parents=True, exist_ok=True)

    def _write_jsonl(path: Path, records: List[Dict[str, Any]]):
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
                fh.write("\n")

    _write_jsonl(output_dir / "ast_packages.jsonl", packages)
    _write_jsonl(output_dir / "ast_functions.jsonl", functions)
    _write_jsonl(output_dir / "ast_equations.jsonl", equations)

    id_counts = {
        "packages": len({rec["id"] for rec in packages}),
        "functions": len({rec["id"] for rec in functions}),
        "equations": len({rec["id"] for rec in equations}),
    }
    stats.update(
        {
            "unique_ids": id_counts,
            "duplicate_ids": {
                "packages": stats["packages"] - id_counts["packages"],
                "functions": stats["functions"] - id_counts["functions"],
                "equations": stats["equations"] - id_counts["equations"],
            },
            "split_summary": {
                "packages": sum(1 for rec in packages if rec["meta"]["split_policy"]["strategy"] != "none"),
                "functions": sum(1 for rec in functions if rec["meta"]["split_policy"]["strategy"] != "none"),
            },
        }
    )

    with (output_dir / "stats.json").open("w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    if any(v != 0 for v in stats["duplicate_ids"].values()):
        raise RuntimeError(f"Duplicate IDs detected: {stats['duplicate_ids']}")

    return stats

