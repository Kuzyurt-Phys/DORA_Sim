import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


KEV_TO_JOULE = 1.602176634e-16

# Model values, not measured detector properties. Match DetectorConstruction's
# 7 mm diameter, 1 mm thick G4_LITHIUM_FLUORIDE pellet and logged density.
# Recheck these inputs if the simulated material or pellet dimensions change.
TLD_DIAMETER_MM = 7.0
TLD_THICKNESS_MM = 1.0
TLD_DENSITY_G_CM3 = 2.635
TLD_MASS_KG = (
    TLD_DENSITY_G_CM3
    * np.pi * (TLD_DIAMETER_MM / 20.0)**2
    * (TLD_THICKNESS_MM / 10.0) / 1000.0
)

N_ROWS = 8
N_COLS = 12

HOLDER_X_MM = 127.55
HOLDER_Y_MM = 85.3
PITCH_MM = 9.0
START_X_MM = -0.5 * HOLDER_X_MM + 14.275
START_Y_MM =  0.5 * HOLDER_Y_MM - 11.15

# Reference normalized DORA field profile from the graph you sent.
# r in mm, normalized dose rate D(r)/D(0).
REF_R_MM = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 45.0])
REF_NORM = np.array([1.000, 0.993, 0.973, 0.941, 0.900, 0.877])


def reference_center_mean() -> float:
    radii = [
        np.hypot(START_X_MM + col * PITCH_MM, START_Y_MM - row * PITCH_MM)
        for row in (3, 4) for col in (5, 6)
    ]
    return float(np.interp(radii, REF_R_MM, REF_NORM).mean())


def load_geant4_csv(filename: str) -> pd.DataFrame:
    """Read scoring rows without silently dropping or truncating invalid data."""
    try:
        raw = pd.read_csv(filename, comment="#", header=None)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("CSV contains no scoring rows.") from exc
    if raw.empty or raw.shape[1] < 2:
        raise ValueError("CSV must contain scoring rows with TLD_ID and Edep_keV.")
    df = raw.iloc[:, :2].copy()
    df.columns = ["TLD_ID", "Edep_keV"]
    df = df.apply(pd.to_numeric, errors="coerce")
    ids = df["TLD_ID"]
    valid = (
        np.isfinite(df).all(axis=1)
        & (ids == np.floor(ids))
        & ids.between(0, N_ROWS * N_COLS - 1)
        & (df["Edep_keV"] >= 0)
    )
    if not valid.all():
        bad = (np.flatnonzero(~valid)[:10] + 1).tolist()
        raise ValueError(
            f"Invalid scoring data in {int((~valid).sum())} row(s); "
            f"first data-row numbers: {bad}. "
            "Require integer TLD IDs 0-95 and finite nonnegative energy. "
            "No rows were silently discarded."
        )
    df["TLD_ID"] = ids.astype(int)
    return df


def make_tld_table(df: pd.DataFrame,n_events: int,target_mean: float | None,holder_x_mm: float = 0.0,) -> pd.DataFrame:
    if not isinstance(n_events, (int, np.integer)) or isinstance(n_events, bool) or n_events <= 0:
        raise ValueError("Number of simulated primaries must be positive.")
    if target_mean is not None and (not np.isfinite(target_mean) or target_mean <= 0):
        raise ValueError("Display target mean must be finite and positive.")
    all_ids = pd.DataFrame({"TLD_ID": np.arange(N_ROWS * N_COLS)})

    edep = df.groupby("TLD_ID", as_index=False)["Edep_keV"].sum()
    out = all_ids.merge(edep, on="TLD_ID", how="left")
    out["Edep_keV"] = out["Edep_keV"].fillna(0.0)

    rows = []
    cols = []
    xs = []
    ys = []
    rs = []

    for tld_id in out["TLD_ID"]:
        row, col = divmod(int(tld_id), N_COLS)
        x = START_X_MM + col * PITCH_MM
        y = START_Y_MM - row * PITCH_MM
        r = np.sqrt(x*x + y*y)

        rows.append(row)
        cols.append(col)
        xs.append(x)
        ys.append(y)
        rs.append(r)

    out["row_index"] = rows
    out["col_index"] = cols
    out["row_label"] = [chr(ord("A") + r) for r in rows]
    out["col_label"] = [c + 1 for c in cols]
    out["x_mm"] = xs
    out["y_mm"] = ys
    out["r_mm"] = rs

    out["Dose_Gy_run"] = (
        out["Edep_keV"]
        * KEV_TO_JOULE
        / TLD_MASS_KG
    )

    out["Dose_Gy_per_primary"] = (
        out["Dose_Gy_run"]
        / float(n_events)
    )

    run_mean_dose = out["Dose_Gy_run"].mean()

    if target_mean is not None:
        if run_mean_dose <= 0:
            raise ValueError(
                "Run mean dose is zero; cannot apply display scaling."
            )

        display_scale_factor = (
            target_mean / run_mean_dose
        )

        out["Dose_Gy_display_scaled"] = (
            out["Dose_Gy_run"]
            * display_scale_factor
        )
    else:
        out["Dose_Gy_display_scaled"] = np.nan

    # Center reference: average of the four cells nearest the geometrical center.
    # Rows D/E and columns 6/7 in human notation.
    center_mask = (
        ((out["row_index"] == 3) | (out["row_index"] == 4)) &
        ((out["col_index"] == 5) | (out["col_index"] == 6))
    )

    center_dose = out.loc[center_mask, "Dose_Gy_per_primary"].mean()
    if not np.isfinite(center_dose) or center_dose <= 0:
        raise ValueError("Central-four mean dose must be finite and positive.")

    out["Norm_to_center"] = out["Dose_Gy_per_primary"] / center_dose
    # Preserve the graph's D(r)/D(0), then use the same central-four
    # normalization as the simulation for shape comparison.
    out["Ref_norm_axis"] = np.interp(
        out["r_mm"], REF_R_MM, REF_NORM, left=np.nan, right=np.nan
    )
    out["Ref_norm_from_graph"] = out["Ref_norm_axis"] / reference_center_mean()
    out["Norm_minus_ref"] = out["Norm_to_center"] - out["Ref_norm_from_graph"]

    return out


