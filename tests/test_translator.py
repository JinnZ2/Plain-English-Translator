"""Regression tests for Plain English Translator.

Each test in `TestFalsifiedClaims` pins a defect that was found by running the
tool rather than by reading it. The docstrings name the claim that was believed
true and the observation that falsified it, so a future reader can tell an
intentional guarantee from an accident of implementation.
"""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from translator import (  # noqa: E402
    EnhancedPlainEnglishTranslator,
    ExtractionError,
    PlainEnglishTranslator,
    TranslationResult,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

MEDICAL_TEXT = (
    "DISCHARGE SUMMARY\n"
    "Patient presents with acute myocardial infarction and hypertension.\n"
    "Prognosis is guarded. Follow up with the physician in 2 weeks.\n"
)

LEGAL_TEXT = (
    "LEASE AGREEMENT\n"
    "Whereas the tenant shall indemnify the landlord for all claims.\n"
    "Tenant waives right to jury trial. Arbitration is mandatory.\n"
    "Payment is due within 30 days.\n"
)


@pytest.fixture
def translator():
    return EnhancedPlainEnglishTranslator()


class TestFalsifiedClaims:
    """One test per hypothesis that running the code proved false."""

    def test_module_imports_without_optional_dependencies(self):
        """Claim: "translator.py works for .txt on a bare install."

        Falsified: `import PyPDF2` / `import fitz` / `from docx import Document`
        sat at module top level, so every entry point — CLI, batch, examples —
        died with ModuleNotFoundError before reading a single document.

        Run in a subprocess with the PDF/DOCX modules blocked, proving the
        import is genuinely lazy rather than merely satisfied by the test env.
        """
        blocker = (
            "import sys\n"
            "class Block:\n"
            "    def find_module(self, name, path=None):\n"
            "        if name in ('PyPDF2', 'fitz', 'pymupdf', 'docx'):\n"
            "            raise ImportError(name)\n"
            "sys.meta_path.insert(0, Block())\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "import translator\n"
            "t = translator.EnhancedPlainEnglishTranslator()\n"
            f"r = t.translate_document({MEDICAL_TEXT!r})\n"
            "assert r.document_type == 'medical', r.document_type\n"
            "print('OK')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", blocker],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
        assert "OK" in proc.stdout

    def test_html_report_escapes_document_markup(self, translator, tmp_path, monkeypatch):
        """Claim: "the HTML report is safe to open."

        Falsified: document text was interpolated into the report unescaped, so
        a contract containing `<script>alert(1)</script>` produced a report that
        executed it. Source documents are untrusted input.
        """
        monkeypatch.chdir(tmp_path)
        hostile = LEGAL_TEXT + "\nThe tenant <script>alert(1)</script> agrees.\n"
        result = translator.translate_document(hostile)
        out = translator.save_translation(result, "hostile")

        rendered = out.read_text(encoding="utf-8")
        assert "<script>alert(1)</script>" not in rendered
        assert "&lt;script&gt;" in rendered

    def test_html_report_escapes_ampersands(self, translator, tmp_path, monkeypatch):
        """Bare `&` in a document must not corrupt the report's markup."""
        monkeypatch.chdir(tmp_path)
        text = LEGAL_TEXT + "\nArbitration is mandatory & binding on both parties.\n"
        result = translator.translate_document(text)
        rendered = translator.save_translation(result, "amp").read_text(encoding="utf-8")

        assert "mandatory &amp; binding" in rendered

    def test_unreadable_pdf_raises_instead_of_returning_empty(self, translator, tmp_path):
        """Claim: "a failed extraction is reported."

        Falsified: extractors caught every exception and returned `""`, which is
        indistinguishable from a genuinely empty document. Callers treated the
        empty string as success.
        """
        fake = tmp_path / "not-really.pdf"
        fake.write_bytes(b"this is not a PDF at all")

        with pytest.raises(ExtractionError):
            translator.extract_text_from_pdf(str(fake))

    def test_batch_does_not_read_binary_as_text(self, tmp_path):
        """Claim: "batch_translate.py supports the documented formats."

        Falsified: README documents `batch_translate.py documents/*.pdf`, but
        process_file used open(..., 'r', errors='ignore') on every path. A PDF
        was decoded as mojibake and reported as "✅ success, 70% confidence"
        with a report full of `obj`/`endstream`/`FlateDecode` and no document
        text. A silent wrong answer, not a crash.
        """
        pymupdf = pytest.importorskip("pymupdf")

        pdf_path = tmp_path / "policy.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 100), "INSURANCE POLICY", fontsize=14)
        page.insert_text(
            (72, 130),
            "Coverage excludes pre-existing conditions. Deductible applies.",
            fontsize=10,
        )
        page.insert_text(
            (72, 150),
            "The insurer may rescind this policy. You may appeal within 30 days.",
            fontsize=10,
        )
        doc.save(str(pdf_path))
        doc.close()

        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "batch_translate.py"), str(pdf_path), "-d", "0"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert proc.returncode == 0, proc.stderr

        report = tmp_path / "translations" / "batch_policy.html"
        assert report.exists(), proc.stdout
        rendered = report.read_text(encoding="utf-8")

        # Real document content, not PDF container internals.
        assert "Deductible" in rendered
        for marker in ("FlateDecode", "endstream", "endobj"):
            assert marker not in rendered, f"PDF internals leaked into report: {marker}"


