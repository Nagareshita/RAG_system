# main.py
import sys
from pathlib import Path

# Add modelica_analyzer to sys.path for all modules
modelica_analyzer_path = Path(__file__).parent / "modelica_analyzer"
if str(modelica_analyzer_path) not in sys.path:
    sys.path.insert(0, str(modelica_analyzer_path))
    print(f"✓ Added to sys.path: {modelica_analyzer_path}")

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from tabs.login_tab import LoginTab
from tabs.vectorization_tab import VectorizationTab
from tabs.agent_design_tab import AgentDesignTab
from tabs.user_tab import UserTab
from tabs.pdf_parser_tab import PDFParserTab
# 新しいModelica Analyzerタブ（ast_jsonl_validator統合版）
try:
    from tabs.modelica_analyzer_tab import ModelicaAnalyzerTab
    MODELICA_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Modelica Analyzerタブの読み込みに失敗: {e}")
    MODELICA_ANALYZER_AVAILABLE = False
    ModelicaAnalyzerTab = None


class MultiAgentRAGSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Agent RAG System")
        self.setGeometry(100, 100, 1200, 800)
        
        # メインタブウィジェット
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 各タブを追加
        self.login_tab = LoginTab()
        self.vectorization_tab = VectorizationTab()
        self.agent_design_tab = AgentDesignTab()
        self.user_tab = UserTab()
        self.pdf_parser_tab = PDFParserTab()
        
        self.tab_widget.addTab(self.login_tab, "ログイン設定")
        self.tab_widget.addTab(self.pdf_parser_tab, "PDF解析")        
        # Modelica Analyzerタブ（利用可能な場合のみ）
        if MODELICA_ANALYZER_AVAILABLE and ModelicaAnalyzerTab:
            self.modelica_analyzer_tab = ModelicaAnalyzerTab()
            self.tab_widget.addTab(self.modelica_analyzer_tab, "Modelicaライブラリ解析")
        self.tab_widget.addTab(self.vectorization_tab, "ベクトル化")
        self.tab_widget.addTab(self.agent_design_tab, "マルチエージェント設計")
        self.tab_widget.addTab(self.user_tab, "エージェント実行")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiAgentRAGSystem()
    window.show()
    sys.exit(app.exec())