import os

import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from monetrix.api_clients.fmp_client import get_historical_price_data

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

st.title("Historical Stock Data")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found.")
    st.info("Ensure .env file is in the project root.")
    st.stop()

st.sidebar.header("Historical Data Input")
symbol_input_hist = st.sidebar.text_input(
    "Enter Stock Symbol:", value="AAPL", key="hist_symbol_input"
).upper()
years_input = st.sidebar.slider(
    "Select Years of History:", 1, 10, 5, key="hist_years"
)  # Min 1 yr, Max 10 yrs, Default 5 yrs
fetch_button_hist = st.sidebar.button("Get Historical Data", key="hist_fetch_button")

st.header(f"Historical Data for {symbol_input_hist} ({years_input} Years)")

if fetch_button_hist:
    if not symbol_input_hist:
        st.warning("Please enter a stock symbol.")
    else:
        with st.spinner(f"Fetching historical data for {symbol_input_hist}..."):
            hist_data = get_historical_price_data(
                symbol_input_hist, API_KEY, years_input
            )

        if hist_data is not None and not hist_data.empty:
            # Create Plotly chart
            fig = px.line(
                hist_data, y="close", title=f"{symbol_input_hist} Closing Price"
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Closing Price (USD)")
            st.plotly_chart(fig, use_container_width=True)

            # Display raw data in an expander
            with st.expander("View Historical Data Table"):
                st.dataframe(hist_data)

        elif hist_data is not None and hist_data.empty:
            st.warning(
                f"No historical data returned for {symbol_input_hist}. The API might have limitations or the symbol may be incorrect."
            )
        else:
            st.error(
                f"Could not retrieve historical data for {symbol_input_hist}. Check API limits or endpoint availability."
            )
else:
    st.info("Enter a stock symbol, select years, and click 'Get Historical Data'.")
