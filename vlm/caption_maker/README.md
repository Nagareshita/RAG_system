VLM Caption Tester (Two-Stage)

概要
- utils/agents/VLMExecutor と vlm/model_manager をそのまま参照し、改変せずに利用します。
- 画像1枚ごとに二段構えの処理を行います。
  1) 一段目: 画像タイプ分類 (table / plot_graph / natural_image / text_ocr / formula)
  2) 二段目: 分類結果に応じた VLM パラメータ + プロンプトでキャプション生成
- PySide6 のテーブルでサムネイル / ファイル名 / 分類 / プリセット / キャプションを表示します。

起動
```
python -m tests.vlm_caption_tester.app
```

UI 構成
- 画像フォルダ: 既定で `new_pdf_converter/images` を指します。フォルダ選択/スキャン可能。
- 分類(一段目)パラメータ: 温度, top-p, top-k, ビーム数等を編集可能。
- タイプ別プリセット(簡易): table, plot_graph, natural_image, text_ocr, formula ごとにプリセットを選択。
- テーブル: サムネイル / ファイル名 / 分類 / プリセット / キャプションを順に表示。

実装メモ
- VLM の呼び出しは utils/agents/vlm_executor.VLMExecutor を経由し、NodeThresholdManager に都度パラメータを投入して実行します。
- モデルは `vlm/SAIL-VL2-2B` のローカル配置を前提にし、ネットワーク DL を行いません。
- マルチスレッドでの同時推論は避け、ワーカー内で順次処理します（モデルのスレッド安全性を考慮）。

注意
- 初回起動時にモデルのロードに時間がかかることがあります。
- 必要な依存: `PySide6`, `transformers`, `torch` 等（既存環境に準拠）。

