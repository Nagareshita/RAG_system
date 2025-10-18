from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional, Any
import os
import platform
import warnings


_LANG: Optional[Any] = None
_WORKER_PARSER: Optional[Any] = None


def _lib_names() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return ["modelica.dll"]
    if system == "Darwin":
        return ["modelica.dylib", "modelica.so"]
    return ["modelica.so", "libmodelica.so"]


def _env_candidates() -> Iterable[Path]:
    for key in ("TS_MODELICA_LIB", "TREE_SITTER_MODELICA_LIB"):
        val = os.getenv(key)
        if val:
            path = Path(val)
            if path.exists():
                print(f"✓ 環境変数 {key} からライブラリ候補: {path}")
                yield path


def _local_candidates() -> Iterable[Path]:
    here = Path(__file__).resolve().parent
    root = here.parent
    names = _lib_names()
    search_roots = [
        here,
        here / "build",
        root / "build",
        root / "third_party" / "tree-sitter-modelica" / "build",
        root / "vendor" / "tree-sitter-modelica" / "build",
        Path("C:/tree-sitter/modelica"),
        Path("C:/parsers"),
    ]

    for base in search_roots:
        for name in names:
            candidate = base / name
            if candidate.exists():
                print(f"tree-sitter ライブラリ発見: {candidate}")
                yield candidate


def load_modelica_language():
    global _LANG
    if _LANG is not None:
        return _LANG

    try:
        from tree_sitter import Language  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("tree-sitter パッケージが必要です。pip install tree-sitter") from exc

    tried: list[str] = []
    for candidate in list(_env_candidates()) + list(_local_candidates()):
        tried.append(str(candidate))
        try:
            _LANG = Language(str(candidate), "modelica")
            return _LANG
        except Exception as exc:  # pragma: no cover
            print(f"tree-sitter 読み込み失敗: {candidate} -> {exc}")
            continue

    raise RuntimeError(
        "tree-sitter Modelica ライブラリが見つかりません。"
        + "\n探索したパス:\n- "
        + "\n- ".join(tried)
    )


def new_parser():
    try:
        from tree_sitter import Parser  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("tree-sitter パッケージが必要です。pip install tree-sitter") from exc

    try:
        lang = load_modelica_language()
        parser = Parser()
        parser.set_language(lang)
        return parser
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"tree-sitter パーサーの作成に失敗: {exc}") from exc


class DummyParser:
    def parse(self, source_bytes: bytes):
        return DummyTree(source_bytes)


class DummyTree:
    def __init__(self, source_bytes: bytes):
        self.source_bytes = source_bytes
        self.root_node = DummyNode(source_bytes)


class DummyNode:
    def __init__(self, source_bytes: bytes):
        self.source_bytes = source_bytes
        self.type = "source_file"
        self.start_byte = 0
        self.end_byte = len(source_bytes)
        self.start_point = (0, 0)
        self.end_point = (source_bytes.count(b"\n"), 0)
        self.child_count = 0
        self.is_named = True
        self.parent = None
        self.id = 0

    def child(self, _index: int):  # pragma: no cover - ダミー
        return None


def init_worker_parser() -> None:
    global _WORKER_PARSER
    _WORKER_PARSER = new_parser()


def get_worker_parser():
    global _WORKER_PARSER
    return _WORKER_PARSER or new_parser()

