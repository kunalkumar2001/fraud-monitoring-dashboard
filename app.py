import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="🚨 Live Fraud Monitoring",
    layout="wide"
)

# ---------------- AUTO REFRESH (EVERY 60s) ----------------
# 🔄 SAFE near real-time refresh (5 seconds)
st.query_params["refresh"] = str(int(datetime.now().timestamp()))
st.markdown(
    "<meta http-equiv='refresh' content='5'>",
    unsafe_allow_html=True
)


# ---------------- DB CONFIG ----------------
NEON_HOST = "ep-rapid-truth-a1jtm7e5.ap-southeast-1.aws.neon.tech"
NEON_DB = "neondb"
NEON_USER = "neondb_owner"
NEON_PASSWORD = quote_plus(st.secrets["NEON_PASSWORD"])

engine = create_engine(
    f"postgresql+psycopg2://{NEON_USER}:{NEON_PASSWORD}"
    f"@{NEON_HOST}:5432/{NEON_DB}?sslmode=require"
)

# ---------------- LOAD ALL DATA ----------------
@st.cache_data(ttl=60)
def load_data():
    query = """
    SELECT *
    FROM fraud_monitor_logs
    ORDER BY event_time DESC;
    """
    return pd.read_sql(query, engine)

df = load_data()

# ---------------- HEADER ----------------
st.title("🚨 Live Fraud Monitoring Dashboard")
st.caption("Auto-refresh every 60 seconds | Live Neon PostgreSQL")

# ---------------- KPI METRICS ----------------
total_txn = len(df)
fraud_txn = (df["status"] == "FRAUD").sum()
avg_score = round(df["fraud_score"].mean(), 3)

c1, c2, c3 = st.columns(3)
c1.metric("Total Transactions", total_txn)
c2.metric("Fraud Transactions", fraud_txn)
c3.metric("Avg Fraud Score", avg_score)

st.divider()

# ---------------- 🚨 RED FRAUD ALERT ----------------
if fraud_txn > 0:
    st.error(
        f"🚨 ALERT: {fraud_txn} FRAUD transaction(s) detected!",
        icon="🚨"
    )
else:
    st.success("✅ No fraud detected. System is SAFE.")

# ---------------- 📈 FRAUD SCORE TREND ----------------
st.subheader("📈 Fraud Score Trend (All Transactions)")

df_sorted = df.sort_values("event_time")
st.line_chart(df_sorted.set_index("event_time")["fraud_score"])

# ---------------- 🧾 LATEST TRANSACTIONS ----------------
st.subheader("🧾 Latest Transactions (All Data)")

rows_to_show = st.slider(
    "Select number of recent transactions to view",
    min_value=10,
    max_value=min(5000, len(df)),
    value=min(200, len(df)),
    step=50
)

def highlight_fraud(row):
    return ["background-color: #ffcccc" if row["status"] == "FRAUD" else "" for _ in row]

styled_latest = (
    df.head(rows_to_show)
    .style
    .apply(highlight_fraud, axis=1)
)

st.dataframe(styled_latest, width="stretch")

# ---------------- 🔴 FRAUD TRANSACTIONS ----------------
st.subheader("🔴 Fraud Transactions (All)")

fraud_df = df[df["status"] == "FRAUD"]

if len(fraud_df) > 0:
    styled_fraud = fraud_df.style.apply(highlight_fraud, axis=1)
    st.dataframe(styled_fraud, width="stretch")
else:
    st.info("No fraud transactions detected.")

# ---------------- FOOTER ----------------
st.caption("🔄 Dashboard auto-refreshes every 60 seconds | Live Monitoring Enabled")
