import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
import time

BACKUP_CSV = "ipo_data_backup.csv"

def extract_symbol(company_url):
    base_site = "https://www.chittorgarh.com"
    full_url = base_site + company_url
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(full_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try to extract NSE symbol
        label = soup.find(string="NSE Symbol")
        if label and label.find_next("strong"):
            return label.find_next("strong").text.strip()

        # Try to extract BSE Code if NSE not found
        label = soup.find(string="BSE Code")
        if label and label.find_next("strong"):
            return label.find_next("strong").text.strip()

    except Exception as e:
        print(f"⚠️ Error scraping symbol from {company_url}: {e}")

    return None

def fetch_all_ipo_data():
    base_url = "https://webnodejs.chittorgarh.com/cloud/report/data-read/82/1/6/{year}/0/0/mainboard/0?search=&v=20-53"
    headers = {"User-Agent": "Mozilla/5.0"}
    combined_data = []

    for year in [2024, 2025]:
        url = base_url.format(year=year)
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()["reportTableData"]

            for row in data:
                company_soup = BeautifulSoup(row["Company"], "html.parser")
                row["Company Name"] = company_soup.text.strip()
                row["Company URL"] = company_soup.a["href"] if company_soup.a else None

                lm_soup = BeautifulSoup(row["Lead Manager"], "html.parser")
                row["Lead Manager Name"] = lm_soup.text.strip()
                row["Lead Manager URL"] = lm_soup.a["href"] if lm_soup.a else None

                # Extract symbol from company detail page
                if row["Company URL"]:
                    row["Symbol"] = extract_symbol(row["Company URL"])
                    time.sleep(1)  # polite crawling
                else:
                    row["Symbol"] = None

            combined_data.extend(data)

        except Exception as e:
            print(f"⚠️ Failed to fetch IPO data for {year}: {e}")

    if not combined_data:
        return pd.DataFrame()

    df = pd.DataFrame(combined_data)

    # Convert columns
    df["Opening Date"] = pd.to_datetime(df["Opening Date"], errors="coerce")
    df["Closing Date"] = pd.to_datetime(df["Closing Date"], errors="coerce")
    df["Listing Date"] = pd.to_datetime(df["Listing Date"].replace("Yet to list", pd.NaT), errors="coerce")
    df["Issue Price (Rs.)"] = df["Issue Price (Rs.)"].str.extract(r'(\d+\.?\d*)').astype(float)
    df["Issue Amount (Rs.cr.)"] = pd.to_numeric(df["Issue Amount (Rs.cr.)"], errors="coerce")

    df = df.drop(columns=["FY"], errors="ignore")
    df = df.drop_duplicates(subset=["Company Name", "Opening Date", "Listing Date", "Issue Price (Rs.)"])

    return df

def get_combined_ipo_data():
    df = fetch_all_ipo_data()

    if not df.empty:
        df = df[[
            "Company Name", "Symbol", "Company URL", "Opening Date", "Closing Date", "Listing Date",
            "Issue Price (Rs.)", "Issue Amount (Rs.cr.)", "Listing at",
            "Lead Manager Name", "Lead Manager URL"
        ]].sort_values("Opening Date", ascending=False)

        df.to_csv(BACKUP_CSV, index=False)
    else:
        print("⚠️ Fetched data empty, loading from backup...")
        if os.path.exists(BACKUP_CSV):
            df = pd.read_csv(BACKUP_CSV, parse_dates=["Opening Date", "Closing Date", "Listing Date"])
        else:
            print("❌ No backup file found. Returning empty DataFrame.")
            return pd.DataFrame()

    return df
