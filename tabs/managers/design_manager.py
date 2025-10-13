# tabs/design_manager.py
import os
import json
from typing import Dict, Any, List, Optional


class DesignManager:
    """設計ファイル管理クラス"""
    
    def __init__(self, designs_dir: str = "configs/designs"):
        self.designs_dir = designs_dir
    
    def get_design_files(self) -> List[str]:
        """設計ファイル一覧を取得"""
        if not os.path.exists(self.designs_dir):
            return []
        
        json_files = [f for f in os.listdir(self.designs_dir) if f.endswith('.json')]
        return sorted(json_files)
    
    def load_design(self, filename: str) -> Optional[Dict[str, Any]]:
        """指定された設計ファイルを読み込み"""
        if not filename or filename == "設計ファイルがありません":
            return None
        
        file_path = os.path.join(self.designs_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"設計ファイル読み込みエラー: {e}")
            return None
    
    def validate_design(self, design_data: Dict[str, Any]) -> bool:
        """設計ファイルの基本的な妥当性チェック"""
        if not isinstance(design_data, dict):
            return False
        
        # 必要な基本キーの存在チェック
        required_keys = ["nodes", "connections"]
        if not all(key in design_data for key in required_keys):
            return False
        
        # nodesが配列であることを確認
        if not isinstance(design_data.get("nodes"), list):
            return False
        
        # connectionsが配列であることを確認
        if not isinstance(design_data.get("connections"), list):
            return False
        
        # 最低限のnode構造チェック
        for node in design_data["nodes"]:
            if not isinstance(node, dict):
                return False
            if not all(key in node for key in ["id", "type"]):
                return False
        
        return True