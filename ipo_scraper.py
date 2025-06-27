import requests
import pandas as pd

def get_ipo_list_chittorgarh():
    url = "https://www.chittorgarh.com/report/latest-ipos-in-india/82/"
    tables = pd.read_html(url)
    
    df = tables[0]
    df.columns = df.columns.str.strip()
    
    df['Listing Date'] = pd.to_datetime(df['Listing Date'], errors='coerce')
    df = df[df['Listing Date'] >= pd.Timestamp.now() - pd.DateOffset(years=1)]
    
    df['Symbol'] = df['Company'].str.extract(r'\((.*?)\)')
    return df[['Company Name', 'Listing Date', 'Issue Price', 'Symbol']].dropna()
