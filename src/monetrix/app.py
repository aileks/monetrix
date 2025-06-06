from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Monetrix",
    page_icon=Path(__file__).parent / "public/favicon.ico",
    layout="wide",
    initial_sidebar_state="auto",
)

pages = [
    st.Page("pages/about.py", title="About", default=True),
    st.Page("pages/quote.py", title="Stock Quote"),
    st.Page("pages/historical.py", title="Historical Data"),
    st.Page("pages/trends.py", title="Market Trends"),
    st.Page("pages/comparison.py", title="Stock Comparison"),
    st.Page("pages/forex.py", title="Forex Rates"),
]

pg = st.navigation(pages)

pg.run()
