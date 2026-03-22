# CLAUDE.md — Plain English Translator

## Project Overview

Plain English Translator is a Python tool that converts complex medical, legal, insurance, and financial jargon into plain, understandable language. It processes documents locally (no data leaves the user's machine) and outputs translated results with red flags, rights, action items, and confidence scores.

**Version**: 1.0.0 (Beta)
**License**: MIT

## Repository Structure

```
Plain-English-Translator/
├── translator.py              # Core module: EnhancedPlainEnglishTranslator class + CLI
├── batch_translate.py         # CLI tool for batch processing multiple documents
├── setup.py                   # Package config (setuptools), entry points, dev deps
├── requirements.txt           # Runtime Python dependencies
├── README.md                  # Project documentation and usage guide
├── CONTRIBUTING.md            # Contribution guidelines (terms, patterns, red flags)
├── LICENSE                    # MIT License
├── PDF_support.md             # Implementation reference/design document
├── .gitignore                 # Git ignore rules
├── examples/
│   ├── README.md              # Example documentation
│   └── medical_example.py     # Sample medical discharge summary translation
└── .github/ISSUE_TEMPLATE/
    ├── bug_report.md
    └── feature_request.md
```

## Key Architecture

### Core Module: `translator.py`

- **`TranslationResult`** — Dataclass holding: `original_text`, `plain_english`, `key_points`, `action_items`, `red_flags`, `your_rights`, `confidence_score`, `document_type`, `source_file`
- **`EnhancedPlainEnglishTranslator`** — Main engine with:
  - Jargon dictionaries for 4 domains (medical, legal, insurance, financial)
  - Document type auto-detection via keyword scoring
  - Red flag detection using phrase matching
  - Sneaky clause detection using regex patterns
  - Rights identification
  - Action item generation
  - Confidence scoring
  - Multi-format file support (PDF via PyMuPDF/PyPDF2, DOCX, TXT)
  - HTML report generation via `save_translation()`
- **`PlainEnglishTranslator`** — Alias for `EnhancedPlainEnglishTranslator` (backwards compatibility)

### Entry Points (from setup.py)

- `plain-english-translator` → `translator:main`
- `pet` → `translator:main` (short alias)

### Key Methods

- `translate_document(text)` — Translate raw text string
- `translate_document_from_file(file_path)` — Translate from a file (PDF/DOCX/TXT)
- `save_translation(result, output_name)` — Save result as HTML to `translations/` directory

## Development Setup

```bash
# Python 3.7+ required
pip install -r requirements.txt

# Dev dependencies
pip install -e ".[dev]"
```

## Running

```bash
# Translate a single document
python translator.py document.txt
python translator.py document.pdf -o output-name

# Batch translate
python batch_translate.py "documents/*.txt"

# Run example
python examples/medical_example.py
```

## Dependencies

**Runtime**: `requests`, `beautifulsoup4`, `pandas`, `PyPDF2`, `PyMuPDF`, `python-docx`, `openpyxl`

**Dev**: `pytest`, `black`, `flake8`, `pytest-cov`

## Code Conventions

- **Python 3.7+** compatibility required
- Use **type hints** for function signatures
- Include **docstrings** for all public methods
- Use **clear variable naming** — no abbreviations for domain-specific terms
- Emoji indicators in user-facing CLI output: ⚠️ (red flags), ✅ (rights/success), 📋 (action items), 🚨 (sneaky clauses)
- Formatting: **black** for code formatting, **flake8** for linting
- Private methods prefixed with `_` (e.g., `_load_jargon_dictionary`)

## Testing

Tests should go in a `tests/` directory and be runnable via:

```bash
pytest
pytest --cov=translator
```

## Adding Content

### New jargon terms
Add to the appropriate domain dict in `translator.py`'s `_load_jargon_dictionary()`:
```python
'technical_term': 'plain English explanation',
```

### New red flag patterns
Add to the appropriate domain list in `_load_document_patterns()`:
```python
'problematic phrase to detect',
```

### New sneaky clause regex patterns
Add to the appropriate list in `_load_sneaky_patterns()`:
```python
r'regex.*pattern.*to.*match',
```

See `CONTRIBUTING.md` for full guidelines.

## Privacy

All document processing happens locally. Documents never leave the user's machine. This is a core design principle — do not introduce any external API calls for document content.
