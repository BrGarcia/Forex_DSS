import yfinance as yf
import pandas as pd

class PriceDataFeed:
    """
    Classe responsável por conectar na API do Yahoo Finance
    e extrair dados formatados para o nosso Advisor.
    """
    def __init__(self, symbol: str):
        # No Yahoo Finance, moedas precisam do sufixo "=X"
        # Exemplo: EURUSD vira EURUSD=X
        self.symbol_raw = symbol
        self.ticker = f"{symbol}=X"

    def obter_cotacao_atual(self) -> float:
        """
        Retorna apenas o preço de fechamento mais recente.
        """
        ativo = yf.Ticker(self.ticker)
        # Puxa o gráfico de 1 dia, em velas de 1 minuto
        dados = ativo.history(period="1d", interval="1m")
        
        if dados.empty:
            raise ValueError(f"Não foi possível obter dados para {self.symbol_raw}")
            
        # Pega o preço de fechamento ('Close') da última linha ([-1])
        preco_atual = dados['Close'].iloc[-1]
        return round(preco_atual, 5)

    def obter_historico_velas(self, periodo="5d", intervalo="15m") -> pd.DataFrame:
        """
        Retorna o histórico completo (Open, High, Low, Close, Volume).
        Esta será a base para a nossa Análise Técnica futura.
        """
        ativo = yf.Ticker(self.ticker)
        df = ativo.history(period=periodo, interval=intervalo)
        
        # Limpeza rápida: remover colunas que o yfinance manda mas não usamos no Forex
        if 'Dividends' in df.columns:
            df.drop(columns=['Dividends', 'Stock Splits'], inplace=True, errors='ignore')
            
        return df

# ==========================================
# ÁREA DE TESTE TANGÍVEL (Execução Direta)
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO TESTE DO DEGRAU 1 (API YFINANCE) ---")
    
    par = "EURUSD"
    alimentador = PriceDataFeed(par)
    
    # 1. Testando a Cotação Atual
    try:
        preco = alimentador.obter_cotacao_atual()
        print(f"\n✅ SUCESSO! A cotação atual do {par} é: {preco}")
        
        # 2. Testando o Histórico de Velas
        print("\nBaixando histórico de velas (Últimos 5 dias, velas de 15 min)...")
        grafico = alimentador.obter_historico_velas()
        
        print("\nVisualização das últimas 3 velas capturadas:")
        print(grafico.tail(3))
        
    except Exception as e:
        print(f"\n❌ ERRO ao conectar com a API: {e}")
        
    print("\n--- TESTE CONCLUÍDO ---")