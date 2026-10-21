# DORA geometry audit — 30 September 2026

## Evidence and limits
Original reference documents were read from the Windows Downloads directory. They were not modified.

| Item | Evidence | Current interpretation |
|---|---|---|
| Lead body | Dora_Techical.pdf, p4 and p9 Fig8 | Lead; outer diameter 360 mm, cavity diameter 90 mm, height 600 mm; radial lead thickness 135 mm. Existing main dimensions retained. |
| Sources | Same document p9 Fig8 | Approximately +/-120 mm from centre. Point-source approximation retained; capsule geometry unknown. |
| Plug inner face | Diagram shows plugs, but gives no explicit inner-face coordinate | Legacy +/-120 mm retained as an assumption. New DORA_PLUG_INNER_Z_MM allows independent diagnostic studies. |
| Tray slot | p9 Fig8 shows central 30 mm strip | Detailed through-channel shape and 100 mm model width are not established measurements. |
| Sample envelope | Dora_2020_10_30.pdf: 129 x 73 mm, maximum height 17 mm | Sample accommodation is not automatically carriage outside dimensions or shielding aperture. |
| 96-well fit | DORA_research_plan_and_meeting_outcomes_2026-09-04_revised_v2.docx | Meeting confirms plate fits. Do not shrink plate using old sample envelope alone. |
| Holder | Current code: solid 127.55 x 85.3 x 19 mm polystyrene box | Neither true hollow plate/carriage shape nor material has been established. No material substitution made. |
| Scoring elements | Current code: 96 LiF cylinders, diameter 7 mm, thickness 1 mm, pitch 9 mm | Legacy TLD model, not a validated EBT4 or BeO model. |
| Reference quantity | Dora_Techical.pdf p8 centre table explicitly uses air kerma | Must establish quantity and normalization before treating a reference curve as LiF absorbed-dose validation. |
| CAD | Eight Pro/DESKTOP .des files; prior extraction audit | Preview colors and unparsed binary records do not establish dimensions or materials. Neutral export/compatible CAD needed. |

## Changes
- Source position parses strictly: malformed, nonfinite, nonpositive and outside-world values are rejected.
- Plug inner face has its own strictly checked parameter; default unchanged at 120 mm, upper limit 300 mm.
- Point sources on/in the assumed lead plug emit a prominent warning. Legacy boundary placement remains unresolved, not silently shifted by an invented distance.
- Removed physical air-sphere source markers. Their 3 mm radius at +/-119 mm crossed the lead interface at +/-120 mm by 2 mm. The marker flag now warns and places no volumes; graphical markers are not yet reimplemented.
- Logs explicitly identify unverified holder/channel assumptions and report the Geant4 LiF density and individual scoring-volume mass.
- Physics list, source energy/probability, default body dimensions and scoring lattice unchanged.

## Validation artifacts
Separate build and checks: /home/ahmetkuzyurt/dora_geometry_audit_20260930/.
The 130 mm plug case is an artificial sensitivity-test setting, NOT a measured replacement geometry.
Short 100-event checks establish execution and sampled overlap behavior, not dose precision or physical validation.

## Next work
1. Resolve actual plug inner face, capsule and source mounting from dimensioned section/CAD. Record source coordinate separately from plug coordinate.
2. Separate the moving carriage, real hollow well plate, inserts and scoring medium; assign measured/manufacturer materials and thicknesses.
3. Add real film/BeO geometry only after thickness, sensitive region and measurement positions are established.
4. Repeat four body/holder controls with independent seeds and event-level uncertainty accounting. Existing large holder effect is unexplained, not evidence of correct geometry.
5. Compare matched quantities: LiF dose, film dose and air kerma are not interchangeable. Do not scale an absolute prediction to 1.13 Gy to validate it.

Existing analysis edits were preserved. No production dataset was overwritten and no commit was created.

## Observed check results
Build succeeded. Default, marker-enabled, body/holder-disabled and diagnostic plug=130 mm cases each completed 100 events with no reported overlap errors at 10000 sample resolution. Eleven invalid configuration inputs were rejected. Geant4 reports LiF density 2.635 g/cm3 and mass 0.101407 g per cylinder. This is the model mass, not a measured detector mass.
