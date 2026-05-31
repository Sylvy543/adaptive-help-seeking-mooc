# 01_data_extraction

Scripts that build the intermediate `user_course_accuracy.csv` file from the raw MOOCCubeX dataset. This file is required as input by `02_analysis/multilevel_analysis.py`.

## What this directory contains

The five scripts here are run in numerical order:

| Script | Purpose |
|---|---|
| `01_inspect_files.py` | Initial diagnostic; verifies that all expected MOOCCubeX files are present and reports their dimensions |
| `01b_inspect_linkage.py` | Inspects the linkage between `user-problem.json`, `problem.json`, and `course.json` to confirm that problem IDs can be mapped to courses |
| `01c_verify_id_match.py` | Confirms the ID-matching strategy: problem IDs in `user-problem.json` are prefixed with `Pm_`, which must be stripped before matching to `problem.json`'s `id` field; matching then proceeds via the `exercise_id` field to the resource list in `course.json` |
| `01d_deeper_inspection.py` | Sample-level diagnostics on the matching success rate; documents the proportion of AI-sample users whose problem attempts can be linked to identifiable courses |
| `02_extract_user_course_accuracy.py` | Final extraction; produces `user_course_accuracy.csv` with one row per `(user_id, course_id)` cell |

## Inputs expected

The scripts expect the following files at paths configurable at the top of `01_inspect_files.py`:

```
relations/user-problem.json    (~22.45 GB)
entities/problem.json          (~1.29 GB)
entities/course.json           (~44.7 MB)
```

## Output

`user_course_accuracy.csv` (the file that `02_analysis/multilevel_analysis.py` reads), structured as:

| Column | Type | Description |
|---|---|---|
| `user_id` | string | MOOCCubeX user ID |
| `course_id` | string | MOOCCubeX course ID |
| `n_attempts` | int | Number of problem attempts in this (user, course) cell |
| `n_correct` | int | Number of correct attempts |
| `accuracy_pct` | float | Percentage correct (0–100) |

The file has approximately 143,385 rows; after filtering to cells with `n_attempts >= 5`, the multilevel analysis uses 1,983 cells across 396 courses.

## Important notes on data attrition

Of the 16,389 students in the main analytic sample (built from `combined_ai_learning_data.csv`), a subset could be linked to identifiable courses after the linkage. Of these, 1,708 students had at least one (user, course) cell meeting the `n_attempts >= 5` inclusion threshold and form the analytic sample for the multilevel model reported in Section 4.7.3 (1,983 cells across 396 courses). Two sources contribute to this attrition:

1. Approximately 30% of problem IDs in `user-problem.json` do not appear in `problem.json` — these problems cannot be linked to a course
2. Of the remaining problems, a portion map to exercises that do not appear in any course's resource list

This attrition is documented in the manuscript Section 4.7.3 and as a caveat in Section 5.5 (Limitations).

## Running the scripts

```bash
# From the repository root, after installing dependencies:
cd 01_data_extraction/
python 01_inspect_files.py        # First — verifies file paths
python 01b_inspect_linkage.py     # Diagnostic
python 01c_verify_id_match.py     # Diagnostic
python 02_extract_user_course_accuracy.py    # Produces the final CSV
```

Total runtime on a modern laptop: about 30 minutes (dominated by the streaming parse of the 22.45 GB `user-problem.json`).

## Memory notes

`user-problem.json` is too large to load into memory in full. The extraction script reads it line by line as JSONL (each line is one independent JSON record), so the file is never held in memory in full. Peak memory during extraction is approximately 4–6 GB.
