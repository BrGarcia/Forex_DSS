import unittest
import pandas as pd
import numpy as np
from analysis.technical import TechnicalAnalyzer

class TestTechnicalAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a synthetic dataframe for testing
        dates = pd.date_range(start="2023-01-01", periods=250, freq="15min")
        data = {
            'Open': np.random.uniform(1.05, 1.10, 250),
            'High': np.random.uniform(1.10, 1.15, 250),
            'Low': np.random.uniform(1.00, 1.05, 250),
            'Close': np.random.uniform(1.05, 1.10, 250),
            'Volume': np.random.randint(100, 1000, 250)
        }
        self.df = pd.DataFrame(data, index=dates)
        self.analyzer = TechnicalAnalyzer(self.df)

    def test_calcular_indicadores(self):
        df_result = self.analyzer.calcular_indicadores()
        
        # Check if indicators are present
        self.assertIn('RSI_14', df_result.columns)
        self.assertIn('EMA_20', df_result.columns)
        self.assertIn('EMA_200', df_result.columns)
        
        # Bollinger Bands columns
        bb_cols = [c for c in df_result.columns if c.startswith('BBL_') or c.startswith('BBU_')]
        self.assertGreaterEqual(len(bb_cols), 2)
        
        # Check if NaN values are dropped (first 200 rows should be NaN for EMA_200)
        self.assertFalse(df_result.isnull().values.any())
        self.assertLess(len(df_result), len(self.df))

    def test_gerar_resumo_atual(self):
        resumo = self.analyzer.gerar_resumo_atual()
        self.assertIsInstance(resumo, str)
        self.assertIn("LEITURA TÉCNICA", resumo)
        self.assertIn("Preço Atual", resumo)
        self.assertIn("Tendência Principal", resumo)

if __name__ == '__main__':
    unittest.main()
