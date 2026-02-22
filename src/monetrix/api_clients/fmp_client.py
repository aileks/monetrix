import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import pandas as pd
import requests
import streamlit as st

from monetrix.api_clients.fmp_parsers import (
    extract_indicator_column,
    normalize_forex_record,
    normalize_historical_dataframe,
    normalize_indicator_timeframe,
    normalize_mover_record,
    normalize_quote_record,
    records_from_payload,
)

ErrorCategory = Literal[
    "auth",
    "plan",
    "rate_limit",
    "not_found",
    "upstream",
    "network",
    "decode",
    "empty",
    "invalid_input",
    "config",
]

FMP_BASE_URL = "https://financialmodelingprep.com/stable"
REQUEST_TIMEOUT_SECONDS = 10
LEGACY_ENDPOINT_MARKER = "legacy endpoint"


@dataclass
class FMPResponse:
    ok: bool
    data: object | None = None
    category: ErrorCategory | None = None
    status_code: int | None = None
    message: str = ""


def _log(message: str) -> None:
    print(f"[fmp_client] {message}")


def _ok(data: object, status_code: int | None = None) -> FMPResponse:
    return FMPResponse(ok=True, data=data, status_code=status_code)


def _fail(
    category: ErrorCategory,
    message: str,
    status_code: int | None = None,
    data: object | None = None,
) -> FMPResponse:
    return FMPResponse(
        ok=False,
        data=data,
        category=category,
        status_code=status_code,
        message=message,
    )


def _build_url(endpoint: str, api_key: str, **params: object) -> str:
    query: dict[str, str] = {"apikey": api_key}
    for key, value in params.items():
        if value is None:
            continue
        query[key] = str(value)

    encoded_query = urlencode(query)
    normalized_endpoint = endpoint.lstrip("/")
    return f"{FMP_BASE_URL}/{normalized_endpoint}?{encoded_query}"


def _redact_api_key(url: str) -> str:
    parsed = urlparse(url)
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    redacted_items = []
    for key, value in query_items:
        redacted_value = "***" if key.lower() == "apikey" else value
        redacted_items.append((key, redacted_value))

    redacted_query = urlencode(redacted_items)
    return urlunparse(parsed._replace(query=redacted_query))


def _status_to_category(status_code: int | None) -> ErrorCategory:
    if status_code == 402:
        return "plan"
    if status_code in {401, 403}:
        return "auth"
    if status_code == 429:
        return "rate_limit"
    if status_code == 404:
        return "not_found"
    return "upstream"


