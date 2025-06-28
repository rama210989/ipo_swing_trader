import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    # Ensure ticker has .NS suffix
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

    # Flatten multi-index columns if any
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)

    return df

def analyze_triggers(df):
    # Basic checks
    if len(df) < 30 or 'Open' not in df.columns or 'Low' not in df.columns or 'Close' not in df.columns:
        print("❌ Insufficient data or required columns missing.")
        return None

    open_col = df['Open']
    low_col = df['Low']
    close_col = df['Close']

    # Handle multi-column DataFrame edge case
    if isinstance(open_col, pd.DataFrame):
        open_col = open_col.iloc[:, 0]
    if isinstance(low_col, pd.DataFrame):
        low_col = low_col.iloc[:, 0]
    if isinstance(close_col, pd.DataFrame):
        close_col = close_col.iloc[:, 0]

    base_price = float(open_col.iloc[0])
    min_low = float(low_col.min())
    dip_pct = (base_price - min_low) / base_price * 100
    last_close = float(close_col.iloc[-1])

    u_curve_formed = dip_pct >= 5

    # Compute EMAs on the close prices
    ema20 = close_col.ewm(span=20, adjust=False).mean()
    ema50 = close_col.ewm(span=50, adjust=False).mean()

    buy_trigger = False
    buy_date = None

    if u_curve_formed:
        crossed = (close_col > base_price) & (close_col.shift(1) <= base_price)
        crossed = crossed.fillna(False).astype(bool)

        if crossed.any():
            buy_trigger = True
            first_cross_idx = crossed.idxmax()
            if first_cross_idx in df.index:
                buy_date = first_cross_idx
            else:
                buy_date = None
        else:
            buy_trigger = False
            buy_date = None

    sell_30_trigger = False
    sell_all_trigger = False

    if buy_trigger and buy_date in df.index:
        df_post_buy = df.loc[buy_date:]
        if len(df_post_buy) > 0:
            ema20_latest = ema20.loc[df_post_buy.index[-1]]
            ema50_latest = ema50.loc[df_post_buy.index[-1]]
            last_close_post_buy = close_col.loc[df_post_buy.index[-1]]

            sell_30_trigger = last_close_post_buy < ema20_latest
            sell_all_trigger = last_close_post_buy < ema50_latest

    # Convert to plain bool
    buy_trigger = bool(buy_trigger)
    sell_30_trigger = bool(sell_30_trigger)
    sell_all_trigger = bool(sell_all_trigger)

    return {
        "Base Price": round(base_price, 2),
        "Lowest Price": round(min_low, 2),
        "Max Dip %": round(dip_pct, 2),
        "Last Close": round(last_close, 2),
        "U-Curve Dip ≥5%": u_curve_formed,
        "BUY Trigger": "✅" if buy_trigger else "",
        "BUY Date": buy_date.strftime("%Y-%m-%d") if buy_date else "",
        "SELL 30% Trigger": "🔁" if sell_30_trigger else "",
        "SELL ALL Trigger": "🚪" if sell_all_trigger else ""
    }
