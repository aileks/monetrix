import json
from typing import Any

import pandas as pd
import requests
import streamlit as st


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
    symbol: str, api_key: str, years: int = 5
) -> pd.DataFrame | None:
    """
    Fetches historical daily price data from FMP API for a given number of years.

    Args:
        symbol (str): The stock ticker symbol.
        api_key (str): The FMP API key.
        years (int): Number of years of historical data to fetch. Max might be limited by API.

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

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={api_key}"

    try:
        print(
            f"Cache miss/fetch: Historical data for {symbol}"
        )  # Add print for cache debug
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check if data is in the expected format {'symbol': 'AAPL', 'historical': [...]}
        if (
            isinstance(data, dict)
            and "historical" in data
            and isinstance(data["historical"], list)
        ):
            if not data["historical"]:  # Handle empty list case
                st.warning(
                    f"No historical data returned for {symbol}. Check symbol or API limits."
                )
                return None

            df = pd.DataFrame(data["historical"])
            # Basic data cleaning and type conversion
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            # Select and rename columns for consistency if needed
            # df = df[['open', 'high', 'low', 'close', 'volume']] # Ensure standard columns
            df = df.sort_index()
            return df
        else:
            print(f"Unexpected historical data format for {symbol}: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding historical JSON for {symbol}. Response: {response.text}")  # type: ignore
        return None
    except Exception as e:  # Catch potential pandas errors
        print(f"Error processing historical data for {symbol}: {e}")
        return None
