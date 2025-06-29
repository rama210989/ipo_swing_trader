# trigger.py

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


def analyze_triggers(df, listing_date, base_price):
    try:
        required_cols = ['Open', 'Close', 'Low', 'High']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Required columns missing: {df.columns}")
            return None

        if len(df) < 20:
            print("❌ Not enough data for analysis")
            return None

        # Prepare EMAs
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        ltp = df['Close'].iloc[-1]

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

        # Max upside calculation - after buy or from listing date if no buy
        start_idx = cross_idx if cross_idx else df.index[0]
        post_start_df = df.loc[start_idx:]
        max_price = post_start_df['High'].max()
        max_price_date = post_start_df['High'].idxmax()
        max_upside_pct = round((max_price - base_price) / base_price * 100, 2)
        sessions_to_max_upside = df.index.get_loc(max_price_date) - df.index.get_loc(start_idx)

        return {
            "Listing Date": listing_date.strftime('%Y-%m-%d') if hasattr(listing_date, 'strftime') else listing_date,
            "Listed Price": round(base_price, 2),
            "LTP": round(ltp, 2),
            "BUY": "✅" if buy_signal else "❌",
            "Buying Date": buying_date,
            "Max Upside (%)": max_upside_pct,
            "# Sessions to Max Upside": sessions_to_max_upside,
            "EMA 20": round(df['EMA20'].iloc[-1], 2),
            "EMA 50": round(df['EMA50'].iloc[-1], 2),
            "U-curve": "✅" if u_curve_detected else "❌",
            "# Sessions in U-curve": sessions_to_u_curve,
            "% Dip from Base Price": percent_dip
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None


def run_trigger_analysis(ipo_df):
    """
    Given IPO DataFrame (with columns including Company Name, Listing Date, Issue Price),
    analyze triggers for all listed stocks with valid Listing Date and Issue Price.
    """

    results = []
    for _, row in ipo_df.iterrows():
        company = row.get("Company Name")
        listing_date = row.get("Listing Date")
        base_price = row.get("Issue Price (Rs.)")

        # Skip if not listed or missing data
        if pd.isna(listing_date) or pd.isna(base_price):
            continue

        # Derive ticker symbol (assume first word, remove special chars)
        symbol = company.split()[0].upper().replace("&", "").replace(".", "") + ".NS"

        price_df = get_price_data(symbol)
        if price_df is None or len(price_df) < 20:
            print(f"Skipping {company} due to insufficient price data")
            continue

        # Filter price_df from listing date onwards
        price_df = price_df[price_df.index >= pd.to_datetime(listing_date)]

        if price_df.empty:
            print(f"No price data after listing date for {company}")
            continue

        analysis = analyze_triggers(price_df, listing_date, base_price)
        if analysis:
            analysis["Stock Name"] = company
            results.append(analysis)

    if results:
        return pd.DataFrame(results)
    else:
        print("No triggers found for the given IPO data.")
        return pd.DataFrame()
