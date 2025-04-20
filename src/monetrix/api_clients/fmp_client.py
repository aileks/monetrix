import json
from typing import Any

import requests


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
