import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.calculator import (
    cac,
    cfa_level,
    gross_margin,
    gross_profit,
    payback_period_months,
)


class CalculatorTest(unittest.TestCase):
    def test_unit_economics_formulas(self):
        self.assertEqual(cac(4000, 8), 500)
        self.assertEqual(gross_profit(100, 20), 80)
        self.assertEqual(gross_margin(100, 20), 0.8)
        self.assertEqual(payback_period_months(160, 80, 80), 2)
        self.assertEqual(cfa_level(100, 250), 3)


if __name__ == "__main__":
    unittest.main()
