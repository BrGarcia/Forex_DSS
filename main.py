import os
import time
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator

def limpar_ecra():
    os.system('cls' if os.name == 'nt' else 'clear')

def executar_analise(par="EURUSD"):
    print(f"\n⏳ Consultando o mercado em tempo real para {par}...")
    try:
        # 1. Obter Dados
        alimentador = PriceDataFeed(par)
        dados_brutos = alimentador.obter_historico_velas(periodo="20d", intervalo="15m")

        # 2. Processar Matemática Técnica
        analista = TechnicalAnalyzer(dados_brutos)
        dados_enriquecidos = analista.calcular_indicadores()

        # 3. Gerar Sugestão Estratégica
        estrategista = SignalGenerator(dados_enriquecidos)
        
        # Imprimir Painéis
        limpar_ecra()
        print(analista.gerar_resumo_atual())
        print(estrategista.analisar_e_sugerir())

        # 4. Gerar Gráfico
        nome_ficheiro = f"analise_grafica_{par}.png"
        gerador = ChartGenerator(dados_enriquecidos, par)
        gerador.salvar_grafico(filename=nome_ficheiro)
        print(f"🖼️  Gráfico atualizado com sucesso: {nome_ficheiro}")

    except Exception as e:
        print(f"❌ Erro ao analisar {par}: {e}")

def main():
    limpar_ecra()
    print("==================================================")
    print("🤖 FOREX ADVISOR - MODO BOT INTERATIVO INICIADO")
    print("==================================================")
    print("O seu assistente está online e a aguardar ordens.")
    
    # O Loop Infinito (O coração do Bot)
    while True:
        print("\n" + "="*50)
        print("Opções:")
        print(" [Enter] Atualizar análise agora")
        print(" [S] Sair do programa")
        comando = input("👉 O que deseja fazer? ").strip().lower()

        if comando == 's':
            print("\nDesligando o Advisor... Até logo!")
            break
        elif comando == '':
            executar_analise("EURUSD")
        else:
            print("❌ Comando não reconhecido. Pressione Enter para analisar ou 'S' para sair.")

if __name__ == "__main__":
    main()