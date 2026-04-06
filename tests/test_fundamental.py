import unittest
from analysis.fundamental import FundamentalAnalyzer

class TestFundamentalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = FundamentalAnalyzer()

    def test_obter_eventos(self):
        eventos = self.analyzer.obter_proximos_eventos()
        self.assertIsInstance(eventos, list)
        self.assertGreater(len(eventos), 0)
        self.assertIn("impact", eventos[0])

    def test_verificar_alerta(self):
        alerta = self.analyzer.verificar_alerta_proximo("EURUSD")
        self.assertIsInstance(alerta, str)
        # Como o evento USD é simulado para daqui a 45 min, deve haver um alerta
        self.assertIn("⚠️", alerta)

if __name__ == '__main__':
    unittest.main()
