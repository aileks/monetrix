import os

import streamlit as st

from monetrix.api_clients.fmp_client import get_stock_quote

API_KEY = os.getenv("FMP_API_KEY")

COMMON_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V"]

st.title("Stock Quote")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info("Ensure .env file is in the project root with FMP_API_KEY='YOUR_KEY'")
    st.stop()

st.sidebar.header("Quote Input")

# TODO: Consider extracting this logic
default_index = COMMON_TICKERS.index("AAPL") if "AAPL" in COMMON_TICKERS else 0
symbol_input = st.sidebar.selectbox(
    "Select stock symbol:",
    options=COMMON_TICKERS,
    index=default_index,
    key="quote_symbol_select",
)
custom_symbol = st.sidebar.text_input(
    "Or enter a custom symbol:", key="quote_custom_symbol"
).upper()
symbol_to_use = custom_symbol if custom_symbol else symbol_input


fetch_button = st.sidebar.button("Get Quote", key="quote_fetch_button")

st.header(f"{symbol_to_use}")

if fetch_button:
    if not symbol_to_use:
        st.warning("Please select or enter a stock symbol.")
    else:
        with st.spinner(f"Fetching quote for {symbol_to_use}..."):
            # Pass the selected/entered symbol to the API function
            quote_data = get_stock_quote(symbol_to_use, API_KEY)  #

        if quote_data:
            # Display key metrics
            price, day_low, day_high, vol = st.columns(4)
            price_quote = quote_data.get("price")
            change = quote_data.get("change", 0)
            percent_change = quote_data.get("changesPercentage", 0)

            price.metric(
                "Price",
                f"${price_quote:,.2f}" if price_quote is not None else "N/A",
                (
                    f"{change:,.2f} ({percent_change:.2f}%)"
                    if price_quote is not None
                    else ""
                ),
            )
            day_low.metric("Day Low", f"${quote_data.get('dayLow', 'N/A'):,.2f}")
            day_high.metric("Day High", f"${quote_data.get('dayHigh', 'N/A'):,.2f}")
            vol.metric("Volume", f"{quote_data.get('volume', 'N/A'):,}")

            with st.expander("View Raw JSON Data"):
                st.json(quote_data)
        else:
            st.error(
                f"Could not retrieve quote data for {symbol_to_use}. Check symbol or API limits."
            )
else:
    st.info("Select a stock symbol and click 'Get Quote'.")
