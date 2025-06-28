import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None
    for attempt in range(max_retries):
        try:
            print(f"Fetching data for {ticker_full} (Attempt {attempt+1})")
            df = yf.download(ticker_full, period="6mo", progress=False)
            print(f"Rows fetched: {len(df)}")
            if not df.empty:
                break
        except Exception as e:
            print(f"Error fetching {ticker_full}: {e}")
        time.sleep(sleep_sec)

    if df is None or df.empty:
        print(f"❌ No data found for {ticker_full}")
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)

    return df

def analyze_triggers(df):
    # Basic validation
    if len(df) < 30 or 'Open' not in df.columns or 'Close' not in df.columns:
        print("❌ Insufficient data or required columns missing.")
        return None

    base_price = float(df['Open'].iloc[0])   # IPO opening price
    latest_close = float(df['Close'].iloc[-1])  # Latest close price

    trigger = latest_close > base_price  # True if current price is above opening price

    return {
        "Base Price": round(base_price, 2),
        "Latest Close": round(latest_close, 2),
        "Trigger": "✅" if trigger else "❌"
    }
