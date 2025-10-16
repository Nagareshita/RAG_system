# src/apps/pymupdf_converter/ui/control_panel.py
"""Control panel UI (flattened package)."""
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFormLayout, QSpinBox, QCheckBox, QProgressBar, QFileDialog,
    QLineEdit, QComboBox, QScrollArea, QWidget
)
from PySide6.QtCore import Signal
from pathlib import Path
import json

class ControlPanel(QGroupBox):
    """コントロールパネル"""
    
    file_selected = Signal(str)
    processing_requested = Signal(dict)
    
    def __init__(self):
        super().__init__("処理設定")
        self.pdf_path = ""
        self.schema = None
        self.pymupdf_controls = {}
        self.rag_controls = {}
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 設定スキーマ読込
        self._load_settings_schema()

        # スクロール可能な設定領域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(4, 4, 4, 4)
        config_layout.setSpacing(8)

        # ファイル選択
        file_group = self._create_file_group()
        config_layout.addWidget(file_group)

        # チャンク設定
        chunk_group = self._create_chunk_group()
        config_layout.addWidget(chunk_group)

        # PyMuPDF4LLM 詳細設定
        pymupdf_group = self._create_pymupdf_group()
        config_layout.addWidget(pymupdf_group)

        # RAG メタデータ設定
        rag_group = self._create_rag_group()
        config_layout.addWidget(rag_group)

        config_layout.addStretch(1)
        scroll.setWidget(config_widget)
        layout.addWidget(scroll, 1)
        
        # 実行ボタン（コンパクト・左寄せ）
        self.process_btn = QPushButton("変換実行")
        self.process_btn.setEnabled(False)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.process_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        
        # プログレス
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("待機中...")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        # 下部に余白
        layout.addStretch(0)
    
    def _create_file_group(self):
        """ファイル選択グループ"""
        group = QGroupBox("ファイル選択")
        layout = QVBoxLayout(group)
        
        self.select_file_btn = QPushButton("PDFファイルを選択")
        self.file_label = QLabel("ファイル: 未選択")
        
        row = QHBoxLayout()
        row.addWidget(self.select_file_btn)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addWidget(self.file_label)
        
        return group
    
    def _load_settings_schema(self):
        """設定スキーマをJSONから読み込み"""
        try:
            # リポジトリルートのJSONを探す
            repo_root = Path(__file__).resolve().parent.parent
            schema_path = repo_root / "pdf_converter_setting.json"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.schema = json.load(f)
            else:
                self.schema = None
        except Exception:
            self.schema = None

    def _get_schema_defaults(self, group_key: str, defaults: dict) -> dict:
        """スキーマからデフォルト値を抽出し、fallbackとマージ"""
        out = dict(defaults)
        if not self.schema:
            return out
        items = self.schema.get(group_key, [])
        for item in items:
            out[item.get("key")] = item.get("default")
        return out

    def _create_chunk_group(self):
        """チャンク設定"""
        group = QGroupBox("チャンク設定")
        layout = QFormLayout(group)

        defaults = self._get_schema_defaults(
            "chunking", {"max_chunk_size": 1000, "overlap_size": 100}
        )

        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 10000)
        self.chunk_size_spin.setValue(int(defaults.get("max_chunk_size", 1000)))
        self.chunk_size_spin.setSuffix(" 文字")

        self.overlap_size_spin = QSpinBox()
        self.overlap_size_spin.setRange(0, 2000)
        self.overlap_size_spin.setValue(int(defaults.get("overlap_size", 100)))
        self.overlap_size_spin.setSuffix(" 文字")

        layout.addRow("最大チャンクサイズ:", self.chunk_size_spin)
        layout.addRow("オーバーラップサイズ:", self.overlap_size_spin)

        return group

    def _create_pymupdf_group(self):
        """PyMuPDF4LLM 詳細設定（JSONスキーマ反映）"""
        group = QGroupBox("PyMuPDF4LLM 詳細")
        layout = QFormLayout(group)

        if not self.schema:
            layout.addRow(QLabel("設定スキーマが見つかりませんでした (pdf_converter_setting.json)"))
            return group

        def add_help(lbl: str):
            help_label = QLabel(lbl)
            help_label.setStyleSheet("color: #666;")
            return help_label

        for item in self.schema.get("pymupdf4llm_params", []):
            key = item.get("key")
            label = item.get("label", key)
            ui = item.get("ui")
            default = item.get("default")
            options = item.get("options", [])
            help_text = item.get("help")

            widget = None
            if ui == "checkbox":
                w = QCheckBox()
                w.setChecked(bool(default))
                widget = w
            elif ui == "spin":
                w = QSpinBox()
                w.setRange(int(item.get("min", 0)), int(item.get("max", 100000)))
                w.setSingleStep(int(item.get("step", 1)))
                w.setValue(int(default) if default is not None else 0)
                widget = w
            elif ui == "dropdown":
                w = QComboBox()
                for opt in options:
                    w.addItem(str(opt))
                if default is not None and str(default) in [str(o) for o in options]:
                    w.setCurrentText(str(default))
                widget = w
            elif ui in ("textbox", "folder"):
                w = QLineEdit()
                if default is not None:
                    w.setText(str(default))
                widget = w
            else:
                # fallback
                w = QLineEdit()
                if default is not None:
                    w.setText(str(default))
                widget = w

            self.pymupdf_controls[key] = widget
            layout.addRow(label + ":", widget)
            if help_text:
                layout.addRow("", add_help(help_text))

        # 相互排他: write_images / embed_images
        def on_write_images_changed(state: bool):
            w_write = self.pymupdf_controls.get("write_images")
            w_embed = self.pymupdf_controls.get("embed_images")
            if isinstance(w_write, QCheckBox) and isinstance(w_embed, QCheckBox):
                if w_write.isChecked():
                    w_embed.setChecked(False)
            self._update_enable_if()

        def on_embed_images_changed(state: bool):
            w_write = self.pymupdf_controls.get("write_images")
            w_embed = self.pymupdf_controls.get("embed_images")
            if isinstance(w_write, QCheckBox) and isinstance(w_embed, QCheckBox):
                if w_embed.isChecked():
                    w_write.setChecked(False)
            self._update_enable_if()

        w_write = self.pymupdf_controls.get("write_images")
        w_embed = self.pymupdf_controls.get("embed_images")
        if isinstance(w_write, QCheckBox):
            w_write.stateChanged.connect(lambda _: on_write_images_changed(True))
        if isinstance(w_embed, QCheckBox):
            w_embed.stateChanged.connect(lambda _: on_embed_images_changed(True))

        # 依存関係のため、全チェックボックスの変更で有効/無効を見直す
        for w in self.pymupdf_controls.values():
            if isinstance(w, QCheckBox):
                w.stateChanged.connect(lambda _: self._update_enable_if())

        # 初期の有効/無効制御
        self._update_enable_if()
        return group

    def _update_enable_if(self):
        """enable_if 条件に基づきUIを有効/無効化"""
        if not self.schema:
            return
        cond_map = {i.get("key"): i.get("enable_if") for i in self.schema.get("pymupdf4llm_params", []) if i.get("enable_if")}
        state = {}
        # 依存元の現在値を収集
        for key, widget in self.pymupdf_controls.items():
            if isinstance(widget, QCheckBox):
                state[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                state[key] = widget.value()
            elif isinstance(widget, QComboBox):
                state[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                state[key] = widget.text()
        # enable_if の評価
        for key, enable_if in cond_map.items():
            target = self.pymupdf_controls.get(key)
            if target is None:
                continue
            enabled = True
            for dep_key, dep_val in enable_if.items():
                if state.get(dep_key) != dep_val:
                    enabled = False
                    break
            if hasattr(target, 'setEnabled'):
                target.setEnabled(enabled)

    def _create_rag_group(self):
        """RAG メタデータ設定"""
        group = QGroupBox("RAG メタデータ")
        layout = QFormLayout(group)

        if not self.schema:
            layout.addRow(QLabel("設定スキーマが見つかりませんでした"))
            return group

        for item in self.schema.get("rag_metadata", []):
            key = item.get("key")
            label = item.get("label", key)
            default = bool(item.get("default", False))
            w = QCheckBox()
            w.setChecked(default)
            self.rag_controls[key] = w
            layout.addRow(label + ":", w)

        return group
    
    def _connect_signals(self):
        """シグナル接続"""
        self.select_file_btn.clicked.connect(self._select_file)
        self.process_btn.clicked.connect(self._request_processing)
    
    def _select_file(self):
        """ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "PDFファイルを選択", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.pdf_path = file_path
            self.file_label.setText(f"ファイル: {Path(file_path).name}")
            self.process_btn.setEnabled(True)
            self.file_selected.emit(file_path)
    
    def _request_processing(self):
        """処理要求"""
        settings = {
            'pdf_path': self.pdf_path,
            'chunk_size': self.chunk_size_spin.value(),
            'overlap_size': self.overlap_size_spin.value(),
            'pymupdf_kwargs': self._collect_pymupdf_kwargs(),
            'rag_settings': self._collect_rag_settings(),
        }
        self.processing_requested.emit(settings)

    def _collect_pymupdf_kwargs(self) -> dict:
        """UIの値からPyMuPDF4LLMに渡すkwargsを作成"""
        kwargs = {}
        for key, widget in self.pymupdf_controls.items():
            if isinstance(widget, QCheckBox):
                kwargs[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                kwargs[key] = int(widget.value())
            elif isinstance(widget, QComboBox):
                kwargs[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                val = widget.text().strip()
                if key == "margins":
                    # 文字列を to_markdown 互換の float / タプル[float] に変換
                    if val == "":
                        # 空は未設定として渡さない
                        continue
                    parts = [p.strip() for p in val.split(',') if p.strip() != '']
                    try:
                        if len(parts) == 1:
                            kwargs[key] = float(parts[0])
                        elif len(parts) in (2, 4):
                            nums = tuple(float(x) for x in parts)
                            kwargs[key] = nums
                        else:
                            print(f"警告: marginsの値を無視しました（1,2,4個のみ許可）: '{val}'")
                    except ValueError:
                        print(f"警告: marginsの数値変換に失敗しました: '{val}'。この設定は無視されます。")
                else:
                    kwargs[key] = val
        # 相互排他の最終調整
        if kwargs.get("write_images") and kwargs.get("embed_images"):
            kwargs["embed_images"] = False
        # extract_wordsの場合、page_chunksを強制有効に（スキーマ説明に基づく）
        if kwargs.get("extract_words"):
            kwargs["page_chunks"] = True
        return kwargs

    def _collect_rag_settings(self) -> dict:
        out = {}
        for key, widget in self.rag_controls.items():
            if isinstance(widget, QCheckBox):
                out[key] = widget.isChecked()
        return out
    
    def set_processing_state(self, processing: bool):
        """処理状態設定"""
        self.process_btn.setEnabled(not processing)
        self.progress_bar.setVisible(processing)
        if processing:
            self.progress_bar.setRange(0, 0)
    
    def update_status(self, message: str):
        """ステータス更新"""
        self.status_label.setText(message)
