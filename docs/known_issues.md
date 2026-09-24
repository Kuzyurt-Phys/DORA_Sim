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

