from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import Tuple, Optional

@dataclass(frozen=True)
class MarketRegime:
    label: str # "strong_trend", "weak_trend", "range", "compression", "high_volatility", "pre_news"
    trend_direction: str # "bullish", "bearish", "neutral"
    trend_strength: float # 0.0 to 1.0
    volatility_label: str # "low", "normal", "high"
    volatility_score: float # 0.0 to 1.0
    reason: str

def classify_trend(row: pd.Series) -> Tuple[str, float]:
    """Classifica a tendência usando EMAs e ADX."""
    ema_20 = row.get("EMA_20")
    ema_200 = row.get("EMA_200")
    adx = row.get("ADX_14", 0)
    
    if ema_20 is None or ema_200 is None:
        return "neutral", 0.0
        
    direction = "bullish" if ema_20 > ema_200 else "bearish"
    
    # Normalizar ADX: 25+ é tendência forte, 50+ é exaustão/extrema
    strength = min(1.0, adx / 50.0)
    
    if adx < 20:
        return "neutral", strength
    
    return direction, strength

def classify_volatility(df: pd.DataFrame) -> Tuple[str, float]:
    """Classifica a volatilidade usando Bollinger Band Width e ATR relativo."""
    if df.empty:
        return "normal", 0.5
        
    ultima = df.iloc[-1]
    
    # Encontrar coluna do Bollinger Band Width
    bbb_cols = [c for c in df.columns if c.startswith('BBB_')]
    bbb = ultima[bbb_cols[0]] if bbb_cols else 0.0
    
    # Média do BBB nos últimos 100 candles
    bbb_mean = df[bbb_cols[0]].tail(100).mean() if bbb_cols else 1.0
    
    rel_vol = bbb / (bbb_mean if bbb_mean > 0 else 1.0)
    
    if rel_vol < 0.75:
        return "low", rel_vol
    elif rel_vol > 1.5:
        return "high", rel_vol
    else:
        return "normal", rel_vol

def classify_market_regime(df: pd.DataFrame, minutes_to_news: int = 1000) -> MarketRegime:
    """Consolida indicadores para definir o regime de mercado."""
    if df.empty:
        return MarketRegime("unknown", "neutral", 0.0, "normal", 0.5, "Dados insuficientes")
        
    if minutes_to_news < 15:
        return MarketRegime("pre_news", "neutral", 0.0, "high", 1.0, "Notícia importante em menos de 15 min")
        
    ultima = df.iloc[-1]
    trend_dir, trend_str = classify_trend(ultima)
    vol_label, vol_score = classify_volatility(df)
    
    adx = ultima.get("ADX_14", 0)
    
    # Encontrar coluna do Bollinger Band Width
    bbb_cols = [c for c in df.columns if c.startswith('BBB_')]
    bbb = ultima[bbb_cols[0]] if bbb_cols else 0.0
    bbb_mean = df[bbb_cols[0]].tail(100).mean() if bbb_cols else 1.0
    
    if adx >= 25:
        label = "strong_trend"
        reason = f"ADX alto ({adx:.1f}) com EMAs alinhadas"
    elif adx < 20 and bbb < (bbb_mean * 0.8):
        label = "compression"
        reason = "ADX baixo e bandas de Bollinger estreitando"
    elif adx < 20:
        label = "range"
        reason = "ADX baixo indicando falta de direção clara"
    elif vol_label == "high":
        label = "high_volatility"
        reason = "Volatilidade acima da média recente"
    else:
        label = "weak_trend"
        reason = "Tendência moderada ou em transição"
        
    return MarketRegime(
        label=label,
        trend_direction=trend_dir,
        trend_strength=trend_str,
        volatility_label=vol_label,
        volatility_score=vol_score,
        reason=reason
    )
