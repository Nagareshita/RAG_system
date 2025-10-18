"""
既存の設定ファイルから旧ASTコレクション参照を削除するスクリプト
"""
import json
import os
from pathlib import Path

def update_config_file(file_path):
    """設定ファイル内のrag_documents_astをrag_documents_ast_packagesに更新"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        updated = False
        
        # ノード設定を探索
        if 'nodes' in config:
            for node in config['nodes']:
                if 'config' in node:
                    # target_collections を確認
                    if 'target_collections' in node['config']:
                        tc = node['config']['target_collections']
                        if isinstance(tc, dict) and 'value' in tc:
                            if tc['value'] == 'rag_documents_ast':
                                tc['value'] = 'rag_documents_ast_packages'
                                updated = True
                                print(f"  ノード {node.get('id', '?')}: rag_documents_ast → rag_documents_ast_packages")
                        elif isinstance(tc, list):
                            for i, val in enumerate(tc):
                                if val == 'rag_documents_ast':
                                    tc[i] = 'rag_documents_ast_packages'
                                    updated = True
                                    print(f"  ノード {node.get('id', '?')}: リスト内の rag_documents_ast → rag_documents_ast_packages")
        
        # その他の設定構造を探索
        def recursive_update(obj, path=""):
            nonlocal updated
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'target_collections':
                        if isinstance(value, dict) and 'value' in value:
                            if value['value'] == 'rag_documents_ast':
                                value['value'] = 'rag_documents_ast_packages'
                                updated = True
                                print(f"  {path}.{key}: rag_documents_ast → rag_documents_ast_packages")
                    elif isinstance(value, (dict, list)):
                        recursive_update(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        recursive_update(item, f"{path}[{i}]")
        
        recursive_update(config)
        
        if updated:
            # バックアップを作成
            backup_path = str(file_path) + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=1, ensure_ascii=False)
            print(f"  バックアップ作成: {backup_path}")
            
            # 更新したファイルを保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=1, ensure_ascii=False)
            print(f"  ✓ 更新完了")
            return True
        else:
            print(f"  変更なし")
            return False
            
    except Exception as e:
        print(f"  エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("旧ASTコレクション参照を更新")
    print("=" * 60)
    
    # configs/designsフォルダ内の全JSONファイルを処理
    designs_dir = Path('configs/designs')
    
    if not designs_dir.exists():
        print(f"エラー: {designs_dir} が見つかりません")
        return
    
    json_files = list(designs_dir.glob('*.json'))
    
    if not json_files:
        print(f"{designs_dir} 内にJSONファイルが見つかりません")
        return
    
    print(f"\n{len(json_files)} 個のファイルを処理します...\n")
    
    updated_count = 0
    
    for json_file in json_files:
        print(f"処理中: {json_file.name}")
        if update_config_file(json_file):
            updated_count += 1
        print()
    
    print("=" * 60)
    print(f"完了: {updated_count}/{len(json_files)} ファイルを更新しました")
    print("=" * 60)
    
    if updated_count > 0:
        print("\n📝 注意:")
        print("- .backup ファイルがバックアップとして保存されています")
        print("- 問題があれば .backup ファイルから復元できます")
        print("- vector_db/rag_documents_ast フォルダは手動で削除してください")

if __name__ == '__main__':
    main()
