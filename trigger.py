import yfinance as yf
import pandas as pd
import time

def get_price_data(ticker, max_retries=2, sleep_sec=1):
    for i in range(max_retries):
        try:
            df = yf.download(ticker, period="6mo", progress=False, auto_adjust=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(-1)
                df = df[['Open', 'Close']].dropna()
                return df
        except Exception as e:
            print(f"Error fetching {ticker} (Attempt {i+1}): {e}")
        time.sleep(sleep_sec)
    print(f"❌ No valid data fetched for {ticker}")
    return None

def analyze_trigger(df):
    try:
        if len(df) < 2:
            print("⚠️ Data too short")
            return None

        first_open = df['Open'].iloc[0]
        last_close = df['Close'].iloc[-1]

        if pd.isna(first_open) or pd.isna(last_close):
            print("⚠️ Missing Open or Close values")
            return None

        trigger_flag = last_close > first_open

        return {
            "Listing Price (Open)": round(first_open, 2),
            "Latest Close": round(last_close, 2),
            "Trigger": "✅" if trigger_flag else "❌"
        }
    except Exception as e:
        print(f"Error in analyze_trigger: {e}")
        return None
