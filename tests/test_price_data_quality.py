import unittest

import pandas as pd

from shared.utils import (
    filtrar_candles_fechados,
    normalizar_ohlc,
    parse_interval_to_timedelta,
    validar_ohlc,
)


def make_ohlc(index, rows=None):
    if rows is None:
        rows = [
            {
                "Open": 1.1000,
                "High": 1.1050,
                "Low": 1.0950,
                "Close": 1.1020,
                "Volume": 100,
            }
            for _ in index
        ]
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index))


class TestPriceDataQuality(unittest.TestCase):
    def test_parse_interval_to_timedelta_15m(self):
        self.assertEqual(parse_interval_to_timedelta("15m"), pd.Timedelta(minutes=15))

    def test_parse_interval_to_timedelta_1h(self):
        self.assertEqual(parse_interval_to_timedelta("1h"), pd.Timedelta(hours=1))

    def test_filtrar_candles_fechados_remove_candle_aberto_m15(self):
        index = pd.to_datetime(
            ["2026-01-01 09:30", "2026-01-01 09:45", "2026-01-01 10:00"],
            utc=True,
        )
        df = make_ohlc(index)

        result = filtrar_candles_fechados(
            df,
            "15m",
            agora=pd.Timestamp("2026-01-01 10:07", tz="UTC"),
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result.index[-1], pd.Timestamp("2026-01-01 09:45", tz="UTC"))

    def test_filtrar_candles_fechados_mantem_candle_fechado_exato(self):
        index = pd.to_datetime(
            ["2026-01-01 09:45", "2026-01-01 10:00"],
            utc=True,
        )
        df = make_ohlc(index)

        result = filtrar_candles_fechados(
            df,
            "15m",
            agora=pd.Timestamp("2026-01-01 10:00", tz="UTC"),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result.index[-1], pd.Timestamp("2026-01-01 09:45", tz="UTC"))

    def test_validar_ohlc_detecta_high_menor_que_close(self):
        index = pd.to_datetime(["2026-01-01 09:00"], utc=True)
        df = make_ohlc(
            index,
            [{"Open": 1.1000, "High": 1.1010, "Low": 1.0950, "Close": 1.1020}],
        )

        report = validar_ohlc(df, intervalo="15m")

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["invalid_ohlc_rows"], 1)

    def test_validar_ohlc_detecta_low_maior_que_open(self):
        index = pd.to_datetime(["2026-01-01 09:00"], utc=True)
        df = make_ohlc(
            index,
            [{"Open": 1.1000, "High": 1.1050, "Low": 1.1010, "Close": 1.1020}],
        )

        report = validar_ohlc(df, intervalo="15m")

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["invalid_ohlc_rows"], 1)

    def test_validar_ohlc_detecta_duplicatas(self):
        index = pd.to_datetime(
            ["2026-01-01 09:00", "2026-01-01 09:00"],
            utc=True,
        )
        df = make_ohlc(index)

        report = validar_ohlc(df, intervalo="15m")

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["duplicate_timestamps"], 1)

    def test_validar_ohlc_detecta_gap_m15(self):
        index = pd.to_datetime(
            ["2026-01-01 09:00", "2026-01-01 09:15", "2026-01-01 09:45"],
            utc=True,
        )
        df = make_ohlc(index)

        report = validar_ohlc(df, intervalo="15m")

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["gap_count"], 1)

    def test_normalizar_ohlc_nao_muta_dataframe_original(self):
        index = pd.to_datetime(
            ["2026-01-01 09:15", "2026-01-01 09:00", "2026-01-01 09:00"],
            utc=True,
        )
        df = make_ohlc(index)
        original_index = df.index.copy()

        result = normalizar_ohlc(df)

        self.assertTrue(result.index.is_monotonic_increasing)
        self.assertEqual(len(result), 2)
        pd.testing.assert_index_equal(df.index, original_index)


if __name__ == "__main__":
    unittest.main()
