# 📈 Forex Advisor - Decision Support System (DSS)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Fase%201%20Estável-green)

## 📌 Sobre o Projeto

O **Forex Advisor DSS** é um sistema de suporte à decisão construído em Python, focado no mercado de câmbio (Forex). Ele atua como um conselheiro inteligente, processando indicadores técnicos e sugerindo direções de trade com base em confluências matemáticas.

O sistema é **Agnóstico de Plataforma**, rodando nativamente no macOS, Linux e Windows.

## 🚀 Funcionalidades Atuais (Fase 1)

- **Coleta de Dados:** Integração com `yfinance` para extração de dados OHLCV (velas de 15m).
- **Motor Técnico:** Cálculo de RSI, EMAs e Bandas de Bollinger via `pandas-ta-openbb`.
- **Motor de Confluência:** Geração automática de sinais (Compra/Venda/Esperar) com sugestão de Stop Loss e Take Profit.
- **Contexto de Sessão:** Identificação das sessões globais (Ásia, Londres, NY) e rompimento de range asiático.
- **Interface CLI:** Dashboard em tempo real com "Radar de Preço" e relatórios detalhados.
- **Visualização:** Geração automática de gráficos de análise técnica em formato `.png`.

## 📂 Estrutura do Projeto

```text
Forex_DSS/
├── app/                  # Orquestração do Bot e lógica de interface
├── analysis/             # Motores matemáticos (Técnico e Gráfico)
├── data_feeds/           # Conectores de APIs de preço (Yahoo Finance)
├── strategy/             # Lógica de sinais e gestão de risco
├── shared/               # Configurações globais e infraestrutura
├── tests/                # Suíte de testes unitários
├── main.py               # Ponto de entrada (Dashboard CLI)
├── requirements.txt      # Dependências corrigidas
└── REVISAO.MD            # Auditoria técnica completa
```

## 🛠️ Instalação e Uso

1. **Requisitos:** Python 3.9+ e ambiente virtual recomendado.
2. **Instalação:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Execução:**
   ```bash
   python main.py
   ```

> **Nota Técnica:** O projeto utiliza o fork `pandas-ta-openbb` para garantir estabilidade e compatibilidade com versões modernas do Python e ARM64 (Mac M1/M2/M3).

## 👨‍💻 Autor
**Bruno Garcia**
*Software desenvolvido para análise quantitativa e suporte à decisão no mercado Forex.*

---
**⚠️ Aviso Legal:** *Este software é um projeto educacional. O mercado Forex envolve alto risco. O autor não se responsabiliza por perdas financeiras.*
