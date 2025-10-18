# 03_target_schema — 理想スキーマ & 埋め込み方針（テンプレート）

実際の内容は audit_collections() 実行で再生成されます。初期値は仕様準拠の提案です。

## rag_documents_ast_functions
- dense(text): signature_line, fqn, short_doc, extends, ports_params_digest, uses_fqn_topk
- sparse: signature tokens / identifiers / constants
- payload: fqn, kind, file_path, line_start, line_end, arity, tags, version, checksum, neighbors.uses
- 禁止: code_text 全文の格納（長文化回避）

## rag_documents_ast_equations
- dense(text): equation_str + owner_fqn + section_type + locality
- sparse: 演算子/識別子/関数名トークン
- payload: owner_fqn, equation_id, section_type, file_path, line_start, line_end

## rag_documents_ast_packages
- dense(text): package name + fqn + short description + exported symbols digest
- sparse: 公開シンボル名列挙
- payload: fqn, exports(top-N), doc_summary, version

## rag_documents_pdf
- dense(text): content + doc_title + section_title + chunk_type + page
- sparse: 見出し/太字/コードフォント等
- payload: chunk_id, page, chunk_type, contains_tables/figures/formulas, source_document, bbox(optional), prev/next
