import yfinance as yf
import pandas as pd
import requests
from shared.config import Config
from shared.logger import logger
from shared.utils import filtrar_candles_fechados, normalizar_ohlc, validar_ohlc

class PriceDataFeed:
    """
    Classe responsável por extrair dados formatados para o Advisor.
    Agora utiliza TwelveData como provedor prioritário (rápidas as requisições)
    com yfinance mantido como fallback seguro.
    """
    def __init__(self, symbol: str):
        self.symbol_raw = symbol
        self.ticker_yf = f"{symbol}=X" # yfinance: EURUSD=X
        self.ticker_td = f"{symbol[:3]}/{symbol[3:]}" # twelvedata: EUR/USD
        self.td_api_key = Config.TWELVEDATA_API_KEY
        self.use_td = bool(self.td_api_key)
        self.last_quality_report = {}

    def obter_cotacao_atual(self) -> float:
        """
        Retorna apenas o preço de fechamento mais recente de forma extremamente rápida.
        Prioriza o TwelveData, depois websocket local do yf e dps o history.
        """
        if self.use_td:
            try:
                url = f"https://api.twelvedata.com/price?symbol={self.ticker_td}&apikey={self.td_api_key}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                if "price" in data:
                    return round(float(data["price"]), 5)
            except Exception as e:
                logger.warning(f"TwelveData Price falhou para {self.symbol_raw}, indo pro fallback ({e})")

        # Fallback YFINANCE
        ativo = yf.Ticker(self.ticker_yf)
        try:
            # 1. Tenta pegar a info em cache / memória de forma quase instantânea
            preco_atual = ativo.fast_info['lastPrice']
            return round(preco_atual, 5)
        except Exception:
            pass
            
        # 2. Fallback longo (Aprova uma requisição HTTP REST demorada)
        dados = ativo.history(period="1d", interval="1m").tail(1)
        if dados.empty:
            raise ValueError(f"Não foi possível obter dados para {self.symbol_raw}")
        
        preco_atual = dados['Close'].iloc[-1]
        return round(preco_atual, 5)

    def _obter_twelvedata_history(self, periodo="5d", intervalo="15m") -> pd.DataFrame:
        """Busca o histórico na TwelveData e formata no mesmo padrão do yfinance."""
        # Converter intervalo para o parse da TwelveData
        interval_td = intervalo.replace("m", "min").replace("minho", "min").replace("d", "day").replace("h", "h")
        
        try:
            dias = int(periodo.replace("d", ""))
        except:
            dias = 5
        
        # Define outputsize com base no intervalo x dias
        if "15m" in intervalo: limit = dias * 96
        elif "1m" in intervalo: limit = dias * 1440
        elif "1h" in intervalo: limit = dias * 24
        else: limit = 500
        
        limit = min(limit, 5000) # Limite nativo da conta gratis do TwelveData

        url = f"https://api.twelvedata.com/time_series?symbol={self.ticker_td}&interval={interval_td}&outputsize={limit}&apikey={self.td_api_key}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if "values" not in data:
            raise ValueError(f"TwelveData não retornou time_series válido. {data.get('message', '')}")
            
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True) # Garantir ordem cronologica progressiva
        df = df.astype(float)
        
        # Padroniza para alinhar perfeitamente com a infraestrutura pre-existente
        df.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'}, inplace=True)
        df.index.name = 'Date'
        
        return df

    def obter_historico_velas(self, periodo="5d", intervalo="15m") -> pd.DataFrame:
        """
        Retorna o histórico formatado, injetando segurança de falhas/YF fallback.
        """
        df = pd.DataFrame()
        usou_twelvedata = False

        if self.use_td:
            try:
                df = self._obter_twelvedata_history(periodo, intervalo)
                usou_twelvedata = True
            except Exception as e:
                logger.warning(f"TwelveData Series falhou ({e}). Iniciando fallback yfinance.")

        # Try-Fallback massivo para o YFinance padrão caso falte Key ou api crashe
        if df.empty or not usou_twelvedata:
            ativo = yf.Ticker(self.ticker_yf)
            df = ativo.history(period=periodo, interval=intervalo)
            
            # Limpeza
            if 'Dividends' in df.columns:
                df.drop(columns=['Dividends', 'Stock Splits'], inplace=True, errors='ignore')
                
        if not df.empty:
            raw_report = validar_ohlc(df, intervalo=intervalo)
            if not raw_report["is_valid"]:
                logger.warning(
                    f"Qualidade OHLC suspeita para {self.symbol_raw}: "
                    f"{'; '.join(raw_report['issues'])}"
                )

            df = normalizar_ohlc(df)

            if getattr(Config, "USE_CLOSED_CANDLES_ONLY", True):
                before = len(df)
                df = filtrar_candles_fechados(df, intervalo=intervalo)
                removed = before - len(df)
                if removed:
                    logger.debug(
                        f"{self.symbol_raw}: {removed} candle(s) aberto(s) removido(s) "
                        f"para análise em {intervalo}."
                    )

            clean_report = validar_ohlc(df, intervalo=intervalo)
            self.last_quality_report = {
                **clean_report,
                "raw_rows": raw_report["rows"],
                "filtered_rows": len(df),
                "raw_issues": raw_report["issues"],
                "closed_candles_only": getattr(Config, "USE_CLOSED_CANDLES_ONLY", True),
            }
        else:
            self.last_quality_report = {
                "is_valid": False,
                "issues": ["Histórico vazio."],
                "rows": 0,
                "duplicate_timestamps": 0,
                "invalid_ohlc_rows": 0,
                "gap_count": 0,
                "missing_columns": [],
                "raw_rows": 0,
                "filtered_rows": 0,
                "raw_issues": ["Histórico vazio."],
                "closed_candles_only": getattr(Config, "USE_CLOSED_CANDLES_ONLY", True),
            }
                
        return df

    def fazer_backup_diario(self, periodo="59d", intervalo="15m") -> str:
        """Salva um backup do histórico em CSV para uso offline e métricas de longo prazo."""
        df = self.obter_historico_velas(periodo=periodo, intervalo=intervalo)
        data_hoje = pd.Timestamp.now().strftime('%Y%m%d')
        caminho_arquivo = f"data/{self.symbol_raw}_{periodo}_{data_hoje}.csv"
        
        if not df.empty:
            df.to_csv(caminho_arquivo)
            return caminho_arquivo
        return ""

if __name__ == "__main__":
    par = "EURUSD"
    # Modo teste isolado da API
    alimentador = PriceDataFeed(par)
    print(f"Buscando cotação atual (Modo Fast TD={alimentador.use_td}):", alimentador.obter_cotacao_atual())
    df = alimentador.obter_historico_velas(periodo="2d", intervalo="15m")
    print(df.tail())
