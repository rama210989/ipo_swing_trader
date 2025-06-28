import pandas as pd
import yfinance as yf
import time


def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 Fetching data for {ticker_full} (Attempt {attempt+1})")
            df = yf.download(ticker_full, period="6mo", progress=False)

            if not df.empty:
                print(f"✅ Data fetched: {len(df)} rows")
                break
        except Exception as e:
            print(f"⚠️ Error fetching {ticker_full}: {e}")
        time.sleep(sleep_sec)

    if df is None or df.empty:
        print(f"❌ No data found for {ticker_full}")
        return None

    # Fix: Flatten MultiIndex columns (if any) to get actual OHLCV columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(1)
    else:
        df.columns = [str(col).strip() for col in df.columns]

    return df


def analyze_triggers(df):
    try:
        required_cols = ['Open', 'Close']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Required columns missing: {df.columns}")
            return None

        if len(df) < 5:
            print("❌ Not enough data")
            return None

        base_price = df['Open'].iloc[0]
        current_price = df['Close'].iloc[-1]
        is_green = current_price > base_price

        return {
            "Listing Price": round(base_price, 2),
            "Current Price": round(current_price, 2),
            "Trigger": "🟢 Green" if is_green else "🔴 Red"
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None


# DEBUG MODE: Optional test block if you want to test this script standalone
if __name__ == "__main__":
    test_tickers = ["ACMESOLAR.NS", "DENTA.NS", "RELIANCE.NS"]

    for ticker in test_tickers:
        print(f"\n🔍 Testing {ticker}")
        df = get_price_data(ticker)
        if df is None:
            print(f"❌ Skipping {ticker} – No data")
            continue

        print(f"📊 Last 3 rows for {ticker}")
        print(df.tail(3))

        triggers = analyze_triggers(df)
        if triggers:
            print(f"✅ Trigger result for {ticker}: {triggers}")
        else:
            print(f"⚠️ Could not analyze triggers for {ticker}")
