import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from monetrix.api_clients.fmp_client import (
    get_historical_price_data,
    get_technical_indicator,
)

API_KEY = os.getenv("FMP_API_KEY")

# Define a list of common tickers (same as in quote.py)
COMMON_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V"]

st.title("Historical Stock Data")


def set_date_range(days: int = 0, weeks: int = 0, months: int = 0, years: int = 0):
    """Updates session state for start and end dates based on offset."""
    today = date.today()
    start_offset = timedelta(days=days, weeks=weeks)
    if months > 0:
        start_offset = timedelta(days=months * 30)
    if years > 0:
        start_offset = timedelta(days=years * 365)

    new_start_date = today - start_offset
    if new_start_date >= today:
        new_start_date = today - timedelta(days=1)

    st.session_state.hist_start_date = new_start_date
    st.session_state.hist_end_date = today


today = date.today()
if "hist_start_date" not in st.session_state:
    st.session_state.hist_start_date = today - timedelta(days=365)
if "hist_end_date" not in st.session_state:
    st.session_state.hist_end_date = today

if not API_KEY:
    st.error("Fatal Error: FMP_API_KEY not found.")
    st.stop()

st.sidebar.header("Input")
# Use selectbox for symbol
default_index_hist = COMMON_TICKERS.index("AAPL") if "AAPL" in COMMON_TICKERS else 0
symbol_input_hist = st.sidebar.selectbox(
    "Select Stock Symbol:",
    options=COMMON_TICKERS,
    index=default_index_hist,
    key="hist_symbol_select",
).upper()

# Date Range Inputs
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

# Date Range Presets
st.sidebar.markdown("Set Date Range:")
cols_dates = st.sidebar.columns([1, 1, 1])
cols_dates[0].button(
    "1M",
    on_click=set_date_range,
    kwargs=dict(months=1),
    key="date_1m",
    use_container_width=True,
)
cols_dates[1].button(
    "6M",
    on_click=set_date_range,
    kwargs=dict(months=6),
    key="date_6m",
    use_container_width=True,
)
cols_dates[2].button(
    "YTD",
    on_click=set_date_range,
    kwargs=dict(days=(today - date(today.year, 1, 1)).days),
    key="date_ytd",
    use_container_width=True,
)
cols_dates_2 = st.sidebar.columns([1, 1, 1])
cols_dates_2[0].button(
    "1Y",
    on_click=set_date_range,
    kwargs=dict(years=1),
    key="date_1y",
    use_container_width=True,
)
cols_dates_2[1].button(
    "5Y",
    on_click=set_date_range,
    kwargs=dict(years=5),
    key="date_5y",
    use_container_width=True,
)
cols_dates_2[2].button(
    "10Y",
    on_click=set_date_range,
    kwargs=dict(years=10),
    key="date_10y",
    use_container_width=True,
)

st.sidebar.divider()

st.sidebar.header("Technical Indicators")
available_indicators = ["SMA", "EMA", "RSI"]
selected_indicators = st.sidebar.multiselect(
    "Select Indicators:", options=available_indicators, key="hist_indicators_select"
)

indicator_periods = {}
if "SMA" in selected_indicators:
    indicator_periods["SMA"] = st.sidebar.number_input(
        "SMA Period:", min_value=2, max_value=200, value=20, step=1, key="sma_period"
    )
if "EMA" in selected_indicators:
    indicator_periods["EMA"] = st.sidebar.number_input(
        "EMA Period:", min_value=2, max_value=200, value=20, step=1, key="ema_period"
    )
if "RSI" in selected_indicators:
    indicator_periods["RSI"] = st.sidebar.number_input(
        "RSI Period:", min_value=2, max_value=50, value=14, step=1, key="rsi_period"
    )

fetch_button_hist = st.sidebar.button("Get Data & Indicators", key="hist_fetch_button")

st.header(f"{symbol_input_hist}")
st.caption(
    f"Date Range: {st.session_state.hist_start_date.strftime('%Y-%m-%d')} to {st.session_state.hist_end_date.strftime('%Y-%m-%d')}"
)

