# Known Issues

## Random seeds

All inspected existing logs appear to start with the same seed pair:

13049039, 61775110

Therefore existing runs must not be treated as statistically independent
replicates.

Future runs need explicit seed recording and independent seeds.

## Event-level uncertainty

Current scoring writes positive energy-deposition steps, not event totals.

EventID and TrackID are not stored.

Therefore statistically correct event-by-event variance cannot currently
be calculated from the CSV output.

## Legacy overlap run

build/dora_leadring_120_1M.log contains a GeomVol1002 overlap warning.

This run must not be used as a validated geometry result.

## Large holder effect in current DORA-body geometry

For the current 10M runs:

- DORA body + no holder:
  6.56581015e-15 Gy/TLD/primary

- DORA body + holder:
  1.45527512e-15 Gy/TLD/primary

This corresponds to:

B/A = 0.221644

or a -77.836% change when the holder is added.

This must not yet be interpreted as a physical holder effect.

Possible causes to investigate include:

- current lead/tray-channel geometry,
- holder placement relative to the lead channel,
- source-boundary configuration,
- secondary-electron transport,
- production cuts / step settings,
- tagging interpretation,
- geometry assumptions that do not match the real DORA device.

The no-holder DORA case also shows a very large lead-history contribution
and requires dedicated investigation before use in thesis conclusions.
