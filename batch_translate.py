#!/usr/bin/env python3
“””
Batch process multiple documents for translation
Perfect for processing a folder full of medical records, contracts, etc.
“””

import argparse
import glob
from pathlib import Path
import time
from translator import PlainEnglishTranslator

def process_file(translator, file_path):
“”“Process a single file”””
try:
# Read the file
with open(file_path, ‘r’, encoding=‘utf-8’, errors=‘ignore’) as f:
content = f.read()

```
    if len(content.strip()) < 50:
        print(f"⚠️  Skipping {file_path} - too short")
        return False
    
    # Translate
    result = translator.translate_document(content)
    
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
```

def main():
parser = argparse.ArgumentParser(description=‘Batch translate multiple documents’)
parser.add_argument(‘pattern’, help=‘File pattern (e.g., “documents/*.txt” or “*.pdf”)’)
parser.add_argument(’–delay’, ‘-d’, type=float, default=0.5, help=‘Delay between files (seconds)’)
parser.add_argument(’–max-files’, ‘-m’, type=int, help=‘Maximum number of files to process’)

```
args = parser.parse_args()

# Find all matching files
files = glob.glob(args.pattern)

if not files:
    print(f"No files found matching pattern: {args.pattern}")
    return

if args.max_files:
    files = files[:args.max_files]

print(f"🚀 Processing {len(files)} files...")
print("="*60)

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
print("\n" + "="*60)
print(f"✅ Batch processing complete!")
print(f"   📊 {success_count}/{len(files)} files processed successfully")
print(f"   ⏱️  Total time: {elapsed:.1f} seconds")
print(f"   📁 Results in: translations/ folder")

# Show some stats
if success_count > 0:
    print(f"\n🎯 Quick tips:")
    print(f"   • Open HTML files in your browser for best viewing")
    print(f"   • Look for red flags (⚠️) first - those need attention")
    print(f"   • Check confidence scores - <70% may need human review")
    print(f"   • Action items (📋) tell you what to do next")
```

if **name** == “**main**”:
main()
