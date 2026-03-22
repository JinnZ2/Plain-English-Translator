# CLAUDE.md — Plain English Translator

## Project Overview

Plain English Translator is a Python tool that converts complex medical, legal, insurance, and financial jargon into plain, understandable language. It processes documents locally (no data leaves the user's machine) and outputs translated results with red flags, rights, action items, and confidence scores.

**Status**: Beta (v1.0.0) — core implementation exists in `PDF_support.md` as reference code but has not yet been extracted into a working `translator.py` module.

## Repository Structure

```
Plain-English-Translator/
├── README.md                 # Project documentation and usage guide
├── CONTRIBUTING.md           # Contribution guidelines (terms, patterns, red flags)
├── LICENSE                   # MIT License
├── Requirements.txt          # Runtime Python dependencies
├── setup.py                  # Package config (setuptools), entry points, dev deps
├── PDF_support.md            # Full implementation reference (~1161 lines of Python code)
├── batch_translate.py        # CLI batch processing tool (imports from translator module)
├── examples/
│   ├── README.md             # Example documentation
│   └── medical_example.py    # Sample medical document translation
└── .gothub/ISSUE_TEMPLATE/
    ├── bug_report.md
    └── feature_request.md
```

## Key Architecture

### Core Classes (defined in PDF_support.md)

- **`TranslationResult`** — Dataclass holding: `original_text`, `plain_english`, `key_points`, `action_items`, `red_flags`, `your_rights`, `confidence_score`, `document_type`, `source_file`
- **`EnhancedPlainEnglishTranslator`** — Main engine with jargon dictionaries, document pattern matching, red flag detection, rights identification, and multi-format file support (PDF, DOCX, TXT)

### Entry Points (from setup.py)

- `plain-english-translator` → `translator:main`
- `pet` → `translator:main` (short alias)

### Important Note

The `translator` module referenced by `batch_translate.py`, `examples/medical_example.py`, and `setup.py` entry points **does not exist as a file yet**. The implementation lives in `PDF_support.md` and needs to be extracted into a proper Python module.

## Development Setup

```bash
# Python 3.7+ required
pip install -r Requirements.txt

# Dev dependencies (defined in setup.py extras_require)
pip install pytest black flake8 pytest-cov
```

## Dependencies

Runtime: `requests`, `beautifulsoup4`, `pandas`, `PyPDF2`, `PyMuPDF`, `python-docx`, `openpyxl`

Dev: `pytest`, `black`, `flake8`, `pytest-cov`

## Code Conventions

- **Python 3.7+** compatibility required
- Use **type hints** for function signatures
- Include **docstrings** for all public functions
- Use **clear variable naming** — no abbreviations for domain-specific terms
- Emoji indicators in user-facing output: ⚠️ (red flags), ✅ (rights/success), 📋 (action items)
- Formatting tools: **black** for code formatting, **flake8** for linting

## Testing

No test suite exists yet. Dev dependencies specify `pytest` and `pytest-cov`. When tests are added, they should go in a `tests/` directory and be runnable via:

```bash
pytest
```

## Document Types Supported

Medical, legal, insurance, and financial documents. Each type has its own:
- Jargon dictionary (term → plain English mapping)
- Red flag patterns (regex-based detection of predatory/concerning clauses)
- Rights indicators (what the user is entitled to)
- Sneaky clause detection patterns

## Contributing Conventions

- New jargon terms follow the format: `"technical_term": "plain English explanation — What it actually means for you"`
- Red flag patterns use regex and include both `pattern` and `meaning` fields
- See `CONTRIBUTING.md` for detailed guidelines on adding medical terms, legal red flags, and insurance decoders

## Privacy

All document processing happens locally. Documents never leave the user's machine. This is a core design principle — do not introduce any external API calls for document content.
