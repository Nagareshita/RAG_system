# src/apps/pymupdf_converter/ui/control_panel.py
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFormLayout, QSpinBox, QCheckBox, QProgressBar, QFileDialog
)
from PySide6.QtCore import Signal
from pathlib import Path

class ControlPanel(QGroupBox):
    """コントロールパネル"""
    
    file_selected = Signal(str)
    processing_requested = Signal(dict)
    
    def __init__(self):
        super().__init__("処理設定")
        self.pdf_path = ""
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # ファイル選択
        file_group = self._create_file_group()
        layout.addWidget(file_group)
        
        # 処理設定
        settings_group = self._create_settings_group()
        layout.addWidget(settings_group)
        
        # 実行ボタン
        self.process_btn = QPushButton("変換実行")
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # プログレス
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("待機中...")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _create_file_group(self):
        """ファイル選択グループ"""
        group = QGroupBox("ファイル選択")
        layout = QVBoxLayout(group)
        
        self.select_file_btn = QPushButton("PDFファイルを選択")
        self.file_label = QLabel("ファイル: 未選択")
        
        layout.addWidget(self.select_file_btn)
        layout.addWidget(self.file_label)
        
        return group
    
    def _create_settings_group(self):
        """設定グループ"""
        group = QGroupBox("チャンク設定")
        layout = QFormLayout(group)
        
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 5000)
        self.chunk_size_spin.setValue(1000)
        self.chunk_size_spin.setSuffix(" 文字")
        
        self.overlap_size_spin = QSpinBox()
        self.overlap_size_spin.setRange(0, 500)
        self.overlap_size_spin.setValue(100)
        self.overlap_size_spin.setSuffix(" 文字")
        
        self.include_formulas_check = QCheckBox("数式の詳細解析")
        self.include_formulas_check.setChecked(True)
        
        layout.addRow("最大チャンクサイズ:", self.chunk_size_spin)
        layout.addRow("オーバーラップサイズ:", self.overlap_size_spin)
        layout.addRow("", self.include_formulas_check)
        
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
            'include_formulas': self.include_formulas_check.isChecked()
        }
        self.processing_requested.emit(settings)
    
    def set_processing_state(self, processing: bool):
        """処理状態設定"""
        self.process_btn.setEnabled(not processing)
        self.progress_bar.setVisible(processing)
        if processing:
            self.progress_bar.setRange(0, 0)
    
    def update_status(self, message: str):
        """ステータス更新"""
        self.status_label.setText(message)