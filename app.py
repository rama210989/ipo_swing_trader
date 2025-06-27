import streamlit as st
from ipo_scraper import get_ipo_list_chittorgarh

st.title("📈 Indian IPO Swing Trading Monitor")

df = get_ipo_list_chittorgarh()
st.write("### Recent IPOs in the Last 1 Year")
st.dataframe(df)
