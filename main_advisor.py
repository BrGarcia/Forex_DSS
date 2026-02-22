import os
import time
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator

def limpar_ecra():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    limpar_ecra()
    print("==================================================")
    print("🚀 FOREX ADVISOR DSS - MOTOR DE ANÁLISE TÉCNICA")
    print("==================================================")

    pares_a_analisar = ["EURUSD"] 

    for par in pares_a_analisar:
        print(f"\n⏳ A iniciar extração de dados para {par}...")
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
            print(analista.gerar_resumo_atual())
            print(estrategista.analisar_e_sugerir())

            # 4. Gerar Gráfico
            nome_ficheiro = f"analise_grafica_{par}.png"
            gerador = ChartGenerator(dados_enriquecidos, par)
            gerador.salvar_grafico(filename=nome_ficheiro)
            print(f"🖼️  Gráfico guardado com sucesso: {nome_ficheiro}")

        except Exception as e:
            print(f"❌ Erro ao analisar {par}: {e}")

        time.sleep(1)

    print("\n==================================================")
    print("✅ CICLO DE ANÁLISE CONCLUÍDO.")
    print("==================================================")

if __name__ == "__main__":
    main()