if fetch_button_hist:
    current_start = st.session_state.hist_start_date
    current_end = st.session_state.hist_end_date

    if not symbol_input_hist:
        st.warning("Please select a stock symbol.")
    elif current_start >= current_end:
        st.warning("Error: Start date must be before end date.")
    else:
        # Fetch historical data first
        with st.spinner(f"Fetching historical data for {symbol_input_hist}..."):
            hist_data = get_historical_price_data(
                symbol_input_hist, API_KEY, current_start, current_end
            )

        if hist_data is not None and not hist_data.empty:
            # Fetch selected indicators
            indicator_series_map = {}
            fetch_errors = []
            if selected_indicators:
                with st.spinner(
                    f"Fetching selected indicators for {symbol_input_hist}..."
                ):
                    for indicator in selected_indicators:
                        period = indicator_periods.get(indicator)
                        if period:
                            indicator_name = f"{indicator}_{period}"
                            # Fetch data using the new function
                            series = get_technical_indicator(
                                API_KEY,
                                symbol_input_hist,
                                period,
                                indicator.lower(),
                            )
                            if series is not None:
                                # Only keep data within the selected date range
                                series = series[current_start:current_end]  # type: ignore
                                indicator_series_map[indicator_name] = series
                            else:
                                fetch_errors.append(indicator_name)
                                st.warning(
                                    f"Could not fetch data for {indicator_name}."
                                )
                        else:
                            st.warning(f"Period not defined for {indicator}, skipping.")

            # Merge indicator data with historical data
            merged_data = hist_data.copy()
            for name, series in indicator_series_map.items():
                merged_data = pd.merge(
                    merged_data,
                    series.rename(name),
                    left_index=True,
                    right_index=True,
                    how="left",
                )

            plot_rsi = "RSI" in selected_indicators and any(
                k.startswith("RSI") for k in indicator_series_map
            )
            rsi_indicator_name = ""
            if plot_rsi:
                rsi_indicator_name = f"RSI_{indicator_periods.get('RSI')}"
                if rsi_indicator_name not in indicator_series_map:
                    plot_rsi = False  # Failed to fetch RSI

            if plot_rsi:
                # Use subplots if RSI is selected and fetched
                fig = make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    row_heights=[0.7, 0.3],
                )  # Allocate more space to price chart

                # Price Chart (Top Row)
                fig.add_trace(
                    go.Scatter(
                        x=merged_data.index,
                        y=merged_data["close"],
                        mode="lines",
                        name="Close Price",
                    ),
                    row=1,
                    col=1,
                )

                # Add SMA/EMA to Price Chart
                for indicator in selected_indicators:
                    if indicator in ["SMA", "EMA"]:
                        period = indicator_periods.get(indicator)
                        indicator_name = f"{indicator}_{period}"
                        if indicator_name in merged_data.columns:
                            fig.add_trace(
                                go.Scatter(
                                    x=merged_data.index,
                                    y=merged_data[indicator_name],
                                    mode="lines",
                                    name=indicator_name,
                                ),
                                row=1,
                                col=1,
                            )

                # RSI Chart (Bottom Row)
                fig.add_trace(
                    go.Scatter(
                        x=merged_data.index,
                        y=merged_data[rsi_indicator_name],
                        mode="lines",
                        name=rsi_indicator_name,
                    ),
                    row=2,
                    col=1,
                )

                # Add RSI horizontal lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

                # Update layout
                fig.update_layout(
                    title=f"{symbol_input_hist} Price and RSI",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",  # Main y-axis title
                    yaxis2_title="RSI",  # Second y-axis title (for RSI subplot)
                    height=700,  # Increase height for subplots
                    hovermode="x unified",  # Better hover experience
                )
                fig.update_xaxes(
                    rangeslider_visible=False
                )  # Hide rangeslider for subplots usually

            else:
                # Use Plotly Express if no RSI
                plot_cols = ["close"]
                for indicator in selected_indicators:
                    if indicator in ["SMA", "EMA"]:
                        period = indicator_periods.get(indicator)
                        indicator_name = f"{indicator}_{period}"
                        if indicator_name in merged_data.columns:
                            plot_cols.append(indicator_name)

                fig = px.line(
                    merged_data,
                    y=plot_cols,
                    title=f"{symbol_input_hist} Closing Price & Indicators",
                )
                fig.update_layout(
                    xaxis_title="Date", yaxis_title="Price (USD)", hovermode="x unified"
                )
                fig.update_xaxes(rangeslider_visible=True)

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

            # Display merged data table
            with st.expander("View Table"):
                st.dataframe(merged_data)

        elif hist_data is not None and hist_data.empty:
            st.warning(
                f"No historical data returned for {symbol_input_hist} in the selected date range."
            )
        else:  # hist_data is None
            st.error(f"Could not retrieve historical data for {symbol_input_hist}.")
else:
    st.info(
        "Select symbol, dates, and optional indicators, then click 'Get Data & Indicators'."
    )
