import os

import pandas as pd
import streamlit as st

from monetrix.api_clients.fmp_client import (
    get_market_gainers,
    get_market_losers,
)

API_KEY = os.getenv("FMP_API_KEY")

st.title("Daily Market Movers")

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found in environment variables.")
    st.info("Ensure .env file is in the project root with FMP_API_KEY='YOUR_KEY'")
    st.stop()

# Use st.empty() placeholders for a cleaner loading experience
gainer_placeholder = st.empty()
loser_placeholder = st.empty()

with st.spinner("Fetching market movers data..."):
    gainers_data = get_market_gainers(API_KEY)
    losers_data = get_market_losers(API_KEY)

# --- Display Top 10 Gainers ---
with gainer_placeholder.container():
    st.header("Top 10 Gainers 📈")
    if gainers_data:
        df_gainers = pd.DataFrame(gainers_data)

        # Limit to top 10 and select/rename columns
        df_gainers_display = df_gainers.head(10)[
            ["symbol", "name", "price", "changesPercentage"]
        ]
        df_gainers_display = df_gainers_display.rename(
            columns={"changesPercentage": "% Change"}  # type: ignore
        )

        st.dataframe(
            df_gainers_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "price": st.column_config.NumberColumn(format="$%.2f"),
                "% Change": st.column_config.NumberColumn(
                    format="+%.2f%%"
                ),  # Add '+' sign
            },
        )
    elif gainers_data == []:
        st.info("No gainer data returned by the API for today.")
    else:
        st.error("Could not retrieve top gainers data.")

st.divider()

with loser_placeholder.container():
    st.header("Top 10 Losers 📉")
    if losers_data:
        df_losers = pd.DataFrame(losers_data)

        # Limit to top 10 and select/rename columns
        df_losers_display = df_losers.head(10)[
            ["symbol", "name", "price", "changesPercentage"]
        ]
        df_losers_display = df_losers_display.rename(
            columns={"changesPercentage": "% Change"}  # type: ignore
        )

        st.dataframe(
            df_losers_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "price": st.column_config.NumberColumn(format="$%.2f"),
                "% Change": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),  # No '+' sign needed
            },
        )
    elif not losers_data:
        st.info("No loser data returned by the API for today.")
    else:
        st.error("Could not retrieve top losers data.")

st.caption("Market data provided by Financial Modeling Prep.")
