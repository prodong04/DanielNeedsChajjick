import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.graph_objects as go
import streamlit.components.v1 as components

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Daniel Study Tracker", layout="wide")

# CSS 스타일 설정 (기존 스타일 유지 및 로딩 바 숨김 처리)
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffffff; }
    .stApp { background-color: #000000; }
    h1, h2, h3, p, span { color: #ffffff !important; text-align: center; }
    
    /* 채찍질 섹션 전용 스타일 */
    .chajjick-header {
        color: #ff4b4b !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 50px;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
    }
    
    .comment-box {
        background-color: #0a0a0a; 
        padding: 20px; 
        border-radius: 10px;
        border: 1px solid #333333;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 15px; 
        text-align: left;
        transition: 0.3s;
    }
    .comment-box:hover {
        border-color: #ff4b4b;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.2);
    }
    
    [data-testid="stMetricLabel"] { color: #bbbbbb !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.8rem !important; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; } 
    
    input, textarea { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }

    /* 로딩 로그/스피너 숨기기 혹은 스타일링 */
    div[data-testid="stStatusWidget"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- [STEP 1] 시각적 요소 먼저 렌더링 (로딩 화면 역할) ---

# 3D 헤더 HTML 정의
header_html = """
<div id="dashboard-container" style="width: 100%; background: transparent; color: white; padding: 10px; font-family: sans-serif;">
    <h1 style="text-align: center; color: #ffffff; font-size: 4.5rem; font-weight: 800; margin-bottom: 10px; letter-spacing: -2px;">
        DanielNeeds<span style="color: #ff4b4b;">Chajjick</span>
    </h1>
    <p style="text-align: center; font-size: 1.4rem; color: #94a3b8; margin-bottom: 0px;">
        Currently Studying: <span style="color: #38bdf8; font-weight: bold;">Stochastic Calculus for Finance II</span> by Steven Shreve
    </p>
    
    <div id="canvas-container" style="width: 100%; height: 450px; display: flex; justify-content: center;">
        <script type="module">
            import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 450, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            renderer.setSize(window.innerWidth > 1000 ? 1000 : window.innerWidth, 450);
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            const geometry = new THREE.TorusKnotGeometry(2.2, 0.7, 200, 32);
            const material = new THREE.MeshNormalMaterial({ wireframe: false });
            const torusKnot = new THREE.Mesh(geometry, material);
            scene.add(torusKnot);
            camera.position.z = 6;

            function animate() {
                requestAnimationFrame(animate);
                torusKnot.rotation.x += 0.01;
                torusKnot.rotation.y += 0.015;
                renderer.render(scene, camera);
            }
            animate();
        </script>
    </div>
</div>
"""

# 상단 제목과 3D 조형물을 즉시 표시
st.title("")
components.html(header_html, height=600)

# --- [STEP 2] 데이터 로딩 (백그라운드 처리 느낌으로) ---

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 로딩 중임을 알리는 얇은 스피너 (선택 사항, 텍스트 없이 깔끔하게)
with st.spinner(""):
    def get_all_data():
        try:
            s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Study", ttl=0).dropna(how='all')
            c_df = conn.read(spreadsheet=SHEET_URL, worksheet="Comments", ttl=0).dropna(how='all')
            return s_df, c_df
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return pd.DataFrame(columns=['Date', 'Pages']), pd.DataFrame(columns=['Date', 'Nickname', 'Content'])

    study_df, comment_df = get_all_data()

    # 데이터 가공
    study_df['Pages'] = pd.to_numeric(study_df['Pages'], errors='coerce').fillna(0).astype(float)
    if not study_df.empty:
        study_df['Date'] = pd.to_datetime(study_df['Date']).dt.date
        study_df = study_df.sort_values('Date')
        study_df['Cumulative'] = study_df['Pages'].cumsum().astype(float)

# --- [STEP 3] 나머지 지표 및 그래프 렌더링 ---

# 진행 지표
TOTAL_PAGES = 526.0
done_pages = float(study_df['Pages'].sum()) if not study_df.empty else 0.0
progress = min(done_pages / TOTAL_PAGES, 1.0)

m1, m2, m3 = st.columns(3)
m1.metric("총 공부량 ", f"{done_pages:.1f} / {TOTAL_PAGES:.1f} p")
m2.metric("진행도 ", f"{progress*100:.1f} %")
m3.metric("남은 페이지 ", f"{max(TOTAL_PAGES - done_pages, 0.0):.1f} p")
st.progress(progress)

# 그래프 섹션
st.write("")
if not study_df.empty:
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Daily Progress")
        fig1 = go.Figure(go.Bar(x=study_df['Date'], y=study_df['Pages'], marker_color='#ffffff'))
        fig1.update_layout(paper_bgcolor='black', plot_bgcolor='black', font_color='white', height=400,
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        st.subheader("📈 Total Progress")
        fig2 = go.Figure(go.Scatter(x=study_df['Date'], y=study_df['Cumulative'], fill='tozeroy', line_color='#ffffff'))
        fig2.update_layout(paper_bgcolor='black', plot_bgcolor='black', font_color='white', height=400,
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<h2 class='chajjick-header'>🚨 CHAJJICK ZONE (채찍질 공간)</h2>", unsafe_allow_html=True)

c_log, c_whip = st.columns([1, 1])

with c_log:
    st.write("### 📅 Study Log")
    if not study_df.empty:
        display_df = study_df.sort_values('Date', ascending=False)[['Date', 'Pages', 'Cumulative']].copy()
        st.table(display_df)

with c_whip:
    st.write("### 🧨 Deliver a Whip")
    with st.form("guest_form", clear_on_submit=True):
        col_n, col_m = st.columns([1, 2])
        n_nick = col_n.text_input("채찍 주인 ", placeholder="이름")
        n_msg = col_m.text_input("채찍질 내용 ", placeholder=".")
        if st.form_submit_button("💥 채찍 휘두르기 "):
            if n_nick and n_msg:
                new_data = pd.DataFrame({
                    "Date": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "Nickname": [n_nick], "Content": [n_msg]
                })
                updated_c = pd.concat([comment_df[['Date', 'Nickname', 'Content']], new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Comments", data=updated_c)
                st.rerun()

    if not comment_df.empty:
        st.write("### ⚡ Recent Whips")
        container = st.container(height=300)
        with container:
            for _, row in comment_df.iloc[::-1].iterrows():
                st.markdown(f"""
                <div class="comment-box">
                    <b style="color:#ff4b4b;">{row.get('Nickname', '익명')}</b> 
                    <small style="color:#888888; float:right;">{row.get('Date', '')}</small><br>
                    <p style="margin-top:10px; color:#ffffff; font-size:1.1rem;">{row.get('Content', '')}</p>
                </div>
                """, unsafe_allow_html=True)