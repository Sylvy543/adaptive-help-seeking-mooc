# Release validation — 9 October 2026

The complete raw-data reconstruction and clean analysis pipeline finished successfully in the existing local Python 3.13.5 environment (versions pinned in requirements.txt). This was not a clean virtual-environment installation test or a cross-platform test.

- The full response log was scanned. All four rebuilt input tables matched the distributed inputs after key alignment: 16,389 student rows, 35,029 feature-count rows, 2,496 student-course rows and 26 raw feature labels. Raw-input numeric comparisons used rtol=atol=1e-13. Raw-file hashes remain in the local reconstruction output.
- All analysis and plotting subprocesses returned exit code zero, including model refits and 10,000-resample bootstrap calculations. Detailed stage status is in validation/execution_status.json; full runtime logs remain in the local outputs/raw_validation/logs directory and are not distributed.
- All 42 final OR4–OR7 CSV tables matched archived references under the comparison rules. Numeric comparisons use rtol=1e-6 and atol=1e-9; designated p/q fields use rtol=1e-5 and atol=1e-250. Provenance, method-description and warning text are not required to be identical. Course-contribution rows are aligned by course ID because near-zero numerical ties can change row order. This is numerical agreement, not byte-identical output. See validation/comparison.json and tools/compare_results.py.
- Raw coder agreement is 13/16, kappa 0.7159763314, with the paired item-resampling interval [0.4319526627, 1.0]. The unchanged raw coder ratings are preserved. Author-mapping reliability is computed separately.
- All seven figures redraw successfully. The published directory preserves the 14 supplied PNG/PDF files exactly. The redrawn Figure 6 correctly labels conditional shares of estimated variance components. Plot fonts, layout and PDF metadata need not match publication files byte for byte.
- Withdrawn dispersion-rescaled standard errors and Fisher-z Spearman intervals are not final results. Final bootstrap intervals appear in curated OR7 tables; stage05 intermediate snapshots explicitly leave them pending.

Statistical fit warnings remain in diagnostic outputs and local logs. Successful execution does not remove overdispersion, outcome-defined group limitations, or the exploratory observational scope. The new repository has not been uploaded to an online service.

The 38 data worksheets in the current OR5–OR7 submission workbooks were also compared against the repository CSVs: all passed (numeric rtol=1e-10, atol=1e-250; headers, row counts and nonnumeric values matched). See validation/worksheet_comparison.json. The two stage07 tables were separately checked against prior final outputs; all 14 publication files passed byte-for-byte source checks.
