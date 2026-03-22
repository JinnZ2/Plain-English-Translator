#!/usr/bin/env python3
"""
Enhanced Plain English Translator with PDF support and expanded legal/insurance detection
Now handles PDFs directly and catches more sneaky clauses!
"""

import PyPDF2
import fitz  # PyMuPDF - better PDF extraction
import re
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, List
from pathlib import Path
from docx import Document  # Word document support


@dataclass
class TranslationResult:
    original_text: str
    plain_english: str
    key_points: List[str]
    action_items: List[str]
    red_flags: List[str]
    your_rights: List[str]
    confidence_score: float
    document_type: str
    source_file: str


# Keep the old name as an alias so existing imports work
PlainEnglishTranslator = None  # defined after class


class EnhancedPlainEnglishTranslator:
    def __init__(self):
        self.jargon_dictionary = self._load_jargon_dictionary()
        self.document_patterns = self._load_document_patterns()
        self.sneaky_patterns = self._load_sneaky_patterns()

    def _load_jargon_dictionary(self) -> Dict[str, Dict[str, str]]:
        """Enhanced jargon dictionary with more sneaky terms"""
        return {
            'medical': {
                # Basic terms
                'myocardial infarction': 'heart attack',
                'cerebrovascular accident': 'stroke',
                'hypertension': 'high blood pressure',
                'hypotension': 'low blood pressure',
                'tachycardia': 'fast heart rate (over 100 bpm)',
                'bradycardia': 'slow heart rate (under 60 bpm)',
                'dyspnea': 'trouble breathing or shortness of breath',
                'acute': 'sudden or severe (happening now)',
                'chronic': 'long-term or ongoing (lasting months/years)',
                'benign': 'not cancerous or harmful',
                'malignant': 'cancerous (spreads to other parts)',
                'contraindicated': 'should not be used with',
                'adverse events': 'bad side effects',
                'efficacy': 'how well it works',
                'comorbidity': 'other health problems you have',
                'prognosis': 'what doctors expect to happen',
                'differential diagnosis': 'other possible conditions',
                'prophylactic': 'preventive treatment (to stop problems before they start)',
                'palliative': 'treatment to make you more comfortable (not cure)',
                # More advanced terms
                'informed consent': 'you understand the risks and agree to treatment',
                'off-label use': "using medicine for something it's not officially approved for",
                'experimental treatment': "treatment that's still being tested (not proven safe)",
                'black box warning': "FDA's strongest warning about dangerous side effects",
                'clinical trial': 'research study testing new treatments',
                'placebo': 'fake treatment with no active medicine',
                'double-blind study': 'neither you nor doctor knows if you get real treatment',
                'exclusion criteria': "reasons you can't participate in treatment/study",
                'inclusion criteria': 'requirements to get this treatment',
                'standard of care': 'normal treatment most doctors would recommend',
            },
            'legal': {
                # Basic terms
                'whereas': 'because',
                'heretofore': 'until now',
                'aforementioned': 'mentioned above',
                'pursuant to': 'according to',
                'notwithstanding': 'despite',
                'indemnify': 'protect from legal responsibility (you pay if they get sued)',
                'covenant': 'promise (that you must keep)',
                'remedy': 'solution or compensation',
                'breach': 'breaking the agreement',
                'default': 'failure to meet obligations',
                'force majeure': 'uncontrollable events like natural disasters',
                'arbitration': 'private dispute resolution instead of court',
                'jurisdiction': 'which court system has authority',
                'severability': 'if one part is invalid, the rest still applies',
                # SNEAKY legal terms that screw people over
                'binding arbitration': 'you give up your right to sue in court (huge disadvantage)',
                'class action waiver': "you can't join group lawsuits (you're on your own)",
                'attorney fees clause': 'if you lose, you pay their lawyer costs too',
                'personal guarantee': "you're personally responsible even if business fails",
                'unlimited liability': 'no limit on how much you could owe',
                'confession of judgment': 'they can get court judgment without trial',
                'waive jury trial': 'judge decides, not jury (usually worse for individuals)',
                'integration clause': "only this written contract counts (verbal promises don't matter)",
                'modification clause': "they can change terms, you can't",
                'automatic renewal': 'contract continues unless you actively cancel',
                'liquidated damages': 'penalty fees that might be way more than actual harm',
                'acceleration clause': 'entire debt becomes due immediately if you miss payment',
                'cross-default': 'if you fail on any other loan, this one becomes due too',
                'dragnet clause': 'this collateral also secures other debts you might owe them',
            },
            'insurance': {
                # Basic terms
                'deductible': 'amount you pay before insurance kicks in',
                'copay': 'fixed amount you pay for each service ($20 per visit)',
                'coinsurance': 'percentage you pay after deductible (you pay 20%, they pay 80%)',
                'out-of-pocket maximum': "most you'll pay in a year (then insurance pays 100%)",
                'pre-authorization': 'insurance approval needed before treatment',
                'formulary': 'list of covered medications',
                'prior authorization': 'must get approval before insurance pays',
                'exclusion': 'something not covered (you pay full price)',
                'rider': 'add-on coverage (costs extra)',
                'underwriting': 'process of deciding coverage and price',
                'claim': 'request for payment',
                'premium': 'monthly payment for coverage',
                'network': 'doctors and hospitals that accept your insurance',
                # SNEAKY insurance terms
                'pre-existing condition exclusion': "they won't cover health problems you already had",
                'experimental treatment exclusion': "they won't pay for newer treatments",
                'not medically necessary': 'insurance excuse to deny claims',
                'out of network penalty': 'you pay much more for non-network doctors',
                'lifetime maximum': 'they stop paying after you reach this limit',
                'rescission': 'they can cancel your policy and demand money back',
                'step therapy': 'must try cheaper treatments first',
                'narrow network': 'very limited choice of doctors',
                'surprise billing': 'out-of-network doctor at in-network hospital bills you',
                'balance billing': "doctor bills you for amount insurance didn't pay",
                'coordination of benefits': 'if you have two insurances, both try to pay less',
                'claims review': 'they can reject claims after initially approving them',
                'renewal restrictions': 'they can refuse to renew your policy',
                'waiting period': 'time you must wait before coverage starts',
                'elimination period': 'time before disability benefits start paying',
            },
            'financial': {
                # Basic terms
                'apr': 'annual percentage rate - true yearly cost of borrowing',
                'compound interest': 'interest that earns interest (grows fast!)',
                'amortization': 'paying off debt gradually over time',
                'escrow': 'money held by third party until conditions are met',
                'equity': 'ownership value (what you actually own)',
                'liquidity': 'how easily you can convert to cash',
                'diversification': 'spreading investments to reduce risk',
                'volatility': 'how much prices swing up and down',
                'yield': 'return on investment',
                'maturity': 'when investment or loan ends',
                # SNEAKY financial terms
                'variable rate': 'interest rate can go up (sometimes a lot)',
                'balloon payment': 'huge final payment that might be unaffordable',
                'prepayment penalty': 'fee for paying off loan early',
                'universal default': "if you're late anywhere, all your rates go up",
                'negative amortization': 'your debt grows even while making payments',
                'yield spread premium': 'broker gets paid more for giving you worse rate',
                'teaser rate': 'low introductory rate that jumps up later',
                'payment shock': 'when low payments suddenly become much higher',
                'recourse debt': 'they can come after your other assets if you default',
                'cross-collateralization': 'one asset secures multiple loans',
            }
        }

    def _load_document_patterns(self) -> Dict[str, Dict]:
        """Enhanced patterns including sneaky clauses"""
        return {
            'medical': {
                'red_flag_phrases': [
                    'experimental', 'off-label use', 'not fda approved',
                    'investigational', 'may cause death', 'black box warning',
                    'irreversible', 'permanent damage', 'clinical trial',
                    'research study', 'no guarantee', 'terminal',
                    'palliative only', 'comfort care', 'do not resuscitate'
                ],
                'rights_indicators': [
                    'right to refuse', 'second opinion', 'medical records',
                    'privacy', 'informed consent', 'patient advocate',
                    'interpreter services', 'advance directive', 'living will',
                    'healthcare proxy', 'discharge against medical advice'
                ]
            },
            'legal': {
                'red_flag_phrases': [
                    # Classic sneaky stuff
                    'waive', 'forfeit', 'binding arbitration', 'class action waiver',
                    'attorney fees', 'liquidated damages', 'personal guarantee',
                    'unlimited liability', 'confession of judgment', 'waive jury trial',
                    # More subtle traps
                    'automatic renewal', 'integration clause', 'modification clause',
                    'acceleration clause', 'cross-default', 'dragnet clause',
                    'hold harmless', 'indemnification', 'venue selection',
                    'choice of law', 'mandatory arbitration', 'class action ban',
                    'jury trial waiver', 'unilateral modification', 'termination at will'
                ],
                'rights_indicators': [
                    'right to cancel', 'cooling off period', 'dispute resolution',
                    'modification', 'termination clause', 'notice period',
                    'cure period', 'right to cure', 'mitigation',
                    'reasonable attorney fees', 'prevailing party'
                ]
            },
            'insurance': {
                'red_flag_phrases': [
                    # Classic exclusions
                    'pre-existing condition exclusion', 'experimental treatment',
                    'not medically necessary', 'out of network penalty',
                    'lifetime maximum', 'rescission', 'step therapy',
                    # Sneaky billing traps
                    'balance billing', 'surprise billing', 'narrow network',
                    'prior authorization required', 'claims review',
                    'coordination of benefits', 'renewal restrictions',
                    'waiting period', 'elimination period', 'benefit reduction'
                ],
                'rights_indicators': [
                    'appeal process', 'external review', 'grievance procedure',
                    'covered services', 'network adequacy', 'emergency services',
                    'continuity of care', 'provider directory', 'formulary exception'
                ]
            },
            'financial': {
                'red_flag_phrases': [
                    'variable rate', 'balloon payment', 'prepayment penalty',
                    'universal default', 'negative amortization', 'yield spread premium',
                    'teaser rate', 'payment shock', 'recourse debt',
                    'cross-collateralization', 'floating rate', 'margin call',
                    'acceleration clause', 'call provision', 'penalty apr'
                ],
                'rights_indicators': [
                    'right of rescission', 'truth in lending', 'fair credit reporting',
                    'dispute resolution', 'billing error rights', 'privacy rights'
                ]
            }
        }

    def _load_sneaky_patterns(self) -> Dict[str, List[str]]:
        """Patterns specifically designed to catch sneaky clauses"""
        return {
            'sneaky_legal': [
                r'you (?:waive|forfeit|give up|relinquish)',
                r'binding arbitration.*class action',
                r'attorney.*fees.*prevailing party',
                r'personal.*guarantee.*unlimited',
                r'automatic.*renew.*unless.*cancel',
                r'modify.*terms.*without.*notice',
                r'entire.*amount.*immediately.*due'
            ],
            'sneaky_insurance': [
                r'not.*medically.*necessary',
                r'experimental.*investigational',
                r'pre-existing.*condition.*exclusion',
                r'out.*network.*penalty.*(\d+)%',
                r'prior.*authorization.*required.*or.*denied',
                r'lifetime.*maximum.*(\$[\d,]+)',
                r'rescission.*misrepresentation'
            ],
            'sneaky_financial': [
                r'variable.*rate.*may.*increase',
                r'balloon.*payment.*(\$[\d,]+)',
                r'prepayment.*penalty.*(\d+).*months',
                r'teaser.*rate.*(\d+\.\d+)%.*then.*(\d+\.\d+)%',
                r'negative.*amortization',
                r'universal.*default.*clause'
            ]
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods for best results"""
        text = ""

        try:
            # Try PyMuPDF first (better for complex layouts)
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()

            # If we got good text, return it
            if len(text.strip()) > 100:
                return text

        except Exception as e:
            print(f"PyMuPDF failed: {e}, trying PyPDF2...")

        try:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()

        except Exception as e:
            print(f"PyPDF2 also failed: {e}")
            return ""

        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading Word document: {e}")
            return ""

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types"""
        file_path = Path(file_path)

        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return self.extract_text_from_docx(str(file_path))
        elif file_path.suffix.lower() in ['.txt', '.text']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def detect_sneaky_clauses(self, text: str, document_type: str) -> List[str]:
        """Detect sneaky clauses using regex patterns"""
        sneaky_clauses = []

        if document_type in ['legal', 'insurance', 'financial']:
            pattern_key = f'sneaky_{document_type}'
            if pattern_key in self.sneaky_patterns:
                for pattern in self.sneaky_patterns[pattern_key]:
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end].strip()
                        sneaky_clauses.append(f"🚨 SNEAKY CLAUSE: {context}")

        return sneaky_clauses

    def detect_document_type(self, text: str) -> str:
        """Enhanced document type detection"""
        text_lower = text.lower()

        medical_keywords = [
            'patient', 'diagnosis', 'treatment', 'medication', 'physician',
            'hospital', 'doctor', 'nurse', 'surgery', 'prescription',
            'discharge', 'clinic', 'medical', 'health', 'symptom'
        ]
        legal_keywords = [
            'whereas', 'party', 'agreement', 'contract', 'hereby', 'covenant',
            'shall', 'tenant', 'landlord', 'lease', 'employment', 'attorney',
            'court', 'jurisdiction', 'arbitration', 'liability'
        ]
        insurance_keywords = [
            'policy', 'coverage', 'deductible', 'premium', 'claim', 'beneficiary',
            'insured', 'insurer', 'copay', 'coinsurance', 'network', 'authorization'
        ]
        financial_keywords = [
            'loan', 'interest', 'payment', 'credit', 'debt', 'mortgage',
            'apr', 'finance', 'bank', 'borrower', 'lender', 'principal'
        ]

        scores = {
            'medical': sum(2 if word in text_lower else 0 for word in medical_keywords),
            'legal': sum(2 if word in text_lower else 0 for word in legal_keywords),
            'insurance': sum(2 if word in text_lower else 0 for word in insurance_keywords),
            'financial': sum(2 if word in text_lower else 0 for word in financial_keywords)
        }

        # Bonus points for specific phrases
        if 'insurance policy' in text_lower or 'explanation of benefits' in text_lower:
            scores['insurance'] += 5
        if 'rental agreement' in text_lower or 'lease agreement' in text_lower:
            scores['legal'] += 5
        if 'discharge summary' in text_lower or 'medical record' in text_lower:
            scores['medical'] += 5
        if 'loan agreement' in text_lower or 'credit card' in text_lower:
            scores['financial'] += 5

        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'

    def translate_document(self, text: str) -> TranslationResult:
        """Translate a document from raw text"""
        if not text or len(text.strip()) < 50:
            raise ValueError("Text is too short to translate meaningfully")

        document_type = self.detect_document_type(text)
        plain_text = self.translate_jargon(text, document_type)
        key_points = self.extract_key_points(text)
        red_flags = self.find_red_flags(text, document_type)
        sneaky_clauses = self.detect_sneaky_clauses(text, document_type)
        rights = self.extract_rights(text, document_type)
        actions = self.generate_action_items(text, document_type)
        confidence = self.calculate_confidence(text, document_type)

        all_red_flags = red_flags + sneaky_clauses

        return TranslationResult(
            original_text=text,
            plain_english=plain_text,
            key_points=key_points,
            action_items=actions,
            red_flags=all_red_flags,
            your_rights=rights,
            confidence_score=confidence,
            document_type=document_type,
            source_file=""
        )

    def translate_document_from_file(self, file_path: str) -> TranslationResult:
        """Translate a document from a file path"""
        text = self.extract_text_from_file(file_path)

        if not text or len(text.strip()) < 50:
            raise ValueError(f"Could not extract meaningful text from {file_path}")

        result = self.translate_document(text)
        # Override source_file with the actual path
        result.source_file = str(file_path)
        return result

    def translate_jargon(self, text: str, document_type: str) -> str:
        """Replace jargon with plain English"""
        if document_type not in self.jargon_dictionary:
            return text

        translated = text
        for jargon, plain in self.jargon_dictionary[document_type].items():
            pattern = r'\b' + re.escape(jargon) + r'\b'
            replacement = f"{plain} ({jargon})"
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)

        return translated

    def extract_key_points(self, text: str) -> List[str]:
        """Extract the most important information"""
        key_points = []

        # Find numbered items
        numbered_items = re.findall(r'\d+\.\s*([^\.]+(?:\.[^0-9][^\.]*)*)', text)
        key_points.extend(numbered_items[:5])

        # Find bullet points
        bullet_items = re.findall(r'[•\-\*]\s*([^\n]+)', text)
        key_points.extend(bullet_items[:3])

        # Find sentences with emphasis words
        emphasis_sentences = re.findall(
            r'[^.!?]*\b(?:important|must|required|mandatory|essential|critical|warning|notice)\b[^.!?]*[.!?]',
            text, re.IGNORECASE
        )
        key_points.extend(emphasis_sentences[:3])

        return [point.strip() for point in key_points if len(point.strip()) > 10]

    def find_red_flags(self, text: str, document_type: str) -> List[str]:
        """Identify potentially problematic clauses"""
        red_flags = []

        if document_type in self.document_patterns:
            red_flag_phrases = self.document_patterns[document_type]['red_flag_phrases']

            for phrase in red_flag_phrases:
                pattern = r'[^.!?]*\b' + re.escape(phrase) + r'\b[^.!?]*[.!?]'
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    red_flags.append(f"⚠️ {match.strip()}")

        return red_flags

    def extract_rights(self, text: str, document_type: str) -> List[str]:
        """Find mentions of your rights and options"""
        rights = []

        if document_type in self.document_patterns:
            rights_phrases = self.document_patterns[document_type]['rights_indicators']

            for phrase in rights_phrases:
                pattern = r'[^.!?]*\b' + re.escape(phrase) + r'\b[^.!?]*[.!?]'
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    rights.append(f"✅ {match.strip()}")

        return rights

    def generate_action_items(self, text: str, document_type: str) -> List[str]:
        """Generate specific things the person should do"""
        actions = []

        # Look for deadlines
        date_patterns = re.findall(
            r'(?:by|before|within|until)\s+([^.!?]*(?:days?|weeks?|months?|years?|\d{1,2}/\d{1,2}/\d{2,4})[^.!?]*)',
            text, re.IGNORECASE
        )
        for date in date_patterns:
            actions.append(f"📅 Important deadline: {date.strip()}")

        # Document-specific actions
        if document_type == 'medical':
            if re.search(r'\bside effects?\b', text, re.IGNORECASE):
                actions.append("📋 Ask your doctor about all side effects and what to watch for")
            if re.search(r'\balternative\b', text, re.IGNORECASE):
                actions.append("💭 Ask about alternative treatment options")

        elif document_type == 'insurance':
            actions.append("📞 Save the customer service number and your policy number")
            actions.append("📋 Understand your deductible and out-of-pocket maximum")

        elif document_type == 'legal':
            actions.append("⚖️ Consider having a lawyer review this before signing")
            actions.append("📋 Keep a copy of all documents")

        return actions

    def calculate_confidence(self, text: str, document_type: str) -> float:
        """Calculate how confident we are in the translation"""
        base_score = 0.7

        # Penalize very long documents
        if len(text) > 10000:
            base_score -= 0.1

        # Boost score if we recognized the document type
        if document_type != 'general':
            base_score += 0.2

        # Penalize if lots of unknown jargon remains
        jargon_count = len(re.findall(r'\b[A-Z]{3,}\b', text))
        if jargon_count > 10:
            base_score -= 0.1

        return max(0.1, min(0.95, base_score))

    def save_translation(self, result: TranslationResult, output_name: str):
        """Save translation result as an HTML report"""
        output_dir = Path("translations")
        output_dir.mkdir(exist_ok=True)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Translation: {output_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; }}
        .section {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
        .red-flags {{ background: #ffeaea; border-left: 4px solid #e74c3c; }}
        .rights {{ background: #eafff5; border-left: 4px solid #27ae60; }}
        .actions {{ background: #fff8ea; border-left: 4px solid #f39c12; }}
        .key-points {{ background: #eaf0ff; border-left: 4px solid #3498db; }}
        .confidence {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; }}
        .plain-english {{ background: #f8f9fa; padding: 20px; border-radius: 8px; white-space: pre-wrap; }}
        ul {{ list-style: none; padding-left: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <h1>Plain English Translation</h1>
    <p class="confidence">Document Type: {result.document_type.title()} | Confidence: {result.confidence_score:.0%}</p>
"""

        if result.red_flags:
            html += '    <div class="section red-flags"><h2>Red Flags</h2><ul>\n'
            for flag in result.red_flags:
                html += f"        <li>{flag}</li>\n"
            html += "    </ul></div>\n"

        if result.your_rights:
            html += '    <div class="section rights"><h2>Your Rights</h2><ul>\n'
            for right in result.your_rights:
                html += f"        <li>{right}</li>\n"
            html += "    </ul></div>\n"

        if result.action_items:
            html += '    <div class="section actions"><h2>Action Items</h2><ul>\n'
            for action in result.action_items:
                html += f"        <li>{action}</li>\n"
            html += "    </ul></div>\n"

        if result.key_points:
            html += '    <div class="section key-points"><h2>Key Points</h2><ul>\n'
            for point in result.key_points:
                html += f"        <li>{point}</li>\n"
            html += "    </ul></div>\n"

        html += f"""    <h2>Plain English Version</h2>
    <div class="plain-english">{result.plain_english}</div>

    <hr>
    <p><em>Generated by Plain English Translator. This is not legal or medical advice.</em></p>
</body>
</html>"""

        output_path = output_dir / f"{output_name}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


# Alias so `from translator import PlainEnglishTranslator` works
PlainEnglishTranslator = EnhancedPlainEnglishTranslator


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Translate complex documents into plain English (supports PDF, DOCX, TXT)'
    )
    parser.add_argument('file', help='Path to document file (PDF, DOCX, or TXT)')
    parser.add_argument('--output', '-o', help='Output filename (without extension)')
    parser.add_argument('--show-sneaky', '-s', action='store_true', help='Highlight sneaky clauses')

    args = parser.parse_args()

    translator = EnhancedPlainEnglishTranslator()

    try:
        print(f"📄 Processing: {args.file}")
        result = translator.translate_document_from_file(args.file)

        print(f"📊 Document Type: {result.document_type.title()}")
        print(f"📊 Translation Confidence: {result.confidence_score:.0%}")

        if result.red_flags:
            print(f"\n🚨 RED FLAGS FOUND ({len(result.red_flags)}):")
            for flag in result.red_flags[:5]:
                print(f"   {flag}")

        if result.action_items:
            print(f"\n📋 ACTION ITEMS ({len(result.action_items)}):")
            for action in result.action_items:
                print(f"   {action}")

        output_name = args.output or Path(args.file).stem
        translator.save_translation(result, output_name)
        print(f"\n💾 Full report: translations/{output_name}.html")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the file exists and is a supported format (PDF, DOCX, TXT)")


if __name__ == "__main__":
    main()
