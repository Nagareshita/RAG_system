# tabs/agent_design_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTextEdit, QLabel, QComboBox, QFileDialog)
import subprocess
import sys

class AgentDesignTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Dear PyGUI起動
        launch_layout = QHBoxLayout()
        self.launch_button = QPushButton("エージェント設計ツール起動")
        self.launch_button.clicked.connect(self.launch_designer)
        launch_layout.addWidget(self.launch_button)
        launch_layout.addStretch()
        
        layout.addLayout(launch_layout)
        
        # 設計ファイル選択
        design_layout = QHBoxLayout()
        self.refresh_button = QPushButton("設計一覧更新")
        self.design_combo = QComboBox()
        self.design_combo.setMinimumWidth(300)
        self.design_combo.currentTextChanged.connect(self.on_design_selected)
        self.refresh_button.clicked.connect(self.refresh_design_list)
        
        design_layout.addWidget(QLabel("選択中の設計:"))
        design_layout.addWidget(self.design_combo)
        design_layout.addWidget(self.refresh_button)
        design_layout.addStretch()
        
        layout.addLayout(design_layout)
        
        # 設計プレビュー
        preview_label = QLabel("設計プレビュー:")
        self.design_preview = QTextEdit()
        self.design_preview.setReadOnly(True)
        self.design_preview.setMaximumHeight(400)
        
        layout.addWidget(preview_label)
        layout.addWidget(self.design_preview)
        
        # 初期化
        self.refresh_design_list()
        
        self.setLayout(layout)

    def refresh_design_list(self):
        """設計ファイル一覧を更新"""
        import os
        
        self.design_combo.clear()
        
        designs_dir = os.path.join("configs", "designs")
        
        if not os.path.exists(designs_dir):
            self.design_combo.addItem("設計ファイルがありません")
            self.design_preview.setPlainText("configs/designs/ フォルダが存在しません。")
            return
        
        json_files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]
        
        if not json_files:
            self.design_combo.addItem("設計ファイルがありません")
            self.design_preview.setPlainText("設計ファイルが見つかりません。Dear PyGUIツールで設計を作成してください。")
            return
        
        # ファイル一覧をコンボボックスに追加
        for file in sorted(json_files):
            self.design_combo.addItem(file)
        
        self.design_preview.append("設計ファイル一覧を更新しました")

    def on_design_selected(self, filename):
        """設計ファイルが選択された時の処理"""
        if not filename or filename == "設計ファイルがありません":
            return
        
        self.load_and_preview_design(filename)

    def load_and_preview_design(self, filename):
        """選択された設計ファイルを読み込んでプレビュー表示"""
        import os
        import json
        
        designs_dir = os.path.join("configs", "designs")
        file_path = os.path.join(designs_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                design_data = json.load(f)
            
            # プレビュー内容を生成
            preview_text = self.generate_preview_text(design_data, filename)
            self.design_preview.setPlainText(preview_text)
            
        except Exception as e:
            self.design_preview.setPlainText(f"設計ファイル読み込みエラー: {str(e)}")

    def generate_preview_text(self, design_data, filename):
        """設計データからプレビューテキストを生成"""
        nodes = design_data.get('nodes', [])
        connections = design_data.get('connections', [])
        metadata = design_data.get('metadata', {})
        
        preview = f"設計ファイル: {filename}\n"
        preview += "=" * 50 + "\n\n"
        
        # メタデータ情報
        if metadata:
            preview += "【設計情報】\n"
            preview += f"作成日時: {metadata.get('created_at', '不明')}\n"
            preview += f"ノード数: {metadata.get('node_count', len(nodes))}\n"
            preview += f"接続数: {metadata.get('connection_count', len(connections))}\n\n"
        
        # ノード情報
        preview += "【エージェント構成】\n"
        for i, node in enumerate(nodes):
            node_type = node.get('type', 'unknown')
            node_id = node.get('id', i)
            preview += f"{i+1}. {node_type} (ID:{node_id})\n"
        
        preview += "\n"
        
        # 接続情報
        if connections:
            preview += "【データフロー】\n"
            for i, conn in enumerate(connections):
                from_id = conn.get('from', '?')
                to_id = conn.get('to', '?')
                
                # ノードIDからタイプを取得
                from_type = next((n['type'] for n in nodes if n['id'] == from_id), f"ID:{from_id}")
                to_type = next((n['type'] for n in nodes if n['id'] == to_id), f"ID:{to_id}")
                
                preview += f"{i+1}. {from_type} → {to_type}\n"
        
        return preview

    def launch_designer(self):
        try:
            # Dear PyGUI設計ツールを別プロセスで起動
            subprocess.Popen([sys.executable, "agent_designer/designer_gui.py"])
            self.design_preview.append("設計ツールを起動しました")
        except Exception as e:
            self.design_preview.append(f"起動エラー: {str(e)}")
    
    def select_design_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "設計ファイル選択", "configs/", "JSON Files (*.json)"
        )
        if file:
            self.design_combo.addItem(file)
            self.design_preview.append(f"設計ファイルを選択: {file}")