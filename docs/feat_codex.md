# Melhorias propostas para analise tecnica e candlestick

Este documento registra sugestoes para evoluir a leitura tecnica do Forex DSS com foco em candlestick, qualidade de dados e sinais mais confiaveis. As sugestoes abaixo consideram o estado atual do projeto, principalmente:

- `data_feeds/price_api.py`: coleta OHLCV via TwelveData, com fallback para yfinance.
- `analysis/technical.py`: RSI 14, EMA 20, EMA 200, Bollinger Bands 20/2 e ATR 14.
- `strategy/percentual_indicator.py`: score percentual por tendencia, RSI, candle, Bollinger, ATR, sessao e noticia.
- `strategy/signal_generator.py`: modo Sniper e modo Tendencia usando confluencia.
- `app/forex_bot.py`: radar multi-par, contexto de sessao, range asiatico e calendario fundamental.

Aviso: as ideias abaixo melhoram o suporte a decisao, mas nao transformam o sistema em garantia de lucro. Cada mudanca deve ser validada por backtest, forward test e controle de risco.

## Diagnostico do estado atual

O projeto ja tem uma base boa para um DSS tecnico: busca candles, calcula indicadores principais, gera grafico e transforma confluencias em score. O ponto mais fraco hoje e que a decisao depende muito da ultima vela e de regras fixas. Isso cria alguns riscos:

- A ultima vela pode ainda estar aberta, gerando falso sinal antes do fechamento do candle.
- O padrao de candlestick e avaliado de forma simplificada por `candle_strength`, sem classificar pavios, rejeicoes, engolfos, dojis ou contexto.
- O score usa pesos manuais, ainda sem calibracao por par, timeframe ou regime de mercado.
- Os dados de volume em Forex via APIs publicas podem ser ausentes, inconsistentes ou pouco representativos.
- A estrategia usa M15 como base principal, sem confirmacao forte em timeframes maiores.
- Stop Loss e Take Profit usam ATR fixo, mas nao consideram estrutura do candle, swing high/low, spread ou zonas de liquidez.

## Prioridade 1: melhorar a qualidade dos dados

Antes de sofisticar o indicador, e importante garantir que a entrada OHLC esteja correta. Sinais bons em dados ruins continuam sendo sinais ruins.

### 1. Usar apenas candle fechado

No radar e no relatorio, remover ou ignorar a vela atual se ela ainda nao fechou no timeframe analisado. Para M15, por exemplo, se agora sao 10:07 UTC, a vela de 10:00 ainda esta em formacao e deve ser tratada como candle parcial.

Implementacao sugerida:

- Criar um helper em `data_feeds/price_api.py` ou `shared/utils.py`, por exemplo `filtrar_candles_fechados(df, intervalo)`.
- Para M15, manter apenas candles cujo timestamp seja anterior ao inicio do candle atual.
- Exibir no relatorio se a analise foi feita sobre vela fechada ou vela em tempo real.

Impacto esperado: reduz falso rompimento, falso engolfo e falsas leituras de RSI/Bollinger antes do fechamento.

### 2. Validar OHLC antes dos indicadores

Adicionar uma etapa de saneamento dos dados:

- `High >= max(Open, Close)`
- `Low <= min(Open, Close)`
- `High >= Low`
- timestamps sem duplicidade
- indice ordenado em ordem crescente
- ausencia de buracos relevantes no historico
- conversao de timezone consistente para UTC

Implementacao sugerida:

- Criar `PriceDataFeed.validar_ohlc(df, intervalo)`.
- Registrar warnings no log quando houver gaps, duplicatas ou candles invalidos.
- Se houver candle invalido, descartar ou corrigir somente quando a correcao for deterministica.

### 3. Comparar provedores quando possivel

Hoje TwelveData e prioridade e yfinance e fallback. Para pares importantes, vale criar um modo de validacao:

- Buscar o ultimo candle em TwelveData e yfinance.
- Comparar diferenca percentual do fechamento.
- Se a diferenca exceder um limite, por exemplo 0,03% em pares principais, marcar o dado como suspeito.

Essa comparacao nao precisa rodar a cada ciclo do radar. Pode rodar em menor frequencia para evitar lentidao e limite de API.

### 4. Tratar spread e bid/ask

