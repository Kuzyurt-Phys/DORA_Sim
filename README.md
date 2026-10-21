# DÓRA Irradiator Simulation

Geant4 simulation and Python analysis for studying energy deposition,
dose distributions and geometry effects in the DÓRA irradiator model.

**Author:** Ahmet Kuzyurt  
**Status:** Research project under development; experimental validation is ongoing.

## Overview

The project includes a Geant4 irradiation model and analysis of energy
deposition across an 8 × 12 array of scoring elements.

Research topics include spatial dose uniformity and the influence of
shielding, sample-holder geometry and particle interaction history.

The simulation uses `FTFP_BERT` with its electromagnetic physics replaced
by `G4EmStandardPhysics_option4`.

## Repository structure

| Path | Contents |
|---|---|
| `DORA_Sim.cc` | Simulation entry point |
| `src/` | Geant4 implementation |
| `include/` | Headers and geometry configuration |
| `analyze_dora.py` | Main dose-map analysis |
| `analysis/` | Additional analysis scripts and documentation |
| `docs/` | Geometry notes, run manifest and known limitations |
| `tests/` | Python analysis tests |
| `run.mac` | Batch macro requesting 1,000,000 events |
| `init_vis.mac`, `vis.mac` | Interactive visualization macros |

## Requirements

- Geant4 with UI and visualization support
- CMake 3.16 or newer
- A C++ compiler compatible with the installed Geant4 version
- Python 3 with NumPy, pandas and Matplotlib

The development environment uses Geant4 11.4 on Ubuntu under WSL.
Other environments have not been verified here.

## Build

From the repository root, with the Geant4 environment configured:

```bash
cmake -S . -B build
cmake --build build -j2
```

If CMake cannot locate Geant4, set `Geant4_DIR` to the directory containing
your installation's `Geant4Config.cmake`.

## Run

Batch mode:

```bash
cd build
./DORA_Sim run.mac
```

The supplied macro requests **1,000,000 events**. Check the run log to
confirm successful completion.

Interactive visualization:

```bash
./DORA_Sim
```

Interactive mode requires a working graphical display.

## Analyse a run

From the repository root, replace `YOUR_OUTPUT.csv` with the actual
simulation output filename:

```bash
MPLBACKEND=Agg python3 analyze_dora.py build/YOUR_OUTPUT.csv \
  --events 1000000 \
  --case-name dora_example \
  --output-dir /tmp/dora_results
```

Set `--events` to the actual number of simulated primary events for that
file, **not the number of CSV rows**. The documented generator emits one
gamma per event, choosing between two sources.

Input requires TLD IDs from 0 to 95 and deposited energy in keV in the
first two columns. Additional columns are ignored by the main analysis.

Outputs include:

- Run dose and dose per primary
- Dose maps and radial profiles
- Normalization to the central four scoring positions
- Spatial spread within radial bins
- Provenance JSON recording input and analysis hashes and settings

See [the analysis guide](analysis/README.md) for details and auxiliary scripts.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Passing analysis tests does not establish physical validation of the model.

## Interpretation and limitations

- Dose conversion uses model LiF cylinders: 7 mm diameter, 1 mm thickness
  and density 2.635 g/cm³. These are model inputs, not measured detector
  properties.
- Recheck the analysis mass and material assumptions when geometry changes.
- Spatial standard deviations describe variation between scoring positions,
  not event-level Monte Carlo uncertainty.
- Existing scoring CSVs do not contain EventID, so event-level statistical
  uncertainty cannot be recovered from them.
- `--target-mean` provides display-only scaling; it is not an absolute-dose
  prediction.
- Existing cases must not be treated as independent statistical replicates.
- The embedded reference profile needs a traceable source citation before
  being presented as a reproducible validation benchmark.

See [known issues](docs/known_issues.md),
[geometry versions](docs/geometry_versions.md) and
[the run manifest](docs/run_manifest.csv).

## Generated files

Build products and most generated CSV, log and PNG outputs are excluded
from version control. They must be regenerated or backed up separately.
The repository retains selected documentation CSV files.
