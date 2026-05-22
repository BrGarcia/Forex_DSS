from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import List, Optional

@dataclass(frozen=True)
class CandleAnatomy:
    open: float
    high: float
    low: float
    close: float
    body: float
    range: float
    upper_wick: float
    lower_wick: float
    direction: str  # "bullish", "bearish", "neutral"
    body_ratio: float
    upper_wick_ratio: float
    lower_wick_ratio: float
    close_position: float # 0.0 (at low) to 1.0 (at high)

@dataclass(frozen=True)
class CandlePattern:
    name: str
    direction: str # "bullish", "bearish", "neutral"
    strength: float # 0.0 to 1.0
    reason: str

def analyze_candle(row: pd.Series) -> CandleAnatomy:
    """Calcula a anatomia e proporções de um único candle."""
    o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]
    
    candle_range = float(h - l)
    # Evitar divisão por zero em candles de range zero
    safe_range = candle_range if candle_range > 0 else 1e-10
    
    body = abs(c - o)
    direction = "bullish" if c > o else "bearish" if c < o else "neutral"
    
    if direction == "bullish":
        upper_wick = h - c
        lower_wick = o - l
    elif direction == "bearish":
        upper_wick = h - o
        lower_wick = c - l
    else: # neutral
        upper_wick = h - c
        lower_wick = c - l
        
    body_ratio = body / safe_range
    upper_wick_ratio = upper_wick / safe_range
    lower_wick_ratio = lower_wick / safe_range
    close_position = (c - l) / safe_range
    
    return CandleAnatomy(
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        body=float(body),
        range=float(candle_range),
        upper_wick=float(upper_wick),
        lower_wick=float(lower_wick),
        direction=direction,
        body_ratio=float(body_ratio),
        upper_wick_ratio=float(upper_wick_ratio),
        lower_wick_ratio=float(lower_wick_ratio),
        close_position=float(close_position)
    )

def detect_doji(candle: CandleAnatomy, max_body_ratio: float = 0.1) -> Optional[CandlePattern]:
    """Detecta padrão Doji (corpo muito pequeno em relação ao range)."""
    if candle.range > 0 and candle.body_ratio <= max_body_ratio:
        # Força é maior quanto menor o corpo
        strength = 1.0 - (candle.body_ratio / max_body_ratio)
        return CandlePattern(
            name="doji",
            direction="neutral",
            strength=round(strength, 2),
            reason=f"Corpo representa apenas {candle.body_ratio:.1%} do range"
        )
    return None

def detect_pinbar_bullish(candle: CandleAnatomy) -> Optional[CandlePattern]:
    """
    Detecta Pinbar de alta: pavio inferior longo, corpo pequeno na parte superior.
    Condições:
    - Pavio inferior >= 2x corpo
    - Pavio inferior >= 50% do range
    - Fechamento na metade superior (close_position > 0.5)
    """
    if candle.range <= 0:
        return None
        
    is_long_lower_wick = candle.lower_wick >= (2 * candle.body)
    is_significant_wick = candle.lower_wick_ratio >= 0.5
    is_closed_high = candle.close_position > 0.5
    
    # Pavio superior não deve ser dominante
    is_upper_wick_small = candle.upper_wick_ratio < 0.2
    
    if is_long_lower_wick and is_significant_wick and is_closed_high and is_upper_wick_small:
        strength = (candle.lower_wick_ratio + candle.close_position) / 2
        return CandlePattern(
            name="pinbar_bullish",
            direction="bullish",
            strength=round(strength, 2),
            reason=f"Pavio inferior dominante ({candle.lower_wick_ratio:.1%}) e fechamento alto"
        )
    return None

def detect_pinbar_bearish(candle: CandleAnatomy) -> Optional[CandlePattern]:
    """
    Detecta Pinbar de baixa: pavio superior longo, corpo pequeno na parte inferior.
    Condições:
    - Pavio superior >= 2x corpo
    - Pavio superior >= 50% do range
    - Fechamento na metade inferior (close_position < 0.5)
    """
    if candle.range <= 0:
        return None
        
    is_long_upper_wick = candle.upper_wick >= (2 * candle.body)
    is_significant_wick = candle.upper_wick_ratio >= 0.5
    is_closed_low = candle.close_position < 0.5
    
    # Pavio inferior não deve ser dominante
    is_lower_wick_small = candle.lower_wick_ratio < 0.2
    
    if is_long_upper_wick and is_significant_wick and is_closed_low and is_lower_wick_small:
        strength = (candle.upper_wick_ratio + (1 - candle.close_position)) / 2
        return CandlePattern(
            name="pinbar_bearish",
            direction="bearish",
            strength=round(strength, 2),
            reason=f"Pavio superior dominante ({candle.upper_wick_ratio:.1%}) e fechamento baixo"
        )
    return None

