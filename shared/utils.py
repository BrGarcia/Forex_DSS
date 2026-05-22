import pandas as pd
import re
from typing import Optional

def format_currency(value: float, symbol: str = "USD") -> str:
    """Formata valor de preço com precisão de 5 casas decimais (Forex Standard)."""
    return f"{value:.5f}"

def calcular_distancia_pips(p1: float, p2: float, is_jpy: bool = False) -> float:
    """Calcula a diferença em pips entre dois preços."""
    multiplicador = 100 if is_jpy else 10000
    return abs(p1 - p2) * multiplicador


def parse_interval_to_timedelta(intervalo: str) -> pd.Timedelta:
    """Converte intervalos comuns de candles para Timedelta."""
    if not isinstance(intervalo, str) or not intervalo.strip():
        raise ValueError("intervalo deve ser uma string não vazia.")

    value = intervalo.strip().lower()
    match = re.fullmatch(r"(\d+)\s*(m|min|h|d|day)", value)
    if not match:
        raise ValueError(f"Intervalo não suportado: {intervalo}")

    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        raise ValueError("intervalo deve ser maior que zero.")

    if unit in ("m", "min"):
        return pd.Timedelta(minutes=amount)
    if unit == "h":
        return pd.Timedelta(hours=amount)
    return pd.Timedelta(days=amount)


def _ensure_utc_index(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)

    if result.index.tz is None:
        result.index = result.index.tz_localize("UTC")
    else:
        result.index = result.index.tz_convert("UTC")
    return result


def normalizar_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza um DataFrame OHLC sem preencher buracos de mercado.

    A função ordena o índice, remove timestamps duplicados mantendo o último
    candle recebido e descarta linhas OHLC estruturalmente inválidas.
    """
    if df.empty:
        return df.copy()

    result = _ensure_utc_index(df)
    result = result.sort_index()
    result = result[~result.index.duplicated(keep="last")]

    required = {"Open", "High", "Low", "Close"}
    if not required.issubset(result.columns):
        return result

    for column in required:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    valid_mask = (
        result["Open"].notna()
        & result["High"].notna()
        & result["Low"].notna()
        & result["Close"].notna()
        & (result["High"] >= result[["Open", "Close"]].max(axis=1))
        & (result["Low"] <= result[["Open", "Close"]].min(axis=1))
        & (result["High"] >= result["Low"])
    )
    return result.loc[valid_mask].copy()


def validar_ohlc(df: pd.DataFrame, intervalo: Optional[str] = None) -> dict:
    """Valida estrutura OHLC e retorna um relatório de qualidade dos dados."""
    issues: list[str] = []
    required = ["Open", "High", "Low", "Close"]
    missing = [column for column in required if column not in df.columns]

    report = {
        "is_valid": True,
        "issues": issues,
        "rows": int(len(df)),
        "duplicate_timestamps": 0,
        "invalid_ohlc_rows": 0,
        "gap_count": 0,
        "missing_columns": missing,
    }

    if missing:
        issues.append(f"Colunas ausentes: {', '.join(missing)}")

    if not isinstance(df.index, pd.DatetimeIndex):
        issues.append("Índice não é DatetimeIndex.")
        report["is_valid"] = False
        return report

    if not df.index.is_monotonic_increasing:
        issues.append("Índice fora de ordem cronológica.")

    duplicate_count = int(df.index.duplicated().sum())
    report["duplicate_timestamps"] = duplicate_count
    if duplicate_count:
        issues.append(f"{duplicate_count} timestamp(s) duplicado(s).")

    if not missing:
        ohlc = df[required].apply(pd.to_numeric, errors="coerce")
        invalid_mask = (
            ohlc.isna().any(axis=1)
            | (ohlc["High"] < ohlc[["Open", "Close"]].max(axis=1))
            | (ohlc["Low"] > ohlc[["Open", "Close"]].min(axis=1))
            | (ohlc["High"] < ohlc["Low"])
        )
        invalid_count = int(invalid_mask.sum())
        report["invalid_ohlc_rows"] = invalid_count
        if invalid_count:
            issues.append(f"{invalid_count} candle(s) OHLC inválido(s).")

    if intervalo and len(df.index) >= 2:
        expected = parse_interval_to_timedelta(intervalo)
        unique_index = pd.DatetimeIndex(df.index.drop_duplicates()).sort_values()
        diffs = unique_index.to_series().diff().dropna()
        gap_count = int((diffs > expected).sum())
        report["gap_count"] = gap_count
        if gap_count:
            issues.append(f"{gap_count} gap(s) acima do intervalo esperado.")

    report["is_valid"] = not issues
    return report


def filtrar_candles_fechados(
    df: pd.DataFrame,
    intervalo: str,
    agora: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Remove a vela em formação de acordo com o intervalo informado."""
    if df.empty:
        return df.copy()

    result = _ensure_utc_index(df)
    delta = parse_interval_to_timedelta(intervalo)

    if agora is None:
        now = pd.Timestamp.now(tz="UTC")
    else:
        now = pd.Timestamp(agora)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")

    candle_atual_inicio = now.floor(delta)
    return result[result.index < candle_atual_inicio].copy()
