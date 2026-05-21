# Plano de implementacao: melhoria da analise tecnica e candlestick

Este plano transforma as propostas de `docs/feat_codex.md` em uma sequencia pratica de implementacao para o Forex DSS. O foco e aumentar a confiabilidade dos sinais por meio de:

- dados OHLC mais limpos;
- uso de candle fechado;
- motor dedicado de candlestick;
- niveis de suporte/resistencia;
- classificacao de regime de mercado;
- analise multi-timeframe;
- score percentual mais explicavel;
- stops e alvos baseados em estrutura;
- testes automatizados para reduzir regressao.

## Principios de implementacao

1. Fazer mudancas pequenas e testaveis.
2. Preservar o fluxo atual do bot enquanto as novas camadas amadurecem.
3. Nao trocar a estrategia inteira de uma vez; primeiro adicionar features, depois integrar ao score.
4. Toda funcao de analise deve retornar dados estruturados, nao apenas texto.
5. Toda regra nova deve ter pelo menos um teste unitario com dados sinteticos.
6. Sinais devem ser calculados somente com candles fechados, salvo modo explicitamente marcado como tempo real.
7. O radar deve continuar funcionando mesmo se uma camada nova falhar; nesses casos, registrar log e degradar para a logica atual.

## Visao geral das fases

| Fase | Objetivo | Arquivos principais | Resultado esperado |
|---|---|---|---|
| 0 | Preparar contratos e dados sinteticos de teste | `tests/fixtures` ou helpers nos testes | Base previsivel para testar candle, niveis e score |
| 1 | Qualidade de dados e candle fechado | `data_feeds/price_api.py`, `shared/utils.py` | Indicadores calculados sobre candles validos |
| 2 | Motor de candlestick | `analysis/candlestick.py` | Padroes numericos e testaveis |
| 3 | Niveis e estrutura de preco | `analysis/levels.py` | Suportes/resistencias por zonas |
| 4 | Regime de mercado | `analysis/market_regime.py`, `analysis/technical.py` | Tendencia/range/volatilidade classificados |
| 5 | Multi-timeframe | `analysis/multi_timeframe.py` | Vies M15/H1/H4 padronizado |
| 6 | Score e sinais | `strategy/percentual_indicator.py`, `strategy/signal_generator.py` | Score com contexto e sinal por confianca |
| 7 | Relatorio e grafico | `app/forex_bot.py`, `analysis/charting.py` | Saida explicavel para operador |
| 8 | Backtest minimo | `backtesting/simple_backtester.py` | Medicao inicial de qualidade das regras |

## Fase 0: base de testes e contratos

### Objetivo

Criar uma base comum para testar regras de candles, niveis, regime e score sem depender de API externa.

### Tarefas

1. Criar helpers de DataFrame sintetico nos testes.
2. Padronizar nomes de colunas: `Open`, `High`, `Low`, `Close`, `Volume`.
3. Criar candles de exemplo para:
   - tendencia de alta;
   - tendencia de baixa;
   - mercado lateral;
   - pinbar bullish;
   - pinbar bearish;
   - engulfing bullish;
   - engulfing bearish;
   - inside bar;
   - breakout;
   - candle invalido;
   - candle aberto/parcial.

### Estrutura sugerida

Opcoes:

- manter helpers dentro de cada arquivo de teste para simplicidade inicial;
- ou criar `tests/helpers.py` se os helpers forem repetidos.

Exemplo de helper:

```python
def make_ohlc(rows, start="2026-01-01 00:00:00", freq="15min"):
    index = pd.date_range(start=start, periods=len(rows), freq=freq, tz="UTC")
    return pd.DataFrame(rows, index=index)
```

### Testes

Arquivo sugerido: `tests/test_test_helpers.py` ou validacao indireta nos demais testes.

Casos:

1. `make_ohlc` cria DataFrame com indice UTC.
2. `make_ohlc` preserva colunas OHLCV.
3. Dados sinteticos sao ordenados cronologicamente.

### Criterio de aceite

Todos os testes novos conseguem construir DataFrames previsiveis sem internet e sem depender de horario real, exceto onde o horario for injetado como parametro.

## Fase 1: qualidade de dados e candle fechado

### Objetivo

Garantir que os indicadores e sinais sejam calculados sobre dados consistentes e sobre a ultima vela fechada.

### Arquivos

- Criar ou evoluir: `shared/utils.py`
- Evoluir: `data_feeds/price_api.py`
- Evoluir: `app/forex_bot.py`
- Criar: `tests/test_price_data_quality.py`

### Funcoes sugeridas

#### `parse_interval_to_timedelta(intervalo: str) -> pd.Timedelta`

Aceitar formatos usados pelo projeto:

- `1m`
- `5m`
- `15m`
- `1h`
- `4h`
- `1d`

