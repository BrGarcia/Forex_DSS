import sys
import os
from datetime import datetime, timezone
import pytz
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator

from shared.logger import logger

class ForexBot:
    def __init__(self, par="EURUSD"):
        self.par = par
        self.ultimo_preco = 0.0
        logger.info(f"ForexBot inicializado para {self.par}")

    def limpar_ecra(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def obter_contexto_sessao(self, df):
        """Identifica a sessão atual usando fusos horários reais (NY e Londres)"""
        # Fusos horários de referência
        tz_ny = pytz.timezone('America/New_York')
        tz_london = pytz.timezone('Europe/London')
        tz_tokyo = pytz.timezone('Asia/Tokyo')
        
        agora_utc = datetime.now(timezone.utc)
        agora_ny = agora_utc.astimezone(tz_ny)
        agora_london = agora_utc.astimezone(tz_london)
        agora_tokyo = agora_utc.astimezone(tz_tokyo)
        
        # 1. Identificar Sessão Atual (Lógica baseada em horário local do mercado)
        # Londres: 08:00 - 16:00
        # NY: 08:00 - 17:00
        # Tóquio: 09:00 - 18:00 (JST)
        
        is_london = 8 <= agora_london.hour < 16
        is_ny = 8 <= agora_ny.hour < 17
        is_tokyo = 9 <= agora_tokyo.hour < 18
        
        if is_london and is_ny: sessao = "SOBREPOSIÇÃO 🇪🇺/🇺🇸 (Overlap)"
        elif is_london: sessao = "EUROPEIA 🇪🇺 (Londres)"
        elif is_ny: sessao = "AMERICANA 🇺🇸 (NY)"
        elif is_tokyo: sessao = "ASIÁTICA 🇯🇵 (Tóquio)"
        else: sessao = "FECHAMENTO/PRE-ASIA 💤"

        # 2. Calcular Range Asiático (Referência UTC para consistência de dados)
        # Usamos 00:00 às 08:00 UTC como padrão de mercado para o range da Ásia
        df_hoje = df[df.index.date == agora_utc.date()]
        df_asia = df_hoje[(df_hoje.index.hour >= 0) & (df_hoje.index.hour < 8)]
        
        contexto_msg = f"Sessão Atual: {sessao}"
        
        if not df_asia.empty:
            max_asia = df_asia['High'].max()
            min_asia = df_asia['Low'].min()
            preco_atual = df['Close'].iloc[-1]
            
            # 3. Lógica de Viés (Londres abriu?)
            if agora_utc.hour >= 8:
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
            logger.error(f"Erro ao gerar relatório completo para {self.par}: {e}", exc_info=True)
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
                # Agora tratamos o erro explicitamente para evitar falhas silenciosas
                logger.error(f"Erro no Radar para {self.par}: {e}")
                sys.stdout.write(f"\r📡 [{datetime.now().strftime('%H:%M:%S')}] ERRO no Radar: {str(e)[:50]}...       ")
                sys.stdout.flush()
