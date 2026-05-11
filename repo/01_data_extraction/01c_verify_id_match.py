"""
01c_verify_id_match.py
=======================
Quick test: verify that stripping 'Pm_' prefix from user-problem.json 
problem_ids yields integers that match problem.json's problem_id values.

USAGE:
    python 01c_verify_id_match.py "/path/to/MOOCCubeX"
"""

import sys
import json
from pathlib import Path

base = Path(sys.argv[1])

# Step 1: Collect first 1000 numeric problem_ids from problem.json
print("Reading first 1000 problem_ids from problem.json...")
prob_ids_numeric = set()
with open(base / "entities" / "problem.json", 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 1000:
            break
        try:
            r = json.loads(line.strip())
            pid = r.get('problem_id')
            if isinstance(pid, int):
                prob_ids_numeric.add(pid)
        except:
            pass

print(f"Got {len(prob_ids_numeric)} numeric IDs. Range: {min(prob_ids_numeric)} - {max(prob_ids_numeric)}")
print(f"Sample: {list(prob_ids_numeric)[:10]}")

# Step 2: Read user-problem.json and try to match
print("\nScanning first 500,000 user-problem records to test matching...")
matches = 0
total = 0
unmatched_samples = []
matched_samples = []

with open(base / "relations" / "user-problem.json", 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 500000:
            break
        try:
            r = json.loads(line.strip())
            pid_raw = r.get('problem_id', '')
            if pid_raw.startswith('Pm_'):
                pid_num = int(pid_raw[3:])  # strip 'Pm_'
                total += 1
                if pid_num in prob_ids_numeric:
                    matches += 1
                    if len(matched_samples) < 5:
                        matched_samples.append((pid_raw, pid_num))
                else:
                    if len(unmatched_samples) < 5:
                        unmatched_samples.append((pid_raw, pid_num))
        except:
            pass

print(f"\nResults from 500k user-problem records:")
print(f"  Total Pm_ records:      {total:,}")
print(f"  Matched our 1000 sample:{matches:,}")
print(f"  Match rate:             {matches/total*100 if total else 0:.2f}%")

print(f"\nMatched samples: {matched_samples}")
print(f"Unmatched samples (likely outside our 1000-record problem.json sample): {unmatched_samples}")

print("\n" + "="*70)
print("CONCLUSION:")
if matches > 0:
    print("  ✓ ID format strip ('Pm_' -> integer) WORKS for matching to problem.json")
    print("  Most 'unmatched' here are because we only loaded 1000 problems.")
    print("  In the real run we'll load all ~1.8M problems, so match rate will be near 100%.")
else:
    print("  ✗ No matches found — the ID format hypothesis is wrong.")
    print("  Please paste this output back to me.")