Retornar `pd.Timedelta`.

#### `filtrar_candles_fechados(df, intervalo, agora=None) -> pd.DataFrame`

Contrato:

- `agora` deve ser injetavel para testes.
- Se `agora=None`, usar `pd.Timestamp.now(tz="UTC")`.
- Remover candles cujo inicio seja maior ou igual ao inicio do candle atual.
- Preservar timezone UTC.
- Nao modificar o DataFrame original.

Exemplo M15:

- `agora=10:07`
- candle `10:00` esta aberto e deve sair;
- ultimo candle valido e `09:45`.

#### `validar_ohlc(df, intervalo=None) -> dict`

Contrato:

Retornar um dicionario:

```python
{
    "is_valid": bool,
    "issues": list[str],
    "rows": int,
    "duplicate_timestamps": int,
    "invalid_ohlc_rows": int,
    "gap_count": int,
}
```

Checagens:

- colunas obrigatorias existem;
- indice e `DatetimeIndex`;
- indice ordenado;
- duplicatas;
- `High >= Open`;
- `High >= Close`;
- `Low <= Open`;
- `Low <= Close`;
- `High >= Low`;
- gaps quando `intervalo` for informado.

#### `normalizar_ohlc(df) -> pd.DataFrame`

Contrato:

- ordenar indice;
- remover duplicatas mantendo ultimo candle;
- converter timezone para UTC;
- opcionalmente remover linhas com OHLC invalido;
- nao preencher candles ausentes automaticamente na primeira versao.

### Integracao no fluxo

1. `PriceDataFeed.obter_historico_velas` continua buscando dados.
2. Depois da busca:
   - normalizar indice;
   - validar OHLC;
   - filtrar candle fechado por padrao.
3. `ForexBot.exibir_relatorio_completo` deve exibir:
   - `Candle analisado: fechado`;
   - quantidade de issues de qualidade, se houver.
4. `ForexBot.atualizar_radar` deve usar a mesma base filtrada.

### Testes unitarios

Arquivo: `tests/test_price_data_quality.py`

Casos recomendados:

1. `test_parse_interval_to_timedelta_15m`
   - entrada `15m`;
   - saida `pd.Timedelta(minutes=15)`.

2. `test_filtrar_candles_fechados_remove_candle_aberto_m15`
   - DataFrame com candles `09:30`, `09:45`, `10:00`;
   - `agora=10:07 UTC`;
   - resultado deve terminar em `09:45`.

3. `test_filtrar_candles_fechados_mantem_candle_fechado_exato`
   - DataFrame com `09:45`;
   - `agora=10:00 UTC`;
   - `09:45` permanece, `10:00` sai se existir.

4. `test_validar_ohlc_detecta_high_menor_que_close`
   - candle com `Close > High`;
   - `is_valid=False`;
   - `invalid_ohlc_rows=1`.

5. `test_validar_ohlc_detecta_low_maior_que_open`
   - candle com `Low > Open`;
   - invalido.

6. `test_validar_ohlc_detecta_duplicatas`
   - dois candles com mesmo timestamp;
   - `duplicate_timestamps=1`.

7. `test_validar_ohlc_detecta_gap_m15`
   - candles `09:00`, `09:15`, `09:45`;
   - gap esperado em `09:30`;
   - `gap_count=1`.

8. `test_normalizar_ohlc_nao_muta_dataframe_original`
   - chamar normalizacao;
   - confirmar que objeto original preserva ordem/duplicatas.

### Criterio de aceite

- Nenhum calculo tecnico deve usar candle aberto por padrao.
- Dados invalidos devem ser detectados antes do `TechnicalAnalyzer`.
- Testes da fase 1 devem passar sem rede.

## Fase 2: motor de candlestick

### Objetivo

Criar uma camada propria de price action que extraia anatomia do candle e detecte padroes com intensidade numerica.

### Arquivos

- Criar: `analysis/candlestick.py`
- Criar: `tests/test_candlestick.py`
- Integrar depois em: `strategy/percentual_indicator.py`

### Modelos sugeridos

Usar `dataclass` para clareza:

```python
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
    direction: str
    body_ratio: float
    upper_wick_ratio: float
    lower_wick_ratio: float
    close_position: float
```

```python
@dataclass(frozen=True)
class CandlePattern:
    name: str
    direction: str
    strength: float
    reason: str
```

Direcoes sugeridas:

- `bullish`
- `bearish`
- `neutral`

### Funcoes sugeridas

#### `analyze_candle(row) -> CandleAnatomy`

Calcular:

- corpo;
- range;
- pavio superior;
- pavio inferior;
- direcao;
- proporcoes;
- posicao do fechamento dentro do range.

#### `detect_doji(candle, max_body_ratio=0.1) -> CandlePattern | None`

Doji quando:

- `body_ratio <= 0.1`;
- range maior que zero.

