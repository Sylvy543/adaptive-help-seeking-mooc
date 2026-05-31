"""
01_inspect_files.py
====================
A small diagnostic script that reads the FIRST FEW LINES of each large JSON 
file in MOOCCubeX to verify their structure. This runs in seconds (no full 
file scan), and tells us whether the main extraction script will work.

USAGE:
    python 01_inspect_files.py /path/to/MOOCCubeX

Replace /path/to/MOOCCubeX with the actual path on your computer, e.g.:
    python 01_inspect_files.py "/Volumes/MyDisk/Data/MOOCCubeX"
    python 01_inspect_files.py "D:/Data/MOOCCubeX"

The script prints the first 3 records from each file and stops.
"""

import sys
import json
from pathlib import Path

if len(sys.argv) < 2:
    print("ERROR: Please provide the path to the MOOCCubeX folder.")
    print("Example: python 01_inspect_files.py /path/to/MOOCCubeX")
    sys.exit(1)

base = Path(sys.argv[1])

files_to_check = [
    "relations/user-problem.json",
    "entities/problem.json",
    "entities/course.json",
]

for relpath in files_to_check:
    full = base / relpath
    print("=" * 78)
    print(f"FILE: {full}")
    print(f"Exists: {full.exists()}")
    
    if not full.exists():
        print("  >>> NOT FOUND. Check the path and try again.")
        continue
    
    size_mb = full.stat().st_size / (1024 * 1024)
    print(f"Size: {size_mb:.1f} MB")
    print("-" * 78)
    
    # Try reading the first 3 lines (assuming JSONL format)
    print("First 3 records (parsed as JSONL):")
    try:
        with open(full, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                if i >= 3:
                    break
                try:
                    record = json.loads(line)
                    # Print top-level keys
                    if isinstance(record, dict):
                        print(f"\n  [Record {i+1}] keys = {list(record.keys())}")
                        # Print first 200 chars of each field
                        for k, v in record.items():
                            v_repr = str(v)
                            if len(v_repr) > 200:
                                v_repr = v_repr[:200] + "..."
                            print(f"    {k}: {v_repr}")
                    else:
                        print(f"\n  [Record {i+1}] (not a dict) = {str(record)[:300]}")
                except json.JSONDecodeError as e:
                    print(f"\n  [Record {i+1}] JSON parse error: {e}")
                    print(f"    Raw line: {line[:300]}")
    except Exception as e:
        print(f"  Error reading file: {e}")
        # Fallback: try reading as a single big JSON
        print("  Trying to read as a single JSON object (top-level array)...")
        try:
            with open(full, 'r', encoding='utf-8') as f:
                # Just read the first 2000 chars to see what it looks like
                head = f.read(2000)
                print(f"  First 2000 chars of file:\n    {head}")
        except Exception as e2:
            print(f"  Error: {e2}")
    
    print()

print("=" * 78)
print("DIAGNOSIS COMPLETE")
print("=" * 78)
print("""
Please send me the output of this script. I will then verify the structure
and either confirm the main extraction script will work as-is, or adjust it
based on what we find.
""")
