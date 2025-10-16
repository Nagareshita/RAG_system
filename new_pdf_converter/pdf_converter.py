# apps_pymupdf_converter.py (プロジェクトルート)
"""
PyMuPDF4LLM PDF to JSON Converter
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def main():
    """メイン関数"""
    try:
        from pymupdf_converter.main_app import main as app_main
        return app_main()
    except ImportError as e:
        print(f"❌ モジュールのインポートに失敗しました: {e}")
        print("依存関係を確認してください:")
        print("pip install pymupdf4llm PySide6")
        return 1
    except Exception as e:
        print(f"❌ アプリケーションエラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
