# 04_migration_plan — 段階的再インデックス & alias 切替（テンプレート）

- *_v2 を新設し、dense(named "text") + sparse + INT8量子化で作成
- データ投入後に alias を v2 へ切替
- 検証で問題があれば alias を削除して旧へロールバック

```python
from qdrant_client import QdrantClient, models as qm
c = QdrantClient(url="http://localhost:6333")

def create_v2(name, dim=1536):
    c.create_collection(
        collection_name=name,
        vectors_config={"text": qm.VectorParams(size=dim, distance=qm.Distance.COSINE)},
        sparse_vectors_config=qm.SparseVectorParams(),
        quantization_config=qm.ScalarQuantizationConfig(type=qm.ScalarType.INT8, always_ram=True),
        optimizers_config=qm.OptimizersConfigDiff(default_segment_number=2)
    )

for base in [
  "rag_documents_ast_equations",
  "rag_documents_ast_functions",
  "rag_documents_ast_packages",
  "rag_documents_pdf",
]:
    create_v2(base+"_v2")

# alias 切替（例）
c.create_alias("rag_documents_ast_functions", "rag_documents_ast_functions_v2")
```
