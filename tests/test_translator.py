"""Tests for the Plain English Translator."""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import tempfile

# Add parent dir to path so we can import translator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator import (
    EnhancedPlainEnglishTranslator,
    PlainEnglishTranslator,
    TranslationResult,
    DISCLAIMER,
    _print_result,
    _try_ollama_enhance,
)


@pytest.fixture
def translator():
    return EnhancedPlainEnglishTranslator()


# --- Basic Initialization ---

class TestInit:
    def test_creates_instance(self, translator):
        assert translator is not None

    def test_has_jargon_dictionary(self, translator):
        assert isinstance(translator.jargon_dictionary, dict)

    def test_has_all_domains(self, translator):
        expected = {'medical', 'legal', 'insurance', 'financial', 'government'}
        assert expected == set(translator.jargon_dictionary.keys())

    def test_has_document_patterns(self, translator):
        assert isinstance(translator.document_patterns, dict)
        assert 'government' in translator.document_patterns

    def test_has_sneaky_patterns(self, translator):
        assert isinstance(translator.sneaky_patterns, dict)
        assert 'sneaky_government' in translator.sneaky_patterns

    def test_backwards_compat_alias(self):
        assert PlainEnglishTranslator is EnhancedPlainEnglishTranslator


# --- Document Type Detection ---

class TestDocumentTypeDetection:
    def test_detects_medical(self, translator):
        text = """Patient was admitted with myocardial infarction. The physician
        ordered medication and the diagnosis was confirmed. The hospital discharge
        summary includes treatment notes from the doctor and nurse."""
        assert translator.detect_document_type(text) == 'medical'

    def test_detects_legal(self, translator):
        text = """Whereas the party agrees to this contract, the agreement shall be
        binding. The tenant and landlord hereby covenant that arbitration shall apply.
        Attorney fees and jurisdiction are specified in this lease."""
        assert translator.detect_document_type(text) == 'legal'

    def test_detects_insurance(self, translator):
        text = """This insurance policy outlines your coverage, deductible, and premium.
        The insured must obtain prior authorization. Copay and coinsurance rates
        apply. Claims must be filed with the insurer within the network."""
        assert translator.detect_document_type(text) == 'insurance'

    def test_detects_financial(self, translator):
        text = """This loan agreement specifies the interest rate, payment schedule,
        and credit terms. The borrower and lender agree to the mortgage APR.
        The bank will hold the principal in escrow."""
        assert translator.detect_document_type(text) == 'financial'

    def test_detects_government(self, translator):
        text = """Your Social Security benefits eligibility determination has been
        completed. The federal agency has reviewed your application for supplemental
        security income. Your SNAP and Medicaid benefits will continue."""
        assert translator.detect_document_type(text) == 'government'

    def test_returns_general_for_unknown(self, translator):
        text = "The quick brown fox jumps over the lazy dog. " * 5
        assert translator.detect_document_type(text) == 'general'

    def test_bonus_phrases_insurance(self, translator):
        text = "This explanation of benefits shows your insurance policy details. " * 5
        assert translator.detect_document_type(text) == 'insurance'

    def test_bonus_phrases_government(self, translator):
        text = "This notice of action regarding your food stamps and section 8 housing authority benefits. " * 5
        assert translator.detect_document_type(text) == 'government'


# --- Jargon Translation ---

class TestJargonTranslation:
    def test_translates_medical_jargon(self, translator):
        result = translator.translate_jargon("The patient has hypertension.", 'medical')
        assert 'high blood pressure' in result
        assert 'hypertension' in result  # keeps original in parens

    def test_translates_legal_jargon(self, translator):
        result = translator.translate_jargon("This is pursuant to the agreement.", 'legal')
        assert 'according to' in result

    def test_translates_insurance_jargon(self, translator):
        result = translator.translate_jargon("Your deductible is $500.", 'insurance')
        assert 'amount you pay before insurance kicks in' in result

    def test_translates_financial_jargon(self, translator):
        result = translator.translate_jargon("The variable rate may increase.", 'financial')
        assert 'interest rate can go up' in result

    def test_translates_government_jargon(self, translator):
        result = translator.translate_jargon("Your determination is pending.", 'government')
        assert 'official decision on your eligibility' in result

    def test_no_translation_for_unknown_domain(self, translator):
        text = "Hello world, this is a test."
        result = translator.translate_jargon(text, 'unknown_domain')
        assert result == text

    def test_case_insensitive(self, translator):
        result = translator.translate_jargon("The patient has HYPERTENSION.", 'medical')
        assert 'high blood pressure' in result


