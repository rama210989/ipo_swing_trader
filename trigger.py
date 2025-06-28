import yfinance as yf
import pandas as pd
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    df = None
    for i in range(max_retries):
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(-1)
                return df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        time.sleep(sleep_sec)
    return None

def analyze_trigger(df):
    try:
        # Clean-up
        df = df.dropna(subset=["Open", "Close"])
        if df.empty:
            return None

        first_open = df['Open'].iloc[0]
        last_close = df['Close'].iloc[-1]
        trigger_flag = last_close > first_open

        return {
            "Listing Price (Open)": round(first_open, 2),
            "Latest Close": round(last_close, 2),
            "Trigger": "✅" if trigger_flag else "❌"
        }
    except Exception as e:
        print(f"Error analyzing trigger: {e}")
        return None
