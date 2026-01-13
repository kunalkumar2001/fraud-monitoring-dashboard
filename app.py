import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="🚨 Live Fraud Monitoring",
    layout="wide"
)

# ---------------- SAFE REAL-TIME REFRESH (3s) ----------------
st.query_params["refresh"] = str(int(datetime.now().timestamp()))
st.markdown(
    "<meta http-equiv='refresh' content='3'>",
    unsafe_allow_html=True
)

# ---------------- FASTAPI CONFIG ----------------
# ⚠️ Change if deployed to cloud
FASTAPI_URL = "https://fraud-realtime-api.onrender.com/"

# ---------------- LOAD DATA FROM FASTAPI ----------------
@st.cache_data(ttl=3)
def load_data():
    response = requests.get(FASTAPI_URL, timeout=5)
    response.raise_for_status()
    return pd.DataFrame(response.json())

df = load_data()

# ---------------- HEADER ----------------
st.title("🚨 Live Fraud Monitoring Dashboard")
st.caption("True real-time | FastAPI + PostgreSQL + Streamlit")

# ---------------- KPI METRICS ----------------
total_txn = len(df)
fraud_txn = (df["status"] == "FRAUD").sum()
avg_score = round(df["fraud_score"].mean(), 3)

c1, c2, c3 = st.columns(3)
c1.metric("Total Transactions", total_txn)
c2.metric("Fraud Transactions", fraud_txn)
c3.metric("Avg Fraud Score", avg_score)

st.divider()

# ---------------- 🚨 REAL-TIME FRAUD ALERT ----------------
if fraud_txn > 0:
    st.error(
        f"🚨 LIVE ALERT: {fraud_txn} FRAUD transaction(s) detected!",
        icon="🚨"
    )
else:
    st.success("✅ No fraud detected. System is SAFE.")

# ---------------- 📈 FRAUD SCORE TREND ----------------
st.subheader("📈 Fraud Score Trend (All Transactions)")

df_sorted = df.sort_values("event_time")
st.line_chart(
    df_sorted.set_index("event_time")["fraud_score"]
)

# ---------------- 🧾 LATEST TRANSACTIONS ----------------
st.subheader("🧾 Latest Transactions (Live)")

rows_to_show = st.slider(
    "Select number of recent transactions",
    min_value=10,
    max_value=min(5000, len(df)),
    value=min(200, len(df)),
    step=50
)

def highlight_fraud(row):
    return [
        "background-color: #ffcccc" if row["status"] == "FRAUD" else ""
        for _ in row
    ]

styled_latest = (
    df.head(rows_to_show)
    .style
    .apply(highlight_fraud, axis=1)
)

st.dataframe(styled_latest, width="stretch")

# ---------------- 🔴 FRAUD TRANSACTIONS ONLY ----------------
st.subheader("🔴 Fraud Transactions (Live)")

fraud_df = df[df["status"] == "FRAUD"]

if not fraud_df.empty:
    styled_fraud = fraud_df.style.apply(highlight_fraud, axis=1)
    st.dataframe(styled_fraud, width="stretch")
else:
    st.info("No fraud transactions detected.")

# ---------------- FOOTER ----------------
st.caption("⚡ True real-time monitoring via FastAPI | Updates every 3 seconds")
