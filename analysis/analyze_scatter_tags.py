import argparse
import pandas as pd

KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4

parser = argparse.ArgumentParser()
parser.add_argument("csv_file")
parser.add_argument("--events", type=int, required=True)
args = parser.parse_args()

df = pd.read_csv(args.csv_file, comment="#", header=None)

if df.shape[1] < 5:
    raise RuntimeError(
        "This file does not contain scatter-tag columns. "
        "Rebuild and rerun after adding TrackInformation and SteppingAction."
    )

df = df.iloc[:, :5]
df.columns = [
    "TLD_ID",
    "Edep_keV",
    "FromLeadInteraction",
    "ParticlePDG",
    "ParentID"
]

df["TLD_ID"] = pd.to_numeric(df["TLD_ID"], errors="coerce")
df["Edep_keV"] = pd.to_numeric(df["Edep_keV"], errors="coerce")
df["FromLeadInteraction"] = pd.to_numeric(df["FromLeadInteraction"], errors="coerce")
df["ParticlePDG"] = pd.to_numeric(df["ParticlePDG"], errors="coerce")
df["ParentID"] = pd.to_numeric(df["ParentID"], errors="coerce")

df = df.dropna()
df = df[(df["TLD_ID"] >= 0) & (df["TLD_ID"] < 96)]
df = df[df["Edep_keV"] >= 0]

total_edep = df["Edep_keV"].sum()

direct = df[df["FromLeadInteraction"] == 0]
lead = df[df["FromLeadInteraction"] == 1]

direct_edep = direct["Edep_keV"].sum()
lead_edep = lead["Edep_keV"].sum()

direct_frac = 100.0 * direct_edep / total_edep if total_edep > 0 else 0.0
lead_frac = 100.0 * lead_edep / total_edep if total_edep > 0 else 0.0

total_dose = total_edep * KEV_TO_JOULE / TLD_MASS_KG
direct_dose = direct_edep * KEV_TO_JOULE / TLD_MASS_KG
lead_dose = lead_edep * KEV_TO_JOULE / TLD_MASS_KG

print()
print("Scatter-tag analysis")
print("====================")
print(f"CSV file: {args.csv_file}")
print(f"Events:   {args.events}")
print()
print("Raw deposited energy")
print("--------------------")
print(f"Total Edep:       {total_edep:.6f} keV")
print(f"Direct-tag Edep:  {direct_edep:.6f} keV")
print(f"Lead-tag Edep:    {lead_edep:.6f} keV")
print()
print("Fractions")
print("---------")
print(f"Direct-tag fraction: {direct_frac:.3f} %")
print(f"Lead-tag fraction:   {lead_frac:.3f} %")
print()
print("Dose")
print("----")
print(f"Total raw dose:       {total_dose:.8e} Gy")
print(f"Direct-tag raw dose:  {direct_dose:.8e} Gy")
print(f"Lead-tag raw dose:    {lead_dose:.8e} Gy")
print()
print("Particle contribution by PDG code")
print("---------------------------------")
print(df.groupby("ParticlePDG")["Edep_keV"].sum().sort_values(ascending=False))
print()