def _extract_api_error_message(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None

    for key in ("Error Message", "error", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _message_to_category(message: str) -> ErrorCategory:
    normalized = message.lower()
    if LEGACY_ENDPOINT_MARKER in normalized:
        return "auth"
    if "subscription" in normalized or "upgrade" in normalized:
        return "plan"
    if "invalid api key" in normalized or "unauthorized" in normalized:
        return "auth"
    if "rate limit" in normalized:
        return "rate_limit"
    if "not found" in normalized:
        return "not_found"
    return "upstream"


def _request_json(url: str) -> FMPResponse:
    redacted_url = _redact_api_key(url)

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        _log(f"network error url={redacted_url}: {exc}")
        return _fail(
            "network",
            "Network error while contacting market data provider.",
        )

    status_code = response.status_code

    try:
        payload = response.json()
    except json.JSONDecodeError:
        body_snippet = " ".join(response.text.split())[:220]
        _log(
            "json decode error "
            f"status={status_code} url={redacted_url} body={body_snippet}"
        )

        category = "decode"
        message = "Received invalid JSON from market data provider."
        append_body_snippet = bool(body_snippet)
        if status_code >= 400:
            category = _status_to_category(status_code)
            if status_code == 402:
                message = (
                    "Technical indicators require a higher FMP subscription tier."
                )
                append_body_snippet = False
            elif body_snippet:
                message = body_snippet
                append_body_snippet = False

        if append_body_snippet:
            message = f"{message} {body_snippet}".strip()

        return _fail(
            category,
            message,
            status_code=status_code,
        )

    provider_error = _extract_api_error_message(payload)
    if status_code >= 400 or provider_error:
        category = _status_to_category(status_code)
        if provider_error and category == "upstream":
            category = _message_to_category(provider_error)

        message = provider_error or "Request to market data provider failed."
        _log(
            f"api error category={category} status={status_code} "
            f"url={redacted_url} message={message}"
        )
        return _fail(
            category,
            message,
            status_code=status_code,
            data=payload,
        )

    return _ok(payload, status_code=status_code)


def format_api_error(result: FMPResponse, fallback: str) -> str:
    if result.ok:
        return fallback

    legacy_auth_error = (
        result.category == "auth" and LEGACY_ENDPOINT_MARKER in result.message.lower()
    )

    category_messages: dict[str, str] = {
        "auth": "Market data API key is invalid or unauthorized.",
        "plan": "Market data endpoint requires a higher FMP subscription tier.",
        "rate_limit": "Market data API limit reached. Try again shortly.",
        "not_found": "Requested market data endpoint was not found.",
        "network": "Network error while reaching the market data provider.",
        "decode": "Market data provider returned an invalid response format.",
        "empty": "No market data returned for this request.",
        "invalid_input": "Invalid input for market data request.",
        "config": "Market data API key is missing or invalidly configured.",
        "upstream": fallback,
    }

    if legacy_auth_error:
        message = (
            "Market data API key is unauthorized for legacy endpoints. "
            "Use stable endpoint routes and verify deployed version."
        )
    else:
        message = category_messages.get(result.category or "", fallback)

    hints: list[str] = []
    if result.status_code is not None:
        hints.append(f"status {result.status_code}")

    if result.message:
        detail = " ".join(result.message.split())
        hints.append(detail[:140])

    if hints:
        return f"{message} ({'; '.join(hints)})"

    return message


@st.cache_data(ttl=900)
def get_stock_quote(symbol: str, api_key: str) -> FMPResponse:
    """Fetches the stock quote for a given symbol from the FMP API."""
    if not api_key:
        _log("missing API key for get_stock_quote")
        return _fail("config", "API key was not provided.")

    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        _log("missing stock symbol for get_stock_quote")
        return _fail("invalid_input", "Stock symbol was not provided.")

    url = _build_url("quote", api_key, symbol=normalized_symbol)
    response = _request_json(url)
    if not response.ok:
        return response

    records = records_from_payload(response.data)
    if records is None:
        if isinstance(response.data, Mapping):
            return _ok(normalize_quote_record(response.data), status_code=response.status_code)

        _log(f"unexpected quote response symbol={normalized_symbol} payload={response.data}")
        return _fail(
            "upstream",
            f"Unexpected response format for quote {normalized_symbol}.",
            status_code=response.status_code,
            data=response.data,
        )

    if not records:
        return _fail(
            "empty",
            f"No quote data returned for {normalized_symbol}.",
            status_code=response.status_code,
        )

    return _ok(normalize_quote_record(records[0]), status_code=response.status_code)


@st.cache_data(ttl=3600)
def get_historical_price_data(
    symbol: str,
    api_key: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame | pd.Series | None:
    """Fetches historical daily price data from FMP API for a given date range."""
    if not api_key:
        _log("missing API key for get_historical_price_data")
        return None

    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        _log("missing stock symbol for get_historical_price_data")
        return None

    url = _build_url("historical-price-eod/full", api_key, symbol=normalized_symbol)
    response = _request_json(url)
    if not response.ok:
        _log(
            f"historical request failed symbol={normalized_symbol} "
            f"category={response.category} status={response.status_code}"
        )
        return None

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected historical response symbol={normalized_symbol}: {response.data}")
        return None

    return normalize_historical_dataframe(
        records,
        start_date=start_date,
        end_date=end_date,
        symbol=normalized_symbol,
        on_error=_log,
    )


@st.cache_data(ttl=600)
def get_market_winners(api_key: str) -> FMPResponse:
    """Fetches the top stock market gainers from the FMP API."""
    if not api_key:
        _log("missing API key for get_market_winners")
        return _fail("config", "API key was not provided for market gainers.")

    url = _build_url("biggest-gainers", api_key)
    response = _request_json(url)
    if not response.ok:
        return response

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected gainers response payload={response.data}")
        return _fail(
            "upstream",
            "Unexpected response format for market gainers.",
            status_code=response.status_code,
            data=response.data,
        )

    normalized = [normalize_mover_record(record) for record in records]
    return _ok(normalized, status_code=response.status_code)


@st.cache_data(ttl=600)
def get_market_losers(api_key: str) -> FMPResponse:
    """Fetches the top stock market losers from the FMP API."""
    if not api_key:
        _log("missing API key for get_market_losers")
        return _fail("config", "API key was not provided for market losers.")

    url = _build_url("biggest-losers", api_key)
    response = _request_json(url)
    if not response.ok:
        return response

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected losers response payload={response.data}")
        return _fail(
            "upstream",
            "Unexpected response format for market losers.",
            status_code=response.status_code,
            data=response.data,
        )

    normalized = [normalize_mover_record(record) for record in records]
    return _ok(normalized, status_code=response.status_code)


@st.cache_data(ttl=3600)
def get_technical_indicator_result(
    api_key: str,
    symbol: str,
    period: int,
    indicator_type: str,
    timeframe: str = "daily",
) -> FMPResponse:
    """Fetches technical indicator data from FMP API."""
    if not api_key or not symbol or period <= 0 or not indicator_type:
        _log("missing required parameters for get_technical_indicator")
        return _fail("invalid_input", "Missing required parameters for indicator request.")

    normalized_symbol = symbol.strip().upper()
    indicator_key = indicator_type.strip().lower()
    normalized_timeframe = normalize_indicator_timeframe(timeframe)

    url = _build_url(
        f"technical-indicators/{indicator_key}",
        api_key,
        symbol=normalized_symbol,
        periodLength=period,
        timeframe=normalized_timeframe,
    )

    response = _request_json(url)
    if not response.ok and response.category in {"not_found", "upstream"}:
        fallback_url = _build_url(
            f"technical-indicators/{indicator_key}",
            api_key,
            symbol=normalized_symbol,
            period=period,
            timeframe=normalized_timeframe,
        )
        fallback_response = _request_json(fallback_url)
        if fallback_response.ok:
            response = fallback_response

    if not response.ok:
        _log(
            f"indicator request failed symbol={normalized_symbol} indicator={indicator_key} "
            f"category={response.category} status={response.status_code}"
        )
        return response

    records = records_from_payload(response.data)
    if records is None:
        _log(
            f"unexpected indicator response symbol={normalized_symbol} "
            f"indicator={indicator_key}: {response.data}"
        )
        return _fail(
            "upstream",
            f"Unexpected response format for indicator {indicator_key}.",
            status_code=response.status_code,
            data=response.data,
        )

    if not records:
        _log(
            f"empty indicator response symbol={normalized_symbol} "
            f"indicator={indicator_key} period={period}"
        )
        return _fail(
            "empty",
            f"No data returned for indicator {indicator_key} period {period}.",
            status_code=response.status_code,
        )

    df = pd.DataFrame(records)
    if "date" not in df.columns:
        _log(
            f"indicator response missing date symbol={normalized_symbol} "
            f"indicator={indicator_key}"
        )
        return _fail(
            "upstream",
            f"Indicator response missing date column for {indicator_key}.",
            status_code=response.status_code,
            data=response.data,
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index()

    indicator_column = extract_indicator_column(df, indicator_key)
    if indicator_column is None:
        _log(
            f"indicator column missing symbol={normalized_symbol} "
            f"indicator={indicator_key}"
        )
        return _fail(
            "upstream",
            f"Indicator column missing for {indicator_key}.",
            status_code=response.status_code,
            data=response.data,
        )

    return _ok(df[indicator_column], status_code=response.status_code)


@st.cache_data(ttl=3600)
def get_technical_indicator(
    api_key: str,
    symbol: str,
    period: int,
    indicator_type: str,
    timeframe: str = "daily",
) -> pd.Series | pd.DataFrame | None:
    """Backwards-compatible wrapper for indicator series data."""
    result = get_technical_indicator_result(
        api_key,
        symbol,
        period,
        indicator_type,
        timeframe,
    )
    if result.ok and isinstance(result.data, (pd.Series, pd.DataFrame)):
        return result.data
    return None


@st.cache_data(ttl=600)
def get_multiple_stock_quotes(api_key: str, symbols: list[str]) -> FMPResponse:
    """Fetches stock quotes for multiple symbols in a single API call."""
    if not api_key:
        _log("missing API key for get_multiple_stock_quotes")
        return _fail("config", "API key not provided for multiple quotes.")

    normalized_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
    if not normalized_symbols:
        return _ok([])

    symbols_str = ",".join(normalized_symbols)
    url = _build_url("batch-quote", api_key, symbols=symbols_str)

    response = _request_json(url)
    if not response.ok:
        return response

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected multiple quote response symbols={symbols_str}: {response.data}")
        return _fail(
            "upstream",
            f"Unexpected response format for quotes {symbols_str}.",
            status_code=response.status_code,
            data=response.data,
        )

    normalized = [normalize_quote_record(record) for record in records]
    return _ok(normalized, status_code=response.status_code)


@st.cache_data(ttl=3600)
def get_forex_pairs_list(api_key: str) -> FMPResponse:
    """Fetches available Forex currency pairs from FMP API."""
    if not api_key:
        _log("missing API key for get_forex_pairs_list")
        return _fail("config", "API key not provided for Forex pairs list.")

    url = _build_url("forex-list", api_key)
    response = _request_json(url)
    if not response.ok:
        return response

    if isinstance(response.data, list) and all(isinstance(item, str) for item in response.data):
        return _ok(sorted(response.data), status_code=response.status_code)

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected forex pairs response payload={response.data}")
        return _fail(
            "upstream",
            "Unexpected response format for Forex pairs list.",
            status_code=response.status_code,
            data=response.data,
        )

    pairs: list[str] = []
    for record in records:
        for key in ("symbol", "ticker", "currencyPair", "pair"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                pairs.append(value.strip().upper())
                break

    unique_pairs = sorted(set(pairs))
    if unique_pairs:
        return _ok(unique_pairs, status_code=response.status_code)

    _log(f"unable to parse forex pairs from payload={response.data}")
    return _fail(
        "upstream",
        "Could not parse Forex pair list from provider response.",
        status_code=response.status_code,
        data=response.data,
    )


@st.cache_data(ttl=60)
def get_forex_quote(api_key: str, pair: str) -> FMPResponse:
    """Fetches the latest quote for a specific Forex pair."""
    if not api_key:
        _log("missing API key for get_forex_quote")
        return _fail("config", "API key not provided for Forex quote.")

    normalized_pair = pair.strip().upper()
    if not normalized_pair:
        _log("missing pair for get_forex_quote")
        return _fail("invalid_input", "Forex pair was not provided.")

    url = _build_url("quote", api_key, symbol=normalized_pair)
    response = _request_json(url)
    if not response.ok:
        return response

    records = records_from_payload(response.data)
    if records is None:
        _log(f"unexpected forex quote response pair={normalized_pair} payload={response.data}")
        return _fail(
            "upstream",
            f"Unexpected response format for Forex quote {normalized_pair}.",
            status_code=response.status_code,
            data=response.data,
        )

    if not records:
        return _fail(
            "empty",
            f"No Forex quote data returned for {normalized_pair}.",
            status_code=response.status_code,
        )

    normalized = [normalize_forex_record(record, normalized_pair) for record in records]
    return _ok(normalized, status_code=response.status_code)
