import sys
import os
from datetime import datetime, timezone
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

    def obter_contexto_sessao(self, df):
        """Identifica a sessão atual e calcula o Range Asiático (00:00 - 08:00 UTC)"""
        agora_utc = datetime.now(timezone.utc)
        hora_utc = agora_utc.hour
        
        # 1. Identificar Sessão Atual
        if 0 <= hora_utc < 8: sessao = "ASIÁTICA 🇯🇵"
        elif 8 <= hora_utc < 13: sessao = "EUROPEIA 🇪🇺 (Londres)"
        elif 13 <= hora_utc < 17: sessao = "SOBREPOSIÇÃO 🇪🇺/🇺🇸 (Overlap)"
        elif 17 <= hora_utc < 21: sessao = "AMERICANA 🇺🇸 (NY)"
        else: sessao = "FECHAMENTO/PRE-ASIA 💤"

        # 2. Calcular Máxima e Mínima da Ásia (00:00 às 08:00 UTC do dia atual)
        # Filtramos o DataFrame para pegar apenas as velas desse intervalo
        df_hoje = df[df.index.date == agora_utc.date()]
        df_asia = df_hoje[(df_hoje.index.hour >= 0) & (df_hoje.index.hour < 8)]
        
        contexto_msg = f"Sessão Atual: {sessao}"
        
        if not df_asia.empty:
            max_asia = df_asia['High'].max()
            min_asia = df_asia['Low'].min()
            preco_atual = df['Close'].iloc[-1]
            
            # 3. Lógica de Viés (Londres abriu?)
            if hora_utc >= 8:
                if preco_atual > max_asia:
                    contexto_msg += f"\n⚠️ Contexto: Preço ACIMA do topo da Ásia ({max_asia:.5f}). Viés Comprador 🟢"
                elif preco_atual < min_asia:
                    contexto_msg += f"\n⚠️ Contexto: Preço ABAIXO do fundo da Ásia ({min_asia:.5f}). Viés Vendedor 🔴"
                else:
                    contexto_msg += f"\n⚠️ Contexto: Preço dentro do Range da Ásia. Consolidação ⏸️"
            else:
                contexto_msg += f"\n📊 Range Ásia em formação: Máx {max_asia:.5f} | Mín {min_asia:.5f}"
        
        return contexto_msg

    def exibir_relatorio_completo(self):
        print(f"\n\n⏳ A gerar relatório estratégico completo para {self.par}...")
        try:
            alimentador = PriceDataFeed(self.par)
            df = alimentador.obter_historico_velas(periodo="5d", intervalo="15m")
            analista = TechnicalAnalyzer(df)
            df_tec = analista.calcular_indicadores()
            estrategista = SignalGenerator(df_tec)
            
            # NOVO: Obtém o contexto de sessão
            contexto = self.obter_contexto_sessao(df_tec)
            
            print("-" * 50)
            print(contexto) # Exibe o contexto no topo do relatório
            print("-" * 50)
            print(analista.gerar_resumo_atual())
            print(estrategista.analisar_e_sugerir())
            
            nome_fig = f"analise_grafica_{self.par}.png"
            ChartGenerator(df_tec, self.par).salvar_grafico(filename=nome_fig)
            print(f"🖼️  Gráfico atualizado: {nome_fig}")
            print("\n👉 Pressione [ENTER] para novo relatório ou aguarde o Radar...")
        except Exception as e:
            print(f"❌ Erro no relatório: {e}")

    def atualizar_radar(self):
            """Lógica do Scanner que fica na linha de fundo do terminal"""
            try:
                # 1. Busca os dados mais recentes
                alimentador = PriceDataFeed(self.par)
                df = alimentador.obter_historico_velas(periodo="2d", intervalo="15m")
                analista = TechnicalAnalyzer(df)
                df_tec = analista.calcular_indicadores()
                
                ultima = df_tec.iloc[-1]
                preco_atual = ultima['Close']   
                rsi = ultima['RSI_14']
                
                # 2. Lógica de Comparação de Preço (Setas)
                if self.ultimo_preco == 0.0:
                    info_p = f"💵 {preco_atual:.5f}"
                else:
                    seta = "⬆️" if preco_atual > self.ultimo_preco else "⬇️" if preco_atual < self.ultimo_preco else "⏸️"
                    info_p = f"💵 {preco_atual:.5f} ({seta})"

                self.ultimo_preco = preco_atual 
                
                # 3. Identificação da Sessão (Horário UTC)
                agora_utc = datetime.now(timezone.utc)
                hora_utc = agora_utc.hour
                
                if 0 <= hora_utc < 8: s_icon = "🇯🇵 ASIA"
                elif 8 <= hora_utc < 13: s_icon = "🇪🇺 LONDRES"
                elif 13 <= hora_utc < 17: s_icon = "🇪🇺/🇺🇸 OVERLAP"
                elif 17 <= hora_utc < 21: s_icon = "🇺🇸 NY"
                else: s_icon = "💤 PRE-ASIA"

                # 4. Impressão da Linha Única
                hora_local = agora_utc.strftime("%H:%M:%S")
                sys.stdout.write(f"\r📡 [{hora_local}] {self.par} | {info_p} | RSI: {rsi:.1f} | SESSÃO: {s_icon}       ")
                sys.stdout.flush()
                
            except Exception as e:
                # Se quiser ver o erro para debugar, pode descomentar a linha abaixo:
                # print(f"Erro no radar: {e}")
                pass
