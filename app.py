import streamlit as st
import pandas as pd
from trigger import get_price_data, run_trigger_analysis
from extract_data import get_combined_ipo_data

# --- Page setup ---
st.set_page_config(layout="wide", page_title="IPO Swing Trader")
st.title("📈 IPO Tools: Trigger Monitor")

# --- Tab Layout ---
tab1, tab2 = st.tabs(["🚀 IPO LTP Summary", "💰 Trade Simulator (Coming Soon)"])

# --- Trigger Tab ---
with tab1:
    st.markdown("*Data Source: Chittorgarh + Yahoo Finance*")

    @st.cache_data(ttl=3600, show_spinner="Fetching IPO data...")
    def load_ipo_data():
        return get_combined_ipo_data()

    if st.button("🔁 Refresh IPO List"):
        st.cache_data.clear()
        st.success("IPO list refreshed. Click 'Run Trigger Analysis' again.")

    ipo_df = load_ipo_data()

    st.subheader("📋 IPO List (from Chittorgarh)")
    st.markdown(f"Total IPOs: **{len(ipo_df)}**")

    if not ipo_df.empty:
        latest_date = ipo_df['Opening Date'].max()
        if pd.notnull(latest_date):
            st.markdown(f"Latest IPO Opening Date: **{latest_date.strftime('%Y-%m-%d')}**")

    st.dataframe(ipo_df[[
        "Company Name", "Opening Date", "Listing Date", "Issue Price (Rs.)",
        "Issue Amount (Rs.cr.)", "Listing at"
    ]])

    if st.button("🚀 Run Trigger Analysis"):
        with st.spinner("Getting LTPs, please wait..."):
            trigger_results = run_trigger_analysis(ipo_df)

        if not trigger_results.empty:
            display_cols = ["Stock Name", "Listing Date", "Listing Price", "LTP"]
            trigger_results = trigger_results[display_cols]

            st.subheader("📊 IPO LTP Summary Table")
            st.dataframe(trigger_results)

            st.markdown("""
            ### 🧾 Column Descriptions:
            - **Stock Name:** Company name from IPO list  
            - **Listing Date:** Date the stock listed  
            - **Listing Price:** Issue price from IPO  
            - **LTP:** Current/Last traded price from Yahoo Finance  
            """)
        else:
            st.info("⚠️ No IPOs with valid listing date or stock data found.")

# --- Trade Simulator Tab (Placeholder) ---
with tab2:
    st.subheader("💰 Trade Simulator")
    st.info("🚧 Coming soon: Simulate swing trades after trigger confirmation.")
