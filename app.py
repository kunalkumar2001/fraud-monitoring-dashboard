import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

st.set_page_config(page_title="Fraud Monitoring Dashboard", layout="wide")

# 🔐 Neon credentials (use Streamlit secrets later)
NEON_HOST = "ep-rapid-truth-a1jtm7e5.ap-southeast-1.aws.neon.tech"
NEON_DB = "neondb"
NEON_USER = "neondb_owner"
NEON_PASSWORD = quote_plus(st.secrets["npg_TdgkZ5vEQUm4"])

engine = create_engine(
    f"postgresql+psycopg2://{NEON_USER}:{NEON_PASSWORD}"
    f"@{NEON_HOST}:5432/{NEON_DB}?sslmode=require"
)

st.title("🚨 Live Fraud Monitoring Dashboard")

@st.cache_data(ttl=60)
def load_data():
    query = """
    SELECT *
    FROM fraud_monitor_logs
    ORDER BY event_time DESC
    LIMIT 1000;
    """
    return pd.read_sql(query, engine)

df = load_data()

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", len(df))
col2.metric("Fraud Transactions", (df["status"] == "FRAUD").sum())
col3.metric("Avg Fraud Score", round(df["fraud_score"].mean(), 3))

st.divider()

# Charts
st.subheader("Fraud vs Safe")
st.bar_chart(df["status"].value_counts())

st.subheader("Fraud Score Over Time")
st.line_chart(df.sort_values("event_time")[["event_time", "fraud_score"]].set_index("event_time"))

st.subheader("Latest Transactions")
st.dataframe(df.head(20))
