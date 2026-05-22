import pandas as pd
from analysis.candlestick import detect_patterns
from analysis.market_regime import classify_market_regime
from analysis.levels import build_levels, detect_level_rejection

# ─────────────────────────────────────────────────────────────
# Utilitário
# ─────────────────────────────────────────────────────────────
def clamp(v: float, min_v: float = -1.0, max_v: float = 1.0) -> float:
    return max(min_v, min(max_v, v))


# ─────────────────────────────────────────────────────────────
# 1. TENDÊNCIA
# ─────────────────────────────────────────────────────────────
def ema_trend(ema_short: float, ema_long: float) -> float:
    """Diferença relativa entre EMA curta e longa. +1 = alta forte, -1 = baixa forte."""
    if ema_long == 0:
        return 0.0
    diff = (ema_short - ema_long) / ema_long
    return clamp(diff * 200)


def ema_slope(ema_current: float, ema_previous: float) -> float:
    """Inclinação da EMA curta. Evita sinais atrasados de cruzamento."""
    if ema_previous == 0:
        return 0.0
    slope = (ema_current - ema_previous) / ema_previous
    return clamp(slope * 500)


# ─────────────────────────────────────────────────────────────
# 2. MOMENTO
# ─────────────────────────────────────────────────────────────
def rsi_score(rsi: float) -> float:
    """RSI normalizado em torno de 50. +1 = sobrecomprado, -1 = sobrevendido."""
    return clamp((rsi - 50) / 20)


# ─────────────────────────────────────────────────────────────
# 3. CONTEXTO DE PREÇO
# ─────────────────────────────────────────────────────────────
def bollinger_position(price: float, bb_lower: float, bb_upper: float) -> float:
    """
    Posição relativa dentro das Bandas de Bollinger.
    +1 = próximo da banda inferior (potencial compra),
    -1 = próximo da banda superior (potencial venda).
    """
    if bb_upper == bb_lower:
        return 0.0
    pos = (price - bb_lower) / (bb_upper - bb_lower)
    pos = max(0.0, min(1.0, pos))
    return 1.0 - (pos * 2)


# ─────────────────────────────────────────────────────────────
# 4. FILTROS INSTITUCIONAIS
# ─────────────────────────────────────────────────────────────
def session_score(session: str) -> float:
    """
    Londres / NY = alta liquidez (+1).
    Ásia = menor movimentação (-0.2).
    Fora de sessão = neutro (0).
    """
    s = session.lower()
    if any(k in s for k in ("london", "new_york", "ny", "europeia",
                             "americana", "overlap", "sobreposição")):
        return 1.0
    elif any(k in s for k in ("asia", "asiática", "tóquio", "tokyo")):
        return -0.2
    return 0.0


def news_risk(minutes_to_news: int) -> float:
    """
    Risco de notícia: reduz o score para evitar entradas em alta imprevisibilidade.
    < 15 min = risco crítico (-1), < 60 min = risco elevado (-0.5).
    """
    if minutes_to_news < 15:
        return -1.0
    elif minutes_to_news < 60:
        return -0.5
    return 0.0


