import os
os.environ.setdefault("MPLBACKEND", "Agg")
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_dora as a

class AnalysisTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"TLD_ID": range(96), "Edep_keV": np.arange(1, 97, dtype=float)})

    def read(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.csv"
            path.write_text(text)
            return a.load_geant4_csv(str(path))

    def test_motion_run_conversion_regression(self):
        # Historical 1M centre run: known energy and independently calculated
        # model response from the motion analysis (all 96 cells included).
        frame = pd.DataFrame({"TLD_ID": [41], "Edep_keV": [94874.028080]})
        out = a.make_tld_table(frame, 1_000_000, None)
        self.assertAlmostEqual(a.TLD_MASS_KG, 1.0140668386616153e-4, delta=1e-15)
        self.assertAlmostEqual(out.Dose_Gy_per_primary.mean(), 1.561421e-15, delta=5e-22)

    def test_invalid_rows_are_rejected(self):
        for row in ["1.5,2", "-1,2", "96,2", "2,-1", "2,inf", "nan,2", "2,nan", "x,2"]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.read("0,1\n" + row + "\n")

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            self.read("# no scoring rows\n")

    def test_extra_columns_and_zero_energy(self):
        out = self.read("# header\n0,0,0,1,22,0\n95,2,0,0,11,1\n")
        self.assertEqual(len(out), 2)
        self.assertEqual(out.Edep_keV.sum(), 2)

    def test_energy_conservation_and_missing_cells(self):
        frame = pd.DataFrame({"TLD_ID": [41, 41, 42], "Edep_keV": [2., 3., 7.]})
        out = a.make_tld_table(frame, 10, None)
        self.assertEqual(len(out), 96)
        self.assertEqual(out.Edep_keV.sum(), 12)
        self.assertEqual(out.loc[out.TLD_ID == 41, "Edep_keV"].iloc[0], 5)
        self.assertAlmostEqual(out.Dose_Gy_run.sum() * a.TLD_MASS_KG / a.KEV_TO_JOULE, 12)

    def test_display_scaling_cannot_change_physical_results(self):
        raw = a.make_tld_table(self.frame(), 100, None)
        scaled = a.make_tld_table(self.frame(), 100, 1.13)
        for col in ["Edep_keV", "Dose_Gy_run", "Dose_Gy_per_primary", "Norm_to_center"]:
            np.testing.assert_array_equal(raw[col], scaled[col])
        self.assertTrue(raw.Dose_Gy_display_scaled.isna().all())
        self.assertAlmostEqual(scaled.Dose_Gy_display_scaled.mean(), 1.13)

    def test_event_count_scaling(self):
        first = a.make_tld_table(self.frame(), 100, None)
        second = a.make_tld_table(self.frame(), 200, None)
        np.testing.assert_allclose(first.Dose_Gy_per_primary, second.Dose_Gy_per_primary * 2)
        np.testing.assert_allclose(first.Norm_to_center, second.Norm_to_center)

    def test_center_is_nearest_four(self):
        out = a.make_tld_table(self.frame(), 100, None)
        center = out.nsmallest(4, "r_mm")
        self.assertEqual(set(center.TLD_ID), {41, 42, 53, 54})
        self.assertAlmostEqual(center.Norm_to_center.mean(), 1)
        self.assertAlmostEqual(center.Ref_norm_from_graph.mean(), 1)

    def test_reference_bounds_and_partial_bins(self):
        out = a.make_tld_table(self.frame(), 100, None)
        self.assertTrue(out.loc[out.r_mm > 45, "Norm_minus_ref"].isna().all())
        self.assertTrue(a.radial_profile(out, 100).ref_norm_mean.isna().all())
        self.assertEqual(a.radial_profile(out).n_TLD.sum(), 96)

    def test_uniform_dose_has_no_spatial_spread(self):
        frame = self.frame(); frame["Edep_keV"] = 1.
        prof = a.radial_profile(a.make_tld_table(frame, 100, None))
        np.testing.assert_allclose(prof.norm_mean, 1)
        np.testing.assert_allclose(prof.norm_spatial_std, 0)

    def test_invalid_normalization_inputs(self):
        for events, target in [(0, None), (-1, None), (1.5, None), (True, None), (1, -1), (1, float("inf"))]:
            with self.subTest(events=events, target=target), self.assertRaises(ValueError):
                a.make_tld_table(self.frame(), events, target)
        frame = self.frame(); frame["Edep_keV"] = 0.
        with self.assertRaises(ValueError):
            a.make_tld_table(frame, 1, None)

if __name__ == "__main__":
    unittest.main()
