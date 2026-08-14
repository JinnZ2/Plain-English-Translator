# Legacy

Superseded files are archived here instead of being deleted.

**Precedence still carries.** A file that has been replaced is not worthless — it
is the record of how the current code got its shape. When you are about to
"simplify" something in `translator.py` and it looks arbitrary, the answer is
often in here: the original author had a reason, and the reason outlived the
file. Read the ancestor before you overwrite the descendant.

Nothing in this folder is imported, executed, or tested. It is not on the
package path (`setup.py` ships `py_modules=["translator"]` only). Treat it as
read-only history.

## Contents

### `PDF_support.md`

- **Was**: the original working draft of the translator, pasted into a Markdown
  file. Despite the `.md` extension it is Python source, not documentation.
- **Superseded by**: `translator.py`, extracted from it in commit `9100e6f`
  (2026-03-22).
- **Why it was retired**: three defects made it unrunnable as-is.
  1. The same ~580 lines appear **twice**, byte-for-byte. Both halves hash
     identically (`md5 1d64e209…`); the file is a doubled paste.
  2. Smart quotes (`“””` instead of `"""`) and Markdown-mangled dunders
     (`def **init**` instead of `def __init__`) — the result of a copy through
     a rich-text editor.
  3. Indentation was flattened, and stray ` ``` ` fences sit inside the code.
- **Why it is kept**: it is the provenance of every jargon term, red-flag
  phrase, and sneaky-clause regex in `translator.py`. If a pattern in the
  current code looks wrong, check here first — the extraction may have dropped
  or altered it. It also still contains method bodies that were stubbed out
  during extraction (see the `# ... [Include all the other methods ...]`
  markers) and never fully carried across.

## Adding to this folder

When you retire a file, move it here with `git mv` (so history follows it) and
add an entry above recording four things: what it **was**, what **superseded**
it, **why** it was retired, and **why it is still worth keeping**. An archive
without provenance is just clutter — the note is the point, not the file.
