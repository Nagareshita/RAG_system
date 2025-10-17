# ast_only/src/modelica/utils_text.py
"""
テキスト処理ユーティリティ
"""
from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import json
import hashlib

def file_bytes(file_path: str | Path) -> bytes:
    """ファイルをbytesとして読み込む"""
    return Path(file_path).read_bytes()

def sha1_text(text: str) -> str:
    """テキストのSHA1ハッシュを計算"""
    return hashlib.sha1(text.encode('utf-8')).hexdigest()

def to_jsonl(rows: List[Dict[str, Any]]) -> str:
    """辞書のリストをJSONL形式に変換"""
    lines = []
    for row in rows:
        lines.append(json.dumps(row, ensure_ascii=False, separators=(',', ':')))
    return '\n'.join(lines)