O candle OHLC geralmente representa mid ou ultimo preco, mas a execucao real depende de bid/ask e spread. Para sinais mais realistas:

- Guardar spread estimado por par.
- Penalizar sinais quando o spread estiver acima da media.
- Ajustar Stop Loss e Take Profit considerando spread.
- Em pares JPY, respeitar pip size `0.01`; nos demais, `0.0001`.

Se a API atual nao fornecer spread, usar configuracao por par em `pairs.json` como fallback.

## Prioridade 2: criar um motor real de candlestick

O projeto ja mede forca do candle em `PercentualIndicator.candle_strength`, mas isso ainda nao e uma analise de price action. A melhoria mais importante e criar uma camada dedicada, por exemplo `analysis/candlestick.py`.

### 1. Extrair anatomia do candle

Para cada candle, calcular:

- corpo absoluto: `abs(Close - Open)`
- range total: `High - Low`
- pavio superior: `High - max(Open, Close)`
- pavio inferior: `min(Open, Close) - Low`
- direcao: alta, baixa ou neutro
- proporcao corpo/range
- proporcao pavio superior/range
- proporcao pavio inferior/range
- tamanho relativo ao ATR

Essas metricas devem ser numericas e testaveis. Evitar classificar apenas por texto.

### 2. Detectar padroes basicos

Implementar funcoes pequenas e independentes:

- `is_doji(candle)`: corpo muito pequeno em relacao ao range.
- `is_pinbar_bullish(candle)`: pavio inferior dominante, fechamento acima do meio do range.
- `is_pinbar_bearish(candle)`: pavio superior dominante, fechamento abaixo do meio do range.
- `is_engulfing_bullish(prev, curr)`: candle atual de alta engolindo corpo anterior de baixa.
- `is_engulfing_bearish(prev, curr)`: candle atual de baixa engolindo corpo anterior de alta.
- `is_inside_bar(prev, curr)`: high/low dentro do candle anterior.
- `is_breakout_candle(curr, lookback)`: fechamento acima/abaixo de maxima/minima recente.
- `is_rejection(candle, level)`: pavio rejeita suporte/resistencia e fecha de volta para dentro.

Cada padrao deve retornar tambem uma intensidade entre `0.0` e `1.0`, nao apenas `True/False`.

### 3. Exigir contexto para cada padrao

Padrao de candle isolado tem baixa confiabilidade. O mesmo pinbar pode significar reversao, pullback ou ruido. O motor deve avaliar:

- tendencia do timeframe maior
- posicao em relacao a EMA 20/200
- proximidade de suporte/resistencia
- proximidade das Bandas de Bollinger
- volatilidade atual via ATR
- sessao de mercado
- risco de noticia nos proximos minutos

Exemplo de regra melhor que a atual:

- Compra por pinbar bullish somente se:
  - H1 ou H4 estiver em tendencia de alta;
  - M15 fizer pullback para EMA 20, suporte ou banda inferior;
  - candle fechar com pavio inferior dominante;
  - RSI nao estiver em sobrecompra;
  - nao houver noticia critica proxima.

## Prioridade 3: adicionar analise multi-timeframe

O M15 e bom para entrada, mas nao deve carregar sozinho o vies direcional. A sugestao e separar funcao por timeframe:

- D1: direcao macro e zonas maiores.
- H4: tendencia principal e areas de decisao.
- H1: estrutura intraday.
- M15: gatilho de entrada.
- M5 opcional: refinamento de entrada, somente se houver dados confiaveis.

Implementacao sugerida:

- Criar `MultiTimeframeAnalyzer`.
- Buscar historicos separados: `1d`, `4h`, `1h`, `15m`.
- Gerar um resultado padronizado por timeframe:
  - tendencia
  - inclinacao da EMA
  - volatilidade
  - ultimo padrao de candle
  - suporte/resistencia mais proximo
  - score tecnico

Regra pratica:

- Sinal de compra em M15 so deve ter peso maximo se H1/H4 tambem estiverem alinhados.
- Se M15 compra contra H4, classificar como pullback contra tendencia e reduzir lote ou exigir confluencia extra.

## Prioridade 4: detectar suporte, resistencia e liquidez

Candlestick melhora muito quando lido em cima de niveis. Sem nivel, o padrao fica solto.

### 1. Swing highs e swing lows

Adicionar deteccao simples:

