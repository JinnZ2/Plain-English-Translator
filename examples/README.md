# Real-World Examples

This folder contains examples of the Plain English Translator in action with real document types. All examples use anonymized, public, or fictional content.

## 🏥 Medical Examples

### `medical_discharge.py`

**What it translates:** Hospital discharge summary
**Why it matters:** Helps patients understand their treatment and follow-up care
**Run it:** `python medical_discharge.py`

**Sample transformation:**

- **Before:** “Patient presents with acute myocardial infarction”
- **After:** “You’re having a heart attack (acute myocardial infarction)”
- **Red flags:** Emergency treatment required
- **Action items:** Ask about recovery time and cardiac rehabilitation

### `medication_guide.py`

**What it translates:** Prescription medication information
**Why it matters:** Understand side effects and drug interactions
**Run it:** `python medication_guide.py`

## ⚖️ Legal Examples

### `rental_agreement.py`

**What it translates:** Apartment lease clauses
**Why it matters:** Spot predatory terms before signing
**Run it:** `python rental_agreement.py`

**Sample red flags it catches:**

- Binding arbitration clauses
- Excessive penalty fees
- Unreasonable restrictions

### `employment_contract.py`

**What it translates:** Job offer contracts
**Why it matters:** Understand non-compete and intellectual property clauses
**Run it:** `python employment_contract.py`

## 🏥 Insurance Examples

### `health_insurance_policy.py`

**What it translates:** Health insurance policy documents
**Why it matters:** Know what’s covered before you need treatment
**Run it:** `python health_insurance_policy.py`

**Sample translations:**

- **Before:** “Prior authorization required for specialist referrals”
- **After:** “You need approval first or you’ll pay full price for specialist visits”

### `explanation_of_benefits.py`

**What it translates:** EOB statements from insurance
**Why it matters:** Understand why claims were denied or what you owe
**Run it:** `python explanation_of_benefits.py`

## 💰 Financial Examples

### `loan_agreement.py`

**What it translates:** Personal or auto loan contracts
**Why it matters:** Understand true costs and penalties
**Run it:** `python loan_agreement.py`

### `credit_card_terms.py`

**What it translates:** Credit card terms and conditions
**Why it matters:** Know when fees apply and how interest is calculated
**Run it:** `python credit_card_terms.py`

## 📊 Performance Examples

Each example shows:

- **Original confusing text**
- **Plain English translation**
- **Key points extracted**
- **Red flags identified**
- **Your rights and options**
- **Specific action items**
- **Confidence score**

## 🚀 Running Examples

```bash
# Run a specific example
python examples/medical_discharge.py

# Run all examples
python examples/run_all_examples.py

# Process your own similar document
python translator.py your-document.txt -o your-document-explained
```

## 📈 Adding New Examples

Have a document type we should cover? Contribute an example!

1. **Anonymize completely** - remove all personal info
1. **Focus on common scenarios** - what do most people encounter?
1. **Show the transformation** - before/after comparison
1. **Explain why it matters** - real-world impact

**Example template:**

```python
# examples/your_document_type.py

# Sample document text (anonymized)
sample_text = """
Your confusing document text here
"""

# What this helps with
print("This example shows how to understand [document type]")
print("Common situations: [when people encounter this]")
print("Why it matters: [potential consequences of not understanding]")

# Run the translator
result = translator.translate_document(sample_text)

# Show results...
```

## 📋 Document Sources

Our examples come from:

- **Public domain** government documents
- **Anonymized** real-world examples (with permission)
- **Fictional but realistic** scenarios based on common patterns
- **Educational materials** from trusted sources

**We never include:**

- Personal information
- Proprietary content
- Confidential documents

## 🎯 Most Requested Examples

Based on user requests, priority examples to add:

1. **Medicare/Medicaid** documents
1. **Divorce/custody** paperwork
1. **Property tax** assessments
1. **Student loan** terms
1. **Power of attorney** forms
1. **Advance directive** documents
1. **Small business** contracts
1. **Software license** agreements

## 💡 Using These Examples

**For learning:** Run examples to see how the tool works
**For testing:** Use these to verify the tool works on your system
**For comparison:** See if your documents produce similar results
**For contribution:** Use as templates for adding new examples

-----

**Remember**: These are examples for education. Always consult professionals for important legal, medical, or financial decisions!
