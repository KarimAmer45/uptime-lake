from __future__ import annotations

import unittest

from uptime_lake.config import PipelineConfig, validate_identifier
from uptime_lake.contracts import anomaly_reasons, quality_reasons


class ContractTests(unittest.TestCase):
    def test_valid_row_has_no_reasons(self):
        row = {
            "index": "1", "timestamp": "2020-02-01 00:00:00", "TP2": "7", "TP3": "8",
            "H1": "7.8", "DV_pressure": "0", "Reservoirs": "8", "Oil_temperature": "50",
            "Motor_current": "7", "COMP": "0", "DV_eletric": "1", "Towers": "0",
            "MPG": "0", "LPS": "0", "Pressure_switch": "0", "Oil_level": "0",
            "Caudal_impulses": "1",
        }
        self.assertEqual([], quality_reasons(row))

    def test_multiple_failures_are_not_hidden(self):
        row = {
            "index": "x", "timestamp": "bad", "TP2": "99", "TP3": "8", "H1": "7.8",
            "DV_pressure": "0", "Reservoirs": "8", "Oil_temperature": "200",
            "Motor_current": "70", "COMP": "2", "DV_eletric": "1", "Towers": "0",
            "MPG": "0", "LPS": "0", "Pressure_switch": "0", "Oil_level": "0",
            "Caudal_impulses": "-1",
        }
        reasons = quality_reasons(row, duplicate=True)
        self.assertIn("invalid_reading_id", reasons)
        self.assertIn("pressure_out_of_range", reasons)
        self.assertIn("duplicate_reading", reasons)

    def test_anomaly_is_explainable(self):
        row = {"oil_temperature": 101.0, "motor_current": 13.0, "tp3": 8.0,
               "reservoirs": 5.0, "lps": 1.0, "oil_level": 0.0}
        self.assertEqual(4, len(anomaly_reasons(row)))

    def test_sql_identifiers_are_validated(self):
        self.assertEqual("metro_dev", validate_identifier("metro_dev", "catalog"))
        with self.assertRaises(ValueError):
            PipelineConfig(catalog="metro; DROP CATALOG metro")


if __name__ == "__main__":
    unittest.main()

