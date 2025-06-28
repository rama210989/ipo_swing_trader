import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 Fetching data for {ticker_full} (Attempt {attempt+1})")
            df = yf.download(ticker_full, progress=False, period="max", auto_adjust=False)  # Fix: Explicit auto_adjust
            if not df.empty:
                print(f"✅ Data fetched: {len(df)} rows")
                break
        except Exception as e:
            print(f"⚠️ Error fetching {ticker_full}: {e}")
        time.sleep(sleep_sec)

    if df is None or df.empty:
        print(f"❌ No data found for {ticker_full}")
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

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

        first_date = df.index.min()
        listing_date = first_date.strftime('%Y-%m-%d')
        base_price = df.loc[first_date, 'High']
        ltp = df['Close'].iloc[-1]

        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        dip_threshold = base_price * 0.95
        dips = df[df['Low'] < dip_threshold]

        u_curve_detected = False
        sessions_to_u_curve = "-"
        percent_dip = "-"
        cross_idx = None
        buying_date = "-"
        buy_signal = False

        if not dips.empty:
            min_low = dips['Low'].min()
            percent_dip = f"{round((min_low - base_price) / base_price * 100, 2)}%"
            dip_idx = dips['Low'].idxmin()
            after_dip = df.loc[dip_idx:]
            cross_row = after_dip[after_dip['Close'] > base_price]
            if not cross_row.empty:
                cross_idx = cross_row.index.min()
                sessions_to_u_curve = str(df.index.get_loc(cross_idx) - df.index.get_loc(dip_idx))
                u_curve_detected = True
                buying_date = cross_idx.strftime('%Y-%m-%d')
                buy_signal = ltp > base_price

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
            "# Sessions U-Curve": sessions_to_u_curve,
            "% Dip": percent_dip,
            "BUY": "✅" if buy_signal else "❌",
            "Buying Date": buying_date,
            "EMA20": round(df['EMA20'].iloc[-1], 2),
            "EMA50": round(df['EMA50'].iloc[-1], 2),
            "SELL 30% Profit": "✅" if sell_signal else "❌",
            "SELL All": "✅" if sell_all_signal else "❌"
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None
