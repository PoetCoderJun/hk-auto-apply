#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skill" / "hk-auto-apply" / "scripts"))
import jd_flags  # noqa: E402


class JdFlagTests(unittest.TestCase):
    def test_required_years(self):
        flags = jd_flags.extract_flags(
            "The ideal candidate has 5+ years of experience in wealth management."
        )
        self.assertEqual(flags["required_years_min"], 5)
        self.assertFalse(flags["year_mentions"][0]["ignored"])

    def test_ignores_company_history(self):
        flags = jd_flags.extract_flags(
            "With over 50 years of experience, the firm is a leading private bank in Hong Kong."
        )
        self.assertIsNone(flags["required_years_min"])
        self.assertTrue(any(item["ignored"] for item in flags["year_mentions"]))

    def test_ignores_strategic_plan(self):
        flags = jd_flags.extract_flags(
            "You will support the 5 year strategic plan across the wealth platform."
        )
        self.assertIsNone(flags["required_years_min"])

    def test_year_range(self):
        flags = jd_flags.extract_flags("We look for 3-5 years of experience in client coverage.")
        self.assertEqual(flags["required_years_min"], 3)
        self.assertEqual(flags["required_years_max"], 5)

    def test_cantonese_preferred_not_native(self):
        flags = jd_flags.extract_flags("Cantonese preferred; Mandarin and English are required.")
        self.assertFalse(flags["native_cantonese"])
        self.assertTrue(flags["cantonese_preferred"])

    def test_native_cantonese(self):
        flags = jd_flags.extract_flags("Native Cantonese is required for daily client calls.")
        self.assertTrue(flags["native_cantonese"])
        self.assertFalse(flags["cantonese_preferred"])


if __name__ == "__main__":
    unittest.main()
