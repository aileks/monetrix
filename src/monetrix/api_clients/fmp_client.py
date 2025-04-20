import json
from datetime import date
from typing import Any, Optional

import pandas as pd
import requests
import streamlit as st


@st.cache_data(ttl=900)
def get_stock_quote(symbol: str, api_key: str) -> dict[str, Any] | None:
    """
    Fetches the stock quote for a given symbol from the FMP API.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').
        api_key (str): The FMP API key.

    Returns:
        dict: A dictionary containing the quote data, or None if an error occurs.
    """
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
) -> Optional[pd.DataFrame] | Optional[pd.Series]:
    """
    Fetches historical daily price data from FMP API for a given date range.

    Args:
        symbol (str): The stock ticker symbol.
        api_key (str): The FMP API key.
        start_date (date): The start date for the historical data.
        end_date (date): The end date for the historical data.

    Returns:
        Optional[pd.DataFrame]: DataFrame with historical data (date, open, high, low, close, volume),
                                 or None if an error occurs.
    """
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
    """
    Fetches the top stock market gainers from the FMP API.

    Args:
        api_key (str): The FMP API key.

    Returns:
        List[dict]: A list of dictionaries, each representing a top gainer,
                    or None if an error occurs.
    """
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
    """
    Fetches the top stock market losers from the FMP API.

    Args:
        api_key (str): The FMP API key.

    Returns:
        List[dict]: A list of dictionaries, each representing a top loser,
                    or None if an error occurs.
    """
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
