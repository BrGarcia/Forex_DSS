import os
import sys
import time
import select
from datetime import datetime
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator

def limpar_ecra():
    os.system('cls' if os.name == 'nt' else 'clear')

def relatorio_completo(par="EURUSD"):
    print(f"\n\n⏳ A gerar relatório estratégico completo para {par}...")
    try:
        alimentador = PriceDataFeed(par)
        dados_brutos = alimentador.obter_historico_velas(periodo="20d", intervalo="15m")
        analista = TechnicalAnalyzer(dados_brutos)
        dados_enriquecidos = analista.calcular_indicadores()
        estrategista = SignalGenerator(dados_enriquecidos)
        
        print(analista.gerar_resumo_atual())
        print(estrategista.analisar_e_sugerir())
        
        nome_ficheiro = f"analise_grafica_{par}.png"
        gerador = ChartGenerator(dados_enriquecidos, par)
        gerador.salvar_grafico(filename=nome_ficheiro)
        print(f"🖼️  Gráfico atualizado: {nome_ficheiro}")
        print("\n👉 Pressione [ENTER] para outro relatório ou aguarde o Radar...")
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")

def radar_rapido(par="EURUSD", preco_anterior=0.0):
    try:
        alimentador = PriceDataFeed(par)
        df = alimentador.obter_historico_velas(periodo="5d", intervalo="15m")
        analista = TechnicalAnalyzer(df)
        df_tec = analista.calcular_indicadores()
        
        ultima_vela = df_tec.iloc[-1]
        preco_atual = ultima_vela['Close']
        rsi = ultima_vela['RSI_14']
        ema_20 = ultima_vela['EMA_20']
        ema_200 = ultima_vela['EMA_200']
        
        tendencia = "ALTA 🟢" if ema_20 > ema_200 else "BAIXA 🔴"
        
        if rsi > 70: rsi_str = f"SOBRECOMPRADO 🔴 ({rsi:.1f})"
        elif rsi < 30: rsi_str = f"SOBREVENDIDO 🟢 ({rsi:.1f})"
        else: rsi_str = f"NEUTRO ⚪ ({rsi:.1f})"
        
        status = "⏳ ESPERAR"
        if (ema_20 > ema_200 and rsi <= 45):
            status = "🔥 PREPARAR COMPRA"
        elif (ema_20 < ema_200 and rsi >= 55):
            status = "🔥 PREPARAR VENDA"

        # --- NOVA LÓGICA DE COMPARAÇÃO DE PREÇOS ---
        if preco_anterior == 0.0:
            info_preco = f"💵 {preco_atual:.5f}" # Primeiro ciclo, não tem histórico
        else:
            if preco_atual > preco_anterior:
                icone = "⬆️"
            elif preco_atual < preco_anterior:
                icone = "⬇️"
            else:
                icone = "⏸️"
            info_preco = f"💵 {preco_atual:.5f} (Ant: {preco_anterior:.5f} {icone})"

        hora = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r📡 [{hora}] {par} | {info_preco} | Tend.: {tendencia} | RSI: {rsi_str} | Status: {status}       ")
        sys.stdout.flush() 
        
        return preco_atual # Devolve o preço atual para ser a memória do próximo ciclo
        
    except Exception:
        return preco_anterior # Se a internet falhar, não perde a memória do preço

def main():
    limpar_ecra()
    print("==================================================")
    print("🤖 FOREX ADVISOR - MODO RADAR (SCANNER ATIVO)")
    print("==================================================")
    print("O bot está a vigiar o mercado silenciosamente.")
    print("👉 Fique atento ao 'Status'. Se aparecer 🔥, pressione [ENTER]!")
    print("👉 Digite 'S' e pressione [ENTER] para sair do sistema.\n")

    intervalo_atualizacao = 60 
    contador_segundos = intervalo_atualizacao 
    
    # A "Memória" do Robô que guarda o preço de 1 minuto atrás
    ultimo_preco_conhecido = 0.0 

    while True:
        if contador_segundos >= intervalo_atualizacao:
            # Envia o preço velho e recebe o novo
            ultimo_preco_conhecido = radar_rapido("EURUSD", ultimo_preco_conhecido)
            contador_segundos = 0
        
        tecla_pressionada, _, _ = select.select([sys.stdin], [], [], 1)
        
        if tecla_pressionada:
            comando = sys.stdin.readline().strip().lower()
            if comando == 's':
                print("\n\nDesligando o Advisor... Até à próxima sessão!")
                break
            else:
                relatorio_completo("EURUSD")
                contador_segundos = intervalo_atualizacao 
        else:
            contador_segundos += 1 

if __name__ == "__main__":
    main()