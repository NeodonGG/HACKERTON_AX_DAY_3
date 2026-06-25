import io
import requests
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── 페이지 기본 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="매출 대시보드",
    page_icon="📊",
    layout="wide",
)

# ── 커스텀 CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #F4F6FB; }

.dashboard-header {
    background: linear-gradient(135deg, #4F8EF7 0%, #7C3AED 100%);
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
    box-shadow: 0 2px 12px rgba(79,142,247,0.10);
    border-left: 5px solid #4F8EF7;
    margin-bottom: 8px;
}
.kpi-label { font-size: 0.82rem; color: #7B8A9A; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.kpi-value { font-size: 2rem; font-weight: 800; color: #1E2A3A; line-height: 1; }
.kpi-sub   { font-size: 0.82rem; color: #4F8EF7; margin-top: 6px; font-weight: 500; }

.section-card {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(79,142,247,0.08);
    margin-bottom: 20px;
}
.section-title { font-size: 1.05rem; font-weight: 700; color: #1E2A3A; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

.filter-area {
    background: white;
    border-radius: 14px;
    padding: 18px 24px;
    box-shadow: 0 2px 12px rgba(79,142,247,0.08);
    margin-bottom: 20px;
}

.upload-area {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(79,142,247,0.08);
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
    <h1>📊 매출 대시보드</h1>
    <p>주문데이터 + 상품마스터를 업로드하면 자동으로 병합하여 분석합니다</p>
</div>
""", unsafe_allow_html=True)

# ── 서울 날씨 (Open-Meteo) ───────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_seoul_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=37.5665&longitude=126.9780"
        "&current=temperature_2m,weathercode"
        "&hourly=temperature_2m"
        "&timezone=Asia%2FSeoul"
        "&forecast_days=1"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def weathercode_to_label(code):
    if code == 0:            return "맑음 ☀️"
    elif code <= 3:          return "구름 많음 ⛅"
    elif code <= 49:         return "안개 🌫️"
    elif code <= 69:         return "비 🌧️"
    elif code <= 79:         return "눈 🌨️"
    elif code <= 82:         return "소나기 🌦️"
    elif code <= 99:         return "뇌우 ⛈️"
    return "알 수 없음"

try:
    weather_data = fetch_seoul_weather()
    current_temp = weather_data["current"]["temperature_2m"]
    current_code = weather_data["current"]["weathercode"]
    hourly_times = weather_data["hourly"]["time"]          # ["2025-06-25T00:00", ...]
    hourly_temps = weather_data["hourly"]["temperature_2m"]

    now_hour = datetime.now().hour
    hourly_df = pd.DataFrame({
        "시각": [t[11:16] for t in hourly_times],          # "00:00" 형식
        "기온(°C)": hourly_temps,
        "hour": range(len(hourly_times)),
    })

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌡️ 서울 현재 날씨 (Open-Meteo)</div>', unsafe_allow_html=True)

    w1, w2, w_chart = st.columns([1, 1, 4], gap="medium")
    with w1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#F97316;">
            <div class="kpi-label">🌡️ 현재 기온</div>
            <div class="kpi-value">{current_temp:.1f} °C</div>
            <div class="kpi-sub">{weathercode_to_label(current_code)}</div>
        </div>""", unsafe_allow_html=True)
    with w2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#0EA5E9;">
            <div class="kpi-label">📍 위치</div>
            <div class="kpi-value" style="font-size:1.3rem;">서울특별시</div>
            <div class="kpi-sub">37.57°N 126.98°E</div>
        </div>""", unsafe_allow_html=True)
    with w_chart:
        fig_weather = go.Figure()
        fig_weather.add_trace(go.Scatter(
            x=hourly_df["시각"],
            y=hourly_df["기온(°C)"],
            mode="lines+markers",
            line=dict(color="#F97316", width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(249,115,22,0.10)",
            name="기온",
        ))
        fig_weather.add_vline(
            x=f"{now_hour:02d}:00",
            line_width=2, line_dash="dash", line_color="#7C3AED",
            annotation_text="현재", annotation_position="top",
        )
        fig_weather.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(title="", showgrid=False, tickangle=-45),
            yaxis=dict(title="°C", showgrid=True, gridcolor="#F0F0F0"),
            margin=dict(t=10, b=10, l=0, r=0),
            height=200,
            showlegend=False,
        )
        st.plotly_chart(fig_weather, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.warning(f"날씨 정보를 불러올 수 없습니다: {e}")

# ── 파일 업로드 ──────────────────────────────────────────────────
st.markdown('<div class="upload-area">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📂 엑셀 파일 업로드</div>', unsafe_allow_html=True)
col_up1, col_up2 = st.columns(2)
with col_up1:
    order_file = st.file_uploader(
        "🛒 주문데이터.xlsx",
        type=["xlsx", "xls"],
        help="주문ID, 상품ID, 고객ID, 주문날짜, 주문수량(EA), 결제금액(원), 지역, 배송상태 컬럼이 필요합니다",
    )
with col_up2:
    product_file = st.file_uploader(
        "📦 상품마스터.xlsx",
        type=["xlsx", "xls"],
        help="상품ID, 상품명, 카테고리, 브랜드, 단가(원), 공급사, 재고수량(EA) 컬럼이 필요합니다",
    )
st.markdown('</div>', unsafe_allow_html=True)

if not order_file or not product_file:
    st.info("주문데이터와 상품마스터 두 파일을 모두 업로드하면 대시보드가 표시됩니다.")
    st.stop()

# ── 데이터 로드 & 병합 ──────────────────────────────────────────
@st.cache_data
def load_and_merge(order_bytes, product_bytes):
    orders   = pd.read_excel(io.BytesIO(order_bytes))
    products = pd.read_excel(io.BytesIO(product_bytes))
    merged   = orders.merge(products, on="상품ID", how="left")
    merged["주문일자"] = pd.to_datetime(merged["주문일자"], errors="coerce")
    merged["월"] = merged["주문일자"].dt.to_period("M").astype(str)
    return merged

try:
    df = load_and_merge(order_file.read(), product_file.read())
except Exception as e:
    st.error(f"파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

required_order   = {"상품ID", "결제금액(원)", "주문수량(EA)", "배송지역", "배송상태", "주문일자"}
required_product = {"상품ID", "상품명", "카테고리", "브랜드"}
missing = (required_order | required_product) - set(df.columns)
if missing:
    st.error(f"필수 컬럼이 없습니다: {missing}")
    st.stop()

# ── 병합 성공 알림 ───────────────────────────────────────────────
st.success(f"병합 완료 — 총 {len(df):,}건의 주문 데이터 ({df['상품명'].nunique()}개 상품)")

# ── 필터 ─────────────────────────────────────────────────────────
st.markdown('<div class="filter-area">', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)

with f1:
    all_categories = sorted(df["카테고리"].dropna().unique().tolist())
    sel_cat = st.multiselect("🗂️ 카테고리", all_categories, default=all_categories)

with f2:
    all_regions = sorted(df["배송지역"].dropna().unique().tolist())
    sel_region = st.multiselect("📍 지역", all_regions, default=all_regions)

with f3:
    all_status = sorted(df["배송상태"].dropna().unique().tolist())
    sel_status = st.multiselect("🚚 배송상태", all_status, default=all_status)

st.markdown('</div>', unsafe_allow_html=True)

fdf = df[
    df["카테고리"].isin(sel_cat) &
    df["배송지역"].isin(sel_region) &
    df["배송상태"].isin(sel_status)
]

if fdf.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# ── KPI 카드 ─────────────────────────────────────────────────────
total_sales  = fdf["결제금액(원)"].sum()
total_orders = len(fdf)
avg_order    = fdf["결제금액(원)"].mean()
total_qty    = fdf["주문수량(EA)"].sum()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💰 전체 결제금액</div>
        <div class="kpi-value">₩ {total_sales:,.0f}</div>
        <div class="kpi-sub">필터 기준 합산</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#7C3AED;">
        <div class="kpi-label">🧾 총 주문 건수</div>
        <div class="kpi-value">{total_orders:,} 건</div>
        <div class="kpi-sub">전체 기간 합산</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#10B981;">
        <div class="kpi-label">📈 건당 평균 결제금액</div>
        <div class="kpi-value">₩ {avg_order:,.0f}</div>
        <div class="kpi-sub">평균 주문 단가</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#F59E0B;">
        <div class="kpi-label">📦 총 주문 수량</div>
        <div class="kpi-value">{total_qty:,} EA</div>
        <div class="kpi-sub">수량 합산</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# ── 차트 행 1 ────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="medium")

COLORS = px.colors.qualitative.Pastel

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗂️ 카테고리별 매출</div>', unsafe_allow_html=True)

    cat_sales = (
        fdf.groupby("카테고리", as_index=False)["결제금액(원)"]
        .sum()
        .sort_values("결제금액(원)", ascending=False)
    )
    fig_cat = px.bar(
        cat_sales, x="카테고리", y="결제금액(원)",
        color="카테고리", color_discrete_sequence=COLORS,
        text=cat_sales["결제금액(원)"].map(lambda v: f"₩{v/1e6:.1f}M"),
    )
    fig_cat.update_traces(textposition="outside", marker_line_width=0)
    fig_cat.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", title=""),
        xaxis=dict(title=""),
        margin=dict(t=20, b=0, l=0, r=0),
        height=320,
    )
    st.plotly_chart(fig_cat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📍 지역별 매출 비중</div>', unsafe_allow_html=True)

    region_sales = (
        fdf.groupby("배송지역", as_index=False)["결제금액(원)"].sum()
    )
    fig_pie = px.pie(
        region_sales, names="배송지역", values="결제금액(원)",
        color_discrete_sequence=COLORS,
        hole=0.4,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=10, b=30, l=0, r=0),
        height=320,
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 차트 행 2 ────────────────────────────────────────────────────
col_left2, col_right2 = st.columns([1, 1], gap="medium")

with col_left2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📅 월별 매출 추이</div>', unsafe_allow_html=True)

    monthly = (
        fdf.groupby("월", as_index=False)["결제금액(원)"].sum()
        .sort_values("월")
    )
    fig_line = px.line(
        monthly, x="월", y="결제금액(원)",
        markers=True,
        color_discrete_sequence=["#4F8EF7"],
    )
    fig_line.update_traces(line_width=2.5, marker_size=8)
    fig_line.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", title=""),
        xaxis=dict(title=""),
        margin=dict(t=10, b=0, l=0, r=0),
        height=320,
    )
    st.plotly_chart(fig_line, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏷️ 브랜드별 매출 TOP 10</div>', unsafe_allow_html=True)

    brand_sales = (
        fdf.groupby("브랜드", as_index=False)["결제금액(원)"].sum()
        .sort_values("결제금액(원)", ascending=True)
        .tail(10)
    )
    fig_brand = px.bar(
        brand_sales, x="결제금액(원)", y="브랜드",
        orientation="h",
        color="결제금액(원)",
        color_continuous_scale=["#C7D9F9", "#4F8EF7"],
        text=brand_sales["결제금액(원)"].map(lambda v: f"₩{v/1e6:.1f}M"),
    )
    fig_brand.update_traces(textposition="outside", marker_line_width=0)
    fig_brand.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", title=""),
        yaxis=dict(title=""),
        margin=dict(t=10, b=0, l=0, r=40),
        height=320,
    )
    st.plotly_chart(fig_brand, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 배송상태 현황 ─────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🚚 배송상태 × 카테고리 현황</div>', unsafe_allow_html=True)

status_cat = (
    fdf.groupby(["배송상태", "카테고리"], as_index=False)["결제금액(원)"].sum()
)
fig_status = px.bar(
    status_cat, x="배송상태", y="결제금액(원)",
    color="카테고리",
    color_discrete_sequence=COLORS,
    barmode="stack",
    text_auto=False,
)
fig_status.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    yaxis=dict(showgrid=True, gridcolor="#F0F0F0", title="결제금액 (원)"),
    xaxis=dict(title=""),
    legend=dict(title="카테고리", orientation="h", y=1.08),
    margin=dict(t=30, b=0, l=0, r=0),
    height=320,
)
st.plotly_chart(fig_status, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 상품별 매출 테이블 ───────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🛍️ 상품별 매출 현황 (병합 데이터)</div>', unsafe_allow_html=True)

product_sales = (
    fdf.groupby(["상품명", "카테고리", "브랜드", "공급사"], as_index=False)
    .agg(결제금액합계=("결제금액(원)", "sum"), 주문건수=("주문수량(EA)", "count"), 총수량=("주문수량(EA)", "sum"))
    .sort_values("결제금액합계", ascending=False)
    .reset_index(drop=True)
)
product_sales.index += 1
product_sales["매출비중"] = (product_sales["결제금액합계"] / product_sales["결제금액합계"].sum() * 100).map("{:.1f}%".format)
product_sales["결제금액합계_표시"] = product_sales["결제금액합계"].map("₩ {:,.0f}".format)

st.dataframe(
    product_sales[["상품명", "카테고리", "브랜드", "공급사", "결제금액합계_표시", "주문건수", "총수량", "매출비중"]],
    use_container_width=True,
    column_config={
        "상품명":         st.column_config.TextColumn("상품명"),
        "카테고리":        st.column_config.TextColumn("카테고리"),
        "브랜드":         st.column_config.TextColumn("브랜드"),
        "공급사":         st.column_config.TextColumn("공급사"),
        "결제금액합계_표시": st.column_config.TextColumn("결제금액 합계"),
        "주문건수":        st.column_config.NumberColumn("주문 건수", format="%d 건"),
        "총수량":         st.column_config.NumberColumn("총 수량", format="%d EA"),
        "매출비중":        st.column_config.TextColumn("매출 비중"),
    },
)
st.markdown('</div>', unsafe_allow_html=True)

# ── 병합 원본 데이터 미리보기 ────────────────────────────────────
with st.expander("🔍 병합 원본 데이터 미리보기"):
    st.dataframe(fdf, use_container_width=True, height=300)
