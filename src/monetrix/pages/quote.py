import os

import streamlit as st

from monetrix.api_clients.fmp_client import get_stock_quote

API_KEY = os.getenv("FMP_API_KEY")

# Define a list of common tickers
COMMON_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V"]

st.title("Stock Quote")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info("Ensure .env file is in the project root with FMP_API_KEY='YOUR_KEY'")
    st.stop()

st.sidebar.header("Quote Input")
default_index = COMMON_TICKERS.index("AAPL")
symbol_input = st.sidebar.selectbox(
    "Select or Enter Stock Symbol:",
    options=COMMON_TICKERS,
    index=default_index,
    key="quote_symbol_select",
)
custom_symbol = st.sidebar.text_input(
    "Or enter a custom symbol:", key="quote_custom_symbol"
).upper()
symbol_to_use = custom_symbol if custom_symbol else symbol_input

fetch_button = st.sidebar.button("Get Quote", key="quote_fetch_button")

st.header(f"Quote for {symbol_to_use}")

if fetch_button:
    if not symbol_to_use:
        st.warning("Please select or enter a stock symbol.")
    else:
        with st.spinner(f"Fetching quote for {symbol_to_use}..."):
            quote_data = get_stock_quote(symbol_to_use, API_KEY)  #

        if quote_data:
            price_col, pe_col, low_col, high_col, vol_col = st.columns(5)

            # Extract data with .get() for safety
            price_quote = quote_data.get("price")
            change = quote_data.get("change", 0)
            percent_change = quote_data.get("changesPercentage", 0)
            pe_ratio = quote_data.get("pe")
            day_low = quote_data.get("dayLow")
            day_high = quote_data.get("dayHigh")
            volume = quote_data.get("volume")

            price_col.metric(
                "Price",
                f"${price_quote:,.2f}" if price_quote is not None else "N/A",
                (
                    f"{change:,.2f} ({percent_change:.2f}%)"
                    if price_quote is not None
                    and change is not None
                    and percent_change is not None
                    else ""
                ),
            )

            pe_col.metric(
                "P/E Ratio",
                f"{pe_ratio:.2f}" if pe_ratio is not None else "N/A",
            )

            low_col.metric(
                "Day Low", f"${day_low:,.2f}" if day_low is not None else "N/A"
            )
            high_col.metric(
                "Day High", f"${day_high:,.2f}" if day_high is not None else "N/A"
            )

            vol_col.metric("Volume", f"{volume:,}" if volume is not None else "N/A")

            with st.expander("View Raw JSON Data"):
                st.json(quote_data)
        else:
            st.error(
                f"Could not retrieve quote data for {symbol_to_use}. Check symbol or API limits."
            )
else:
    st.info("Select a stock symbol and click 'Get Quote'.")
