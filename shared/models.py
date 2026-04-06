from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeSignal:
    symbol: str
    action: str # "BUY", "SELL", "WAIT"
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    strength: float = 0.0 # Confluência
