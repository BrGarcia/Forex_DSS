import sys
import os
from datetime import datetime
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator

class ForexBot:
    def __init__(self, par="EURUSD"):
        self.par = par
        self.ultimo_preco = 0.0

    def limpar_ecra(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def exibir_relatorio_completo(self):
        print(f"\n\n⏳ A gerar relatório estratégico completo para {self.par}...")
        try:
            alimentador = PriceDataFeed(self.par)
            df = alimentador.obter_historico_velas(periodo="20d", intervalo="15m")
            analista = TechnicalAnalyzer(df)
            df_tec = analista.calcular_indicadores()
            estrategista = SignalGenerator(df_tec)
            
            print(analista.gerar_resumo_atual())
            print(estrategista.analisar_e_sugerir())
            
            nome_fig = f"analise_grafica_{self.par}.png"
            ChartGenerator(df_tec, self.par).salvar_grafico(filename=nome_fig)
            print(f"🖼️  Gráfico atualizado: {nome_fig}")
            print("\n👉 Pressione [ENTER] para novo relatório ou aguarde o Radar...")
        except Exception as e:
            print(f"❌ Erro no relatório: {e}")

    def atualizar_radar(self):
        """Lógica do Scanner que fica na linha de fundo"""
        try:
            alimentador = PriceDataFeed(self.par)
            df = alimentador.obter_historico_velas(periodo="5d", intervalo="15m")
            analista = TechnicalAnalyzer(df)
            df_tec = analista.calcular_indicadores()
            
            ultima = df_tec.iloc[-1]
            preco_atual = ultima['Close']
            rsi = ultima['RSI_14']
            
            # Comparação de Preço
            if self.ultimo_preco == 0.0:
                info_p = f"💵 {preco_atual:.5f}"
            else:
                seta = "⬆️" if preco_atual > self.ultimo_preco else "⬇️" if preco_atual < self.ultimo_preco else "⏸️"
                info_p = f"💵 {preco_atual:.5f} ({seta})"

            self.ultimo_preco = preco_atual # Guarda na memória da classe
            
            # Status de oportunidade
            ema20, ema200 = ultima['EMA_20'], ultima['EMA_200']
            status = "⏳"
            if (ema20 > ema200 and rsi <= 45): status = "🔥 COMPRA?"
            elif (ema20 < ema200 and rsi >= 55): status = "🔥 VENDA?"

            hora = datetime.now().strftime("%H:%M:%S")
            sys.stdout.write(f"\r📡 [{hora}] {self.par} | {info_p} | RSI: {rsi:.1f} | Status: {status}      ")
            sys.stdout.flush()
        except:
            pass