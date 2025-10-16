# PyMuPDF4LLM PDF to JSON Converter (Minimal)

This is a slimmed-down folder extracted to run only the GUI converter `apps_pymupdf_converter.py`.

## Requirements

- Python 3.9+
- Packages: see `requirements.txt`

## Install

```
pip install -r requirements.txt
```

## Run

```
python apps_pymupdf_converter.py
```

Then select a PDF, tune chunking parameters, and export results as JSON or Markdown.

## Structure

- `apps_pymupdf_converter.py` - Entry point for the GUI app
- `pymupdf_converter/` - Single package with everything needed:
  - `main_app.py`, `control_panel.py`, `result_viewer.py`, `pdf_processor.py`
  - `llm_models.py`, `llm_chunker.py`, `llm_processor.py`

Unrelated modules were removed and the hierarchy was flattened for clarity.
