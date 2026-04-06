# NEXT

## Próximo passo recomendado: Fase 2 - Monitoramento Multi-Par

Agora que o núcleo do sistema está **estável, testado e confiável**, o próximo passo é escalar a capacidade do Advisor de monitorar apenas um par para uma **grade de observação simultânea**.

## Objetivos da Fase 2

1. **Configuração Dinâmica:** Criar um arquivo `pairs.json` ou similar para listar os pares a serem monitorados (ex: EURUSD, GBPUSD, USDJPY, AUDUSD).
2. **Scanner em Tempo Real:** Evoluir o radar CLI para percorrer a lista de pares e exibir os sinais de confluência mais fortes no topo.
3. **Gestão de Risco por Conta:** Integrar um calculador de lote que considere o balanço atual da conta (definido no `.env` ou `config.py`) e o risco máximo configurado.
4. **Motor Fundamentalista Inicial:** Implementar um scraper ou API para capturar "Notícias de Alto Impacto" (Calendário Econômico) e avisar o usuário se houver evento nos próximos 30 minutos.

## Por que este é o próximo passo?

- A lógica de análise técnica já funciona perfeitamente em escala unitária.
- Um trader real monitora vários ativos simultaneamente em busca de confluência.
- A gestão de risco precisa ser dinâmica para ser útil (pips -> lote financeiro).

## Critério de pronto da Fase 2

1. Dashboard exibindo mini-radares para pelo menos 3 pares simultaneamente.
2. Aviso visual de "Notícia Próxima" na interface.
3. Sugestão de lote calculada com base em % de risco da conta.

## Observação importante

Mantenha o foco na **Dashboard CLI**. A transação para uma interface gráfica (GUI/Web) deve ser considerada apenas após o motor fundamentalista estar operando e os testes estarem cobrindo 80% do código.
