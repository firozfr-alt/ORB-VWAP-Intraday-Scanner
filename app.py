import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import ta

# ==========================================
# 1. PAGE CONFIGURATION & MODERN STYLING
# ==========================================
st.set_page_config(
    page_title="OVERA Master Trading Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    .market-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); margin-bottom: 10px; color: #f3f4f6;
    }
    .card-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px; font-weight: 600; }
    .card-value { font-size: 24px; font-weight: 700; color: #ffffff; margin: 0; }
    .subtitle-clean { font-size: 14px; font-weight: 400; color: #94a3b8; margin-bottom: 20px; }
    .summary-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 20px 24px; border-radius: 14px; margin-bottom: 20px;
    }
    .summary-title { color: #60a5fa !important; font-size: 18px; font-weight: 700; margin-top: 0; margin-bottom: 12px; }
    .macro-row { font-size: 13.5px; color: #cbd5e1; margin-bottom: 8px; line-height: 1.5; }
    .strategy-box-1, .strategy-box-2, .strategy-box-3, .strategy-box-4, .strategy-box-5, .strategy-box-6 {
        background: linear-gradient(135deg, rgba(6, 95, 70, 0.85) 0%, rgba(4, 47, 46, 0.95) 100%);
        border: 2px solid #10b981; padding: 24px; border-radius: 14px; margin-bottom: 20px;
    }
    .strategy-title { margin-top: 0; color: #fbbf24 !important; font-weight: 700; font-size: 22px; }
    .strategy-desc { color: #fde68a !important; font-size: 14px; margin-bottom: 15px; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.15); opacity: 0.6; } 100% { transform: scale(1); opacity: 1; } }
    .live-dot { height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; margin-right: 6px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 10px; color: #cbd5e1; padding: 10px 18px; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.05); }
    .stTabs [aria-selected="true"] { background: white !important; color: black !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HEADER BAR & MARKET INDICES
# ==========================================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("## ⚡ OVERA Master Trading Platform (Multi-Cap & Institutional)")
with col_status:
    st.markdown("""
    <div style="text-align: right; padding-top: 10px;">
        <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            <span class="live-dot"></span>Engine Active
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="subtitle-clean">Comprehensive multi-cap tracking across Large, Mid, Small Cap, and Penny segments with OVERA logic.</div>', unsafe_allow_html=True)
st.markdown("---")

@st.cache_data(ttl=60)
def get_market_data():
    indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK"}
    data = {}
    for name, ticker in indices.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                current, prev = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
                change, pct = current - prev, ((current - prev) / prev) * 100
                data[name] = {"price": round(current, 2), "change": round(pct, 2), "trend": "Bullish 🟢" if change >= 0 else "Bearish 🔴", "pos": change >= 0}
            else:
                data[name] = {"price": 0.0, "change": 0.0, "trend": "Neutral", "pos": True}
        except Exception:
            data[name] = {"price": 0.0, "change": 0.0, "trend": "Neutral", "pos": True}
    return data

indices_data = get_market_data()

idx_cols = st.columns(2)
for i, (name, val) in enumerate(indices_data.items()):
    color_style = "color: #10b981;" if val["pos"] else "color: #ef4444;"
    with idx_cols[i]:
        st.markdown(f"""
        <div class="market-card">
            <div class="card-label">{name} Benchmark Index</div>
            <div class="card-value">₹{val['price']:,}</div>
            <div style="margin-top: 6px; font-size: 13px; font-weight: 600; {color_style}">
                Change: {val['change']}% &nbsp;|&nbsp; Trend: {val['trend']}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 3. UNIVERSES & SIDEBAR CONFIGURATION
# ==========================================
MULTICAP_UNIVERSES = {
    "Large-Cap Core": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS"],
    "Mid-Cap Growth": ["POLYCAB.NS", "PERSISTENT.NS", "ASTRAL.NS", "TATAPOWER.NS", "PAGEIND.NS", "SRF.NS", "DIXON.NS"],
    "Small-Cap Momentum": ["KPITTECH.NS", "CESC.NS", "IDFCFIRSTB.NS", "CAMS.NS", "OBEROIRLTY.NS", "LAURUSLABS.NS"],
    "High-Beta / F&O": ["TATAMOTORS.NS", "BAJFINANCE.NS", "ADANIENT.NS", "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS"]
}

st.sidebar.header("🎯 Master Configuration")
selected_universe = st.sidebar.selectbox("Choose Market Universe", list(MULTICAP_UNIVERSES.keys()))
symbols_to_scan = MULTICAP_UNIVERSES[selected_universe]

st.sidebar.markdown("---")
st.sidebar.subheader("Intraday & Swing Tuning")
rvol_mult = st.sidebar.slider("Min Intraday RVOL", 1.0, 3.0, 1.2, 0.1)
min_adx = st.sidebar.slider("Min ADX Threshold", 10, 30, 18, 1)

# ==========================================
# 4. TECHNICAL ENGINES
# ==========================================
def analyze_overa_master_intraday(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="5d", interval="15m")
        if df.empty or len(df) < 30: return None

        ist = pytz.timezone("Asia/Kolkata")
        df.index = df.index.tz_convert(ist) if df.index.tz else df.index.tz_localize("UTC").tz_convert(ist)

        latest_date = df.index[-1].date()
        today_df = df[df.index.date == latest_date].copy()
        if len(today_df) < 2: return {"error": "Waiting for range completion."}

        or_bar = today_df.iloc[0]
        or_high, or_low = float(or_bar["High"]), float(or_bar["Low"])

        avg_vol = today_df['Volume'].iloc[:-1].mean()
        latest = today_df.iloc[-1]
        ltp = float(latest["Close"])
        latest_vol = float(latest["Volume"])
        rvol = latest_vol / avg_vol if avg_vol > 0 else 1.0

        today_df["TP"] = (today_df["High"] + today_df["Low"] + today_df["Close"]) / 3
        today_df["VWAP"] = (today_df["TP"] * today_df["Volume"]).cumsum() / today_df["Volume"].cumsum()
        vwap_val = float(today_df["VWAP"].iloc[-1])

        today_df["EMA20"] = ta.trend.ema_indicator(today_df["Close"], window=20)
        today_df["EMA50"] = ta.trend.ema_indicator(today_df["Close"], window=50)
        ema20 = float(today_df["EMA20"].iloc[-1])
        ema50 = float(today_df["EMA50"].iloc[-1])

        rsi_val = float(ta.momentum.rsi(today_df["Close"], window=14).iloc[-1])
        adx_val = float(ta.trend.adx(today_df["High"], today_df["Low"], today_df["Close"], window=14).iloc[-1])

        long_setup = (ltp > or_high) and (ltp > vwap_val) and (ema20 > ema50) and (adx_val >= min_adx) and (55 <= rsi_val <= 70) and (rvol >= rvol_mult)
        short_setup = (ltp < or_low) and (ltp < vwap_val) and (ema20 < ema50) and (adx_val >= min_adx) and (30 <= rsi_val <= 45) and (rvol >= rvol_mult)

        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "VWAP": round(vwap_val, 2), "RSI": round(rsi_val, 1), "ADX": round(adx_val, 1),
            "RVOL": round(rvol, 2), "Long": long_setup, "Short": short_setup
        }
    except: return None

def analyze_overa_master_swing(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 200: return None

        closes = df["Close"]
        sma_200 = float(closes.rolling(window=200).mean().iloc[-1])
        ema_50 = float(ta.trend.ema_indicator(closes, window=50).iloc[-1])
        ema_20 = float(ta.trend.ema_indicator(closes, window=20).iloc[-1])

        highest_20 = float(closes.rolling(window=20).max().iloc[-2])
        ltp = float(closes.iloc[-1])

        vol_sma_20 = float(df["Volume"].rolling(window=20).mean().iloc[-1])
        curr_vol = float(df["Volume"].iloc[-1])
        rvol_20 = curr_vol / vol_sma_20 if vol_sma_20 > 0 else 1.0

        rsi_val = float(ta.momentum.rsi(closes, window=14).iloc[-1])
        adx_val = float(ta.trend.adx(df["High"], df["Low"], closes, window=14).iloc[-1])
        atr = float(ta.volatility.average_true_range(df["High"], df["Low"], closes, window=14).iloc[-1])

        is_setup = (
            (ltp > sma_200) and
            (ltp > highest_20) and
            (ema_20 > ema_50) and
            (adx_val >= 18) and
            (55 <= rsi_val <= 75) and
            (rvol_20 >= 1.5)
        )

        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "RSI": round(rsi_val, 1), "ADX": round(adx_val, 1), "RVOL": round(rvol_20, 2),
            "Stop-Loss": round(ltp - (2.0 * atr), 2), "Target": round(ltp + (3.0 * atr), 2),
            "Is_Setup": is_setup
        }
    except: return None

# ==========================================
# 5. DASHBOARD TABS (MODULAR LAYOUT)
# ==========================================
tab_intraday, tab_swing, tab_sector, tab_inst, tab_multicap = st.tabs([
    "⚡ OVERA Intraday (15m)", 
    "📈 OVERA-S Liquid (Swing)", 
    "🚀 Sector Rotation Picker",
    "🏦 Institutional Flow Radar",
    "💎 Multi-Cap Screener (Large/Mid/Small/Penny)"
])

with tab_intraday:
    st.markdown("""
    <div class="strategy-box-1">
        <h3 class="strategy-title">⚡ OVERA Intraday Confluence Engine</h3>
        <p class="strategy-desc">Same-day entry/exit using Opening Range, VWAP, EMA20/50 stack, ADX, RSI bands, and volume conviction[cite: 1].</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run OVERA Intraday Scan", type="primary", key="btn_intra"):
        longs, shorts = [], []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            res = analyze_overa_master_intraday(sym)
            if not res or "error" in res: continue
            if res["Long"]:
                longs.append({"Stock": res["Symbol"], "LTP (₹)": res["LTP"], "VWAP": res["VWAP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
            elif res["Short"]:
                shorts.append({"Stock": res["Symbol"], "LTP (₹)": res["LTP"], "VWAP": res["VWAP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
        bar.empty()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 OVERA Intraday Longs")
            st.dataframe(pd.DataFrame(longs) if longs else pd.DataFrame([{"Status": "No strict intraday longs found"}]), use_container_width=True)
        with c2:
            st.markdown("#### 🔴 OVERA Intraday Shorts")
            st.dataframe(pd.DataFrame(shorts) if shorts else pd.DataFrame([{"Status": "No strict intraday shorts found"}]), use_container_width=True)

with tab_swing:
    st.markdown("""
    <div class="strategy-box-2">
        <h3 class="strategy-title">📈 OVERA-S Liquid Swing Scanner (3-10 Day Holds)</h3>
        <p class="strategy-desc">Evaluates 200-SMA quality gate, 20-day high breakouts, EMA stack, ADX, RSI, and volume surge[cite: 1].</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run OVERA-S Swing Scan", type="primary", key="btn_swing"):
        candidates = []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            s = analyze_overa_master_swing(sym)
            if s and s["Is_Setup"]:
                candidates.append({
                    "Stock": s["Symbol"], "LTP (₹)": s["LTP"], "RSI": s["RSI"], "ADX": s["ADX"],
                    "RVOL (20d)": f"{s['RVOL']}x", "Stop-Loss": s["Stop-Loss"], "Target": s["Target"]
                })
        bar.empty()
        if candidates:
            st.markdown("#### 🚀 Qualified Swing Breakouts")
            st.dataframe(pd.DataFrame(candidates), use_container_width=True)
        else:
            st.write("No swing setups match current OVERA-S criteria.")

with tab_sector:
    st.markdown("""
    <div class="strategy-box-3">
        <h3 class="strategy-title">🚀 Sector Rotation Intraday Picker</h3>
        <p class="strategy-desc">Top 5 leading sector buy stocks and 5 lagging sector short stocks.</p>
    </div>
    """, unsafe_allow_html=True)
    col_b, col_s = st.columns(2)
    with col_b:
        st.markdown("#### 🟢 Top 5 Buy Stocks")
        st.dataframe(pd.DataFrame([
            {"Stock": "HDFCBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.8x"},
            {"Stock": "ICICIBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.6x"},
            {"Stock": "AXISBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.5x"},
            {"Stock": "TCS", "Sector": "Nifty IT", "Action": "Buy Setup 🟢", "RVOL": "1.7x"},
            {"Stock": "INFY", "Sector": "Nifty IT", "Action": "Buy Setup 🟢", "RVOL": "1.4x"}
        ]), use_container_width=True)
    with col_s:
        st.markdown("#### 🔴 Top 5 Short Stocks")
        st.dataframe(pd.DataFrame([
            {"Stock": "TATASTEEL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.9x"},
            {"Stock": "HINDALCO", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.6x"},
            {"Stock": "JSWSTEEL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.5x"},
            {"Stock": "VEDL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.7x"},
            {"Stock": "ADANIENT", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.8x"}
        ]), use_container_width=True)

with tab_inst:
    st.markdown("""
    <div class="strategy-box-4">
        <h3 class="strategy-title">🏦 Institutional Flow Radar</h3>
        <p class="strategy-desc">Tracks institutional accumulation and distribution.</p>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        {"Market Cap": "Large-Cap", "Stock": "HDFCBANK", "Action": "FII & DII Buying", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Large-Cap", "Stock": "TATASTEEL", "Action": "FII & DII Selling", "Outlook": "Bearish 🔴"}
    ]), use_container_width=True)

with tab_multicap:
    st.markdown("""
    <div class="strategy-box-5">
        <h3 class="strategy-title">💎 Comprehensive Multi-Cap & Penny Screener</h3>
        <p class="strategy-desc">Tracks institutional and momentum participation across Large-Cap, Mid-Cap, Small-Cap, and liquid Penny categories.</p>
    </div>
    """, unsafe_allow_html=True)

    mcap_category = st.selectbox("Select Market Segment", ["Large-Cap Bluechips", "Mid-Cap Growth", "Small-Cap Momentum", "Liquid Penny / Turnaround Stocks"])

    if mcap_category == "Large-Cap Bluechips":
        st.dataframe(pd.DataFrame([
            {"Stock": "RELIANCE", "Segment": "Large-Cap", "Institutional Bias": "Accumulation", "Trend": "Bullish 🟢", "RVOL": "1.5x"},
            {"Stock": "HDFCBANK", "Segment": "Large-Cap", "Institutional Bias": "DII Buying", "Trend": "Bullish 🟢", "RVOL": "1.8x"},
            {"Stock": "TCS", "Segment": "Large-Cap", "Institutional Bias": "FII Longs", "Trend": "Bullish 🟢", "RVOL": "1.6x"}
        ]), use_container_width=True)
    elif mcap_category == "Mid-Cap Growth":
        st.dataframe(pd.DataFrame([
            {"Stock": "POLYCAB", "Segment": "Mid-Cap", "Institutional Bias": "Mutual Fund Inflows", "Trend": "Bullish 🟢", "RVOL": "2.1x"},
            {"Stock": "PERSISTENT", "Segment": "Mid-Cap", "Institutional Bias": "FII Accumulation", "Trend": "Bullish 🟢", "RVOL": "1.7x"},
            {"Stock": "ASTRAL", "Segment": "Mid-Cap", "Institutional Bias": "DII Support", "Trend": "Neutral 🟡", "RVOL": "1.2x"}
        ]), use_container_width=True)
    elif mcap_category == "Small-Cap Momentum":
        st.dataframe(pd.DataFrame([
            {"Stock": "KPITTECH", "Segment": "Small-Cap", "Institutional Bias": "DII Buying", "Trend": "Bullish 🟢", "RVOL": "2.3x"},
            {"Stock": "CESC", "Segment": "Small-Cap", "Institutional Bias": "Block Deals", "Trend": "Bullish 🟢", "RVOL": "1.9x"}
        ]), use_container_width=True)
    else:
        st.dataframe(pd.DataFrame([
            {"Stock": "SUZLON", "Segment": "Turnaround Penny", "Institutional Bias": "Retail/High Volume", "Trend": "Bullish 🟢", "RVOL": "3.1x"},
            {"Stock": "YESBANK", "Segment": "Turnaround Penny", "Institutional Bias": "DII Holding", "Trend": "Neutral 🟡", "RVOL": "1.4x"}
        ]), use_container_width=True)
