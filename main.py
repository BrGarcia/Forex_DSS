import sys
import time
import json
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

def carregar_pares():
    try:
        with open("pairs.json", "r") as f:
            data = json.load(f)
            return data.get("pairs", ["EURUSD"])
    except:
        return ["EURUSD"]

def main():
    lista_pares = carregar_pares()
    bot = ForexBot(pares=lista_pares)
    bot.limpar_ecra()
    
    print("==================================================")
    print("🤖 FOREX ADVISOR - MODO MULTI-RADAR ATIVO")
    print(f"Ativos: {', '.join(lista_pares)}")
    print("==================================================")
    print("👉 [1-9]: Relatório do Par | [S]: Sair\n")

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
            elif cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(lista_pares):
                    bot.exibir_relatorio_completo(par=lista_pares[idx])
                    contador = intervalo # Reinicia o radar logo após o relatório
            else:
                # Se pressionar qualquer outra tecla (como ENTER), mostra o primeiro
                bot.exibir_relatorio_completo()
                contador = intervalo
        
        time.sleep(1)
        contador += 1

if __name__ == "__main__":
    main()
    