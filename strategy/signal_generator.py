import pandas as pd

class SignalGenerator:
    """
    Motor de Confluência e Gestão de Risco.
    Avalia a análise técnica e gera a sugestão de trade final.
    """
    def __init__(self, dataframe: pd.DataFrame, risco_recompensa: float = 2.0):
        self.df = dataframe
        self.rr_ratio = risco_recompensa # Relação de Risco 1:2

    def analisar_e_sugerir(self) -> str:
        if self.df.empty:
            return "Sem dados para gerar sinal."

        ultima_vela = self.df.iloc[-1]
        
        preco_atual = ultima_vela['Close']
        rsi = ultima_vela['RSI_14']
        ema_20 = ultima_vela['EMA_20']
        ema_200 = ultima_vela['EMA_200']
        
        col_bbl = [c for c in self.df.columns if c.startswith('BBL_')][0]
        col_bbu = [c for c in self.df.columns if c.startswith('BBU_')][0]
        bb_inferior = ultima_vela[col_bbl]
        bb_superior = ultima_vela[col_bbu]

        margem_bb = preco_atual * 0.0005 

        sinal = "ESPERAR (Mercado Neutro)"
        lote_sugerido = 0.01 # Começando com o mínimo absoluto para segurança
        stop_loss = 0.0
        take_profit = 0.0

        # Lógica do SINAL DE COMPRA (Sniper)
        if (ema_20 > ema_200) and (rsi < 40) and (preco_atual <= bb_inferior + margem_bb):
            sinal = "COMPRAR 🟢"
            # Define Stop Loss abaixo do fundo recente (aprox. 15 pips para EURUSD)
            stop_loss = preco_atual - 0.0015
            # Define Take Profit com base na relação Risco/Retorno (aprox 30 pips)
            take_profit = preco_atual + (0.0015 * self.rr_ratio)

        # Lógica do SINAL DE VENDA (Sniper)
        elif (ema_20 < ema_200) and (rsi > 60) and (preco_atual >= bb_superior - margem_bb):
            sinal = "VENDER 🔴"
            stop_loss = preco_atual + 0.0015
            take_profit = preco_atual - (0.0015 * self.rr_ratio)

        # Se não há sinal, os preços de SL e TP ficam zerados
        str_sl = f"{stop_loss:.5f}" if stop_loss > 0 else "N/A"
        str_tp = f"{take_profit:.5f}" if take_profit > 0 else "N/A"

        resumo = f"""
==================================================
📊 SUGESTÃO DE OPERAÇÃO (Risk/Reward 1:{int(self.rr_ratio)})
==================================================
SUGESTÃO    : {sinal}
QUANTIDADE  : {lote_sugerido} (Micro Lote Inicial)
Stop Loss   : {str_sl}
Take Profit : {str_tp}
==================================================
"""
        return resumo