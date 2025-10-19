"""設定ファイル"""
import os

# ～ここに接続情報を定義～
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "your_collection"

# ～ここに自動検索トリガーのキーワードリストを定義～
AUTO_SEARCH_KEYWORDS = [
    "keyword1",
    "keyword2",
    # ...
]