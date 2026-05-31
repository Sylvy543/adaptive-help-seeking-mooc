"""
01b_inspect_linkage.py
=======================
Second-round diagnostic: investigate how to link user-problem records 
to courses, given that:
  1. problem_id formats differ between user-problem.json (Pm_xxx) and 
     problem.json (numeric)
  2. problem.json doesn't have course_id; course.json links via 
     resource_id (V_xxx, video IDs).

This script:
  1. Inspects more user-problem records to confirm Pm_ format is consistent
  2. Inspects more problem.json records to look for any field that might 
     connect to courses
  3. Reads ALL of course.json (only ~43MB) and extracts the course->resource 
     mapping, so we can see what resource IDs are present
  4. Looks for video.json or other relation files that might link problem 
     IDs to course IDs

USAGE:
    python 01b_inspect_linkage.py "/path/to/MOOCCubeX"
"""

import sys
import json
from pathlib import Path
from collections import Counter

if len(sys.argv) < 2:
    print("Usage: python 01b_inspect_linkage.py /path/to/MOOCCubeX")
    sys.exit(1)

base = Path(sys.argv[1])

# ============================================
# Part 1: Sample 30 user-problem records to confirm Pm_ format
# ============================================
print("=" * 78)
print("PART 1: Confirming user-problem.json problem_id format")
print("=" * 78)

up_file = base / "relations" / "user-problem.json"
problem_id_prefixes = Counter()
sample_pids = []

with open(up_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 50:
            break
        try:
            r = json.loads(line.strip())
            pid = r.get('problem_id', '')
            if pid:
                # Track prefix (everything before underscore, or first 3 chars)
                prefix = pid.split('_')[0] if '_' in pid else pid[:3]
                problem_id_prefixes[prefix] += 1
                if len(sample_pids) < 5:
                    sample_pids.append(pid)
        except:
            pass

print(f"Sample problem_ids from user-problem.json: {sample_pids}")
print(f"problem_id prefix distribution (first 50): {dict(problem_id_prefixes)}")

# ============================================
# Part 2: Sample 30 problem.json records to inspect ID format
# ============================================
print("\n" + "=" * 78)
print("PART 2: Confirming problem.json problem_id format")
print("=" * 78)

prob_file = base / "entities" / "problem.json"
prob_id_types = Counter()
prob_id_samples = []
all_keys_seen = set()

with open(prob_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 50:
            break
        try:
            r = json.loads(line.strip())
            all_keys_seen.update(r.keys())
            pid = r.get('problem_id')
            if pid is not None:
                prob_id_types[type(pid).__name__] += 1
                if len(prob_id_samples) < 10:
                    prob_id_samples.append(pid)
        except:
            pass

print(f"Sample problem_ids from problem.json: {prob_id_samples}")
print(f"Type distribution: {dict(prob_id_types)}")
print(f"All keys seen in problem.json: {sorted(all_keys_seen)}")

# ============================================
# Part 3: Search problem.json for any field that links to courses
# ============================================
print("\n" + "=" * 78)
print("PART 3: Searching problem.json for any course-linking field")
print("=" * 78)
print("Looking through 1000 records to see all possible field values...")

course_like_fields = ['course_id', 'course', 'from_course', 'cid', 'C_id']
field_examples = {f: [] for f in course_like_fields}
exercise_id_samples = []
context_id_samples = []

with open(prob_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 1000:
            break
        try:
            r = json.loads(line.strip())
            for f_name in course_like_fields:
                if f_name in r:
                    if len(field_examples[f_name]) < 3:
                        field_examples[f_name].append(r[f_name])
            if 'exercise_id' in r and len(exercise_id_samples) < 5:
                exercise_id_samples.append(r['exercise_id'])
            if 'context_id' in r and len(context_id_samples) < 5:
                context_id_samples.append(r['context_id'])
        except:
            pass

print(f"\nDirect course-link fields found: ")
for f_name, examples in field_examples.items():
    if examples:
        print(f"  {f_name}: {examples}")
    else:
        print(f"  {f_name}: NOT FOUND")

print(f"\nexercise_id samples: {exercise_id_samples}")
print(f"context_id samples: {context_id_samples}")

# ============================================
# Part 4: Read course.json fully and check what's in resource
# ============================================
print("\n" + "=" * 78)
print("PART 4: Reading course.json and inspecting resource field")
print("=" * 78)

course_file = base / "entities" / "course.json"
course_resource_id_prefixes = Counter()
course_count = 0
sample_course = None

with open(course_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            c = json.loads(line.strip())
            course_count += 1
            if course_count == 1:
                sample_course = c
            resources = c.get('resource', [])
            for res in resources:
                rid = res.get('resource_id', '')
                if rid:
                    prefix = rid.split('_')[0] if '_' in rid else rid[:2]
                    course_resource_id_prefixes[prefix] += 1
        except:
            pass

print(f"Total courses: {course_count}")
print(f"Resource ID prefix distribution: {dict(course_resource_id_prefixes)}")
print(f"\nSample first course (truncated):")
if sample_course:
    print(f"  id: {sample_course.get('id')}")
    print(f"  name: {sample_course.get('name')}")
    print(f"  resource[0:2]: {sample_course.get('resource', [])[:2]}")

# ============================================
# Part 5: Check if there's a problem-course or problem-exercise relation file
# ============================================
print("\n" + "=" * 78)
print("PART 5: Looking for additional relation files in MOOCCubeX")
print("=" * 78)

relations_dir = base / "relations"
print(f"Files in {relations_dir}:")
for f in sorted(relations_dir.iterdir()):
    if f.is_file():
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name}: {size_mb:.1f} MB")

# Sample any other relation files we haven't seen
other_relations = ['exercise-problem.json', 'problem-course.json', 'course-problem.json',
                   'video-course.json', 'course-video.json', 'concept-course.json',
                   'problem-exercise.json', 'exercise-course.json']
print(f"\nChecking for known related files:")
for rf in other_relations:
    full = relations_dir / rf
    if full.exists():
        print(f"  ✓ FOUND: {full.name} ({full.stat().st_size / (1024*1024):.1f} MB)")
        # Show first record
        try:
            with open(full, 'r', encoding='utf-8') as f:
                first = f.readline().strip()
                print(f"    First record: {first[:300]}")
        except:
            pass

# Also check entities dir for additional files
entities_dir = base / "entities"
print(f"\nFiles in {entities_dir}:")
for f in sorted(entities_dir.iterdir()):
    if f.is_file():
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name}: {size_mb:.1f} MB")

print("\n" + "=" * 78)
print("DIAGNOSIS COMPLETE — please paste this entire output back to me.")
print("=" * 78)
