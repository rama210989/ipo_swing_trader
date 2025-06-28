import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 Fetching data for {ticker_full} (Attempt {attempt+1})")
            df = yf.download(ticker_full, progress=False, period="max", auto_adjust=False)
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
        buy_price = None

        if not dips.empty:
            min_low = dips['Low'].min()
            percent_dip = round((min_low - base_price) / base_price * 100, 2)
            dip_idx = dips['Low'].idxmin()
            after_dip = df.loc[dip_idx:]
            cross_row = after_dip[after_dip['Close'] > base_price]
            if not cross_row.empty:
                cross_idx = cross_row.index.min()
                sessions_to_u_curve = df.index.get_loc(cross_idx) - df.index.get_loc(dip_idx)
                u_curve_detected = True
                buying_date = cross_idx.strftime('%Y-%m-%d')
                buy_price = df.loc[cross_idx, 'Close']

        buy_signal = u_curve_detected and (ltp > base_price)

        # Max upside calculation
        max_price = df['High'].max()
        max_price_date = df['High'].idxmax()
        max_upside_pct = round((max_price - base_price) / base_price * 100, 2)
        sessions_to_max_upside = df.index.get_loc(max_price_date) - df.index.get_loc(first_date)

        # Sell 30% and sell all signals and prices/dates
        sell_30_price = None
        sell_30_date = None
        sell_all_price = None
        sell_all_date = None

        if buy_signal and cross_idx is not None:
            post_buy_df = df.loc[cross_idx:]
            for idx, row in post_buy_df.iterrows():
                if sell_30_price is None and row['Close'] < row['EMA20']:
                    sell_30_price = row['Close']
                    sell_30_date = idx
                if sell_all_price is None and row['Close'] < row['EMA50']:
                    sell_all_price = row['Close']
                    sell_all_date = idx
                if sell_30_price and sell_all_price:
                    break

        percent_upside_30 = round((sell_30_price - base_price) / base_price * 100, 2) if sell_30_price else "-"
        percent_upside_all = round((sell_all_price - base_price) / base_price * 100, 2) if sell_all_price else "-"

        sell_30_date_str = sell_30_date.strftime('%Y-%m-%d') if sell_30_date else "-"
        sell_all_date_str = sell_all_date.strftime('%Y-%m-%d') if sell_all_date else "-"

        return {
            "Listing Price": round(base_price, 2),
            "Listing Date": listing_date,
            "LTP": round(ltp, 2),
            "U-curve": "✅" if u_curve_detected else "❌",
            "# sessions in u-curve": sessions_to_u_curve,
            "% dip from base price": percent_dip,
            "BUY": "✅" if buy_signal else "❌",
            "Buying Date": buying_date,
            "EMA 20": round(df['EMA20'].iloc[-1], 2),
            "EMA 50": round(df['EMA50'].iloc[-1], 2),
            "Max upside (%)": max_upside_pct,
            "# sessions to max upside": sessions_to_max_upside,
            "Sell 30 %": "✅" if sell_30_price else "❌",
            "Price at which sold 30%": round(sell_30_price, 2) if sell_30_price else "-",
            "Sell all": "✅" if sell_all_price else "❌",
            "Price at which sold all": round(sell_all_price, 2) if sell_all_price else "-",
            "% upside while selling 30%": percent_upside_30,
            "% upside while selling all": percent_upside_all
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None