Forca:

- maior quando corpo for menor.

#### `detect_pinbar_bullish(candle) -> CandlePattern | None`

Condicoes iniciais:

- pavio inferior >= 2x corpo;
- pavio inferior >= 50% do range;
- fechamento acima do meio do candle;
- pavio superior nao dominante.

Forca:

- baseada em `lower_wick_ratio` e `close_position`.

#### `detect_pinbar_bearish(candle) -> CandlePattern | None`

Condicoes espelhadas:

- pavio superior >= 2x corpo;
- pavio superior >= 50% do range;
- fechamento abaixo do meio do candle.

#### `detect_engulfing_bullish(prev, curr) -> CandlePattern | None`

Condicoes:

- candle anterior bearish;
- candle atual bullish;
- corpo atual cobre o corpo anterior;
- opcional: corpo atual maior que media recente.

#### `detect_engulfing_bearish(prev, curr) -> CandlePattern | None`

Espelho do bullish.

#### `detect_inside_bar(prev, curr) -> CandlePattern | None`

Condicoes:

- `curr.High <= prev.High`;
- `curr.Low >= prev.Low`.

Direcao pode ser `neutral`, ou herdada do rompimento em etapa posterior.

#### `detect_breakout(df, lookback=20) -> CandlePattern | None`

Condicoes:

- fechamento acima da maxima dos `lookback` candles anteriores;
- ou fechamento abaixo da minima dos `lookback` candles anteriores.

Forca:

- distancia do fechamento ate o nivel rompido em multiplos de ATR, se disponivel;
- corpo/range do candle de rompimento.

#### `detect_patterns(df) -> list[CandlePattern]`

Retornar padroes do ultimo candle fechado, avaliando tambem o candle anterior quando necessario.

### Integracao inicial

Na primeira entrega, apenas criar o modulo e testes. Nao alterar o sinal final ainda. Depois integrar ao score na Fase 6.

### Testes unitarios

Arquivo: `tests/test_candlestick.py`

Casos recomendados:

1. `test_analyze_candle_bullish_anatomy`
   - candle `Open=1.1000`, `High=1.1050`, `Low=1.0980`, `Close=1.1040`;
   - direcao `bullish`;
   - corpo `0.0040`;
   - pavio superior `0.0010`;
   - pavio inferior `0.0020`.

2. `test_analyze_candle_bearish_anatomy`
   - validar direcao e proporcoes.

3. `test_detect_doji_returns_neutral_pattern`
   - corpo pequeno;
   - `name="doji"`;
   - `direction="neutral"`.

4. `test_detect_pinbar_bullish`
   - pavio inferior dominante;
   - fechamento acima de 50% do range;
   - strength entre `0.0` e `1.0`.

5. `test_detect_pinbar_bearish`
   - pavio superior dominante.

6. `test_pinbar_bullish_rejects_large_upper_wick`
   - candle com pavios iguais nao deve ser bullish pinbar.

7. `test_detect_engulfing_bullish`
   - candle atual engole corpo anterior bearish.

8. `test_detect_engulfing_bearish`
   - inverso.

9. `test_detect_inside_bar`
   - high/low dentro do candle anterior.

10. `test_detect_breakout_bullish`
    - fechamento acima da maxima dos 20 candles anteriores.

11. `test_detect_breakout_bearish`
    - fechamento abaixo da minima dos 20 candles anteriores.

12. `test_detect_patterns_returns_sorted_by_strength`
    - quando houver mais de um padrao, o mais forte vem primeiro.

13. `test_zero_range_candle_does_not_crash`
    - `High == Low`;
    - nao deve dividir por zero.

### Criterio de aceite

- O motor de candlestick nao depende de indicadores externos.
- Todas as funcoes sao deterministicas.
- Padroes retornam `strength` normalizado entre `0.0` e `1.0`.

## Fase 3: suporte, resistencia e liquidez

### Objetivo

Contextualizar padroes de candle em niveis relevantes, evitando sinais soltos no meio do grafico.

### Arquivos

- Criar: `analysis/levels.py`
- Criar: `tests/test_levels.py`
- Evoluir depois: `analysis/charting.py`

### Modelos sugeridos

```python
@dataclass(frozen=True)
class PriceLevel:
    kind: str
    price: float
    lower: float
    upper: float
    touches: int
    strength: float
    source: str
```

`kind`:

- `support`
- `resistance`
- `range_high`
- `range_low`

### Funcoes sugeridas

#### `find_swings(df, left=2, right=2) -> pd.DataFrame`

Adicionar colunas:

- `swing_high: bool`
- `swing_low: bool`

#### `build_levels(df, atr_col="ATRr_14", tolerance_atr=0.25) -> list[PriceLevel]`

Criar zonas a partir de swings proximos:

