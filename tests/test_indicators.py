import unittest

import pandas as pd

from monetrix.indicators import compute_indicator_from_dataframe, compute_indicator_series


class IndicatorTests(unittest.TestCase):
    def test_sma_computation(self) -> None:
        close = pd.Series([10.0, 20.0, 30.0, 40.0])
        sma = compute_indicator_series(close, "SMA", 2)

        self.assertIsNotNone(sma)
        if sma is None:
            return
        self.assertAlmostEqual(float(sma.iloc[1]), 15.0)
        self.assertAlmostEqual(float(sma.iloc[3]), 35.0)

    def test_ema_computation(self) -> None:
        close = pd.Series([10.0, 20.0, 30.0, 40.0])
        ema = compute_indicator_series(close, "EMA", 2)

        self.assertIsNotNone(ema)
        if ema is None:
            return
        self.assertGreater(float(ema.iloc[3]), 30.0)
        self.assertLess(float(ema.iloc[3]), 40.0)

    def test_rsi_flat_series_is_50(self) -> None:
        close = pd.Series([100.0] * 30)
        rsi = compute_indicator_series(close, "RSI", 14)

        self.assertIsNotNone(rsi)
        if rsi is None:
            return
        last_value = float(rsi.dropna().iloc[-1])
        self.assertAlmostEqual(last_value, 50.0)

    def test_dataframe_helper_uses_close_column(self) -> None:
        frame = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0]})
        series = compute_indicator_from_dataframe(frame, "SMA", 2)

        self.assertIsNotNone(series)
        if series is None:
            return
        self.assertEqual(series.name, "sma")


if __name__ == "__main__":
    unittest.main()