# --- Red Flag Detection ---

class TestRedFlags:
    def test_finds_medical_red_flags(self, translator):
        text = "This is an experimental treatment. It has a black box warning."
        flags = translator.find_red_flags(text, 'medical')
        assert len(flags) >= 1

    def test_finds_legal_red_flags(self, translator):
        text = "You waive your right. Binding arbitration applies. Class action waiver."
        flags = translator.find_red_flags(text, 'legal')
        assert len(flags) >= 1

    def test_finds_insurance_red_flags(self, translator):
        text = "Pre-existing condition exclusion. Not medically necessary denial."
        flags = translator.find_red_flags(text, 'insurance')
        assert len(flags) >= 1

    def test_finds_financial_red_flags(self, translator):
        text = "This loan has a balloon payment and prepayment penalty."
        flags = translator.find_red_flags(text, 'financial')
        assert len(flags) >= 1

    def test_finds_government_red_flags(self, translator):
        text = "Your benefits terminated due to overpayment. You must repay."
        flags = translator.find_red_flags(text, 'government')
        assert len(flags) >= 1

    def test_flags_have_emoji(self, translator):
        text = "This is an experimental treatment."
        flags = translator.find_red_flags(text, 'medical')
        if flags:
            assert flags[0].startswith('⚠️')


# --- Sneaky Clause Detection ---

class TestSneakyClauses:
    def test_detects_legal_sneaky(self, translator):
        text = "You waive your right to a jury trial and class action."
        clauses = translator.detect_sneaky_clauses(text, 'legal')
        assert len(clauses) >= 1

    def test_detects_insurance_sneaky(self, translator):
        text = "Treatment deemed not medically necessary will be denied."
        clauses = translator.detect_sneaky_clauses(text, 'insurance')
        assert len(clauses) >= 1

    def test_detects_financial_sneaky(self, translator):
        text = "The variable rate may increase to 25% after introductory period."
        clauses = translator.detect_sneaky_clauses(text, 'financial')
        assert len(clauses) >= 1

    def test_detects_government_sneaky(self, translator):
        text = "Failure to report income will result in termination of benefits."
        clauses = translator.detect_sneaky_clauses(text, 'government')
        assert len(clauses) >= 1

    def test_sneaky_has_emoji(self, translator):
        text = "You waive your right to a jury trial."
        clauses = translator.detect_sneaky_clauses(text, 'legal')
        if clauses:
            assert '🚨' in clauses[0]


# --- Rights Extraction ---

class TestRightsExtraction:
    def test_finds_medical_rights(self, translator):
        text = "You have the right to refuse treatment. Ask for a second opinion."
        rights = translator.extract_rights(text, 'medical')
        assert len(rights) >= 1

    def test_finds_legal_rights(self, translator):
        text = "You have a right to cancel within the cooling off period."
        rights = translator.extract_rights(text, 'legal')
        assert len(rights) >= 1

    def test_finds_government_rights(self, translator):
        text = "You have the right to appeal. Request a fair hearing."
        rights = translator.extract_rights(text, 'government')
        assert len(rights) >= 1

    def test_rights_have_emoji(self, translator):
        text = "You have the right to refuse treatment."
        rights = translator.extract_rights(text, 'medical')
        if rights:
            assert rights[0].startswith('✅')


# --- Action Items ---

