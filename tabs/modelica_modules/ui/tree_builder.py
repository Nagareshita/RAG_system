# ast_only/src/ui/tree_builder.py
"""
Modelica階層ツリー構造の構築を担当。
FQNやpackage_pathから実際のライブラリ構造を復元する。
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

class ModelicaTreeBuilder:
    """Modelicaの階層構造を構築するクラス"""
    
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.hierarchy: Dict[str, Dict] = {}
    
    def build_tree_model(self, records: List[Dict[str, Any]], root_name: str = "ライブラリ") -> QStandardItemModel:
        """レコードから階層ツリーモデルを構築（2カラムヘッダー）"""
        self.records = records
        print(f"🌳 ツリー構築開始: {len(records)} レコード, ルート='{root_name}'")
        
        try:
            self._build_hierarchy()
            
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["名前", "種類"])  # 要素数欄を削除
            
            root = QStandardItem(root_name)
            root.setData({"type": "root", "count": len(records)}, Qt.UserRole)
            model.appendRow([root, QStandardItem("root")])  # 2カラムのみ
            
            if not records:
                empty_item = QStandardItem("(空)")
                root.appendRow([empty_item, QStandardItem("")])
                print("📝 空のツリーを作成しました")
                return model
            
            # デバッグ情報省略...
            
            # トップレベルパッケージから構築
            self._build_tree_items(root, self.hierarchy, "")
            
            print("✅ ツリー構築完了")
            return model
            
        except Exception as e:
            print(f"❌ ツリー構築エラー: {e}")
            # エラー時でも空のモデルを返す（2カラム）
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["名前", "種類"])
            
            root = QStandardItem(f"エラー: {root_name}")
            error_item = QStandardItem(f"構築エラー: {str(e)}")
            model.appendRow([root, error_item])
            return model
    
    def _build_hierarchy(self):
        """レコードから階層辞書を構築"""
        self.hierarchy = {}
        
        print(f"🔍 階層分析開始...")
        fqn_examples = []
        
        for i, record in enumerate(self.records):
            fqn = record.get("fqn", "")
            if not fqn:
                print(f"⚠️  FQNが空のレコード: {record.get('name', '?')}")
                continue
                
            if i < 5:  # 最初の5個をデバッグ表示
                fqn_examples.append(fqn)
            
            # FQNを分割してパスを作成
            parts = fqn.split(".")
            current_level = self.hierarchy
            
            # 階層の各レベルを作成
            for j, part in enumerate(parts):
                if not part:  # 空の部分をスキップ
                    continue
                    
                if part not in current_level:
                    current_level[part] = {
                        "_children": {},
                        "_records": [],
                        "_info": {
                            "name": part,
                            "path": ".".join(parts[:j+1]),
                            "level": j,
                            "is_leaf": j == len(parts) - 1
                        }
                    }
                
                # 最後の要素なら、このレコードを追加
                if j == len(parts) - 1:
                    current_level[part]["_records"].append(record)
                
                current_level = current_level[part]["_children"]
        
        print(f"📝 FQN例: {fqn_examples}")
        print(f"🏗️  階層構築完了: {len(self.hierarchy)} トップレベル")
    
    def _build_tree_items(self, parent_item: QStandardItem, hierarchy: Dict, parent_path: str):
        """階層辞書からQStandardItemを再帰的に構築（要素数欄削除対応）"""
        try:
            for name, data in sorted(hierarchy.items()):
                records = data.get("_records", [])
                children = data.get("_children", {})
                info = data.get("_info", {})
                
                # アイテムの基本情報
                current_path = f"{parent_path}.{name}" if parent_path else name
                
                # 種類の判定
                if len(records) == 1:
                    display_kind = records[0].get("kind", "unknown")
                elif len(records) > 1:
                    display_kind = f"複数({len(records)})"
                else:
                    display_kind = "package" if children else "empty"
                
                # ツリーアイテムを作成（2カラムのみ）
                name_item = QStandardItem(name)
                kind_item = QStandardItem(display_kind)
                # count_itemは作成しない
                
                # アイテムにデータを保存
                item_data = {
                    "type": "node",
                    "name": name,
                    "path": current_path,
                    "records": records,
                    "children_count": len(children),
                    "debug_info": {
                        "records_count": len(records),
                        "children_keys": list(children.keys())[:3]
                    }
                }
                name_item.setData(item_data, Qt.UserRole)
                
                # 種類に応じてアイコンや色を設定
                self._set_item_appearance(name_item, display_kind, len(records), len(children))
                
                # 2カラムのみ追加
                parent_item.appendRow([name_item, kind_item])
                
                # 子要素を再帰的に追加
                if children:
                    self._build_tree_items(name_item, children, current_path)
        
        except Exception as e:
            print(f"❌ ツリーアイテム構築エラー: {e}")
            # エラーアイテムを追加（2カラム）
            error_item = QStandardItem(f"エラー: {str(e)}")
            parent_item.appendRow([error_item, QStandardItem("error")])
    
    def _calculate_element_count(self, record: Dict[str, Any]) -> str:
        """単一レコードの要素数を計算"""
        counts = []
        for key, label in [
            ("components", "C"), ("variables", "V"), ("parameters", "P"),
            ("equations", "E"), ("connections", "Cn")
        ]:
            count = len(record.get(key, []))
            if count > 0:
                counts.append(f"{label}:{count}")
        
        # フォールバック情報があれば追加
        if record.get("meta", {}).get("fallback_extraction"):
            if not counts:
                counts.append("(F)")  # Fallback indicator
        
        return "/".join(counts) if counts else "0"
    
    def _set_item_appearance(self, item: QStandardItem, kind: str, record_count: int, children_count: int):
        """アイテムの外観を設定"""
        # 種類に応じてアイコンっぽい文字を設定
        if "package" in kind.lower():
            item.setText(f"📁 {item.text()}")
        elif "model" in kind.lower():
            item.setText(f"🔧 {item.text()}")
        elif "function" in kind.lower():
            item.setText(f"⚙️ {item.text()}")
        elif "connector" in kind.lower():
            item.setText(f"🔌 {item.text()}")
        elif "block" in kind.lower():
            item.setText(f"📦 {item.text()}")
        elif children_count > 0:
            item.setText(f"📂 {item.text()}")
        else:
            item.setText(f"📄 {item.text()}")
        
        # フォールバック抽出の場合は色を変える（今後のCSS対応用）
        # if record_count > 0:
        #     first_record = item.data(Qt.UserRole).get("records", [{}])[0]
        #     if first_record.get("meta", {}).get("fallback_extraction"):
        #         item.setToolTip("フォールバック抽出による概算データ")

def create_tree_model(records: List[Dict[str, Any]], folder_path: Optional[Path] = None) -> QStandardItemModel:
    """便利関数: レコードからツリーモデルを作成"""
    root_name = folder_path.name if folder_path else "ライブラリ"
    builder = ModelicaTreeBuilder()
    return builder.build_tree_model(records, root_name)

class TreeBuilder:
    """app_pyside_modelica_analyzer.py との互換性のためのラッパークラス"""
    
    def __init__(self, tree_widget):
        self.tree_widget = tree_widget
        self.tree_builder = ModelicaTreeBuilder()
        # 初期設定で2カラムに設定
        self.tree_widget.setHeaderLabels(["名前", "種類"])
        
    def build_tree_from_records(self, records: List[Dict[str, Any]]):
        """レコードからツリーウィジェットを構築"""
        try:
            # QTreeWidget を初期化
            self.tree_widget.clear()
            self.tree_widget.setHeaderLabels(["名前", "種類"])  # 2カラムに修正
            
            if not records:
                print("📝 レコードが空です")
                return
            
            print(f"🌳 ツリー構築開始: {len(records)} レコード")
            
            # 階層構造を構築
            hierarchy = self._build_hierarchy_from_records(records)
            
            # ツリーウィジェットにアイテムを追加
            self._add_items_to_tree(hierarchy, None)
            
            # 最初のレベルを展開
            for i in range(min(3, self.tree_widget.topLevelItemCount())):
                item = self.tree_widget.topLevelItem(i)
                if item:
                    item.setExpanded(True)
            
            print(f"✅ ツリー構築完了: {self.tree_widget.topLevelItemCount()} トップレベルアイテム")
            
        except Exception as e:
            print(f"❌ ツリー構築エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _build_hierarchy_from_records(self, records: List[Dict[str, Any]]) -> Dict:
        """レコードから階層構造を構築"""
        hierarchy = {}
        
        for record in records:
            fqn = record.get("fqn", "")
            if not fqn:
                # FQNがない場合は名前を使用
                fqn = record.get("name", "unknown")
            
            # FQNを分割してパスを作成
            parts = fqn.split(".")
            current_level = hierarchy
            
            # 階層の各レベルを作成
            for j, part in enumerate(parts):
                if not part:
                    continue
                    
                if part not in current_level:
                    current_level[part] = {
                        "_children": {},
                        "_records": [],
                        "_info": {
                            "name": part,
                            "path": ".".join(parts[:j+1]),
                            "level": j,
                            "is_leaf": j == len(parts) - 1
                        }
                    }
                
                # 最後の要素なら、このレコードを追加
                if j == len(parts) - 1:
                    current_level[part]["_records"].append(record)
                
                current_level = current_level[part]["_children"]
        
        return hierarchy
    
    def _add_items_to_tree(self, hierarchy: Dict, parent_item):
        """階層構造からQTreeWidgetItemを作成（要素数欄削除）"""
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt
        
        for name, data in sorted(hierarchy.items()):
            records = data.get("_records", [])
            children = data.get("_children", {})
            
            # 表示情報を計算
            if len(records) == 1:
                record = records[0]
                kind = record.get("kind", "unknown")
            elif len(records) > 1:
                kind = f"複数({len(records)})"
            else:
                kind = "package" if children else "empty"
            
            # アイテムを作成（2カラムのみ）
            if parent_item is None:
                item = QTreeWidgetItem(self.tree_widget)
            else:
                item = QTreeWidgetItem(parent_item)
            
            # アイテムの表示を設定（要素数欄を削除）
            display_name = self._get_display_name(name, kind)
            item.setText(0, display_name)
            item.setText(1, kind)
            # 要素数欄（第3カラム）は設定しない
            
            # レコードデータを保存（最初のレコードまたは代表的なもの）
            if records:
                item.setData(0, Qt.ItemDataRole.UserRole, records[0])
            else:
                # 子要素があるパッケージ的なアイテムの場合
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "kind": "package",
                    "name": name,
                    "fqn": name,
                    "components": [],
                    "variables": [],
                    "parameters": [],
                    "equations": [],
                    "connections": [],
                    "extends": [],
                    "imports": [],
                    "docstring": None,
                    "meta": {"package_node": True}
                })
            
            # 子要素を再帰的に追加
            if children:
                self._add_items_to_tree(children, item)
    
    def _calculate_element_count(self, record: Dict[str, Any]) -> str:
        """レコードの要素数を計算"""
        counts = []
        
        components = len(record.get("components", []))
        variables = len(record.get("variables", []))
        parameters = len(record.get("parameters", []))
        
        if components > 0:
            counts.append(f"C:{components}")
        if variables > 0:
            counts.append(f"V:{variables}")
        if parameters > 0:
            counts.append(f"P:{parameters}")
        
        # 方程式の数を計算
        equations = record.get("equations", [])
        if equations:
            eq_count = 0
            for eq_block in equations:
                if isinstance(eq_block, dict):
                    eq_count += len(eq_block.get("equations", []))
                else:
                    eq_count += 1
            if eq_count > 0:
                counts.append(f"E:{eq_count}")
        
        # 接続の数
        connections = len(record.get("connections", []))
        if connections > 0:
            counts.append(f"Cn:{connections}")
        
        return "/".join(counts) if counts else "0"
    
    def _get_display_name(self, name: str, kind: str) -> str:
        """表示名を取得（アイコン付き）"""
        if "package" in kind.lower():
            return f"📁 {name}"
        elif "model" in kind.lower():
            return f"🔧 {name}"
        elif "function" in kind.lower():
            return f"⚙️ {name}"
        elif "connector" in kind.lower():
            return f"🔌 {name}"
        elif "block" in kind.lower():
            return f"📦 {name}"
        elif kind == "複数":
            return f"📂 {name}"
        else:
            return f"📄 {name}"


# 後方互換性のためのエイリアス
ModelicaTreeWidget = TreeBuilder