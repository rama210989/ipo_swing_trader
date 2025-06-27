import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_ipo_list_chittorgarh():
    url = "https://www.chittorgarh.com/report/latest-ipos-in-india/82/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table")
    rows = table.find_all("tr")

    data = []
    for row in rows[1:]:  # Skip header row
        cols = row.find_all("td")
        if len(cols) >= 6:
            company = cols[0].text.strip()
            listing_date = pd.to_datetime(cols[4].text.strip(), errors='coerce')
            issue_price = cols[2].text.strip().replace("₹", "").replace(",", "")
            try:
                issue_price = float(issue_price)
            except:
                issue_price = None
            data.append([company, listing_date, issue_price])

    df = pd.DataFrame(data, columns=["Company", "Listing Date", "Issue Price"])
    df = df[df["Listing Date"] >= pd.Timestamp.now() - pd.DateOffset(years=1)]
    return df
