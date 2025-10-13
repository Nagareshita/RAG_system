# ast_only/src/ui/components.py
"""
共通UIコンポーネントの定義（DetailTabsWidget対応拡張版）
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel, QSplitter

# 新しい詳細タブシステムをインポート
try:
    from tabs.modelica_modules.ui.detail_tabs import DetailTabsWidget
    DETAIL_TABS_AVAILABLE = True
except ImportError:
    DetailTabsWidget = None
    DETAIL_TABS_AVAILABLE = False

class DetailViewer(QWidget):
    """詳細表示ウィジェット（従来版・後方互換性維持）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.current_data = None
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        self.title_label = QLabel("詳細情報")
        layout.addWidget(self.title_label)
        
        self.detail_text = QPlainTextEdit()
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.detail_text)
    
    def update_content(self, data: Dict[str, Any]):
        """表示内容を更新（従来のシンプル版）"""
        self.current_data = data
        
        if not data:
            self.detail_text.setPlainText("選択してください")
            return
        
        content_parts = []
        
        # 基本情報
        item_type = data.get("type", "unknown")
        if item_type == "node":
            content_parts.append(f"名前: {data.get('name', '')}")
            content_parts.append(f"パス: {data.get('path', '')}")
            content_parts.append(f"子要素数: {data.get('children_count', 0)}")
            
            # 統計情報
            stats = []
            for key, label in [
                ("component_count", "コンポーネント"),
                ("variable_count", "変数"),
                ("parameter_count", "パラメータ")
            ]:
                count = data.get(key, 0)
                if count > 0:
                    stats.append(f"{label}: {count}")
            
            if stats:
                content_parts.append("統計:")
                content_parts.extend(f"  - {stat}" for stat in stats)
            
            # レコード詳細
            records = data.get("records", [])
            if records:
                content_parts.append(f"\n含まれるレコード ({len(records)} 件):")
                for i, record in enumerate(records[:5]):  # 最初の5件のみ表示
                    kind = record.get("kind", "unknown")
                    name = record.get("name", "")
                    fqn = record.get("fqn", "")
                    content_parts.append(f"  {i+1}. [{kind}] {name}")
                    if fqn and fqn != name:
                        content_parts.append(f"     FQN: {fqn}")
                    
                    # パラメータ情報
                    params = record.get("parameters", [])
                    if params:
                        param_names = [p.get("name", "") for p in params[:3]]
                        content_parts.append(f"     パラメータ: {', '.join(param_names)}")
                
                if len(records) > 5:
                    content_parts.append(f"  ... 他 {len(records) - 5} 件")
        
        self.detail_text.setPlainText("\n".join(content_parts))


class TreeDetailSplitter(QSplitter):
    """ツリーと詳細表示の分割ウィジェット（段階的詳細表示対応版）"""
    
    item_selected = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # 左側: ツリー
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        left_layout.addWidget(QLabel("ライブラリ構造"))
        
        from PySide6.QtWidgets import QTreeView
        self.tree_view = QTreeView()
        self.tree_view.clicked.connect(self._on_tree_clicked)
        left_layout.addWidget(self.tree_view)
        
        # 右側: 詳細表示（段階的タブ対応）
        if DETAIL_TABS_AVAILABLE:
            self.detail_viewer = DetailTabsWidget()
        else:
            self.detail_viewer = DetailViewer()
        
        # 分割に追加
        self.addWidget(left_widget)
        self.addWidget(self.detail_viewer)
        self.setStretchFactor(0, 2)
        self.setStretchFactor(1, 3)  # 詳細表示側を少し広く
    
    def set_model(self, model: QStandardItemModel):
        """ツリーモデルを設定"""
        self.tree_view.setModel(model)
        self.tree_view.expandAll()
    
    def _on_tree_clicked(self, index: QModelIndex):
        """ツリー項目がクリックされた時の処理"""
        if not index.isValid():
            return
        
        item = self.tree_view.model().itemFromIndex(index)
        if item:
            data = item.data(Qt.UserRole)
            
            # 段階的詳細表示の場合は、レコードを直接渡す
            if DETAIL_TABS_AVAILABLE and hasattr(self.detail_viewer, 'update_content'):
                records = data.get("records", []) if data else []
                if records:
                    # 最初のレコードを表示（複数ある場合は将来的にリスト表示を追加）
                    self.detail_viewer.update_content(records[0])
                else:
                    self.detail_viewer.update_content({})
            else:
                # 従来の詳細表示
                self.detail_viewer.update_content(data or {})
            
            self.item_selected.emit(data)

def apply_dark_style(app):
    """ダークテーマを適用"""
    qss = """
    QWidget { 
        background: #1f2327; 
        color: #e6e6e6; 
        font-size: 13px; 
        font-family: 'Segoe UI', 'Yu Gothic UI', sans-serif;
    }
    QToolBar { 
        background: #24292e; 
        spacing: 6px; 
        padding: 6px; 
        border: none;
    }
    QToolBar QToolButton { 
        background: #2a2f34; 
        border: 1px solid #31363b; 
        border-radius: 6px; 
        padding: 6px 10px; 
        margin: 2px;
    }
    QToolBar QToolButton:hover { 
        background: #31363b; 
        border-color: #4a5159;
    }
    QPlainTextEdit, QLineEdit { 
        background: #191d21; 
        border: 1px solid #31363b; 
        border-radius: 8px; 
        padding: 4px;
    }
    QTableView, QTreeView { 
        background: #1b1f23; 
        border: 1px solid #31363b; 
        border-radius: 8px;
        alternate-background-color: #232830;
    }
    QHeaderView::section {
        background: #24292e;
        border: 1px solid #31363b;
        padding: 4px;
    }
    QPushButton { 
        background: #2a2f34; 
        border: 1px solid #31363b; 
        border-radius: 6px; 
        padding: 6px 10px; 
        margin: 2px;
    }
    QPushButton:hover { 
        background: #31363b; 
        border-color: #4a5159;
    }
    QLabel {
        color: #e6e6e6;
        font-weight: 500;
    }
    QSplitter::handle {
        background: #31363b;
        width: 6px;
        border-radius: 3px;
    }
    QTabWidget::pane {
        border: 1px solid #31363b;
        background: #1f2327;
    }
    QTabBar::tab {
        background: #2a2f34;
        border: 1px solid #31363b;
        padding: 8px 12px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #31363b;
        border-bottom: 2px solid #4a9eff;
    }
    QTabBar::tab:hover {
        background: #31363b;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #31363b;
        border-radius: 6px;
        margin: 8px 0px;
        padding-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px 0 4px;
    }
    QScrollArea {
        border: 1px solid #31363b;
        border-radius: 6px;
    }
    QComboBox {
        background: #2a2f34;
        border: 1px solid #31363b;
        border-radius: 6px;
        padding: 6px;
        min-width: 100px;
    }
    QComboBox:hover {
        border-color: #4a5159;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }
    QComboBox QAbstractItemView {
        background: #2a2f34;
        border: 1px solid #31363b;
        selection-background-color: #4a9eff;
    }
    """
    app.setStyleSheet(qss)