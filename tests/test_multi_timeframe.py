import unittest
import pandas as pd
from analysis.multi_timeframe import MultiTimeframeAnalyzer

class TestMultiTimeframe(unittest.TestCase):
    
    def setUp(self):
        # Criar DataFrames sintéticos para M15, H1 e H4
        def create_df(bullish=True):
            trend = 1.05 if bullish else 0.95
            return pd.DataFrame({
                "Open": [1.0] * 101,
                "High": [1.1] * 101,
                "Low":  [0.9] * 101,
                "Close":[trend] * 101,
                "EMA_20": [trend + 0.1] * 101 if bullish else [trend - 0.1] * 101,
                "EMA_200": [1.0] * 101,
                "ADX_14": [25.0] * 101,
                "BBB_20_2.0": [0.005] * 101
            })
            
        self.data_dict = {
            "15m": create_df(bullish=True),
            "1h": create_df(bullish=True),
            "4h": create_df(bullish=True)
        }
        
    def test_calculate_alignment_bullish_aligned(self):
        analyzer = MultiTimeframeAnalyzer(self.data_dict)
        result = analyzer.run()
        self.assertEqual(result.alignment, "bullish_aligned")
        self.assertEqual(result.alignment_score, 1.0)
        
    def test_calculate_alignment_countertrend(self):
        self.data_dict["4h"] = pd.DataFrame({
            "Open": [1.0] * 101, "High": [1.1] * 101, "Low": [0.9] * 101, "Close": [0.95] * 101,
            "EMA_20": [0.9] * 101, "EMA_200": [1.0] * 101,
            "ADX_14": [25.0] * 101, "BBB_20_2.0": [0.005] * 101
        })
        analyzer = MultiTimeframeAnalyzer(self.data_dict)
        result = analyzer.run()
        self.assertEqual(result.alignment, "countertrend_bullish")

    def test_analyze_timeframe_handles_empty_df(self):
        analyzer = MultiTimeframeAnalyzer({"15m": pd.DataFrame()})
        analysis = analyzer.analyze_timeframe("15m")
        self.assertEqual(analysis.trend, "neutral")

if __name__ == '__main__':
    unittest.main()
