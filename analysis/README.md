# DORA analysis

## Main dose-map analysis

Run from the repository root:

```bash
MPLBACKEND=Agg python3 analyze_dora.py build/dora_traychannel_with_holder_120_10M.csv --events 10000000 --case-name dora_holder --output-dir /tmp/dora_results
python3 -m unittest discover -s tests -v
```

`--events` is the simulated primary count, not the number of scoring rows.
The current generator emits one gamma per event, randomly choosing one of two sources.
Existing CSVs contain positive deposition steps, without EventID; event-level MC uncertainty is unavailable.

Input must contain integer TLD IDs 0-95 and finite nonnegative energy in keV.
Malformed rows cause an error rather than being silently discarded. Extra columns are ignored by the dose-map analysis.

Outputs include run dose, dose per primary, central-four normalized dose, radial spatial SD, figures, and provenance JSON (input/analysis SHA-256 and settings).
`--target-mean` creates a display-only column. It does not change dose maps or comparison profiles and is not an absolute-dose prediction.

Normalization uses D6, D7, E6, E7 (IDs 41, 42, 53, 54), at approximately 6.364 mm radius.
The original graph D(r)/D(0) is retained in `Ref_norm_axis`; comparison uses the graph normalized at these same four positions.
Reference values outside 0-45 mm are unavailable. Radial bins containing any unsupported TLD are excluded from reference comparison.

Column migration: `Dose_Gy_raw` -> `Dose_Gy_run`; `Dose_Gy_scaled` -> `Dose_Gy_display_scaled` (NaN when disabled).
Radial `dose_std_Gy` -> `dose_spatial_std_Gy`; `norm_std` -> `norm_spatial_std`. These are spatial spread, not MC uncertainty.

## Other scripts

- `analyze_interaction_tags.py`: interaction-history analysis; six-column schema.
- `analyze_scatter_tags.py`: now reads the six-column schema and reports interaction history and depositing-track PDG. The older README warning about a five-column mapping was stale.
- `compare_dora_cases.py`: already normalizes each case using explicit `--events-a` and `--events-b`. The former same-event-count restriction was stale. These auxiliary readers still have their own permissive input filtering; they were not refactored in this cleanup.
- `legacy/`: historical scripts, not current analysis.

See `docs/known_issues.md` for unresolved geometry, seed and scoring limitations. Existing cases are not independent statistical replicates.

## Dose conversion convention (7 October 2026)

The main analysis now uses 1.602176634e-16 J/keV and the model-cylinder mass
derived from diameter 7 mm, thickness 1 mm and LiF density 2.635 g/cm3:
approximately 1.014066839e-4 kg. These are simulation model inputs, not measured
detector properties; recheck them against the run log when geometry/materials change.
The metadata records the mass, dimensions, density and conversion factor.

This replaces the former rounded 1.01e-4 kg and 1.60218e-16 J/keV convention.
New doses are approximately 0.401% lower than the old main-script values for the
same deposited energy. Normalized shapes and consistently calculated dose ratios
do not change. Existing output files were not rewritten. The historical motion
calculations already used the adopted convention.
