import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 Fetching data for {ticker_full} (Attempt {attempt+1})")
            df = yf.download(ticker_full, period="6mo", progress=False, auto_adjust=False)
            
            if df is not None and not df.empty:
                print(f"✅ Data fetched: {len(df)} rows")
                # Debug: print columns received
                print(f"Columns before flattening: {df.columns}")

                # Flatten MultiIndex columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(-1)
                    print(f"Columns after flattening: {df.columns}")

                # Strip column names
                df.columns = [str(col).strip() for col in df.columns]

                return df
            else:
                print(f"⚠️ Empty DataFrame for {ticker_full}")
        except Exception as e:
            print(f"⚠️ Error fetching {ticker_full}: {e}")

        time.sleep(sleep_sec)

    print(f"❌ Failed to fetch data for {ticker_full} after {max_retries} attempts.")
    return None

def analyze_triggers(df):
    try:
        required_cols = ['Open', 'Close']
        print(f"Analyzing DataFrame columns: {df.columns}")

        if not all(col in df.columns for col in required_cols):
            print(f"❌ Missing required columns. Found columns: {list(df.columns)}")
            return None

        if len(df) < 5:
            print(f"❌ Not enough data. Only {len(df)} rows available.")
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
        print(f"⚠️ Trigger analysis error: {e}")
        return None

# For debugging in terminal or Colab
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
