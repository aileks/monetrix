# Monetrix

Monetrix is a simple financial data visualizer dashboard built with Streamlit. It allows users to
fetch and visualize stock quotes and historical price data using the Financial Modeling Prep (FMP)
API.

## Features

* **Stock Quote:** Get near real-time stock price quotes, including day high/low and volume.
* **Historical Data:** View and chart historical closing prices for stocks over custom date ranges
  or preset intervals (1M, 6M, YTD, 1Y, 5Y, 10Y).
* **Easy Ticker Selection:** Choose from a list of common stock tickers or potentially enter a
  custom one.
* **Simple Interface:** Uses Streamlit for an interactive web application experience.

## Requirements

* Python >= 3.11
* Poetry (for dependency management)
* An API Key
  from [Financial Modeling Prep (FMP)](https://site.financialmodelingprep.com/developer/docs/)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aileks/monetrix.git
   cd monetrix
   ```

2. **Set up API Key:**
    * Copy the `.env.example` file to `.env`:
      ```bash
      cp .env.example .env
      ```
    * Add your FMP API key to the `.env` file:
      ```env
      FMP_API_KEY='YOUR_FMP_API_KEY'
      ```
    * Replace `'YOUR_FMP_API_KEY'` with your actual key obtained from FMP.

3. **Install Dependencies:**
    * Ensure you have Poetry installed ([refer to docs](https://python-poetry.org/docs/)).
    * Install project dependencies:
      ```bash
      poetry install
      ```

## Usage

1. **Run the Streamlit Application:**
   ```bash
   poetry run streamlit run src/monetrix/app.py
   ```
2. Open your web browser and navigate to the local URL provided by Streamlit (usually
   `http://localhost:8501`).
3. Use the sidebar navigation to select the desired feature: "About", "Stock Quote", or "Historical
   Data".
4. For "Stock Quote" and "Historical Data", select a ticker symbol from the dropdown, adjust date
   ranges if necessary, and click the fetch button.