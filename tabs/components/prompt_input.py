# tabs/components/prompt_input.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QPushButton, QTextEdit, QSizePolicy,
                               QFrame, QFileDialog)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from typing import Dict, Any, List, Optional
from pathlib import Path


class ImageDropWidget(QFrame):
    """画像ドラッグ&ドロップエリア"""
    image_selected = Signal(str)  # 画像パスを通知
    
    def __init__(self):
        super().__init__()
        self.image_path: Optional[str] = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        
        layout = QVBoxLayout()
        self.label = QLabel("🖼️ 画像をドラッグ&ドロップ\nまたはクリックして選択")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: gray;")
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.setStyleSheet("ImageDropWidget { background-color: #f5f5f5; border: 2px dashed #ccc; }")
        
    def mousePressEvent(self, event):
        """クリックでファイルダイアログを開く"""
        if event.button() == Qt.LeftButton:
            self.select_image_file()
    
    def select_image_file(self):
        """ファイルダイアログで画像を選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "画像ファイルを選択",
            "",
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif);;すべてのファイル (*)"
        )
        
        if file_path:
            self.set_image_path(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """ドラッグ開始時の処理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """ドロップ時の処理"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # 画像ファイルかチェック
            valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            if any(file_path.lower().endswith(ext) for ext in valid_extensions):
                self.set_image_path(file_path)
                event.acceptProposedAction()
            else:
                print(f"サポートされていないファイル形式: {file_path}")
                event.ignore()
        else:
            event.ignore()
    
    def set_image_path(self, path: str):
        """画像パスを設定"""
        self.image_path = path
        file_name = Path(path).name
        self.label.setText(f"✅ {file_name}")
        self.label.setStyleSheet("color: green;")
        self.setStyleSheet("ImageDropWidget { background-color: #e8f5e9; border: 2px solid #4caf50; }")
        self.image_selected.emit(path)
    
    def clear_image(self):
        """画像選択をクリア"""
        self.image_path = None
        self.label.setText("🖼️ 画像をドラッグ&ドロップ\nまたはクリックして選択")
        self.label.setStyleSheet("color: gray;")
        self.setStyleSheet("ImageDropWidget { background-color: #f5f5f5; border: 2px dashed #ccc; }")
    
    def get_image_path(self) -> Optional[str]:
        """現在の画像パスを取得"""
        return self.image_path


class PromptInputWidget(QWidget):
    """プロンプト入力UI部品"""
    send_requested = Signal(str, dict, str, str)  # prompt, design_data, design_name, image_path
    refresh_requested = Signal()
    
    def __init__(self, design_manager):
        super().__init__()
        self.design_manager = design_manager
        self.setup_ui()
        self.refresh_design_list()
    
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 設計選択部分
        design_selection_layout = QHBoxLayout()
        design_selection_layout.addWidget(QLabel("使用する設計:"))
        
        self.design_combo = QComboBox()
        self.design_combo.setMinimumWidth(200)
        
        self.refresh_designs_button = QPushButton("更新")
        self.refresh_designs_button.clicked.connect(self.refresh_design_list)
        
        design_selection_layout.addWidget(self.design_combo)
        design_selection_layout.addWidget(self.refresh_designs_button)
        layout.addLayout(design_selection_layout)

        # 画像ドラッグ&ドロップエリア
        layout.addWidget(QLabel("画像入力 (オプション):"))
        self.image_drop_widget = ImageDropWidget()
        self.image_drop_widget.image_selected.connect(self.on_image_selected)
        layout.addWidget(self.image_drop_widget)
        
        # クリアボタン
        clear_image_layout = QHBoxLayout()
        self.clear_image_button = QPushButton("画像をクリア")
        self.clear_image_button.clicked.connect(self.on_clear_image_clicked)
        self.clear_image_button.setEnabled(False)
        clear_image_layout.addStretch()
        clear_image_layout.addWidget(self.clear_image_button)
        layout.addLayout(clear_image_layout)

        # プロンプト入力部分
        layout.addWidget(QLabel("プロンプト入力:"))
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setMinimumWidth(250)
        
        # サイズポリシーを可変に設定
        sp = self.prompt_input.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Expanding)
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        self.prompt_input.setSizePolicy(sp)
        layout.addWidget(self.prompt_input, stretch=1)

        # 送信ボタン
        self.send_button = QPushButton("送信")
        self.send_button.clicked.connect(self.on_send_clicked)
        layout.addWidget(self.send_button)
        
        self.setLayout(layout)
    
    def refresh_design_list(self):
        """設計ファイル一覧を更新"""
        try:
            self.design_combo.clear()
            
            json_files = self.design_manager.get_design_files()
            
            if not json_files:
                self.design_combo.addItem("設計ファイルがありません")
                return
            
            for filename in json_files:
                self.design_combo.addItem(filename)
            
            self.refresh_requested.emit()
            
        except Exception as e:
            print(f"設計一覧の更新エラー: {e}")
            self.design_combo.clear()
            self.design_combo.addItem("設計ファイルがありません")
    
    def get_selected_design(self) -> Dict[str, Any]:
        """選択された設計ファイルを取得"""
        selected_design_name = self.design_combo.currentText()
        
        if not selected_design_name or selected_design_name == "設計ファイルがありません":
            return None
        
        design_data = self.design_manager.load_design(selected_design_name)
        
        if not design_data:
            print(f"設計ファイル読み込みエラー: {selected_design_name}")
            return None
        
        if not self.design_manager.validate_design(design_data):
            print(f"設計ファイル形式エラー: {selected_design_name}")
            return None
        
        return design_data
    
    def on_image_selected(self, image_path: str):
        """画像選択時の処理"""
        print(f"画像が選択されました: {image_path}")
        self.clear_image_button.setEnabled(True)
    
    def on_clear_image_clicked(self):
        """画像クリアボタンクリック時の処理"""
        self.image_drop_widget.clear_image()
        self.clear_image_button.setEnabled(False)
        print("画像がクリアされました")
    
    def on_send_clicked(self):
        """送信ボタンクリック時の処理"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            print("プロンプトを入力してください。")
            return
        
        design_data = self.get_selected_design()
        if not design_data:
            print("エラー: 有効な設計ファイルが選択されていません")
            return
        
        design_name = self.design_combo.currentText()
        image_path = self.image_drop_widget.get_image_path() or ""
        
        self.send_requested.emit(prompt, design_data, design_name, image_path)
    
    def set_enabled(self, enabled: bool):
        """UI有効/無効の切り替え"""
        self.send_button.setEnabled(enabled)
        self.prompt_input.setEnabled(enabled)
        self.design_combo.setEnabled(enabled)
        self.refresh_designs_button.setEnabled(enabled)
        self.image_drop_widget.setEnabled(enabled)
        if enabled and self.image_drop_widget.get_image_path():
            self.clear_image_button.setEnabled(True)
        else:
            self.clear_image_button.setEnabled(False)
    
    def clear_prompt(self):
        """プロンプト入力をクリア"""
        self.prompt_input.clear()
    
    def get_prompt_text(self) -> str:
        """現在のプロンプトテキストを取得"""
        return self.prompt_input.toPlainText().strip()
    
    def set_prompt_text(self, text: str):
        """プロンプトテキストを設定"""
        self.prompt_input.setPlainText(text)