def make_maps(out: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    dose_map = np.zeros((N_ROWS, N_COLS))
    norm_map = np.zeros((N_ROWS, N_COLS))

    for _, row in out.iterrows():
        r = int(row["row_index"])
        c = int(row["col_index"])
        dose_map[r, c] = row["Dose_Gy_run"]
        norm_map[r, c] = row["Norm_to_center"]

    return dose_map, norm_map


def radial_profile(out: pd.DataFrame, bin_width_mm: float = 5.0) -> pd.DataFrame:
    if not np.isfinite(bin_width_mm) or bin_width_mm <= 0:
        raise ValueError("Radial bin width must be finite and positive.")
    max_r = out["r_mm"].max()
    bins = np.arange(0.0, max_r + bin_width_mm, bin_width_mm)

    tmp = out.copy()
    tmp["r_bin"] = pd.cut(tmp["r_mm"], bins=bins, include_lowest=True)

    prof = tmp.groupby("r_bin", observed=False).agg(
        r_mean_mm=("r_mm", "mean"),
        n_TLD=("TLD_ID", "count"),
        dose_mean_Gy=("Dose_Gy_run", "mean"),
        dose_spatial_std_Gy=("Dose_Gy_run", "std"),
        norm_mean=("Norm_to_center", "mean"),
        norm_spatial_std=("Norm_to_center", "std"),
        ref_norm_mean=("Ref_norm_from_graph", "mean"),
        n_reference_TLD=("Ref_norm_from_graph", "count"),
    ).reset_index()

    prof = prof.dropna(subset=["r_mean_mm"])
    # Compare only bins for which every TLD has a valid reference.
    prof.loc[prof["n_reference_TLD"] != prof["n_TLD"], "ref_norm_mean"] = np.nan
    prof["norm_minus_ref"] = prof["norm_mean"] - prof["ref_norm_mean"]

    return prof


def plot_heatmap(dose_map: np.ndarray, title: str, output: str) -> None:
    fig, ax = plt.subplots(figsize=(14, 8))

    im = ax.imshow(dose_map, vmin=0.0, vmax=np.nanmax(dose_map))

    ax.set_xticks(np.arange(N_COLS))
    ax.set_xticklabels(np.arange(1, N_COLS + 1))

    ax.set_yticks(np.arange(N_ROWS))
    ax.set_yticklabels([chr(ord("A") + i) for i in range(N_ROWS)])

    for i in range(N_ROWS):
        for j in range(N_COLS):
            ax.text(j, i, f"{dose_map[i, j]:.2e}",
                    ha="center", va="center", fontsize=7)

    ax.set_title(title)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Absorbed dose per simulation run (Gy)")

    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def plot_radial_profile(prof: pd.DataFrame, output: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.errorbar(
        prof["r_mean_mm"],
        prof["norm_mean"],
        yerr=prof["norm_spatial_std"],
        fmt="o",
        capsize=3,
        label="Simulation (bars: spatial SD across TLDs, not MC uncertainty)"
    )

    ax.plot(REF_R_MM, REF_NORM / reference_center_mean(), marker="s",
            label="DORA graph (renormalized to central four)")

    ax.set_xlabel("Distance from central axis r (mm)")
    ax.set_ylabel("Dose / mean dose at central four TLDs")
    ax.set_title("Normalized radial profile")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="Geant4 CSV file, e.g. DORA_Results_nt_TLD_Scoring_t0.csv")
    parser.add_argument("--events", type=int, required=True, help="Number of simulated primary gammas")
    parser.add_argument("--target-mean", type=float, default=None,
                        help="Optional display-only target mean dose in Gy, e.g. 1.13")
    parser.add_argument("--case-name", default="DORA_case",
                        help="Name used in output filenames")

    parser.add_argument("--output-dir", type=Path, default=Path("."),
                        help="Directory for generated CSV, PNG and provenance JSON files")
    args = parser.parse_args()
    if not args.case_name or Path(args.case_name).name != args.case_name or args.case_name in (".", ".."):
        parser.error("--case-name must be a filename prefix without directory components")

    df = load_geant4_csv(args.csv_file)
    out = make_tld_table(df, args.events, args.target_mean)
    dose_map, norm_map = make_maps(out)
    prof = radial_profile(out)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    case = str(args.output_dir / args.case_name)

    out.to_csv(f"{case}_processed_tld.csv", index=False)
    pd.DataFrame(
        dose_map,
        index=[chr(ord("A") + i) for i in range(N_ROWS)],
        columns=np.arange(1, N_COLS + 1)
    ).to_csv(f"{case}_dose_map_Gy.csv")

    pd.DataFrame(
        norm_map,
        index=[chr(ord("A") + i) for i in range(N_ROWS)],
        columns=np.arange(1, N_COLS + 1)
    ).to_csv(f"{case}_norm_map.csv")

    prof.to_csv(f"{case}_radial_profile.csv", index=False)

    plot_heatmap(
        dose_map,
        title=f"{case}: simulation run dose map",
        output=f"{case}_heatmap.png"
    )

    plot_radial_profile(
        prof,
        output=f"{case}_radial_profile.png"
    )

    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_csv": str(Path(args.csv_file).resolve()),
        "input_sha256": hashlib.sha256(Path(args.csv_file).read_bytes()).hexdigest(),
        "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "events": args.events,
        "events_source": "user-supplied --events; not inferred from scoring rows",
        "scoring_rows": len(df),
        "tld_count": len(out),
        "tld_mass_kg": TLD_MASS_KG,
        "tld_mass_source": "model cylinder dimensions and logged LiF density; not a measured detector mass",
        "tld_diameter_mm": TLD_DIAMETER_MM,
        "tld_thickness_mm": TLD_THICKNESS_MM,
        "tld_density_g_cm3": TLD_DENSITY_G_CM3,
        "kev_to_joule": KEV_TO_JOULE,
        "display_target_mean_Gy": args.target_mean,
        "center_TLD_IDs": [41, 42, 53, 54],
        "reference_radius_mm": REF_R_MM.tolist(),
        "reference_axis_normalized": REF_NORM.tolist(),
        "reference_center_divisor": reference_center_mean(),
        "radial_bin_width_mm": 5.0,
        "reference_outside_range": "unavailable; partially covered bins excluded",
        "uncertainty": "Spatial SD across TLDs only; no event-level MC uncertainty",
        "mean_run_dose_Gy": float(out["Dose_Gy_run"].mean()),
        "mean_dose_Gy_per_primary": float(out["Dose_Gy_per_primary"].mean()),
        "software": {"numpy": np.__version__, "pandas": pd.__version__},
    }
    Path(f"{case}_metadata.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    print("\n--- DORA analysis summary ---")
    print(f"Input CSV: {args.csv_file}")
    print(f"Number of hits in CSV: {len(df)}")
    print(f"Number of simulated primaries: {args.events}")

    print("\nRaw simulation:")
    print(f"  Mean dose for this run: {out['Dose_Gy_run'].mean():.6e} Gy")
    print(f"  Mean dose per primary:      {out['Dose_Gy_per_primary'].mean():.6e} Gy/primary")

    if args.target_mean is not None:
        print("\nDisplay-only scaling (not a dose prediction):")
        print(f"  Target mean dose:           {args.target_mean:.6f} Gy")
        print(f"  Achieved scaled mean dose:  {out['Dose_Gy_display_scaled'].mean():.6e} Gy")
        print(f"  Minimum scaled dose:        {out['Dose_Gy_display_scaled'].min():.6e} Gy")
        print(f"  Maximum scaled dose:        {out['Dose_Gy_display_scaled'].max():.6e} Gy")

    print("\nNormalization: central four TLDs (D6, D7, E6, E7), not r=0.")
    print("Reference: graph renormalized to the same central-four positions.")
    print("Reference outside 0-45 mm: unavailable (NaN); partial bins excluded.")
    print("Radial standard deviations describe spatial TLD spread, not MC uncertainty.")
    print("\nRadial comparison:")
    print(prof[[
        "r_mean_mm",
        "n_TLD",
        "norm_mean",
        "ref_norm_mean",
        "norm_minus_ref"
    ]].to_string(index=False))

    print("\nOutput files written:")
    print(f"  {case}_processed_tld.csv")
    print(f"  {case}_dose_map_Gy.csv")
    print(f"  {case}_norm_map.csv")
    print(f"  {case}_radial_profile.csv")
    print(f"  {case}_heatmap.png")
    print(f"  {case}_radial_profile.png")
    print(f"  {case}_metadata.json")


if __name__ == "__main__":
    main()
