# AST JSONL Validator 改善ログ

## 改善日: 2025年10月17日

### 改善内容

#### 1. プログレスバー表示の修正 ✓

**問題点:**
- ディレクトリ読み込み時に適切なプログレスバーが表示されず、不自然な90%固定表示が重なって表示される
- プログレスウィンドウが立ち上がらない

**解決策:**
- `_Progress`クラスを`QWidget`から`QDialog`に変更し、`QProgressBar`ウィジェットを使用
- `extract_dir`関数の進捗計算を修正し、ファイル数ベースの正確な進捗を報告
- 進捗コールバックのシグネチャを`(message, value)`から`(message, current, total)`に変更
- ファイル処理前に全ファイルをスキャンして総数を取得し、処理中に正確な進捗を表示

**変更ファイル:**
- `app.py`: `_Progress`クラスと`_ExtractWorker`クラスを修正
- `modelica_raw_extractor.py`: `extract_dir`関数を修正

#### 2. 検証機能の強化 ✓

**問題点:**
- 既存の「検証」ボタンは分割前のデータのみを検証
- 実際に保存されるJSONLファイル（分割後）の検証ができない

**解決策:**
- 検証ボタンを2つに分離:
  - **「分割前検証」**: 抽出した生データの品質を確認（データ抽出の品質確認）
  - **「分割後検証」**: 実際に保存される形式（パッケージ、関数、方程式に分割後）を検証
- 分割後検証では以下を確認:
  - 各カテゴリのレコード数
  - ID重複チェック
  - サイズ統計（最小/最大/平均、10KB超過件数）
  - 分割統計（分割されたパッケージ/関数の数）

**利点:**
- 保存前に実際のJSONL出力の品質を確認可能
- ID重複などの問題を事前に検出
- メモリ上で検証するため、ファイルを書き出す前に問題を発見できる

**変更ファイル:**
- `app.py`: `_run_validation`を`_run_validation_raw`と`_run_validation_split`に分離

#### 3. UIの改善

**追加機能:**
- プログレスバーに詳細情報（現在の処理数/総数）を表示
- エラー発生時もプログレスバーに反映
- ダイアログのモーダル表示で処理中の操作ミスを防止

### 使用方法

1. **ファイル/ディレクトリ読込**
   - 「ファイル読込」: 単一の.moファイルを読み込み
   - 「ディレクトリ読込」: フォルダ内の全.moファイルを再帰的に読み込み
   - プログレスバーで処理状況をリアルタイム表示

2. **分割前検証**
   - 抽出したデータの品質確認
   - コード長、重複、種別内訳などを表示

3. **分割後検証** ⭐ 新機能
   - 実際に保存される形式での検証
   - パッケージ/関数/方程式の各カテゴリを分析
   - ID重複、サイズ超過、分割統計を確認

4. **JSONL出力**
   - 検証結果を確認後、実際のJSONLファイルを出力

5. **JSONL検証**
   - 既存のJSONLファイルを読み込んで検証

### 技術的詳細

#### プログレスバーの実装
```python
class _Progress(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setModal(True)  # モーダルダイアログ
        self.progress_bar = QProgressBar()  # 実際のプログレスバー
        self.progress_bar.setRange(0, 100)
        
    def update(self, message: str, value: int, maximum: int = 100):
        pct = int((value / maximum) * 100) if maximum else 0
        self.progress_bar.setValue(pct)
        self.detail_label.setText(f"{value} / {maximum}")
```

#### 分割後検証の実装
```python
def _run_validation_split(self):
    # メモリ上で分割処理を実行
    packages, functions, equations, split_stats = build_split_outputs(
        self.records, self.repo_context
    )
    
    # 各カテゴリを分析
    # - ID重複チェック
    # - サイズ統計
    # - 分割統計
```

### テスト推奨事項

1. ✓ 小規模ディレクトリでプログレスバーの動作確認
2. ✓ 分割前検証と分割後検証の結果比較
3. ✓ 大規模データでの分割統計確認
4. ✓ ID重複が検出される場合のエラーメッセージ確認

### 今後の改善案

- [ ] 検証結果のエクスポート機能（CSV/JSON）
- [ ] 分割後検証で検出された問題の自動修正機能
- [ ] プログレスバーのキャンセル機能
- [ ] 検証結果の可視化（グラフ表示）