- agrupar swings que estejam dentro da tolerancia;
- contar toques;
- calcular forca por numero de toques e recencia.

#### `nearest_level(price, levels) -> PriceLevel | None`

Retornar nivel mais proximo do preco atual.

#### `is_price_in_zone(price, level) -> bool`

Checar se o preco esta entre `level.lower` e `level.upper`.

#### `detect_level_rejection(candle, level) -> dict`

Retornar:

```python
{
    "rejected": bool,
    "direction": "bullish" | "bearish" | "neutral",
    "strength": float,
    "level": PriceLevel,
}
```

Regras iniciais:

- suporte: pavio inferior toca/entra na zona e fechamento volta acima da zona;
- resistencia: pavio superior toca/entra na zona e fechamento volta abaixo da zona.

### Range asiatico

Extrair a logica existente de `ForexBot.obter_contexto_sessao` para uma funcao reaproveitavel:

#### `calculate_asian_range(df, date_utc=None) -> dict`

Retornar:

```python
{
    "high": float,
    "low": float,
    "mid": float,
    "has_range": bool,
}
```

#### `classify_price_vs_asian_range(price, asian_range) -> str`

Retornos:

- `above_range`
- `below_range`
- `inside_range`
- `no_range`

### Testes unitarios

Arquivo: `tests/test_levels.py`

Casos recomendados:

1. `test_find_swings_marks_swing_high`
   - serie com maxima isolada;
   - marcar somente o ponto correto.

2. `test_find_swings_marks_swing_low`
   - serie com minima isolada.

3. `test_build_levels_groups_nearby_swings`
   - dois swings proximos;
   - gerar uma zona com `touches=2`.

4. `test_nearest_level_returns_closest_zone`
   - preco atual entre dois niveis;
   - retornar o mais proximo.

5. `test_is_price_in_zone_true`
   - preco dentro de `lower/upper`.

6. `test_is_price_in_zone_false`
   - preco fora.

7. `test_detect_support_rejection_bullish`
   - candle com pavio inferior atravessando suporte e fechamento acima.

8. `test_detect_resistance_rejection_bearish`
   - candle com pavio superior atravessando resistencia e fechamento abaixo.

9. `test_calculate_asian_range_uses_utc_00_to_08`
   - DataFrame com horas UTC;
   - high/low devem vir apenas da janela asiatica.

10. `test_classify_price_vs_asian_range_above_below_inside`
    - validar os tres retornos principais.

### Criterio de aceite

- O sistema consegue dizer se o ultimo candle reagiu em zona relevante.
- Zonas sao calculadas por ATR/tolerancia, nao por linha exata.

## Fase 4: regime de mercado

### Objetivo

Identificar se o mercado favorece continuacao, reversao em range ou nenhuma entrada.

### Arquivos

- Criar: `analysis/market_regime.py`
- Evoluir: `analysis/technical.py`
- Criar: `tests/test_market_regime.py`

### Indicadores tecnicos adicionais

Em `TechnicalAnalyzer.calcular_indicadores`, adicionar:

- ADX 14;
- Bollinger Band Width;
- ATR percentile ou ATR relativo;
- opcional: EMA 50 para uma camada intermediaria.

Observacao: validar nomes dinamicos de colunas do `pandas_ta`, como ja e feito com Bollinger.

### Modelo sugerido

```python
@dataclass(frozen=True)
class MarketRegime:
    label: str
    trend_direction: str
    trend_strength: float
    volatility_label: str
    volatility_score: float
    reason: str
```

Labels:

- `strong_trend`
- `weak_trend`
- `range`
- `compression`
- `high_volatility`
- `pre_news`

### Funcoes sugeridas

#### `classify_trend(row) -> tuple[str, float]`

Usar:

- EMA 20 vs EMA 200;
- slope da EMA 20;
- ADX.

#### `classify_volatility(df) -> tuple[str, float]`

Usar:

- ATR atual vs percentil dos ultimos N candles;
- Bollinger Band Width atual vs media.

#### `classify_market_regime(df, minutes_to_news=1000) -> MarketRegime`

Regras iniciais:

- se noticia em menos de 15 min: `pre_news`;
- ADX alto e EMAs alinhadas: `strong_trend`;
- ADX baixo e Bollinger estreita: `compression`;
- ADX baixo e preco oscilando entre zonas: `range`;
- ATR percentile muito alto: `high_volatility`;
- caso contrario: `weak_trend`.

### Testes unitarios

Arquivo: `tests/test_market_regime.py`

Casos recomendados:

1. `test_classify_market_regime_pre_news_overrides_technical`
   - `minutes_to_news=10`;
   - label `pre_news`.

2. `test_classify_market_regime_strong_uptrend`
   - EMA 20 > EMA 200, slope positiva, ADX alto;
   - `trend_direction="bullish"`.

