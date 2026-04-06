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
        
        # NOVO: Calcula as Bandas de Bollinger (20 períodos, 2 Desvios Padrão)
        self.df.ta.bbands(length=20, std=2, append=True)

        # NOVO: Calcula o ATR (Average True Range) para volatilidade
        self.df.ta.atr(length=14, append=True)
        
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
        if ema_20 > ema_200:
            tendencia = "ALTA 🟢 (EMA Curta acima da Longa)"
        else:
            tendencia = "BAIXA 🔴 (EMA Curta abaixo da Longa)"
            
        # --- 2. Momento (RSI) ---
        if rsi > 70:
            condicao_rsi = f"SOBRECOMPRADO 🔴 ({rsi:.2f})"
        elif rsi < 30:
            condicao_rsi = f"SOBREVENDIDO 🟢 ({rsi:.2f})"
        else:
            condicao_rsi = f"NEUTRO ⚪ ({rsi:.2f})"

        # --- 3. Volatilidade (Bollinger Bands) ---
        # Adicionamos uma margem minúscula (0.05%) para considerar que "tocou" na banda
        margem = fechamento * 0.0005 
        
        if fechamento <= (bb_inferior + margem):
            condicao_bb = f"TOCANDO BANDA INFERIOR 🟢 (Preço esticado para baixo)"
        elif fechamento >= (bb_superior - margem):
            condicao_bb = f"TOCANDO BANDA SUPERIOR 🔴 (Preço esticado para cima)"
        else:
            condicao_bb = f"DENTRO DAS BANDAS ⚪ (Volatilidade normal)"

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