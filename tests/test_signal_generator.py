import unittest
import pandas as pd
from strategy.signal_generator import SignalGenerator

class TestSignalGenerator(unittest.TestCase):
    def test_sinal_compra(self):
        # Setup synthetic dataframe to trigger BUY signal
        # BUY conditions: (ema_20 > ema_200) and (rsi < 40) and (preco_atual <= bb_inferior + margem)
        data = {
            'Close': [1.1000],
            'RSI_14': [35.0],
            'EMA_20': [1.1200],
            'EMA_200': [1.1100],
            'BBL_20_2.0': [1.1000],
            'BBU_20_2.0': [1.1400]
        }
        df = pd.DataFrame(data)
        generator = SignalGenerator(df)
        resumo = generator.analisar_e_sugerir()
        self.assertIn("COMPRAR 🟢", resumo)

    def test_sinal_venda(self):
        # Setup synthetic dataframe to trigger SELL signal
        # SELL conditions: (ema_20 < ema_200) and (rsi > 60) and (preco_atual >= bb_superior - margem)
        data = {
            'Close': [1.1400],
            'RSI_14': [65.0],
            'EMA_20': [1.1100],
            'EMA_200': [1.1200],
            'BBL_20_2.0': [1.1000],
            'BBU_20_2.0': [1.1400]
        }
        df = pd.DataFrame(data)
        generator = SignalGenerator(df)
        resumo = generator.analisar_e_sugerir()
        self.assertIn("VENDER 🔴", resumo)

    def test_sinal_neutro(self):
        # Setup synthetic dataframe for wait signal
        data = {
            'Close': [1.1200],
            'RSI_14': [50.0],
            'EMA_20': [1.1200],
            'EMA_200': [1.1100],
            'BBL_20_2.0': [1.1000],
            'BBU_20_2.0': [1.1400]
        }
        df = pd.DataFrame(data)
        generator = SignalGenerator(df)
        resumo = generator.analisar_e_sugerir()
        self.assertIn("ESPERAR (Mercado Neutro)", resumo)

if __name__ == '__main__':
    unittest.main()
