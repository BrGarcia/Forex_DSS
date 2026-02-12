import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (Segurança)
# Isso procura um arquivo .env na raiz do projeto
load_dotenv()

class Config:
    # --- 1. DEFINIÇÕES DE DIRETÓRIOS ---
    # Identifica a raiz do projeto automaticamente
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"
    
    # Garante que as pastas existam (cria se não existirem)
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # Caminhos específicos
    DB_PATH = DATA_DIR / "trading_system.db"
    LOG_FILE = LOG_DIR / "system.log"

    # --- 2. CREDENCIAIS DA CORRETORA (MetaTrader 5) ---
    # Nunca coloque senhas reais aqui. O código busca do sistema/ambiente.
    MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0)) # Retorna 0 se não achar
    MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER = os.getenv("MT5_SERVER", "")
    
    # --- 3. PARÂMETROS DE TRADING (Estratégia) ---
    SYMBOL = "EURUSD"       # Par padrão
    TIMEFRAME_STR = "M15"   # String para logs
    TIMEFRAME = 15          # Inteiro para cálculos (15 minutos)
    
    # --- 4. GESTÃO DE RISCO (Risk Management) ---
    # Risco máximo por operação (1.0 = 1%, 0.02 = 2% não, cuidado! 0.01 é 1%)
    RISK_PER_TRADE = 0.01   
    
    # Risco:Retorno (Ex: Arrisca 1 para ganhar 2)
    RISK_REWARD_RATIO = 2.0
    
    # Tamanho Mínimo e Máximo de Lote (Proteção)
    MIN_LOT = 0.01
    MAX_LOT = 1.00
    
    # --- 5. CONFIGURAÇÕES DO SISTEMA ---
    # Modo Live = True (Dinheiro Real/Demo na Corretora)
    # Modo Live = False (Backtest ou Simulação Offline)
    LIVE_MODE = False 
    
    # Nível de Log (DEBUG mostra tudo, INFO mostra só o principal)
    LOG_LEVEL = "DEBUG" 

# Validação simples para garantir que carregou
if __name__ == "__main__":
    print(f"Diretório Base: {Config.BASE_DIR}")
    print(f"Banco de Dados: {Config.DB_PATH}")
    print(f"Login MT5 Configurado? {'Sim' if Config.MT5_LOGIN != 0 else 'Não (Verifique o .env)'}")