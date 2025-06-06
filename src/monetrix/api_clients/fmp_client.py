import json
from datetime import date
from typing import Any, Optional

import pandas as pd
import requests
import streamlit as st


@st.cache_data(ttl=900)
def get_stock_quote(symbol: str, api_key: str) -> dict[str, Any] | None:
    """Fetches the stock quote for a given symbol from the FMP API."""
    if not api_key:
        print("Error: API key was not provided to get_stock_quote.")
        return None
    if not symbol:
        print("Error: Stock symbol was not provided.")
        return None

    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # FMP often returns a list, even for a single quote
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict):
            return data  # Handle cases where it might return a dict directly
        else:
            # Log unexpected format, return None
            print(f"Warning: Unexpected response format for {symbol}: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for {symbol}.")
        print(f"Response text: {response.text}")  # type: ignore
        return None


@st.cache_data(ttl=3600)
def get_historical_price_data(
    symbol: str, api_key: str, start_date: date, end_date: date
) -> Optional[pd.DataFrame | pd.Series]:
    """Fetches historical daily price data from FMP API for a given date range."""
    if not api_key:
        print("Error: API key was not provided for historical data.")
        return None
    if not symbol:
        print("Error: Stock symbol was not provided for historical data.")
        return None

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date_str}&to={end_date_str}&apikey={api_key}"
    print(f"Requesting URL: {url}")

    try:
        print(
            f"Cache miss/fetch: Historical data for {symbol} ({start_date_str} to {end_date_str})"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if (
            isinstance(data, dict)
            and "historical" in data
            and isinstance(data["historical"], list)
        ):
            if not data["historical"]:
                # Return empty DataFrame instead of None, easier to handle in UI
                return pd.DataFrame()

            df = pd.DataFrame(data["historical"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            df = df.sort_index()

            # Ensure standard columns exist, fill missing numerics with 0
            for col in ["open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    df[col] = 0

            # Reorder columns
            df = df[
                ["open", "high", "low", "close", "volume"]
                + [
                    c
                    for c in df.columns
                    if c not in ["open", "high", "low", "close", "volume"]
                ]
            ]

            return df
        else:
            print(f"Unexpected historical data format for {symbol}: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        try:
            print(f"API Error Response: {response.text}")  # type: ignore
        except:  # noqa: E722
            pass  # Ignore if response object doesn't exist
        return None
    except json.JSONDecodeError:
        print(
            f"Error decoding historical JSON for {symbol}. Response: {response.text}"  # type: ignore
        )
        return None
    except Exception as e:
        print(f"Error processing historical data for {symbol}: {e}")
        return None


@st.cache_data(ttl=600)
def get_market_winners(api_key: str) -> list[dict[str, Any]] | None:
    """Fetches the top stock market gainers from the FMP API."""
    if not api_key:
        print("Error: API key was not provided for market gainers.")
        return None

    url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return data
        else:
            print(f"Warning: Unexpected response format for market gainers: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching market gainers: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response for market gainers.")
        print(f"Response text: {response.text}")  # type: ignore
        return None


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_market_losers(api_key: str) -> list[dict[str, Any]] | None:
    """Fetches the top stock market losers from the FMP API."""
    if not api_key:
        print("Error: API key was not provided for market losers.")
        return None

    url = (
        f"https://financialmodelingprep.com/api/v3/stock_market/losers?apikey={api_key}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return data
        else:
            print(f"Warning: Unexpected response format for market losers: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching market losers: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response for market losers.")
        print(f"Response text: {response.text}")  # type: ignore
        return None


@st.cache_data(ttl=3600)
def get_technical_indicator(
    api_key: str,
    symbol: str,
    period: int,
    indicator_type: str,  # 'sma', 'ema', 'rsi', etc.
    timeframe: str = "daily",  # FMP also supports intraday like '1min', '5min', '1hour', etc.
) -> Optional[pd.Series | pd.DataFrame]:
    """Fetches specified technical indicator data from FMP API."""
    if not all([api_key, symbol, period, indicator_type]):
        print("Error: Missing required parameters for get_technical_indicator.")
        return None

    api_timeframe = timeframe if timeframe != "1day" else "daily"
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/{api_timeframe}/{symbol}?period={period}&type={indicator_type}&apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            # Ensure 'date' column exists
            if "date" not in df.columns:
                print(
                    f"Error: 'date' column missing in indicator response for {symbol} {indicator_type}"
                )
                return None

            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            df = df.sort_index()

            # Find the indicator column (could be 'sma', 'ema', 'rsi')
            indicator_col_name = indicator_type.lower()
            if indicator_col_name not in df.columns:
                # Sometimes the column name matches the type exactly
                if indicator_type in df.columns:
                    indicator_col_name = indicator_type
                else:  # Try finding the first column that isn't date/open/high/low/close/volume if name mismatch
                    potential_cols = [
                        c
                        for c in df.columns
                        if c not in ["open", "high", "low", "close", "volume"]
                    ]
                    if potential_cols:
                        indicator_col_name = potential_cols[0]
                    else:
                        print(
                            f"Error: Indicator column ('{indicator_type.lower()}') not found in response for {symbol}"
                        )
                        return None

            return df[indicator_col_name]
        elif isinstance(data, list) and len(data) == 0:
            print(
                f"No indicator data returned for {symbol} {indicator_type} period {period}"
            )
            return None  # Return None for empty list
        else:
            print(
                f"Warning: Unexpected response format for {symbol} indicator {indicator_type}: {data}"
            )
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching indicator {indicator_type} for {symbol}: {e}")
        try:
            print(f"API Error Response: {response.text}")  # type: ignore
        except:  # noqa: E722
            pass
        return None
    except json.JSONDecodeError:
        print(f"Error decoding indicator JSON for {symbol} {indicator_type}. Response: {response.text}")  # type: ignore
        return None
    except Exception as e:
        print(f"Error processing indicator data for {symbol} {indicator_type}: {e}")
        return None


@st.cache_data(ttl=600)
def get_multiple_stock_quotes(
    api_key: str, symbols: list[str]
) -> list[dict[str, Any]] | None:
    """Fetches stock quotes for multiple symbols in a single API call."""
    if not api_key:
        print("Error: API key not provided for multiple quotes.")
        return None
    if not symbols:
        print("Error: No symbols provided for multiple quotes.")
        return []  # Return empty list if no symbols given

    # Join symbols into comma-separated string
    symbols_str = ",".join(symbols).upper()
    url = (
        f"https://financialmodelingprep.com/api/v3/quote/{symbols_str}?apikey={api_key}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Expecting a list of quote objects
        if isinstance(data, list):
            return data
        else:
            print(
                f"Warning: Unexpected response format for multiple quotes ({symbols_str}): {data}"
            )

            # If it returns a single dict for a single symbol, wrap it in a list
            if isinstance(data, dict) and len(symbols) == 1:
                return [data]
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching multiple quotes for {symbols_str}: {e}")
        try:
            print(f"API Error Response: {response.text}")  # type: ignore
        except:  # noqa: E722
            pass
        return None
    except json.JSONDecodeError:
        print(f"Error decoding multiple quotes JSON for {symbols_str}. Response: {response.text}")  # type: ignore
        return None
    except Exception as e:
        print(f"Error processing multiple quotes data for {symbols_str}: {e}")
        return None


@st.cache_data(ttl=3600)
def get_forex_pairs_list(api_key: str) -> list[str] | None:
    """Fetches the list of available Forex currency pairs from FMP API."""
    if not api_key:
        print("Error: API key not provided for Forex pairs list.")
        return None

    url = f"https://financialmodelingprep.com/api/v3/symbol/available-forex-currency-pairs?apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if (
            isinstance(data, dict)
            and "symbolsList" in data
            and isinstance(data["symbolsList"], list)
        ):
            pairs = [
                item.get("symbol") for item in data["symbolsList"] if item.get("symbol")
            ]
            return sorted(pairs)  # Return sorted list of symbols
        # Handle alternative structure if API returns just a list of strings
        elif isinstance(data, list) and all(isinstance(item, str) for item in data):
            return sorted(data)
        else:
            print(f"Warning: Unexpected response format for Forex pairs list: {data}")
            # Fallback if API is unavailable or format is wrong
            return [
                "EURUSD",
                "USDJPY",
                "GBPUSD",
                "AUDUSD",
                "USDCAD",
                "USDCHF",
                "NZDUSD",
            ]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Forex pairs list: {e}")
        return ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
    except json.JSONDecodeError:
        print(f"Error decoding JSON for Forex pairs list. Response: {response.text}")  # type: ignore
        return ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
    except Exception as e:
        print(f"Generic error processing Forex pairs list: {e}")
        return ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]


@st.cache_data(ttl=60)
def get_forex_quote(api_key: str, pair: str) -> list[dict[str, Any]] | None:
    """Fetches the latest quote for a specific Forex pair using the /api/v3/fx/ endpoint."""
    if not api_key:
        print("Error: API key not provided for Forex quote.")
        return None
    if not pair:
        print("Error: Forex pair not provided.")
        return None

    url = f"https://financialmodelingprep.com/api/v3/fx/{pair}?apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Expecting a list containing one quote dictionary
        if isinstance(data, list) and len(data) > 0:
            return data
        elif isinstance(data, list) and len(data) == 0:
            print(f"Empty list returned for Forex quote {pair}")
            return None
        else:
            print(f"Warning: Unexpected response format for Forex quote {pair}: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Forex quote for {pair}: {e}")
        try:
            print(f"API Error Response: {response.text}")  # type: ignore
        except:
            pass
        return None
    except json.JSONDecodeError:
        print(f"Error decoding Forex quote JSON for {pair}. Response: {response.text}")  # type: ignore
        return None
    except Exception as e:
        print(f"Error processing Forex quote data for {pair}: {e}")
        return None
