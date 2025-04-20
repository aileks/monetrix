import os
from datetime import datetime

import streamlit as st

from monetrix.api_clients.fmp_client import get_forex_pairs_list, get_forex_quote

API_KEY = os.getenv("FMP_API_KEY")

st.title("Forex Rates")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info("Ensure .env file is in the project root with FMP_API_KEY='YOUR_KEY'")
    st.stop()

with st.spinner("Loading available Forex pairs..."):
    forex_pairs = get_forex_pairs_list(API_KEY)

if not forex_pairs:
    st.error("Could not load Forex pair list. Using fallback.")
    forex_pairs = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]

default_pair = "EURUSD" if "EURUSD" in forex_pairs else forex_pairs[0]
selected_pair = st.selectbox(
    "Select Currency Pair:",
    options=forex_pairs,
    index=forex_pairs.index(default_pair),
    key="forex_pair_select",
)

get_quote_button = st.button("Get Forex Quote", key="forex_fetch_button")

if get_quote_button:
    if not selected_pair:
        st.warning("Please select a currency pair.")
    else:
        with st.spinner(f"Fetching quote for {selected_pair}..."):
            quote_data_list = get_forex_quote(API_KEY, selected_pair)

        if quote_data_list:
            # API returns a list, take the first element
            quote_data = quote_data_list[0]
            st.header(f"Quote for {quote_data.get('ticker', selected_pair)}")

            # Extract data with .get()
            bid_price = quote_data.get("bid")
            ask_price = quote_data.get("ask")
            change = quote_data.get("changes")

            # Calculate percentage change if not provided directly
            open_price = quote_data.get("open")
            percent_change = None
            if change is not None and open_price is not None and open_price != 0:
                percent_change = (change / open_price) * 100

            timestamp_ms = quote_data.get("timestamp")
            last_updated = "N/A"
            if timestamp_ms:
                # Convert from milliseconds to seconds for datetime
                last_updated = datetime.fromtimestamp(timestamp_ms / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            # Display using metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Bid", f"{bid_price:.5f}" if bid_price is not None else "N/A"
                )  # Use more decimal places for Forex
            with col2:
                st.metric("Ask", f"{ask_price:.5f}" if ask_price is not None else "N/A")
            with col3:
                st.metric(
                    "Change",
                    f"{change:.5f}" if change is not None else "N/A",
                    f"{percent_change:.3f}%" if percent_change is not None else None,
                )  # Delta shows percentage change

            st.caption(f"Last updated: {last_updated}")

            with st.expander("View Raw JSON Data"):
                st.json(quote_data)

        else:
            st.error(f"Could not retrieve quote data for {selected_pair}.")
else:
    st.info("Select a currency pair and click 'Get Forex Quote'.")

st.caption("Forex data provided by Financial Modeling Prep.")
