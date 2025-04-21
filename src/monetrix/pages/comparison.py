import os
import re

import streamlit as st

from monetrix.api_clients.fmp_client import get_multiple_stock_quotes

API_KEY = os.getenv("FMP_API_KEY")

COMMON_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V"]
MAX_COMPARE = 5  # Set a max limit for comparison

st.title("Stock Comparison")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info("Ensure .env file is in the project root with FMP_API_KEY='YOUR_KEY'")
    st.stop()

selected_common_symbols = st.multiselect(
    "Select Common Stocks:",
    options=COMMON_TICKERS,
    default=COMMON_TICKERS[:2] if len(COMMON_TICKERS) >= 2 else COMMON_TICKERS,
    key="compare_symbols_select",
)

custom_symbols_input = st.text_area(
    "Enter Custom Tickers (comma, space, or newline separated):",
    height=70,
    key="compare_custom_symbols_input",
    placeholder="e.g., IBM, NVDA, JPM",
)

compare_button = st.button("Compare Stocks", key="compare_fetch_button")

if compare_button:
    custom_symbols_raw = re.split(r"[,\s\n]+", custom_symbols_input)
    custom_symbols = [s.strip().upper() for s in custom_symbols_raw if s.strip()]
    combined_symbols_list = selected_common_symbols + custom_symbols
    final_symbols_set = set()
    final_symbols_list = []
    for symbol in combined_symbols_list:
        if symbol not in final_symbols_set:
            final_symbols_set.add(symbol)
            final_symbols_list.append(symbol)

    valid_input = True  # Flag to control execution flow
    if not final_symbols_list or len(final_symbols_list) < 2:
        st.warning(
            "Please ensure your combined selections result in at least 2 unique stocks."
        )
        valid_input = False
    elif len(final_symbols_list) > MAX_COMPARE:
        # Exceeded hard limit
        st.error(
            f"Too many unique stocks selected ({len(final_symbols_list)}). Please limit your combined input to {MAX_COMPARE} unique stocks."
        )
        valid_input = False

    if valid_input:
        symbols_to_fetch = final_symbols_list
        with st.spinner(f"Fetching data for {', '.join(symbols_to_fetch)}..."):
            comparison_data = get_multiple_stock_quotes(API_KEY, symbols_to_fetch)

        if comparison_data:
            st.header("Comparison Metrics")
            cols = st.columns(len(symbols_to_fetch))

            for i, symbol in enumerate(symbols_to_fetch):
                stock_data = next(
                    (item for item in comparison_data if item["symbol"] == symbol), None
                )
                if stock_data:
                    with cols[i]:
                        st.subheader(f"{stock_data.get('name', symbol)}")
                        price = stock_data.get("price")
                        change = stock_data.get("change")
                        pct_change = stock_data.get("changesPercentage")
                        price_delta = (
                            f"{change:,.2f} ({pct_change:.2f}%)"
                            if change is not None and pct_change is not None
                            else None
                        )
                        st.metric(
                            "Price",
                            f"${price:,.2f}" if price is not None else "N/A",
                            price_delta,
                        )
                        pe = stock_data.get("pe")
                        st.metric("P/E Ratio", f"{pe:.2f}" if pe is not None else "N/A")
                        mkt_cap = stock_data.get("marketCap")
                        st.metric(
                            "Market Cap",
                            f"${mkt_cap:,.0f}" if mkt_cap is not None else "N/A",
                        )
                        vol = stock_data.get("volume")
                        st.metric("Volume", f"{vol:,}" if vol is not None else "N/A")
                else:
                    with cols[i]:
                        st.subheader(symbol)
                        st.warning("Data not found.")

        elif not comparison_data:
            st.info("No quote data returned for the selected symbols.")
        else:
            st.error(
                f"Could not retrieve comparison data for {', '.join(symbols_to_fetch)}."
            )

if not compare_button:
    st.info("Select/enter 2 or more stocks (max 5) and click 'Compare Stocks'.")


st.caption("Stock quote data provided by Financial Modeling Prep.")