class TestActionItems:
    def test_medical_actions(self, translator):
        text = "There may be side effects. Consider an alternative treatment."
        actions = translator.generate_action_items(text, 'medical')
        assert len(actions) >= 1

    def test_insurance_actions(self, translator):
        text = "Your policy details are enclosed."
        actions = translator.generate_action_items(text, 'insurance')
        assert len(actions) >= 1

    def test_legal_actions(self, translator):
        text = "Please review the contract terms."
        actions = translator.generate_action_items(text, 'legal')
        assert len(actions) >= 1

    def test_government_actions(self, translator):
        text = "Your appeal must be filed. You have an overpayment. Request a hearing."
        actions = translator.generate_action_items(text, 'government')
        assert len(actions) >= 3  # appeal + overpayment + hearing

    def test_deadline_detection(self, translator):
        text = "You must respond within 30 days."
        actions = translator.generate_action_items(text, 'legal')
        deadline_actions = [a for a in actions if '📅' in a]
        assert len(deadline_actions) >= 1


# --- Confidence Score ---

class TestConfidenceScore:
    def test_returns_float(self, translator):
        score = translator.calculate_confidence("Test text " * 20, 'medical')
        assert isinstance(score, float)

    def test_between_0_and_1(self, translator):
        score = translator.calculate_confidence("Test " * 50, 'medical')
        assert 0.1 <= score <= 0.95

    def test_known_type_scores_higher(self, translator):
        text = "Patient diagnosis treatment medication physician hospital. " * 5
        known = translator.calculate_confidence(text, 'medical')
        unknown = translator.calculate_confidence(text, 'general')
        assert known > unknown

    def test_short_text(self, translator):
        score = translator.calculate_confidence("Short text here.", 'medical')
        assert 0.1 <= score <= 0.95

    def test_very_long_text(self, translator):
        score = translator.calculate_confidence("Word " * 5000, 'medical')
        assert 0.1 <= score <= 0.95


# --- Full Translation ---

class TestTranslateDocument:
    def test_full_medical_translation(self, translator):
        text = """Patient presented with acute myocardial infarction and hypertension.
        The physician recommended experimental treatment with a black box warning.
        The patient has the right to refuse treatment and seek a second opinion.
        Treatment must begin within 14 days."""
        result = translator.translate_document(text)
        assert isinstance(result, TranslationResult)
        assert result.document_type == 'medical'
        assert 'heart attack' in result.plain_english
        assert len(result.red_flags) >= 1
        assert result.confidence_score > 0

    def test_full_legal_translation(self, translator):
        text = """Whereas the party agrees, pursuant to this agreement, the tenant hereby
        covenants to binding arbitration with a class action waiver. Attorney fees
        shall be borne by the losing party. The contract includes automatic renewal
        unless you actively cancel within 30 days."""
        result = translator.translate_document(text)
        assert isinstance(result, TranslationResult)
        assert result.document_type == 'legal'
        assert len(result.red_flags) >= 1

    def test_full_government_translation(self, translator):
        text = """Your Social Security disability determination has been completed by the
        federal agency. Your supplemental security income benefits eligibility
        depends on your income. You have the right to appeal this determination
        and request a fair hearing within 60 days. Your SNAP and Medicaid
        benefits will not be affected."""
        result = translator.translate_document(text)
        assert isinstance(result, TranslationResult)
        assert result.document_type == 'government'
        assert len(result.action_items) >= 1

    def test_rejects_short_text(self, translator):
        with pytest.raises(ValueError, match="too short"):
            translator.translate_document("Hi")

    def test_rejects_empty_text(self, translator):
        with pytest.raises(ValueError):
            translator.translate_document("")

    def test_source_file_empty_for_text(self, translator):
        text = "Patient with hypertension and chronic illness treatment. " * 5
        result = translator.translate_document(text)
        assert result.source_file == ""


# --- File Translation ---

class TestTranslateFromFile:
    def test_reads_txt_file(self, translator):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False,
                                          encoding='utf-8') as f:
            f.write("Patient presented with acute myocardial infarction and hypertension. " * 5)
            f.flush()
            result = translator.translate_document_from_file(f.name)
            assert result.source_file == f.name
            assert result.document_type == 'medical'
        os.unlink(f.name)

    def test_rejects_unsupported_format(self, translator):
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"data")
        with pytest.raises(ValueError, match="Unsupported file type"):
            translator.translate_document_from_file(f.name)
        os.unlink(f.name)


