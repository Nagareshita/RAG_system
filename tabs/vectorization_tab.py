# tabs/vectorization_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QPushButton, QFileDialog, QTextEdit, QProgressBar,
                               QLabel, QListWidget, QComboBox, QSpinBox, QCheckBox,
                               QLineEdit, QSplitter, QDialog, QDoubleSpinBox,
                               QTabWidget,
                               QSizePolicy)
from PySide6.QtCore import Qt
from utils.vector_manager import VectorManager
from tabs.query_optimaizer.optimizer import optimize_query
import os

class VectorizationTab(QWidget):
    def __init__(self):
        super().__init__()
        # シングルトンインスタンスを取得
        self.vector_manager = VectorManager()
        self.selected_files = []
        self.search_config_file = "configs/vectorization_search_settings.json"
        self.setup_ui()
        # 初期値で自動計算実行
        self.update_encode_batch()
        # 検索設定を自動読み込み
        self.load_search_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # ファイル選択
        file_group = QGroupBox("ファイル選択")
        file_layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        self.select_ast_button = QPushButton("AST JSONLフォルダ選択")
        self.select_pdf_button = QPushButton("PDF JSONフォルダ選択")
        
        self.select_ast_button.clicked.connect(self.select_ast_folder)
        self.select_pdf_button.clicked.connect(self.select_pdf_folder)
        
        button_layout.addWidget(self.select_ast_button)
        button_layout.addWidget(self.select_pdf_button)
        
        file_layout.addLayout(button_layout)
        
        self.file_list = QListWidget()
        file_layout.addWidget(QLabel("選択されたファイル:"))
        file_layout.addWidget(self.file_list)
        
        # ファイル構造表示エリア
        self.structure_text = QTextEdit()
        self.structure_text.setMaximumHeight(150)
        self.structure_text.setReadOnly(True)
        file_layout.addWidget(QLabel("ファイル構造解析結果:"))
        file_layout.addWidget(self.structure_text)
        
        # コンパクト化: 高さとリストの上限を抑える
        self.file_list.setMaximumHeight(100)
        file_group.setLayout(file_layout)
        file_group.setMaximumHeight(220)
        file_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        # ベクトル化設定
        vector_group = QGroupBox("ベクトル化設定")
        vector_layout = QVBoxLayout()
        
        # モデル情報
        self.model_label = QLabel("モデル: BAAI/bge-m3")
        vector_layout.addWidget(self.model_label)
        
        # 保存方式は常に分離（混合は廃止）
        from PySide6.QtWidgets import QSpinBox, QCheckBox
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("保存方式: 分離（固定）"))
        vector_layout.addLayout(mode_layout)
        
        # パフォーマンス設定
        perf_layout = QHBoxLayout()
        
        # バッチサイズ設定
        perf_layout.addWidget(QLabel("バッチサイズ:"))
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 256)
        self.batch_size_spinbox.setValue(128)
        # エンコードバッチの自動更新を接続
        self.batch_size_spinbox.valueChanged.connect(self.update_encode_batch)
        perf_layout.addWidget(self.batch_size_spinbox)
        
        # エンコードバッチサイズ（自動計算）
        perf_layout.addWidget(QLabel("エンコードバッチ:"))
        self.encode_batch_spinbox = QSpinBox()
        self.encode_batch_spinbox.setRange(1, 128)
        self.encode_batch_spinbox.setValue(64)
        perf_layout.addWidget(self.encode_batch_spinbox)
        
        # 自動計算チェックボックス
        self.auto_encode_checkbox = QCheckBox("自動計算")
        self.auto_encode_checkbox.setChecked(True)
        self.auto_encode_checkbox.toggled.connect(self.toggle_auto_encode)
        perf_layout.addWidget(self.auto_encode_checkbox)
        
        # GPUチェックボックス
        self.gpu_checkbox = QCheckBox("GPU使用")
        self.gpu_checkbox.setChecked(True)
        perf_layout.addWidget(self.gpu_checkbox)
        
        vector_layout.addLayout(perf_layout)
        
        # テキスト長制限設定（推奨値付き）
        text_limit_layout = QVBoxLayout()
        
        text_input_layout = QHBoxLayout()
        text_input_layout.addWidget(QLabel("最大テキスト長:"))
        self.max_text_length_spinbox = QSpinBox()
        self.max_text_length_spinbox.setRange(100, 5000)
        self.max_text_length_spinbox.setValue(1500)  # 推奨値に変更
        text_input_layout.addWidget(self.max_text_length_spinbox)
        text_limit_layout.addLayout(text_input_layout)
        
        # 推奨値ラベル
        recommendation_label = QLabel("推奨: 1000-2000文字 (文脈保持とノイズ削減のバランス)")
        recommendation_label.setStyleSheet("color: #666; font-size: 10px;")
        text_limit_layout.addWidget(recommendation_label)
        
        vector_layout.addLayout(text_limit_layout)
        
        # 実行ボタンとプログレスバー
        self.vectorize_button = QPushButton("ベクトル化実行")
        self.vectorize_button.clicked.connect(self.start_vectorization)
        
        self.progress_bar = QProgressBar()
        
        vector_layout.addWidget(self.vectorize_button)
        vector_layout.addWidget(self.progress_bar)
        
        vector_group.setLayout(vector_layout)
        
        # 検索タブ（設定/ログ/結果）
        self.search_tabs = QTabWidget()

        # 設定タブ
        settings_widget = QWidget()
        search_layout = QVBoxLayout(settings_widget)

        # 入力行
        row = QHBoxLayout()
        row.addWidget(QLabel("クエリ:"))
        self.search_query = QLineEdit()
        self.search_query.setToolTip("検索したいキーワード。例: IF97 密度 p s / Rotational support tau など")
        row.addWidget(self.search_query, stretch=7)  # 横幅を少し小さく
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self.run_search)
        row.addWidget(self.search_button, stretch=1)  # 右横に配置
        search_layout.addLayout(row)

        # 最適化オプション
        row_optq = QHBoxLayout()
        self.chk_optimize_query = QCheckBox("ユーザークエリを最適化")
        self.chk_optimize_query.setChecked(False)
        self.chk_optimize_query.setToolTip("VLMを用いてクエリを最適化（候補は1件、失敗時はエラー）")
        row_optq.addWidget(self.chk_optimize_query)
        row_optq.addWidget(QLabel("VLMプリセット:"))
        self.combo_opt_preset = QComboBox()
        self.combo_opt_preset.addItems(["qa", "accurate", "balanced", "code", "ocr", "creative", "summary", "json"])
        self.combo_opt_preset.setEnabled(False)
        row_optq.addWidget(self.combo_opt_preset)
        # チェックに応じて有効化
        def _toggle_opt(v):
            self.combo_opt_preset.setEnabled(self.chk_optimize_query.isChecked())
        self.chk_optimize_query.toggled.connect(_toggle_opt)
        search_layout.addLayout(row_optq)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Dense TopK:"))
        self.search_topk = QSpinBox()
        self.search_topk.setRange(1, 200)
        self.search_topk.setValue(50)
        self.search_topk.setToolTip("Dense検索で最初に取得する候補数。大きいほど網羅的だが時間増")
        row2.addWidget(self.search_topk)
        row2.addWidget(QLabel("最終候補数:"))
        self.search_finalk = QSpinBox()
        self.search_finalk.setRange(1, 100)
        self.search_finalk.setValue(15)
        self.search_finalk.setToolTip("最終的に返す件数。再ランク後に上位から切り出し")
        row2.addWidget(self.search_finalk)
        row2.addWidget(QLabel("閾値:"))
        self.search_threshold = QDoubleSpinBox()
        self.search_threshold.setRange(0.0, 1.0)
        self.search_threshold.setSingleStep(0.01)
        self.search_threshold.setValue(0.0)
        self.search_threshold.setToolTip("Denseスコアの下限。0.0はフィルタ無し、数値を上げると高スコアのみ残す")
        row2.addWidget(self.search_threshold)
        self.search_use_reranker = QCheckBox("再ランク使用")
        self.search_use_reranker.setChecked(True)
        self.search_use_reranker.setToolTip("クロスエンコーダで上位候補を文脈で再評価。精度↑だが時間増")
        row2.addWidget(self.search_use_reranker)
        search_layout.addLayout(row2)

        # 検索対象の選択（AST3種+PDF）
        cross_row = QHBoxLayout()
        cross_row.addWidget(QLabel("検索対象:"))
        self.chk_ast_pkgs = QCheckBox("packages")
        self.chk_ast_funcs = QCheckBox("functions")
        self.chk_ast_eqs = QCheckBox("equations")
        self.chk_pdf = QCheckBox("pdf")
        tip_cross = (
            "検索対象: 選択した複数コレクション（ASTの3種+PDF）をまたいで候補を収集。\n"
            "処理: 各コレクションでDense検索→候補を統合→（任意で擬似ハイブリッド）→再ランク"
        )
        for w in [self.chk_ast_pkgs, self.chk_ast_funcs, self.chk_ast_eqs, self.chk_pdf]:
            w.setToolTip(tip_cross)
        for w in [self.chk_ast_pkgs, self.chk_ast_funcs, self.chk_ast_eqs, self.chk_pdf]:
            w.setChecked(False)
            cross_row.addWidget(w)
        self.chk_select_all = QCheckBox("全選択")
        def toggle_all(state):
            checked = self.chk_select_all.isChecked()
            self.chk_ast_pkgs.setChecked(checked)
            self.chk_ast_funcs.setChecked(checked)
            self.chk_ast_eqs.setChecked(checked)
            self.chk_pdf.setChecked(checked)
        self.chk_select_all.toggled.connect(toggle_all)
        cross_row.addWidget(self.chk_select_all)
        search_layout.addLayout(cross_row)

        # 疑似スパースは削除（シンプル化）

        # チューニング行（再ランクモデル / スコア合成 / プレビュー長 / 計測）
        tune_row = QHBoxLayout()
        tune_row.addWidget(QLabel("再ランクモデル:"))
        self.search_reranker_model = QComboBox()
        self.search_reranker_model.addItems([
            "BAAI/bge-reranker-large",
            "BAAI/bge-reranker-base",
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        ])
        self.search_reranker_model.setToolTip(
            "再ランクモデル: 上位候補を文脈で再評価。\n"
            "- bge-reranker-large: 精度高いが重い\n- bge-reranker-base: 中庸\n- MiniLM: 軽量で速いが精度は低め"
        )
        tune_row.addWidget(self.search_reranker_model)
        tune_row.addWidget(QLabel("スコア合成α(再ランク):"))
        self.search_mix_alpha = QDoubleSpinBox()
        self.search_mix_alpha.setRange(0.0, 1.0)
        self.search_mix_alpha.setSingleStep(0.05)
        self.search_mix_alpha.setValue(1.0)  # 1.0=完全に再ランクのみ
        self.search_mix_alpha.setToolTip(
            "スコア合成α: 最終 = α*再ランク + (1-α)*Dense。\n再ランクを強く信頼するほどαを大きく。"
        )
        tune_row.addWidget(self.search_mix_alpha)
        tune_row.addWidget(QLabel("プレビュー長:"))
        self.search_preview_len = QSpinBox()
        self.search_preview_len.setRange(40, 1000)
        self.search_preview_len.setValue(120)
        self.search_preview_len.setToolTip("結果行に表示する文字数の上限")
        tune_row.addWidget(self.search_preview_len)
        self.search_show_timings = QCheckBox("時間を表示")
        self.search_show_timings.setChecked(True)
        self.search_show_timings.setToolTip("Dense/横断候補/再ランクの所要時間をログに表示")
        tune_row.addWidget(self.search_show_timings)
        search_layout.addLayout(tune_row)

        # 検索設定保存ボタン
        save_search_layout = QHBoxLayout()
        self.save_search_button = QPushButton("検索設定を保存")
        self.save_search_button.clicked.connect(self.save_search_settings)
        self.save_search_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        save_search_layout.addWidget(self.save_search_button)
        search_layout.addLayout(save_search_layout)

        # 結果タブ
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        self.search_results = QListWidget()
        results_layout.addWidget(self.search_results)

        # ログタブ
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        self.log_text = QTextEdit()
        log_layout.addWidget(self.log_text)

        # タブに追加
        self.search_tabs.addTab(settings_widget, "設定")
        self.search_tabs.addTab(log_widget, "ログ")
        self.search_tabs.addTab(results_widget, "検索結果")
        
        layout.addWidget(file_group)
        layout.addWidget(vector_group)
        layout.addWidget(self.search_tabs)
        
        self.setLayout(layout)
        
        # 詳細表示: 結果リストのダブルクリック
        self.search_results.itemDoubleClicked.connect(self.open_result_detail)
        self.search_last_results = []
        self._search_progress_dialog = None
        self._search_progress_label = None
        self._search_progress_bar = None

    def run_search(self):
        try:
            q_raw = self.search_query.text().strip()
            topk = self.search_topk.value()
            finalk = self.search_finalk.value()
            use_reranker = self.search_use_reranker.isChecked()
            threshold = float(self.search_threshold.value())
            reranker_name = self.search_reranker_model.currentText()
            alpha = float(self.search_mix_alpha.value())
            preview_len = self.search_preview_len.value()
            show_timings = self.search_show_timings.isChecked()
            # 検索対象の選択
            cross_cols = []
            if self.chk_ast_pkgs.isChecked():
                cross_cols.append("rag_documents_ast_packages")
            if self.chk_ast_funcs.isChecked():
                cross_cols.append("rag_documents_ast_functions")
            if self.chk_ast_eqs.isChecked():
                cross_cols.append("rag_documents_ast_equations")
            if self.chk_pdf.isChecked():
                cross_cols.append("rag_documents_pdf")
            use_cross = len(cross_cols) > 0
            # 疑似スパース機能は削除済み
            self.search_results.clear()
            self.search_last_results = []
            if not q_raw:
                self.log_text.append("検索クエリが空です")
                return
            if not use_cross:
                # ポップアップを表示
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "検索対象未選択", "検索対象コレクションを選択してください")
                return

            # ログ: 検索開始
            self.log_text.append(f"[検索] 開始: cols={cross_cols}, dense_topk={topk}, final_k={finalk}, reranker={use_reranker}, thr={threshold}, alpha={alpha}")
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            # 進捗ウィンドウ表示
            self._show_search_progress("準備中…")

            # モデル初期化
            if not self.vector_manager.model:
                self.log_text.append("[検索] モデル初期化を実行")
                self._update_search_progress("モデル初期化中…")
                ok = self.vector_manager.initialize_model(self.gpu_checkbox.isChecked())
                if not ok:
                    self.log_text.append("[検索] モデル初期化に失敗")
                    self._close_search_progress()
                    return

            # クエリ最適化（候補数=1固定）
            q = q_raw
            if self.chk_optimize_query.isChecked():
                # フォーカス推定: 優先順位 functions > equations > packages > pdf
                # 複数選択時は、最も具体的なもの（functions）を優先
                focus = "general"  # デフォルト
                if self.chk_pdf.isChecked():
                    focus = "pdf"
                if self.chk_ast_pkgs.isChecked():
                    focus = "packages"
                if self.chk_ast_eqs.isChecked():
                    focus = "equations"
                if self.chk_ast_funcs.isChecked():
                    focus = "functions"
                
                preset = self.combo_opt_preset.currentText()
                try:
                    self.log_text.append(f"[最適化] 実行: focus={focus}, preset={preset}")
                    self._update_search_progress("クエリ最適化中…")
                    q = optimize_query(q_raw, focus=focus, preset=preset, use_vlm=True)
                    self.log_text.append(f"[最適化] 元クエリ: {q_raw[:50]}{'...' if len(q_raw) > 50 else ''}")
                    self.log_text.append(f"[最適化] 最適化後: {q}")
                except Exception as e:
                    self.log_text.append(f"[最適化] エラー: {e}")
                    self._close_search_progress()
                    return

            # 再ランク初期化
            if use_reranker and not getattr(self.vector_manager, 'reranker_model', None):
                self.log_text.append(f"[検索] 再ランクモデル初期化を実行 ({reranker_name})")
                ok = self.vector_manager.initialize_reranker(reranker_name)
                if not ok:
                    self.log_text.append("[検索] 再ランクモデル初期化に失敗。再ランクなしで続行")
                    use_reranker = False

            # Dense検索（検索対象で候補統合）
            import time
            self.log_text.append("[検索] Dense検索を実行中…")
            self._update_search_progress("Dense検索実行中…")
            t0 = time.perf_counter()
            initial_results = self.vector_manager.search_across_collections(
                query=q,
                collections=cross_cols,
                initial_k=topk,
                final_k=max(finalk, topk),
                similarity_threshold=threshold,
                use_reranker=False,
                use_hybrid=False,
                dense_weight=1.0,
                sparse_weight=0.0,
            )
            dt_dense = (time.perf_counter() - t0) * 1000
            if show_timings:
                self.log_text.append(f"[検索] Dense結果: {len(initial_results)} 件 ({dt_dense:.1f} ms)")

            # 再ランク
            if use_reranker and initial_results:
                self.log_text.append("[検索] 再ランクを実行中…")
                self._update_search_progress("再ランク実行中…")
                t1 = time.perf_counter()
                reranked = self.vector_manager._rerank_results(q, initial_results)
                dt_rerank = (time.perf_counter() - t1) * 1000
                # スコア合成: final = alpha*rerank + (1-alpha)*dense
                mixed = []
                for itm in reranked:
                    rer = float(itm.get("score", 0.0))
                    org = float(itm.get("original_score", rer))
                    final_score = alpha * rer + (1.0 - alpha) * org
                    itm2 = dict(itm)
                    itm2["final_score"] = final_score
                    mixed.append(itm2)
                mixed.sort(key=lambda x: x.get("final_score", x.get("score", 0.0)), reverse=True)
                # fqn重複を除去してから最終件数に切り詰め
                results = self._dedup_by_fqn(mixed)[:finalk]
                if show_timings:
                    self.log_text.append(f"[検索] 再ランク完了: {len(results)} 件 ({dt_rerank:.1f} ms)")
            else:
                # fqn重複を除去してから最終件数に切り詰め
                results = self._dedup_by_fqn(initial_results)[:finalk]
                self.log_text.append(f"[検索] 再ランク未実行: {len(results)} 件")

            # 結果表示
            for r in results:
                text = r.get("text") or ""
                preview = (text[:preview_len] + "…") if isinstance(text, str) and len(text) > preview_len else text
                score = r.get("final_score", r.get("score", 0.0))
                chunk_id = r.get("chunk_id") or r.get("entry_id")
                col_name = r.get("collection", "")
                # 併記: (rerank / dense)
                if use_reranker:
                    rer = r.get("score")
                    org = r.get("original_score", rer)
                    self.search_results.addItem(f"[{col_name}] {score:.3f} (rer:{rer:.3f}/dense:{org:.3f})\t{chunk_id}\t{preview}")
                else:
                    self.search_results.addItem(f"[{col_name}] {score:.3f}\t{chunk_id}\t{preview}")
            self.search_last_results = results

            self.log_text.append("[検索] 完了")
            # 検索結果タブをアクティブに
            try:
                self.search_tabs.setCurrentIndex(2)
                self._close_search_progress()
            except Exception:
                self._close_search_progress()
        except Exception as e:
            self.log_text.append(f"検索エラー: {e}")
            self._close_search_progress()

    def open_result_detail(self, item):
        try:
            row = self.search_results.currentRow()
            if row < 0 or row >= len(self.search_last_results):
                return
            result = self.search_last_results[row]
            dlg = QDialog(self)
            dlg.setWindowTitle("検索結果の詳細")
            dlg.resize(800, 600)
            v = QVBoxLayout(dlg)
            text = QTextEdit()
            text.setReadOnly(True)
            # 詳細内容を整形
            try:
                import json
                pretty = json.dumps(result, ensure_ascii=False, indent=2)
            except Exception:
                pretty = str(result)
            text.setText(pretty)
            v.addWidget(text)
            btns = QHBoxLayout()
            close_btn = QPushButton("閉じる")
            close_btn.clicked.connect(dlg.accept)
            btns.addWidget(close_btn)
            v.addLayout(btns)
            dlg.exec()
        except Exception as e:
            self.log_text.append(f"詳細表示エラー: {e}")

    def update_encode_batch(self):
        """バッチサイズに基づいてエンコードバッチを自動更新"""
        if self.auto_encode_checkbox.isChecked():
            batch_size = self.batch_size_spinbox.value()
            # エンコードバッチ = バッチサイズ / 2 (最小8、最大64)
            encode_batch = max(8, min(64, batch_size // 2))
            self.encode_batch_spinbox.setValue(encode_batch)

    def toggle_auto_encode(self, checked):
        """エンコードバッチの自動計算ON/OFF"""
        self.encode_batch_spinbox.setEnabled(not checked)
        if checked:
            self.update_encode_batch()

    # ===== 検索用 進捗ダイアログ =====
    def _show_search_progress(self, text: str = "処理中…"):
        try:
            if self._search_progress_dialog is not None:
                return
            dlg = QDialog(self)
            dlg.setWindowTitle("検索中…")
            dlg.setModal(True)
            lay = QVBoxLayout(dlg)
            label = QLabel(text)
            bar = QProgressBar()
            bar.setRange(0, 0)
            lay.addWidget(label)
            lay.addWidget(bar)
            self._search_progress_dialog = dlg
            self._search_progress_label = label
            self._search_progress_bar = bar
            dlg.resize(360, 100)
            dlg.show()
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.processEvents()
        except Exception:
            self._search_progress_dialog = None

    def _update_search_progress(self, text: str):
        try:
            if self._search_progress_dialog and self._search_progress_label:
                self._search_progress_label.setText(text)
                from PySide6.QtCore import QCoreApplication
                QCoreApplication.processEvents()
        except Exception:
            pass

    def _close_search_progress(self):
        try:
            if self._search_progress_dialog:
                self._search_progress_dialog.accept()
        except Exception:
            pass
        finally:
            self._search_progress_dialog = None
            self._search_progress_label = None
            self._search_progress_bar = None

    # ===== 検索結果ユーティリティ =====
    def _dedup_by_fqn(self, items):
        """metadata.fqn が同一の結果を重複排除（先勝ち）。
        - 引数はスコア降順であることを前提に、最初の出現を採用。
        - fqnが無い結果はそのまま通す。
        """
        seen = set()
        out = []
        for r in items:
            fqn = None
            md = r.get("metadata") if isinstance(r, dict) else None
            if isinstance(md, dict):
                fqn = md.get("fqn") or md.get("metadata.fqn")
            if fqn:
                if fqn in seen:
                    continue
                seen.add(fqn)
            out.append(r)
        return out

    def select_ast_folder(self):
        """ASTフォルダを選択してJSONLファイルを再帰的に検索"""
        folder = QFileDialog.getExistingDirectory(self, "AST JSONLフォルダ選択")
        if folder:
            self._scan_folder_for_files(folder, ".jsonl", "AST")

    def select_pdf_folder(self):
        """PDFフォルダを選択してJSONファイルを再帰的に検索"""
        folder = QFileDialog.getExistingDirectory(self, "PDF JSONフォルダ選択")
        if folder:
            self._scan_folder_for_files(folder, ".json", "PDF")

    def _scan_folder_for_files(self, folder_path, extension, file_type):
        """フォルダを再帰的にスキャンして指定拡張子のファイルを収集"""
        import glob
        
        # 再帰的にファイルを検索
        pattern = os.path.join(folder_path, "**", f"*{extension}")
        found_files = glob.glob(pattern, recursive=True)
        
        if not found_files:
            self.log_text.append(f"⚠️ {folder_path} に{extension}ファイルが見つかりませんでした")
            return
        
        # 既存のselected_filesリストに追加
        if not hasattr(self, 'selected_files'):
            self.selected_files = []
        
        new_files = 0
        for file_path in found_files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.file_list.addItem(f"{file_type}: {os.path.basename(file_path)}")
                self._analyze_and_display_structure(file_path)
                new_files += 1
        
        self.log_text.append(f"📁 {file_type}フォルダから{new_files}個の新しいファイルを追加しました")



    def select_ast_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "AST JSONLファイル選択", "", "JSONL Files (*.jsonl)"
        )
        self.selected_files = getattr(self, 'selected_files', [])
        for file in files:
            self.file_list.addItem(f"AST: {os.path.basename(file)}")
            self.selected_files.append(file)
            self._analyze_and_display_structure(file)
                
    def select_pdf_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "PDF JSONファイル選択", "", "JSON Files (*.json)"
        )
        self.selected_files = getattr(self, 'selected_files', [])
        for file in files:
            self.file_list.addItem(f"PDF: {os.path.basename(file)}")
            self.selected_files.append(file)
            self._analyze_and_display_structure(file)

    def _analyze_and_display_structure(self, file_path):
        """ファイル構造を解析してUIに表示"""
        try:
            structure = self.vector_manager.analyze_file_structure(file_path)
            
            display_text = f"📁 {os.path.basename(file_path)}\n"
            display_text += f"形式: {structure.get('file_type', 'Unknown')}\n"
            display_text += f"エントリー数: {structure.get('total_entries', 0)}\n"
            
            if structure.get('text_fields'):
                display_text += f"検出されたテキストフィールド: {', '.join(structure['text_fields'])}\n"
            else:
                display_text += "テキストフィールド: なし\n"
                
            if structure.get('error'):
                display_text += f"⚠️ エラー: {structure['error']}\n"
                
            display_text += "-" * 50 + "\n"
            
            self.structure_text.append(display_text)
            self.log_text.append(f"ファイル解析完了: {os.path.basename(file_path)}")
            
        except Exception as e:
            error_msg = f"構造解析エラー ({os.path.basename(file_path)}): {str(e)}"
            self.structure_text.append(error_msg)
            self.log_text.append(error_msg)

    def start_vectorization(self):
        """プログレスバー連携版ベクトル化処理"""
        try:
            # 選択されたファイルがあるかチェック
            if not hasattr(self, 'selected_files') or not self.selected_files:
                self.log_text.append("ファイルが選択されていません")
                return
            
            self.log_text.append("ベクトル化を開始します...")
            self.progress_bar.setValue(0)
            
            # 各ファイルの構造解析
            file_structures = []
            for i, file_path in enumerate(self.selected_files):
                self.log_text.append(f"構造解析中: {os.path.basename(file_path)}")
                structure = self.vector_manager.analyze_file_structure(file_path)
                
                if structure.get('error'):
                    self.log_text.append(f"構造解析エラー: {structure['error']}")
                    continue
                    
                file_structures.append(structure)
                progress = int((i + 1) / len(self.selected_files) * 30)  # 0-30%
                self.progress_bar.setValue(progress)
            
            if not file_structures:
                self.log_text.append("処理可能なファイルがありません")
                return
            
            self.log_text.append(f"{len(file_structures)}ファイルの構造解析完了")
            self.progress_bar.setValue(30)
            
            # プログレスバー更新用コールバック
            def update_progress(value):
                self.progress_bar.setValue(value)
                
            # ログ更新用コールバック
            def update_log(message):
                self.log_text.append(message)
                # GUIの更新を強制
                from PySide6.QtCore import QCoreApplication
                QCoreApplication.processEvents()
            
            # 実際のベクトル化実行
            self.log_text.append("ベクトル化処理開始...")

            # UI設定値を取得
            batch_size = self.batch_size_spinbox.value()
            encode_batch_size = self.encode_batch_spinbox.value()
            max_text_length = self.max_text_length_spinbox.value()

            self.vector_manager.use_gpu = self.gpu_checkbox.isChecked()

            success = self.vector_manager.vectorize_documents(
                file_structures, 
                progress_callback=update_progress,
                log_callback=update_log,
                batch_size=batch_size,
                encode_batch_size=encode_batch_size,  # 実際に使用されるように修正済み
                max_text_length=max_text_length
            )
            
            if success:
                self.log_text.append("ベクトル化完了！")
                self.progress_bar.setValue(100)
            else:
                self.log_text.append("ベクトル化に失敗しました")
                self.progress_bar.setValue(0)
                
        except Exception as e:
            error_msg = f"ベクトル化エラー: {str(e)}"
            self.log_text.append(error_msg)
            self.progress_bar.setValue(0)
            print(f"詳細エラー: {e}")

    def save_search_settings(self):
        """検索設定をJSONファイルに保存"""
        try:
            import json
            
            settings = {
                # 検索設定
                "dense_topk": self.search_topk.value(),
                "final_k": self.search_finalk.value(),
                "threshold": self.search_threshold.value(),
                "use_reranker": self.search_use_reranker.isChecked(),
                "reranker_model": self.search_reranker_model.currentText(),
                "mix_alpha": self.search_mix_alpha.value(),
                "preview_len": self.search_preview_len.value(),
                "show_timings": self.search_show_timings.isChecked(),
                
                # クエリ最適化
                "optimize_query": self.chk_optimize_query.isChecked(),
                "opt_preset": self.combo_opt_preset.currentText(),
                
                # 検索対象
                "search_target": {
                    "ast_packages": self.chk_ast_pkgs.isChecked(),
                    "ast_functions": self.chk_ast_funcs.isChecked(),
                    "ast_equations": self.chk_ast_eqs.isChecked(),
                    "pdf": self.chk_pdf.isChecked()
                }
            }
            
            # configsフォルダが存在しない場合は作成
            import os
            os.makedirs(os.path.dirname(self.search_config_file), exist_ok=True)
            
            # JSONファイルに保存
            with open(self.search_config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            self.log_text.append(f"✅ 検索設定を保存しました: {self.search_config_file}")
            
        except Exception as e:
            self.log_text.append(f"❌ 検索設定保存エラー: {str(e)}")

    def load_search_settings(self):
        """JSONファイルから検索設定を読み込み"""
        try:
            import json
            import os
            
            if not os.path.exists(self.search_config_file):
                self.log_text.append("ℹ️ 検索設定ファイルが見つかりません。デフォルト設定を使用します。")
                return
            
            with open(self.search_config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 検索設定の復元
            if "dense_topk" in settings:
                self.search_topk.setValue(settings["dense_topk"])
            if "final_k" in settings:
                self.search_finalk.setValue(settings["final_k"])
            if "threshold" in settings:
                self.search_threshold.setValue(settings["threshold"])
            if "use_reranker" in settings:
                self.search_use_reranker.setChecked(settings["use_reranker"])
            if "reranker_model" in settings:
                index = self.search_reranker_model.findText(settings["reranker_model"])
                if index >= 0:
                    self.search_reranker_model.setCurrentIndex(index)
            if "mix_alpha" in settings:
                self.search_mix_alpha.setValue(settings["mix_alpha"])
            if "preview_len" in settings:
                self.search_preview_len.setValue(settings["preview_len"])
            if "show_timings" in settings:
                self.search_show_timings.setChecked(settings["show_timings"])
            
            # クエリ最適化
            if "optimize_query" in settings:
                self.chk_optimize_query.setChecked(settings["optimize_query"])
            if "opt_preset" in settings:
                index = self.combo_opt_preset.findText(settings["opt_preset"])
                if index >= 0:
                    self.combo_opt_preset.setCurrentIndex(index)
            
            # 検索対象
            if "search_target" in settings:
                target = settings["search_target"]
                if "ast_packages" in target:
                    self.chk_ast_pkgs.setChecked(target["ast_packages"])
                if "ast_functions" in target:
                    self.chk_ast_funcs.setChecked(target["ast_functions"])
                if "ast_equations" in target:
                    self.chk_ast_eqs.setChecked(target["ast_equations"])
                if "pdf" in target:
                    self.chk_pdf.setChecked(target["pdf"])
            
            self.log_text.append(f"✅ 検索設定を読み込みました: {self.search_config_file}")
            
        except Exception as e:
            self.log_text.append(f"⚠️ 検索設定読み込みエラー: {str(e)}")

