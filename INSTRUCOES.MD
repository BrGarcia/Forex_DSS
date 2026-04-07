# 📖 Manual do Usuário - Forex Advisor DSS

Bem-vindo ao **Forex Advisor DSS**! Este sistema foi desenvolvido para ajudar você a tomar decisões no mercado de câmbio (Forex) de forma mais técnica e profissional, mesmo que você seja um iniciante.

---

## 🚀 1. Como Começar

### Pré-requisitos
- Ter o **Python 3.9** ou superior instalado.
- Conexão com a internet (para baixar os preços em tempo real).

### Instalação Rápida
1. Abra o terminal ou prompt de comando na pasta do projeto.
2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

### Executando o Programa
No terminal, digite:
```bash
python main.py
```

---

## 🎮 2. Comandos do Teclado

O programa roda em uma interface de texto (CLI) interativa:

- **[1 a 9]**: Exibe um relatório detalhado do par correspondente na lista (Ex: Pressione `1` para ver o primeiro par da lista).
- **[S]**: Sai do programa com segurança.
- **[ENTER]**: Atualiza ou exibe o relatório do primeiro par disponível.

---

## 📊 3. Entendendo a Tela (O "Radar")

Na parte inferior da tela, você verá o **Radar de Preços** que se atualiza automaticamente:
`EURUSD: 1.08540 ↑ | 🟢 | RSI:35`

- **Símbolo (EURUSD)**: O par de moedas sendo monitorado.
- **Preço e Seta**: O preço atual e se ele subiu (↑), desceu (↓) ou está estável (→) em relação à última leitura.
- **Círculo de Status**:
  - 🟢 **Verde**: Oportunidade de COMPRA detectada.
  - 🔴 **Vermelho**: Oportunidade de VENDA detectada.
  - ⚪ **Branco**: Mercado neutro, hora de esperar.
- **RSI**: O valor do indicador de força (explicado abaixo).

---

## 🧠 4. Guia para Iniciantes: Interpretando os Indicadores

Se você é novo no mercado, aqui está como ler os dados do relatório completo:

### A. Tendência (EMAs)
O sistema usa duas Médias Móveis Exponenciais (EMA 20 e EMA 200).
- **EMA 20 acima da EMA 200**: Tendência de **ALTA**. O mercado está subindo no longo prazo.
- **EMA 20 abaixo da EMA 200**: Tendência de **BAIXA**. O mercado está caindo no longo prazo.

### B. Momento (RSI 14)
O RSI mede a "velocidade" do preço em uma escala de 0 a 100.
- **Abaixo de 30 (Sobrevendido)**: O preço caiu muito e pode estar "barato", sugerindo uma possível subida.
- **Acima de 70 (Sobrecomprado)**: O preço subiu muito e pode estar "caro", sugerindo uma possível queda.

### C. Volatilidade (Bandas de Bollinger)
São "envelopes" que cercam o preço.
- Quando o preço toca a **Banda Inferior**, ele está esticado para baixo (chance de repique).
- Quando o preço toca a **Banda Superior**, ele está esticado para cima (chance de correção).

### D. Sessões de Mercado
O Forex funciona 24h, mas a volatilidade muda conforme a cidade:
- **Ásia (Tóquio)**: Geralmente mais calmo. O sistema marca a máxima e mínima deste período.
- **Europa (Londres)** e **EUA (Nova York)**: Períodos de maior movimento.
- **Overlap (Sobreposição)**: Quando Londres e NY estão abertas juntas. É o melhor momento para operar devido à alta liquidez.

---

## 🛡️ 5. Sugestão de Operação e Gestão de Risco

Quando o sistema exibe um sinal de **COMPRAR** ou **VENDER**, ele também fornece:

1. **QUANTIDADE (Lote)**: O tamanho da posição sugerido. O sistema calcula isso automaticamente para arriscar apenas **1% do seu capital** (baseado no saldo configurado).
2. **Stop Loss (SL)**: O "botão de pânico". Se o preço atingir este nível, você deve sair da operação para evitar perdas maiores.
3. **Take Profit (TP)**: O seu alvo de lucro.
4. **Relação Risco/Retorno (1:2)**: O sistema é configurado para que o seu lucro potencial seja o dobro do seu risco. Assim, mesmo que você acerte apenas metade das vezes, ainda terá lucro.

---

## ⚠️ 6. Avisos Importantes

1. **O DSS é um Suporte, não um Robô de Execução**: Ele sugere, mas você decide se entra na corretora.
2. **Cuidado com Notícias**: O sistema exibe um alerta `⚠️` se houver notícias importantes próximas. Evite operar minutos antes de grandes anúncios econômicos.
3. **Timeframe**: Este sistema foi otimizado para o gráfico de **15 minutos (M15)**.

---
**Aviso Legal:** *O mercado Forex envolve alto risco. Nunca invista dinheiro que você não pode perder. Este software é uma ferramenta educacional e não garante lucros.*
