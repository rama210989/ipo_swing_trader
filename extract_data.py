# extract_data.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
import os

BACKUP_CSV = "ipo_data_backup.csv"

def fetch_all_ipo_data():
    url = "https://webnodejs.chittorgarh.com/cloud/report/data-read/82/1/6/2025/0/0/mainboard/0?search=&v=20-53"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()["reportTableData"]

        for row in data:
            # Clean company name and URLs
            company_soup = BeautifulSoup(row["Company"], "html.parser")
            row["Company Name"] = company_soup.text.strip()
            row["Company URL"] = company_soup.a["href"] if company_soup.a else None

            lm_soup = BeautifulSoup(row["Lead Manager"], "html.parser")
            row["Lead Manager Name"] = lm_soup.text.strip()
            row["Lead Manager URL"] = lm_soup.a["href"] if lm_soup.a else None

        df = pd.DataFrame(data)

        # Convert columns
        df["Opening Date"] = pd.to_datetime(df["Opening Date"], errors="coerce")
        df["Closing Date"] = pd.to_datetime(df["Closing Date"], errors="coerce")
        df["Listing Date"] = pd.to_datetime(df["Listing Date"].replace("Yet to list", pd.NaT), errors="coerce")
        df["Issue Price (Rs.)"] = df["Issue Price (Rs.)"].str.extract(r'(\d+\.?\d*)').astype(float)
        df["Issue Amount (Rs.cr.)"] = pd.to_numeric(df["Issue Amount (Rs.cr.)"], errors="coerce")

        # Filter 2024 and 2025 IPOs only
        df = df[df["Opening Date"].dt.year.isin([2024, 2025])]

        # Drop FY column (not needed anymore)
        df = df.drop(columns=["FY"], errors="ignore")

        # Remove duplicates
        df = df.drop_duplicates(subset=[
            "Company Name", "Opening Date", "Listing Date", "Issue Price (Rs.)"
        ])

        return df

    except Exception as e:
        print(f"⚠️ Failed to fetch IPO data: {e}")
        return pd.DataFrame()

def get_combined_ipo_data():
    df = fetch_all_ipo_data()

    if not df.empty:
        df = df[[
            "Company Name", "Company URL", "Opening Date", "Closing Date", "Listing Date",
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
