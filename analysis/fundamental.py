import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from shared.logger import logger


# ─────────────────────────────────────────────────────────────
# Mapa de países → código de moeda (ForexFactory usa país/ISO)
# ─────────────────────────────────────────────────────────────
_COUNTRY_TO_CURRENCY = {
    "USD": "USD", "usd": "USD",
    "EUR": "EUR", "eur": "EUR",
    "GBP": "GBP", "gbp": "GBP",
    "JPY": "JPY", "jpy": "JPY",
    "AUD": "AUD", "aud": "AUD",
    "CAD": "CAD", "cad": "CAD",
    "CHF": "CHF", "chf": "CHF",
    "NZD": "NZD", "nzd": "NZD",
    "CNY": "CNY", "cny": "CNY",
    # ForexFactory usa o proprio codigo ISO
}

_HIGH_IMPACT_KEYWORDS = {
    "High", "HIGH", "high"
}


class FundamentalAnalyzer:
    """
    Rastreador de Eventos Econômicos de Alto Impacto.

    Fonte: ForexFactory JSON calendar (gratuito, sem API key, atualizado semanalmente).
    URL  : https://nfs.faireconomy.media/ff_calendar_thisweek.json

    Cache em memória para evitar requisições repetidas durante o mesmo ciclo
    do bot (cache expira a cada 60 minutos).

    Métodos públicos:
      - obter_proximos_eventos() → list[dict]
      - minutos_ate_proximo_evento(par) → int
      - verificar_alerta_proximo(par) → str
      - listar_eventos_do_dia(par) → str  (novo: para uso no relatório completo)
    """

    _FF_URL_WEEK  = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    _FF_URL_NEXT  = "https://nfs.faireconomy.media/ff_calendar_nextweek.json"
    _CACHE_TTL_MIN = 60  # Renova cache a cada 60 minutos

    def __init__(self):
        self._cache: list = []
        self._cache_ts: datetime | None = None

    # ─────────────────────────────────────────────────────────
    # Camada de dados (com cache)
    # ─────────────────────────────────────────────────────────
    def _carregar_calendario(self) -> list:
        """
        Busca o calendário da semana atual no ForexFactory.
        Usa cache em memória para não sobrecarregar a API.
        """
        agora = datetime.now(timezone.utc)

        # Verifica se o cache ainda é válido
        if (
            self._cache
            and self._cache_ts
            and (agora - self._cache_ts).total_seconds() < self._CACHE_TTL_MIN * 60
        ):
            return self._cache

        eventos = []
        for url in [self._FF_URL_WEEK, self._FF_URL_NEXT]:
            try:
                resp = requests.get(url, timeout=8,
                                    headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                dados = resp.json()
                eventos.extend(dados)
                logger.info(f"FundamentalAnalyzer: {len(dados)} eventos carregados de {url}")
            except Exception as e:
                logger.warning(f"FundamentalAnalyzer: falha ao carregar {url} → {e}")

        self._cache    = eventos
        self._cache_ts = agora
        return eventos

    def _parse_eventos(self) -> list[dict]:
        """
        Parseia os eventos brutos do ForexFactory para o formato interno:
          {currency, title, impact, datetime_utc, minutes_to}

        Filtra apenas eventos de HOJE e AMANHÃ para reduzir ruído.
        """
        agora  = datetime.now(timezone.utc)
        limite = agora + timedelta(hours=24)

        raw    = self._carregar_calendario()
        parsed = []

        for ev in raw:
            try:
                # Parse da data com timezone (formato ISO 8601)
                dt_str = ev.get("date", "")
                if not dt_str:
                    continue
                dt = datetime.fromisoformat(dt_str).astimezone(timezone.utc)

                # Só importa eventos futuros nas próximas 24h
                if dt < agora or dt > limite:
                    continue

                impact   = ev.get("impact", "")
                country  = ev.get("country", "")
                currency = _COUNTRY_TO_CURRENCY.get(country, country.upper()[:3])
                title    = ev.get("title", "N/A")
                mins_to  = int((dt - agora).total_seconds() / 60)

                parsed.append({
                    "currency":     currency,
                    "event":        title,
                    "impact":       impact,
                    "datetime_utc": dt,
                    "minutes_to":   mins_to,
                    "time_str":     dt.strftime("%H:%M UTC"),
                })
            except Exception as e:
                logger.debug(f"FundamentalAnalyzer: erro ao parsear evento: {e} | {ev}")

        # Ordena por hora do evento
        parsed.sort(key=lambda x: x["minutes_to"])
        return parsed

    # ─────────────────────────────────────────────────────────
    # API Pública
    # ─────────────────────────────────────────────────────────
    def obter_proximos_eventos(self) -> list:
        """
        Retorna lista de eventos de alto impacto nas próximas 24 horas.
        Fallback para lista vazia se a API estiver indisponível.
        """
        try:
            todos = self._parse_eventos()
            return [e for e in todos if e["impact"] in _HIGH_IMPACT_KEYWORDS]
        except Exception as e:
            logger.error(f"FundamentalAnalyzer.obter_proximos_eventos falhou: {e}")
            return []

    def minutos_ate_proximo_evento(self, par: str) -> int:
        """
        Retorna o mínimo de minutos até o próximo evento de alto impacto
        para as moedas do par.
        Retorna 1000 quando não há eventos relevantes na janela de 24h.
        """
        moeda1 = par[:3].upper()
        moeda2 = par[3:6].upper()
        eventos = self.obter_proximos_eventos()
        mins_list = [
            ev["minutes_to"] for ev in eventos
            if ev["currency"] in (moeda1, moeda2)
        ]
        return int(min(mins_list)) if mins_list else 1000

    def verificar_alerta_proximo(self, par: str) -> str:
        """
        Verifica se há notícia de alto impacto nas próximas 2 horas para o par.
        Retorna string formatada para exibição no radar e no relatório.
        """
        moeda1 = par[:3].upper()
        moeda2 = par[3:6].upper()
        eventos = self.obter_proximos_eventos()
        alertas = []

        for ev in eventos:
            if ev["currency"] in (moeda1, moeda2) and ev["minutes_to"] <= 120:
                urgencia = "🔴" if ev["minutes_to"] <= 15 else "⚠️"
                alertas.append(
                    f"{urgencia} {ev['currency']} — {ev['event']} às {ev['time_str']} "
                    f"(em {ev['minutes_to']}min)"
                )

        return " | ".join(alertas) if alertas else "✅ Sem notícias críticas nas próximas 2h"

    def listar_eventos_do_dia(self, par: str) -> str:
        """
        Retorna um painel completo com todos os eventos de alto impacto
        das próximas 24h para as moedas do par. Usado no relatório completo.
        """
        moeda1 = par[:3].upper()
        moeda2 = par[3:6].upper()

        try:
            todos   = self._parse_eventos()
            filtros = [
                ev for ev in todos
                if ev["currency"] in (moeda1, moeda2)
                and ev["impact"] in _HIGH_IMPACT_KEYWORDS
            ]
        except Exception:
            filtros = []

        if not filtros:
            return "📰 Sem eventos de alto impacto para este par nas próximas 24h."

        linhas = ["📰 CALENDÁRIO ECONÔMICO (Próximas 24h — Alto Impacto)"]
        linhas.append("-" * 50)
        for ev in filtros:
            urgencia = "🔴" if ev["minutes_to"] <= 15 else ("⚠️" if ev["minutes_to"] <= 60 else "📅")
            linhas.append(
                f"  {urgencia} [{ev['time_str']}] {ev['currency']} — {ev['event']} "
                f"(em {ev['minutes_to']}min)"
            )
        linhas.append("-" * 50)
        return "\n".join(linhas)


# ─────────────────────────────────────────────────────────────
# Teste isolado
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    analista = FundamentalAnalyzer()
    print("\n--- ALERTA RÁPIDO ---")
    print(analista.verificar_alerta_proximo("EURUSD"))
    print(f"\nMinutos até próximo evento EUR/USD: {analista.minutos_ate_proximo_evento('EURUSD')}")
    print("\n--- CALENDÁRIO DO DIA ---")
    print(analista.listar_eventos_do_dia("EURUSD"))
