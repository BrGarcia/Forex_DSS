import pandas as pd

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


def candle_strength(open_: float, close: float, high: float, low: float) -> float:
    """Força direcional do candle: corpo vs range total."""
    body    = abs(close - open_)
    range_  = high - low if high != low else 1e-9
    direction = 1 if close > open_ else -1
    return clamp(direction * (body / range_) * 2)


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


def distance_from_ema(price: float, ema: float) -> float:
    """Distância relativa do preço à EMA. Mercado 'esticado' = possível reversão."""
    if ema == 0:
        return 0.0
    return clamp((price - ema) / ema * 100)


# ─────────────────────────────────────────────────────────────
# 4. FILTROS INSTITUCIONAIS
# ─────────────────────────────────────────────────────────────
def atr_volatility(atr: float, price: float) -> float:
    """Alta volatilidade = maior probabilidade de movimento direcional."""
    if price == 0:
        return 0.0
    return clamp(atr / price * 1000)


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

    Transforma múltiplas variáveis técnicas num score único de probabilidade:
      - 0   → Forte pressão vendedora
      - 50  → Mercado neutro
      - 100 → Forte pressão compradora

    Faixas de interpretação:
      - 70–100 → Compra
      - 30–70  → Aguardar
      - 0–30   → Venda

    Uso:
        indicador = PercentualIndicator(df_com_indicadores)
        resultado = indicador.calcular(session_str="europeia", minutes_to_news=45)
        print(indicador.formatar_painel("europeia", 45))
    """

    WEIGHTS: dict = {
        "ema_t":    25,
        "ema_s":    15,
        "rsi":      15,
        "candle":   10,
        "bb":       15,
        "dist_ema":  5,
        "atr":       5,
        "session":   5,
        "news":      5,
    }

    def __init__(self, df: pd.DataFrame):
        if len(df) < 2:
            raise ValueError(
                "DataFrame precisa ter ao menos 2 linhas para calcular o PercentualIndicator."
            )
        self.df         = df
        self._ultima    = df.iloc[-1]
        self._penultima = df.iloc[-2]

        # Resolve nomes de colunas dinâmicas (pandas_ta inclui parâmetros no nome)
        bbl_cols = [c for c in df.columns if c.startswith('BBL_')]
        bbu_cols = [c for c in df.columns if c.startswith('BBU_')]
        self._col_bbl = bbl_cols[0] if bbl_cols else None
        self._col_bbu = bbu_cols[0] if bbu_cols else None

    # ── Cálculo Principal ────────────────────────────────────
    def calcular(self, session_str: str = "", minutes_to_news: int = 1000) -> dict:
        """
        Calcula o score percentual de confluência.

        Args:
            session_str     : Descrição da sessão atual (ex: "europeia", "americana").
            minutes_to_news : Minutos até o próximo evento econômico de alto impacto.

        Returns:
            dict com:
              - 'score'     : float 0–100
              - 'direction' : str ("BUY 🟢" | "SELL 🔴" | "WAIT ⚪")
              - 'label'     : str ("COMPRA" | "VENDA" | "NEUTRO")
              - 'details'   : dict com contribuição normalizada de cada componente
        """
        u = self._ultima
        p = self._penultima

        # ── Extração de dados do DataFrame ──
        price     = float(u['Close'])
        ema_short = float(u['EMA_20'])
        ema_long  = float(u['EMA_200'])
        ema_prev  = float(p['EMA_20'])
        rsi       = float(u['RSI_14'])
        open_     = float(u['Open'])
        close     = float(u['Close'])
        high      = float(u['High'])
        low       = float(u['Low'])
        bb_lower  = float(u[self._col_bbl]) if self._col_bbl else price
        bb_upper  = float(u[self._col_bbu]) if self._col_bbu else price
        atr_val   = float(u.get('ATRr_14', price * 0.001))

        # ── Cálculo dos componentes ──
        ema_t  = ema_trend(ema_short, ema_long)
        ema_s  = ema_slope(ema_short, ema_prev)
        rsi_c  = rsi_score(rsi)
        candle = candle_strength(open_, close, high, low)
        bb_c   = bollinger_position(price, bb_lower, bb_upper)
        dist_c = distance_from_ema(price, ema_short)
        atr_c  = atr_volatility(atr_val, price)
        sess_c = session_score(session_str)
        news_c = news_risk(minutes_to_news)

        # ── Score ponderado ──
        w = self.WEIGHTS
        score = 50.0 + (
            ema_t  * w["ema_t"]    +
            ema_s  * w["ema_s"]    +
            rsi_c  * w["rsi"]      +
            candle * w["candle"]   +
            bb_c   * w["bb"]       +
            dist_c * w["dist_ema"] +
            atr_c  * w["atr"]      +
            sess_c * w["session"]  +
            news_c * w["news"]
        )
        score = max(0.0, min(100.0, score))

        # ── Interpretação ──
        if score > 70:
            direction, label = "BUY 🟢",  "COMPRA"
        elif score < 30:
            direction, label = "SELL 🔴", "VENDA"
        else:
            direction, label = "WAIT ⚪", "NEUTRO"

        return {
            "score":     round(score, 2),
            "direction": direction,
            "label":     label,
            "details": {
                "ema_trend": round(ema_t,  3),
                "ema_slope": round(ema_s,  3),
                "rsi":       round(rsi_c,  3),
                "candle":    round(candle, 3),
                "bollinger": round(bb_c,   3),
                "dist_ema":  round(dist_c, 3),
                "atr":       round(atr_c,  3),
                "session":   round(sess_c, 3),
                "news":      round(news_c, 3),
            }
        }

    # ── Formatação Visual ────────────────────────────────────
    @staticmethod
    def formatar_barra(score: float, largura: int = 20) -> str:
        """Barra de progresso visual para a CLI. Ex: [████████░░░░░░░░░░░░] 40.0%"""
        preenchimento = int((score / 100) * largura)
        barra = "█" * preenchimento + "░" * (largura - preenchimento)
        return f"[{barra}] {score:.1f}%"

    def formatar_painel(self, session_str: str = "", minutes_to_news: int = 1000) -> str:
        """Painel completo para exibição na CLI com decomposição por componente."""
        r     = self.calcular(session_str, minutes_to_news)
        score = r["score"]
        d     = r["details"]
        w     = self.WEIGHTS
        barra = self.formatar_barra(score)

        return (
            f"\n{'='*50}\n"
            f"📊 INDICADOR PERCENTUAL DE CONFLUÊNCIA\n"
            f"{'='*50}\n"
            f"  Score   : {barra}\n"
            f"  Direção : {r['direction']}\n"
            f"{'-'*50}\n"
            f"  EMA Trend  ({w['ema_t']:>2}pt) : {d['ema_trend']:+.3f}\n"
            f"  EMA Slope  ({w['ema_s']:>2}pt) : {d['ema_slope']:+.3f}\n"
            f"  RSI        ({w['rsi']:>2}pt) : {d['rsi']:+.3f}\n"
            f"  Candle     ({w['candle']:>2}pt) : {d['candle']:+.3f}\n"
            f"  Bollinger  ({w['bb']:>2}pt) : {d['bollinger']:+.3f}\n"
            f"  Dist. EMA  ( {w['dist_ema']}pt) : {d['dist_ema']:+.3f}\n"
            f"  ATR        ( {w['atr']}pt) : {d['atr']:+.3f}\n"
            f"  Sessão     ( {w['session']}pt) : {d['session']:+.3f}\n"
            f"  Notícia    ( {w['news']}pt) : {d['news']:+.3f}\n"
            f"{'='*50}"
        )

    def resumo_radar(self, session_str: str = "", minutes_to_news: int = 1000) -> str:
        """Versão ultra-compacta para exibição no radar de 1 linha."""
        r = self.calcular(session_str, minutes_to_news)
        return f"📊{r['score']:.0f}%"


# ─────────────────────────────────────────────────────────────
# Função legada (mantida para compatibilidade)
# ─────────────────────────────────────────────────────────────
def advanced_forex_score(data: dict) -> dict:
    """
    Interface funcional (legacy). Prefira a classe PercentualIndicator para integração.
    """
    ema_t  = ema_trend(data.get("ema_short", 0), data.get("ema_long", 1))
    ema_s  = ema_slope(data.get("ema_short", 0), data.get("ema_short_prev", 1))
    rsi    = rsi_score(data.get("rsi", 50))
    candle = candle_strength(data.get("open", 0), data.get("close", 0),
                              data.get("high", 0), data.get("low", 0))
    bb     = bollinger_position(data.get("price", 0),
                                 data.get("bb_lower", 0), data.get("bb_upper", 0))
    dist   = distance_from_ema(data.get("price", 0), data.get("ema_short", 1))
    atr    = atr_volatility(data.get("atr", 0), data.get("price", 1))
    sess   = session_score(data.get("session", ""))
    news   = news_risk(data.get("minutes_to_news", 1000))

    w = PercentualIndicator.WEIGHTS
    score = 50.0 + (
        ema_t * w["ema_t"] + ema_s * w["ema_s"] + rsi * w["rsi"] +
        candle * w["candle"] + bb * w["bb"] + dist * w["dist_ema"] +
        atr * w["atr"] + sess * w["session"] + news * w["news"]
    )
    score = max(0.0, min(100.0, score))
    direction = "BUY 🟢" if score > 70 else ("SELL 🔴" if score < 30 else "WAIT ⚪")
    return {"score": round(score, 2), "direction": direction}
