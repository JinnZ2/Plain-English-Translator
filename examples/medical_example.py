#!/usr/bin/env python3
"""
Example: Translating a medical discharge summary
"""

import sys
from pathlib import Path

# Allow running from the examples/ directory or the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from translator import PlainEnglishTranslator  # noqa: E402  - needs sys.path set above

# Sample medical text (anonymized)

medical_text = """
DISCHARGE SUMMARY

Patient presents with acute myocardial infarction secondary to coronary artery occlusion.
Underwent emergent percutaneous coronary intervention with drug-eluting stent placement.
Post-procedural course complicated by transient hypotension requiring vasopressor support.

MEDICATIONS:

- Clopidogrel 75mg daily - contraindicated with omeprazole
- Metoprolol tartrate 25mg BID for cardioprotection
- Atorvastatin 80mg daily for secondary prevention
- Aspirin 81mg daily indefinitely

FOLLOW-UP:
Cardiology appointment in 2 weeks. Patient advised to monitor for signs of stent thrombosis
including chest pain, dyspnea, or diaphoresis. Return to ED immediately if symptoms occur.

PROGNOSIS:
With appropriate medical therapy and lifestyle modifications, long-term prognosis is favorable.
Patient counseled on smoking cessation and cardiac rehabilitation enrollment.
"""


def main():
    # Create translator
    translator = PlainEnglishTranslator()

    # Translate the document
    print("🏥 Translating medical discharge summary...\n")
    result = translator.translate_document(medical_text)

    # Show the results
    print(f"📊 Translation Confidence: {result.confidence_score:.0%}\n")

    print("🎯 KEY POINTS (What this really means):")
    for i, point in enumerate(result.key_points, 1):
        print(f"   {i}. {point}")

    print(f"\n⚠️  RED FLAGS ({len(result.red_flags)} found):")
    for flag in result.red_flags:
        print(f"   {flag}")

    print(f"\n✅ YOUR RIGHTS ({len(result.your_rights)} found):")
    for right in result.your_rights:
        print(f"   {right}")

    print(f"\n📋 ACTION ITEMS ({len(result.action_items)} found):")
    for action in result.action_items:
        print(f"   {action}")

    # Save detailed report
    translator.save_translation(result, "medical_discharge_example")
    print("\n💾 Detailed report saved to: translations/medical_discharge_example.html")

    print("\n" + "=" * 80)
    print("PLAIN ENGLISH VERSION:")
    print("=" * 80)
    print(result.plain_english)


if __name__ == "__main__":
    main()
