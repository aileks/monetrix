import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Monetrix", layout="wide", initial_sidebar_state="auto")

pages = [
    st.Page("pages/about.py", title="About", default=True),
    st.Page("pages/quote.py", title="Stock Quote"),
    st.Page("pages/historical.py", title="Historical Data"),
    st.Page("pages/trends.py", title="Market Trends"),
]

pg = st.navigation(pages)

pg.run()