3. `test_classify_market_regime_strong_downtrend`
   - EMA 20 < EMA 200, slope negativa, ADX alto.

4. `test_classify_market_regime_compression`
   - Bollinger Band Width baixo e ADX baixo.

5. `test_classify_market_regime_high_volatility`
   - ATR atual acima do percentil definido.

6. `test_classify_market_regime_handles_missing_adx`
   - sem coluna ADX;
   - nao deve quebrar;
   - retornar fallback `weak_trend` ou `range`.

7. `test_technical_analyzer_adds_adx_and_bandwidth`
   - apos `calcular_indicadores`, colunas esperadas existem ou sao detectaveis por prefixo.

### Criterio de aceite

- O regime de mercado e retornado como dado estruturado.
- O score pode usar o regime sem parsing de texto.

## Fase 5: analise multi-timeframe

### Objetivo

Separar vies direcional de entrada. M15 fica como gatilho; H1/H4 filtram contexto.

### Arquivos

- Criar: `analysis/multi_timeframe.py`
- Criar: `tests/test_multi_timeframe.py`
- Evoluir: `app/forex_bot.py`
- Evoluir: `strategy/percentual_indicator.py`

### Modelo sugerido

```python
@dataclass(frozen=True)
class TimeframeAnalysis:
    timeframe: str
    trend: str
    score: float
    last_pattern: str | None
    regime: str
    nearest_level: float | None
```

```python
@dataclass(frozen=True)
class MultiTimeframeResult:
    entry_timeframe: str
    higher_timeframes: list[str]
    alignment: str
    alignment_score: float
    analyses: dict[str, TimeframeAnalysis]
```

Alinhamentos:

- `bullish_aligned`
- `bearish_aligned`
- `mixed`
- `countertrend_bullish`
- `countertrend_bearish`

### Funcoes sugeridas

#### `analyze_timeframe(df, timeframe) -> TimeframeAnalysis`

Calcular:

- tendencia por EMA;
- score tecnico simples;
- ultimo padrao de candle;
- regime;
- nivel proximo.

#### `calculate_alignment(analyses) -> tuple[str, float]`

Regras iniciais:

- H1 e H4 bullish, M15 bullish: `bullish_aligned`, score alto.
- H1 e H4 bearish, M15 bearish: `bearish_aligned`, score alto.
- M15 contra H4: `countertrend_*`, score reduzido.
- divergencia entre H1 e H4: `mixed`.

#### `MultiTimeframeAnalyzer`

Pode receber DataFrames ja carregados:

```python
MultiTimeframeAnalyzer({
    "15m": df_m15,
    "1h": df_h1,
    "4h": df_h4,
})
```

Evitar que a primeira versao acople diretamente a chamadas de API. Isso facilita testes.

### Integracao com dados reais

Em `ForexBot`, criar etapa opcional:

1. Buscar M15 como hoje.
2. Buscar H1 e H4 em menor frequencia ou cachear por par.
3. Gerar `mtf_result`.
4. Passar `mtf_result` para score/sinal.

### Testes unitarios

Arquivo: `tests/test_multi_timeframe.py`

Casos recomendados:

1. `test_calculate_alignment_bullish_aligned`
   - M15/H1/H4 bullish;
   - alignment `bullish_aligned`;
   - score positivo.

2. `test_calculate_alignment_bearish_aligned`
   - todos bearish.

3. `test_calculate_alignment_countertrend_bullish`
   - M15 bullish, H4 bearish;
   - `countertrend_bullish`;
   - score menor que alinhado.

4. `test_calculate_alignment_mixed`
   - H1 bullish, H4 bearish.

5. `test_analyze_timeframe_handles_empty_df`
   - DataFrame vazio;
   - retornar erro controlado ou resultado neutro documentado.

6. `test_multi_timeframe_analyzer_does_not_call_network`
   - construir com DataFrames;
   - garantir que analise roda sem mock de API.

### Criterio de aceite

- O sinal final consegue saber se esta a favor ou contra H1/H4.
- Testes multi-timeframe rodam sem internet.

## Fase 6: score percentual e geracao de sinal

### Objetivo

Integrar candlestick, niveis, regime, multi-timeframe e qualidade de dados ao score e ao `SignalGenerator`.

### Arquivos

- Evoluir: `strategy/percentual_indicator.py`
- Evoluir: `strategy/signal_generator.py`
- Criar/expandir: `tests/test_percentual_indicator.py`
- Expandir: `tests/test_signal_generator.py`

### Score proposto

Manter a ideia de score 0-100, mas separar componentes:

