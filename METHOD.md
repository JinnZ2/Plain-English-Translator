# How this repo gets audited

A record of the loop used on 2026-08-14, kept so the next pass can start where
this one stopped instead of rediscovering the same things.

## The loop

```
hypothesize → run → observe → falsified? → revise the claim → look for unknowns → rerun
```

The load-bearing word is **run**. Every defect below was found by executing the
code, not by reading it. Reading the repo produces a plausible story about what
it does; running it produces the truth. Where the two disagreed, reading lost —
every time.

Two rules that earned their place:

1. **A passing test proves nothing until you've watched it fail.** After fixing
   a bug, revert the fix and confirm the test catches it. An untested test is
   just a comment that costs CPU time.
2. **A silent wrong answer outranks a crash.** A crash tells the user something
   broke. A confident report built from garbage does not. Prioritise
   accordingly — see H3, the worst defect found.

## Round 1 — the claims that were checked

| # | Hypothesis | Result | What the run showed |
|---|---|---|---|
| H1 | The tool runs as documented | **Falsified** | `import PyPDF2` at module top killed *every* entry point — CLI, batch, examples — even for `.txt`, which needs no dependencies at all |
| H2 | The HTML report is safe to open | **Falsified** | `<script>alert(1)</script>` in a source contract reached the report unescaped and executable |
| H3 | Batch supports the documented formats | **Falsified** | README documents `batch_translate.py documents/*.pdf`; batch read PDFs as raw text and reported **"✅ success, 70% confidence"** over a report containing `FlateDecode`/`endstream` and zero document text |
| H4 | `PDF_support.md` is documentation | **Falsified** | It is mangled Python source, duplicated byte-for-byte (both halves `md5 1d64e209…`). Archived to `legacy/` |
| H5 | Declared dependencies are used | **Falsified** | `requests`, `beautifulsoup4`, `pandas`, `openpyxl` were imported nowhere. `requests` also contradicted the local-only privacy promise |
| H6 | Extraction failures are reported | **Falsified** | Extractors caught everything and returned `""` — indistinguishable from a genuinely empty document |

Six for six. The repo's documentation described an intended tool; the code was
a different tool. That gap is the thing to keep testing for.

### The one that matters most

H3 is the defect worth remembering. H1 was loud — it crashed immediately and
anyone would have caught it. H3 was quiet: it produced a clean green checkmark,
a plausible 70% confidence score, and an HTML report with a professional
header — over PDF binary internals. For a tool whose whole purpose is helping
someone understand a medical or legal document they're about to sign, a
confident empty answer is worse than no answer.

**Generalisation:** wherever two code paths claim to do the same job, run the
same input through both and diff the outputs. Here `translator.py policy.pdf`
and `batch_translate.py policy.pdf` claimed equivalence and disagreed
completely. The single-file path extracted the text; the batch path never
called the extractor at all.

## Round 2 — verifying the fixes were real

Reverting the fixes and re-running was itself informative. The first attempt
was **inconclusive**: removing the fixes broke the test module's import
(`ExtractionError` no longer existed), so pytest failed at collection and
proved nothing about the individual tests. Isolating the two critical probes
against a pristine copy of the pre-fix code gave the actual before/after:

| Probe | Pre-fix | Post-fix |
|---|---|---|
| `<script>` in report | present, unescaped | escaped |
| `&` in report | corrupted markup | `&amp;` |
| Batch PDF → real text | absent | present |
| Batch PDF → `FlateDecode` | present | absent |

Worth noting: *a failed verification attempt is a result too.* "The test suite
errored" is not "the tests work" — it's an unknown, and it needed a second,
better-isolated run to resolve.

## Known unknowns — where to start next time

Things this pass did **not** resolve. Listed so they aren't mistaken for
settled:

- **Extraction is incomplete.** `legacy/PDF_support.md` still carries
  `# ... [Include all the other methods from the original translator] ...`
  markers. Some original method bodies may never have been carried into
  `translator.py`. Nobody has diffed the ancestor against the descendant
  term-by-term.
- **Detection accuracy is unmeasured.** `detect_document_type` is tested on
  four clean, obviously-domain-specific samples. Its behaviour on a real
  hybrid — a medical bill, which is simultaneously medical, insurance, and
  financial — is unknown. Keyword scoring will pick exactly one.
- **Confidence scores are arbitrary.** `calculate_confidence` starts at 0.70
  and nudges by hand-picked constants. No document has ever been checked
  against a known-good translation, so the number is not calibrated against
  anything. The README tells users to trust it (`<70% may need human review`).
  That advice currently has no evidence behind it.
- **Jargon replacement can nest.** `translate_jargon` substitutes in dictionary
  order across the whole text; a term whose plain-English expansion contains
  another dictionary term could be rewritten twice. Not observed in practice,
  not ruled out either.
- **OCR / scanned PDFs.** A scanned document yields no extractable text layer.
  The tool now raises `ExtractionError` rather than silently returning empty,
  but it offers the user no path forward.

## Adding to this record

When you run the loop again, append a round. Keep the falsified hypotheses even
after they're fixed — the fix only makes sense alongside the observation that
forced it, and a claim that was wrong once is worth re-testing after a
refactor. Same principle as `legacy/`: precedence carries.
