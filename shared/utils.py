import pandas as pd

def format_currency(value: float, symbol: str = "USD") -> str:
    """Formata valor de preço com precisão de 5 casas decimais (Forex Standard)."""
    return f"{value:.5f}"

def calcular_distancia_pips(p1: float, p2: float, is_jpy: bool = False) -> float:
    """Calcula a diferença em pips entre dois preços."""
    multiplicador = 100 if is_jpy else 10000
    return abs(p1 - p2) * multiplicador
