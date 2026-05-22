from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import List, Optional, Dict

@dataclass(frozen=True)
class PriceLevel:
    kind: str  # "support", "resistance", "range_high", "range_low"
    price: float
    lower: float
    upper: float
    touches: int
    strength: float
    source: str # "swing", "asian_range", "psychological"

def find_swings(df: pd.DataFrame, left: int = 2, right: int = 2) -> pd.DataFrame:
    """
    Identifica Swing Highs e Swing Lows no DataFrame.
    Adiciona colunas 'swing_high' e 'swing_low' (boolean).
    """
    df = df.copy()
    df["swing_high"] = False
    df["swing_low"] = False
    
    for i in range(left, len(df) - right):
        window_high = df.iloc[i-left : i+right+1]["High"]
        if df.iloc[i]["High"] == window_high.max() and window_high.max() > window_high.min():
            df.iloc[i, df.columns.get_loc("swing_high")] = True
            
        window_low = df.iloc[i-left : i+right+1]["Low"]
        if df.iloc[i]["Low"] == window_low.min() and window_low.max() > window_low.min():
            df.iloc[i, df.columns.get_loc("swing_low")] = True
            
    return df

def build_levels(df: pd.DataFrame, atr_col: str = "ATRr_14", tolerance_atr: float = 0.25) -> List[PriceLevel]:
    """
    Cria zonas de suporte e resistência a partir de swings próximos.
    """
    if df.empty:
        return []
        
    df_swings = find_swings(df)
    highs = df_swings[df_swings["swing_high"]]["High"].tolist()
    lows = df_swings[df_swings["swing_low"]]["Low"].tolist()
    
    atr = df[atr_col].iloc[-1] if atr_col in df.columns else (df["High"] - df["Low"]).mean()
    tolerance = atr * tolerance_atr
    
    levels = []
    
    # Agrupar Highs (Resistências)
    for h in highs:
        found = False
        for lvl in [l for l in levels if l.kind == "resistance"]:
            if abs(h - lvl.price) <= tolerance:
                # Atualiza nível existente (simplificação: mantém preço original ou média)
                found = True
                # Poderia recalcular a zona aqui se quiser ser mais dinâmico
                break
        if not found:
            levels.append(PriceLevel(
                kind="resistance",
                price=h,
                lower=h - tolerance,
                upper=h + tolerance,
                touches=1,
                strength=0.5,
                source="swing"
            ))
            
    # Agrupar Lows (Suportes)
    for lo in lows:
        found = False
        for lvl in [l for l in levels if l.kind == "support"]:
            if abs(lo - lvl.price) <= tolerance:
                found = True
                break
        if not found:
            levels.append(PriceLevel(
                kind="support",
                price=lo,
                lower=lo - tolerance,
                upper=lo + tolerance,
                touches=1,
                strength=0.5,
                source="swing"
            ))
            
    return levels

def nearest_level(price: float, levels: List[PriceLevel]) -> Optional[PriceLevel]:
    """Retorna o nível mais próximo do preço atual."""
    if not levels:
        return None
    return min(levels, key=lambda l: abs(l.price - price))

def is_price_in_zone(price: float, level: PriceLevel) -> bool:
    """Verifica se o preço está dentro da zona do nível."""
    return level.lower <= price <= level.upper

def detect_level_rejection(candle_row: pd.Series, level: PriceLevel) -> Dict:
    """
    Verifica se um candle rejeitou um nível de preço.
    """
    o, h, l, c = candle_row["Open"], candle_row["High"], candle_row["Low"], candle_row["Close"]
    rejected = False
    direction = "neutral"
    strength = 0.0
    
    if level.kind == "support":
        # Pavio inferior atravessa a zona e fechamento volta acima
        if l < level.upper and c > level.lower:
            if l < level.lower: # Atravessou mesmo
                rejected = True
                direction = "bullish"
                strength = 0.8
            elif l <= level.upper: # Apenas tocou
                rejected = True
                direction = "bullish"
                strength = 0.5
                
    elif level.kind == "resistance":
        # Pavio superior atravessa a zona e fechamento volta abaixo
        if h > level.lower and c < level.upper:
            if h > level.upper:
                rejected = True
                direction = "bearish"
                strength = 0.8
            elif h >= level.lower:
                rejected = True
                direction = "bearish"
                strength = 0.5
                
    return {
        "rejected": rejected,
        "direction": direction,
        "strength": strength,
        "level": level
    }

def calculate_asian_range(df: pd.DataFrame, date_utc: Optional[pd.Timestamp] = None) -> Dict:
    """
    Calcula o range asiático (00:00 às 08:00 UTC).
    """
    if df.empty:
        return {"has_range": False}
        
    if date_utc is None:
        date_utc = df.index[-1].normalize()
    else:
        date_utc = pd.Timestamp(date_utc).normalize()
        
    df_day = df[df.index.normalize() == date_utc]
    df_asia = df_day[(df_day.index.hour >= 0) & (df_day.index.hour < 8)]
    
    if df_asia.empty:
        return {"has_range": False}
        
    h = df_asia["High"].max()
    l = df_asia["Low"].min()
    
    return {
        "high": h,
        "low": l,
        "mid": (h + l) / 2,
        "has_range": True
    }

def classify_price_vs_asian_range(price: float, asian_range: Dict) -> str:
    """Classifica a posição do preço em relação ao range asiático."""
    if not asian_range.get("has_range"):
        return "no_range"
        
    if price > asian_range["high"]:
        return "above_range"
    elif price < asian_range["low"]:
        return "below_range"
    else:
        return "inside_range"
