# ベクトル化タブ - 現状分析レポート

## 調査日: 2025年10月17日

---

## 📊 現状のベクトル化ロジック

### 1. ASTファイルの状況

#### 出力ファイル（3種類）
Modelicaライブラリ解析タブから出力されるJSONLファイル：
```
data/ast/
├── ast_packages.jsonl    # パッケージ、モデル、ブロック、コネクタなど
├── ast_functions.jsonl   # 関数定義
└── ast_equations.jsonl   # 個別の方程式
```

**特徴:**
- 各ファイルは独立したJSONL形式
- 異なる種類のASTデータを格納
- 追加データは各ファイルに追記される形式

---

## 🗄️ 現在のQdrantコレクション構造

### 実装されている2つのモード

#### モード1: 「分離」（Separated Collections）
```python
# vector_manager.py の _process_separated_collections メソッド
if collection_type == "分離":
    # AST専用コレクション（全JSONLファイルを一括）
    rag_documents_ast
    
    # PDF専用コレクション
    rag_documents_pdf
```

**問題点:**
- ❌ **3種類のJSONLを区別していない**
  - `ast_packages.jsonl`, `ast_functions.jsonl`, `ast_equations.jsonl`
  - これらが全て `rag_documents_ast` に混在
- ❌ **ファイル拡張子（.jsonl）だけで判定**
  - 3つのASTファイルを区別する仕組みがない
- ❌ **typeフィルタリング機能なし**
  - 検索時にパッケージ/関数/方程式を区別できない

#### モード2: 「混合」（Mixed Collection）
```python
# 単一コレクション
rag_documents_mixed
```

**問題点:**
- ❌ AST（3種類）とPDFが全て混在
- ❌ 検索精度の低下

---

## 🔍 コード分析詳細

### vectorization_tab.py
```python
# 現在の保存方式選択UI
self.collection_combo = QComboBox()
self.collection_combo.addItems(["分離", "混合"])
```

**判定ロジック:**
```python
collection_choice = self.collection_combo.currentText()
# "分離" または "混合" のみ
```

### vector_manager.py

#### ファイル判定（現状）
```python
def _process_separated_collections(self, file_structures, ...):
    # 拡張子だけで判定
    ast_files = [f for f in file_structures if f['file_path'].endswith('.jsonl')]
    pdf_files = [f for f in file_structures if f['file_path'].endswith('.json')]
```

**問題:**
- ファイル名の内容（packages, functions, equations）を見ていない
- 3種類のJSONLを区別できない

#### コレクション作成
```python
# AST用（全種類が混在）
self.create_collection("rag_documents_ast")

# PDF用
self.create_collection("rag_documents_pdf")
```

**問題:**
- ASTコレクションが1つしかない
- 3種類のデータが区別されない

---

## 🎯 理想的な構造（提案）

### オプション A: 3つの独立したコレクション

```python
# 推奨構造
rag_documents_ast_packages    # パッケージ、モデル、ブロック等
rag_documents_ast_functions   # 関数定義
rag_documents_ast_equations   # 方程式

rag_documents_pdf             # PDFチャンク
```

**メリット:**
- ✅ データの完全な分離
- ✅ 検索対象を明確に限定可能
- ✅ 各データタイプに最適化された検索戦略
- ✅ スケーラビリティ（将来的な拡張が容易）

**デメリット:**
- ⚠️ コレクション数が増加
- ⚠️ 横断検索時に複数クエリが必要

---

### オプション B: 1つのコレクション + typeフィルタ

```python
# 単一コレクション
rag_documents_unified

# ペイロードにtype情報を追加
{
    "text": "...",
    "type": "ast_package",     # or "ast_function", "ast_equation", "pdf"
    "source_file": "...",
    "metadata": {...}
}
```

**実装例:**
```python
# 検索時にフィルタリング
from qdrant_client.models import Filter, FieldCondition, MatchValue

client.search(
    collection_name="rag_documents_unified",
    query_vector=vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="type",
                match=MatchValue(value="ast_package")
            )
        ]
    )
)
```

**メリット:**
- ✅ コレクション管理がシンプル
- ✅ 横断検索が容易
- ✅ フィルタリングで柔軟な検索

