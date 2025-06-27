from ipo_scraper import get_nse_recent_ipos

st.title("📈 Indian IPO Monitor (NSE Source)")

df = get_nse_recent_ipos()
st.dataframe(df)
