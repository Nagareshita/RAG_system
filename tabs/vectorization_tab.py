# tabs/vectorization_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QPushButton, QFileDialog, QTextEdit, QProgressBar,
                               QLabel, QListWidget, QComboBox, QSpinBox, QCheckBox)
from utils.vector_manager import VectorManager
import os

class VectorizationTab(QWidget):
    def __init__(self):
        super().__init__()
        # シングルトンインスタンスを取得
        self.vector_manager = VectorManager()
        self.selected_files = []
        self.setup_ui()
        # 初期値で自動計算実行
        self.update_encode_batch()
    
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
        
        file_group.setLayout(file_layout)
        
        # ベクトル化設定
        vector_group = QGroupBox("ベクトル化設定")
        vector_layout = QVBoxLayout()
        
        # モデル情報
        self.model_label = QLabel("モデル: BAAI/bge-m3")
        vector_layout.addWidget(self.model_label)
        
        # コレクション選択設定（分離をデフォルトに）
        from PySide6.QtWidgets import QSpinBox, QCheckBox, QComboBox
        collection_layout = QHBoxLayout()
        collection_layout.addWidget(QLabel("保存方式:"))
        self.collection_combo = QComboBox()
        self.collection_combo.addItems(["分離", "混合"])
        collection_layout.addWidget(self.collection_combo)
        vector_layout.addLayout(collection_layout)
        
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
        
        # ログ
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        layout.addWidget(file_group)
        layout.addWidget(vector_group)
        layout.addWidget(log_group)
        
        self.setLayout(layout)

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

            # コレクションタイプ判定（シンプル化）
            collection_choice = self.collection_combo.currentText()
            # 直接UIの選択値を渡す
            
            self.vector_manager.use_gpu = self.gpu_checkbox.isChecked()

            success = self.vector_manager.vectorize_documents(
                file_structures, 
                progress_callback=update_progress,
                log_callback=update_log,
                batch_size=batch_size,
                encode_batch_size=encode_batch_size,  # 実際に使用されるように修正済み
                max_text_length=max_text_length,
                collection_type=collection_choice
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