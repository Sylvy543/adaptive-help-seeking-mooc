"""
02_extract_user_course_accuracy.py  (v2 - via exercise_id bridge)
==================================================================
Extracts per-(user × course) accuracy from MOOCCubeX.

LINKAGE STRATEGY (as confirmed by diagnostic):
  user-problem.json:  user_id, problem_id (e.g. 'Pm_6906522'), is_correct
  problem.json:       problem_id (numeric, e.g. 6906522), exercise_id (e.g. 'Ex_856')
  course.json:        id (e.g. 'C_584313'), resource list containing 'Ex_xxx' entries
  
  Connection path:
    Pm_6906522 → strip 'Pm_' → 6906522 → problem.json → Ex_856 → course.json → C_xxx

USAGE:
    python 02_extract_user_course_accuracy.py "/path/to/MOOCCubeX" [output.csv]

EXPECTED RUNTIME: 30-60 minutes (Phase 3 dominates).
EXPECTED OUTPUT SIZE: 10-50 MB.
"""

import sys
import json
import time
from pathlib import Path
from collections import defaultdict
import csv

if len(sys.argv) < 2:
    print("Usage: python 02_extract_user_course_accuracy.py /path/to/MOOCCubeX [output.csv]")
    sys.exit(1)

base = Path(sys.argv[1])
output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("user_course_accuracy.csv")

course_file = base / "entities" / "course.json"
problem_file = base / "entities" / "problem.json"
user_problem_file = base / "relations" / "user-problem.json"

for f in [course_file, problem_file, user_problem_file]:
    if not f.exists():
        print(f"ERROR: Cannot find {f}")
        sys.exit(1)

# ==========================================================================
# PHASE 1: Build exercise_id -> course_id map from course.json
# ==========================================================================
print("=" * 78)
print("PHASE 1: Building exercise_id -> course_id map (from course.json)")
print("=" * 78)
print(f"Reading {course_file} (~43 MB)...")

t0 = time.time()
exercise_to_course = {}
ambiguous_exercise = 0
exercise_count = 0
course_count = 0

