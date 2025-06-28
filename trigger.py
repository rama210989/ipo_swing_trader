import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 Fetching data for {ticker_full} (Attempt {attempt+1})")
            # Fetch full available history
            df = yf.download(ticker_full, progress=False, period="max")
            
            if not df.empty:
                print(f"✅ Data fetched: {len(df)} rows")
                break
        except Exception as e:
            print(f"⚠️ Error fetching {ticker_full}: {e}")
        time.sleep(sleep_sec)

    if df is None or df.empty:
        print(f"❌ No data found for {ticker_full}")
        return None

    # Flatten MultiIndex columns if present (yfinance often returns MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        print(f"Columns before flattening: {df.columns}")
        df.columns = df.columns.get_level_values(0)  # Take first level like 'Open', 'Close' etc.
        print(f"Columns after flattening: {df.columns}")

    df = df.rename(columns=lambda x: str(x).strip())
    return df


def analyze_triggers(df):
    try:
        required_cols = ['Open', 'Close', 'Low', 'High']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Required columns missing: {df.columns}")
            return None

        if len(df) < 20:
            print("❌ Not enough data for analysis")
            return None

        # Get listing (IPO) date and base price = highest price on first available day
        listing_date = df.index.min().strftime('%Y-%m-%d')  # first available date in data
        base_price = df.loc[df.index.min(), 'High']

        ltp = df['Close'].iloc[-1]

        # Calculate EMA20 and EMA50
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        dip_threshold = base_price * 0.95
        dips = df[df['Low'] < dip_threshold]

        u_curve_detected = False
        sessions_to_u_curve = None
        percent_dip = None

        if not dips.empty:
            min_low = dips['Low'].min()
            percent_dip = round((min_low - base_price) / base_price * 100, 2)

            dip_idx = dips['Low'].idxmin()
            after_dip = df.loc[dip_idx:]
            cross_idx = after_dip[after_dip['Close'] > base_price].index.min()

            if pd.notna(cross_idx):
                u_curve_detected = True
                sessions_to_u_curve = df.index.get_loc(cross_idx) - df.index.get_loc(dip_idx)

        buy_signal = u_curve_detected and (ltp > base_price)

        sell_signal = False
        sell_all_signal = False
        if buy_signal:
            if ltp < df['EMA20'].iloc[-1]:
                sell_signal = True
            if ltp < df['EMA50'].iloc[-1]:
                sell_all_signal = True

        return {
            "Listing Price": round(base_price, 2),
            "Listing Date": listing_date,
            "LTP": round(ltp, 2),
            "U-Curve": "✅" if u_curve_detected else "❌",
            "# Sessions U-Curve": sessions_to_u_curve if sessions_to_u_curve is not None else "-",
            "% Dip": percent_dip if percent_dip is not None else "-",
            "BUY": "✅" if buy_signal else "❌",
            "Buying Date": cross_idx.strftime('%Y-%m-%d') if pd.notna(cross_idx) else "-",
            "EMA20": round(df['EMA20'].iloc[-1], 2),
            "EMA50": round(df['EMA50'].iloc[-1], 2),
            "SELL 30% Profit": "✅" if sell_signal else "❌",
            "SELL All": "✅" if sell_all_signal else "❌"
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None


# Example debug run - Remove or comment this out in production
if __name__ == "__main__":
    tickers = ["ACMESOLAR.NS", "RELIANCE.NS"]
    for t in tickers:
        df = get_price_data(t)
        if df is not None:
            result = analyze_triggers(df)
            print(f"{t} analysis:\n{result}\n")
        else:
            print(f"No data for {t}")
