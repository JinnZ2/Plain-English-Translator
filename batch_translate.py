#!/usr/bin/env python3
"""
Batch process multiple documents for translation
Perfect for processing a folder full of medical records, contracts, etc.
"""

import argparse
import glob
from pathlib import Path
import time
from translator import PlainEnglishTranslator


def process_file(translator, file_path):
    """Process a single file"""
    try:
        # Route through the same extractor the single-file CLI uses, so PDFs and
        # Word documents are decoded rather than read as raw bytes. Reading a
        # .pdf with open(..., 'r', errors='ignore') silently yields the file's
        # binary internals, which then "translate" into a confident-looking
        # report containing no document text at all.
        result = translator.translate_document_from_file(file_path)

        # Save with original filename
        output_name = Path(file_path).stem
        translator.save_translation(result, f"batch_{output_name}")

        print(f"✅ {file_path} → translations/batch_{output_name}.html ({result.confidence_score:.0%} confidence)")

        # Show quick summary
        if result.red_flags:
            print(f"   ⚠️  {len(result.red_flags)} red flags found!")
        if result.your_rights:
            print(f"   ✅ {len(result.your_rights)} rights identified")
        if result.action_items:
            print(f"   📋 {len(result.action_items)} action items")

        return True

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Batch translate multiple documents')
    parser.add_argument(
        'pattern',
        nargs='+',
        help='File pattern (e.g., "documents/*.txt") or an explicit list of files. '
             'Accepts both, so an unquoted pattern the shell already expanded still works.',
    )
    parser.add_argument('--delay', '-d', type=float, default=0.5, help='Delay between files (seconds)')
    parser.add_argument('--max-files', '-m', type=int, help='Maximum number of files to process')

    args = parser.parse_args()

    # Expand each argument as a glob, keeping literal paths that match nothing
    # in the glob sense but exist on disk. Duplicates are dropped while
    # preserving the order given.
    files = []
    for pattern in args.pattern:
        matches = sorted(glob.glob(pattern)) or ([pattern] if Path(pattern).is_file() else [])
        for match in matches:
            if match not in files:
                files.append(match)

    if not files:
        print(f"No files found matching: {' '.join(args.pattern)}")
        return

    if args.max_files:
        files = files[:args.max_files]

    print(f"🚀 Processing {len(files)} files...")
    print("=" * 60)

    # Create translator
    translator = PlainEnglishTranslator()

    # Process each file
    success_count = 0
    start_time = time.time()

    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file_path}")

        if process_file(translator, file_path):
            success_count += 1

        # Don't hammer the system
        if args.delay > 0 and i < len(files):
            time.sleep(args.delay)

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ Batch processing complete!")
    print(f"   📊 {success_count}/{len(files)} files processed successfully")
    print(f"   ⏱️  Total time: {elapsed:.1f} seconds")
    print("   📁 Results in: translations/ folder")

    # Show some stats
    if success_count > 0:
        print("\n🎯 Quick tips:")
        print("   • Open HTML files in your browser for best viewing")
        print("   • Look for red flags (⚠️) first - those need attention")
        print("   • Check confidence scores - <70% may need human review")
        print("   • Action items (📋) tell you what to do next")


if __name__ == "__main__":
    main()
