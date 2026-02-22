# Monetrix

Monetrix is a simple financial data visualizer dashboard built with Streamlit. It allows users to
fetch and visualize stock quotes and historical price data using the Financial Modeling Prep (FMP)
API.

![Preview](src/monetrix/img/preview.png)

## Features

* **Stock Quote:** Get near real-time stock price quotes, including day high/low and volume.
* **Historical Data:** View and chart historical closing prices for stocks over custom date ranges
  or preset intervals (1M, 6M, YTD, 1Y, 5Y, 10Y). Add technical indicators like SMA, EMA, and RSI.
* **Market Trends:** See the top stock market gainers and losers for the current trading day.
* **Stock Comparison:** Compare metrics for up to 5 different stocks side-by-side, including price,
  P/E ratio, market cap, and volume.
* **Forex Rates:** View currency exchange rates for various forex pairs.
* **Easy Ticker Selection:** Choose from a list of common stock tickers or enter a custom one.
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
    * **Local development (`.env`):** copy the `.env.example` file to `.env`:
      ```bash
      cp src/.env.example src/.env
      ```
    * Add your FMP API key to the `.env` file:
      ```env
      FMP_API_KEY='YOUR_FMP_API_KEY'
      ```
    * Replace `'YOUR_FMP_API_KEY'` with your actual key obtained from FMP.
    * **Streamlit Cloud (`.streamlit/secrets.toml`):** set either flat or nested key:
      ```toml
      FMP_API_KEY = "YOUR_FMP_API_KEY"
      ```
      ```toml
      [fmp]
      api_key = "YOUR_FMP_API_KEY"
      ```

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
3. Use the sidebar navigation to select the desired feature:
    * **About:** Overview of the application.
    * **Stock Quote:** Get real-time stock price information for a selected ticker.
    * **Historical Data:** View historical price charts with optional technical indicators (SMA,
      EMA, RSI).
    * **Market Trends:** See the top market gainers and losers for the current trading day.
    * **Stock Comparison:** Compare multiple stocks side-by-side (up to 5).
    * **Forex Rates:** View exchange rates for forex currency pairs.

## Feature Details

### Stock Quote

Select a stock ticker from the dropdown or enter a custom symbol, then click "Get Quote" to view
current price, P/E ratio, day high/low, and volume.

### Historical Data

View historical price charts with the following options:

- Select from preset date ranges (1M, 6M, YTD, 1Y, 5Y, 10Y) or choose custom dates
- Add technical indicators (SMA, EMA, RSI) with customizable periods, computed locally from
  historical close prices
- Interactive charts with zoom and hover details

### Market Trends

View the top market gainers and losers for the current trading day, showing symbol, name, price, and
percentage change.

### Stock Comparison

Compare up to 5 stocks side-by-side:

- Select from common tickers in the dropdown
- Enter custom tickers in the text area
- View price, P/E ratio, market cap, and volume for each stock

### Forex Rates

View forex currency pair exchange rates:

- Select from available currency pairs
- See bid/ask prices and recent changes

## Dependencies

- Streamlit for the web interface
- Pandas for data handling
- Plotly for interactive charts
- Requests for API communication
- Python-dotenv for environment variable management

## Data Attribution

All financial data is provided by Financial Modeling Prep (FMP) API.
