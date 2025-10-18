"""
クエリ最適化 テストGUI（単独アプリ）

目的:
- ユーザークエリから最適化候補（サブクエリ）を生成（VLM使用時は失敗で終了／未使用時はヒューリスティック）
- 検索パラメータ（TopK/FinalK/閾値/再ランカー/対象コレクション）を調整して比較
- 「生クエリ検索」と「最適化クエリ検索」を両方実行して結果を比較する

実行:
  python scripts/query_optimize_gui.py

依存:
- PySide6
- qdrant-client, FlagEmbedding（すでに本プロジェクトで使用）
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict, Any
import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QListWidget, QTextEdit, QSplitter, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt

# リポジトリルートを import パスに追加
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.vector_manager import VectorManager
from scripts.query_optimize_test import generate_queries_with_vlm, heuristic_optimize


class QueryOptimizeGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("クエリ最適化テスト（GUI）")
        self.resize(1100, 720)

        self.vm = VectorManager()
        self._results_by_index: Dict[int, List[Dict[str, Any]]] = {}

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 上段: 入力/パラメータ
        input_group = QGroupBox("最適化・検索パラメータ")
        input_layout = QVBoxLayout()

        # クエリ + フォーカス
        row_q = QHBoxLayout()
        row_q.addWidget(QLabel("ユーザークエリ:"))
        self.edit_query = QLineEdit()
        self.edit_query.setPlaceholderText("例: water tank temperature control")
        self.edit_query.setToolTip("最適化の起点となるユーザークエリ")
        row_q.addWidget(self.edit_query)

        row_q.addWidget(QLabel("フォーカス:"))
        self.combo_focus = QComboBox()
        self.combo_focus.addItems(["functions", "equations", "packages", "pdf"])
        self.combo_focus.setToolTip("主に探したい対象（最適化の指針）")
        row_q.addWidget(self.combo_focus)
        input_layout.addLayout(row_q)

        # VLM/最適化設定
        row_opt = QHBoxLayout()
        self.chk_use_vlm = QCheckBox("VLMを使用（失敗時は終了）")
        self.chk_use_vlm.setChecked(True)
        row_opt.addWidget(self.chk_use_vlm)
        row_opt.addWidget(QLabel("VLMプリセット:"))
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(["qa", "code", "ocr", "balanced", "accurate", "creative", "summary", "json"])
        row_opt.addWidget(self.combo_preset)
        row_opt.addWidget(QLabel("候補数:"))
        self.spin_candidates = QSpinBox()
        self.spin_candidates.setRange(1, 10)
        self.spin_candidates.setValue(3)
        row_opt.addWidget(self.spin_candidates)
        btn_gen = QPushButton("最適化候補を生成")
        btn_gen.clicked.connect(self.on_generate_candidates)
        row_opt.addWidget(btn_gen)
        input_layout.addLayout(row_opt)

        # 検索設定
        row_search = QHBoxLayout()
        row_search.addWidget(QLabel("Dense TopK:"))
        self.spin_topk = QSpinBox()
        self.spin_topk.setRange(1, 200)
        self.spin_topk.setValue(50)
        row_search.addWidget(self.spin_topk)
        row_search.addWidget(QLabel("FinalK:"))
        self.spin_finalk = QSpinBox()
        self.spin_finalk.setRange(1, 100)
        self.spin_finalk.setValue(20)
        row_search.addWidget(self.spin_finalk)
        row_search.addWidget(QLabel("閾値:"))
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.0, 1.0)
        self.spin_threshold.setSingleStep(0.01)
        self.spin_threshold.setValue(0.0)
        row_search.addWidget(self.spin_threshold)
        self.chk_gpu = QCheckBox("GPU使用")
        self.chk_gpu.setChecked(True)
        row_search.addWidget(self.chk_gpu)
        row_search.addWidget(QLabel("再ランカー:"))
        self.combo_reranker = QComboBox()
        self.combo_reranker.addItems(["BAAI/bge-reranker-large", "BAAI/bge-reranker-base", "cross-encoder/ms-marco-MiniLM-L-6-v2", "(なし)"])
        row_search.addWidget(self.combo_reranker)
        input_layout.addLayout(row_search)

        # 対象コレクション
        row_cols = QHBoxLayout()
        row_cols.addWidget(QLabel("対象コレクション:"))
        self.chk_pkgs = QCheckBox("packages")
        self.chk_funcs = QCheckBox("functions")
        self.chk_eqs = QCheckBox("equations")
        self.chk_pdf = QCheckBox("pdf")
        for w in [self.chk_pkgs, self.chk_funcs, self.chk_eqs, self.chk_pdf]:
            row_cols.addWidget(w)
        btn_sel_all = QPushButton("全選択")
        btn_sel_all.clicked.connect(lambda: self._set_all_cols(True))
        btn_clear = QPushButton("全解除")
        btn_clear.clicked.connect(lambda: self._set_all_cols(False))
        row_cols.addWidget(btn_sel_all)
        row_cols.addWidget(btn_clear)
        input_layout.addLayout(row_cols)

        # 実行ボタン
        row_run = QHBoxLayout()
        btn_search_raw = QPushButton("生クエリで検索")
        btn_search_raw.clicked.connect(self.on_search_raw)
        row_run.addWidget(btn_search_raw)
        btn_search_selected = QPushButton("最適化（選択）で検索")
        btn_search_selected.clicked.connect(self.on_search_selected)
        row_run.addWidget(btn_search_selected)
        btn_search_all = QPushButton("最適化（全候補）で検索")
        btn_search_all.clicked.connect(self.on_search_all)
        row_run.addWidget(btn_search_all)
        btn_search_both = QPushButton("両方検索（生＋最適化）")
        btn_search_both.clicked.connect(self.on_search_both)
        row_run.addWidget(btn_search_both)
        input_layout.addLayout(row_run)

        input_group.setLayout(input_layout)

        # 下段: 候補/結果/ログ（スプリッタ）
        splitter = QSplitter(Qt.Horizontal)

        # 候補リスト
        left_box = QGroupBox("最適化クエリ候補")
        left_layout = QVBoxLayout()
        self.list_candidates = QListWidget()
        self.list_candidates.setToolTip("生成されたサブクエリ。選択して検索ボタンで実行")
        left_layout.addWidget(self.list_candidates)
        left_box.setLayout(left_layout)

        # 結果リスト（生/最適化の2列）
        mid_box = QGroupBox("検索結果（比較）")
        mid_layout = QHBoxLayout()
        # 左: 生クエリ
        raw_box = QGroupBox("生クエリ結果")
        raw_v = QVBoxLayout()
        self.list_results_raw = QListWidget()
        raw_v.addWidget(self.list_results_raw)
        raw_box.setLayout(raw_v)
        # 右: 最適化クエリ
        opt_box = QGroupBox("最適化クエリ結果")
        opt_v = QVBoxLayout()
        self.list_results_opt = QListWidget()
        opt_v.addWidget(self.list_results_opt)
        opt_box.setLayout(opt_v)
        mid_layout.addWidget(raw_box)
        mid_layout.addWidget(opt_box)
        mid_box.setLayout(mid_layout)

        # ログ
        right_box = QGroupBox("ログ")
        right_layout = QVBoxLayout()
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        right_layout.addWidget(self.text_log)
        right_box.setLayout(right_layout)

        splitter.addWidget(left_box)
        splitter.addWidget(mid_box)
        splitter.addWidget(right_box)
        splitter.setSizes([300, 450, 350])

        root.addWidget(input_group)
        root.addWidget(splitter)

        input_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def _set_all_cols(self, val: bool):
        self.chk_pkgs.setChecked(val)
        self.chk_funcs.setChecked(val)
        self.chk_eqs.setChecked(val)
        self.chk_pdf.setChecked(val)

    def _collect_collections(self) -> List[str]:
        cols: List[str] = []
        if self.chk_pkgs.isChecked():
            cols.append("rag_documents_ast_packages")
        if self.chk_funcs.isChecked():
            cols.append("rag_documents_ast_functions")
        if self.chk_eqs.isChecked():
            cols.append("rag_documents_ast_equations")
        if self.chk_pdf.isChecked():
            cols.append("rag_documents_pdf")
        return cols

    def log(self, msg: str):
        self.text_log.append(msg)
        QApplication.processEvents()

    # === ハンドラ ===
    def on_generate_candidates(self):
        q = self.edit_query.text().strip()
        if not q:
            self.log("[最適化] クエリが空です")
            return
        focus = self.combo_focus.currentText()
        preset = self.combo_preset.currentText()
        n = self.spin_candidates.value()
        self.list_candidates.clear()
        self._results_by_index.clear()
        self.log(f"[最適化] 生成開始: focus={focus}, preset={preset}, n={n}")
        t0 = time.perf_counter()
        if self.chk_use_vlm.isChecked():
            try:
                queries = self._generate_with_vlm_strict(q, focus, preset, n)
            except Exception as e:
                self.log(f"[最適化] VLMエラー: {e}")
                QMessageBox.critical(self, "VLMエラー", f"VLMが利用できないため終了します\n詳細: {e}")
                QApplication.exit(1)
                return
        else:
            queries = heuristic_optimize(q, focus, n)
        dt = (time.perf_counter() - t0) * 1000
        for s in queries:
            self.list_candidates.addItem(s)
        self.log(f"[最適化] 完了: {len(queries)} 件 ({dt:.1f} ms)")

    def _generate_with_vlm_strict(self, user_query: str, focus: str, preset: str, n: int) -> List[str]:
        """VLM必須（フォールバック禁止）。失敗時は例外を送出し、GUI側で終了する。"""
        try:
            from vlm.model_manager import ModelManager
        except Exception as ie:
            raise RuntimeError("vlm.model_manager をインポートできません") from ie

        # プロンプト作成はテストスクリプト関数を流用
        from scripts.query_optimize_test import build_opt_prompt
        prompt = build_opt_prompt(user_query, focus, n)

        mm = ModelManager()
        ok = mm.setup_model(progress_callback=lambda m: self.log(f"[VLM] {m}"))
        if not ok:
            raise RuntimeError("VLMモデルのセットアップに失敗しました")
        try:
            text = mm.generate_response(prompt, preset=preset)
        finally:
            try:
                mm.cleanup_model()
            except Exception:
                pass

        lines = [ln.strip(" -\t") for ln in text.splitlines() if ln.strip()]
        cleaned = []
        for ln in lines:
            if any(bad in ln.lower() for bad in ["select ", " from ", " where ", "{", "}", ":", ";"]):
                continue
            cleaned.append(ln)
        out = [ln for ln in cleaned if len(ln.split()) >= 2][:max(1, n)]
        if not out:
            raise RuntimeError("VLMから有効な候補が得られませんでした")
        return out

    def _ensure_models(self) -> bool:
        # 埋め込みモデル
        self.vm.use_gpu = self.chk_gpu.isChecked()
        if not self.vm.model:
            self.log("[検索] 埋め込みモデルを初期化中…")
            if not self.vm.initialize_model(self.vm.use_gpu):
                self.log("[検索] 埋め込みモデル初期化に失敗")
                return False
        # 再ランカー
        rer = self.combo_reranker.currentText()
        if rer and rer != "(なし)" and not getattr(self.vm, "reranker_model", None):
            self.log(f"[検索] 再ランカー初期化: {rer}")
            if not self.vm.initialize_reranker(rer):
                self.log("[検索] 再ランカー初期化に失敗。再ランク無しで続行")
        return True

    def _run_search_for_query(self, q: str) -> List[Dict[str, Any]]:
        cols = self._collect_collections()
        if not cols:
            self.log("[検索] 対象コレクションを選択してください")
            return []
        topk = self.spin_topk.value()
        finalk = self.spin_finalk.value()
        thr = float(self.spin_threshold.value())
        self.log(f"[検索] 実行: cols={cols}, topk={topk}, finalk={finalk}, thr={thr}")
        t0 = time.perf_counter()
        hits = self.vm.search_across_collections(
            query=q,
            collections=cols,
            initial_k=topk,
            final_k=finalk,
            similarity_threshold=thr,
            use_reranker=True if getattr(self.vm, "reranker_model", None) else False,
            use_hybrid=False,
            dense_weight=1.0,
            sparse_weight=0.0,
        )
        dt = (time.perf_counter() - t0) * 1000
        self.log(f"[検索] 完了: {len(hits)} 件 ({dt:.1f} ms)")
        return hits

    def on_search_selected(self):
        row = self.list_candidates.currentRow()
        if row < 0:
            self.log("[検索] 候補が選択されていません")
            return
        q = self.list_candidates.currentItem().text()
        if not self._ensure_models():
            return
        hits = self._run_search_for_query(q)
        self._results_by_index[row] = hits
        self._show_results_opt(hits)

    def on_search_all(self):
        count = self.list_candidates.count()
        if count == 0:
            self.log("[検索] 候補がありません")
            return
        if not self._ensure_models():
            return
        agg: List[Dict[str, Any]] = []
        for i in range(count):
            q = self.list_candidates.item(i).text()
            hits = self._run_search_for_query(q)
            self._results_by_index[i] = hits
            agg.extend(hits)
        # 簡易マージ: スコア降順
        agg.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        self._show_results_opt(agg)

    def on_search_raw(self):
        q = self.edit_query.text().strip()
        if not q:
            self.log("[検索] 生クエリが空です")
            return
        if not self._ensure_models():
            return
        hits = self._run_search_for_query(q)
        self._show_results_raw(hits)

    def on_search_both(self):
        # 生クエリ
        q_raw = self.edit_query.text().strip()
        if not q_raw:
            self.log("[検索] 生クエリが空です")
            return
        if not self._ensure_models():
            return
        raw_hits = self._run_search_for_query(q_raw)
        self._show_results_raw(raw_hits)
        # 最適化（選択があれば選択、無ければ全候補）
        row = self.list_candidates.currentRow()
        if row >= 0:
            q_opt = self.list_candidates.currentItem().text()
            opt_hits = self._run_search_for_query(q_opt)
        else:
            # 全候補をまとめて
            agg: List[Dict[str, Any]] = []
            for i in range(self.list_candidates.count()):
                q_opt_i = self.list_candidates.item(i).text()
                agg.extend(self._run_search_for_query(q_opt_i))
            # スコア降順で表示
            agg.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            opt_hits = agg
        self._show_results_opt(opt_hits)

    def _show_results_raw(self, hits: List[Dict[str, Any]]):
        self.list_results_raw.clear()
        for r in hits:
            col = r.get("collection", "")
            score = r.get("score", 0.0)
            text = r.get("text", "")
            preview = (text[:160] + "…") if isinstance(text, str) and len(text) > 160 else text
            self.list_results_raw.addItem(f"[{col}] {score:.3f}\t{preview}")

    def _show_results_opt(self, hits: List[Dict[str, Any]]):
        self.list_results_opt.clear()
        for r in hits:
            col = r.get("collection", "")
            score = r.get("score", 0.0)
            text = r.get("text", "")
            preview = (text[:160] + "…") if isinstance(text, str) and len(text) > 160 else text
            self.list_results_opt.addItem(f"[{col}] {score:.3f}\t{preview}")


def main():
    app = QApplication(sys.argv)
    w = QueryOptimizeGUI()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
