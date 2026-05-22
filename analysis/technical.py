import pandas as pd
import pandas_ta as ta

class TechnicalAnalyzer:
    """
    Recebe os dados brutos de preço (OHLCV) e aplica as fórmulas matemáticas
    para gerar indicadores (EMAs, RSI, Bollinger Bands).
    """
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()

    def calcular_indicadores(self) -> pd.DataFrame:
        self.df.ta.rsi(length=14, append=True)
        self.df.ta.ema(length=20, append=True)
        self.df.ta.ema(length=200, append=True)
        
        # Bandas de Bollinger (20 períodos, 2 Desvios Padrão)
        self.df.ta.bbands(length=20, std=2, append=True)

        # ATR (Average True Range) para volatilidade
        self.df.ta.atr(length=14, append=True)
        
        # NOVO: ADX para força da tendência
        self.df.ta.adx(length=14, append=True)
        
        # NOVO: Bollinger Band Width para compressão
        self.df.ta.bbands(length=20, std=2, append=True) # redundante mas garante se bbands mudar
        # pandas_ta já adiciona BBB_20_2.0 quando bbands é calculado
        
        self.df.dropna(inplace=True)
        return self.df

    def gerar_resumo_atual(self) -> str:
        self.calcular_indicadores()
        
        if self.df.empty:
            return "❌ Dados insuficientes para análise técnica completa."
            
        ultima_vela = self.df.iloc[-1]
        
        fechamento = ultima_vela['Close']
        rsi = ultima_vela['RSI_14']
        ema_20 = ultima_vela['EMA_20']
        ema_200 = ultima_vela['EMA_200']
        
        # Encontra o nome exato das colunas das Bandas dinamicamente 
        # (Isso evita erros de versão da biblioteca pandas_ta)
        col_bbl = [c for c in self.df.columns if c.startswith('BBL_')][0] # Banda Inferior
        col_bbu = [c for c in self.df.columns if c.startswith('BBU_')][0] # Banda Superior
        
        bb_inferior = ultima_vela[col_bbl]
        bb_superior = ultima_vela[col_bbu]
        
        # --- 1. Tendência (EMAs) ---
        is_uptrend = ema_20 > ema_200
        if is_uptrend:
            tendencia = "ALTA 🟢 (EMA Curta acima da Longa)"
        else:
            tendencia = "BAIXA 🔴 (EMA Curta abaixo da Longa)"
            
        # --- 2. Contextualizando Momento (RSI) com a Tendência ---
        if rsi > 70:
            condicao_rsi = f"SOBRECOMPRADO 🔴 ({rsi:.2f} - Risco de Recuo)"
        elif rsi < 30:
            condicao_rsi = f"SOBREVENDIDO 🟢 ({rsi:.2f} - Potencial Reversão/Pullback)"
        else:
            # RSI entre 30 e 70: Contextualiza com a tendência principal
            if is_uptrend and rsi >= 45:
                condicao_rsi = f"FORÇA COMPRADORA 🟢 ({rsi:.2f} - A favor da tendência)"
            elif not is_uptrend and rsi <= 55:
                condicao_rsi = f"FORÇA VENDEDORA 🔴 ({rsi:.2f} - A favor da tendência)"
            else:
                condicao_rsi = f"MOMENTO FRACO ⚪ ({rsi:.2f} - Contra a tendência macro)"

        # --- 3. Volatilidade (Bollinger Bands) ---
        # Adicionamos uma margem minúscula (0.05%) para considerar que "tocou" na banda
        margem = fechamento * 0.0005 
        
        if fechamento <= (bb_inferior + margem):
            condicao_bb = f"BANDA INFERIOR 🟢 (Preço baixo, desconto para compra)"
        elif fechamento >= (bb_superior - margem):
            condicao_bb = f"BANDA SUPERIOR 🔴 (Preço alto, risco de exaustão)"
        else:
            # Contextualiza: se tá no meio da banda, tem espaço para correr.
            if is_uptrend:
                condicao_bb = f"ESPAÇO LIVRE 🟢 (Longe da banda superior, alvo p/ cima)"
            else:
                condicao_bb = f"ESPAÇO LIVRE 🔴 (Longe da banda inferior, alvo p/ baixo)"

        # --- Formatação do Painel ---
        resumo = f"""
==================================================
📊 LEITURA TÉCNICA (Confluência Avançada)
==================================================
• Preço Atual        : {fechamento:.5f}
• Tendência Principal: {tendencia}
• Momento (RSI 14)   : {condicao_rsi}
• Volatilidade (BB)  : {condicao_bb}
==================================================
        """
        return resumo