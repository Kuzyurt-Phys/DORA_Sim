import argparse
import pandas as pd

KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4
N_TLDS = 96


def load_case(csv_file, events):
    if events <= 0:
        raise ValueError("Number of events must be positive.")

    df = pd.read_csv(
        csv_file,
        comment="#",
        header=None,
    )

    if df.shape[1] < 2:
        raise RuntimeError(
            f"{csv_file} contains fewer than 2 columns."
        )

    df = df.iloc[:, :2].copy()
    df.columns = [
        "TLD_ID",
        "Edep_keV",
    ]

    df["TLD_ID"] = pd.to_numeric(
        df["TLD_ID"],
        errors="coerce",
    )

    df["Edep_keV"] = pd.to_numeric(
        df["Edep_keV"],
        errors="coerce",
    )

    df = df.dropna()

    df = df[
        (df["TLD_ID"] >= 0)
        & (df["TLD_ID"] < N_TLDS)
        & (df["Edep_keV"] >= 0)
    ].copy()

    total_edep_keV = df["Edep_keV"].sum()

    total_energy_joule = (
        total_edep_keV * KEV_TO_JOULE
    )

    mean_dose_per_tld = (
        total_energy_joule
        / (N_TLDS * TLD_MASS_KG)
    )

    mean_dose_per_tld_per_primary = (
        mean_dose_per_tld / events
    )

    return {
        "rows": len(df),
        "total_edep_keV": total_edep_keV,
        "mean_dose_per_tld_Gy": mean_dose_per_tld,
        "mean_dose_per_tld_per_primary_Gy":
            mean_dose_per_tld_per_primary,
    }


parser = argparse.ArgumentParser(
    description=(
        "Compare two DORA simulation cases "
        "using dose normalized per primary."
    )
)

parser.add_argument(
    "--case-a",
    required=True,
)

parser.add_argument(
    "--case-b",
    required=True,
)

parser.add_argument(
    "--events-a",
    type=int,
    required=True,
)

parser.add_argument(
    "--events-b",
    type=int,
    required=True,
)

parser.add_argument(
    "--label-a",
    default="Case A",
)

parser.add_argument(
    "--label-b",
    default="Case B",
)

parser.add_argument(
    "--output",
    default="comparison_summary.txt",
)

args = parser.parse_args()


case_a = load_case(
    args.case_a,
    args.events_a,
)

case_b = load_case(
    args.case_b,
    args.events_b,
)


dose_a = (
    case_a[
        "mean_dose_per_tld_per_primary_Gy"
    ]
)

dose_b = (
    case_b[
        "mean_dose_per_tld_per_primary_Gy"
    ]
)


if dose_a <= 0:
    raise RuntimeError(
        "Case A has zero normalized dose; "
        "ratio cannot be calculated."
    )


ratio = dose_b / dose_a

relative_change_percent = (
    (ratio - 1.0) * 100.0
)



summary = f"""
DORA case comparison
====================

Case A
------
Label:   {args.label_a}
File:    {args.case_a}
Events:  {args.events_a}
Rows:    {case_a["rows"]}
Edep:    {case_a["total_edep_keV"]:.6f} keV

Mean dose over 96 TLDs:
{case_a["mean_dose_per_tld_Gy"]:.8e} Gy/TLD

Mean dose per primary:
{dose_a:.8e} Gy/TLD/primary


Case B
------
Label:   {args.label_b}
File:    {args.case_b}
Events:  {args.events_b}
Rows:    {case_b["rows"]}
Edep:    {case_b["total_edep_keV"]:.6f} keV

Mean dose over 96 TLDs:
{case_b["mean_dose_per_tld_Gy"]:.8e} Gy/TLD

Mean dose per primary:
{dose_b:.8e} Gy/TLD/primary


Comparison
----------
B / A ratio:
{ratio:.6f}

Relative change from A to B:
{relative_change_percent:.3f} %

"""

print(summary)

with open(args.output, "w") as f:
    f.write(summary)
