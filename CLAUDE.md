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
├── setup.py                   # Package config (setuptools), entry points, extras
├── requirements.txt           # Optional file-format dependencies (see below)
├── README.md                  # Project documentation and usage guide
├── CONTRIBUTING.md            # Contribution guidelines (terms, patterns, red flags)
├── METHOD.md                  # Audit log: hypotheses tested, what was falsified, open unknowns
├── LICENSE                    # MIT License
├── .flake8                    # Lint config (excludes legacy/)
├── .gitignore                 # Git ignore rules
├── tests/
│   └── test_translator.py     # Regression tests, incl. one per historical defect
├── legacy/                    # Superseded files, kept as record — never imported
│   ├── README.md              # Provenance notes for each archived file
│   └── PDF_support.md         # Original draft source that translator.py came from
├── examples/
│   ├── README.md              # Example documentation
│   └── medical_example.py     # Sample medical discharge summary translation
└── .github/ISSUE_TEMPLATE/
    ├── bug_report.md
    └── feature_request.md
```

### The `legacy/` folder

Superseded files are **moved here with `git mv`, not deleted** — precedence
carries. When current code looks arbitrary, the reason is often in the
ancestor. Every archived file gets a `legacy/README.md` entry recording what it
was, what superseded it, why it was retired, and why it's still worth keeping.
Nothing in `legacy/` is imported, executed, tested, or linted.

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
- `save_translation(result, output_name)` — Save result as escaped HTML to the
  `translations/` directory; returns the output `Path`

Raises `ExtractionError` (module-level) when a document's text cannot be read.

## Development Setup

```bash
# Python 3.7+ required. Core needs no dependencies;
# this adds PDF and Word support.
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

**Core**: none. Translating `.txt` uses only the standard library.

**Optional (`pip install -r requirements.txt`)**: `PyMuPDF`, `PyPDF2` (PDF),
`python-docx` (Word). These are **imported lazily inside the extractor that
needs them** — never at module top level. A missing package must degrade one
file format, not break the tool. Do not move these to module-level imports.

**Dev (`pip install -e ".[dev]"`)**: `pytest`, `black`, `flake8`, `pytest-cov`

`requests`, `beautifulsoup4`, `pandas`, and `openpyxl` were removed in Aug 2026 —
they were declared but never imported, and `requests` contradicted the
local-only privacy guarantee.

## Code Conventions

- **Python 3.7+** compatibility required
- Use **type hints** for function signatures
- Include **docstrings** for all public methods
- Use **clear variable naming** — no abbreviations for domain-specific terms
- Emoji indicators in user-facing CLI output: ⚠️ (red flags), ✅ (rights/success), 📋 (action items), 🚨 (sneaky clauses)
- Formatting: **black** for code formatting, **flake8** for linting
- Private methods prefixed with `_` (e.g., `_load_jargon_dictionary`)

## Testing

Tests live in `tests/` and run via:

```bash
pytest
pytest --cov=translator
```

`tests/test_translator.py::TestFalsifiedClaims` pins one test per defect found
by running the tool. Each carries a docstring naming the claim that was believed
true and the observation that disproved it. **Don't delete these as
redundant** — they are the only thing keeping fixed bugs fixed.

Two conventions worth keeping (rationale in `METHOD.md`):

- After fixing a bug, **revert the fix and confirm the test fails.** A test that
  has never failed proves nothing.
- Prioritise **silent wrong answers over crashes.** The worst bug found in this
  repo wasn't a traceback — it was `batch_translate.py` reporting
  "✅ success, 70% confidence" over a report built from PDF binary internals.

## Invariants

Learned the hard way; breaking these reintroduces shipped bugs.

1. **Optional imports stay lazy.** See Dependencies above.
2. **Escape everything interpolated into HTML.** Source documents are untrusted
   input — a real contract can contain `<script>`. `save_translation()` runs
   every value through `html.escape`.
3. **Extraction failures raise `ExtractionError`; they never return `""`.** An
   empty string is indistinguishable from a genuinely empty document.
4. **Batch and single-file paths share one extractor.** `batch_translate.py`
   calls `translate_document_from_file()`. It must never `open()` a document
   itself — that's how PDFs got read as raw bytes.

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
