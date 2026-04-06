# NEXT

## Próximo passo recomendado: Fase 3 - Dashboard Web & Performance

Com o motor de análise técnica, fundamental e o suporte multi-par operando perfeitamente no terminal, o projeto agora deve evoluir para uma **interface visual profissional** que permita acompanhar o mercado com a experiência de um terminal de trading (Bloomber/Refinitiv style).

## Objetivos da Fase 3

1. **API de Backend (FastAPI):** Expor a lógica do `ForexBot` via endpoints REST e WebSockets.
2. **Interface em Tempo Real (HTMX):** Criar o dashboard web dinâmico conforme o `IMPLEMENTACAO_FRONTEND.MD`.
3. **Gráficos Interativos:** Implementar `Lightweight Charts` para visualizar as entradas e indicadores de forma fluída.
4. **Motor Fundamental Real:** Evoluir o `FundamentalAnalyzer` para buscar notícias de um feed real (Investing.com ou similar via Scraper).

## Por que este é o próximo passo?

- O sistema atual é potente mas visualmente limitado pelo terminal.
- Gráficos interativos permitem uma validação visual muito mais rápida dos sinais.
- Uma API web permite o uso do Advisor em dispositivos móveis.

## Critério de pronto da Fase 3

1. Dashboard web acessível localmente via browser.
2. Atualização automática do radar sem refresh de página.
3. Gráfico de velas carregando dinamicamente para o par selecionado.

## Observação importante

Mantenha a filosofia de **baixa latência**. Use o template proposto com HTMX para garantir que o advisor continue leve e eficiente.
