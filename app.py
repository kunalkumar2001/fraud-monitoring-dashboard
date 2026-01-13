import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

st.set_page_config(page_title="Fraud Monitoring Dashboard", layout="wide")

NEON_HOST = "ep-rapid-truth-a1jtm7e5.ap-southeast-1.aws.neon.tech"
NEON_DB = "neondb"
NEON_USER = "neondb_owner"

NEON_PASSWORD = quote_plus(st.secrets["NEON_PASSWORD"])

engine = create_engine(
    f"postgresql+psycopg2://{NEON_USER}:{NEON_PASSWORD}"
    f"@{NEON_HOST}:5432/{NEON_DB}?sslmode=require"
)

st.title("🚨 Live Fraud Monitoring Dashboard")

@st.cache_data(ttl=60)
def load_data():
    return pd.read_sql(
        "SELECT * FROM fraud_monitor_logs ORDER BY event_time DESC LIMIT 1000;",
        engine
    )

df = load_data()

st.metric("Total Transactions", len(df))
st.metric("Fraud Transactions", (df["status"] == "FRAUD").sum())
st.metric("Avg Fraud Score", round(df["fraud_score"].mean(), 3))

st.dataframe(df.head(20))
