import sys, os, importlib.util
path = os.path.join(os.getcwd(), 'new_pdf_converter', 'pymupdf_converter', 'llm_chunker.py')
spec = importlib.util.spec_from_file_location('llm_chunker', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MarkdownChunker = mod.MarkdownChunker
from pathlib import Path
p = Path('new_pdf_converter/DA010809_original.md')
text = p.read_text(encoding='utf-8')
chunker = MarkdownChunker()
secs = chunker._parse_sections(text)
print('sections:', len(secs))
for i,s in enumerate(secs[:12]):
    print(i, s['level'], repr(s['title'][:60]), 'page=', s.get('page'), 'content_len=', len(s.get('content','')))
