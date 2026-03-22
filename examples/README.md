# Real-World Examples

This folder contains examples of the Plain English Translator in action with real document types. All examples use anonymized, public, or fictional content.

## Available Examples

### `medical_example.py`

**What it translates:** Hospital discharge summary
**Why it matters:** Helps patients understand their treatment and follow-up care
**Run it:** `python examples/medical_example.py`

**Sample transformation:**

- **Before:** "Patient presents with acute myocardial infarction"
- **After:** "You're having a heart attack (acute myocardial infarction)"
- **Red flags:** Emergency treatment required
- **Action items:** Ask about recovery time and cardiac rehabilitation

## Running Examples

```bash
# Run from the project root
python examples/medical_example.py

# Process your own document
python translator.py your-document.txt -o your-document-explained
```

## What Each Example Shows

- **Original confusing text**
- **Plain English translation**
- **Key points extracted**
- **Red flags identified**
- **Your rights and options**
- **Specific action items**
- **Confidence score**

## Adding New Examples

Have a document type we should cover? Contribute an example!

1. **Anonymize completely** - remove all personal info
1. **Focus on common scenarios** - what do most people encounter?
1. **Show the transformation** - before/after comparison
1. **Explain why it matters** - real-world impact

**Example template:**

```python
#!/usr/bin/env python3
"""
Example: Translating a [document type]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from translator import PlainEnglishTranslator

sample_text = """
Your confusing document text here
"""

def main():
    translator = PlainEnglishTranslator()
    result = translator.translate_document(sample_text)

    print(f"Document Type: {result.document_type}")
    print(f"Confidence: {result.confidence_score:.0%}")
    print(f"Red Flags: {len(result.red_flags)}")
    print(f"Action Items: {len(result.action_items)}")

if __name__ == "__main__":
    main()
```

## Most Requested Examples

Based on user requests, priority examples to add:

1. **Rental agreement** - spot predatory lease terms
1. **Employment contract** - understand non-compete and IP clauses
1. **Health insurance policy** - know what's covered before treatment
1. **Explanation of benefits** - understand why claims were denied
1. **Loan agreement** - understand true costs and penalties
1. **Credit card terms** - know when fees apply

## Document Sources

Our examples come from:

- **Public domain** government documents
- **Anonymized** real-world examples (with permission)
- **Fictional but realistic** scenarios based on common patterns
- **Educational materials** from trusted sources

**We never include:**

- Personal information
- Proprietary content
- Confidential documents

---

**Remember**: These are examples for education. Always consult professionals for important legal, medical, or financial decisions!
