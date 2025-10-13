# ast_only/src/modelica/parser_loader.py
"""
tree-sitter パーサーの読み込みを担当。
実用版 - 実際のtree-sitter Modelicaライブラリを探索・読み込み。
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Iterable, Any
import os, platform
import warnings

_LANG: Optional[Any] = None
_WORKER_PARSER: Optional[Any] = None  # optional: ProcessPool initializer用

def _lib_names():
    """プラットフォーム別のライブラリファイル名候補"""
    system = platform.system()
    if system == "Windows":
        return ["modelica.dll"]
    elif system == "Darwin":
        return ["modelica.dylib", "modelica.so"]
    else:
        return ["modelica.so", "libmodelica.so"]

def _env_candidates() -> Iterable[Path]:
    """環境変数からライブラリパスを取得"""
    for key in ("TS_MODELICA_LIB", "TREE_SITTER_MODELICA_LIB"):
        val = os.getenv(key)
        if val:
            p = Path(val)
            if p.exists():
                print(f"✓ 環境変数 {key} からライブラリ候補: {p}")
                yield p

def _local_candidates() -> Iterable[Path]:
    """ローカル候補パスからライブラリを探索"""
    here = Path(__file__).resolve().parent
    root = here.parents[1] if len(here.parents) >= 2 else here
    modelica_modules = here.parent  # tabs/modelica_modules
    names = _lib_names()
    
    bases = [
        here,
        here / "build",
        modelica_modules / "build",  # tabs/modelica_modules/build (追加)
        root / "build", 
        root / "third_party" / "tree-sitter-modelica" / "build",
        root / "vendor" / "tree-sitter-modelica" / "build",
        root / "parsers",
        # Windows固有の追加パス
        Path("C:/tree-sitter/modelica"),
        Path("C:/parsers"),
    ]
    
    print(f"tree-sitterライブラリ探索中...")
    print(f"候補ファイル名: {names}")
    
    for base in bases:
        print(f"探索パス: {base}")
        for n in names:
            p = base / n
            if p.exists():
                print(f"ライブラリ発見: {p}")
                yield p
            else:
                print(f"見つからず: {p}")

def load_modelica_language():
    """tree-sitter Modelica言語を読み込み"""
    global _LANG
    if _LANG is not None:
        return _LANG

    # まずtree-sitterのimportを試行
    try:
        from tree_sitter import Language
        print("tree-sitter パッケージの読み込み成功")
    except ImportError as e:
        print(f"tree-sitter パッケージが見つかりません: {e}")
        print("pip install tree-sitter でインストールしてください")
        raise RuntimeError(f"tree-sitter パッケージが必要です: {e}")

    tried = []
    
    # 環境変数と候補パスから探索
    for p in list(_env_candidates()) + list(_local_candidates()):
        tried.append(str(p))
        try:
            print(f"ライブラリ読み込み試行: {p}")
            _LANG = Language(str(p), "modelica")
            print(f"tree-sitter Modelica言語の読み込み成功: {p}")
            return _LANG
        except Exception as e:
            print(f"読み込み失敗: {p} - {e}")
            continue

    # すべて失敗した場合のエラーメッセージ
    hint = (
        "tree-sitter Modelicaライブラリが見つかりません。\n\n"
        "解決方法:\n"
        "1. 環境変数 TS_MODELICA_LIB にライブラリのパスを設定\n"
        "2. build/modelica.dll を適切な場所に配置\n"
        "3. tree-sitter-modelica をビルドしてライブラリを生成"
    )
    
    error_msg = (
        f"tree-sitter Modelica言語を読み込めませんでした。\n\n"
        f"探索したパス:\n- " + "\n- ".join(tried) + f"\n\n{hint}"
    )
    
    print(f"{error_msg}")
    raise RuntimeError(error_msg)

def new_parser():
    """新しいパーサーインスタンスを作成"""
    try:
        from tree_sitter import Parser

        lang = load_modelica_language()
        parser = Parser()
        parser.set_language(lang)
        print("tree-sitter パーサーの作成成功")
        return parser

    except Exception as e:
        print(f"tree-sitter パーサーの作成に失敗: {e}")
        print("ダミーパーサーにフォールバック")
        warnings.warn(f"tree-sitter パーサー作成失敗: {e}。ダミーパーサーを使用します。")
        return DummyParser()

# --- Fallback: ダミーパーサー実装 ---

class DummyParser:
    """tree-sitterが利用できない場合のダミーパーサー"""
    
    def parse(self, source_bytes: bytes):
        """ダミーの解析処理"""
        return DummyTree(source_bytes)

class DummyTree:
    """ダミーの構文木"""
    
    def __init__(self, source_bytes: bytes):
        self.source_bytes = source_bytes
        self.root_node = DummyNode(source_bytes)

class DummyNode:
    """ダミーのノード"""
    
    def __init__(self, source_bytes: bytes):
        self.source_bytes = source_bytes
        self.type = "source_file"
        self.start_byte = 0
        self.end_byte = len(source_bytes)
        self.start_point = (0, 0)
        self.end_point = (source_bytes.count(b'\n'), 0)
        self.child_count = 0
        self.is_named = True
        self.parent = None
        self.id = 0
    
    def child(self, index: int):
        return None

# --- Optional: for ProcessPoolExecutor(initializer=...) ---

def init_worker_parser() -> None:
    """ワーカープロセス用パーサー初期化"""
    global _WORKER_PARSER
    _WORKER_PARSER = new_parser()

def get_worker_parser():
    """ワーカープロセス用パーサー取得"""
    global _WORKER_PARSER
    return _WORKER_PARSER or new_parser()