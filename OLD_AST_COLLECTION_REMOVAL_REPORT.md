# 旧ASTコレクション完全削除レポート

## 実施日時
2025年10月17日

## 問題の特定

### 症状
`rag_documents_ast` フォルダが作成され続ける

### 原因
1. **既存の設定ファイル**に旧コレクション名が保存されていた
2. Agent Designerがこれらの設定を読み込み、旧コレクションを参照
3. 検索時にコレクションが存在しないと自動作成される

## 実施した対策

### 1. コード内の参照削除 ✅

#### a) agent_designer/ui/agent_settings/retriever/config.py
```python
# 変更前
'options': [
    ('rag_documents_pdf', 'rag_documents_pdf（PDF検索）'),
    ('rag_documents_ast', 'rag_documents_ast（AST検索）')
]

# 変更後
'options': [
    ('rag_documents_pdf', 'rag_documents_pdf（PDF検索）'),
    ('rag_documents_ast_packages', 'rag_documents_ast_packages（ASTパッケージ）'),
    ('rag_documents_ast_functions', 'rag_documents_ast_functions（AST関数）'),
    ('rag_documents_ast_equations', 'rag_documents_ast_equations（AST方程式）')
]
```

#### b) agent_designer/ui/node_settings.py
旧コレクション名へのフォールバックロジックを削除し、新しい3つのコレクションに対応

### 2. 既存設定ファイルの更新 ✅

#### 作成したツール
`scripts/update_ast_collection_refs.py`
- configs/designs/*.json 内の `rag_documents_ast` を自動検出
- `rag_documents_ast_packages` に自動更新
- バックアップファイル（*.backup）を自動作成

#### 実行結果
```
処理中: test5.json
  .node_thresholds.3.target_collections: rag_documents_ast → rag_documents_ast_packages
  バックアップ作成: configs\designs\test5.json.backup
  ✓ 更新完了

完了: 1/6 ファイルを更新しました
```

### 3. 旧コレクションフォルダの削除 ✅

#### 場所
`vector_db/collection/rag_documents_ast/`

#### 削除コマンド
```powershell
Remove-Item -Recurse -Force vector_db\collection\rag_documents_ast
```

#### 削除後の確認
```
vector_db/collection/
├── rag_documents_ast_equations/     ✓
├── rag_documents_ast_functions/     ✓
├── rag_documents_ast_packages/      ✓
└── rag_documents_pdf/               ✓
```

## 現在の状態

### コレクション構造
- ✅ `rag_documents_ast_packages` - ASTパッケージ専用
- ✅ `rag_documents_ast_functions` - AST関数専用
- ✅ `rag_documents_ast_equations` - AST方程式専用
- ✅ `rag_documents_pdf` - PDF文書専用
- ❌ `rag_documents_ast` - 完全に削除

### 影響を受けるファイル

#### 更新済み ✅
- `utils/vector_manager.py` - 3つのコレクション分離ロジック実装
- `agent_designer/ui/agent_settings/retriever/config.py` - UI選択肢更新
- `agent_designer/ui/node_settings.py` - 新コレクション対応
- `configs/designs/test5.json` - 設定値更新（バックアップ作成済み）

#### 影響なし
- `tabs/vectorization_tab.py` - 変更不要（既存インターフェースで動作）
- 検索機能 - コレクション名を受け取るだけなので変更不要

## 検証項目

### ✅ 完了した検証
1. コード内に `rag_documents_ast` への参照がないことを確認
2. 設定ファイルを更新してバックアップを作成
3. 旧コレクションフォルダを削除
4. 新しい4つのコレクションが正しく存在することを確認

### ⏳ 次のステップ
1. main.pyを起動して動作確認
2. Agent Designerで新しいコレクション選択肢が表示されることを確認
3. ベクトル化タブで3つのASTファイルが正しく分離されることを確認
4. 検索機能が新しいコレクションで正常に動作することを確認

## トラブルシューティング

### 万が一 rag_documents_ast が再作成された場合

#### 1. 設定ファイルを再確認
```powershell
# configs/designs/*.json 内に rag_documents_ast が残っていないか確認
Get-ChildItem configs/designs/*.json | Select-String "rag_documents_ast" -Context 1,1
```

#### 2. コード内を再検索
```powershell
# Python ファイル内に rag_documents_ast への参照が残っていないか確認
Get-ChildItem -Recurse -Include *.py | Select-String 'rag_documents_ast"' -Exclude "*_packages*","*_functions*","*_equations*"
```

#### 3. バックアップから復元
```powershell
# 必要に応じて .backup ファイルから復元
Copy-Item configs/designs/test5.json.backup configs/designs/test5.json -Force
```

## 作成されたドキュメント

1. **DEDUPLICATION_AND_OPTION_A_IMPLEMENTATION.md**
   - 重複防止機能とオプションAの実装詳細
   
2. **MIGRATION_FROM_OLD_AST_COLLECTION.md**
   - 旧コレクションからの移行ガイド
   - ユーザー向け手順書
   
3. **OLD_AST_COLLECTION_REMOVAL_REPORT.md** (本ファイル)
   - 完全削除の実施レポート

4. **scripts/update_ast_collection_refs.py**
   - 設定ファイル自動更新ツール

## まとめ

### 実施した作業
- ✅ コード内の参照削除（2ファイル）
- ✅ 既存設定ファイルの更新（1ファイル）
- ✅ 旧コレクションフォルダの削除
- ✅ 自動更新スクリプトの作成
- ✅ ドキュメント作成（3ファイル）

### 効果
- 🎯 旧コレクションへの参照が完全に削除された
- 🎯 新しい3つのコレクション構造に完全移行
- 🎯 既存の設定ファイルも更新済み
- 🎯 今後 `rag_documents_ast` が作成されることはない

### 次のアクション
main.pyを起動してベクトル化と検索の動作確認を実行してください。
