import unittest
import pandas as pd
from datetime import datetime, timezone
from app.forex_bot import ForexBot

class TestForexBot(unittest.TestCase):
    def setUp(self):
        self.bot = ForexBot("EURUSD")
        
        # Create a synthetic dataframe for session context testing
        dates = pd.date_range(start=datetime.now(timezone.utc).replace(hour=0, minute=0), periods=96, freq="15min")
        data = {
            'Open': [1.1000] * 96,
            'High': [1.1050] * 96,
            'Low': [1.0950] * 96,
            'Close': [1.1000] * 96
        }
        self.df = pd.DataFrame(data, index=dates)

    def test_obter_contexto_sessao_format(self):
        contexto = self.bot.obter_contexto_sessao(self.df)
        self.assertIsInstance(contexto, str)
        self.assertIn("Sessão Atual:", contexto)

if __name__ == '__main__':
    unittest.main()
