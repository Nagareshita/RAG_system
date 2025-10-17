# 重複防止機能とオプションA実装

## 概要
Qdrantベクトルデータベースに対して、**ファイル単位の重複防止機能**と**3つのASTコレクション分離（オプションA）**を実装しました。

実装日: 2025年10月17日

## 実装内容

### 1. 重複防止機能（utils/vector_manager.py）

#### 1.1 check_file_exists() メソッド
```python
def check_file_exists(self, collection_name: str, file_hash: str) -> bool
```

**機能:**
- 指定されたfile_hashが既にコレクションに存在するかチェック
- Qdrantの`scroll`とPayloadフィルタを使用して高速検索

**実装詳細:**
```python
result = client.scroll(
    collection_name=collection_name,
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="file_hash",
                match=MatchValue(value=file_hash)
            )
        ]
    ),
    limit=1
)
return len(result[0]) > 0
```

**特徴:**
- コレクションが存在しない場合はFalseを返す（新規追加を許可）
- エラー時は安全側に倒してFalse（追加を許可）
- limit=1で最小限のデータ取得（高速化）

#### 1.2 add_documents_with_dedup() メソッド
```python
def add_documents_with_dedup(self, collection_name: str, source_file: str, 
                            documents: List[Dict[str, Any]]) -> Dict[str, Any]
```

**機能:**
- ファイルハッシュを計算して重複チェック
- 既存ファイルはスキップ、新規ファイルのみ追加

**戻り値の構造:**
```python
# 成功時
{
    "status": "added",
    "count": 1234,  # 追加されたドキュメント数
    "file_hash": "abc123...",
    "file_path": "/path/to/file.jsonl"
}

# スキップ時
{
    "status": "skipped",
    "reason": "already_exists",
    "file_hash": "abc123...",
    "file_path": "/path/to/file.jsonl"
}

# エラー時
{
    "status": "error",
    "error": "エラーメッセージ",
    "file_path": "/path/to/file.jsonl"
}
```

#### 1.3 _process_single_collection() の改修

**主な変更点:**
```python
# ファイル処理前に重複チェックを追加
if self.check_file_exists(collection_name, file_hash):
    skipped_files += 1
    if log_callback:
        log_callback(f"スキップ: {os.path.basename(file_path)} (既に処理済み)")
    continue
```

**追加された統計情報:**
- `added_files`: 新規追加されたファイル数
- `skipped_files`: スキップされたファイル数
- 処理完了時にログ出力

### 2. オプションA: 3つのASTコレクション分離

#### 2.1 _identify_ast_file_type() メソッド
```python
def _identify_ast_file_type(self, file_path: str) -> str
```

**機能:**
- ファイル名からASTのタイプを判定
- "packages" | "functions" | "equations" | "unknown" を返す

**判定ロジック:**
| ファイル名 | 判定結果 |
|-----------|---------|
| ast_packages.jsonl | packages |
| ast_functions.jsonl | functions |
| ast_equations.jsonl | equations |
| packages.jsonl | packages |
| functions.jsonl | functions |
| equations.jsonl | equations |
| その他 | unknown |

#### 2.2 _process_separated_collections() の改修

**以前の構造:**
```
rag_documents_ast (混合)
rag_documents_pdf
```

**新しい構造（オプションA）:**
```
rag_documents_ast_packages   ← パッケージ定義専用
rag_documents_ast_functions  ← 関数定義専用
rag_documents_ast_equations  ← 方程式専用
rag_documents_pdf            ← PDF文書専用
```

**処理フロー:**
1. 全ファイルをタイプ別に分類
   - `.jsonl` → ASTファイルとして_identify_ast_file_type()で判定
   - `.json` → PDFファイル
2. 各タイプごとに専用コレクションを作成
3. タイプ不明なJSONLは警告してスキップ

**コード構造:**
```python
# ファイル分類
for f in file_structures:
    if file_path.endswith('.jsonl'):
        ast_type = self._identify_ast_file_type(file_path)
        if ast_type == "packages":
            ast_packages_files.append(f)
        elif ast_type == "functions":
            ast_functions_files.append(f)
        elif ast_type == "equations":
            ast_equations_files.append(f)
    elif file_path.endswith('.json'):
        pdf_files.append(f)

# 各コレクションを処理
if ast_packages_files:
    self.create_collection("rag_documents_ast_packages")
    self._process_single_collection("rag_documents_ast_packages", ...)

if ast_functions_files:
    self.create_collection("rag_documents_ast_functions")
    self._process_single_collection("rag_documents_ast_functions", ...)

if ast_equations_files:
    self.create_collection("rag_documents_ast_equations")
    self._process_single_collection("rag_documents_ast_equations", ...)
```

## ユーザーインターフェース

