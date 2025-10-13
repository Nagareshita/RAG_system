
# tools/build_modelica_parser.py
from __future__ import annotations
import argparse, platform, subprocess, sys, shutil
from pathlib import Path
# --------- 位置決め（どこで実行してもOK） ---------
THIS_FILE = Path(__file__).resolve()
SCRIPT_DIR = THIS_FILE.parent
DEFAULT_REPO = SCRIPT_DIR / "tree-sitter-modelica"
DEFAULT_OUT  = SCRIPT_DIR / "build"
LIB_NAME = "modelica" + (".dll" if platform.system()=="Windows" else ".so")
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)
def ensure_generated(repo: Path):
    """src/parser.c が無ければ generate"""
    parser_c = repo / "src" / "parser.c"
    if parser_c.exists():
        return
    # 1) グローバル CLI, 2) npx の順でトライ
    try:
        run(["tree-sitter", "--version"])
        run(["tree-sitter", "generate"], cwd=repo)
    except Exception:
        run(["npx", "tree-sitter", "generate"], cwd=repo)
def build_shared(repo: Path, out_dir: Path) -> Path:
    """py-tree-sitter 用の共有ライブラリを作成"""
    from tree_sitter import Language  # pip install tree-sitter
    out_dir.mkdir(parents=True, exist_ok=True)
    out_lib = out_dir / LIB_NAME
    Language.build_library(str(out_lib), [str(repo)])
    return out_lib
def smoke_test(lib_path: Path):
    """最小パースの動作確認"""
    from tree_sitter import Language, Parser
    lang = Language(str(lib_path), "modelica")
    p = Parser(); p.set_language(lang)
    code = b"""
    model TestModel
      Real x(start=1.0);
    equation
      der(x) = -x;
    end TestModel;
    """
    tree = p.parse(code)
    print(f"✅ smoke test: root={tree.root_node.type}, children={len(tree.root_node.children)}")
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO,
                    help="path to tree-sitter-modelica (default: RagModelica/tree-sitter-modelica)")
    ap.add_argument("--out",  type=Path, default=DEFAULT_OUT,
                    help="output dir for built library (default: RagModelica/build)")
    ap.add_argument("--slot", type=str, default="",
                    help="optional subfolder under build (e.g., --slot parsers -> build/parsers)")
    args = ap.parse_args()
    repo = args.repo.resolve()
    out  = (args.out / args.slot).resolve() if args.slot else args.out.resolve()
    if not repo.exists():
        print(f"❌ repo not found: {repo}")
        sys.exit(1)
    print(f" REPO         : {repo}")
    print(f"📤 OUT DIR      : {out}")
    ensure_generated(repo)
    lib = build_shared(repo, out)
    print(f"✅ built: {lib}")
    smoke_test(lib)
if __name__ == "__main__":
    main()
