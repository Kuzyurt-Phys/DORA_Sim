import argparse
import pandas as pd

KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4
N_TLDS = 96

def load_total(csv_file):
    df = pd.read_csv(csv_file, comment="#", header=None)
    df = df.iloc[:, :2]
    df.columns = ["TLD_ID", "Edep_keV"]

    df["TLD_ID"] = pd.to_numeric(df["TLD_ID"], errors="coerce")
    df["Edep_keV"] = pd.to_numeric(df["Edep_keV"], errors="coerce")
    df = df.dropna()

    df = df[(df["TLD_ID"] >= 0) & (df["TLD_ID"] < 96)]
    df = df[df["Edep_keV"] >= 0]

    total_edep = df["Edep_keV"].sum()
    total_dose = total_edep * KEV_TO_JOULE / TLD_MASS_KG
    mean_dose = total_dose / N_TLDS

    return len(df), total_edep, mean_dose

parser = argparse.ArgumentParser()
parser.add_argument("--simple", required=True)
parser.add_argument("--dora", required=True)
parser.add_argument("--events", type=int, required=True)
parser.add_argument("--case-name", default="comparison")
args = parser.parse_args()

simple_hits, simple_edep, simple_mean = load_total(args.simple)
dora_hits, dora_edep, dora_mean = load_total(args.dora)

ratio = dora_mean / simple_mean
enhancement = (ratio - 1.0) * 100.0
extra_fraction = (dora_mean - simple_mean) / dora_mean * 100.0

summary = f"""
DORA simple-vs-lead-ring comparison
===================================

Simple file: {args.simple}
DORA file:   {args.dora}
Events:      {args.events}

Raw hits
--------
Simple hits: {simple_hits}
DORA hits:   {dora_hits}

Raw deposited energy
--------------------
Simple total Edep: {simple_edep:.6f} keV
DORA total Edep:   {dora_edep:.6f} keV

Raw mean dose
-------------
Simple mean raw dose: {simple_mean:.8e} Gy
DORA mean raw dose:   {dora_mean:.8e} Gy

Main result
-----------
DORA/simple ratio: {ratio:.6f}
Enhancement:       {enhancement:.3f} %
Extra fraction of DORA-body total dose: {extra_fraction:.3f} %
"""

print(summary)

with open(f"{args.case_name}_summary.txt", "w") as f:
    f.write(summary)