- swing high: maxima maior que as `n` velas anteriores e posteriores.
- swing low: minima menor que as `n` velas anteriores e posteriores.

Usar esses pontos para criar zonas de suporte/resistencia com tolerancia baseada em ATR.

### 2. Range asiatico ja existente

O bot ja identifica o range asiatico em `ForexBot.obter_contexto_sessao`. Esse contexto pode virar feature numerica:

- preco acima do topo da Asia: vies comprador.
- preco abaixo do fundo da Asia: vies vendedor.
- preco dentro do range: mercado lateral ou aguardando rompimento.
- falso rompimento do range: possivel reversao se houver candle de rejeicao.

### 3. Zonas ao inves de linhas exatas

Suporte e resistencia devem ser tratados como zonas:

- tolerancia minima: `0.25 * ATR`
- tolerancia maxima: configuravel por par
- se o preco estiver dentro da zona, aumentar peso de rejeicao/pinbar/engolfo

## Prioridade 5: classificar regime de mercado

Nem toda regra funciona em todo mercado. Antes do sinal, classificar o regime:

- Tendencia forte
- Tendencia fraca
- Lateralidade
- Alta volatilidade
- Baixa volatilidade
- Pre-noticia

Indicadores uteis:

- ADX 14 para forca de tendencia.
- Bollinger Band Width para compressao/expansao.
- ATR percentile para volatilidade relativa.
- Distancia entre EMA 20 e EMA 200.
- Sequencia de topos/fundos ascendentes ou descendentes.

Uso no sinal:

- Em tendencia forte, preferir pullbacks e continuacao.
- Em lateralidade, preferir reversoes em extremos do range.
- Em baixa volatilidade, reduzir confianca de rompimentos.
- Em alta volatilidade/noticia, reduzir lote ou bloquear entrada.

## Prioridade 6: melhorar o score percentual

O `PercentualIndicator` ja e uma boa base. A evolucao recomendada e substituir parte dos pesos fixos por componentes mais explicaveis e calibraveis.

### Novos componentes sugeridos

Adicionar ao score:

- `mtf_alignment`: alinhamento M15/H1/H4.
- `candlestick_pattern`: tipo e forca do padrao.
- `level_reaction`: rejeicao em suporte, resistencia, range asiatico ou Bollinger.
- `market_regime`: tendencia, range, compressao ou expansao.
- `data_quality`: penalizacao por candle aberto, gap, dado suspeito ou provedor divergente.
- `spread_penalty`: penalizacao por custo de execucao alto.

### Ajuste de interpretacao

Em vez de apenas:

- `score > 70`: compra
- `score < 30`: venda

Usar classificacao por confianca:

- `80-100`: compra forte, se risco permitido.
- `65-80`: compra moderada, exigir candle fechado e contexto.
- `45-65`: neutro.
- `20-35`: venda moderada.
- `0-20`: venda forte.

Essa abordagem evita tratar 71% como sinal forte demais.

## Prioridade 7: stops e alvos baseados em estrutura

Hoje o `SignalGenerator` usa `ATR * 1.5` para distancia de stop. Isso e simples e util, mas pode ficar artificial.

Melhoria recomendada:

- Para compra por pinbar ou rejeicao: SL abaixo do pavio/swing low + buffer de ATR.
- Para venda por pinbar ou rejeicao: SL acima do pavio/swing high + buffer de ATR.
- Para rompimento: SL dentro do range rompido ou abaixo/acima da vela de rompimento.
- TP1 em 1R, TP2 em 2R ou proxima zona relevante.
- Se o alvo ate a proxima resistencia/suporte for menor que 1.5R, bloquear a entrada.

Isso conecta risco/retorno a estrutura real do grafico.

## Prioridade 8: backtest e calibracao

Antes de usar sinais mais sofisticados no radar, criar uma base minima de validacao.

### Metricas essenciais

- win rate
- payoff medio
- expectancy
- max drawdown
- profit factor
- quantidade de trades
- resultado por par
- resultado por sessao
- resultado por padrao de candle
- resultado por regime de mercado

### Metodo recomendado

- Separar dados por periodo de treino e teste.
- Calibrar pesos no treino.
- Validar em periodo fora da amostra.
- Rodar walk-forward simples.
- Evitar otimizar demais para um unico par ou mes.

