import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Sentry | Live Fraud Monitoring",
    page_icon="🛰️",
    layout="wide",
)

# ============================================================
# THEME — dark ops-room palette (charcoal/navy + amber alert + teal safe)
# ============================================================
ACCENT_ALERT = "#F4573D"     # fraud / danger
ACCENT_SAFE = "#2FD4B4"      # safe / normal
ACCENT_INFO = "#5B8DEF"      # neutral accent
BG = "#0B0F14"
PANEL = "#121821"
BORDER = "#232C38"
TEXT = "#E7ECF2"
SUBTEXT = "#8A97A8"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {TEXT};
    }}
    .stApp {{
        background: radial-gradient(circle at 20% 0%, #101722 0%, {BG} 45%);
    }}
    #MainMenu, footer, header {{visibility: hidden;}}

    .sentry-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid {BORDER};
        padding-bottom: 18px;
        margin-bottom: 22px;
    }}
    .sentry-title {{
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
    }}
    .sentry-sub {{
        color: {SUBTEXT};
        font-size: 0.92rem;
        margin-top: 4px;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 999px;
        padding: 7px 14px;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', monospace;
        color: {SUBTEXT};
    }}
    .dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {ACCENT_SAFE};
        box-shadow: 0 0 8px {ACCENT_SAFE};
    }}
    .dot.alert {{ background: {ACCENT_ALERT}; box-shadow: 0 0 8px {ACCENT_ALERT}; }}

    .kpi-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-left: 3px solid var(--accent, {ACCENT_INFO});
        border-radius: 10px;
        padding: 16px 18px;
    }}
    .kpi-label {{
        color: {SUBTEXT};
        font-size: 0.78rem;
        font-weight: 500;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.9rem;
        font-weight: 700;
        color: {TEXT};
        line-height: 1;
    }}
    .kpi-delta {{
        font-size: 0.78rem;
        margin-top: 6px;
        color: {SUBTEXT};
    }}

    .section-title {{
        font-size: 1.05rem;
        font-weight: 600;
        margin: 4px 0 12px 0;
        color: {TEXT};
    }}

    .alert-banner {{
        background: linear-gradient(90deg, rgba(244,87,61,0.16), rgba(244,87,61,0.04));
        border: 1px solid rgba(244,87,61,0.4);
        border-radius: 10px;
        padding: 14px 18px;
        font-weight: 600;
        color: {ACCENT_ALERT};
        margin-bottom: 20px;
    }}
    .safe-banner {{
        background: linear-gradient(90deg, rgba(47,212,180,0.14), rgba(47,212,180,0.03));
        border: 1px solid rgba(47,212,180,0.35);
        border-radius: 10px;
        padding: 14px 18px;
        font-weight: 600;
        color: {ACCENT_SAFE};
        margin-bottom: 20px;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# AUTO REFRESH
# ============================================================
st_autorefresh(interval=60_000, key="fraud_refresh")

# ============================================================
# CONFIG
# ============================================================
FASTAPI_URL = "https://fraud-realtime-api.onrender.com/latest"
DISPLAY_ROWS = 5000
CITY_COORDS = {
    "New York": (40.71, -74.01), "Los Angeles": (34.05, -118.24),
    "Chicago": (41.88, -87.63), "Houston": (29.76, -95.37),
    "Phoenix": (33.45, -112.07), "Philadelphia": (39.95, -75.16),
    "San Antonio": (29.42, -98.49), "San Diego": (32.72, -117.16),
    "San Jose": (37.34, -121.89), "Dallas": (32.78, -96.80),
    "Austin": (30.27, -97.74), "Jacksonville": (30.33, -81.66),
    "Fort Worth": (32.75, -97.33), "Columbus": (39.96, -83.00),
    "Charlotte": (35.23, -80.84), "San Francisco": (37.77, -122.42),
    "Indianapolis": (39.77, -86.16), "Seattle": (47.61, -122.33),
    "Denver": (39.74, -104.99), "Boston": (42.36, -71.06),
    "Nashville": (36.16, -86.78), "Detroit": (42.33, -83.05),
    "Portland": (45.52, -122.68), "Memphis": (35.15, -90.05),
    "Las Vegas": (36.17, -115.14), "Baltimore": (39.29, -76.61),
    "Milwaukee": (43.04, -87.91), "Atlanta": (33.75, -84.39),
    "Miami": (25.76, -80.19),
}

# Priority columns shown first in every table — status/fraud_score are the
# whole point of this dashboard, so they should never be scrolled out of view.
PRIORITY_COLS = ["transaction_id", "status", "fraud_score", "amount",
                  "transaction_type", "location"]

PLOTLY_CONFIG = {"displayModeBar": False}

# ============================================================
# SESSION STATE
# ============================================================
if "offset" not in st.session_state:
    st.session_state.offset = 0
if "df_all" not in st.session_state:
    st.session_state.df_all = pd.DataFrame()
if "prev_fraud_count" not in st.session_state:
    st.session_state.prev_fraud_count = 0

# ============================================================
# FETCH → APPEND → MOVE OFFSET
# ============================================================
def load_chunk(offset):
    response = requests.get(
        FASTAPI_URL, params={"offset": offset, "limit": DISPLAY_ROWS}, timeout=15
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())

try:
    df_new = load_chunk(st.session_state.offset)
    if not df_new.empty:
        st.session_state.df_all = pd.concat(
            [st.session_state.df_all, df_new], ignore_index=True
        )
        st.session_state.offset += len(df_new)
except Exception:
    st.error("🚨 Unable to fetch live data from API")
    st.stop()

df_all = st.session_state.df_all
df_display = df_all.tail(DISPLAY_ROWS).copy()

current_fraud_count = int((df_all["status"] == "FRAUD").sum())
fraud_delta = current_fraud_count - st.session_state.prev_fraud_count
st.session_state.prev_fraud_count = current_fraud_count

recent_fraud = bool((df_display["status"] == "FRAUD").any()) if not df_display.empty else False

# ============================================================
# SIDEBAR FILTERS
# ============================================================
with st.sidebar:
    st.markdown("### Filters")
    tx_types = st.multiselect(
        "Transaction type",
        options=sorted(df_all["transaction_type"].dropna().unique()) if not df_all.empty else [],
    )
    locations = st.multiselect(
        "Location",
        options=sorted(df_all["location"].dropna().unique()) if not df_all.empty else [],
    )
    fraud_only = st.checkbox("Show fraud only", value=False)
    st.markdown("---")
    st.caption(f"Auto-refresh every 60s • {len(df_all):,} rows loaded so far")

def apply_filters(df):
    if tx_types:
        df = df[df["transaction_type"].isin(tx_types)]
    if locations:
        df = df[df["location"].isin(locations)]
    if fraud_only:
        df = df[df["status"] == "FRAUD"]
    return df

df_view = apply_filters(df_display)

# ============================================================
# HEADER
# ============================================================
dot_class = "dot alert" if recent_fraud else "dot"
status_text = "ALERT" if recent_fraud else "MONITORING"
st.markdown(f"""
<div class="sentry-header">
    <div>
        <p class="sentry-title">🛰️ Sentry — Live Fraud Monitoring</p>
        <p class="sentry-sub">Streaming rolling window · {DISPLAY_ROWS:,} most recent records</p>
    </div>
    <div class="status-pill"><span class="{dot_class}"></span>{status_text}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI CARDS
# ============================================================
fraud_rate = (current_fraud_count / len(df_all) * 100) if len(df_all) else 0
k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "TOTAL LOADED ROWS", f"{len(df_all):,}", None, ACCENT_INFO),
    (k2, "DISPLAYED ROWS", f"{len(df_display):,}", None, ACCENT_INFO),
    (k3, "FRAUD COUNT", f"{current_fraud_count:,}",
     (f"+{fraud_delta} since last refresh" if fraud_delta else "no change"), ACCENT_ALERT),
    (k4, "FRAUD RATE", f"{fraud_rate:.1f}%", None,
     ACCENT_ALERT if fraud_rate > 30 else ACCENT_SAFE),
]
for col, label, value, delta, accent in kpis:
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--accent:{accent}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-delta">{delta}</div>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)

st.write("")

# ============================================================
# ALERT BANNER
# ============================================================
if recent_fraud:
    st.markdown(
        '<div class="alert-banner">🚨 Fraud detected in recent transactions — review flagged rows below.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="safe-banner">✅ No fraud detected in the current window.</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# TREND + FRAUD RATE DONUT
# ============================================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<p class="section-title">📈 Fraud score trend (1-min buckets)</p>', unsafe_allow_html=True)
    if not df_display.empty:
        trend = df_display.copy()
        trend["event_time"] = pd.to_datetime(trend["event_time"])
        bucketed = (
            trend.set_index("event_time")["fraud_score"]
            .resample("1min").mean()
            .dropna()
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=bucketed.index, y=bucketed.values,
            mode="lines", line=dict(color=ACCENT_INFO, width=2),
            fill="tozeroy", fillcolor="rgba(91,141,239,0.12)",
            name="Avg fraud score",
        ))
        fig.add_hline(y=0.5, line_dash="dot", line_color=ACCENT_ALERT,
                       annotation_text="fraud threshold", annotation_font_color=ACCENT_ALERT)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT, height=340, margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor=BORDER, showgrid=False),
            yaxis=dict(gridcolor=BORDER, range=[0, 1]),
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Waiting for data...")

with col_right:
    st.markdown('<p class="section-title">🎯 Fraud share</p>', unsafe_allow_html=True)
    safe_count = len(df_all) - current_fraud_count
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Safe", "Fraud"], values=[safe_count, current_fraud_count],
        hole=0.68, marker=dict(colors=[ACCENT_SAFE, ACCENT_ALERT]),
        textinfo="none",
    )])
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", height=340, showlegend=True,
        legend=dict(orientation="h", y=-0.1, font=dict(color=TEXT)),
        margin=dict(l=10, r=10, t=30, b=10), font_color=TEXT,
        annotations=[dict(text=f"{fraud_rate:.1f}%", x=0.5, y=0.5,
                           font_size=26, font_color=ACCENT_ALERT, showarrow=False)],
    )
    st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================================
# FRAUD BY CITY
# ============================================================
st.markdown('<p class="section-title">📍 Fraud hotspots by city</p>', unsafe_allow_html=True)
if not df_all.empty and "location" in df_all.columns:
    city_fraud = (
        df_all[df_all["status"] == "FRAUD"]["location"]
        .value_counts().reset_index()
    )
    city_fraud.columns = ["location", "fraud_count"]
    city_fraud["lat"] = city_fraud["location"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
    city_fraud["lon"] = city_fraud["location"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
    unmapped = sorted(set(city_fraud.loc[city_fraud["lat"].isna(), "location"]))
    city_fraud = city_fraud.dropna(subset=["lat", "lon"])

    if unmapped:
        st.caption(f"No coordinates on file yet for: {', '.join(unmapped)} — add them to CITY_COORDS.")

    if not city_fraud.empty:
        fig_map = go.Figure(go.Scattergeo(
            lat=city_fraud["lat"], lon=city_fraud["lon"],
            text=city_fraud["location"] + ": " + city_fraud["fraud_count"].astype(str),
            marker=dict(
                size=city_fraud["fraud_count"],
                sizemode="area", sizeref=2. * city_fraud["fraud_count"].max() / (40. ** 2),
                color=ACCENT_ALERT, opacity=0.75, line=dict(width=0),
            ),
        ))
        fig_map.update_geos(
            scope="usa", bgcolor="rgba(0,0,0,0)",
            landcolor=PANEL, subunitcolor=BORDER, showlakes=False,
        )
        fig_map.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", height=360,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.caption("No mappable city coordinates yet.")

# ============================================================
# TABLES — column_config instead of row-wise Styler (much faster at 5k rows)
# ============================================================
def status_display(df):
    df = df.copy()
    df["status"] = df["status"].map(lambda s: "🔴 FRAUD" if s == "FRAUD" else "🟢 SAFE")
    # Put the columns people actually scan first (status/fraud_score), so
    # they're visible without scrolling right on a normal-width screen.
    front = [c for c in PRIORITY_COLS if c in df.columns]
    rest = [c for c in df.columns if c not in front]
    return df[front + rest]

col_cfg = {
    "fraud_score": st.column_config.ProgressColumn(
        "fraud_score", min_value=0.0, max_value=1.0, format="%.3f"
    ),
    "status": st.column_config.TextColumn("status"),
}

st.markdown('<p class="section-title">🧾 Latest transactions</p>', unsafe_allow_html=True)
if not df_view.empty:
    st.dataframe(status_display(df_view), column_config=col_cfg, use_container_width=True, height=360)
else:
    st.info("No rows match the current filters.")

st.markdown('<p class="section-title">🔴 All fraud transactions loaded so far</p>', unsafe_allow_html=True)
fraud_df = apply_filters(df_all[df_all["status"] == "FRAUD"])
if not fraud_df.empty:
    st.dataframe(status_display(fraud_df), column_config=col_cfg, use_container_width=True, height=360)
else:
    st.info("No fraud transactions detected yet.")

st.caption("⚡ Incremental loading: 5,000 rows/minute · UI shows the latest 5,000 rows for performance")
