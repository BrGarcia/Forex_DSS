import pandas as pd


class SignalGenerator:
    """
    Motor de Confluência e Gestão de Risco.
    Avalia a análise técnica e gera a sugestão de trade final.

    Modos de Entrada:
    ─────────────────────────────────────────────────────────
    • Modo Sniper (Reversão/Pullback) — Alta precisão
        Requer 3 condições simultâneas rígidas:
        BUY : EMA curta > longa  +  RSI < 40  +  preço tocando BB inferior
        SELL: EMA curta < longa  +  RSI > 60  +  preço tocando BB superior

    • Modo Tendência (Continuação) — Confirmado pelo Score Percentual
        Ativado quando o Sniper não dispara mas o Score indica confluência forte.
        BUY : Score > 70  +  EMA curta > longa  +  RSI em zona neutra (45–65)
        SELL: Score < 30  +  EMA curta < longa  +  RSI em zona neutra (35–55)
    ─────────────────────────────────────────────────────────
    """

    def __init__(self, dataframe: pd.DataFrame, risco_recompensa: float = 2.0):
        self.df       = dataframe
        self.rr_ratio = risco_recompensa  # Relação Risco/Retorno padrão 1:2

    def analisar_e_sugerir(self, score_data: dict = None) -> str:
        """
        Gera a sugestão de operação combinando análise técnica clássica
        com o Score Percentual de Confluência (quando disponível).

        Args:
            score_data: Dict retornado por PercentualIndicator.calcular().
                        Se None, apenas o Modo Sniper é avaliado.

        Returns:
            String formatada com sugestão, modo, SL e TP.
        """
        if self.df.empty:
            return "Sem dados para gerar sinal."

        ultima_vela = self.df.iloc[-1]

        preco_atual = ultima_vela['Close']
        rsi         = ultima_vela['RSI_14']
        ema_20      = ultima_vela['EMA_20']
        ema_200     = ultima_vela['EMA_200']

        col_bbl     = [c for c in self.df.columns if c.startswith('BBL_')][0]
        col_bbu     = [c for c in self.df.columns if c.startswith('BBU_')][0]
        bb_inferior = ultima_vela[col_bbl]
        bb_superior = ultima_vela[col_bbu]

        margem_bb = preco_atual * 0.0005

        atr = ultima_vela.get('ATRr_14', 0.0015)
        if atr == 0:
            atr = 0.0015

        sinal         = "ESPERAR (Mercado Neutro)"
        modo          = ""
        lote_sugerido = 0.01
        stop_loss     = 0.0
        take_profit   = 0.0

        # ── Modo Sniper (Reversão/Pullback) ──────────────────────────
        # Prioridade máxima: entrada cirúrgica em pullbacks dentro de tendência
        if (ema_20 > ema_200) and (rsi < 40) and (preco_atual <= bb_inferior + margem_bb):
            sinal        = "COMPRAR 🟢"
            modo         = "Sniper 🎯 (Reversão)"
            distancia_sl = atr * 1.5
            stop_loss    = preco_atual - distancia_sl
            take_profit  = preco_atual + (distancia_sl * self.rr_ratio)

        elif (ema_20 < ema_200) and (rsi > 60) and (preco_atual >= bb_superior - margem_bb):
            sinal        = "VENDER 🔴"
            modo         = "Sniper 🎯 (Reversão)"
            distancia_sl = atr * 1.5
            stop_loss    = preco_atual + distancia_sl
            take_profit  = preco_atual - (distancia_sl * self.rr_ratio)

        # ── Modo Tendência (Continuação via Score Percentual) ─────────
        # Ativado somente quando Sniper não disparou E score indica forte confluência
        elif score_data:
            score = score_data.get("score", 50)

            if score > 70 and (ema_20 > ema_200) and (45 <= rsi <= 65):
                sinal        = "COMPRAR 🟢"
                modo         = f"Tendência 📈 (Score {score:.0f}%)"
                distancia_sl = atr * 1.5
                stop_loss    = preco_atual - distancia_sl
                take_profit  = preco_atual + (distancia_sl * self.rr_ratio)

            elif score < 30 and (ema_20 < ema_200) and (35 <= rsi <= 55):
                sinal        = "VENDER 🔴"
                modo         = f"Tendência 📉 (Score {score:.0f}%)"
                distancia_sl = atr * 1.5
                stop_loss    = preco_atual + distancia_sl
                take_profit  = preco_atual - (distancia_sl * self.rr_ratio)

        # ── Formatação do Resumo ──────────────────────────────────────
        str_sl    = f"{stop_loss:.5f}"  if stop_loss    > 0 else "N/A"
        str_tp    = f"{take_profit:.5f}" if take_profit   > 0 else "N/A"
        modo_linha = f"\nMODO        : {modo}" if modo else ""

        resumo = f"""
==================================================
📊 SUGESTÃO DE OPERAÇÃO (Risk/Reward 1:{int(self.rr_ratio)})
==================================================
SUGESTÃO    : {sinal}{modo_linha}
QUANTIDADE  : {lote_sugerido} (Micro Lote Inicial)
Stop Loss   : {str_sl}
Take Profit : {str_tp}
==================================================
"""
        return resumo