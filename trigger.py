import pandas as pd
import yfinance as yf
import time

def get_price_data(ticker, max_retries=3, sleep_sec=1):
    ticker_full = ticker if ticker.endswith('.NS') else ticker + '.NS'
    df = None

    for attempt in range(max_retries):
        try:
            df = yf.download(ticker_full, progress=False, period="5d", interval="1d", auto_adjust=True)
            if not df.empty:
                break
        except Exception as e:
            print(f"⚠️ Error fetching {ticker_full}: {e}")
        time.sleep(sleep_sec)

    if df is None or df.empty:
        print(f"❌ No data found for {ticker_full}")
        return None

    return df

def run_trigger_analysis(ipo_df):
    """
    Return summary of:
    - Stock Name
    - Listing Date
    - Listing Price (Issue Price)
    - LTP (last close)
    """

    summary_data = []

    for _, row in ipo_df.iterrows():
        company = row.get("Company Name")
        listing_date = row.get("Listing Date")
        issue_price = row.get("Issue Price (Rs.)")

        if pd.isna(listing_date) or pd.isna(issue_price):
            continue

        # Build Ticker
        symbol = company.split()[0].upper().replace("&", "").replace(".", "") + ".NS"

        # Get LTP
        price_df = get_price_data(symbol)
        if price_df is None or price_df.empty:
            continue

        ltp = round(price_df['Close'].iloc[-1], 2)

        summary_data.append({
            "Stock Name": company,
            "Listing Date": listing_date.strftime("%Y-%m-%d"),
            "Listing Price": round(issue_price, 2),
            "LTP": ltp
        })

    return pd.DataFrame(summary_data)