### ベクトル化タブの動作

**保存方式: "分離"を選択した場合:**
1. ASTファイルをタイプ別に自動判定
2. 各タイプごとに専用コレクションに保存
3. 重複チェックにより既存ファイルは自動スキップ

**ログ出力例:**
```
構造解析中: ast_packages.jsonl (5000エントリー)
構造解析中: ast_functions.jsonl (8000エントリー)
構造解析中: ast_equations.jsonl (12000エントリー)
3ファイルの構造解析完了
ベクトル化処理開始...

AST Packages専用コレクションを処理中... (1ファイル)
処理中: ast_packages.jsonl (5000エントリー)
ベクトル化中: 128件 (1-128)
...
ast_packages.jsonl 完了: 5000ベクトル
ベクトル化完了: 総計 5000 ベクトル
結果: 追加 1ファイル, スキップ 0ファイル

AST Functions専用コレクションを処理中... (1ファイル)
スキップ: ast_functions.jsonl (既に処理済み)  ← 重複検出
結果: 追加 0ファイル, スキップ 1ファイル

...
```

## 技術詳細

### ファイルハッシュの計算
- SHA-256アルゴリズム使用
- ファイル内容全体をハッシュ化
- 1バイトでも変更があれば異なるハッシュ値

### Qdrant Payloadフィルタ
```python
Filter(
    must=[
        FieldCondition(
            key="file_hash",
            match=MatchValue(value="abc123...")
        )
    ]
)
```

**利点:**
- インデックスを利用した高速検索
- 大量のベクトルがあっても効率的
- ファイル単位で一括チェック

### インポートの追加
```python
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue  # 追加
)
```

## メリット

### 1. 重複防止機能
- ✅ 同じファイルを複数回ベクトル化することを防止
- ✅ ストレージ容量の節約
- ✅ 検索結果の重複を回避
- ✅ 処理時間の短縮（既存ファイルはスキップ）

### 2. オプションA（3つのコレクション分離）
- ✅ 検索精度の向上（パッケージ定義だけ検索、など）
- ✅ コレクション単位での管理が容易
- ✅ 用途別の検索パラメータ調整が可能
- ✅ データタイプ別の統計取得が簡単

### 3. 段階的な移行
- ✅ 既存の"混合"モードも引き続き使用可能
- ✅ ユーザーがUI で選択可能
- ✅ 既存データに影響なし

## 動作確認項目

### テストシナリオ1: 重複防止
1. ast_packages.jsonl を選択してベクトル化
2. 同じファイルを再度選択してベクトル化
3. ログに「スキップ: ast_packages.jsonl (既に処理済み)」が表示されること
4. コレクション内のベクトル数が変わらないこと

### テストシナリオ2: 3つのコレクション分離
1. 保存方式: "分離"を選択
2. ast_packages.jsonl, ast_functions.jsonl, ast_equations.jsonl を選択
3. ベクトル化実行
4. Qdrantに以下のコレクションが作成されること:
   - rag_documents_ast_packages
   - rag_documents_ast_functions
   - rag_documents_ast_equations

### テストシナリオ3: ファイル更新検知
1. ast_packages.jsonl を編集（1行追加）
2. 再度ベクトル化
3. file_hashが変わるため新規追加されること

## 今後の拡張

### 検索機能への統合
現在の実装ではベクトル化のみ対応。検索機能も3つのコレクションに対応する必要があります:

```python
# 検索時にコレクションを指定
results_packages = vector_manager.search(
    query="ModelicaのPackage構造",
    collection_name="rag_documents_ast_packages"
)

results_functions = vector_manager.search(
    query="流体計算の関数",
    collection_name="rag_documents_ast_functions"
)
```

### UI改善案
- コレクション選択ドロップダウンに3つのASTコレクションを追加
- 複数コレクションの同時検索オプション
- コレクション別の統計表示

## ファイル一覧

### 変更されたファイル
- `utils/vector_manager.py`: 全ての主要機能を実装
  - check_file_exists() 追加
  - add_documents_with_dedup() 追加
  - _identify_ast_file_type() 追加
  - _process_single_collection() 改修
  - _process_separated_collections() 改修
  - インポート追加（Filter, FieldCondition, MatchValue）

### 影響を受けないファイル
- `tabs/vectorization_tab.py`: UI側は変更不要
  - 既存のインターフェースで新機能が動作

## まとめ

- ✅ 重複防止機能により、同じファイルの二重登録を防止
- ✅ オプションA実装により、ASTデータを3つのコレクションに分離
- ✅ 既存の"混合"モードも維持し、後方互換性を確保
- ✅ ログ出力により、スキップ/追加の状況を可視化
- ✅ 次のステップ: 検索機能への統合、UI改善
