"""
01d_deeper_inspection.py
=========================
The previous test showed problem.json's first 1000 IDs are 1730-4398, while 
user-problem.json IDs go up to 6,906,522+. Two possibilities:
  (A) problem.json's IDs cover the full range — we just need to scan more of it
  (B) problem.json and user-problem.json use truly disjoint ID systems

This script:
  1. Scans the FULL problem.json to find the actual ID range and check how 
     many distinct IDs exist
  2. Tests whether the Pm_xxx integers from user-problem.json fall within 
     that range
  3. Inspects user-video.json (3 GB) — if it has user_id + video_id (V_xxx),
     and V_xxx IDs in course.json match, this gives us an ALTERNATIVE 
     multilevel structure: per-(user × course) video engagement, with 
     accuracy potentially recoverable via course-level aggregation.

USAGE:
    python 01d_deeper_inspection.py "/path/to/MOOCCubeX"

Runtime: ~3-5 minutes (scanning the full 1.2 GB problem.json).
"""

import sys
import json
import time
from pathlib import Path
from collections import Counter

if len(sys.argv) < 2:
    print("Usage: python 01d_deeper_inspection.py /path/to/MOOCCubeX")
    sys.exit(1)

base = Path(sys.argv[1])

# ============================================
# Part 1: Scan the FULL problem.json for ID range
# ============================================
print("=" * 78)
print("PART 1: Scanning full problem.json for ID range")
print("=" * 78)

prob_file = base / "entities" / "problem.json"
print(f"Reading {prob_file} (~1.2 GB)... this takes ~2 min")

t0 = time.time()
all_problem_ids = set()
min_id, max_id = float('inf'), 0
record_count = 0

with open(prob_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            pid = r.get('problem_id')
            if isinstance(pid, int):
                all_problem_ids.add(pid)
                if pid < min_id:
                    min_id = pid
                if pid > max_id:
                    max_id = pid
            record_count += 1
            if record_count % 200000 == 0:
                print(f"  ... {record_count:,} records, "
                      f"{len(all_problem_ids):,} unique IDs, "
                      f"range [{min_id}, {max_id}]")
        except json.JSONDecodeError:
            pass

print(f"\nDone in {time.time()-t0:.1f}s")
print(f"  Total records:           {record_count:,}")
print(f"  Unique problem_ids:      {len(all_problem_ids):,}")
print(f"  ID range:                [{min_id}, {max_id}]")

# ============================================
# Part 2: Check whether user-problem IDs match
# ============================================
print("\n" + "=" * 78)
print("PART 2: Checking if user-problem IDs match the problem.json ID set")
print("=" * 78)

up_file = base / "relations" / "user-problem.json"
print(f"Scanning first 1,000,000 records of user-problem.json...")

matches = 0
total_pm = 0
unmatched_samples = []
matched_samples = []
up_id_min, up_id_max = float('inf'), 0

with open(up_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 1_000_000:
            break
        try:
            r = json.loads(line.strip())
            pid_raw = r.get('problem_id', '')
            if pid_raw.startswith('Pm_'):
                pid_num = int(pid_raw[3:])
                total_pm += 1
                up_id_min = min(up_id_min, pid_num)
                up_id_max = max(up_id_max, pid_num)
                if pid_num in all_problem_ids:
                    matches += 1
                    if len(matched_samples) < 5:
                        matched_samples.append((pid_raw, pid_num))
                else:
                    if len(unmatched_samples) < 5:
                        unmatched_samples.append((pid_raw, pid_num))
        except (ValueError, json.JSONDecodeError):
            pass

print(f"\nResults from first 1M user-problem records:")
print(f"  Total Pm_ records:         {total_pm:,}")
print(f"  Matched problem.json IDs:  {matches:,} ({matches/total_pm*100 if total_pm else 0:.2f}%)")
print(f"  user-problem ID range:     [{up_id_min}, {up_id_max}]")
print(f"  problem.json ID range:     [{min_id}, {max_id}]")
print(f"  Overlap of ranges?         {up_id_min <= max_id and up_id_max >= min_id}")
print(f"\nMatched samples: {matched_samples}")
print(f"Unmatched samples: {unmatched_samples}")

# ============================================
# Part 3: Check user-video.json as alternative bridge
# ============================================
print("\n" + "=" * 78)
print("PART 3: Inspecting user-video.json (alternative bridge?)")
print("=" * 78)

uv_file = base / "relations" / "user-video.json"
if uv_file.exists():
    print(f"Reading first 5 records of {uv_file}...")
    with open(uv_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            try:
                r = json.loads(line.strip())
                print(f"  [Record {i+1}] keys = {list(r.keys())}")
                for k, v in list(r.items())[:8]:
                    v_str = str(v)
                    if len(v_str) > 150:
                        v_str = v_str[:150] + "..."
                    print(f"    {k}: {v_str}")
                print()
            except:
                pass
else:
    print("user-video.json not found.")

# ============================================
# Part 4: Inspect video.json — does it link to course?
# ============================================
print("\n" + "=" * 78)
print("PART 4: Inspecting video.json — does it have course_id?")
print("=" * 78)

video_file = base / "entities" / "video.json"
if video_file.exists():
    print(f"Reading first 3 records of {video_file}...")
    keys_seen = set()
    with open(video_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            try:
                r = json.loads(line.strip())
                keys_seen.update(r.keys())
                print(f"  [Record {i+1}] keys = {list(r.keys())}")
                for k, v in list(r.items())[:8]:
                    v_str = str(v)
                    if len(v_str) > 200:
                        v_str = v_str[:200] + "..."
                    print(f"    {k}: {v_str}")
                print()
            except:
                pass
    print(f"All distinct keys in video.json: {sorted(keys_seen)}")
else:
    print("video.json not found.")

# ============================================
# Part 5: Inspect other.json — sometimes contains relation tables
# ============================================
print("\n" + "=" * 78)
print("PART 5: Inspecting other.json — what's in it?")
print("=" * 78)

other_file = base / "entities" / "other.json"
if other_file.exists():
    size_mb = other_file.stat().st_size / (1024 * 1024)
    print(f"other.json is {size_mb:.1f} MB. Reading first 3 records...")
    with open(other_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            try:
                r = json.loads(line.strip())
                print(f"  [Record {i+1}] keys = {list(r.keys())}")
                for k, v in list(r.items())[:8]:
                    v_str = str(v)
                    if len(v_str) > 200:
                        v_str = v_str[:200] + "..."
                    print(f"    {k}: {v_str}")
                print()
            except:
                pass

# ============================================
# Final summary & next-step recommendation
# ============================================
print("\n" + "=" * 78)
print("SUMMARY & RECOMMENDATION")
print("=" * 78)

if matches > 0:
    print(f"""
GOOD NEWS: {matches/total_pm*100:.1f}% of user-problem IDs match problem.json.
The 'Pm_' -> int strip works correctly. The previous test failed only because 
problem.json's first 1000 records were a small subset of the full ID space.
The main extraction script (02_extract_user_course_accuracy.py) should work.
""")
else:
    print("""
PROBLEM CONFIRMED: user-problem.json IDs do NOT appear in problem.json at all.
This means the two files use disjoint ID systems despite the matching numeric 
appearance — likely they come from different platforms/exports merged into 
MOOCCubeX. We need an alternative approach (likely user-video.json as the 
multilevel structure source).
""")

print("Please paste this entire output back to me.")
