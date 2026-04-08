import sys
import os
from datetime import datetime, timezone
import pytz
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from strategy.signal_generator import SignalGenerator
from strategy.percentual_indicator import PercentualIndicator
from analysis.fundamental import FundamentalAnalyzer

from shared.logger import logger
from shared.config import Config

import json

class ForexBot:
    def __init__(self, pares=None):
        self.pares = pares if pares else ["EURUSD"]
        self.ultimos_precos = {par: 0.0 for par in self.pares}
        self.historico_sinais = {}
        
        # Carregar configurações de conta se existirem
        self.conta_config = self._carregar_config_conta()
        self.analista_fundamental = FundamentalAnalyzer()
        
        logger.info(f"ForexBot inicializado para monitorar: {', '.join(self.pares)}")
        
        # Realiza/Verifica backup esporádico do dia (histórico 59d)
        self._verificar_backup_diario()

    def _verificar_backup_diario(self):
        hoje = datetime.now(timezone.utc).strftime("%Y%m%d")
        for par in self.pares:
            arquivo = f"data/{par}_59d_{hoje}.csv"
            if not os.path.exists(arquivo):
                try:
                    logger.info(f"Realizando backup diário 59d para {par}...")
                    alimentador = PriceDataFeed(par)
                    caminho = alimentador.fazer_backup_diario()
                    if caminho:
                        logger.info(f"Backup gravado em {caminho}")
                except Exception as e:
                    logger.error(f"Falha ao realizar backup de {par}: {e}")

    def _carregar_config_conta(self):
        try:
            with open("pairs.json", "r") as f:
                data = json.load(f)
                return data.get("account", {"balance": 1000.0, "risk_percentage": 0.01})
        except:
            return {"balance": 1000.0, "risk_percentage": 0.01}

    def calcular_lote_sugerido(self, stop_loss_dist, par):
        """Calcula o tamanho do lote com base no risco da conta e distância do SL."""
        if stop_loss_dist <= 0: return 0.01
        
        balanço = self.conta_config.get("balance", 1000.0)
        risco_perc = self.conta_config.get("risk_percentage", 0.01)
        valor_em_risco = balanço * risco_perc
        
        # Simplificação: 1 lote padrão = 100.000 unidades
        # 0.01 lote (micro) = 1.000 unidades
        # Em pares com USD como secundário, 1 pip em 0.01 lote vale approx $0.10
        # stop_loss_dist está em preço (ex: 0.0020 para 20 pips)
        
        is_jpy = "JPY" in par
        pip_value = 0.01 if is_jpy else 0.0001
        pips_em_risco = stop_loss_dist / pip_value
        
        if pips_em_risco == 0: return 0.01
        
        # Valor de 1 micro lote (0.01) por pip é aprox $0.10 (para pares XXX/USD)
        # lote = valor_em_risco / (pips * valor_por_pip_do_micro_lote) * 0.01
        # Assumindo $10 por pip em 1.0 lote padrão
        lote = valor_em_risco / (pips_em_risco * 10)
        
        # Aplica o teto configurado de segurança da conta
        lote_final = min(Config.MAX_LOT, max(Config.MIN_LOT, round(lote, 2)))
        return lote_final

    def limpar_ecra(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _obter_sessao_str(self) -> str:
        """Retorna string simples da sessão atual para uso no PercentualIndicator."""
        tz_ny     = pytz.timezone('America/New_York')
        tz_london = pytz.timezone('Europe/London')
        tz_tokyo  = pytz.timezone('Asia/Tokyo')
        agora_utc   = datetime.now(timezone.utc)
        agora_ny    = agora_utc.astimezone(tz_ny)
        agora_london = agora_utc.astimezone(tz_london)
        agora_tokyo  = agora_utc.astimezone(tz_tokyo)
        is_london = 8 <= agora_london.hour < 16
        is_ny     = 8 <= agora_ny.hour    < 17
        is_tokyo  = 9 <= agora_tokyo.hour < 18
        if is_london and is_ny: return "sobreposição"
        if is_london:           return "europeia"
        if is_ny:               return "americana"
        if is_tokyo:            return "asiática"
        return "fechamento"

    def obter_contexto_sessao(self, df, par="EURUSD"):
        """Identifica a sessão atual usando fusos horários reais (NY e Londres)"""
        # ... (mesmo código anterior, mas com o par no log se necessário)
        # [MANTIDO O CÓDIGO DE TIMEZONES]
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

    def exibir_relatorio_completo(self, par=None):
        par_alvo = par if par else self.pares[0]
        print(f"\n\n⏳ A gerar relatório estratégico completo para {par_alvo}...")
        try:
            alimentador = PriceDataFeed(par_alvo)
            df = alimentador.obter_historico_velas(periodo="5d", intervalo="15m")
            analista = TechnicalAnalyzer(df)
            df_tec = analista.calcular_indicadores()
            estrategista = SignalGenerator(df_tec)
            
            # Obtém o contexto de sessão
            contexto = self.obter_contexto_sessao(df_tec, par_alvo)
            
            # Calendário Econômico completo do dia
            calendario = self.analista_fundamental.listar_eventos_do_dia(par_alvo)
            alerta_imediato = self.analista_fundamental.verificar_alerta_proximo(par_alvo)

            print("-" * 50)
            print(contexto)
            print(calendario)
            print(f"🚨 Alerta Imediato: {alerta_imediato}")
            print("-" * 50)
            print(analista.gerar_resumo_atual())

            # ── Indicador Percentual de Confluência ──────────────
            score_result = None
            try:
                session_str  = self._obter_sessao_str()
                mins_to_news = self.analista_fundamental.minutos_ate_proximo_evento(par_alvo)
                indicador    = PercentualIndicator(df_tec)
                score_result = indicador.calcular(session_str, mins_to_news)
                print(indicador.formatar_painel(session_str, mins_to_news))
            except Exception as e:
                logger.warning(f"PercentualIndicator falhou para {par_alvo}: {e}")

            # Ajuste de Lote Dinâmico baseado no sinal (passa score para Modo Tendência)
            resumo_sinal = estrategista.analisar_e_sugerir(score_data=score_result)
            
            # Extrair distância do SL para cálculo de lote real se houver sinal
            ultima = df_tec.iloc[-1]
            atr = ultima.get('ATRr_14', 0.0015)
            lote_real = self.calcular_lote_sugerido(atr * 1.5, par_alvo)
            
            # Substituir o lote padrão no texto do resumo pelo lote calculado
            resumo_sinal = resumo_sinal.replace("QUANTIDADE  : 0.01", f"QUANTIDADE  : {lote_real:.2f}")

            print(resumo_sinal)
            
            nome_fig = f"analise_grafica_{par_alvo}.png"
            ChartGenerator(df_tec, par_alvo).salvar_grafico(filename=nome_fig)
            print(f"🖼️  Gráfico atualizado: {nome_fig}")
            print("\n👉 Pressione [ENTER] para novo relatório ou aguarde o Radar...")
        except Exception as e:
            logger.error(f"Erro ao gerar relatório completo para {par_alvo}: {e}", exc_info=True)
            print(f"❌ Erro no relatório: {e}")

    def atualizar_radar(self):
        """Scanner que percorre todos os pares configurados"""
        linhas    = []
        agora_utc = datetime.now(timezone.utc)
        hora_local = agora_utc.strftime("%H:%M:%S")

        # Sessão é global (não depende do par)
        session_str = self._obter_sessao_str()

        for par in self.pares:
            try:
                # 1. Busca os dados mais recentes
                alimentador = PriceDataFeed(par)
                df          = alimentador.obter_historico_velas(periodo="5d", intervalo="15m")
                analista    = TechnicalAnalyzer(df)
                df_tec      = analista.calcular_indicadores()

                ultima      = df_tec.iloc[-1]
                preco_atual = ultima['Close']
                rsi         = ultima['RSI_14']

                # 2. Comparação de Preço (Setas)
                ultimo_p = self.ultimos_precos.get(par, 0.0)
                if ultimo_p == 0.0:
                    info_p = f"{preco_atual:.5f}"
                else:
                    seta = "↑" if preco_atual > ultimo_p else "↓" if preco_atual < ultimo_p else "→"
                    info_p = f"{preco_atual:.5f} {seta}"
                self.ultimos_precos[par] = preco_atual

                # 3. Alerta Fundamental
                alerta = self.analista_fundamental.verificar_alerta_proximo(par)
                a_icon = "⚠️" if "⚠️" in alerta else ""

                # 4. Score Percentual (calcula PRIMEIRO para alimentar o sinal)
                score_result = None
                score_txt    = ""
                try:
                    mins_to_news = self.analista_fundamental.minutos_ate_proximo_evento(par)
                    indicador    = PercentualIndicator(df_tec)
                    score_result = indicador.calcular(session_str, mins_to_news)
                    score_txt    = f"|📊{score_result['score']:.0f}%"
                except Exception as e:
                    logger.debug(f"Score percentual falhou no radar para {par}: {e}")

                # 5. Sinal com ambos os modos (Sniper + Tendência via score)
                estrategista = SignalGenerator(df_tec)
                resumo       = estrategista.analisar_e_sugerir(score_data=score_result)
                if "COMPRAR" in resumo:  s_status = "🟢"
                elif "VENDER" in resumo: s_status = "🔴"
                else:                    s_status = "⚪"

                linhas.append(f"{par}{a_icon}: {info_p}|{s_status}|RSI:{rsi:.0f}{score_txt}")

            except Exception as e:
                logger.error(f"Erro no Radar para {par}: {e}")
                linhas.append(f"{par}:❌")

        # 5. Impressão Multilinhas ou Linha Única Combinada
        sys.stdout.write("\033[K") # Limpa a linha atual
        output = f"📡 [{hora_local}] " + " | ".join(linhas)
        # Se for muito longo, truncamos ou usamos multilinhas (para CLI vamos manter compacto)
        sys.stdout.write(f"\r{output[:150]}...") 
        sys.stdout.flush()
