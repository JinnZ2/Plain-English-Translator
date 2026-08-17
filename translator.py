#!/usr/bin/env python3
"""
Enhanced Plain English Translator with PDF support and expanded legal/insurance detection
Now handles PDFs directly and catches more sneaky clauses!
"""

import html
import re
import sys
import argparse
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path

# PDF and DOCX support are optional. Plain .txt documents — the most common
# case — must work on a bare Python install, so these are imported lazily by
# the extractors that need them rather than at module load.


class ExtractionError(Exception):
    """Raised when a document's text cannot be read.

    Extraction failures are raised rather than returned as empty strings so a
    caller can never mistake an unreadable document for an empty one.
    """


def _import_pymupdf():
    """Import PyMuPDF, preferring the modern name over the deprecated `fitz`."""
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        import fitz  # noqa: F401  - pre-1.24 PyMuPDF only exposes `fitz`
        return fitz

DISCLAIMER = (
    "DISCLAIMER: This is an automated translation tool. It is NOT legal, medical, "
    "financial, or professional advice. Always consult a qualified professional "
    "before making decisions based on complex documents."
)


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
            },
            'government': {
                # Benefits and assistance
                'adjudication': 'the process of deciding your claim',
                'beneficiary': 'person who receives benefits',
                'determination': 'official decision on your eligibility',
                'entitlement': 'benefits you have a legal right to receive',
                'means-tested': 'eligibility depends on your income/assets',
                'categorical eligibility': 'you qualify based on receiving other benefits',
                'presumptive eligibility': 'temporary approval while full application is processed',
                'redetermination': 'review to check if you still qualify',
                'overpayment': 'they say they paid you too much and want money back',
                'recoupment': 'they take back overpaid benefits from future payments',
                'fair hearing': 'your right to challenge a decision before a judge',
                'administrative law judge': 'judge who decides government benefit disputes',
                'notice of action': 'letter telling you about changes to your benefits',
                'good cause': 'acceptable reason for missing a deadline or requirement',
                'enumeration': 'assigning a Social Security number',
                'quarters of coverage': 'work credits needed for Social Security',
                'full retirement age': 'age when you get full Social Security benefits',
                'disability determination': 'decision about whether you qualify for disability benefits',
                'substantial gainful activity': 'earning enough that they say you can work',
                'federal poverty level': 'income threshold used to determine benefit eligibility',
                'cost of living adjustment': 'yearly increase to keep up with inflation',
                'supplemental security income': 'monthly payments for disabled/elderly with low income',
                'medicaid': 'government health insurance for low-income individuals',
                'medicare': 'government health insurance for people 65+ or with disabilities',
                'snap': 'food assistance program (formerly food stamps)',
                'tanf': 'temporary cash assistance for families with children',
                'section 8': 'government help paying rent',
                'wic': 'nutrition program for pregnant women, infants, and children',
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
            },
            'government': {
                'red_flag_phrases': [
                    'overpayment', 'recoupment', 'benefits terminated',
                    'benefits reduced', 'benefits suspended', 'ineligible',
                    'disqualified', 'fraud', 'intentional program violation',
                    'sanctions', 'penalty', 'must repay', 'wage garnishment',
                    'failure to comply', 'benefits will stop', 'mandatory work requirement'
                ],
                'rights_indicators': [
                    'fair hearing', 'right to appeal', 'notice of action',
                    'good cause', 'free legal aid', 'legal services',
                    'ombudsman', 'advocate', 'discrimination complaint',
                    'reasonable accommodation', 'language access', 'interpreter',
                    'continued benefits pending appeal', 'aid paid pending'
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
            ],
            'sneaky_government': [
                r'failure.*to.*(?:report|comply|appear).*result.*in.*(?:termination|loss|reduction)',
                r'overpayment.*must.*(?:repay|return)',
                r'benefits.*(?:terminated|reduced|suspended).*without.*(?:notice|hearing)',
                r'waive.*(?:right|hearing|appeal)',
                r'(?:fraud|intentional).*program.*violation'
            ]
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods for best results"""
        text = ""
        attempts = []

        try:
            # Try PyMuPDF first (better for complex layouts)
            pymupdf = _import_pymupdf()
            doc = pymupdf.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()

            # If we got good text, return it
            if len(text.strip()) > 100:
                return text

        except ImportError:
            attempts.append("PyMuPDF is not installed")
        except Exception as e:
            attempts.append(f"PyMuPDF failed: {e}")

        try:
            # Fallback to PyPDF2
            import PyPDF2

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()

        except ImportError:
            attempts.append("PyPDF2 is not installed")
        except Exception as e:
            attempts.append(f"PyPDF2 failed: {e}")

        if not text.strip():
            raise ExtractionError(
                f"Could not extract any text from {file_path}. "
                + "; ".join(attempts)
                + ". Install PDF support with: pip install PyMuPDF PyPDF2"
            )

        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            from docx import Document
        except ImportError:
            raise ExtractionError(
                "Reading .docx files needs python-docx. "
                "Install it with: pip install python-docx"
            )

        try:
            doc = Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            raise ExtractionError(f"Error reading Word document {file_path}: {e}")

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

        if document_type in ['legal', 'insurance', 'financial', 'government']:
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
        government_keywords = [
            'benefits', 'eligibility', 'applicant', 'determination', 'federal',
            'state', 'agency', 'social security', 'medicaid', 'medicare',
            'snap', 'tanf', 'disability', 'supplemental'
        ]

        scores = {
            'medical': sum(2 if word in text_lower else 0 for word in medical_keywords),
            'legal': sum(2 if word in text_lower else 0 for word in legal_keywords),
            'insurance': sum(2 if word in text_lower else 0 for word in insurance_keywords),
            'financial': sum(2 if word in text_lower else 0 for word in financial_keywords),
            'government': sum(2 if word in text_lower else 0 for word in government_keywords)
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
        if 'notice of action' in text_lower or 'benefit determination' in text_lower:
            scores['government'] += 5
        if 'social security' in text_lower or 'food stamps' in text_lower:
            scores['government'] += 5
        if 'section 8' in text_lower or 'housing authority' in text_lower:
            scores['government'] += 5

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

        elif document_type == 'government':
            actions.append("📋 Save this notice and note any deadlines")
            actions.append("📞 Call the agency if anything is unclear - use the number on the notice")
            if re.search(r'\bappeal\b', text, re.IGNORECASE):
                actions.append("⚖️ You may have the right to appeal - check deadlines carefully")
            if re.search(r'\boverpayment\b', text, re.IGNORECASE):
                actions.append("💰 If they say you were overpaid, you can request a waiver")
            if re.search(r'\bhearing\b', text, re.IGNORECASE):
                actions.append("⚖️ You have the right to a fair hearing - consider getting free legal help")

        return actions

    def calculate_confidence(self, text: str, document_type: str) -> float:
        """Calculate how confident we are in the translation.

        Factors:
        - Did we recognize the document type?
        - How many jargon terms did we successfully translate?
        - How much unknown jargon (uppercase abbreviations) remains?
        - Document length (very long docs may have untranslated sections)
        - Presence of complex structures we can't parse well (tables, formulas)
        """
        score = 0.0

        # Document type recognition (0-0.25)
        if document_type != 'general':
            score += 0.25
        else:
            score += 0.05

        # Jargon coverage: what fraction of known terms did we find? (0-0.35)
        if document_type in self.jargon_dictionary:
            text_lower = text.lower()
            domain_terms = self.jargon_dictionary[document_type]
            found = sum(1 for term in domain_terms if term in text_lower)
            total = len(domain_terms)
            if total > 0:
                coverage = found / total
                # Higher coverage = we understand more of this document
                score += 0.35 * min(coverage * 5, 1.0)  # cap at 1.0
        else:
            score += 0.05

        # Unknown jargon penalty (0-0.2, starts at 0.2 and decreases)
        unknown_abbrevs = len(re.findall(r'\b[A-Z]{3,}\b', text))
        if unknown_abbrevs <= 3:
            score += 0.2
        elif unknown_abbrevs <= 10:
            score += 0.1
        # else: no bonus

        # Length factor (0-0.1)
        text_len = len(text)
        if text_len < 500:
            score += 0.05  # very short, might miss context
        elif text_len < 5000:
            score += 0.1   # good length
        elif text_len < 15000:
            score += 0.07  # getting long
        else:
            score += 0.02  # very long, likely missed things

        # Structural complexity penalty (0-0.1, starts at 0.1)
        has_tables = bool(re.search(r'\t.*\t.*\t', text))
        has_formulas = bool(re.search(r'[=<>]{2,}|[\$€£]\d+.*[\+\-\*\/]', text))
        structural_score = 0.1
        if has_tables:
            structural_score -= 0.05
        if has_formulas:
            structural_score -= 0.03
        score += structural_score

        return round(max(0.1, min(0.95, score)), 2)

    def translate_side_by_side(self, text: str, document_type: Optional[str] = None) -> List[Dict[str, str]]:
        """Return sentence-level side-by-side: original vs plain English.

        Returns a list of dicts with 'original' and 'plain' keys.
        """
        if document_type is None:
            document_type = self.detect_document_type(text)

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        pairs = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            plain = self.translate_jargon(sentence, document_type)
            # Only include if translation actually changed something
            pairs.append({
                'original': sentence,
                'plain': plain
            })
        return pairs

    def translate_to_spanish(self, result: TranslationResult) -> Dict[str, str]:
        """Provide basic Spanish plain-language equivalents for common output phrases.

        This uses a local lookup table for common terms — no external API needed.
        Returns a dict with Spanish versions of key output sections.
        """
        spanish_terms = {
            # Red flag labels
            'RED FLAGS FOUND': 'SEÑALES DE ALERTA',
            'SNEAKY CLAUSE': 'CLÁUSULA ENGAÑOSA',
            # Action items
            'Important deadline': 'Fecha límite importante',
            'Ask your doctor about all side effects': 'Pregúntele a su médico sobre los efectos secundarios',
            'Ask about alternative treatment options': 'Pregunte sobre opciones de tratamiento alternativas',
            'Save the customer service number': 'Guarde el número de servicio al cliente',
            'Understand your deductible': 'Entienda su deducible',
            'Consider having a lawyer review this': 'Considere que un abogado revise esto',
            'Keep a copy of all documents': 'Guarde una copia de todos los documentos',
            'Save this notice and note any deadlines': 'Guarde este aviso y anote las fechas límite',
            'Call the agency if anything is unclear': 'Llame a la agencia si algo no está claro',
            'You may have the right to appeal': 'Usted puede tener derecho a apelar',
            # Document types
            'Medical': 'Médico',
            'Legal': 'Legal',
            'Insurance': 'Seguro',
            'Financial': 'Financiero',
            'Government': 'Gobierno',
            'General': 'General',
            # Section headers
            'Your Rights': 'Sus Derechos',
            'Action Items': 'Acciones a Tomar',
            'Key Points': 'Puntos Clave',
            'Plain English Version': 'Versión en Lenguaje Simple',
        }

        # Translate the plain english text using domain jargon → Spanish simple terms
        spanish_jargon = {
            'heart attack': 'ataque al corazón',
            'stroke': 'derrame cerebral',
            'high blood pressure': 'presión arterial alta',
            'trouble breathing': 'dificultad para respirar',
            'you give up your right to sue': 'usted renuncia a su derecho de demandar',
            'you pay before insurance kicks in': 'lo que usted paga antes de que el seguro cubra',
            'monthly payment for coverage': 'pago mensual por cobertura',
            'interest rate can go up': 'la tasa de interés puede subir',
        }

        output = {
            'document_type': spanish_terms.get(result.document_type.title(), result.document_type),
            'disclaimer': (
                "AVISO: Esta es una herramienta de traducción automatizada. NO es consejo "
                "legal, médico, financiero ni profesional. Siempre consulte a un profesional "
                "calificado antes de tomar decisiones basadas en documentos complejos."
            ),
            'section_headers': spanish_terms,
            'spanish_jargon': spanish_jargon,
        }
        return output

    def translate_to_ojibwe(self, result: TranslationResult) -> Dict[str, str]:
        """Provide Ojibwe (Anishinaabemowin) plain-language equivalents for key output terms.

        Ojibwe is spoken across the Great Lakes region by Anishinaabe peoples.
        This uses a local lookup table — no external API needed.
        Note: These are common/standardized forms; regional dialects vary.
        """
        ojibwe_terms = {
            # Section headers
            'Red Flags': 'Naniizaanizi Mazina\'iganan',  # Danger signs
            'Your Rights': 'Gidakiiwinan',  # Your rights/entitlements
            'Action Items': 'Ge-izhichigeng',  # Things to do
            'Key Points': 'Gichi-ina\'oonwewinan',  # Important points
            'Plain English Version': 'Weweni Zhibii\'igaadeg',  # Written clearly
            # Document types
            'Medical': 'Mashkiki',  # Medicine
            'Legal': 'Inaakonige',  # Law/legal
            'Insurance': 'Aazhogan Mazina\'igan',  # Protection paper
            'Financial': 'Zhooniyaa',  # Money
            'Government': 'Ogimaawiwin',  # Government/leadership
            'General': 'Maamawi',  # General/together
        }

        # Key medical/legal/financial concepts in Ojibwe
        ojibwe_concepts = {
            'heart attack': 'ode\' aakozi',  # heart sickness
            'high blood pressure': 'ishpagonagizi miskwi',  # blood is high
            'hospital': 'aakoziwigamig',  # sick-house
            'medicine': 'mashkiki',
            'doctor': 'mashkikiiwinini',  # medicine person
            'money': 'zhooniyaa',
            'help': 'wiidookaazowin',
            'rights': 'akiiwinan',
            'danger': 'naniizaanad',
            'warning': 'aanjimaajitoon',
            'family': 'niijaanisag',
            'food': 'miijim',
            'home': 'endaayan',  # where you live
            'water': 'nibi',
            'children': 'abinoojiinyag',
        }

        output = {
            'language_name': 'Anishinaabemowin (Ojibwe)',
            'document_type': ojibwe_terms.get(result.document_type.title(), result.document_type),
            'disclaimer': (
                "AANIIN: Maanda mazina'igan wii-wiidookaagoyin ji-nisidotaman. "
                "Gaawiin dash inaakonige-wiidookaagewiniwi, gaawiin mashkiki-wiidookaagewiniwi. "
                "Gagwejim awiiya ge-wiidookook."
                # Translation: This document is to help you understand.
                # It is not legal advice, it is not medical advice.
                # Ask someone who can help you.
            ),
            'section_headers': ojibwe_terms,
            'concepts': ojibwe_concepts,
        }
        return output

    def translate_to_navajo(self, result: TranslationResult) -> Dict[str, str]:
        """Provide Navajo (Diné Bizaad) plain-language equivalents for key output terms.

        Navajo is spoken by the Diné people, primarily in the Navajo Nation
        (Arizona, New Mexico, Utah). This uses a local lookup table.
        """
        navajo_terms = {
            # Section headers
            'Red Flags': "Báhádzidígíí",  # Dangerous things
            'Your Rights': "Bee baa áhólníigíí",  # What you are entitled to
            'Action Items': "Ída'iinííłaago baa ntsáhákees",  # Things to think about doing
            'Key Points': "T'áá bí ałchíní bee haz'ą́ą́ dóó baa áhólyáago",  # Important things
            'Plain English Version': "Saad bee yá'át'ééhígo bik'ehgo",  # In good/clear words
            # Document types
            'Medical': "Azee'",  # Medicine
            'Legal': "Beehaz'áanii",  # Law
            'Insurance': "Bee ná'ádleehígíí",  # Protection/coverage
            'Financial': "Béeso",  # Money
            'Government': "Wáshindoon",  # Washington/Government
            'General': "T'áá altso",  # All/general
        }

        navajo_concepts = {
            'heart attack': "ajéí bidziil nááná'áłtso",  # heart becomes very ill
            'high blood pressure': "dił yílchíhígíí",  # blood pushes hard
            'hospital': "azee' ál'íní",  # place where medicine is made
            'medicine': "azee'",
            'doctor': "azee' ííł'íní",  # one who makes medicine
            'money': "béeso",
            'help': "shíká a'doolwołígíí",  # help for me
            'rights': "bee baa áhólníigíí",
            'danger': "báhádzidígíí",
            'warning': "yee'iidzaago",
            'family': "k'é",  # kinship/family
            'food': "ch'iyáán",
            'home': "hooghan",  # hogan/home
            'water': "tó",
            'children': "áłchíní",
        }

        output = {
            'language_name': 'Diné Bizaad (Navajo)',
            'document_type': navajo_terms.get(result.document_type.title(), result.document_type),
            'disclaimer': (
                "DÍÍ NAALTSOOS: Díí naaltsoos saad bee yá'át'ééhígo bee na'ídíkid. "
                "Doo beehaz'áanii bik'ehgo yá'adaat'éhígíí át'é da, "
                "doo azee' bik'ehgo yá'adaat'éhígíí át'é da. "
                "Níká'adoolwołígíí bił yíníłta'."
                # Translation: This document explains in clear words.
                # It is not legal advice, it is not medical advice.
                # Read it with someone who can help you.
            ),
            'section_headers': navajo_terms,
            'concepts': navajo_concepts,
        }
        return output

    def translate_to_cherokee(self, result: TranslationResult) -> Dict[str, str]:
        """Provide Cherokee (ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ / Tsalagi Gawonihisdi) plain-language
        equivalents for key output terms.

        Cherokee is spoken by the Cherokee Nation and Eastern Band of Cherokee Indians.
        Cherokee has its own syllabary (ᏣᎳᎩ ᎤᏪᏍᏓ) created by Sequoyah.
        This uses a local lookup table with both syllabary and transliteration.
        """
        cherokee_terms = {
            # Section headers (syllabary + transliteration)
            'Red Flags': 'ᎤᏍᎦᏃᎵᏙᏗ (usganolidodi)',  # Warning signs
            'Your Rights': 'ᏣᏗᏱ ᎤᏂᎩᏍᏔᏂ (tsadiyi unigistani)',  # Your rights
            'Action Items': 'ᏗᎦᎸᏫᏍᏓᏁᏗ (digalvwisdanedi)',  # Things to do
            'Key Points': 'ᎤᎵᎮᎵᏍᏗ (ulihelisdi)',  # Important things
            'Plain English Version': 'ᎣᏍᏓ ᎠᏕᎶᏆᏍᏗ (osda adeloquasdi)',  # Good explanation
            # Document types
            'Medical': 'ᏅᏩᏙᎯ (nvwadohi)',  # Medicine/healing
            'Legal': 'ᏧᏓᎴᏅᏓ (tsudaleenvda)',  # Law
            'Insurance': 'ᎠᎵᏍᎦᎳᏗᏍᏗ (alisgaladisdi)',  # Protection
            'Financial': 'ᎠᏕᎳ (adela)',  # Money
            'Government': 'ᎠᏂᏴᏫᏯ ᎠᏂᎬᎿᏬᏍᎩ (aniyvwiya anigenvwosgi)',  # People who govern
            'General': 'ᏂᎦᏛᎢ (nigadvhi)',  # All
        }

        cherokee_concepts = {
            'heart attack': 'ᎤᏂᎦ ᎠᎩᎵᎯᏍᏗ (uniga agilihisdi)',  # heart sickness
            'high blood pressure': 'ᎩᎦ ᎤᏲ (giga uyo)',  # blood is bad/strong
            'hospital': 'ᏅᏩᏙᎯᏙᏗ (nvwadohidodi)',  # healing place
            'medicine': 'ᏅᏩᏙᎯ (nvwadohi)',
            'doctor': 'ᏗᏬᏂᎯᏍᎩ (diwonihisgi)',  # one who heals
            'money': 'ᎠᏕᎳ (adela)',
            'help': 'ᎠᎵᏍᏗᏱᏗᏍᏗ (alisdiyidisdi)',  # helping
            'rights': 'ᎤᏂᎩᏍᏔᏂ (unigistani)',
            'danger': 'ᎤᏍᎦᏃᎵ (usganoliyo)',
            'warning': 'ᎠᏍᎦᏃᏗ (asganodi)',
            'family': 'ᏏᏓᏁᎸ (sidanelv)',
            'food': 'ᎠᎵᏍᏓᏴᏗ (alisdayedi)',  # something to eat
            'home': 'ᎨᏒᎢ (gesvi)',  # home/dwelling
            'water': 'ᎠᎹ (ama)',
            'children': 'ᏂᎬᏂ (nigvni)',  # the young ones
        }

        output = {
            'language_name': 'ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ (Cherokee)',
            'document_type': cherokee_terms.get(result.document_type.title(), result.document_type),
            'disclaimer': (
                "ᎯᎠ ᏓᎪᏪᎸᎢ: ᎯᎠ ᎣᏍᏓ ᎠᏕᎶᏆᏍᏗ ᎦᏬᏂᎯᏍᏗ ᎨᏒᎢ. "
                "ᎥᏝ ᏧᏓᎴᏅᏓ ᎠᎵᏍᎪᎸᏗ ᎨᏒᎢ ᎤᏍᏗ, "
                "ᎥᏝ ᏅᏩᏙᎯ ᎠᎵᏍᎪᎸᏗ ᎨᏒᎢ ᎤᏍᏗ. "
                "ᎠᏎᏃ ᎾᏍᎩ ᏗᏤᎵ ᎠᎵᏍᏗᏱᏗ ᏥᏍᏕᎸᏗ."
                # Translation: This is a clear-words document.
                # It is not legal advice, it is not medical advice.
                # Please find someone to help you.
            ),
            'section_headers': cherokee_terms,
            'concepts': cherokee_concepts,
        }
        return output

    def save_translation(self, result: TranslationResult, output_name: str) -> Path:
        """Save translation result as an HTML report and return its path"""
        output_dir = Path("translations")
        output_dir.mkdir(exist_ok=True)

        # Document text is untrusted input — a contract or discharge summary can
        # contain anything, including markup. Escape every interpolated value so
        # the report renders the document rather than executing it.
        esc = html.escape

        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Translation: {esc(str(output_name))}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
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
    <p class="confidence">Document Type: {esc(result.document_type.title())}
       | Confidence: {result.confidence_score:.0%}</p>
"""

        sections = [
            ("red-flags", "Red Flags", result.red_flags),
            ("rights", "Your Rights", result.your_rights),
            ("actions", "Action Items", result.action_items),
            ("key-points", "Key Points", result.key_points),
        ]

        for css_class, heading, items in sections:
            if not items:
                continue
            page += f'    <div class="section {css_class}"><h2>{heading}</h2><ul>\n'
            for item in items:
                page += f"        <li>{esc(item)}</li>\n"
            page += "    </ul></div>\n"

        page += f"""    <h2>Plain English Version</h2>
    <div class="plain-english">{esc(result.plain_english)}</div>

    <hr>
    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-top: 20px;">
        <strong>⚠️ {DISCLAIMER}</strong>
    </div>
    <p><em>Generated by Plain English Translator.</em></p>
</body>
</html>"""

        output_path = output_dir / f"{output_name}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page)

        return output_path


# Alias so `from translator import PlainEnglishTranslator` works
PlainEnglishTranslator = EnhancedPlainEnglishTranslator


def _try_ollama_enhance(text: str, document_type: str) -> Optional[str]:
    """Try to enhance translation using a local Ollama LLM. Returns None if unavailable."""
    try:
        import urllib.request
        import urllib.error

        prompt = (
            f"You are a plain-language translator. The following is a {document_type} document. "
            f"Rewrite it in simple, clear English that anyone can understand. "
            f"Keep all important details but remove jargon.\n\n{text[:3000]}"
        )

        data = json.dumps({
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }).encode('utf-8')

        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get("response", None)
    except Exception:
        return None


def _print_result(result: TranslationResult, side_by_side: bool = False,
                  spanish: bool = False, ojibwe: bool = False,
                  navajo: bool = False, cherokee: bool = False,
                  use_ollama: bool = False):
    """Print a full translation result to terminal."""
    translator = EnhancedPlainEnglishTranslator()

    print(f"\n{'=' * 70}")
    print(f"📊 Document Type: {result.document_type.title()}")
    print(f"📊 Translation Confidence: {result.confidence_score:.0%}")
    print(f"{'=' * 70}")

    # Always show disclaimer first
    print(f"\n⚠️  {DISCLAIMER}\n")

    # Red flags first — most important
    if result.red_flags:
        print(f"🚨 RED FLAGS FOUND ({len(result.red_flags)}):")
        for flag in result.red_flags:
            print(f"   {flag}")
        print()

    # Your rights
    if result.your_rights:
        print(f"✅ YOUR RIGHTS ({len(result.your_rights)}):")
        for right in result.your_rights:
            print(f"   {right}")
        print()

    # Action items
    if result.action_items:
        print(f"📋 ACTION ITEMS ({len(result.action_items)}):")
        for action in result.action_items:
            print(f"   {action}")
        print()

    # Key points
    if result.key_points:
        print(f"🔑 KEY POINTS ({len(result.key_points)}):")
        for point in result.key_points:
            print(f"   • {point}")
        print()

    # Side-by-side mode
    if side_by_side:
        print("📖 SIDE-BY-SIDE TRANSLATION:")
        print("-" * 70)
        pairs = translator.translate_side_by_side(result.original_text, result.document_type)
        for i, pair in enumerate(pairs, 1):
            if pair['original'] != pair['plain']:
                print(f"  ORIGINAL:  {pair['original'][:200]}")
                print(f"  PLAIN:     {pair['plain'][:200]}")
                print()
        print()
    else:
        # Print the full plain English translation
        print("📝 PLAIN ENGLISH TRANSLATION:")
        print("-" * 70)
        print(result.plain_english[:5000])
        if len(result.plain_english) > 5000:
            print(f"\n... ({len(result.plain_english) - 5000} more characters in full report)")
        print()

    # Ollama enhanced version
    if use_ollama:
        print("🤖 Checking for local LLM (Ollama)...")
        enhanced = _try_ollama_enhance(result.original_text, result.document_type)
        if enhanced:
            print("🤖 LLM-ENHANCED TRANSLATION:")
            print("-" * 70)
            print(enhanced[:5000])
            print()
        else:
            print("   Ollama not available. Install from https://ollama.com and run: ollama pull llama3.2")
            print()

    # Spanish output
    if spanish:
        spanish_info = translator.translate_to_spanish(result)
        print(f"🇪🇸 TIPO DE DOCUMENTO: {spanish_info['document_type']}")
        print(f"⚠️  {spanish_info['disclaimer']}")
        print()

    # Ojibwe output
    if ojibwe:
        ojibwe_info = translator.translate_to_ojibwe(result)
        print(f"🪶 {ojibwe_info['language_name']}")
        print(f"   Document Type: {ojibwe_info['document_type']}")
        print(f"   ⚠️  {ojibwe_info['disclaimer']}")
        print(f"   Key terms in Anishinaabemowin:")
        for eng, oji in list(ojibwe_info['concepts'].items())[:8]:
            print(f"      {eng} → {oji}")
        print()

    # Navajo output
    if navajo:
        navajo_info = translator.translate_to_navajo(result)
        print(f"🪶 {navajo_info['language_name']}")
        print(f"   Document Type: {navajo_info['document_type']}")
        print(f"   ⚠️  {navajo_info['disclaimer']}")
        print(f"   Key terms in Diné Bizaad:")
        for eng, nav in list(navajo_info['concepts'].items())[:8]:
            print(f"      {eng} → {nav}")
        print()

    # Cherokee output
    if cherokee:
        cherokee_info = translator.translate_to_cherokee(result)
        print(f"🪶 {cherokee_info['language_name']}")
        print(f"   Document Type: {cherokee_info['document_type']}")
        print(f"   ⚠️  {cherokee_info['disclaimer']}")
        print(f"   Key terms in ᏣᎳᎩ (Cherokee):")
        for eng, chr_term in list(cherokee_info['concepts'].items())[:8]:
            print(f"      {eng} → {chr_term}")
        print()

    # Final disclaimer
    print("-" * 70)
    print(f"⚠️  {DISCLAIMER}")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Translate complex documents into plain English (supports PDF, DOCX, TXT)'
    )
    parser.add_argument('file', nargs='?', help='Path to document file (PDF, DOCX, or TXT)')
    parser.add_argument('--output', '-o', help='Output filename (without extension)')
    parser.add_argument('--show-sneaky', '-s', action='store_true', help='Highlight sneaky clauses')
    parser.add_argument('--side-by-side', '-sbs', action='store_true',
                        help='Show sentence-by-sentence original vs plain English')
    parser.add_argument('--spanish', '-es', action='store_true',
                        help='Include Spanish plain-language output')
    parser.add_argument('--ojibwe', action='store_true',
                        help='Include Ojibwe (Anishinaabemowin) plain-language output')
    parser.add_argument('--navajo', action='store_true',
                        help='Include Navajo (Diné Bizaad) plain-language output')
    parser.add_argument('--cherokee', action='store_true',
                        help='Include Cherokee (ᏣᎳᎩ) plain-language output')
    parser.add_argument('--ollama', action='store_true',
                        help='Use local Ollama LLM for enhanced translation')
    parser.add_argument('--json', action='store_true',
                        help='Output result as JSON')

    args = parser.parse_args()

    translator = EnhancedPlainEnglishTranslator()

    # Interactive mode: no file argument
    if args.file is None:
        print("=" * 70)
        print("📝 Plain English Translator — Interactive Mode")
        print("=" * 70)
        print(f"\n⚠️  {DISCLAIMER}\n")
        print("Paste or type your document text below.")
        print("When done, press Enter on an empty line (or Ctrl+D / Ctrl+Z).\n")

        lines = []
        try:
            while True:
                line = input()
                if line == '' and lines:
                    break
                lines.append(line)
        except EOFError:
            pass

        text = '\n'.join(lines)
        if len(text.strip()) < 50:
            print("❌ Text too short. Please provide at least a few sentences.")
            sys.exit(1)

        result = translator.translate_document(text)
        _print_result(result, side_by_side=args.side_by_side,
                      spanish=args.spanish, ojibwe=args.ojibwe,
                      navajo=args.navajo, cherokee=args.cherokee,
                      use_ollama=args.ollama)

        if args.json:
            print("\n📄 JSON OUTPUT:")
            output = asdict(result)
            output.pop('original_text')  # don't dump the full original
            print(json.dumps(output, indent=2))

        return

    # File mode
    try:
        print(f"📄 Processing: {args.file}")
        result = translator.translate_document_from_file(args.file)

        if args.json:
            output = asdict(result)
            output.pop('original_text')
            print(json.dumps(output, indent=2))
            return

        _print_result(result, side_by_side=args.side_by_side,
                      spanish=args.spanish, ojibwe=args.ojibwe,
                      navajo=args.navajo, cherokee=args.cherokee,
                      use_ollama=args.ollama)

        output_name = args.output or Path(args.file).stem
        translator.save_translation(result, output_name)
        print(f"💾 Full report: translations/{output_name}.html")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the file exists and is a supported format (PDF, DOCX, TXT)")
        sys.exit(1)


if __name__ == "__main__":
    main()
