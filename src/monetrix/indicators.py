from typing import cast

import pandas as pd


def compute_indicator_series(
    close_prices: pd.Series,
    indicator: str,
    period: int,
) -> pd.Series | None:
    if period <= 0:
        return None

    if indicator == "SMA":
        return cast(
            pd.Series,
            close_prices.rolling(window=period, min_periods=period).mean(),
        )

    if indicator == "EMA":
        return cast(
            pd.Series,
            close_prices.ewm(span=period, adjust=False, min_periods=period).mean(),
        )

    if indicator == "RSI":
        delta = close_prices.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)

        avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

        rs = cast(pd.Series, avg_gain / avg_loss.replace(0, pd.NA))
        rsi = cast(pd.Series, 100 - (100 / (1 + rs)))

        loss_zero = avg_loss == 0
        gain_zero = avg_gain == 0
        rsi = cast(pd.Series, rsi.mask(loss_zero & ~gain_zero, 100.0))
        rsi = cast(pd.Series, rsi.mask(loss_zero & gain_zero, 50.0))
        return cast(pd.Series, rsi.astype(float))

    return None


def compute_indicator_from_dataframe(
    frame: pd.DataFrame,
    indicator: str,
    period: int,
) -> pd.Series | None:
    if "close" not in frame.columns:
        return None

    close_series = cast(pd.Series, frame["close"])
    series = compute_indicator_series(close_series, indicator, period)
    if series is None:
        return None

    series.name = indicator.lower()
    return series
