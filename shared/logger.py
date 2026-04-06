import logging
import sys
from pathlib import Path

def setup_logger(name="forex_dss", log_file="logs/system.log", level=logging.DEBUG):
    """Configura um logger centralizado que escreve em arquivo e no console."""
    
    # Garante que o diretório de logs existe
    Path(log_file).parent.mkdir(exist_ok=True)
    
    # Formatação das mensagens
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', 
                                datefmt='%Y-%m-%d %H:%M:%S')

    # Handler para Arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Handler para Console (opcional, já que o bot tem sua própria interface CLI)
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evita duplicar handlers se a função for chamada múltiplas vezes
    if not logger.handlers:
        logger.addHandler(file_handler)
        # logger.addHandler(console_handler)

    return logger

# Instância padrão
logger = setup_logger()
