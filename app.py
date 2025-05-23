import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import requests
from requests.utils import quote
import random
import time

TRIVIA_LIST = [
    "💰 The Bombay Stock Exchange (BSE) is the oldest stock exchange in Asia, founded in 1875.",
    "📊 The Nifty 50 index covers about 66.8% of the float-adjusted market capitalization of the NSE.",
    "📈 India’s stock market is the 5th largest in the world by market cap.",
    "📉 A 'bear market' refers to a market that has fallen 20% or more from recent highs.",
    "🔁 The term 'Nifty' comes from combining 'National' and 'Fifty'.",
    "🌍 FIIs (Foreign Institutional Investors) play a major role in India’s stock volatility.",
    "📎 Circuit breakers are used by SEBI to control extreme stock market volatility.",
    "🚀 The biggest one-day gain for Sensex was over 2400 points (March 2020)."
]

# ----------------------
# Configuration
# ----------------------
st.set_page_config(
    page_title="Indian Market Indices Dashboard",
    layout="wide",
    page_icon="📈"
)

# ----------------------
# Constants
# ----------------------
API_URL_TEMPLATE = "https://priceapi.moneycontrol.com/pricefeed/notapplicable/inidicesindia/{}"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.moneycontrol.com/"
}

INDICATORS = [
    {"code": "in;cjn", "label": "Nifty Commodities"},
    {"code": "in;nnx", "label": "Nifty Energy"},
    {"code": "in;cnxt", "label": "Nifty FMCG"},
    {"code": "in;ncx", "label": "Nifty Healthcare"},
    {"code": "in;cnxs", "label": "Nifty Infrastructure"},
    {"code": "in;mfy", "label": "Nifty IT"},
    {"code": "mc;nscapf", "label": "Nifty Private Banks"},
    {"code": "in;IDXN", "label": "Nifty Public Sector"},
    {"code": "in;cnxa", "label": "Nifty Auto"},
    {"code": "in;cnit", "label": "Nifty IT Services"},
    {"code": "in;cuk", "label": "Nifty Media"},
    {"code": "in;cnxf", "label": "Nifty Financial Services"},
    {"code": "in;cpr", "label": "Nifty Pharma"},
    {"code": "in;cfm", "label": "Nifty Metal"},
    {"code": "in;CNXM", "label": "Nifty Midcap"},
    {"code": "in;crl", "label": "Nifty Realty"},
    {"code": "in;cnmx", "label": "Nifty Smallcap"},
    {"code": "in;cgy", "label": "Nifty Green Energy"},
    {"code": "in;nxb", "label": "Nifty Banks"},
    {"code": "in;cfr", "label": "Nifty Retail"},
    {"code": "in;cnxz", "label": "Nifty Oil & Gas"},
    {"code": "in;cnxc", "label": "Nifty Consumer Durables"},
    {"code": "in;cps", "label": "Nifty PSU Banks"},
    {"code": "in;crv", "label": "Nifty Value 20"},
    {"code": "mc;oilgas", "label": "MC Oil & Gas"},
    {"code": "mc;nmidcaps", "label": "MC Nifty Midcaps"},
    {"code": "mc;nm150qlty", "label": "MC Nifty150 Quality 30"},
]

def decorate_label(label):
    emojis = {
        "Energy": "⚡", "IT": "💻", "Pharma": "💊",
        "Auto": "🚗", "Bank": "🏦", "Retail": "🛍️",
        "Media": "🎬", "Realty": "🏘️", "Metal": "🪙"
    }
    for key, emoji in emojis.items():
        if key in label:
            return f"{emoji} {label}"
    return label

# ----------------------
# Fetch Functions
# ----------------------
def fetch_indicator(code: str, label: str, retries=3, delay=1) -> dict:
    url = API_URL_TEMPLATE.format(quote(code))
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=5)
            resp.raise_for_status()
            parsed = resp.json()
            if not isinstance(parsed, dict) or "data" not in parsed or parsed["data"] is None:
                raise ValueError(f"Invalid JSON response for {label}")
            data = parsed["data"]
            price = float(data.get("pricecurrent", "0").replace(",", ""))
            change = float(data.get("pricechange", "0").replace(",", ""))
            pct = float(data.get("pricepercentchange", "0").replace("%", ""))
            return {"label": label, "price": price, "change": change, "pct": pct}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