| Componente | Peso inicial | Observacao |
|---|---:|---|
| EMA trend | 15 | reduzir peso isolado |
| EMA slope | 10 | manter aceleracao |
| RSI | 10 | momento, nao gatilho unico |
| Bollinger position | 10 | contexto de preco |
| Candle pattern | 15 | novo motor candlestick |
| Level reaction | 15 | rejeicao/rompimento em zona |
| MTF alignment | 15 | filtro direcional |
| Market regime | 5 | bonificar regra adequada ao ambiente |
| Data quality | -10 a 0 | penalidade |
| News/spread risk | -10 a 0 | penalidade |

Os pesos devem ser constantes configuraveis para facilitar backtest.

### Saida do score

Alterar `calcular` para retornar mais detalhes:

```python
{
    "score": 76.0,
    "direction": "BUY",
    "confidence": "moderate",
    "label": "COMPRA_MODERADA",
    "details": {...},
    "reasons": [
        "M15/H1/H4 alinhados em alta",
        "Pinbar bullish em suporte",
        "RSI saudavel"
    ],
    "penalties": [
        "Spread acima da media"
    ]
}
```

### Classificacao de confianca

Compra:

- `80-100`: `COMPRA_FORTE`
- `65-80`: `COMPRA_MODERADA`

Neutro:

- `35-65`: `NEUTRO`

Venda:

- `20-35`: `VENDA_MODERADA`
- `0-20`: `VENDA_FORTE`

### Sinais no `SignalGenerator`

Adicionar estrutura ao retorno interno antes de formatar texto:

```python
{
    "action": "BUY" | "SELL" | "WAIT",
    "mode": "sniper" | "trend" | "breakout" | "reversal" | "wait",
    "confidence": "strong" | "moderate" | "neutral",
    "entry": float,
    "stop_loss": float | None,
    "take_profit": float | None,
    "risk_reward": float | None,
    "reasons": list[str],
}
```

Manter `analisar_e_sugerir` retornando string para compatibilidade com CLI, mas criar metodo novo:

- `gerar_sinal(score_data=None, context=None) -> dict`
- `formatar_sinal(signal: dict) -> str`

### Stop e alvo por estrutura

Implementar:

#### `calculate_structural_stop(action, entry, candle, nearest_level, atr) -> float`

Compra:

- abaixo do `Low` do candle padrao ou swing low;
- buffer `0.2 * ATR`.

Venda:

- acima do `High` do candle padrao ou swing high;
- buffer `0.2 * ATR`.

#### `calculate_take_profit(action, entry, stop_loss, levels, rr_ratio=2.0) -> float`

Regra:

- alvo minimo `2R`;
- se houver proxima zona antes de `1.5R`, bloquear ou reduzir confianca;
- se houver proxima zona depois de `2R`, usar `2R` como TP padrao.

### Testes unitarios

Arquivo: `tests/test_percentual_indicator.py`

Casos:

1. `test_score_penalizes_open_candle_quality`
   - `data_quality=-1`;
   - score final menor que sem penalidade.

2. `test_score_rewards_bullish_candle_at_support`
   - pinbar bullish + suporte;
   - score aumenta.

3. `test_score_rewards_mtf_bullish_alignment`
   - MTF alinhado em alta;
   - score > neutro.

4. `test_score_reduces_countertrend_signal`
   - M15 bullish contra H4 bearish;
   - score menor que caso alinhado.

5. `test_score_pre_news_penalty_can_force_wait_zone`
   - score base compra moderada;
   - noticia em menos de 15 min;
   - score cai para neutro ou sinal bloqueado conforme regra definida.

6. `test_score_returns_reasons_and_penalties`
   - retorno contem listas.

7. `test_confidence_boundaries`
   - 80 vira forte;
   - 65 vira moderado;
   - 64.99 vira neutro/limite definido.

Arquivo: `tests/test_signal_generator.py`

Adicionar:

1. `test_gerar_sinal_returns_structured_buy`
   - score alto, contexto bullish;
   - `action="BUY"`.

2. `test_gerar_sinal_wait_when_score_neutral`
   - score 50;
   - `action="WAIT"`.

3. `test_structural_stop_buy_below_candle_low`
   - entrada acima do low;
   - SL menor que low por buffer.

4. `test_structural_stop_sell_above_candle_high`
   - SL maior que high.

5. `test_take_profit_respects_rr_ratio`
   - distancia TP = 2x distancia risco quando sem nivel proximo.

6. `test_signal_blocks_trade_when_next_level_too_close`
   - resistencia antes de 1.5R em compra;
   - sinal vira WAIT ou confianca reduzida.

7. `test_analisar_e_sugerir_preserves_legacy_text_output`
   - metodo antigo ainda retorna string contendo `SUGESTÃO`.

### Criterio de aceite

- Score final explica motivos e penalidades.
- Sinal final pode ser consumido como dict e como string.
- Regras antigas continuam funcionando enquanto as novas camadas sao opcionais.

## Fase 7: relatorio, radar e grafico

### Objetivo

Mostrar ao usuario por que o sinal existe, qual candle foi analisado e qual contexto foi usado.