# --- Key Points Extraction ---

class TestKeyPoints:
    def test_numbered_items(self, translator):
        text = "1. Important first point. 2. Second important point. 3. Third point."
        points = translator.extract_key_points(text)
        assert len(points) >= 1

    def test_bullet_items(self, translator):
        text = "- First bullet point\n- Second bullet point\n- Third bullet"
        points = translator.extract_key_points(text)
        assert len(points) >= 1

    def test_emphasis_words(self, translator):
        text = "It is important that you follow up. This is required by law."
        points = translator.extract_key_points(text)
        assert len(points) >= 1

    def test_short_items_excluded(self, translator):
        text = "1. Hi. 2. Ok."
        points = translator.extract_key_points(text)
        assert len(points) == 0  # too short


# --- Side-by-Side Translation ---

class TestSideBySide:
    def test_returns_list_of_dicts(self, translator):
        text = "The patient has hypertension. Treatment is contraindicated."
        pairs = translator.translate_side_by_side(text, 'medical')
        assert isinstance(pairs, list)
        assert all(isinstance(p, dict) for p in pairs)
        assert all('original' in p and 'plain' in p for p in pairs)

    def test_auto_detects_type(self, translator):
        text = "Patient diagnosed with acute myocardial infarction at the hospital. " * 3
        pairs = translator.translate_side_by_side(text)
        assert len(pairs) >= 1

    def test_translates_jargon_in_pairs(self, translator):
        text = "The patient has hypertension."
        pairs = translator.translate_side_by_side(text, 'medical')
        assert any('high blood pressure' in p['plain'] for p in pairs)


# --- Spanish Output ---

