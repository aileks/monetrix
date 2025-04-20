import os
from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from monetrix.api_clients.fmp_client import get_historical_price_data

API_KEY = os.getenv("FMP_API_KEY")

st.title("Historical Stock Data")


def set_date_range(days: int = 0, weeks: int = 0, months: int = 0, years: int = 0):
    """Updates session state for start and end dates based on offset."""
    today = date.today()
    start_offset = timedelta(days=days, weeks=weeks)
    # Use relativedelta for months/years if more precision is needed,
    # but timedelta is simpler for approximate ranges.
    if months > 0:
        start_offset = timedelta(days=months * 30)
    if years > 0:
        start_offset = timedelta(days=years * 365)

    new_start_date = today - start_offset
    # Ensure start date is not today or later
    if new_start_date >= today:
        new_start_date = today - timedelta(days=1)

    st.session_state.hist_start_date = new_start_date
    st.session_state.hist_end_date = today
    # Optional: Trigger a rerun if needed immediately after setting state,
    # although changing widget state often does this automatically.
    # st.rerun()


today = date.today()
if "hist_start_date" not in st.session_state:
    st.session_state.hist_start_date = today - timedelta(days=365)  # Default 1 year
if "hist_end_date" not in st.session_state:
    st.session_state.hist_end_date = today

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found.")
    st.stop()

st.sidebar.header("Historical Data Input")
symbol_input_hist = st.sidebar.text_input(
    "Enter Stock Symbol:", value="AAPL", key="hist_symbol_input"
).upper()

start_date_input = st.sidebar.date_input(
    "Start Date",
    max_value=st.session_state.hist_end_date - timedelta(days=1),
    key="hist_start_date",
)
end_date_input = st.sidebar.date_input(
    "End Date",
    min_value=st.session_state.hist_start_date + timedelta(days=1),
    max_value=today,
    key="hist_end_date",
)

st.sidebar.markdown("Set Date Range:")
cols = st.sidebar.columns([1, 1, 1])
# Note: Using callbacks (on_click) is generally cleaner
cols[0].button(
    "1M",
    on_click=set_date_range,
    kwargs=dict(months=1),
    key="date_1m",
    use_container_width=True,
)
cols[1].button(
    "6M",
    on_click=set_date_range,
    kwargs=dict(months=6),
    key="date_6m",
    use_container_width=True,
)
cols[2].button(
    "YTD",
    on_click=set_date_range,
    kwargs=dict(days=(today - date(today.year, 1, 1)).days),
    key="date_ytd",
    use_container_width=True,
)

cols = st.sidebar.columns([1, 1, 1])
cols[0].button(
    "1Y",
    on_click=set_date_range,
    kwargs=dict(years=1),
    key="date_1y",
    use_container_width=True,
)
cols[1].button(
    "5Y",
    on_click=set_date_range,
    kwargs=dict(years=5),
    key="date_5y",
    use_container_width=True,
)

fetch_button_hist = st.sidebar.button("Get Historical Data", key="hist_fetch_button")

st.header(f"{symbol_input_hist}")
st.caption(
    f"Date Range: {st.session_state.hist_start_date.strftime('%Y-%m-%d')} to {st.session_state.hist_end_date.strftime('%Y-%m-%d')}"
)

if fetch_button_hist:
    current_start = st.session_state.hist_start_date
    current_end = st.session_state.hist_end_date

    if not symbol_input_hist:
        st.warning("Please enter a stock symbol.")
    elif current_start >= current_end:
        st.warning("Error: Start date must be before end date.")
    else:
        with st.spinner(f"Fetching historical data for {symbol_input_hist}..."):
            hist_data = get_historical_price_data(
                symbol_input_hist, API_KEY, current_start, current_end
            )

        # (Rest of the data display logic remains the same...)
        if hist_data is not None:
            if not hist_data.empty:
                fig = px.line(
                    hist_data, y="close", title=f"{symbol_input_hist} Closing Price"
                )
                fig.update_layout(xaxis_title="Date", yaxis_title="Closing Price (USD)")
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("View Historical Data Table"):
                    st.dataframe(hist_data)
            else:
                st.warning(
                    f"No historical data returned for {symbol_input_hist} in the selected date range."
                )
        else:
            st.error(f"Could not retrieve historical data for {symbol_input_hist}.")
else:
    st.info(
        "Enter symbol, select dates or use presets, then click 'Get Historical Data'."
    )