### Arquivos

- Evoluir: `app/forex_bot.py`
- Evoluir: `analysis/charting.py`
- Criar/expandir: `tests/test_forex_bot.py`
- Criar: `tests/test_charting.py` se necessario

### Relatorio completo

Adicionar bloco:

```text
LEITURA CANDLESTICK
Timeframe de entrada : M15
Candle analisado     : fechado
Padrao principal     : Pinbar bullish (forca 0.82)
Contexto             : pullback em tendencia de alta H1/H4
Nivel relevante      : suporte M15 em 1.08420 (+0.18 ATR)
Regime               : tendencia moderada, volatilidade normal
Qualidade dos dados  : OK
```

### Radar

Manter compacto:

```text
EURUSD: 1.08450 ↑ | 🟢 | RSI:54 | 📊76% | MTF↑ | Pin↑
```

Se o terminal ficar longo, priorizar:

- par;
- preco;
- sinal;
- score;
- MTF;
- alerta noticia.

### Grafico

Adicionar gradualmente:

1. Marcar ultimo padrao de candle.
2. Desenhar suporte/resistencia como faixas horizontais.
3. Desenhar SL/TP quando houver sinal.
4. Manter Bollinger, EMA e RSI existentes.

### Testes

Arquivo: `tests/test_forex_bot.py`

Casos:

1. `test_relatorio_includes_candle_closed_status`
   - mockar dados;
   - saida contem `Candle analisado`.

2. `test_radar_handles_missing_mtf_without_crashing`
   - simular falha no MTF;
   - radar ainda imprime par.

3. `test_relatorio_includes_score_reasons`
   - score estruturado com reasons;
   - texto inclui motivo principal.

Arquivo: `tests/test_charting.py`

Casos:

1. `test_chart_generator_accepts_levels_optional`
   - chamar grafico sem niveis e com niveis.

2. `test_chart_generator_accepts_signal_optional`
   - chamar grafico sem sinal e com sinal.

3. `test_chart_generator_handles_missing_pattern`
   - nao quebrar se padrao ausente.

Observacao: para testes de grafico, nao validar pixel. Validar que o arquivo e criado em diretorio temporario e nao esta vazio.

### Criterio de aceite

- Relatorio fica mais explicavel.
- Radar continua compacto.
- Grafico nao quebra se contexto opcional estiver ausente.

## Fase 8: backtest minimo

### Objetivo

Medir se as novas regras melhoram a estrategia antes de depender delas no uso diario.

### Arquivos

- Criar: `backtesting/simple_backtester.py`
- Criar: `tests/test_backtester.py`
- Opcional: `docs/backtest_results.md`

### Escopo inicial

Simulador simples por candle fechado:

1. Recebe DataFrame OHLC com indicadores.
2. Itera candle por candle.
3. Calcula sinal usando somente dados ate aquele candle.
4. Entra no fechamento do candle de sinal ou abertura do proximo candle, definir uma regra e manter.
5. Verifica se SL ou TP foi atingido nos candles seguintes.
6. Salva resultado do trade.

### Modelo de trade

```python
{
    "symbol": "EURUSD",
    "entry_time": timestamp,
    "action": "BUY",
    "entry": 1.0845,
    "stop_loss": 1.0820,
    "take_profit": 1.0895,
    "exit_time": timestamp,
    "exit_price": 1.0895,
    "result_r": 2.0,
    "pattern": "pinbar_bullish",
    "regime": "weak_trend",
    "session": "london",
}
```

### Metricas

Implementar:

- total de trades;
- win rate;
- loss rate;
- media de R;
- expectancy;
- profit factor;
- max drawdown em R;
- resultado por par;
- resultado por padrao;
- resultado por regime;
- resultado por sessao.

### Testes unitarios

Arquivo: `tests/test_backtester.py`

Casos:

1. `test_backtester_records_winning_buy_trade`
   - candle seguinte atinge TP;
   - resultado `+R`.

2. `test_backtester_records_losing_buy_trade`
   - candle seguinte atinge SL;
   - resultado `-1R`.

3. `test_backtester_records_winning_sell_trade`
   - venda atinge TP abaixo.

4. `test_backtester_handles_no_signal`
   - nenhum trade gerado.

5. `test_backtester_does_not_look_ahead`
   - sinal no candle N nao pode usar dados do candle N+1.

6. `test_metrics_calculate_win_rate`
   - 2 wins, 1 loss;
   - win rate 66.67%.

7. `test_metrics_calculate_profit_factor`
   - ganhos/perdas corretamente.

8. `test_metrics_group_by_pattern`
   - saida agregada por padrao.

### Criterio de aceite

- Backtest roda localmente sem API.
- E possivel comparar estrategia antiga vs nova em dados salvos.
- O resultado por padrao/regime indica quais regras merecem ficar no radar.

