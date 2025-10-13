# tabs/components/log_display.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QSizePolicy
from PySide6.QtCore import QTimer
from datetime import datetime


class LogDisplayWidget(QWidget):
    """ログ表示UI部品"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # ラベル
        layout.addWidget(QLabel("リアルタイムログ:"))
        
        # ログテキストエリア
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumWidth(200)
        
        # サイズポリシーを可変に設定
        sp = self.log_text.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Expanding)
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        self.log_text.setSizePolicy(sp)
        
        layout.addWidget(self.log_text)
        self.setLayout(layout)
        
        # ログの自動スクロール用タイマー
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._scroll_to_bottom)
        self.scroll_timer.setSingleShot(True)
    
    def add_log(self, message: str, timestamp: bool = True):
        """ログメッセージを追加"""
        if timestamp:
            current_time = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{current_time}] {message}"
        else:
            formatted_message = message
        
        self.log_text.append(formatted_message)
        
        # 少し遅延してスクロール（レンダリング完了を待つ）
        self.scroll_timer.start(100)
    
    def add_log_without_timestamp(self, message: str):
        """タイムスタンプなしでログを追加"""
        self.add_log(message, timestamp=False)
    
    def _scroll_to_bottom(self):
        """ログを最下部にスクロール"""
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear(self):
        """ログをクリア"""
        self.log_text.clear()
    
    def add_separator(self):
        """区切り線を追加"""
        self.add_log("=" * 50, timestamp=False)
    
    def add_section_header(self, title: str):
        """セクションヘッダーを追加"""
        self.add_log(f"=== {title} ===", timestamp=False)
    
    def get_log_content(self) -> str:
        """現在のログ内容を取得"""
        return self.log_text.toPlainText()
    
    def save_log(self, filepath: str):
        """ログをファイルに保存"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_log_content())
            self.add_log(f"ログを保存しました: {filepath}")
        except Exception as e:
            self.add_log(f"ログ保存エラー: {e}")