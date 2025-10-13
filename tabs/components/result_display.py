# tabs/components/result_display.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from typing import Dict, Any


class ResultDisplayWidget(QWidget):
    """結果表示UI部品"""
    
    def __init__(self, result_formatter):
        super().__init__()
        self.result_formatter = result_formatter
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ラベル
        layout.addWidget(QLabel("マルチエージェント回答："))
        
        # WebEngineView
        self.output_view = QWebEngineView()
        
        # WebEngineの設定（ローカルファイルとリモートURLへのアクセスを許可）
        settings = self.output_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        layout.addWidget(self.output_view, stretch=1)
        self.setLayout(layout)
    
    def display_results(self, results: Dict[str, Any]):
        """結果を表示"""
        try:
            from pathlib import Path
            from PySide6.QtCore import QUrl
            
            # 結果のフォーマット
            formatted_content = self.result_formatter.format_refined_result(results)
            
            # HTMLに変換（data/debug_output.htmlに保存される）
            html_content = self.result_formatter.set_output_html(formatted_content)
            
            # debug_output.htmlをsetUrl()で読み込む（相対パス参照を正しく解決）
            debug_html_path = Path("data") / "debug_output.html"
            if debug_html_path.exists():
                file_url = debug_html_path.resolve().as_uri()
                self.output_view.setUrl(QUrl(file_url))
            else:
                # ファイルが存在しない場合はsetHtmlで表示
                self.output_view.setHtml(html_content)
            
        except Exception as e:
            error_html = f"<p>表示エラー: {e}</p><pre>{str(results)}</pre>"
            self.output_view.setHtml(error_html)
    
    def display_text(self, text: str):
        """テキストを直接表示"""
        try:
            from pathlib import Path
            from PySide6.QtCore import QUrl
            
            # HTMLに変換（data/debug_output.htmlに保存される）
            html_content = self.result_formatter.set_output_html(text)
            
            # debug_output.htmlをsetUrl()で読み込む（相対パス参照を正しく解決）
            debug_html_path = Path("data") / "debug_output.html"
            if debug_html_path.exists():
                file_url = debug_html_path.resolve().as_uri()
                self.output_view.setUrl(QUrl(file_url))
            else:
                # ファイルが存在しない場合はsetHtmlで表示
                self.output_view.setHtml(html_content)
        except Exception as e:
            error_html = f"<p>表示エラー: {e}</p><pre>{text}</pre>"
            self.output_view.setHtml(error_html)
    
    def display_error(self, error_message: str):
        """エラーメッセージを表示"""
        error_html = f"<p style='color: red;'>エラー: {error_message}</p>"
        self.output_view.setHtml(error_html)
    
    def clear(self):
        """表示内容をクリア"""
        self.output_view.setHtml("<p>結果が表示されます...</p>")