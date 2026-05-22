import sys
import os
from datetime import datetime, timezone
import pytz
from data_feeds.price_api import PriceDataFeed
from analysis.technical import TechnicalAnalyzer
from analysis.charting import ChartGenerator
from analysis.candlestick import detect_patterns
from analysis.levels import (
    build_levels, nearest_level, calculate_asian_range, 
    classify_price_vs_asian_range, detect_level_rejection
)
from analysis.market_regime import classify_market_regime
from analysis.multi_timeframe import MultiTimeframeAnalyzer
from strategy.signal_generator import SignalGenerator
from strategy.percentual_indicator import PercentualIndicator
from analysis.fundamental import FundamentalAnalyzer

from shared.logger import logger
from shared.config import Config

import json
import pandas as pd

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
        """Identifica a sessão atual e o range asiático usando a nova lógica de níveis."""
        tz_ny     = pytz.timezone('America/New_York')
        tz_london = pytz.timezone('Europe/London')
        tz_tokyo  = pytz.timezone('Asia/Tokyo')
        
        agora_utc = datetime.now(timezone.utc)
        agora_ny = agora_utc.astimezone(tz_ny)
        agora_london = agora_utc.astimezone(tz_london)
        agora_tokyo = agora_utc.astimezone(tz_tokyo)
        
        is_london = 8 <= agora_london.hour < 16
        is_ny = 8 <= agora_ny.hour < 17
        is_tokyo = 9 <= agora_tokyo.hour < 18
        
        if is_london and is_ny: sessao = "SOBREPOSIÇÃO 🇪🇺/🇺🇸 (Overlap)"
        elif is_london: sessao = "EUROPEIA 🇪🇺 (Londres)"
        elif is_ny: sessao = "AMERICANA 🇺🇸 (NY)"
        elif is_tokyo: sessao = "ASIÁTICA 🇯🇵 (Tóquio)"
        else: sessao = "FECHAMENTO/PRE-ASIA 💤"

        contexto_msg = f"Sessão Atual: {sessao}"
        
        # Calcular Range Asiático usando o módulo de níveis
        asian_range = calculate_asian_range(df)
        if asian_range.get("has_range"):
            max_asia = asian_range["high"]
            min_asia = asian_range["low"]
            preco_atual = df['Close'].iloc[-1]
            status = classify_price_vs_asian_range(preco_atual, asian_range)
            
            if status == "above_range":
                contexto_msg += f"\n⚠️ Contexto: Preço ACIMA do topo da Ásia ({max_asia:.5f}). Viés Comprador 🟢"
            elif status == "below_range":
                contexto_msg += f"\n⚠️ Contexto: Preço ABAIXO do fundo da Ásia ({min_asia:.5f}). Viés Vendedor 🔴"
            else:
                contexto_msg += f"\n⚠️ Contexto: Preço dentro do Range da Ásia. Consolidação ⏸️"
        
        return contexto_msg

    def _formatar_qualidade_dados(self, quality_report: dict) -> str:
        """Formata o diagnóstico de qualidade dos candles para o relatório."""
        if not quality_report:
            return "Qualidade dos Dados: não informada"

        status = "OK" if quality_report.get("is_valid") else "ATENÇÃO"
        candle_status = "fechado" if quality_report.get("closed_candles_only", True) else "tempo real"
        linhas = [
            f"Qualidade dos Dados: {status}",
            f"Candle analisado  : {candle_status}",
            f"Candles usados    : {quality_report.get('filtered_rows', quality_report.get('rows', 0))}",
        ]

        issues = quality_report.get("raw_issues") or quality_report.get("issues") or []
        if issues:
            linhas.append(f"Alertas          : {'; '.join(issues)}")

        return "\n".join(linhas)

    def _formatar_leitura_candlestick(self, df: pd.DataFrame) -> str:
        """Detecta e formata padrões de candlestick para o relatório."""
        patterns = detect_patterns(df)
        if not patterns:
            return "🕯️  Padrões Candlestick: Nenhum padrão relevante detectado no candle atual."
        
        main_p = patterns[0]
        out = f"🕯️  Padrão Principal  : {main_p.name.upper()} ({main_p.direction}) - Força: {main_p.strength:.2f}\n"
        out += f"📝 Motivo            : {main_p.reason}"
        
        if len(patterns) > 1:
            out += f"\n➕ Outros padrões    : {', '.join([p.name for p in patterns[1:]])}"
            
        return out

    def _formatar_niveis_proximos(self, df: pd.DataFrame) -> str:
        """Identifica níveis de suporte/resistência e reações neles."""
        levels = build_levels(df)
        if not levels:
            return "🎯  Níveis de Preço  : Nenhum nível relevante identificado recentemente."
            
        preco_atual = df['Close'].iloc[-1]
        near = nearest_level(preco_atual, levels)
        
        out = f"🎯  Nível mais Próximo: {near.price:.5f} ({near.kind.upper()})\n"
        
        # Verificar se houve rejeição no último candle
        rejection = detect_level_rejection(df.iloc[-1], near)
        if rejection["rejected"]:
            out += f"⚡ Reação Detectada : REJEIÇÃO {rejection['direction'].upper()} (Força: {rejection['strength']:.2f})"
        else:
            is_jpy = any("JPY" in str(par) for par in self.pares)
            dist_pips = abs(preco_atual - near.price) * (100 if is_jpy else 10000)
            out += f"📍 Distância Atual  : {dist_pips:.1f} pips do nível"
            
        return out

    def _formatar_regime_mercado(self, df: pd.DataFrame, mins_to_news: int) -> str:
        """Classifica e formata o regime de mercado para o relatório."""
        regime = classify_market_regime(df, mins_to_news)
        
        icon = {
            "strong_trend": "🚀",
            "weak_trend": "📈",
            "range": "↔️",
            "compression": "🗜️",
            "high_volatility": "🌪️",
            "pre_news": "📢"
        }.get(regime.label, "❓")
        
        out = f"{icon}  Regime de Mercado: {regime.label.upper()}\n"
        out += f"📊 Tendência        : {regime.trend_direction.upper()} (Força: {regime.trend_strength:.2f})\n"
        out += f"🌪️ Volatilidade      : {regime.volatility_label.upper()}\n"
        out += f"📝 Justificativa    : {regime.reason}"
        
        return out

    def _formatar_mtf(self, df_m15: pd.DataFrame, par: str) -> str:
        """Executa e formata a análise multi-timeframe."""
        try:
            alimentador = PriceDataFeed(par)
            # Buscar dados H1 e H4
            df_h1 = alimentador.obter_historico_velas(periodo="5d", intervalo="1h")
            df_h4 = alimentador.obter_historico_velas(periodo="10d", intervalo="4h")
            
            # Preparar indicadores
            df_h1 = TechnicalAnalyzer(df_h1).calcular_indicadores()
            df_h4 = TechnicalAnalyzer(df_h4).calcular_indicadores()
            
            analyzer = MultiTimeframeAnalyzer({"15m": df_m15, "1h": df_h1, "4h": df_h4})
            mtf = analyzer.run()
            
            icon = "✅" if "aligned" in mtf.alignment else "⚠️"
            out = f"{icon}  MTF Alignment     : {mtf.alignment.upper()} (Score: {mtf.alignment_score:.2f})\n"
            for tf, analysis in mtf.analyses.items():
                out += f"   • {tf.upper()}: {analysis.trend.upper()} | {analysis.regime}\n"
            return out.strip()
        except Exception as e:
            return f"⚠️  MTF Analysis    : Falha ao carregar timeframes superiores ({e})"

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
            print(self._formatar_qualidade_dados(alimentador.last_quality_report))
            print("-" * 50)
            print(contexto)
            print(calendario)
            print(f"🚨 Alerta Imediato: {alerta_imediato}")
            print("-" * 50)
            print(self._formatar_leitura_candlestick(df_tec))
            print("-" * 50)
            print(self._formatar_niveis_proximos(df_tec))
            print("-" * 50)
            print(self._formatar_regime_mercado(df_tec, self.analista_fundamental.minutos_ate_proximo_evento(par_alvo)))
            print("-" * 50)
            print(self._formatar_mtf(df_tec, par_alvo))
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
            levels_for_chart = build_levels(df_tec)
            ChartGenerator(df_tec, par_alvo).salvar_grafico(filename=nome_fig, levels=levels_for_chart)
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
