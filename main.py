import time
import sys
import signal
from shared.config import Config
from shared.logger import setup_logger
from bot_technical_trader.main_trader import TechnicalTrader

# 1. Configuração Inicial de Logs
# O logger "root" que vai capturar eventos gerais do sistema
log = setup_logger("MainSystem")

def graceful_exit(signum, frame):
    """
    Função para desligar o robô com segurança quando você aperta CTRL+C.
    Evita que o bot morra no meio de uma operação de envio de ordem.
    """
    log.warning("Recebido sinal de encerramento (CTRL+C). Fechando conexões...")
    # Aqui você poderia adicionar lógica para fechar posições abertas se quisesse
    sys.exit(0)

def main():
    log.info(f"--- INICIANDO FOREX ADVISOR [Versão: {Config.VERSION}] ---")
    log.info(f"Modo: {'LIVE TRADING' if Config.LIVE_MODE else 'PAPER TRADING'}")
    
    # 2. Instancia o Bot Técnico (O "Operário")
    # A classe TechnicalTrader deve estar definida dentro da pasta do bot
    trader = TechnicalTrader()
    
    # 3. Tentativa de Conexão Inicial (MetaTrader 5)
    if not trader.connect():
        log.critical("Falha crítica ao conectar com a corretora. Encerrando.")
        sys.exit(1)
        
    log.info("Sistema conectado e pronto. Iniciando loop principal...")

    # 4. O Loop Infinito (Heartbeat)
    while True:
        try:
            # Verifica se é hora de operar (ex: mercado está aberto?)
            # Esta lógica pode estar dentro do trader ou aqui fora
            
            # --- EXECUTA A ESTRATÉGIA ---
            trader.run_cycle() 
            
            # --- ESPERA INTELIGENTE ---
            # O bot não precisa rodar a cada milissegundo. 
            # Se o timeframe é M15, ele pode dormir alguns segundos.
            time.sleep(1) 

        except KeyboardInterrupt:
            graceful_exit(None, None)
            
        except Exception as e:
            # Se der um erro não tratado, o bot não deve fechar sozinho,
            # ele deve registrar o erro e tentar continuar (ou parar se for grave).
            log.error(f"Erro não tratado no Loop Principal: {e}", exc_info=True)
            time.sleep(5) # Espera um pouco antes de tentar de novo para não floodar o log

if __name__ == "__main__":
    # Registra o sinal de saída (CTRL+C)
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)
    
    main()