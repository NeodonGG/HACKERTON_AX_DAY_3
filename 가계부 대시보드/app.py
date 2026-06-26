import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ── 페이지 기본 설정 ─────────────────────────────────────────────
st.set_page_config(page_title="가계부 대시보드", page_icon="💰", layout="wide")

# ── 커스텀 CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #F4F6FB; }

.dashboard-header {
    background: linear-gradient(135deg, #16A34A 0%, #0EA5E9 100%);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 28px;
    color: white;
}
.dashboard-header h1 { font-size: 2.4rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; }
.dashboard-header p  { font-size: 1rem; opacity: 0.85; margin: 0; }

.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(22,163,74,0.10);
    border-left: 5px solid #16A34A;
    margin-bottom: 8px;
}
.kpi-label { font-size: 0.82rem; color: #7B8A9A; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.kpi-value { font-size: 2rem; font-weight: 800; color: #1E2A3A; line-height: 1; }
.kpi-sub   { font-size: 0.82rem; color: #16A34A; margin-top: 6px; font-weight: 500; }

.section-card {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(22,163,74,0.08);
    margin-bottom: 20px;
}
.section-title { font-size: 1.05rem; font-weight: 700; color: #1E2A3A; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

.filter-area {
    background: white;
    border-radius: 14px;
    padding: 18px 24px;
    box-shadow: 0 2px 12px rgba(22,163,74,0.08);
    margin-bottom: 20px;
}

.upload-area {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(22,163,74,0.08);
    margin-bottom: 20px;
}

.stDataFrame { border-radius: 10px; overflow: hidden; }
section[data-testid="stSidebar"] { display: none; }
hr { display: none; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 배너 ────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>💰 나만의 가계부 대시보드</h1>
    <p>수입·지출 내역을 한눈에 확인하고, 카드/현금 내역을 합쳐 분석해요</p>
</div>
""", unsafe_allow_html=True)

# ── 기본 데이터 로드 ─────────────────────────────────────────────
@st.cache_data
def load_default():
    df = pd.read_csv("data/가계부.csv")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df

base_df = load_default()

# ── 도전과제: 형식이 다른 엑셀 2개 병합 ──────────────────────────
st.markdown('<div class="upload-area">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📂 카드·현금 내역 추가로 합치기 (선택)</div>', unsafe_allow_html=True)
st.caption("컬럼 형식이 서로 다른 엑셀 2개(카드 사용내역 / 현금 가계부)를 업로드하면 기본 데이터에 자동으로 병합돼요.")
col_up1, col_up2 = st.columns(2)
with col_up1:
    card_file = st.file_uploader(
        "💳 카드_사용내역.xlsx",
        type=["xlsx", "xls"],
        help="결제일, 가맹점명, 카테고리, 결제금액 컬럼 형식",
    )
with col_up2:
    cash_file = st.file_uploader(
        "💵 현금가계부.xlsx",
        type=["xlsx", "xls"],
        help="date, item, type, amount, memo 컬럼 형식",
    )
st.markdown('</div>', unsafe_allow_html=True)

def normalize_card(raw: bytes) -> pd.DataFrame:
    d = pd.read_excel(io.BytesIO(raw))
    return pd.DataFrame({
        "날짜": pd.to_datetime(d["결제일"]),
        "분류": d["카테고리"],
        "항목": d["가맹점명"],
        "구분": "지출",
        "금액": d["결제금액"],
        "결제수단": "신용카드",
    })

def normalize_cash(raw: bytes) -> pd.DataFrame:
    d = pd.read_excel(io.BytesIO(raw))
    return pd.DataFrame({
        "날짜": pd.to_datetime(d["date"], format="%Y/%m/%d"),
        "분류": d["memo"],
        "항목": d["item"],
        "구분": d["type"],
        "금액": d["amount"],
        "결제수단": "현금",
    })

df = base_df.copy()
added_msgs = []
if card_file is not None:
    try:
        df = pd.concat([df, normalize_card(card_file.read())], ignore_index=True)
        added_msgs.append("카드 사용내역")
    except Exception as e:
        st.error(f"카드 내역을 불러오는 중 오류: {e}")
if cash_file is not None:
    try:
        df = pd.concat([df, normalize_cash(cash_file.read())], ignore_index=True)
        added_msgs.append("현금 가계부")
    except Exception as e:
        st.error(f"현금 가계부를 불러오는 중 오류: {e}")

if added_msgs:
    st.success(f"병합 완료 — {', '.join(added_msgs)} 데이터가 합쳐졌어요. 총 {len(df):,}건")

df["월"] = df["날짜"].dt.to_period("M").astype(str)

# ── 필터 ─────────────────────────────────────────────────────────
st.markdown('<div class="filter-area">', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)

with f1:
    months = sorted(df["월"].unique().tolist())
    sel_months = st.multiselect("📅 월", months, default=months)
with f2:
    cats = sorted(df["분류"].unique().tolist())
    sel_cats = st.multiselect("🗂️ 분류", cats, default=cats)
with f3:
    sel_types = st.multiselect("↕️ 구분", ["수입", "지출"], default=["수입", "지출"])

st.markdown('</div>', unsafe_allow_html=True)

fdf = df[df["월"].isin(sel_months) & df["분류"].isin(sel_cats) & df["구분"].isin(sel_types)]

if fdf.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# ── KPI 카드 ─────────────────────────────────────────────────────
total_income  = fdf.loc[fdf["구분"] == "수입", "금액"].sum()
total_expense = fdf.loc[fdf["구분"] == "지출", "금액"].sum()
net_balance   = total_income - total_expense
this_month    = df["월"].max()
this_month_expense = df.loc[(df["월"] == this_month) & (df["구분"] == "지출"), "금액"].sum()

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#16A34A;">
        <div class="kpi-label">💵 총 수입</div>
        <div class="kpi-value">{total_income:,.0f}원</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#EF4444;">
        <div class="kpi-label">💸 총 지출</div>
        <div class="kpi-value">{total_expense:,.0f}원</div>
    </div>""", unsafe_allow_html=True)
with k3:
    color = "#16A34A" if net_balance >= 0 else "#EF4444"
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:{color};">
        <div class="kpi-label">🧾 순잔액</div>
        <div class="kpi-value" style="color:{color};">{net_balance:,.0f}원</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#0EA5E9;">
        <div class="kpi-label">📆 이번 달({this_month}) 지출</div>
        <div class="kpi-value">{this_month_expense:,.0f}원</div>
    </div>""", unsafe_allow_html=True)

# ── 월별 수입/지출 추이 ──────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 월별 수입·지출 추이</div>', unsafe_allow_html=True)

monthly = fdf.groupby(["월", "구분"])["금액"].sum().reset_index()
fig_trend = px.bar(
    monthly, x="월", y="금액", color="구분", barmode="group",
    color_discrete_map={"수입": "#16A34A", "지출": "#EF4444"},
)
fig_trend.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=20, b=10, l=0, r=0))
st.plotly_chart(fig_trend, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 카테고리별 지출 & 결제수단별 지출 ────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🥧 카테고리별 지출 비중</div>', unsafe_allow_html=True)
    cat_expense = fdf[fdf["구분"] == "지출"].groupby("분류")["금액"].sum().reset_index().sort_values("금액", ascending=False)
    fig_pie = px.pie(cat_expense, names="분류", values="금액", hole=0.45)
    fig_pie.update_layout(margin=dict(t=20, b=10, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💳 결제수단별 지출</div>', unsafe_allow_html=True)
    pay_expense = fdf[fdf["구분"] == "지출"].groupby("결제수단")["금액"].sum().reset_index().sort_values("금액", ascending=False)
    fig_bar = px.bar(pay_expense, x="결제수단", y="금액", color="결제수단")
    fig_bar.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False, margin=dict(t=20, b=10, l=0, r=0))
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 도전과제: 환율 API (Frankfurter, 키 불필요) ──────────────────
@st.cache_data(ttl=3600)
def fetch_usd_krw_rate():
    r = requests.get("https://api.frankfurter.app/latest?from=USD&to=KRW", timeout=10)
    r.raise_for_status()
    return r.json()

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🌍 오늘의 환율 (해외 지출 참고용)</div>', unsafe_allow_html=True)
try:
    rate_data = fetch_usd_krw_rate()
    usd_krw = rate_data["rates"]["KRW"]
    rate_date = rate_data["date"]

    rc1, rc2 = st.columns([1, 2])
    with rc1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#7C3AED;">
            <div class="kpi-label">💱 1 USD</div>
            <div class="kpi-value">{usd_krw:,.2f}원</div>
            <div class="kpi-sub">기준일: {rate_date}</div>
        </div>""", unsafe_allow_html=True)
    with rc2:
        usd_amount = st.number_input("해외 결제 금액(USD)을 원화로 환산해보기", min_value=0.0, value=100.0, step=10.0)
        st.metric("환산 금액", f"{usd_amount * usd_krw:,.0f}원")
except Exception as e:
    st.warning(f"환율 정보를 불러올 수 없습니다: {e}")
st.markdown('</div>', unsafe_allow_html=True)

# ── 상세 내역 테이블 ─────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📋 상세 내역</div>', unsafe_allow_html=True)
st.dataframe(
    fdf.sort_values("날짜", ascending=False)[["날짜", "분류", "항목", "구분", "금액", "결제수단"]],
    use_container_width=True,
    hide_index=True,
)
st.markdown('</div>', unsafe_allow_html=True)
