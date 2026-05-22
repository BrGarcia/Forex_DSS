from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import pandas as pd
from analysis.technical import TechnicalAnalyzer
from analysis.candlestick import detect_patterns
from analysis.market_regime import classify_market_regime
from analysis.levels import build_levels, nearest_level

@dataclass(frozen=True)
class TimeframeAnalysis:
    timeframe: str
    trend: str # "bullish", "bearish", "neutral"
    score: float # 0.0 to 1.0
    last_pattern: Optional[str]
    regime: str
    nearest_level: Optional[float]

@dataclass(frozen=True)
class MultiTimeframeResult:
    entry_timeframe: str
    higher_timeframes: List[str]
    alignment: str # "bullish_aligned", "bearish_aligned", "mixed", "countertrend_bullish", "countertrend_bearish"
    alignment_score: float # -1.0 to 1.0
    analyses: Dict[str, TimeframeAnalysis]

class MultiTimeframeAnalyzer:
    """Analisa confluência técnica entre múltiplos timeframes."""
    
    def __init__(self, data_dict: Dict[str, pd.DataFrame]):
        """
        :param data_dict: Dicionário mapeando timeframe (ex: '15m') para DataFrame com indicadores.
        """
        self.data_dict = data_dict

    def analyze_timeframe(self, timeframe: str) -> TimeframeAnalysis:
        """Extrai métricas principais de um timeframe."""
        df = self.data_dict.get(timeframe)
        if df is None or df.empty:
            return TimeframeAnalysis(timeframe, "neutral", 0.0, None, "unknown", None)
            
        ultima = df.iloc[-1]
        
        # Tendência simples (EMA 20 vs 200)
        ema_20 = ultima.get("EMA_20", 0)
        ema_200 = ultima.get("EMA_200", 0)
        trend = "bullish" if ema_20 > ema_200 else "bearish"
        
        # Regime e Níveis
        regime = classify_market_regime(df)
        levels = build_levels(df)
        near = nearest_level(ultima["Close"], levels)
        
        # Padrões
        patterns = detect_patterns(df)
        last_pattern = patterns[0].name if patterns else None
        
        # Score de alinhamento simples (0 a 1)
        score = 0.5 + (0.5 if trend == "bullish" else -0.5)
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            score=score,
            last_pattern=last_pattern,
            regime=regime.label,
            nearest_level=near.price if near else None
        )

    def calculate_alignment(self, analyses: Dict[str, TimeframeAnalysis]) -> Tuple[str, float]:
        """Calcula alinhamento entre timeframes."""
        m15 = analyses.get("15m")
        h1 = analyses.get("1h")
        h4 = analyses.get("4h")
        
        if not m15 or not h1 or not h4:
            return "mixed", 0.0
            
        # Regras de alinhamento
        if m15.trend == "bullish" and h1.trend == "bullish" and h4.trend == "bullish":
            return "bullish_aligned", 1.0
        elif m15.trend == "bearish" and h1.trend == "bearish" and h4.trend == "bearish":
            return "bearish_aligned", 1.0
        elif m15.trend == "bullish" and h4.trend == "bearish":
            return "countertrend_bullish", -0.5
        elif m15.trend == "bearish" and h4.trend == "bullish":
            return "countertrend_bearish", -0.5
        
        return "mixed", 0.0

    def run(self, entry_tf: str = "15m") -> MultiTimeframeResult:
        """Executa a análise completa."""
        analyses = {tf: self.analyze_timeframe(tf) for tf in self.data_dict.keys()}
        alignment, score = self.calculate_alignment(analyses)
        
        return MultiTimeframeResult(
            entry_timeframe=entry_tf,
            higher_timeframes=[tf for tf in self.data_dict.keys() if tf != entry_tf],
            alignment=alignment,
            alignment_score=score,
            analyses=analyses
        )
