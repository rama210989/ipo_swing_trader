import requests
import pandas as pd

def get_nse_recent_ipos():
    url = "https://www.nseindia.com/api/ipo-track-record"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/market-data/new-ipo"
    }

    session = requests.Session()
    session.headers.update(headers)
    session.get("https://www.nseindia.com", timeout=5)

    r = session.get(url, timeout=10)

    if "application/json" not in r.headers.get("Content-Type", ""):
        raise ValueError("NSE did not return JSON (likely blocked). Try again later.")

    data = r.json()
    ipo_list = data.get("data", [])
    df = pd.DataFrame(ipo_list)
    df['issuePrice'] = pd.to_numeric(df['issuePrice'], errors='coerce')
    df['listDate'] = pd.to_datetime(df['listDate'], errors='coerce')
    df = df[df['listDate'] >= pd.Timestamp.now() - pd.DateOffset(years=1)]
    df = df[['companyName', 'symbol', 'issuePrice', 'listDate']]
    return df
