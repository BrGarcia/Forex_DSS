import mplfinance as mpf
import pandas as pd

class ChartGenerator:
    """
    Recebe um DataFrame enriquecido e desenha o gráfico com EMAs, RSI e Bollinger Bands.
    """
    def __init__(self, df: pd.DataFrame, symbol: str):
        self.df = df
        self.symbol = symbol

    def salvar_grafico(self, filename: str = "grafico_analise.png", velas_visiveis: int = 100):
        df_zoom = self.df.tail(velas_visiveis).copy()
        
        # Pega as colunas das Bandas dinamicamente
        col_bbl = [c for c in self.df.columns if c.startswith('BBL_')][0]
        col_bbu = [c for c in self.df.columns if c.startswith('BBU_')][0]
        
        indicadores_visuais = [
            # 1. EMAs (Linhas contínuas fortes)
            mpf.make_addplot(df_zoom['EMA_20'], color='blue', width=1.5),
            mpf.make_addplot(df_zoom['EMA_200'], color='orange', width=2.0),
            
            # 2. Bollinger Bands (Painel principal, linhas tracejadas, um pouco transparentes)
            mpf.make_addplot(df_zoom[col_bbu], color='gray', linestyle='dashed', width=1.2, alpha=0.7),
            mpf.make_addplot(df_zoom[col_bbl], color='gray', linestyle='dashed', width=1.2, alpha=0.7),
            
            # 3. RSI (Painel separado em baixo)
            mpf.make_addplot(df_zoom['RSI_14'], color='purple', panel=1, ylabel='RSI (14)')
        ]
        
        estilo = mpf.make_mpf_style(base_mpf_style='yahoo', gridstyle=':')
        
        mpf.plot(
            df_zoom,
            type='candle',
            style=estilo,
            addplot=indicadores_visuais,
            volume=False,
            title=f"\nAnálise Técnica: {self.symbol} (M15)",
            ylabel='Preço',
            figsize=(12, 8),
            savefig=filename
        )
