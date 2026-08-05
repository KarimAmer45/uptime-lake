from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_sample import validate


class SampleValidationTests(unittest.TestCase):
    def test_sample_reconciles_and_exercises_every_rule(self):
        root = Path(__file__).resolve().parents[1]
        result = validate(root / "data/sample/metropt3_sample.csv")
        self.assertTrue(result["reconciled"])
        self.assertEqual(22, result["source_rows"])
        self.assertEqual(12, result["silver_rows"])
        self.assertEqual(10, result["reject_rows"])
        self.assertEqual(10, result["quality_checks"])
        self.assertTrue(all(count > 0 for count in result["failed_rows_by_check"].values()))


if __name__ == "__main__":
    unittest.main()

