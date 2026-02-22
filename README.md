cat << 'EOF' > README.md
# 📈 Forex Advisor - Decision Support System (DSS)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange)

## 📌 Sobre o Projeto

O **Forex Advisor DSS** é um sistema de suporte à decisão construído em Python, focado no mercado de câmbio (Forex). Diferente de um robô de execução automática (Expert Advisor), este sistema atua como um conselheiro inteligente. Ele coleta dados de mercado em tempo real, processa a pesada carga matemática de indicadores técnicos e avalia o sentimento fundamentalista, entregando um painel limpo no terminal com uma **sugestão de direção e um percentual de convicção**.

O foco principal da arquitetura é ser **Agnóstico de Plataforma**, rodando nativamente no macOS e Linux, dispensando a necessidade de terminais locais (como o MetaTrader 5) ou máquinas virtuais Windows.

## 🚀 Funcionalidades

- **Coleta de Dados Independente:** Utiliza APIs públicas (`yfinance`) para obter dados OHLCV (Velas) sem depender de corretoras específicas.
- **Motor Técnico (Fase 1):** Calcula automaticamente indicadores chave (RSI, MACD, EMAs) usando a biblioteca `pandas_ta`.
- **Motor Fundamentalista (Fase 2):** Processa dados de calendários econômicos e impacto de notícias para gerar um score de sentimento.
- **Motor de Confluência:** Pondera as análises técnicas e fundamentalistas para gerar um "Grau de Convicção" (ex: 82% de chance de Alta).
- **Interface CLI Limpa:** Exibe um painel de fácil leitura diretamente no terminal do usuário.

## 📂 Estrutura da Arquitetura

O projeto utiliza uma arquitetura modular e desacoplada:

ForexAdvisor_DSS/
├── shared/               # Configurações globais, sistema de logs e constantes
├── data_feeds/           # Conectores de APIs (Yahoo Finance, Calendário Econômico)
├── analysis/             # Lógica matemática (Cálculo de indicadores e sentimento)
├── strategy/             # Motor de confluência (Geração de sinais e scores)
├── data/                 # Armazenamento de logs e bancos de dados SQLite locais
├── .env                  # Variáveis de ambiente e chaves de API (Não versionado)
├── requirements.txt      # Dependências do projeto
└── main_advisor.py       # Arquivo de execução principal (Terminal Dashboard)

## 🛠️ Instalação e Configuração

### Pré-requisitos
- **Python 3.10** ou superior.
- Git.

### Passo a Passo

1. **Clone o repositório:**
   git clone https://github.com/seu-usuario/forex-advisor-dss.git
   cd forex-advisor-dss

2. **Crie um ambiente virtual (Recomendado):**
   python -m venv venv
   source venv/bin/activate

3. **Instale as dependências:**
   pip install -r requirements.txt

4. **Configure as Variáveis de Ambiente:**
   Crie um arquivo chamado `.env` na raiz do projeto contendo suas configurações.

## 💻 Como Usar

Para iniciar o painel de análise no seu terminal, basta executar o orquestrador principal:

python main_advisor.py

O sistema fará o download das últimas cotações, processará os motores de análise e exibirá o painel atualizado no seu terminal.

## 👨‍💻 Autor

**Bruno Garcia**
- Projeto desenvolvido para auxiliar na tomada de decisão quantitativa e qualitativa no mercado de moedas.

---
**⚠️ Aviso Legal:** *Este software é um projeto educacional e de pesquisa quantitativa. Ele fornece análises baseadas em dados históricos e probabilidade estatística, o que não constitui aconselhamento financeiro. O mercado Forex envolve alto risco. O autor não se responsabiliza por perdas financeiras decorrentes do uso desta ferramenta.*
EOF
