import unittest
import pandas as pd
import numpy as np
from analysis.candlestick import (
    analyze_candle, detect_doji, detect_pinbar_bullish, 
    detect_pinbar_bearish, detect_engulfing_bullish, 
    detect_engulfing_bearish, detect_inside_bar, 
    detect_breakout, detect_patterns
)

class TestCandlestick(unittest.TestCase):
    
    def test_analyze_candle_bullish_anatomy(self):
        # Candle: Open=1.1000, High=1.1050, Low=1.0980, Close=1.1040
        row = pd.Series({
            "Open": 1.1000, "High": 1.1050, "Low": 1.0980, "Close": 1.1040
        })
        anatomy = analyze_candle(row)
        
        self.assertEqual(anatomy.direction, "bullish")
        self.assertAlmostEqual(anatomy.body, 0.0040)
        self.assertAlmostEqual(anatomy.range, 0.0070)
        self.assertAlmostEqual(anatomy.upper_wick, 0.0010)
        self.assertAlmostEqual(anatomy.lower_wick, 0.0020)
        self.assertAlmostEqual(anatomy.close_position, (1.1040 - 1.0980) / 0.0070)

    def test_analyze_candle_bearish_anatomy(self):
        # Candle: Open=1.1040, High=1.1050, Low=1.0980, Close=1.1000
        row = pd.Series({
            "Open": 1.1040, "High": 1.1050, "Low": 1.0980, "Close": 1.1000
        })
        anatomy = analyze_candle(row)
        
        self.assertEqual(anatomy.direction, "bearish")
        self.assertAlmostEqual(anatomy.body, 0.0040)
        self.assertAlmostEqual(anatomy.upper_wick, 0.0010)
        self.assertAlmostEqual(anatomy.lower_wick, 0.0020)

    def test_detect_doji_returns_neutral_pattern(self):
        # Doji: Open=1.1000, High=1.1010, Low=1.0990, Close=1.1001
        row = pd.Series({
            "Open": 1.1000, "High": 1.1010, "Low": 1.0990, "Close": 1.1001
        })
        anatomy = analyze_candle(row)
        pattern = detect_doji(anatomy)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "doji")
        self.assertEqual(pattern.direction, "neutral")
        self.assertTrue(pattern.strength > 0)

    def test_detect_pinbar_bullish(self):
        # Pinbar Alta: Open=1.1030, High=1.1040, Low=1.1000, Close=1.1035
        # Range = 0.0040, Body = 0.0005, Lower Wick = 0.0030
        row = pd.Series({
            "Open": 1.1030, "High": 1.1040, "Low": 1.1000, "Close": 1.1035
        })
        anatomy = analyze_candle(row)
        pattern = detect_pinbar_bullish(anatomy)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "pinbar_bullish")
        self.assertEqual(pattern.direction, "bullish")
        self.assertTrue(0.0 <= pattern.strength <= 1.0)

    def test_detect_pinbar_bearish(self):
        # Pinbar Baixa: Open=1.1010, High=1.1050, Low=1.1005, Close=1.1008
        # Range = 0.0045, Body = 0.0002, Upper Wick = 0.0040
        row = pd.Series({
            "Open": 1.1010, "High": 1.1050, "Low": 1.1005, "Close": 1.1008
        })
        anatomy = analyze_candle(row)
        pattern = detect_pinbar_bearish(anatomy)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "pinbar_bearish")
        self.assertEqual(pattern.direction, "bearish")

    def test_pinbar_bullish_rejects_large_upper_wick(self):
        # Pavios iguais (não é pinbar)
        row = pd.Series({
            "Open": 1.1020, "High": 1.1050, "Low": 1.1000, "Close": 1.1025
        })
        anatomy = analyze_candle(row)
        pattern = detect_pinbar_bullish(anatomy)
        self.assertIsNone(pattern)

    def test_detect_engulfing_bullish(self):
        prev_row = pd.Series({"Open": 1.1020, "High": 1.1025, "Low": 1.1010, "Close": 1.1015}) # Bearish
        curr_row = pd.Series({"Open": 1.1010, "High": 1.1035, "Low": 1.1005, "Close": 1.1030}) # Bullish (Engulfs)
        
        prev = analyze_candle(prev_row)
        curr = analyze_candle(curr_row)
        pattern = detect_engulfing_bullish(prev, curr)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "engulfing_bullish")

    def test_detect_engulfing_bearish(self):
        prev_row = pd.Series({"Open": 1.1015, "High": 1.1025, "Low": 1.1010, "Close": 1.1020}) # Bullish
        curr_row = pd.Series({"Open": 1.1025, "High": 1.1030, "Low": 1.1000, "Close": 1.1005}) # Bearish (Engulfs)
        
        prev = analyze_candle(prev_row)
        curr = analyze_candle(curr_row)
        pattern = detect_engulfing_bearish(prev, curr)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "engulfing_bearish")

    def test_detect_inside_bar(self):
        prev_row = pd.Series({"Open": 1.1000, "High": 1.1050, "Low": 1.0950, "Close": 1.1040})
        curr_row = pd.Series({"Open": 1.1000, "High": 1.1020, "Low": 1.0980, "Close": 1.1010}) # Inside
        
        prev = analyze_candle(prev_row)
        curr = analyze_candle(curr_row)
        pattern = detect_inside_bar(prev, curr)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "inside_bar")

    def test_detect_breakout_bullish(self):
        data = {
            "Open": [1.1000] * 20 + [1.1040],
            "High": [1.1020] * 20 + [1.1060],
            "Low":  [1.0980] * 20 + [1.1040],
            "Close":[1.1010] * 20 + [1.1055]
        }
        df = pd.DataFrame(data)
        pattern = detect_breakout(df, lookback=20)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "breakout_bullish")

    def test_detect_patterns_returns_sorted_by_strength(self):
        # Candle que é tanto breakout quanto pinbar (hipotético para teste)
        data = {
            "Open": [1.1000] * 20 + [1.1030],
            "High": [1.1020] * 20 + [1.1055],
            "Low":  [1.0980] * 20 + [1.1000],
            "Close":[1.1010] * 20 + [1.1050]
        }
        df = pd.DataFrame(data)
        patterns = detect_patterns(df)
        
        self.assertTrue(len(patterns) >= 1)
        # Verificar se está ordenado (descendente)
        strengths = [p.strength for p in patterns]
        self.assertEqual(strengths, sorted(strengths, reverse=True))

    def test_zero_range_candle_does_not_crash(self):
        row = pd.Series({
            "Open": 1.1000, "High": 1.1000, "Low": 1.1000, "Close": 1.1000
        })
        # Não deve levantar ZeroDivisionError
        anatomy = analyze_candle(row)
        self.assertEqual(anatomy.range, 0.0)
        self.assertEqual(anatomy.body_ratio, 0.0)

if __name__ == '__main__':
    unittest.main()
