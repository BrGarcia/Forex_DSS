import sys
import select
from app.forex_bot import ForexBot

def main():
    bot = ForexBot("EURUSD")
    bot.limpar_ecra()
    
    print("==================================================")
    print("🤖 FOREX ADVISOR - MODO RADAR ATIVO")
    print("==================================================")
    print("👉 [ENTER]: Relatório Completo | [S]: Sair\n")

    intervalo = 60
    contador = intervalo 

    while True:
        if contador >= intervalo:
            bot.atualizar_radar()
            contador = 0
        
        # Escuta o teclado sem travar o programa
        tecla, _, _ = select.select([sys.stdin], [], [], 1)
        
        if tecla:
            cmd = sys.stdin.readline().strip().lower()
            if cmd == 's': break
            else:
                bot.exibir_relatorio_completo()
                contador = intervalo # Reinicia o radar logo após o relatório
        else:
            contador += 1

if __name__ == "__main__":
    main()