# ─────────────────────────────────────────────────────────────
# CLASSE PRINCIPAL
# ─────────────────────────────────────────────────────────────
class PercentualIndicator:
    """
    Indicador de Confluência Percentual (0–100).
    """

    WEIGHTS: dict = {
        "ema_t":    15,
        "ema_s":    10,
        "rsi":      10,
        "candle":   15,
        "bb":       10,
        "level":    15,
        "mtf":      15,
        "regime":    5,
        "quality": -10,
        "news":     -5,
    }

    def __init__(self, df: pd.DataFrame, quality_report: dict = None):
        if len(df) < 2:
            raise ValueError("DataFrame precisa ter ao menos 2 linhas.")
        self.df         = df
        self._ultima    = df.iloc[-1]
        self._penultima = df.iloc[-2]
        self._quality   = quality_report
        
        # Resolve nomes de colunas dinâmicas
        bbl_cols = [c for c in df.columns if c.startswith('BBL_')]
        bbu_cols = [c for c in df.columns if c.startswith('BBU_')]
        self._col_bbl = bbl_cols[0] if bbl_cols else None
        self._col_bbu = bbu_cols[0] if bbu_cols else None

    # ── Cálculo Principal ────────────────────────────────────
    def calcular(self, session_str: str = "", minutes_to_news: int = 1000) -> dict:
        """Calcula o score com novas confluências."""
        u = self._ultima
        
        # 1. Indicadores Base
        ema_t  = ema_trend(float(u['EMA_20']), float(u['EMA_200']))
        ema_s  = ema_slope(float(u['EMA_20']), float(self._penultima['EMA_20']))
        rsi_c  = rsi_score(float(u['RSI_14']))
        bb_c   = bollinger_position(float(u['Close']), float(u[self._col_bbl]) if self._col_bbl else float(u['Close']), float(u[self._col_bbu]) if self._col_bbu else float(u['Close']))
        
        # 2. Candlestick
        patterns = detect_patterns(self.df)
        candle_c = 0.0
        if patterns:
            main_p = patterns[0]
            if main_p.direction == "bullish": candle_c = main_p.strength
            elif main_p.direction == "bearish": candle_c = -main_p.strength
            
        # 3. Níveis
        levels = build_levels(self.df)
        near = nearest_level(float(u['Close']), levels)
        level_c = 0.0
        if near:
            rej = detect_level_rejection(u, near)
            if rej["rejected"]:
                level_c = rej["strength"] if rej["direction"] == "bullish" else -rej["strength"]

        # 4. Regime
        regime = classify_market_regime(self.df, minutes_to_news)
        regime_c = regime.trend_strength if regime.trend_direction == "bullish" else -regime.trend_strength

        # 5. Penalidades
        qual_c = 0.0
        if self._quality and not self._quality.get("is_valid", True):
            qual_c = 1.0 # Penalidade total

        # Score
        w = self.WEIGHTS
        score = 50.0 + (
            ema_t * w["ema_t"] + ema_s * w["ema_s"] + rsi_c * w["rsi"] +
            candle_c * w["candle"] + bb_c * w["bb"] + 
            level_c * w["level"] + regime_c * w["regime"] +
            qual_c * w["quality"] + news_risk(minutes_to_news) * 5
        )
        score = max(0.0, min(100.0, score))
        
        # Interpretação
        if score > 70: direction, label = "BUY 🟢",  "COMPRA"
        elif score < 30: direction, label = "SELL 🔴", "VENDA"
        else: direction, label = "WAIT ⚪", "NEUTRO"

        return {
            "score":     round(score, 2),
            "direction": direction,
            "label":     label,
            "details": {
                "ema_trend": round(ema_t,  3),
                "ema_slope": round(ema_s,  3),
                "rsi":       round(rsi_c,  3),
                "candle":    round(candle_c, 3),
                "bollinger": round(bb_c,   3),
                "level":     round(level_c, 3),
                "regime":    round(regime_c, 3),
                "quality":   round(qual_c, 3),
            }
        }

    @staticmethod
    def formatar_barra(score: float, largura: int = 20) -> str:
        preenchimento = int((score / 100) * largura)
        barra = "█" * preenchimento + "░" * (largura - preenchimento)
        return f"[{barra}] {score:.1f}%"

    def formatar_painel(self, session_str: str = "", minutes_to_news: int = 1000) -> str:
        """Painel completo."""
        r = self.calcular(session_str, minutes_to_news)
        d = r["details"]
        return f"\n{'='*50}\n📊 INDICADOR CONFLUÊNCIA ({r['score']:.1f}%)\n{'='*50}\nDireção: {r['direction']}\nDetails: {d}"
