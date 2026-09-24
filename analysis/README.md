# DORA Analysis Scripts

## analyze_interaction_tags.py

Current interaction-history analysis.

Expected CSV schema:

1. TLD_ID
2. Edep_keV
3. FromLeadInteraction
4. FromHolderInteraction
5. ParticlePDG
6. ParentID

Status: current.

---

## analyze_scatter_tags.py

Interaction / particle analysis.

Status: requires correction.

Known issue:
The current version accepts six-column CSV files but assigns the
columns using the older five-column schema. Particle classification
is therefore incorrect.

---

## compare_dora_cases.py

Compares total deposited energy between simulation cases.

Status: usable only when compared runs contain the same number of
primary events.

Future version must explicitly normalize by number of primaries.

---

## analyze_dora.py

Main dose-map analysis currently located in the project root.

Status: current but requires cleanup of reference-profile handling,
normalization definition, and uncertainty treatment.

---

## legacy/

Historical scripts that must not be used for current results.
