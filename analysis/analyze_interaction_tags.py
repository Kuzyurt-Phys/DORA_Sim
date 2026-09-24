import argparse
import pandas as pd

KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4
N_TLDS = 96

parser = argparse.ArgumentParser()
parser.add_argument("csv_file")
parser.add_argument("--events", type=int, required=True)
args = parser.parse_args()

df = pd.read_csv(args.csv_file, comment="#", header=None)

if df.shape[1] < 6:
    raise RuntimeError(
        "This file does not contain the holder-tag columns. "
        "Rebuild and rerun after adding FromHolderInteraction."
    )

df = df.iloc[:, :6]
df.columns = [
    "TLD_ID",
    "Edep_keV",
    "FromLeadInteraction",
    "FromHolderInteraction",
    "ParticlePDG",
    "ParentID"
]

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna()
df = df[(df["TLD_ID"] >= 0) & (df["TLD_ID"] < 96)]
df = df[df["Edep_keV"] >= 0]

total_edep = df["Edep_keV"].sum()

pure_direct = df[
    (df["FromLeadInteraction"] == 0) &
    (df["FromHolderInteraction"] == 0)
]

lead_only = df[
    (df["FromLeadInteraction"] == 1) &
    (df["FromHolderInteraction"] == 0)
]

holder_only = df[
    (df["FromLeadInteraction"] == 0) &
    (df["FromHolderInteraction"] == 1)
]

lead_and_holder = df[
    (df["FromLeadInteraction"] == 1) &
    (df["FromHolderInteraction"] == 1)
]

def summarize(label, sub):
    edep = sub["Edep_keV"].sum()
    frac = 100.0 * edep / total_edep if total_edep > 0 else 0.0
    dose_sum = edep * KEV_TO_JOULE / TLD_MASS_KG
    dose_mean = dose_sum / N_TLDS
    print(f"{label:<22} {edep:14.6f} keV   {frac:8.3f} %   mean/TLD {dose_mean:.8e} Gy")

print()
print("Interaction-tag analysis")
print("========================")
print(f"CSV file: {args.csv_file}")
print(f"Events:   {args.events}")
print()

print("Raw deposited energy split")
print("--------------------------")
summarize("Pure direct", pure_direct)
summarize("Lead only", lead_only)
summarize("Holder only", holder_only)
summarize("Lead + holder", lead_and_holder)

print()
print("Total")
print("-----")
total_dose_sum = total_edep * KEV_TO_JOULE / TLD_MASS_KG
total_dose_mean = total_dose_sum / N_TLDS
print(f"Total Edep:             {total_edep:.6f} keV")
print(f"Total raw dose sum:     {total_dose_sum:.8e} Gy")
print(f"Mean raw dose per TLD:  {total_dose_mean:.8e} Gy")

print()
print("Combined fractions")
print("------------------")
lead_any = df[df["FromLeadInteraction"] == 1]["Edep_keV"].sum()
holder_any = df[df["FromHolderInteraction"] == 1]["Edep_keV"].sum()

lead_any_frac = 100.0 * lead_any / total_edep if total_edep > 0 else 0.0
holder_any_frac = 100.0 * holder_any / total_edep if total_edep > 0 else 0.0

print(f"Any lead interaction:   {lead_any_frac:.3f} %")
print(f"Any holder interaction: {holder_any_frac:.3f} %")

print()
print("Particle contribution by PDG code")
print("---------------------------------")
print(df.groupby("ParticlePDG")["Edep_keV"].sum().sort_values(ascending=False))
print()
