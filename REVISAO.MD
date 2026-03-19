# 📋 Relatório de Revisão Técnica - Forex Advisor DSS

**Data:** 18 de Março de 2026  
**Analista:** Software Engineer (Gemini CLI)  
**Status do Projeto:** 🟠 Em Desenvolvimento (Fase 1/2)

---

## 1. Análise de Consistência e Estrutura

### 📂 Discrepâncias de Arquivos
- **Erro de Nomeclatura:** O arquivo `shared/database_interface.py.py` possui extensão dupla. Deve ser renomeado para `database_interface.py`.
- **Arquivos Órfãos/Vazios:** `shared/constants.py`, `shared/logger.py`, `shared/models.py` e `shared/utils.py` estão presentes no sistema de arquivos, mas totalmente vazios (0 bytes). Isso indica uma estrutura planejada mas não implementada, ou resquícios de refatoração.
- **Divergência com README:** 
    - O `README.md` aponta `main_advisor.py` como o ponto de entrada, mas o arquivo real é `main.py`.
    - O `README.md` menciona um diretório `data/`, que não existe no repositório (embora seja criado dinamicamente pelo `config.py`).
- **Ausência de `.gitignore`:** O projeto não possui um arquivo `.gitignore`, o que é crítico para evitar o versionamento de `__pycache__`, arquivos de log, bancos de dados SQLite locais e o arquivo sensível `.env`.

### ⚙️ Configuração (`shared/config.py`)
- **Conflito de Arquitetura:** O `README.md` afirma que o sistema é "Agnóstico de Plataforma" e usa `yfinance`, mas o `config.py` contém configurações específicas para **MetaTrader 5 (MT5)** (`MT5_LOGIN`, `MT5_SERVER`). Isso sugere uma inconsistência no design ou uma mudança de direção não totalmente limpa no código.
- **Dependência Omitida:** O código utiliza `dotenv`, mas a biblioteca `python-dotenv` não está listada no `requirements.txt`.

---

## 2. Falhas Técnicas e Riscos de Implementação

### 🔴 Tratamento de Erros (Silent Failures)
No método `ForexBot.atualizar_radar`, existe um bloco `except: pass`. Isso é extremamente perigoso, pois mascara falhas de conexão, limites de taxa (rate limiting) da API do Yahoo Finance ou erros de parsing, dificultando o debugging em tempo real.

### 🧵 Portabilidade e Concorrência
O `main.py` utiliza `select.select([sys.stdin], ...)` para capturar comandos do teclado. 
- **Limitação:** Embora funcione em macOS/Linux, este método não é portável para Windows (onde `select` não funciona em arquivos/stdin).
- **UX:** O loop de 1 segundo para o radar pode causar uma percepção de "lag" na resposta aos comandos do usuário.

### 📉 Eficiência de Dados (`data_feeds/price_api.py`)
O método `obter_cotacao_atual` baixa um histórico de 1 dia com intervalo de 1 minuto apenas para extrair o último preço. 
- **Impacto:** Isso consome mais banda e processamento do que o necessário. O `yfinance` possui formas mais leves de obter o "last price" ou pode-se reutilizar o último dataframe baixado pelo radar.

---

## 3. Lógica de Domínio (Forex & Trading)

### 🌍 Gestão de Sessões (Hardcoded UTC)
O método `obter_contexto_sessao` usa horas UTC fixas (ex: 08:00 para Londres).
- **Problema:** O mercado Forex é sensível ao **Horário de Verão (DST)**. Quando Londres ou Nova York mudam seu relógio, a abertura em relação ao UTC muda. Hardcodar esses valores causará análises de contexto erradas em metade do ano.

### 📏 Cálculos de Risco Fixos
Os valores de Stop Loss e Take Profit em `signal_generator.py` estão fixos em pips (0.0015).
- **Inconsistência:** Isso não leva em conta a volatilidade atual do par (ATR) nem a diferença de escala entre pares (ex: EUR/USD vs USD/JPY, onde 0.0015 tem significados completamente diferentes).

---

## 4. Sugestões de Melhoria e Roadmap

### ✅ Ações Imediatas (Quick Wins)
1. **Saneamento:** Renomear `database_interface.py.py` e remover arquivos vazios ou adicionar `__init__.py` para torná-los pacotes válidos.
2. **Documentação:** Corrigir as referências no `README.md` para `main.py`.
3. **Segurança:** Criar um `.gitignore` robusto.
4. **Dependências:** Atualizar `requirements.txt` com `python-dotenv`.

### 🛠️ Refatoração Recomendada
1. **Logger Centralizado:** Implementar o `shared/logger.py` para substituir os `print()` espalhados pelo código, permitindo auditoria posterior.
2. **Abstração de API:** Criar uma interface para o `PriceDataFeed` que permita trocar `yfinance` por outras fontes (Alpha Vantage, Oanda) sem alterar o `ForexBot`.
3. **Validação de Sinais:** Adicionar testes unitários para o `TechnicalAnalyzer` e `SignalGenerator` usando dados sintéticos para garantir que os sinais de Compra/Venda são gerados corretamente sob as condições definidas.

### 🚀 Evolução Sugerida
- **Suporte a Múltiplos Pares:** Atualmente o `main.py` está travado no "EURUSD". Evoluir para um arquivo de configuração ou argumento de linha de comando para monitorar múltiplos pares simultaneamente.
- **Cálculo Dinâmico de Sessões:** Utilizar a biblioteca `pytz` ou `zoneinfo` para calcular as aberturas de mercado dinamicamente com base nas zonas de tempo de Londres (Europe/London) e NY (America/New_York).

---
**Conclusão:** O projeto possui uma base sólida e modular, mas carece de polimento em termos de "production-readiness" e precisão nos conceitos de mercado financeiro.
