# Plain English Translator

**Empowering people through understanding**

Stop getting screwed over by documents you can’t understand. This tool translates medical records, insurance policies, legal contracts, and financial documents into plain English - plus tells you what you should actually *do* about it.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)

## 🚀 Why This Matters

Ever tried to understand your insurance policy? Medical discharge papers? A rental agreement? These documents are deliberately written to confuse you. **That stops now.**

This tool:

- ✅ Translates jargon into words humans actually use
- ⚠️ Flags the stuff that could hurt you
- 📋 Tells you exactly what to do next
- 🎯 Explains your actual rights and options
- 💪 Gives you the confidence to advocate for yourself

## 🔥 Real-World Impact

**Medical**: “Myocardial infarction” → “Heart attack” + “Ask your doctor about…”
**Insurance**: “Prior authorization required” → “You need approval first or you’ll pay full price”  
**Legal**: “Binding arbitration clause” → “⚠️ You give up your right to sue in court”
**Financial**: “Compound interest” → “Interest that earns interest (this adds up fast!)”

## ⚡ Quick Start

```bash
# Install
pip install -r requirements.txt

# Translate a document
python translator.py your-scary-document.txt

# Get a beautiful HTML report
open translations/your-scary-document.html
```

## 🛠 Installation

```bash
git clone https://github.com/yourusername/plain-english-translator.git
cd plain-english-translator
pip install -r requirements.txt
```

## 📖 Usage Examples

### Command Line

```bash
# Basic translation
python translator.py medical-report.txt

# Custom output name  
python translator.py insurance-policy.pdf -o my-policy-explained

# Process multiple files
python batch_translate.py documents/*.pdf
```

### Python API

```python
from translator import PlainEnglishTranslator

translator = PlainEnglishTranslator()
result = translator.translate_document(your_document_text)

print(f"Key points: {result.key_points}")
print(f"Red flags: {result.red_flags}")  
print(f"Your rights: {result.your_rights}")
```

## 🏥 Medical Documents

Perfect for:

- Discharge summaries
- Treatment consent forms
- Medication guides
- Insurance explanations of benefits
- Lab results

**Example transformation:**

```
Before: "Patient presents with acute myocardial infarction, requires immediate percutaneous coronary intervention"

After: "You're having a heart attack (acute myocardial infarction) and need immediate treatment to open blocked arteries (percutaneous coronary intervention)"

Red Flags: ⚠️ This is a medical emergency requiring immediate treatment
Your Rights: ✅ You have the right to understand all treatment options and risks
Action Items: 📋 Ask about recovery time and follow-up care needed
```

## ⚖️ Legal Documents

Handles:

- Rental agreements
- Employment contracts
- Terms of service
- Arbitration clauses
- Liability waivers

**Example:**

```
Before: "Party hereby waives any right to trial by jury and agrees to binding arbitration"

After: "⚠️ You give up your right to a jury trial and must use private arbitration instead (you can't sue in regular court)"
```

## 🏥 Insurance Policies

Decodes:

- Coverage explanations
- Prior authorization requirements
- Network restrictions
- Claim procedures
- Exclusions

## 💰 Financial Documents

Clarifies:

- Loan agreements
- Investment prospectuses
- Credit card terms
- Mortgage documents

## 🤝 Contributing

**This tool gets better when real people add real-world knowledge.**

### Adding Medical Terms

```python
# In translator.py, add to jargon_dictionary['medical']:
'new_medical_term': 'what it actually means',
```

### Adding Red Flag Patterns

```python
# Add phrases that should trigger warnings:
'red_flag_phrases': [
    'your new scary phrase',
    'another warning sign'
]
```

### Contributing Examples

Have a document that got translated well (or poorly)? Add it to `/examples` with before/after comparisons.

## 🎯 Roadmap

- [ ] **PDF support** - Direct PDF parsing
- [ ] **Web interface** - Upload and translate online
- [ ] **Mobile app** - Take photos of documents
- [ ] **Real-time translation** - Browser extension
- [ ] **Crowdsourced dictionary** - Community-contributed terms
- [ ] **Legal review flagging** - “You should definitely get a lawyer”
- [ ] **Multi-language support** - Beyond English
- [ ] **Voice output** - Audio explanations
- [ ] **Integration APIs** - For healthcare/legal platforms

## 🚨 Important Notes

**This tool helps you understand documents - it’s not legal or medical advice.** Always consult professionals for important decisions.

**Privacy**: This tool runs locally on your computer. Your documents never leave your machine.

**Accuracy**: We aim for high accuracy but complex documents may need professional review. Check the confidence score in each report.

## 📄 License

MIT License - Use it, modify it, share it. Let’s democratize understanding together.

## 🙏 Acknowledgments

Built with frustration at systems that deliberately confuse people, and hope that technology can level the playing field.

**Special thanks to everyone who’s ever been screwed over by fine print they couldn’t understand. This one’s for you.**

-----

## 🐛 Found a Bug?

Open an issue! Even better, tell us:

- What document type you were processing
- What went wrong vs. what you expected
- The confidence score the tool gave

## 💡 Feature Requests

Got an idea? We want to hear it! Especially if you work in:

- Healthcare (patient advocacy)
- Legal aid
- Financial counseling
- Insurance
- Government services

**Together, we can make important information accessible to everyone.**
