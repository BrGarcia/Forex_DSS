import unittest
import pandas as pd
import numpy as np
from analysis.levels import (
    find_swings, build_levels, nearest_level, 
    is_price_in_zone, detect_level_rejection, 
    calculate_asian_range, classify_price_vs_asian_range,
    PriceLevel
)

class TestLevels(unittest.TestCase):
    
    def setUp(self):
        # Criar um DataFrame básico para testes (preço com leve ruído para evitar flat lines)
        dates = pd.date_range("2026-01-01", periods=20, freq="15min", tz="UTC")
        data = {
            "Open": [1.1000] * 20,
            "High": [1.1005] * 20,
            "Low":  [1.0995] * 20,
            "Close":[1.1000] * 20
        }
        self.df = pd.DataFrame(data, index=dates)

    def test_find_swings_marks_swing_high(self):
        # Injetar uma máxima isolada no meio
        self.df.iloc[10, self.df.columns.get_loc("High")] = 1.1050
        df_swings = find_swings(self.df)
        
        self.assertTrue(df_swings.iloc[10]["swing_high"])
        self.assertFalse(df_swings.iloc[9]["swing_high"])
        self.assertFalse(df_swings.iloc[11]["swing_high"])

    def test_find_swings_marks_swing_low(self):
        # Injetar uma mínima isolada no meio
        self.df.iloc[10, self.df.columns.get_loc("Low")] = 1.0950
        df_swings = find_swings(self.df)
        
        self.assertTrue(df_swings.iloc[10]["swing_low"])

    def test_build_levels_groups_nearby_swings(self):
        # Resetar highs para evitar swings indesejados nas bases
        self.df["High"] = 1.1000
        # Dois swings de alta próximos
        self.df.iloc[5, self.df.columns.get_loc("High")] = 1.1050
        self.df.iloc[15, self.df.columns.get_loc("High")] = 1.1052
        
        # Simular ATR
        self.df["ATRr_14"] = 0.0010
        
        levels = build_levels(self.df)
        
        resistances = [l for l in levels if l.kind == "resistance"]
        self.assertEqual(len(resistances), 1)
        self.assertAlmostEqual(resistances[0].price, 1.1050)

    def test_nearest_level_returns_closest_zone(self):
        l1 = PriceLevel("support", 1.0900, 1.0890, 1.0910, 1, 0.5, "swing")
        l2 = PriceLevel("resistance", 1.1100, 1.1090, 1.1110, 1, 0.5, "swing")
        
        near = nearest_level(1.0920, [l1, l2])
        self.assertEqual(near, l1)

    def test_is_price_in_zone(self):
        lvl = PriceLevel("support", 1.0900, 1.0890, 1.0910, 1, 0.5, "swing")
        self.assertTrue(is_price_in_zone(1.0905, lvl))
        self.assertFalse(is_price_in_zone(1.0920, lvl))

    def test_detect_support_rejection_bullish(self):
        lvl = PriceLevel("support", 1.0900, 1.0890, 1.0910, 1, 0.5, "swing")
        # Candle que atravessa e volta
        candle = pd.Series({"Open": 1.0920, "High": 1.0930, "Low": 1.0885, "Close": 1.0915})
        
        res = detect_level_rejection(candle, lvl)
        self.assertTrue(res["rejected"])
        self.assertEqual(res["direction"], "bullish")

    def test_calculate_asian_range_uses_utc_00_to_08(self):
        # DataFrame cobrindo um dia inteiro
        dates = pd.date_range("2026-01-01 00:00:00", periods=96, freq="15min", tz="UTC")
        data = {
            "Open": [1.1000] * 96,
            "High": [1.1010] * 96,
            "Low":  [1.0990] * 96,
            "Close":[1.1000] * 96
        }
        df = pd.DataFrame(data, index=dates)
        
        # Setar um high específico na madrugada (ex: 03:00)
        df.iloc[12, df.columns.get_loc("High")] = 1.1050
        
        res = calculate_asian_range(df)
        self.assertTrue(res["has_range"])
        self.assertEqual(res["high"], 1.1050)

    def test_classify_price_vs_asian_range(self):
        ar = {"high": 1.1050, "low": 1.1000, "has_range": True}
        self.assertEqual(classify_price_vs_asian_range(1.1060, ar), "above_range")
        self.assertEqual(classify_price_vs_asian_range(1.1040, ar), "inside_range")
        self.assertEqual(classify_price_vs_asian_range(1.0990, ar), "below_range")

if __name__ == '__main__':
    unittest.main()
