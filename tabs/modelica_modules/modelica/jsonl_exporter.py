# ast_only/src/modelica/jsonl_exporter.py
"""
RAG最適化されたJSONL出力システム（情報保持最大化版）
ベクトル化・検索システム連携用の形式で出力、フィルタされたデータをそのまま尊重
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional, TextIO
import json
import hashlib
from datetime import datetime
import re

try:
    from tabs.modelica_modules.modelica.content_filter import ContentFilter, FilterRuleManager
    CONTENT_FILTER_AVAILABLE = True
except ImportError:
    ContentFilter = None
    FilterRuleManager = None
    CONTENT_FILTER_AVAILABLE = False

class JSONLExporter:
    """JSONL形式でのデータ出力管理（情報保持最大化）"""
    
    def __init__(self):
        if CONTENT_FILTER_AVAILABLE:
            self.filter_manager = FilterRuleManager()
            self.content_filter = ContentFilter()
        else:
            self.filter_manager = None
            self.content_filter = None
    
    def preview_jsonl_record(self, record: Dict[str, Any], stage: str = "rag_optimized") -> str:
        """単一レコードのJSONLプレビューを生成（修正：真の1行JSONL形式）"""
        if not self.content_filter:
            return "ContentFilter が利用できません"
        
        try:
            # フィルタリング適用
            filtered_record = self.content_filter.filter_record(record, stage)
            
            # JSONL用のレコード形式を構築（制限なし）
            jsonl_record = self._build_jsonl_record(filtered_record)
            
            # 修正：1行のJSONLとして返す（indent=2を削除）
            return json.dumps(jsonl_record, ensure_ascii=False, separators=(',', ':'))
            
        except Exception as e:
            return f"プレビュー生成エラー: {str(e)}"
    
    def _build_jsonl_record(self, filtered_record: Dict[str, Any]) -> Dict[str, Any]:
        """JSONL用のレコード形式を構築（フィルタ結果をそのまま尊重、制限なし）"""
        
        # メインコンテンツを構築（制限を一切設けない）
        content_parts = []
        
        # 基本情報
        content_parts.append(f"[{filtered_record.get('kind', 'unknown')}] {filtered_record.get('name', 'unnamed')}")
        
        # パッケージパス
        if filtered_record.get("package_path"):
            if isinstance(filtered_record["package_path"], list):
                package_str = ".".join(str(p) for p in filtered_record["package_path"])
            else:
                package_str = str(filtered_record["package_path"])
            content_parts.append(f"Package: {package_str}")
        
        # ドキュメント（制限なし、フィルタ結果をそのまま使用）
        doc_text = ""
        if filtered_record.get("documentation"):
            doc_text = str(filtered_record["documentation"])
        elif filtered_record.get("docstring"):
            doc_text = str(filtered_record["docstring"])
        
        if doc_text and len(doc_text.strip()) > 0:
            content_parts.append(f"Documentation: {doc_text}")
        
        # パラメータ（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("parameters"):
            params = filtered_record["parameters"]
            if isinstance(params, list) and params:
                param_strs = []
                for p in params:  # 制限なし
                    if isinstance(p, dict):
                        param_str = f"{p.get('name', '?')}: {p.get('type', '?')}"
                        if p.get('default') not in [None, "", "0", "false"]:
                            param_str += f" = {p['default']}"
                        if p.get('description'):
                            param_str += f" - {p['description']}"
                        param_strs.append(param_str)
                    else:
                        param_strs.append(str(p))
                if param_strs:
                    content_parts.append(f"Parameters: {'; '.join(param_strs)}")
        
        # コンポーネント（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("components"):
            components = filtered_record["components"]
            if isinstance(components, list) and components:
                comp_strs = []
                for c in components:  # 制限なし
                    if isinstance(c, dict):
                        comp_str = f"{c.get('name', '?')}: {c.get('type_name', c.get('type', '?'))}"
                        if c.get('prefixes'):
                            prefixes = c['prefixes']
                            if isinstance(prefixes, list):
                                comp_str += f" [{', '.join(str(p) for p in prefixes)}]"
                            else:
                                comp_str += f" [{prefixes}]"
                        if c.get('modifications'):
                            mods = c['modifications']
                            if isinstance(mods, dict):
                                mod_strs = [f"{k}={v}" for k, v in mods.items()]
                                comp_str += f" ({', '.join(mod_strs)})"
                        comp_strs.append(comp_str)
                    else:
                        comp_strs.append(str(c))
                if comp_strs:
                    content_parts.append(f"Components: {'; '.join(comp_strs)}")
        
        # 方程式（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("equations"):
            equations = filtered_record["equations"]
            eq_strs = []
            
            if isinstance(equations, list):
                for eq in equations:  # 制限なし
                    if isinstance(eq, str):
                        eq_clean = eq.strip()
                        if len(eq_clean) > 5:
                            eq_strs.append(eq_clean)  # 文字数制限も除去
                    elif isinstance(eq, dict) and "equations" in eq:
                        section_type = eq.get("section_type", "")
                        if section_type:
                            eq_strs.append(f"[{section_type}]")
                        for inner_eq in eq["equations"]:  # 制限なし
                            eq_str = str(inner_eq).strip()
                            if len(eq_str) > 5 and "connect(" not in eq_str.lower():
                                eq_strs.append(eq_str)  # 文字数制限も除去
                    else:
                        eq_str = str(eq).strip()
                        if len(eq_str) > 5:
                            eq_strs.append(eq_str)  # 文字数制限も除去
                            
            if eq_strs:
                content_parts.append(f"Equations: {'; '.join(eq_strs)}")
        
        # 接続（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("connections"):
            connections = filtered_record["connections"]
            if isinstance(connections, list) and connections:
                conn_strs = []
                for c in connections:  # 制限なし
                    if isinstance(c, dict):
                        from_conn = c.get("from", c.get("from_connector", "?"))
                        to_conn = c.get("to", c.get("to_connector", "?"))
                        conn_strs.append(f"{from_conn} -> {to_conn}")
                    else:
                        conn_strs.append(str(c))
                if conn_strs:
                    content_parts.append(f"Connections: {'; '.join(conn_strs)}")
        
        # 依存関係（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("dependencies"):
            deps = filtered_record["dependencies"]
            if isinstance(deps, dict):
                dep_strs = []
                for dep_type, dep_list in deps.items():
                    if dep_list:
                        if isinstance(dep_list, list):
                            if dep_type == "component_instances":
                                # コンポーネントインスタンスは詳細表示
                                inst_strs = []
                                for inst in dep_list:  # 制限なし
                                    if isinstance(inst, dict):
                                        inst_str = f"{inst.get('instance_name', '?')}: {inst.get('type', '?')}"
                                        if inst.get('library'):
                                            inst_str += f" (from {inst['library']})"
                                        inst_strs.append(inst_str)
                                    else:
                                        inst_strs.append(str(inst))
                                if inst_strs:
                                    dep_strs.append(f"{dep_type}: {', '.join(inst_strs)}")
                            else:
                                dep_strs.append(f"{dep_type}: {', '.join(str(d) for d in dep_list)}")  # 制限なし
                        else:
                            dep_strs.append(f"{dep_type}: {dep_list}")
                if dep_strs:
                    content_parts.append(f"Dependencies: {'; '.join(dep_strs)}")
        
        # 物理量情報（制限なし、フィルタ結果をそのまま使用）
        if filtered_record.get("physical_quantities"):
            pq = filtered_record["physical_quantities"]
            if isinstance(pq, dict):
                pq_parts = []
                if pq.get("quantities"):
                    quantities = pq["quantities"]  # 制限なし
                    q_strs = []
                    for q in quantities:
                        if isinstance(q, dict):
                            q_str = q.get('name', '?')
                            if q.get('unit'):
                                q_str += f"[{q['unit']}]"
                            q_strs.append(q_str)
                    if q_strs:
                        pq_parts.append(f"quantities: {', '.join(q_strs)}")
                if pq.get("units"):
                    pq_parts.append(f"units: {', '.join(str(u) for u in pq['units'])}")  # 制限なし
                if pq.get("domains"):
                    pq_parts.append(f"domains: {', '.join(str(d) for d in pq['domains'])}")  # 制限なし
                if pq_parts:
                    content_parts.append(f"Physical: {'; '.join(pq_parts)}")
        
        # extends/imports（従来形式もサポート）
        if filtered_record.get("extends"):
            extends = filtered_record["extends"]
            if isinstance(extends, list) and extends:
                content_parts.append(f"Extends: {', '.join(str(e) for e in extends)}")
            elif extends:
                content_parts.append(f"Extends: {extends}")
        
        if filtered_record.get("imports"):
            imports = filtered_record["imports"]
            if isinstance(imports, list) and imports:
                content_parts.append(f"Imports: {', '.join(str(i) for i in imports)}")
            elif imports:
                content_parts.append(f"Imports: {imports}")
        
        # コンテンツテキストを結合
        content_text = " | ".join(content_parts)
        
        # 詳細な統計情報
        stats = {
            "parameters_count": len(filtered_record.get("parameters", [])),
            "components_count": len(filtered_record.get("components", [])),
            "equations_count": self._count_equations(filtered_record.get("equations", [])),
            "connections_count": len(filtered_record.get("connections", [])),
            "content_sections": len(content_parts)
        }
        
        # 最終的なJSONLレコード
        jsonl_record = {
            "id": filtered_record.get("id", filtered_record.get("fqn", filtered_record.get("name", "unknown"))),
            "content": content_text,
            "metadata": {
                "kind": filtered_record.get("kind", "unknown"),
                "name": filtered_record.get("name", "unnamed"),
                "stage": filtered_record.get("stage", "unknown"),
                "package_path": filtered_record.get("package_path", []),
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content_text),
                "stats": stats
            },
            # 構造化された詳細情報も保持（検索時の参照用）
            "structured_data": {
                "parameters": filtered_record.get("parameters", []),
                "components": filtered_record.get("components", []),
                "equations": filtered_record.get("equations", []),
                "connections": filtered_record.get("connections", []),
                "dependencies": filtered_record.get("dependencies", {}),
                "physical_quantities": filtered_record.get("physical_quantities", {})
            }
        }
        
        return jsonl_record
    
    def _count_equations(self, equations: List) -> int:
        """方程式の総数をカウント"""
        if not equations:
            return 0
        
        total = 0
        for eq in equations:
            if isinstance(eq, dict) and "equations" in eq:
                total += len(eq["equations"])
            else:
                total += 1
        return total
    
    def export_records(
        self, 
        records: List[Dict[str, Any]], 
        output_path: Path,
        stage: str = "rag_optimized",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """レコードをJSONL形式で出力（制限なし）"""
        if not self.content_filter:
            raise RuntimeError("ContentFilter が利用できません")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        exported_count = 0
        skipped_count = 0
        total_stats = {
            "parameters": 0,
            "components": 0,
            "equations": 0,
            "connections": 0
        }
        
        export_stats = {
            "total_input": len(records),
            "exported": 0,
            "skipped": 0,
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "output_file": str(output_path),
            "content_stats": total_stats
        }
        
        if metadata:
            export_stats["metadata"] = metadata
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in records:
                try:
                    # フィルタリング適用
                    filtered_record = self.content_filter.filter_record(record, stage)
                    
                    # 有効性チェック
                    if self._is_valid_record(filtered_record):
                        # JSONL形式で出力
                        jsonl_record = self._build_jsonl_record(filtered_record)
                        f.write(json.dumps(jsonl_record, ensure_ascii=False) + '\n')
                        exported_count += 1
                        
                        # 統計更新
                        stats = jsonl_record["metadata"]["stats"]
                        total_stats["parameters"] += stats.get("parameters_count", 0)
                        total_stats["components"] += stats.get("components_count", 0)
                        total_stats["equations"] += stats.get("equations_count", 0)
                        total_stats["connections"] += stats.get("connections_count", 0)
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"レコード出力エラー: {record.get('name', '?')} - {e}")
                    skipped_count += 1
        
        export_stats["exported"] = exported_count
        export_stats["skipped"] = skipped_count
        
        # 統計ファイルも出力
        stats_path = output_path.with_suffix('.stats.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(export_stats, f, indent=2, ensure_ascii=False)
        
        print(f"JSONL出力完了: {exported_count}件出力, {skipped_count}件スキップ")
        print(f"出力先: {output_path}")
        print(f"統計: {stats_path}")
        print(f"総パラメータ数: {total_stats['parameters']}")
        print(f"総コンポーネント数: {total_stats['components']}")
        print(f"総方程式数: {total_stats['equations']}")
        print(f"総接続数: {total_stats['connections']}")
        
        return export_stats
    
    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """レコードの有効性をチェック"""
        # 必須フィールドのチェック
        if not record.get("id") and not record.get("name"):
            return False
        
        # 内容があるかチェック
        has_content = any([
            record.get("documentation"),
            record.get("docstring"),
            record.get("parameters"),
            record.get("equations"), 
            record.get("components"),
            record.get("physical_quantities"),
            record.get("connections"),
            record.get("dependencies")
        ])
        
        return has_content