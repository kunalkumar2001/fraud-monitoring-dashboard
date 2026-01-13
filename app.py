import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="🚨 Live Fraud Monitoring",
    layout="wide"
)

# ---------------- STATE-SAFE AUTO REFRESH (60s) ----------------
st_autorefresh(interval=60_000, key="fraud_refresh")

# ---------------- FASTAPI CONFIG ----------------
FASTAPI_URL = "https://fraud-realtime-api.onrender.com/latest"

# ---------------- SESSION STATE INIT ----------------
if "offset" not in st.session_state:
    st.session_state.offset = 0

if "df_all" not in st.session_state:
    st.session_state.df_all = pd.DataFrame()

# ---------------- LOAD NEXT CHUNK (5000 ROWS) ----------------
def load_chunk(offset):
    response = requests.get(
        FASTAPI_URL,
        params={"offset": offset, "limit": 5000},
        timeout=15
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())

# ---------------- FETCH → APPEND → MOVE OFFSET ----------------
try:
    df_new = load_chunk(st.session_state.offset)

    if not df_new.empty:
        st.session_state.df_all = pd.concat(
            [st.session_state.df_all, df_new],
            ignore_index=True
        )
        st.session_state.offset += len(df_new)

except Exception as e:
    st.error("🚨 Unable to fetch live data from API")
    st.stop()

df_all = st.session_state.df_all

# ---------------- DISPLAY WINDOW ----------------
DISPLAY_ROWS = 5000
df_display = df_all.tail(DISPLAY_ROWS)

# ---------------- HEADER ----------------
st.title("🚨 Live Fraud Monitoring Dashboard")
st.caption("Loads 5,000 rows every 60 seconds | Rolling window display")

# ---------------- KPI METRICS ----------------
c1, c2, c3 = st.columns(3)
c1.metric("Total Loaded Rows", len(df_all))
c2.metric("Displayed Rows", len(df_display))
c3.metric("Fraud Count", (df_all["status"] == "FRAUD").sum())

st.divider()

# ---------------- 🚨 LIVE FRAUD ALERT ----------------
if not df_display.empty and (df_display["status"] == "FRAUD").any():
    st.error("🚨 FRAUD DETECTED IN RECENT TRANSACTIONS!", icon="🚨")
else:
    st.success("✅ No fraud in recent transactions")

# ---------------- 📈 FRAUD SCORE TREND ----------------
st.subheader("📈 Fraud Score Trend (Last 5,000 Records)")

st.line_chart(
    df_display.sort_values("event_time")
              .set_index("event_time")["fraud_score"]
)

# ---------------- TABLE STYLING ----------------
def highlight_fraud(row):
    return [
        "background-color: #ffcccc" if row["status"] == "FRAUD" else ""
        for _ in row
    ]

# ---------------- LATEST TRANSACTIONS ----------------
st.subheader("🧾 Latest Transactions (Last 5,000 Records)")

st.dataframe(
    df_display.style.apply(highlight_fraud, axis=1),
    width="stretch"
)

# ---------------- ALL FRAUD TRANSACTIONS ----------------
st.subheader("🔴 All Fraud Transactions (Loaded So Far)")

fraud_df = df_all[df_all["status"] == "FRAUD"]

if not fraud_df.empty:
    st.dataframe(
        fraud_df.style.apply(highlight_fraud, axis=1),
        width="stretch"
    )
else:
    st.info("No fraud transactions detected yet.")

# ---------------- FOOTER ----------------
st.caption(
    "⚡ Incremental loading: 5,000 rows per minute | "
    "UI shows latest 5,000 rows for performance"
)