class TestDocumentTypeDetection:
    @pytest.mark.parametrize(
        "text,expected",
        [
            (MEDICAL_TEXT, "medical"),
            (LEGAL_TEXT, "legal"),
            (
                "Your insurance policy has a deductible and copay. "
                "Prior authorization is required before the insurer pays a claim.",
                "insurance",
            ),
            (
                "This loan agreement sets the APR. The borrower owes the lender "
                "principal plus interest on the mortgage debt.",
                "financial",
            ),
        ],
    )
    def test_detects_domain(self, translator, text, expected):
        assert translator.detect_document_type(text) == expected

    def test_unknown_domain_falls_back_to_general(self, translator):
        assert translator.detect_document_type("The cat sat on a warm flat rock.") == "general"


class TestTranslation:
    def test_jargon_is_replaced_and_original_kept(self, translator):
        result = translator.translate_document(MEDICAL_TEXT)
        assert "heart attack" in result.plain_english
        # The original term stays in parentheses so nothing is lost.
        assert "myocardial infarction" in result.plain_english

    def test_returns_translation_result(self, translator):
        result = translator.translate_document(MEDICAL_TEXT)
        assert isinstance(result, TranslationResult)
        assert 0.1 <= result.confidence_score <= 0.95

    def test_short_text_is_rejected(self, translator):
        with pytest.raises(ValueError):
            translator.translate_document("Too short.")

    def test_legal_document_yields_action_items(self, translator):
        result = translator.translate_document(LEGAL_TEXT)
        assert result.action_items
        assert any("30 days" in item for item in result.action_items)

    def test_unsupported_extension_is_rejected(self, translator, tmp_path):
        bad = tmp_path / "notes.rtf"
        bad.write_text("some text that is long enough to pass the length check ok")
        with pytest.raises(ValueError):
            translator.translate_document_from_file(str(bad))

    def test_txt_roundtrip_sets_source_file(self, translator, tmp_path):
        path = tmp_path / "summary.txt"
        path.write_text(MEDICAL_TEXT, encoding="utf-8")
        result = translator.translate_document_from_file(str(path))
        assert result.source_file == str(path)
        assert result.document_type == "medical"


class TestBackwardsCompatibility:
    def test_alias_points_at_the_real_class(self):
        """`PlainEnglishTranslator` was briefly bound to None at import time."""
        assert PlainEnglishTranslator is EnhancedPlainEnglishTranslator
        assert PlainEnglishTranslator() is not None
