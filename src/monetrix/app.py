import os

import streamlit as st
from dotenv import load_dotenv

from monetrix.api_clients.fmp_client import get_stock_quote

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

# --- Streamlit App Layout ---

st.set_page_config(layout="wide")
st.title("Monetrix - Simple Stock Quote Dashboard")

# Check if API Key is loaded before proceeding
if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info(
        "Please ensure you have a .env file in the project root with FMP_API_KEY='YOUR_KEY'"
    )
    st.stop()  # Stop execution if no API key

st.sidebar.header("Input")
symbol_input = st.sidebar.text_input(
    "Enter Stock Symbol (e.g., AAPL, GME):", "AAPL"
).upper()
fetch_button = st.sidebar.button("Get Quote")

st.header(f"Quote for {symbol_input}")

if fetch_button:
    if not symbol_input:
        st.warning("Please enter a stock symbol.")
    else:
        with st.spinner(f"Fetching quote for {symbol_input}..."):
            quote_data = get_stock_quote(symbol_input, API_KEY)

        if quote_data:
            st.success(f"Data fetched successfully for {symbol_input}!")

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Price",
                f"${quote_data.get('price', 'N/A'):,.2f}",
                f"{quote_data.get('change', 0):,.2f} ({quote_data.get('changesPercentage', 0):.2f}%)",
            )
            col2.metric("Day Low", f"${quote_data.get('dayLow', 'N/A'):,.2f}")
            col3.metric("Day High", f"${quote_data.get('dayHigh', 'N/A'):,.2f}")
            col4.metric("Volume", f"{quote_data.get('volume', 'N/A'):,}")

            # Display raw JSON
            with st.expander("View Raw JSON Data"):
                st.json(quote_data)
        else:
            st.error(
                f"Could not retrieve quote data for {symbol_input}. Check symbol or API limits."
            )
else:
    st.info("Enter a stock symbol and click 'Get Quote' in the sidebar.")
