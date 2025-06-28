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

    print(f"Columns fetched: {df.columns.tolist()}")
    return df

def analyze_triggers(df):
    print("Analyzing triggers...")

    # Check data length
    if len(df) < 30:
        print(f"❌ Data length too short: {len(df)} rows")
        return None

    # Check required columns
    required_cols = ['Open', 'Close']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            return None

    # Check if values are non-null and numeric
    if df['Open'].isnull().all():
        print("❌ 'Open' column is all nulls")
        return None
    if df['Close'].isnull().all():
        print("❌ 'Close' column is all nulls")
        return None

    try:
        base_price = float(df['Open'].iloc[0])   # IPO opening price
        latest_close = float(df['Close'].iloc[-1])  # Latest close price
    except Exception as e:
        print(f"❌ Error converting prices to float: {e}")
        return None

    print(f"Base price (IPO open): {base_price}")
    print(f"Latest close price: {latest_close}")

    trigger = latest_close > base_price

    return {
        "Base Price": round(base_price, 2),
        "Latest Close": round(latest_close, 2),
        "Trigger": "✅" if trigger else "❌"
    }
