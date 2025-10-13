# tabs/user_tab.py
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QSplitter)
from PySide6.QtCore import Qt
from pathlib import Path
from .managers.design_manager import DesignManager
from .managers.workflow_manager import WorkflowManager
from .formatters.result_formatter import ResultFormatter
from .components.prompt_input import PromptInputWidget
from .components.result_display import ResultDisplayWidget
from .components.log_display import LogDisplayWidget

class UserTab(QWidget):
    def __init__(self):
        super().__init__()
        # マネージャーとフォーマッターの初期化
        self.design_manager = DesignManager()
        self.result_formatter = ResultFormatter()
        
        # UIコンポーネントの作成
        self.setup_ui()
        self.connect_signals()
        
        # ワークフロー管理用のマネージャー
        self.workflow_manager = None
    
    def setup_ui(self):
        """UI構築"""
        layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        
        # UIコンポーネントの作成
        self.prompt_widget = PromptInputWidget(self.design_manager)
        self.result_widget = ResultDisplayWidget(self.result_formatter)
        self.log_widget = LogDisplayWidget()
        
        # スプリッターに追加
        splitter.addWidget(self.prompt_widget)
        splitter.addWidget(self.result_widget)
        splitter.addWidget(self.log_widget)
        
        # 初期サイズ比率を設定
        splitter.setSizes([250, 820, 220])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def connect_signals(self):
        """シグナル接続"""
        # プロンプト入力からの送信要求
        self.prompt_widget.send_requested.connect(self.execute_workflow)
        
        # ログ表示用（後で削除される古いメソッドとの互換性）
        self.log_text = self.log_widget.log_text  # 一時的な互換性
    
    def execute_workflow(self, prompt: str, design_data: dict, design_name: str, image_path: str = ""):
        """ワークフロー実行"""
        # UIを無効化
        self.prompt_widget.set_enabled(False)
        
        # ログに記録
        self.log_widget.add_section_header("ワークフロー実行開始")
        self.log_widget.add_log(f"使用設計ファイル: {design_name}")
        self.log_widget.add_log(f"プロンプト: {prompt[:50]}..." if len(prompt) > 50 else f"プロンプト: {prompt}")
        if image_path:
            self.log_widget.add_log(f"画像: {Path(image_path).name}")
        
        # ワークフローマネージャーを作成・実行
        self.workflow_manager = WorkflowManager(design_data, prompt, design_name, image_path)
        self.workflow_manager.log_signal.connect(self.log_widget.add_log_without_timestamp)
        self.workflow_manager.result_signal.connect(self.handle_workflow_result)
        self.workflow_manager.finished.connect(self.on_workflow_finished)
        
        self.workflow_manager.start()
    
    def handle_workflow_result(self, results):
        """ワークフロー実行結果を処理"""
        if not results:
            self.result_widget.display_error("結果が空です。")
            return
        
        if "error" in results:
            self.result_widget.display_error(results["error"])
            return
        
        # 結果をResultFormatterで処理して表示
        self.result_widget.display_results(results)
        self.log_widget.add_log("結果表示完了")
    
    def on_workflow_finished(self):
        """ワークフロー完了後の処理"""
        self.prompt_widget.set_enabled(True)
        self.log_widget.add_section_header("ワークフロー実行完了")
        
    # 下位互換性のためのメソッド（将来削除予定）
    def refresh_design_list(self):
        """設計ファイル一覧を更新（下位互換性用）"""
        self.prompt_widget.refresh_design_list()

    def get_selected_design(self):
        """選択されている設計ファイルを取得（下位互換性用）"""
        return self.prompt_widget.get_selected_design()
    
    # 下位互換性のためのメソッド（将来削除予定）
    def append_realtime_log(self, log_message):
        """リアルタイムログメッセージを表示（下位互換性用）"""
        self.log_widget.add_log_without_timestamp(f">> {log_message}")
        
        # アプリケーションのイベント処理を強制実行（リアルタイム表示のため）
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()