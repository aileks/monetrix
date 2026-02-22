from collections.abc import Callable, Mapping
from datetime import date
from typing import cast

import pandas as pd


def records_from_payload(payload: object) -> list[dict[str, object]] | None:
    if isinstance(payload, list):
        records: list[dict[str, object]] = []
        for item in payload:
            if isinstance(item, dict):
                records.append(dict(item))
        return records

    if isinstance(payload, Mapping):
        for key in ("data", "results", "quotes", "historical", "symbolsList"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                records: list[dict[str, object]] = []
                for item in candidate:
                    if isinstance(item, dict):
                        records.append(dict(item))
                return records

    return None


def to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().replace("%", "").replace(",", "")
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None

    return None


def normalize_quote_record(record: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(record)

    symbol = normalized.get("symbol")
    ticker = normalized.get("ticker")
    if not isinstance(symbol, str) and isinstance(ticker, str):
        normalized["symbol"] = ticker
    if not isinstance(ticker, str) and isinstance(symbol, str):
        normalized["ticker"] = symbol

    if "changesPercentage" not in normalized:
        percent_value = normalized.get("changePercentage")
        if percent_value is None:
            percent_value = normalized.get("changesPercent")
        parsed_percent = to_float(percent_value)
        if parsed_percent is not None:
            normalized["changesPercentage"] = parsed_percent

    if "change" not in normalized:
        change_value = normalized.get("priceChange")
        if change_value is None:
            change_value = normalized.get("changes")
        parsed_change = to_float(change_value)
        if parsed_change is not None:
            normalized["change"] = parsed_change

    if "changes" not in normalized and "change" in normalized:
        normalized["changes"] = normalized["change"]

    return normalized


def normalize_mover_record(record: Mapping[str, object]) -> dict[str, object]:
    normalized = normalize_quote_record(record)

    if "name" not in normalized:
        for key in ("companyName", "company", "shortName"):
            value = normalized.get(key)
            if isinstance(value, str) and value.strip():
                normalized["name"] = value
                break

    percent_value = to_float(normalized.get("changesPercentage"))
    if percent_value is not None:
        normalized["changesPercentage"] = percent_value

    price_value = to_float(normalized.get("price"))
    if price_value is not None:
        normalized["price"] = price_value

    return normalized


def normalize_forex_record(record: Mapping[str, object], pair: str) -> dict[str, object]:
    normalized = normalize_quote_record(record)

    if "ticker" not in normalized:
        normalized["ticker"] = pair
    if "symbol" not in normalized:
        normalized["symbol"] = pair

    price_value = to_float(normalized.get("price"))
    if "bid" not in normalized and price_value is not None:
        normalized["bid"] = price_value
    if "ask" not in normalized and price_value is not None:
        normalized["ask"] = price_value

    return normalized


def normalize_indicator_timeframe(timeframe: str) -> str:
    normalized = timeframe.strip().lower()
    if normalized in {"daily", "1day"}:
        return "1day"
    return normalized


def extract_indicator_column(df: pd.DataFrame, indicator_key: str) -> str | None:
    candidates = [
        indicator_key,
        indicator_key.upper(),
        indicator_key.lower(),
        "value",
        "indicator",
        "technicalIndicator",
    ]
    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    fallback_columns = [
        col for col in df.columns if col not in {"open", "high", "low", "close", "volume"}
    ]
    if fallback_columns:
        return fallback_columns[0]

    return None


def normalize_historical_dataframe(
    records: list[dict[str, object]],
    start_date: date,
    end_date: date,
    symbol: str,
    on_error: Callable[[str], None] | None = None,
) -> pd.DataFrame | None:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    rename_map = {
        "openPrice": "open",
        "highPrice": "high",
        "lowPrice": "low",
        "closePrice": "close",
        "tradingVolume": "volume",
    }
    for source, target in rename_map.items():
        if source in df.columns and target not in df.columns:
            df[target] = df[source]

    if "date" not in df.columns:
        if on_error is not None:
            on_error(f"historical response missing date column symbol={symbol}")
        return None

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index()

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    df = df[(df.index >= start_ts) & (df.index <= end_ts)]

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = 0

    ordered_columns = ["open", "high", "low", "close", "volume"] + [
        column
        for column in df.columns
        if column not in ["open", "high", "low", "close", "volume"]
    ]
    return cast(pd.DataFrame, df.loc[:, ordered_columns])
