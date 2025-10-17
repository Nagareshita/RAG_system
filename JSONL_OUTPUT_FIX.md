# JSONL出力先の変更 - 修正ログ

## 修正日: 2025年10月17日

## 変更内容

### 修正前の動作
- `JSONL出力`ボタンをクリックすると、自動的に`out`フォルダを作成して出力
- ディレクトリ選択ダイアログでキャンセルしても、`out`フォルダに強制的に出力
- ユーザーが出力先を選択できない

### 修正後の動作
- `JSONL出力`ボタンをクリックすると、ディレクトリ選択ダイアログが表示される
- **デフォルトディレクトリ**: `data/ast`
- ユーザーが任意のディレクトリを選択可能
- キャンセルした場合は出力を中止（フォルダを勝手に作らない）
- 選択したディレクトリが存在しない場合は自動作成

## 修正したファイル

### 1. `tabs/modelica_analyzer_tab.py`
```python
def _export_jsonl(self):
    if not self.records:
        QMessageBox.information(self, "情報", "出力するデータがありません")
        return
    
    # デフォルトの出力先を data/ast に設定
    default_dir = Path(__file__).resolve().parents[1] / "data" / "ast"
    
    # ディレクトリ選択ダイアログを表示
    dir_path = QFileDialog.getExistingDirectory(
        self, 
        "JSONL出力先ディレクトリを選択", 
        str(default_dir)
    )
    
    # キャンセルされた場合は処理を中止
    if not dir_path:
        return
    
    output_dir = Path(dir_path)
    
    # 出力ディレクトリを作成（存在しない場合）
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ... (以下、出力処理)
```

### 2. `ast_jsonl_validator/app.py`
同様の修正を適用（スタンドアロン版）

### 3. `tabs/ast_validator/app.py`
同様の修正を適用（tabs配下のコピー版）

**注**: `tabs/ast_validator/app.py`は`parents[2]`を使用（ディレクトリ階層が1つ深いため）

## 使用方法

### JSONL出力の手順

1. **データ読み込み**
   - ディレクトリ読込でModelicaライブラリを読み込む

2. **検証（推奨）**
   - 分割後検証でデータ品質を確認

3. **JSONL出力**
   - `JSONL出力`ボタンをクリック
   - ディレクトリ選択ダイアログが開く
   - デフォルトで`c:\git\RAG_system\data\ast`が表示される
   - そのまま`OK`で確定、または別のフォルダを選択
   - `キャンセル`で出力を中止

4. **出力結果**
   - 選択したディレクトリに3つのファイルが生成される:
     - `ast_packages.jsonl`
     - `ast_functions.jsonl`
     - `ast_equations.jsonl`

## デフォルトディレクトリについて

### パスの決定方法
- `tabs/modelica_analyzer_tab.py`: `Path(__file__).resolve().parents[1] / "data" / "ast"`
  - `parents[1]` → RAG_systemルートディレクトリ
  - → `c:\git\RAG_system\data\ast`

- `tabs/ast_validator/app.py`: `Path(__file__).resolve().parents[2] / "data" / "ast"`
  - `parents[2]` → RAG_systemルートディレクトリ
  - → `c:\git\RAG_system\data\ast`

### ディレクトリ構造
```
RAG_system/
├── data/
│   └── ast/           ← デフォルト出力先
│       ├── ast_packages.jsonl
│       ├── ast_functions.jsonl
│       └── ast_equations.jsonl
├── tabs/
│   ├── modelica_analyzer_tab.py
│   └── ast_validator/
│       └── app.py
└── ast_jsonl_validator/
    └── app.py
```

## 改善ポイント

✅ **ユーザーフレンドリー**
- 出力先を自由に選択可能
- デフォルトで適切な場所（data/ast）を提案

✅ **安全性向上**
- キャンセル時に勝手にフォルダを作らない
- 意図しない場所へのファイル出力を防止

✅ **柔軟性**
- プロジェクトごとに異なる出力先を選択可能
- 既存のフォルダを選んで上書きも可能

## テスト確認事項

- [x] ディレクトリ選択ダイアログが表示される
- [x] デフォルトで`data/ast`が選択される
- [x] キャンセル時に出力が中止される
- [x] 選択したディレクトリにファイルが出力される
- [x] 存在しないディレクトリを選択しても自動作成される
- [x] エラーなく動作する

---

## ✅ 修正完了

3つのファイル全てで`JSONL出力`機能を修正しました。
- ユーザーが出力先を選択可能
- デフォルトは`data/ast`
- キャンセル時は出力を中止