class TestSpanishOutput:
    def test_returns_dict(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        spanish = translator.translate_to_spanish(result)
        assert isinstance(spanish, dict)

    def test_has_disclaimer(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        spanish = translator.translate_to_spanish(result)
        assert 'disclaimer' in spanish
        assert 'AVISO' in spanish['disclaimer']

    def test_has_document_type(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        spanish = translator.translate_to_spanish(result)
        assert spanish['document_type'] == 'Médico'


# --- Ojibwe Output ---

class TestOjibweOutput:
    def test_returns_dict(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert isinstance(ojibwe, dict)

    def test_has_language_name(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert 'Anishinaabemowin' in ojibwe['language_name']

    def test_has_disclaimer(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert 'disclaimer' in ojibwe
        assert len(ojibwe['disclaimer']) > 20

    def test_has_document_type(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert ojibwe['document_type'] == 'Mashkiki'  # Medicine

    def test_has_concepts(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert 'concepts' in ojibwe
        assert 'heart attack' in ojibwe['concepts']
        assert 'water' in ojibwe['concepts']

    def test_has_section_headers(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        ojibwe = translator.translate_to_ojibwe(result)
        assert 'section_headers' in ojibwe
        assert 'Your Rights' in ojibwe['section_headers']


# --- Navajo Output ---

class TestNavajoOutput:
    def test_returns_dict(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert isinstance(navajo, dict)

    def test_has_language_name(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert 'Diné Bizaad' in navajo['language_name']

    def test_has_disclaimer(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert 'disclaimer' in navajo
        assert len(navajo['disclaimer']) > 20

    def test_has_document_type(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert navajo['document_type'] == "Azee'"  # Medicine

    def test_has_concepts(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert 'concepts' in navajo
        assert 'water' in navajo['concepts']
        assert navajo['concepts']['water'] == 'tó'

    def test_has_section_headers(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        navajo = translator.translate_to_navajo(result)
        assert 'section_headers' in navajo
        assert 'Government' in navajo['section_headers']


# --- Cherokee Output ---

class TestCherokeeOutput:
    def test_returns_dict(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        assert isinstance(cherokee, dict)

    def test_has_language_name(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        assert 'Cherokee' in cherokee['language_name']
        assert 'ᏣᎳᎩ' in cherokee['language_name']

    def test_has_disclaimer(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        assert 'disclaimer' in cherokee
        assert len(cherokee['disclaimer']) > 20

    def test_has_syllabary(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        # Check that Cherokee syllabary characters are present
        assert 'ᏣᎳᎩ' in cherokee['language_name']
        # Check concepts have syllabary
        assert any('Ꭰ' in v or 'Ꮎ' in v or 'Ꮕ' in v
                    for v in cherokee['concepts'].values())

    def test_has_concepts(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        assert 'concepts' in cherokee
        assert 'water' in cherokee['concepts']
        assert 'ama' in cherokee['concepts']['water']

    def test_has_section_headers(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        cherokee = translator.translate_to_cherokee(result)
        assert 'section_headers' in cherokee
        assert 'Medical' in cherokee['section_headers']


# --- HTML Output ---

class TestSaveTranslation:
    def test_creates_html_file(self, translator):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                translator.save_translation(result, "test_output")
                output = Path(tmpdir) / "translations" / "test_output.html"
                assert output.exists()
                content = output.read_text()
                assert 'DISCLAIMER' in content
                assert 'Plain English Translation' in content
            finally:
                os.chdir(orig_cwd)


# --- Disclaimer ---

class TestDisclaimer:
    def test_disclaimer_exists(self):
        assert DISCLAIMER
        assert 'NOT' in DISCLAIMER
        assert 'legal' in DISCLAIMER.lower()
        assert 'medical' in DISCLAIMER.lower()

    def test_disclaimer_in_html(self, translator):
        text = "Patient has hypertension. " * 5
        result = translator.translate_document(text)
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                translator.save_translation(result, "disc_test")
                content = (Path(tmpdir) / "translations" / "disc_test.html").read_text()
                assert 'DISCLAIMER' in content
            finally:
                os.chdir(orig_cwd)


# --- Ollama Integration ---

class TestOllamaIntegration:
    def test_returns_none_when_unavailable(self):
        # Ollama is not running in test env
        result = _try_ollama_enhance("test text", "medical")
        assert result is None

    @patch('urllib.request.urlopen')
    def test_returns_response_when_available(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"response": "Simple version"}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = _try_ollama_enhance("complex medical text", "medical")
        assert result == "Simple version"


# --- Print Result ---

class TestPrintResult:
    def test_prints_without_error(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result)
        captured = capsys.readouterr()
        assert 'DISCLAIMER' in captured.out
        assert 'Document Type' in captured.out

    def test_prints_side_by_side(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result, side_by_side=True)
        captured = capsys.readouterr()
        assert 'SIDE-BY-SIDE' in captured.out

    def test_prints_spanish(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result, spanish=True)
        captured = capsys.readouterr()
        assert 'AVISO' in captured.out

    def test_prints_ojibwe(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result, ojibwe=True)
        captured = capsys.readouterr()
        assert 'Anishinaabemowin' in captured.out

    def test_prints_navajo(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result, navajo=True)
        captured = capsys.readouterr()
        assert 'Diné Bizaad' in captured.out

    def test_prints_cherokee(self, translator, capsys):
        text = "Patient has hypertension and chronic conditions. " * 5
        result = translator.translate_document(text)
        _print_result(result, cherokee=True)
        captured = capsys.readouterr()
        assert 'ᏣᎳᎩ' in captured.out


# --- CLI / Main ---

class TestCLI:
    def test_interactive_mode_too_short(self):
        """Interactive mode rejects short input."""
        with patch('builtins.input', side_effect=["hi", ""]):
            with pytest.raises(SystemExit):
                from translator import main
                main()

    def test_file_mode_missing_file(self):
        """File mode fails gracefully for missing files."""
        with patch('sys.argv', ['translator.py', 'nonexistent_file.txt']):
            with pytest.raises(SystemExit):
                from translator import main
                main()
