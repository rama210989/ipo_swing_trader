import streamlit as st
import pandas as pd

st.title("📈 Indian IPO Monitor (Using Uploaded CSV)")

# Replace with your actual raw GitHub CSV URL here:
csv_url = "https://raw.githubusercontent.com/rama210989/ipo_swing_trader/refs/heads/main/IPO%20365%20finallynitin%2C%20Technical%20Analysis%20Scanner.csv"

@st.cache_data  # Cache to avoid reloading on every interaction
def load_ipo_csv(url):
    df = pd.read_csv(url)
    
    # Clean columns:
    # Remove quotes from column names if any, strip spaces
    df.columns = [col.strip().replace('"', '') for col in df.columns]

    # Clean and convert columns
    df['% Chg'] = df['% Chg'].str.replace('%', '', regex=False).astype(float)
    df['Price'] = df['Price'].astype(float)
    # Remove commas from Volume and convert to int
    df['Volume'] = df['Volume'].str.replace(',', '', regex=False).astype(int)
    
    return df

df = load_ipo_csv(csv_url)

st.dataframe(df)

# Optional: Add filters for convenience
chg_filter = st.slider("% Change filter", float(df['% Chg'].min()), float(df['% Chg'].max()), (float(df['% Chg'].min()), float(df['% Chg'].max())))
price_filter = st.slider("Price filter", float(df['Price'].min()), float(df['Price'].max()), (float(df['Price'].min()), float(df['Price'].max())))

filtered_df = df[(df['% Chg'] >= chg_filter[0]) & (df['% Chg'] <= chg_filter[1]) & 
                 (df['Price'] >= price_filter[0]) & (df['Price'] <= price_filter[1])]

st.markdown(f"### Filtered results ({len(filtered_df)})")
st.dataframe(filtered_df)