def detect_engulfing_bullish(prev: CandleAnatomy, curr: CandleAnatomy) -> Optional[CandlePattern]:
    """
    Detecta Engolfo de alta: corpo atual engole o corpo anterior.
    Condições:
    - Anterior bearish, atual bullish
    - Fechamento atual > Abertura anterior
    - Abertura atual < Fechamento anterior
    """
    if prev.direction == "bearish" and curr.direction == "bullish":
        if curr.close > prev.open and curr.open < prev.close:
            # Força baseada em quanto o corpo atual supera o anterior
            strength = min(1.0, curr.body / (prev.body if prev.body > 0 else 1e-10) / 2)
            return CandlePattern(
                name="engulfing_bullish",
                direction="bullish",
                strength=round(strength, 2),
                reason="Corpo atual engolindo corpo anterior vendedor"
            )
    return None

def detect_engulfing_bearish(prev: CandleAnatomy, curr: CandleAnatomy) -> Optional[CandlePattern]:
    """
    Detecta Engolfo de baixa: corpo atual engole o corpo anterior.
    Condições:
    - Anterior bullish, atual bearish
    - Fechamento atual < Abertura anterior
    - Abertura atual > Fechamento anterior
    """
    if prev.direction == "bullish" and curr.direction == "bearish":
        if curr.close < prev.open and curr.open > prev.close:
            strength = min(1.0, curr.body / (prev.body if prev.body > 0 else 1e-10) / 2)
            return CandlePattern(
                name="engulfing_bearish",
                direction="bearish",
                strength=round(strength, 2),
                reason="Corpo atual engolindo corpo anterior comprador"
            )
    return None

def detect_inside_bar(prev: CandleAnatomy, curr: CandleAnatomy) -> Optional[CandlePattern]:
    """Detecta Inside Bar: candle atual contido no range do anterior."""
    if curr.high <= prev.high and curr.low >= prev.low:
        return CandlePattern(
            name="inside_bar",
            direction="neutral",
            strength=0.7,
            reason="Candle atual totalmente contido no range anterior"
        )
    return None

def detect_breakout(df: pd.DataFrame, lookback: int = 20) -> Optional[CandlePattern]:
    """Detecta rompimento de máximas/mínimas recentes."""
    if len(df) <= lookback:
        return None
        
    curr_row = df.iloc[-1]
    prev_rows = df.iloc[-(lookback+1):-1]
    
    max_recent = prev_rows["High"].max()
    min_recent = prev_rows["Low"].min()
    
    if curr_row["Close"] > max_recent:
        return CandlePattern(
            name="breakout_bullish",
            direction="bullish",
            strength=0.8,
            reason=f"Fechamento acima da máxima de {lookback} períodos"
        )
    elif curr_row["Close"] < min_recent:
        return CandlePattern(
            name="breakout_bearish",
            direction="bearish",
            strength=0.8,
            reason=f"Fechamento abaixo da mínima de {lookback} períodos"
        )
    return None

def detect_patterns(df: pd.DataFrame) -> List[CandlePattern]:
    """Analisa o DataFrame e retorna todos os padrões detectados no último candle."""
    if len(df) < 2:
        return []
        
    patterns = []
    curr_anatomy = analyze_candle(df.iloc[-1])
    prev_anatomy = analyze_candle(df.iloc[-2])
    
    # Padrões de um único candle
    doji = detect_doji(curr_anatomy)
    if doji: patterns.append(doji)
    
    pin_bull = detect_pinbar_bullish(curr_anatomy)
    if pin_bull: patterns.append(pin_bull)
    
    pin_bear = detect_pinbar_bearish(curr_anatomy)
    if pin_bear: patterns.append(pin_bear)
    
    # Padrões de dois candles
    eng_bull = detect_engulfing_bullish(prev_anatomy, curr_anatomy)
    if eng_bull: patterns.append(eng_bull)
    
    eng_bear = detect_engulfing_bearish(prev_anatomy, curr_anatomy)
    if eng_bear: patterns.append(eng_bear)
    
    inside = detect_inside_bar(prev_anatomy, curr_anatomy)
    if inside: patterns.append(inside)
    
    # Rompimentos
    breakout = detect_breakout(df)
    if breakout: patterns.append(breakout)
    
    # Ordenar por força (decrescente)
    patterns.sort(key=lambda p: p.strength, reverse=True)
    
    return patterns
