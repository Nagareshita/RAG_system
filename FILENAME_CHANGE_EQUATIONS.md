# ファイル名変更: equations.jsonl → ast_equations.jsonl

## 変更日: 2025年10月17日

## 変更内容

出力ファイルの命名規則を統一するため、`equations.jsonl`を`ast_equations.jsonl`にリネームしました。

### 変更理由
- 他のファイル（`ast_packages.jsonl`, `ast_functions.jsonl`）との命名規則の統一
- ファイル名だけで「ASTデータである」ことが明確になる
- プロジェクト内での検索性・識別性の向上

### 修正したファイル

#### 1. split_exporter.py（2ファイル）
- ✅ `ast_jsonl_validator/split_exporter.py`
- ✅ `tabs/ast_validator/split_exporter.py`

**変更内容:**
```python
# 修正前
_write_jsonl(output_dir / "equations.jsonl", equations)

# 修正後
_write_jsonl(output_dir / "ast_equations.jsonl", equations)
```

#### 2. app.py（3ファイル）
- ✅ `ast_jsonl_validator/app.py`
- ✅ `tabs/ast_validator/app.py`
- ✅ `tabs/modelica_analyzer_tab.py`

**変更内容（出力完了メッセージ）:**
```python
# 修正前
f"equations.jsonl: {stats['equations']} 行\n"

# 修正後
f"ast_equations.jsonl: {stats['equations']} 行\n"
```

#### 3. ドキュメント（2ファイル）
- ✅ `JSONL_OUTPUT_FIX.md`
- ✅ `MODELICA_TAB_MIGRATION.md`

## 出力ファイル一覧

### 修正前
```
data/ast/
├── ast_packages.jsonl
├── ast_functions.jsonl
└── equations.jsonl          ← 命名規則が不統一
```

### 修正後（統一済み）
```
data/ast/
├── ast_packages.jsonl
├── ast_functions.jsonl
└── ast_equations.jsonl      ← `ast_`プレフィックスで統一
```

## 各ファイルの内容

| ファイル名 | 内容 | 説明 |
|-----------|------|------|
| `ast_packages.jsonl` | パッケージ、モデル、ブロック、コネクタなどのレコード | クラス定義の構造情報 |
| `ast_functions.jsonl` | 関数レコード | 関数の定義と実装情報 |
| `ast_equations.jsonl` | 方程式レコード | 個別の方程式とその変数情報 |

## 影響範囲

### アプリケーション
- ✅ メインタブ（`tabs/modelica_analyzer_tab.py`）
- ✅ スタンドアロン版（`ast_jsonl_validator/app.py`）
- ✅ tabs配下のコピー版（`tabs/ast_validator/app.py`）

### 後方互換性
- ⚠️ 既存の`equations.jsonl`を参照しているコードがある場合は修正が必要
- 新規出力は全て`ast_equations.jsonl`となります

### 推奨対応
既存の`equations.jsonl`ファイルがある場合:
```powershell
# リネーム
Rename-Item "equations.jsonl" "ast_equations.jsonl"

# または新規出力で上書き
# （アプリから再度JSONL出力を実行）
```

## エラーチェック

全ファイルでエラーなし:
- ✅ `ast_jsonl_validator/split_exporter.py`
- ✅ `tabs/ast_validator/split_exporter.py`
- ✅ `tabs/modelica_analyzer_tab.py`

## 使用例

### JSONL出力後
```bash
# 出力先ディレクトリの確認
ls c:\git\RAG_system\data\ast

# 出力結果:
# ast_packages.jsonl   - パッケージ定義
# ast_functions.jsonl  - 関数定義
# ast_equations.jsonl  - 方程式
```

### 出力完了メッセージ
```
出力先: c:\git\RAG_system\data\ast
ast_packages.jsonl: 150 行
ast_functions.jsonl: 45 行
ast_equations.jsonl: 320 行    ← 新しいファイル名
重複ID: {}
```

---

## ✅ 変更完了

3つのJSONLファイルの命名規則が統一され、全て`ast_`プレフィックスが付きました。
