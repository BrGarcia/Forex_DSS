import sys
import time
from app.forex_bot import ForexBot

# Compatibilidade para Windows e Linux/macOS
if sys.platform == "win32":
    import msvcrt
    def escutar_teclado():
        if msvcrt.kbhit():
            # Limpa o buffer e retorna o comando
            char = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            return char
        return None
else:
    import select
    def escutar_teclado():
        tecla, _, _ = select.select([sys.stdin], [], [], 0.1)
        if tecla:
            return sys.stdin.readline().strip().lower()
        return None

def main():
    bot = ForexBot("EURUSD")
    bot.limpar_ecra()
    
    print("==================================================")
    print("🤖 FOREX ADVISOR - MODO RADAR ATIVO")
    print("==================================================")
    print("👉 [ENTER/QUALQUER TECLA]: Relatório | [S]: Sair\n")

    intervalo = 60
    contador = intervalo 

    while True:
        if contador >= intervalo:
            bot.atualizar_radar()
            contador = 0
        
        # Escuta o teclado sem travar o programa
        cmd = escutar_teclado()
        
        if cmd:
            if cmd == 's': break
            else:
                bot.exibir_relatorio_completo()
                contador = intervalo # Reinicia o radar logo após o relatório
        
        time.sleep(1)
        contador += 1

if __name__ == "__main__":
    main()
    