with open(course_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            c = json.loads(line)
            cid = c.get('id')
            if not cid:
                continue
            course_count += 1
            
            for res in c.get('resource', []):
                rid = res.get('resource_id', '')
                if rid.startswith('Ex_'):
                    exercise_count += 1
                    if rid in exercise_to_course:
                        if exercise_to_course[rid] != cid:
                            ambiguous_exercise += 1
                    else:
                        exercise_to_course[rid] = cid
        except json.JSONDecodeError:
            continue

print(f"PHASE 1 done in {time.time()-t0:.1f}s")
print(f"  Courses processed:                 {course_count:,}")
print(f"  Exercise references in courses:    {exercise_count:,}")
print(f"  Unique Ex_id -> course mappings:   {len(exercise_to_course):,}")
print(f"  Ambiguous exercises (>=2 courses): {ambiguous_exercise:,}")

if not exercise_to_course:
    print("\nERROR: No Ex_ resources found in course.json. Aborting.")
    sys.exit(1)

print("\nSample Ex_ -> course mappings:")
for i, (eid, cid) in enumerate(exercise_to_course.items()):
    if i >= 5:
        break
    print(f"  {eid} -> {cid}")

# ==========================================================================
# PHASE 2: Build problem_id (numeric) -> course_id map via problem.json
# ==========================================================================
print("\n" + "=" * 78)
print("PHASE 2: Building problem_id -> course_id map (via problem.json)")
print("=" * 78)
print(f"Reading {problem_file} (~1.2 GB)...")

t0 = time.time()
problem_to_course = {}
problem_count = 0
matched_via_exercise = 0
no_exercise_id = 0
exercise_not_in_course = 0

with open(problem_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            problem_count += 1
            
            pid = r.get('problem_id')
            eid = r.get('exercise_id')
            
            if pid is None:
                continue
            if not eid:
                no_exercise_id += 1
                continue
            
            cid = exercise_to_course.get(eid)
            if cid is None:
                exercise_not_in_course += 1
                continue
            
            problem_to_course[pid] = cid
            matched_via_exercise += 1
            
            if problem_count % 500000 == 0:
                el = time.time() - t0
                print(f"  ... read {problem_count:,} problems "
                      f"({len(problem_to_course):,} mapped) in {el:.1f}s")
        except json.JSONDecodeError:
            continue

print(f"\nPHASE 2 done in {time.time()-t0:.1f}s")
print(f"  Total problems read:                       {problem_count:,}")
print(f"  Successfully mapped to course:             {matched_via_exercise:,}")
print(f"  Problems without exercise_id:              {no_exercise_id:,}")
print(f"  Problems with exercise not in any course:  {exercise_not_in_course:,}")

if not problem_to_course:
    print("\nERROR: Failed to build problem -> course map. Aborting.")
    sys.exit(1)

print(f"\nSample problem -> course mappings:")
for i, (pid, cid) in enumerate(problem_to_course.items()):
    if i >= 5:
        break
    print(f"  problem_id {pid} -> {cid}")

# Free memory
del exercise_to_course

# ==========================================================================
# PHASE 3: Stream user-problem.json and aggregate per (user, course)
# ==========================================================================
print("\n" + "=" * 78)
print("PHASE 3: Streaming user-problem.json (~21 GB)")
print("=" * 78)
print(f"Reading {user_problem_file}...")
print("This will take 30-60 minutes. Progress shown every 1M records.\n")

ucd_agg = defaultdict(lambda: [0, 0])

t0 = time.time()
record_count = 0
matched_count = 0
no_pm_prefix = 0
pid_not_in_problem = 0
parse_errors = 0
malformed_correct = 0

with open(user_problem_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record_count += 1
        try:
            rec = json.loads(line)
            
            uid = rec.get('user_id')
            pid_raw = rec.get('problem_id', '')
            is_correct = rec.get('is_correct')
            
            if uid is None or not pid_raw:
                continue
            
            if not pid_raw.startswith('Pm_'):
                no_pm_prefix += 1
                continue
            
            try:
                pid_num = int(pid_raw[3:])
            except ValueError:
                no_pm_prefix += 1
                continue
            
            cid = problem_to_course.get(pid_num)
            if cid is None:
                pid_not_in_problem += 1
                continue
            
            if isinstance(is_correct, bool):
                correct_val = 1 if is_correct else 0
            elif isinstance(is_correct, (int, float)):
                correct_val = 1 if is_correct > 0 else 0
            else:
                malformed_correct += 1
                continue
            
            key = (uid, cid)
            ucd_agg[key][0] += 1
            ucd_agg[key][1] += correct_val
            matched_count += 1
            
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        
        if record_count % 1_000_000 == 0:
            elapsed = time.time() - t0
            rate = record_count / elapsed if elapsed > 0 else 0
            print(f"  ... {record_count:,} records "
                  f"({matched_count:,} matched, "
                  f"{pid_not_in_problem:,} unmatched) "
                  f"@ {rate:,.0f} rec/s, elapsed {elapsed/60:.1f} min")

elapsed = time.time() - t0
print(f"\nPHASE 3 done in {elapsed/60:.1f} minutes")
print(f"  Total records processed:               {record_count:,}")
mr = matched_count/record_count*100 if record_count else 0
print(f"  Successfully matched to a course:      {matched_count:,} ({mr:.1f}%)")
print(f"  Records without Pm_ prefix:            {no_pm_prefix:,}")
print(f"  Records with problem_id not in map:    {pid_not_in_problem:,}")
print(f"  Records with malformed is_correct:     {malformed_correct:,}")
print(f"  Parse errors:                          {parse_errors:,}")
print(f"  Unique (user, course) pairs:           {len(ucd_agg):,}")

# ==========================================================================
# PHASE 4: Write output CSV
# ==========================================================================
print("\n" + "=" * 78)
print(f"PHASE 4: Writing output to {output_path}")
print("=" * 78)

with open(output_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['user_id', 'course_id', 'n_attempts', 'n_correct', 'accuracy_pct'])
    for (uid, cid), (total, correct) in ucd_agg.items():
        accuracy_pct = (correct / total * 100) if total > 0 else 0
        writer.writerow([uid, cid, total, correct, f"{accuracy_pct:.2f}"])

output_size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"Done.")
print(f"  Output file: {output_path}")
print(f"  File size:   {output_size_mb:.1f} MB")
print(f"  Rows:        {len(ucd_agg):,}")

print("\nFirst 5 rows:")
with open(output_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 6:
            break
        print(f"  {line.strip()}")

print("\n" + "=" * 78)
print(f"READY TO UPLOAD: {output_path}")
print("=" * 78)