## Sequencia recomendada de PRs ou commits

1. `docs`: plano e contratos de implementacao.
2. `test`: helpers de dados sinteticos.
3. `feat(data)`: candle fechado e validacao OHLC.
4. `feat(candle)`: anatomia e padroes de candlestick.
5. `feat(levels)`: swings, zonas e range asiatico.
6. `feat(regime)`: ADX, volatilidade e classificacao.
7. `feat(mtf)`: analise multi-timeframe.
8. `feat(score)`: score com contexto e penalidades.
9. `feat(signal)`: sinal estruturado, SL/TP por estrutura.
10. `feat(report)`: relatorio, radar e grafico explicaveis.
11. `feat(backtest)`: backtester minimo e metricas.
12. `chore`: calibracao de pesos com base em resultados.

## Ordem de risco tecnico

Baixo risco:

- criar `analysis/candlestick.py` isolado;
- criar `analysis/levels.py` isolado;
- adicionar testes sinteticos;
- adicionar relatorio opcional.

Medio risco:

- alterar `PriceDataFeed` para filtrar candle aberto;
- adicionar ADX e novas colunas dinamicas;
- integrar regime e niveis ao score.

Alto risco:

- mudar criterio final de compra/venda;
- alterar calculo de lote/SL/TP;
- usar multi-timeframe com varias chamadas de API no radar.

Mitigacao:

- manter flags ou fallback para logica antiga;
- cachear timeframes maiores;
- comparar score antigo e novo em paralelo antes de trocar decisao final.

## Flags de compatibilidade sugeridas

Em `shared/config.py`, adicionar:

```python
USE_CLOSED_CANDLES_ONLY = True
ENABLE_CANDLESTICK_ENGINE = True
ENABLE_LEVEL_ANALYSIS = True
ENABLE_MARKET_REGIME = True
ENABLE_MULTI_TIMEFRAME = False
ENABLE_STRUCTURED_SIGNAL = True
ENABLE_BACKTEST_MODE = False
```

Motivo:

- permitir ligar/desligar camadas durante validacao;
- facilitar teste A/B;
- evitar que falha em modulo novo pare o radar.

## Definition of Done geral

Uma fase so deve ser considerada concluida quando:

1. Codigo implementado.
2. Testes unitarios da fase passando.
3. Testes existentes do projeto passando.
4. Relatorio ou radar nao quebram com contexto ausente.
5. Logs mostram falhas de dados sem encerrar o bot.
6. A mudanca esta documentada em `docs/feat_codex_plan.md` ou documento tecnico relacionado.

## Comandos de validacao

Comandos esperados ao longo da implementacao:

```bash
python -m unittest
python -m unittest tests.test_price_data_quality
python -m unittest tests.test_candlestick
python -m unittest tests.test_levels
python -m unittest tests.test_market_regime
python -m unittest tests.test_multi_timeframe
python -m unittest tests.test_signal_generator
python -m unittest tests.test_backtester
```

Se o projeto migrar para `pytest`, manter os nomes de testes e apenas trocar o runner.

## Primeira entrega recomendada

A primeira entrega de codigo deve ser pequena:

1. `filtrar_candles_fechados`
2. `validar_ohlc`
3. testes de qualidade de dados
4. integracao no `PriceDataFeed.obter_historico_velas`
5. indicacao no relatorio de que o candle analisado esta fechado

Essa entrega tem o melhor custo-beneficio porque reduz falsos sinais sem mudar a estrategia principal.

## Segunda entrega recomendada

Depois dos dados confiaveis:

1. criar `analysis/candlestick.py`;
2. implementar anatomia do candle;
3. implementar doji, pinbar, engulfing e inside bar;
4. adicionar testes unitarios;
5. mostrar o padrao detectado no relatorio, ainda sem alterar sinal final.

Esse passo permite validar visualmente a leitura de candles antes de deixar o padrao influenciar compra/venda.

## Terceira entrega recomendada

Integrar contexto:

1. `analysis/levels.py`;
2. suporte/resistencia por swing;
3. rejeicao em zona;
4. score recebe `level_reaction`;
5. grafico mostra zonas.

So depois disso vale aumentar o peso de candlestick no sinal, porque padrao sem nivel tende a gerar ruido.

## Resultado esperado ao fim do plano

O Forex DSS deve sair de uma estrategia baseada em indicadores e ultima vela para uma arquitetura de confluencia:

- dado validado;
- candle fechado;
- padrao de candle quantificado;
- nivel relevante;
- regime de mercado;
- alinhamento H1/H4;
- score com motivos e penalidades;
- SL/TP coerente com estrutura;
- backtest medindo a qualidade das regras.

Com isso, o sistema fica mais preciso, mais explicavel e mais facil de evoluir sem quebrar o comportamento atual.
