import unittest
import pandas as pd
import numpy as np
from analysis.market_regime import classify_market_regime, MarketRegime

class TestMarketRegime(unittest.TestCase):
    
    def test_classify_market_regime_pre_news_overrides_technical(self):
        df = pd.DataFrame({"Close": [1.1000]})
        regime = classify_market_regime(df, minutes_to_news=10)
        self.assertEqual(regime.label, "pre_news")

    def test_classify_market_regime_strong_uptrend(self):
        # Mock row with strong trend indicators
        data = {
            "EMA_20": [1.1050] * 101,
            "EMA_200": [1.1000] * 101,
            "ADX_14": [30.0] * 101,
            "BBB_20_2.0": [0.0050] * 101,
            "Close": [1.1060] * 101
        }
        df = pd.DataFrame(data)
        
        regime = classify_market_regime(df)
        self.assertEqual(regime.label, "strong_trend")
        self.assertEqual(regime.trend_direction, "bullish")

    def test_classify_market_regime_range(self):
        data = {
            "EMA_20": [1.1005] * 101,
            "EMA_200": [1.1000] * 101,
            "ADX_14": [15.0] * 101,
            "BBB_20_2.0": [0.0050] * 101,
            "Close": [1.1002] * 101
        }
        df = pd.DataFrame(data)
        
        regime = classify_market_regime(df)
        self.assertEqual(regime.label, "range")

    def test_classify_market_regime_compression(self):
        data = {
            "EMA_20": [1.1005] * 101,
            "EMA_200": [1.1000] * 101,
            "ADX_14": [12.0] * 101,
            "BBB_20_2.0": [0.0050] * 100 + [0.0010],
            "Close": [1.1002] * 101
        }
        df = pd.DataFrame(data)
        
        regime = classify_market_regime(df)
        self.assertEqual(regime.label, "compression")

    def test_classify_market_regime_high_volatility(self):
        data = {
            "EMA_20": [1.1005] * 101,
            "EMA_200": [1.1000] * 101,
            "ADX_14": [22.0] * 101,
            "BBB_20_2.0": [0.0050] * 100 + [0.0200],
            "Close": [1.1002] * 101
        }
        df = pd.DataFrame(data)
        
        regime = classify_market_regime(df)
        self.assertEqual(regime.label, "high_volatility")

    def test_handles_missing_columns(self):
        df = pd.DataFrame({"Close": [1.1000]})
        regime = classify_market_regime(df)
        # Não deve quebrar, deve retornar algo sensato
        self.assertIsNotNone(regime.label)

if __name__ == '__main__':
    unittest.main()
