# 📊 INDICADOR_PERCENTUAL

## 🧠 Objetivo

Este indicador tem como objetivo transformar múltiplas variáveis técnicas do mercado Forex em um **score percentual (0 a 100)** que represente a probabilidade de uma operação:

- **0 → Forte venda**
- **50 → Neutro**
- **100 → Forte compra**

Diferente de indicadores tradicionais, este modelo funciona como um **sistema de confluência**, agregando tendência, momento, contexto e fatores externos.

---

# 🧱 Estrutura do Modelo

O modelo é dividido em **4 camadas principais**:

## 1. Tendência (Bias Direcional)

### 🔹 EMA Trend
Mede a diferença entre duas médias móveis exponenciais:
- EMA curta acima da longa → tendência de alta
- EMA curta abaixo da longa → tendência de baixa

### 🔹 EMA Slope
Mede a inclinação da EMA curta:
- Inclinação positiva → aceleração de alta
- Inclinação negativa → aceleração de baixa

👉 Isso evita sinais atrasados de cruzamento simples.

---

## 2. Momento (Momentum)

### 🔹 RSI
Normalizado em torno de 50:
- RSI > 50 → pressão compradora
- RSI < 50 → pressão vendedora

### 🔹 Força do Candle
Mede o tamanho do corpo em relação ao range:
- Corpo grande → movimento forte
- Corpo pequeno → indecisão

👉 Direção do candle é considerada (alta ou baixa).

---

## 3. Contexto de Preço

### 🔹 Bollinger Bands
Posição do preço dentro das bandas:
- Próximo da banda inferior → possível compra
- Próximo da banda superior → possível venda

### 🔹 Distância da EMA
- Preço muito afastado da EMA → mercado esticado
- Preço próximo da EMA → zona de equilíbrio

---

## 4. Filtros Institucionais

### 🔹 Volatilidade (ATR)
- Alta volatilidade → maior probabilidade de movimento
- Baixa volatilidade → mercado lateral

### 🔹 Sessão de Mercado
- Londres / NY → maior liquidez
- Ásia → menor movimentação

### 🔹 Risco de Notícia
- Próximo de eventos → alta imprevisibilidade

---

# ⚙️ Cálculo do Score

Cada componente é normalizado entre **-1 e +1**.

O score final é calculado como:

```
Score = 50 + Σ (componente * peso)
```

Onde:
- 50 = ponto neutro
- pesos definem a importância relativa

---

# ⚖️ Pesos Utilizados

| Componente | Peso |
|----------|------|
| EMA Trend | 25 |
| EMA Slope | 15 |
| RSI | 15 |
| Candle | 10 |
| Bollinger | 15 |
| Distância EMA | 5 |
| ATR | 5 |
| Sessão | 5 |
| Notícia | 5 |

---

# 🎯 Interpretação

| Score | Ação |
|------|------|
| 0–30 | Venda |
| 30–70 | Neutro |
| 70–100 | Compra |

---

# ⚠️ Considerações Importantes

- O score não é certeza, mas **probabilidade estatística**
- Deve ser usado como filtro, não gatilho isolado
- Melhor desempenho com confirmação (price action)

---

# 💻 Implementação em Python

```python
import math

def clamp(v, min_v=-1, max_v=1):
    return max(min_v, min(max_v, v))

# =========================
# 1. TENDÊNCIA
# =========================
def ema_trend(ema_short, ema_long):
    diff = (ema_short - ema_long) / ema_long
    return clamp(diff * 200)


def ema_slope(ema_current, ema_previous):
    slope = (ema_current - ema_previous) / ema_previous
    return clamp(slope * 500)

# =========================
# 2. MOMENTO
# =========================
def rsi_score(rsi):
    return clamp((rsi - 50) / 20)


def candle_strength(open_, close, high, low):
    body = abs(close - open_)
    range_ = high - low if high != low else 1

    strength = body / range_

    direction = 1 if close > open_ else -1
    return clamp(direction * strength * 2)

# =========================
# 3. CONTEXTO
# =========================
def bollinger_position(price, bb_lower, bb_upper):
    if bb_upper == bb_lower:
        return 0

    pos = (price - bb_lower) / (bb_upper - bb_lower)
    pos = max(0, min(1, pos))

    return 1 - (pos * 2)


def distance_from_ema(price, ema):
    dist = (price - ema) / ema
    return clamp(dist * 100)

# =========================
# 4. VOLATILIDADE
# =========================
def atr_volatility(atr, price):
    ratio = atr / price
    return clamp(ratio * 1000)

# =========================
# 5. FILTROS EXTERNOS
# =========================
def session_score(session):
    if session == "london" or session == "new_york":
        return 1
    elif session == "asia":
        return -0.2
    return 0


def news_risk(minutes_to_news):
    if minutes_to_news < 15:
        return -1
    elif minutes_to_news < 60:
        return -0.5
    return 0

# =========================
# SCORE FINAL
# =========================
def advanced_forex_score(data):
    ema_t = ema_trend(data["ema_short"], data["ema_long"])
    ema_s = ema_slope(data["ema_short"], data["ema_short_prev"])

    rsi = rsi_score(data["rsi"])
    candle = candle_strength(
        data["open"], data["close"], data["high"], data["low"]
    )

    bb = bollinger_position(
        data["price"], data["bb_lower"], data["bb_upper"]
    )
    dist_ema = distance_from_ema(data["price"], data["ema_short"])

    atr = atr_volatility(data["atr"], data["price"])

    session = session_score(data["session"])
    news = news_risk(data["minutes_to_news"])

    weights = {
        "ema_t": 25,
        "ema_s": 15,
        "rsi": 15,
        "candle": 10,
        "bb": 15,
        "dist_ema": 5,
        "atr": 5,
        "session": 5,
        "news": 5
    }

    score = 50 + (
        ema_t * weights["ema_t"] +
        ema_s * weights["ema_s"] +
        rsi * weights["rsi"] +
        candle * weights["candle"] +
        bb * weights["bb"] +
        dist_ema * weights["dist_ema"] +
        atr * weights["atr"] +
        session * weights["session"] +
        news * weights["news"]
    )

    score = max(0, min(100, score))

    if score > 70:
        direction = "BUY"
    elif score < 30:
        direction = "SELL"
    else:
        direction = "WAIT"

    return {
        "score": round(score, 2),
        "direction": direction
    }
```