@st.cache_data(ttl=300)
def fetch_all_indicators() -> pd.DataFrame:
    records = []
    for ind in INDICATORS:
        try:
            rec = fetch_indicator(ind["code"], ind["label"])
            records.append(rec)
        except Exception as e:
            st.warning(f"Failed to fetch {ind['label']}: {e}")
    return pd.DataFrame(records)

# ----------------------
# Sidebar Controls
# ----------------------
st.sidebar.header("🔧 Controls")
all_labels = [ind["label"] for ind in INDICATORS]

selection = st.sidebar.multiselect("Select Sectors (or leave empty for All)", options=all_labels)
search_query = st.sidebar.text_input("🔍 Search Sector")
view = st.sidebar.radio("Choose View", ("Summary Cards", "Heatmap", "Bar Chart"))
theme = st.sidebar.radio("🌓 Theme Mode", ["Light", "Dark"])

# ----------------------
# Theme Logic
# ----------------------
if theme == "Dark":
    st.markdown("""
    <style>
        .main { background-color: #2e2e2e; color: white; }
        .sidebar .sidebar-content { background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .main { background-color: white; color: black; }
        .sidebar .sidebar-content { background-color: #f0f0f0; }
    </style>
    """, unsafe_allow_html=True)

# ----------------------
# Main Display
# ----------------------
st.title("📈 Indian Market Indices Dashboard")
st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

now = datetime.now()
if now.weekday() >= 5 or now.hour < 9 or now.hour > 16:
    st.warning("⚠️ Market may be closed — data might not reflect live changes.")

with st.spinner("⏳ Fetching live market data..."):
    st.markdown("### 🧠 Did You Know?")
    st.info(random.choice(TRIVIA_LIST))
    df = fetch_all_indicators()

# ----------------------
# Data Filtering
# ----------------------
if selection:
    df = df[df["label"].isin(selection)]

if search_query:
    df = df[df["label"].str.contains(search_query, case=False)]

if df.empty:
    st.warning("No data available for selected filters. Try adjusting your selection.")
else:
    st.markdown("### 📈 Top Performers")
    top_gainers = df.sort_values("pct", ascending=False).head(3)
    top_losers = df.sort_values("pct").head(3)
    col1, col2 = st.columns(2)
    with col1:
        st.success("**Top Gainers**")
        for _, row in top_gainers.iterrows():
            st.markdown(f"📈 **{row['label']}** — `{row['pct']}%`")
    with col2:
        st.error("**Top Losers**")
        for _, row in top_losers.iterrows():
            st.markdown(f"📉 **{row['label']}** — `{row['pct']}%`")

    if view == "Summary Cards":
        st.subheader("Key Metrics")
        for start in range(0, len(df), 4):
            cols = st.columns(4)
            for col, (_, row) in zip(cols, df.iloc[start:start + 4].iterrows()):
                col.metric(
                    label=decorate_label(row["label"]),
                    value=f"₹{row['price']:,}",
                    delta=f"{row['change']:+.2f} ({row['pct']:+.2f}%)"
                )

    elif view == "Heatmap":
        st.subheader("Sector Performance Heatmap")
        heatmap = go.Figure(
            data=go.Heatmap(
                z=[df["pct"].tolist()],
                x=df["label"].tolist(),
                y=[""],
                colorscale="RdYlGn",
                colorbar=dict(title="% Change"),
                zmid=0
            )
        )
        heatmap.update_layout(height=300, xaxis_tickangle=-45, margin=dict(t=50, b=100))
        st.plotly_chart(heatmap, use_container_width=True)

    else:
        st.subheader("Sector % Change - Bar Chart")
        bar = px.bar(
            df.sort_values("pct"),
            x="pct", y="label",
            orientation="h",
            labels={"pct": "% Change", "label": "Sector"},
            title="Sector % Change"
        )
        st.plotly_chart(bar, use_container_width=True)

    st.subheader("📊 Sector Price Distribution")
    pie = px.pie(df, names="label", values="price", title="Market Sector Distribution")
    st.plotly_chart(pie, use_container_width=True)

    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download data as CSV",
        data=convert_df_to_csv(df),
        file_name="market_indices.csv",
        mime="text/csv",
    )

# ----------------------
# Footer
# ----------------------
st.markdown("""
    <hr style='margin-top: 3rem;'/>
    <div style='text-align: center; color: gray; font-size: 0.9rem;'>
        Built with ❤️ by <strong>Irika Ishani</strong><br>
        Live data sourced from <a href='https://www.moneycontrol.com/' target='_blank'>Moneycontrol</a>
    </div>
""", unsafe_allow_html=True)
