import argparse
import pandas as pd

KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4
N_TLDS = 96

EXPECTED_COLUMNS = [
    "TLD_ID",
    "Edep_keV",
    "FromLeadInteraction",
    "FromHolderInteraction",
    "ParticlePDG",
    "ParentID",
]


parser = argparse.ArgumentParser(
    description="Analyze interaction-history tags in DORA TLD CSV output."
)

parser.add_argument("csv_file")
parser.add_argument("--events", type=int, required=True)

args = parser.parse_args()

if args.events <= 0:
    raise ValueError("--events must be a positive integer")


# ------------------------------------------------------------
# Read current six-column CSV format
# ------------------------------------------------------------

df = pd.read_csv(
    args.csv_file,
    comment="#",
    header=None
)

if df.shape[1] < 6:
    raise RuntimeError(
        f"Expected at least 6 CSV columns, found {df.shape[1]}. "
        "This script requires the current DORA CSV schema."
    )

# Ignore possible extra columns, but require the first six
df = df.iloc[:, :6].copy()
df.columns = EXPECTED_COLUMNS


# ------------------------------------------------------------
# Convert columns to numeric values
# ------------------------------------------------------------

for column in EXPECTED_COLUMNS:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna()


# ------------------------------------------------------------
# Basic validity checks
# ------------------------------------------------------------

df = df[
    (df["TLD_ID"] >= 0)
    & (df["TLD_ID"] < N_TLDS)
    & (df["Edep_keV"] >= 0)
].copy()

for flag in ["FromLeadInteraction", "FromHolderInteraction"]:
    invalid = ~df[flag].isin([0, 1])

    if invalid.any():
        raise RuntimeError(
            f"Column {flag} contains values other than 0 or 1."
        )


# ------------------------------------------------------------
# Interaction-history categories
# ------------------------------------------------------------

neither = df[
    (df["FromLeadInteraction"] == 0)
    & (df["FromHolderInteraction"] == 0)
]

holder_only = df[
    (df["FromLeadInteraction"] == 0)
    & (df["FromHolderInteraction"] == 1)
]

lead_only = df[
    (df["FromLeadInteraction"] == 1)
    & (df["FromHolderInteraction"] == 0)
]

lead_and_holder = df[
    (df["FromLeadInteraction"] == 1)
    & (df["FromHolderInteraction"] == 1)
]


def energy_sum(dataframe):
    return dataframe["Edep_keV"].sum()


total_edep = energy_sum(df)

category_edep = {
    "No lead/holder history": energy_sum(neither),
    "Holder only": energy_sum(holder_only),
    "Lead only": energy_sum(lead_only),
    "Lead + holder": energy_sum(lead_and_holder),
}


# ------------------------------------------------------------
# Dose normalization
# ------------------------------------------------------------

def mean_dose_per_tld(edep_keV):
    """
    Mean dose over the complete 96-TLD array for the full run.
    """
    energy_joule = edep_keV * KEV_TO_JOULE

    total_tld_mass = N_TLDS * TLD_MASS_KG

    return energy_joule / total_tld_mass


def mean_dose_per_tld_per_primary(edep_keV):
    """
    Mean dose per TLD per simulated primary event.
    """
    return mean_dose_per_tld(edep_keV) / args.events


# ------------------------------------------------------------
# Print report
# ------------------------------------------------------------

print()
print("DORA interaction-history analysis")
print("=================================")
print(f"CSV file: {args.csv_file}")
print(f"Events:   {args.events}")
print(f"Rows:     {len(df)}")

print()
print("Raw deposited energy")
print("--------------------")
print(f"Total Edep: {total_edep:.6f} keV")

print()
print("Energy fractions by interaction history")
print("---------------------------------------")

for name, edep in category_edep.items():

    fraction = (
        100.0 * edep / total_edep
        if total_edep > 0
        else 0.0
    )

    print(
        f"{name:25s}: "
        f"{edep:14.6f} keV "
        f"({fraction:8.4f} %)"
    )


print()
print("Mean dose over 96 TLDs")
print("----------------------")

print(
    "Full run:    "
    f"{mean_dose_per_tld(total_edep):.8e} Gy/TLD"
)

print(
    "Per primary: "
    f"{mean_dose_per_tld_per_primary(total_edep):.8e} "
    "Gy/TLD/primary"
)


print()
print("Mean dose contribution per primary")
print("----------------------------------")

for name, edep in category_edep.items():

    dose = mean_dose_per_tld_per_primary(edep)

    print(
        f"{name:25s}: "
        f"{dose:.8e} Gy/TLD/primary"
    )


# ------------------------------------------------------------
# Particle contribution
# ------------------------------------------------------------

particle_energy = (
    df.groupby("ParticlePDG")["Edep_keV"]
    .sum()
    .sort_values(ascending=False)
)

particle_table = pd.DataFrame({
    "Edep_keV": particle_energy,
})

if total_edep > 0:
    particle_table["Fraction_percent"] = (
        100.0 * particle_table["Edep_keV"] / total_edep
    )
else:
    particle_table["Fraction_percent"] = 0.0


print()
print("Particle contribution by depositing-track PDG code")
print("--------------------------------------------------")
print(particle_table)

print()
