# 旧ASTコレクションからの移行ガイド

## 概要
以前のシステムでは、ASTデータが単一の`rag_documents_ast`コレクションに保存されていました。  
新しいシステムでは、3つの専用コレクションに分離されています：
- `rag_documents_ast_packages`（パッケージ定義）
- `rag_documents_ast_functions`（関数定義）
- `rag_documents_ast_equations`（方程式）

## 実施日
2025年10月17日

## 変更内容

### 1. コードの修正

#### a) agent_designer/ui/agent_settings/retriever/config.py
**変更前:**
```python
'options': [
    ('rag_documents_pdf', 'rag_documents_pdf（PDF検索）'),
    ('rag_documents_ast', 'rag_documents_ast（AST検索）')  # 旧コレクション
]
```

**変更後:**
```python
'options': [
    ('rag_documents_pdf', 'rag_documents_pdf（PDF検索）'),
    ('rag_documents_ast_packages', 'rag_documents_ast_packages（ASTパッケージ）'),
    ('rag_documents_ast_functions', 'rag_documents_ast_functions（AST関数）'),
    ('rag_documents_ast_equations', 'rag_documents_ast_equations（AST方程式）')
]
```

#### b) agent_designer/ui/node_settings.py
**変更前:**
```python
if collection_text and "rag_documents_pdf" in collection_text:
    target_collection = 'rag_documents_pdf'
else:
    target_collection = 'rag_documents_ast'  # デフォルトで旧コレクション
```

**変更後:**
```python
if "rag_documents_pdf" in collection_text:
    target_collection = 'rag_documents_pdf'
elif "rag_documents_ast_packages" in collection_text:
    target_collection = 'rag_documents_ast_packages'
elif "rag_documents_ast_functions" in collection_text:
    target_collection = 'rag_documents_ast_functions'
elif "rag_documents_ast_equations" in collection_text:
    target_collection = 'rag_documents_ast_equations'
else:
    target_collection = 'rag_documents_pdf'  # デフォルト
```

### 2. 旧コレクションの削除手順

#### ステップ1: 現在のコレクション確認
```powershell
# vector_dbフォルダの内容を確認
ls vector_db
```

予想される出力：
```
rag_documents_ast/           # 旧コレクション（削除対象）
rag_documents_ast_packages/  # 新コレクション
rag_documents_ast_functions/ # 新コレクション
rag_documents_ast_equations/ # 新コレクション
rag_documents_pdf/           # PDFコレクション
meta.json
```

#### ステップ2: 旧コレクションの削除
```powershell
# 旧ASTコレクションフォルダを削除
Remove-Item -Recurse -Force vector_db\rag_documents_ast
```

**注意:** この操作は元に戻せません。必要に応じてバックアップを取ってください。

#### ステップ3: 確認
```powershell
# 削除されたことを確認
ls vector_db
```

`rag_documents_ast`フォルダが存在しないことを確認します。

### 3. 新しいデータの再ベクトル化

旧コレクションを削除した後、新しい3つのコレクションにデータを追加します：

1. **main.pyを起動**
2. **ベクトル化タブを開く**
3. **保存方式: "分離"を選択**
4. **AST JSONLフォルダを選択**
   - `data/ast`フォルダを選択
   - 以下のファイルが自動検出されます：
     - `ast_packages.jsonl`
     - `ast_functions.jsonl`
     - `ast_equations.jsonl`
5. **ベクトル化実行**

ログ出力例：
```
AST Packages専用コレクションを処理中... (1ファイル)
処理中: ast_packages.jsonl (5000エントリー)
...
結果: 追加 1ファイル, スキップ 0ファイル

AST Functions専用コレクションを処理中... (1ファイル)
処理中: ast_functions.jsonl (8000エントリー)
...
結果: 追加 1ファイル, スキップ 0ファイル

AST Equations専用コレクションを処理中... (1ファイル)
処理中: ast_equations.jsonl (12000エントリー)
...
結果: 追加 1ファイル, スキップ 0ファイル
```

### 4. エージェントデザイナーでの使用

#### 以前の方法:
Retrieverノードの設定で「rag_documents_ast」を選択

#### 新しい方法:
目的に応じて適切なコレクションを選択：
- **パッケージ構造を調べる場合**: `rag_documents_ast_packages`
- **関数定義を探す場合**: `rag_documents_ast_functions`
- **方程式実装を調べる場合**: `rag_documents_ast_equations`

#### メリット:
- 検索精度が向上（関係ないデータが混ざらない）
- 検索速度が向上（コレクションサイズが小さい）
- 目的に応じた最適な検索が可能

### 5. 設定ファイルの更新

既存のAgent Designer設定ファイル（`configs/designs/*.json`）で`rag_documents_ast`を参照している場合、手動で更新が必要です：

**更新例:**
```json
// 旧設定
{
  "target_collections": {
    "value": "rag_documents_ast"
  }
}

// 新設定（目的に応じて選択）
{
  "target_collections": {
    "value": "rag_documents_ast_packages"
  }
}
```

## トラブルシューティング

### Q1: 旧コレクションを削除したらエラーが出る
**A:** エージェントデザイナーの設定で、まだ`rag_documents_ast`を参照している可能性があります。
- 各Retrieverノードの設定を開き、新しいコレクションを選択し直してください。

### Q2: 検索結果が以前と異なる
**A:** これは正常です。以前は3種類のデータが混在していましたが、今は分離されています。
- 目的に応じて適切なコレクションを選択してください。
- 複数のコレクションを同時に検索したい場合は、複数のRetrieverノードを使用してください。

### Q3: データが見つからない
**A:** ベクトル化が正しく完了しているか確認してください。
```powershell
# 各コレクションのstorage.sqliteが存在するか確認
ls vector_db\rag_documents_ast_packages\storage.sqlite
ls vector_db\rag_documents_ast_functions\storage.sqlite
ls vector_db\rag_documents_ast_equations\storage.sqlite
```

### Q4: 旧コレクションのデータを保持したい
**A:** 削除前にバックアップを取ってください：
```powershell
# バックアップフォルダを作成
New-Item -ItemType Directory -Force -Path vector_db_backup
# 旧コレクションをバックアップ
Copy-Item -Recurse vector_db\rag_documents_ast vector_db_backup\
```

## まとめ

- ✅ 旧コレクション`rag_documents_ast`への参照をすべて削除
- ✅ 新しい3つのコレクションに対応
- ✅ Agent Designer UIで新しいコレクションを選択可能
- ✅ 旧コレクションフォルダは手動で削除可能
- ✅ 新しいシステムでの再ベクトル化が可能

## 次のステップ

1. 旧`rag_documents_ast`フォルダを削除
2. 新しい3つのコレクションでデータを再ベクトル化
3. Agent Designerの既存設定を新しいコレクション名に更新
4. 検索精度と速度の改善を実感！
