import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


KEV_TO_JOULE = 1.60218e-16

# Current simulation geometry:
# 7 mm diameter, 1 mm thickness LiF pellet.
# This matches your current code.
TLD_MASS_KG = 1.01e-4

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


def load_geant4_csv(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, comment="#", header=None)

    if df.shape[1] < 2:
        raise ValueError("CSV must contain at least two columns: TLD_ID and Edep_keV")

    df = df.iloc[:, :2]
    df.columns = ["TLD_ID", "Edep_keV"]

    df["TLD_ID"] = pd.to_numeric(df["TLD_ID"], errors="coerce")
    df["Edep_keV"] = pd.to_numeric(df["Edep_keV"], errors="coerce")
    df = df.dropna()

    df["TLD_ID"] = df["TLD_ID"].astype(int)

    df = df[(df["TLD_ID"] >= 0) & (df["TLD_ID"] < 96)]
    df = df[df["Edep_keV"] >= 0.0]

    return df


def make_tld_table(df: pd.DataFrame, n_events: int, target_mean: float | None) -> pd.DataFrame:
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

    out["Dose_Gy_raw"] = (out["Edep_keV"] * KEV_TO_JOULE) / TLD_MASS_KG
    out["Dose_Gy_per_primary"] = out["Dose_Gy_raw"] / float(n_events)

    raw_mean = out["Dose_Gy_raw"].mean()

    if target_mean is not None:
        if raw_mean <= 0:
            raise ValueError("Raw mean dose is zero; cannot normalize to target mean.")
        scale_factor = target_mean / raw_mean
    else:
        scale_factor = 1.0

    out["Dose_Gy_scaled"] = out["Dose_Gy_raw"] * scale_factor

    # Center reference: average of the four cells nearest the geometrical center.
    # Rows D/E and columns 6/7 in human notation.
    center_mask = (
        ((out["row_index"] == 3) | (out["row_index"] == 4)) &
        ((out["col_index"] == 5) | (out["col_index"] == 6))
    )

    center_dose = out.loc[center_mask, "Dose_Gy_scaled"].mean()

    out["Norm_to_center"] = out["Dose_Gy_scaled"] / center_dose
    out["Ref_norm_from_graph"] = np.interp(out["r_mm"], REF_R_MM, REF_NORM)
    out["Norm_minus_ref"] = out["Norm_to_center"] - out["Ref_norm_from_graph"]

    return out


def make_maps(out: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    dose_map = np.zeros((N_ROWS, N_COLS))
    norm_map = np.zeros((N_ROWS, N_COLS))

    for _, row in out.iterrows():
        r = int(row["row_index"])
        c = int(row["col_index"])
        dose_map[r, c] = row["Dose_Gy_scaled"]
        norm_map[r, c] = row["Norm_to_center"]

    return dose_map, norm_map


def radial_profile(out: pd.DataFrame, bin_width_mm: float = 5.0) -> pd.DataFrame:
    max_r = out["r_mm"].max()
    bins = np.arange(0.0, max_r + bin_width_mm, bin_width_mm)

    tmp = out.copy()
    tmp["r_bin"] = pd.cut(tmp["r_mm"], bins=bins, include_lowest=True)

    prof = tmp.groupby("r_bin", observed=False).agg(
        r_mean_mm=("r_mm", "mean"),
        n_TLD=("TLD_ID", "count"),
        dose_mean_Gy=("Dose_Gy_scaled", "mean"),
        dose_std_Gy=("Dose_Gy_scaled", "std"),
        norm_mean=("Norm_to_center", "mean"),
        norm_std=("Norm_to_center", "std"),
        ref_norm_mean=("Ref_norm_from_graph", "mean"),
    ).reset_index()

    prof = prof.dropna(subset=["r_mean_mm"])
    prof["norm_minus_ref"] = prof["norm_mean"] - prof["ref_norm_mean"]

    return prof


def plot_heatmap(dose_map: np.ndarray, title: str, output: str) -> None:
    fig, ax = plt.subplots(figsize=(14, 8))

    im = ax.imshow(dose_map, vmin=0.0, vmax=max(2.0, np.nanmax(dose_map)))

    ax.set_xticks(np.arange(N_COLS))
    ax.set_xticklabels(np.arange(1, N_COLS + 1))

    ax.set_yticks(np.arange(N_ROWS))
    ax.set_yticklabels([chr(ord("A") + i) for i in range(N_ROWS)])

    for i in range(N_ROWS):
        for j in range(N_COLS):
            ax.text(j, i, f"{dose_map[i, j]:.2f}",
                    ha="center", va="center", fontsize=7)

    ax.set_title(title)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Absorbed dose (Gy)")

    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def plot_radial_profile(prof: pd.DataFrame, output: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.errorbar(
        prof["r_mean_mm"],
        prof["norm_mean"],
        yerr=prof["norm_std"],
        fmt="o",
        capsize=3,
        label="Simulation"
    )

    ax.plot(REF_R_MM, REF_NORM, marker="s", label="DORA reference graph")

    ax.set_xlabel("Distance from central axis r (mm)")
    ax.set_ylabel("Normalized dose rate / dose")
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
                        help="Optional target mean dose in Gy, e.g. 1.13")
    parser.add_argument("--case-name", default="DORA_case",
                        help="Name used in output filenames")

    args = parser.parse_args()

    df = load_geant4_csv(args.csv_file)
    out = make_tld_table(df, args.events, args.target_mean)
    dose_map, norm_map = make_maps(out)
    prof = radial_profile(out)

    case = args.case_name

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
        title=f"{case}: scaled dose map",
        output=f"{case}_heatmap.png"
    )

    plot_radial_profile(
        prof,
        output=f"{case}_radial_profile.png"
    )

    print("\n--- DORA analysis summary ---")
    print(f"Input CSV: {args.csv_file}")
    print(f"Number of hits in CSV: {len(df)}")
    print(f"Number of simulated primaries: {args.events}")

    print("\nRaw simulation:")
    print(f"  Mean raw dose for this run: {out['Dose_Gy_raw'].mean():.6e} Gy")
    print(f"  Mean dose per primary:      {out['Dose_Gy_per_primary'].mean():.6e} Gy/primary")

    if args.target_mean is not None:
        print("\nScaled map:")
        print(f"  Target mean dose:           {args.target_mean:.6f} Gy")
        print(f"  Achieved scaled mean dose:  {out['Dose_Gy_scaled'].mean():.6f} Gy")
        print(f"  Minimum scaled dose:        {out['Dose_Gy_scaled'].min():.6f} Gy")
        print(f"  Maximum scaled dose:        {out['Dose_Gy_scaled'].max():.6f} Gy")

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


if __name__ == "__main__":
    main()
