import streamlit as st

st.set_page_config(page_title="Monetrix • Home", layout="wide")

st.title("Welcome to Monetrix!")

st.sidebar.header("Home")
st.sidebar.info("Select a feature above.")

st.markdown(
    """
    Monetrix is a dashboard designed to visualize financial market data.

    **👈 Select a feature from the sidebar** to get started!

    ### Features:
    - **Stock Quote:** Get real-time(ish) price quotes for individual stocks.
    - **Historical Data:** View and chart historical price trends.
    """
)