Resultado esperado: saber quais padroes realmente ajudam e quais apenas parecem bons visualmente.

## Roadmap de implementacao

### Fase 1: dados confiaveis

1. Criar filtro de candle fechado.
2. Criar validador OHLC.
3. Registrar gaps, duplicatas e candles suspeitos.
4. Adicionar flag de qualidade no DataFrame.
5. Atualizar testes unitarios para dados invalidos e candle aberto.

### Fase 2: motor candlestick

1. Criar `analysis/candlestick.py`.
2. Implementar anatomia do candle.
3. Implementar doji, pinbar, engulfing, inside bar e breakout candle.
4. Retornar padroes com intensidade numerica.
5. Adicionar testes unitarios com candles sinteticos.

### Fase 3: niveis e contexto

1. Criar deteccao de swing high/low.
2. Criar zonas de suporte/resistencia por ATR.
3. Converter range asiatico em feature numerica.
4. Detectar rejeicao em zona.
5. Integrar contexto ao `PercentualIndicator`.

### Fase 4: multi-timeframe

1. Criar `analysis/multi_timeframe.py`.
2. Buscar M15, H1 e H4.
3. Calcular tendencia e score por timeframe.
4. Criar `mtf_alignment`.
5. Fazer o `SignalGenerator` exigir alinhamento ou classificar sinal contra tendencia.

### Fase 5: backtest

1. Criar `backtesting/` com simulador simples por candle fechado.
2. Salvar trades em CSV.
3. Gerar metricas por par, sessao, padrao e regime.
4. Ajustar thresholds com base nas metricas.
5. Documentar os resultados antes de ligar no radar principal.

## Mudancas de codigo recomendadas

Arquivos novos:

- `analysis/candlestick.py`
- `analysis/levels.py`
- `analysis/market_regime.py`
- `analysis/multi_timeframe.py`
- `backtesting/simple_backtester.py`
- `tests/test_candlestick.py`
- `tests/test_levels.py`
- `tests/test_market_regime.py`

Arquivos a evoluir:

- `data_feeds/price_api.py`: filtro de candle fechado, validacao OHLC, qualidade de dados.
- `analysis/technical.py`: adicionar ADX, Bollinger Band Width e ATR percentile.
- `strategy/percentual_indicator.py`: incluir padroes, niveis, regime e multi-timeframe.
- `strategy/signal_generator.py`: stops por estrutura e classificacao de confianca.
- `app/forex_bot.py`: mostrar no relatorio o padrao detectado, timeframe dominante, nivel mais proximo e qualidade dos dados.
- `analysis/charting.py`: desenhar zonas, swings, padroes e SL/TP no grafico.

## Exemplo de saida desejada no relatorio

```text
LEITURA CANDLESTICK
Timeframe de entrada : M15
Candle analisado     : fechado
Padrao principal     : Pinbar bullish (forca 0.82)
Contexto             : pullback em tendencia de alta H1/H4
Nivel relevante      : suporte M15 em 1.08420 (+0.18 ATR)
Regime               : tendencia moderada, volatilidade normal
Qualidade dos dados  : OK

SINAL
Direcao              : compra moderada
Confianca            : 76%
Motivo               : alinhamento MTF + rejeicao em suporte + RSI saudavel
Invalidacao          : fechamento abaixo do pavio/suporte
SL sugerido          : abaixo do swing low + buffer ATR
TP sugerido          : proxima resistencia ou 2R
```

## Ordem de impacto esperado

1. Candle fechado e validacao OHLC: maior ganho imediato de precisao operacional.
2. Candlestick com anatomia e contexto: melhora a qualidade do gatilho.
3. Multi-timeframe: reduz sinais contra a direcao dominante.
4. Suporte/resistencia por zonas: melhora SL, TP e filtros de entrada.
5. Regime de mercado: evita aplicar estrategia errada no ambiente errado.
6. Backtest e calibracao: transforma opiniao em evidencia.

## Conclusao

A melhor evolucao para o projeto nao e adicionar muitos indicadores, e sim melhorar a leitura de contexto. A prioridade deve ser: dados limpos, vela fechada, padrao de candle quantificado, nivel relevante, alinhamento multi-timeframe e validacao por backtest. Com isso, o Forex DSS passa de uma leitura tecnica baseada em regras fixas para um motor de confluencia mais robusto, explicavel e mensuravel.
