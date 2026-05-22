from analysis.candlestick import detect_patterns
from analysis.levels import build_levels, nearest_level
import pandas as pd


class SignalGenerator:
    """
    Motor de Confluência e Gestão de Risco.
    """

    def __init__(self, dataframe: pd.DataFrame, risco_recompensa: float = 2.0):
        self.df       = dataframe
        self.rr_ratio = risco_recompensa

    def _calculate_structural_stop(self, action: str, entry: float, atr: float, nearest_level: float = None) -> float:
        """Calcula SL baseado em volatilidade ou nível técnico."""
        buffer = atr * 0.2
        if nearest_level:
            if action == "BUY": return min(entry - atr * 1.5, nearest_level - buffer)
            return max(entry + atr * 1.5, nearest_level + buffer)
        
        if action == "BUY": return entry - atr * 1.5
        return entry + atr * 1.5

    def analisar_e_sugerir(self, score_data: dict = None) -> str:
        if self.df.empty:
            return "Sem dados para gerar sinal."

        ultima = self.df.iloc[-1]
        preco_atual = float(ultima['Close'])
        atr = float(ultima.get('ATRr_14', 0.0015))
        
        levels = build_levels(self.df)
        near = nearest_level(preco_atual, levels)
        near_price = near.price if near else None
        
        # Lógica de sinal baseada em Score e Estrutura
        sinal = "WAIT ⚪"
        stop_loss = 0.0
        take_profit = 0.0
        
        if score_data:
            score = score_data.get("score", 50)
            if score > 70:
                sinal = "BUY 🟢"
                stop_loss = self._calculate_structural_stop("BUY", preco_atual, atr, near_price)
                take_profit = preco_atual + (preco_atual - stop_loss) * self.rr_ratio
            elif score < 30:
                sinal = "SELL 🔴"
                stop_loss = self._calculate_structural_stop("SELL", preco_atual, atr, near_price)
                take_profit = preco_atual - (stop_loss - preco_atual) * self.rr_ratio

        return f"\n{'='*50}\nSIGNAL: {sinal}\nSL: {stop_loss:.5f}\nTP: {take_profit:.5f}\n{'='*50}"