**デメリット:**
- ⚠️ 大規模データ時のパフォーマンス
- ⚠️ フィルタ条件の管理が必要

---

## 📝 現状の問題点まとめ

### 1. ファイル識別の問題
```python
# 現在: 拡張子のみで判定
ast_files = [f for f in file_structures if f['file_path'].endswith('.jsonl')]

# 問題: 以下を区別できない
# - ast_packages.jsonl
# - ast_functions.jsonl
# - ast_equations.jsonl
```

### 2. コレクション構造の問題
```
現状:
  rag_documents_ast    ← 3種類が混在
  rag_documents_pdf

理想 (オプションA):
  rag_documents_ast_packages
  rag_documents_ast_functions
  rag_documents_ast_equations
  rag_documents_pdf

理想 (オプションB):
  rag_documents_unified (+ typeフィルタ)
```

### 3. メタデータの問題
```python
# 現在のペイロード
{
    "text": "...",
    "source_file": "ast_packages.jsonl",  # ファイル名はあるが
    "entry_id": 123,
    "metadata": {...}
    # type情報がない！
}
```

---

## 🔧 必要な修正

### 優先度：高

#### 1. ファイル種別の識別
```python
def _identify_ast_file_type(self, file_path: str) -> str:
    """ASTファイルの種類を識別"""
    basename = os.path.basename(file_path).lower()
    
    if 'package' in basename:
        return 'ast_package'
    elif 'function' in basename:
        return 'ast_function'
    elif 'equation' in basename:
        return 'ast_equation'
    else:
        return 'ast_unknown'
```

#### 2. コレクション名の改善（オプションA）
```python
def _get_collection_name(self, file_type: str) -> str:
    """ファイルタイプに応じたコレクション名"""
    mapping = {
        'ast_package': 'rag_documents_ast_packages',
        'ast_function': 'rag_documents_ast_functions',
        'ast_equation': 'rag_documents_ast_equations',
        'pdf': 'rag_documents_pdf'
    }
    return mapping.get(file_type, 'rag_documents_unknown')
```

#### 3. type情報の追加（オプションB）
```python
def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], 
                 document_type: str = None):
    """ドキュメント追加（type情報付き）"""
    # ...
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={
            "text": doc.get("text", ""),
            "type": document_type,  # ← 追加
            "source_file": doc.get("source_file", ""),
            # ...
        }
    )
```

---

## 💡 推奨実装方針

### フェーズ1: ファイル種別識別の実装
1. ファイル名からtype情報を抽出
2. `file_structures`にtype情報を追加

### フェーズ2: コレクション構造の選択
**推奨: オプションA（独立コレクション）**

理由:
- データの性質が大きく異なる
  - packages: 構造定義（中規模テキスト）
  - functions: 関数実装（小～中規模）
  - equations: 個別方程式（小規模）
- 検索戦略が異なる
- パフォーマンスの最適化が容易

### フェーズ3: UI改善
```python
# 保存方式の選択肢を拡張
self.collection_combo.addItems([
    "分離（3つのASTコレクション + PDF）",  # オプションA
    "統合（typeフィルタ使用）",            # オプションB
    "混合（非推奨）"                       # 現状維持
])
```

---

## 🎯 次のアクション

### すぐに実装すべき修正

1. **ファイルタイプ識別関数の追加**
   - `_identify_ast_file_type()` 実装

2. **コレクション分離処理の修正**
   - `_process_separated_collections()` を3コレクション対応に

3. **UI改善**
   - より明確な保存方式の説明

4. **ログ出力の改善**
   - どのファイルがどのコレクションに入ったかを明示

### 検討事項

- [ ] オプションA vs オプションB の最終決定
- [ ] 既存データの移行方法
- [ ] 検索UI側の対応（複数コレクション検索）
- [ ] パフォーマンステスト

---

## 📌 結論

**現状:** ASTの3種類のJSONLファイルが1つのコレクション（`rag_documents_ast`）に混在しており、区別できない。

**理想:** 3つの独立したコレクション、またはtypeフィルタ付き統合コレクション。

**推奨:** オプションA（独立コレクション）を実装して、データの性質に応じた最適化を行う。
