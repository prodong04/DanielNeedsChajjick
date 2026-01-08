import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="dongryeolneedschajjick", layout="wide")

# --- CSS 스타일 수정 (가독성 향상 및 색상 변경) ---
st.markdown("""
    <style>
    /* 전체 배경 및 기본 텍스트 색상 */
    .main { background-color: #000000; color: #ffffff; }
    .stApp { background-color: #000000; }
    
    /* 제목 색상 변경 (민트 -> 화이트) */
    h1, h2, h3 { color: #ffffff !important; text-align: center; }
    
    /* Metric (통계 수치) 가독성 향상 */
    [data-testid="stMetricLabel"] { color: #bbbbbb !important; } /* 레이블은 약간 회색으로 구분 */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2rem !important; } /* 값은 밝고 크게 */
    
    /* Progress Bar 색상 변경 (화이트) */
    .stProgress > div > div > div > div { background-color: #ffffff; }
    
    /* 댓글 박스 디자인 변경 */
    .comment-box {
        background-color: #111111; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ffffff; /* 테두리 화이트 */
        margin-bottom: 10px;
    }
    .comment-nickname { color: #ffffff; font-weight: bold; } /* 닉네임 화이트 */
    .comment-date { color: #888888; font-size: 0.8em; }
    
    /* 입력 폼 글자색 */
    .stTextInput > div > div > input { color: #ffffff; }
    .stTextArea > div > div > textarea { color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결 설정
# 본인의 구글 시트 공유 링크(편집 권한 포함)를 아래에 붙여넣으세요!
url = "https://docs.google.com/spreadsheets/d/1EqPYrlRnb5pOk4H_ekTAc5tBSnJWEvUfQgugaY1T3Lw/edit?usp=sharing"
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"구글 시트 연결 오류: {e}. URL과 권한을 확인해주세요.")
    st.stop()

# 데이터 불러오기 함수
def get_data():
    try:
        study_df = conn.read(spreadsheet=url, worksheet="Study")
        comment_df = conn.read(spreadsheet=url, worksheet="Comments")
        return study_df.dropna(how='all'), comment_df.dropna(how='all')
    except Exception:
        # 시트가 비어있거나 없을 경우 빈 DataFrame 반환
        return pd.DataFrame(columns=['Date', 'Pages']), pd.DataFrame(columns=['Date', 'Nickname', 'Password', 'Content'])

study_df, comment_df = get_data()

# --- UI 레이아웃 ---
st.title("dongryeolneedschajjick")

# 회전하는 지구 (Three.js)
earth_html = """
<div id="container" style="width: 100%; height: 350px; background: black; display: flex; justify-content: center;">
    <script type="module">
        import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 350, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize(window.innerWidth, 350);
        document.getElementById('container').appendChild(renderer.domElement);
        const geometry = new THREE.SphereGeometry(2, 32, 32);
        const texture = new THREE.TextureLoader().load('https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg');
        const material = new THREE.MeshPhongMaterial({ map: texture, shininess: 5 });
        const earth = new THREE.Mesh(geometry, material);
        scene.add(earth);
        const light = new THREE.DirectionalLight(0xffffff, 1);
        light.position.set(5, 3, 5).normalize();
        scene.add(light);
        camera.position.z = 5;
        function animate() { requestAnimationFrame(animate); earth.rotation.y += 0.005; renderer.render(scene, camera); }
        animate();
    </script>
</div>
"""
components.html(earth_html, height=350)

# 통계 계산
total_pages = 560
total_done = pd.to_numeric(study_df['Pages'], errors='coerce').sum() if not study_df.empty else 0
progress_pct = min(total_done / total_pages, 1.0)

# 통계 표시 (간격 조정)
c1, c2, c3 = st.columns(3, gap="large")
c1.metric("총 공부량", f"{int(total_done)} / {total_pages} p")
c2.metric("진행도", f"{progress_pct*100:.1f} %")
c3.metric("남은 페이지", f"{max(total_pages - int(total_done), 0)} p")

st.progress(progress_pct)

# 3. 관리자 패널 (비밀번호: 1234)
st.sidebar.title("🔐 Admin")
admin_pw = st.sidebar.text_input("관리자 비번", type="password")

if admin_pw == "000401":
    st.sidebar.success("관리자 모드 접속")
    with st.sidebar.form("study_form"):
        d = st.date_input("날짜", datetime.date.today())
        p = st.number_input("페이지", min_value=0)
        if st.form_submit_button("기록 하기"):
            new_row = pd.DataFrame({"Date": [str(d)], "Pages": [p]})
            updated_study = pd.concat([study_df, new_row], ignore_index=True)
            conn.update(spreadsheet=url, worksheet="Study", data=updated_study)
            st.toast("시트에 기록 되었습니다!", icon="✅")
            st.rerun()

# 4. 댓글 섹션
st.markdown("---")
st.subheader("💬 chajjick")

with st.form("comment_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    nick = c1.text_input("닉네임")
    pw = c2.text_input("비밀번호", type="password", placeholder="제 맘대로 수정과 삭제가 가능합니다...")
    msg = st.text_area("내용", placeholder="dongryeolneedschajjick")
    if st.form_submit_button("댓글 달기"):
        if nick and msg:
            new_comm = pd.DataFrame({
                "Date": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Nickname": [nick], "Password": [pw], "Content": [msg]
            })
            updated_comm = pd.concat([comment_df, new_comm], ignore_index=True)
            conn.update(spreadsheet=url, worksheet="Comments", data=updated_comm)
            st.toast("댓글이 등록 되었습니다", icon="🎉")
            st.rerun()
        else:
            st.warning("닉네임과 내용을 입력해주세요.")

# 댓글 출력 (최신순)
if not comment_df.empty:
    for idx, row in comment_df.iloc[::-1].iterrows():
        st.markdown(f"""
        <div class="comment-box">
            <span class="comment-nickname">{row['Nickname']}</span> <span class="comment-date">({row['Date']})</span><br>
            <p style="margin-top:10px;">{row['Content']}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("첫 번째 댓글의 주인공이 되어보세요!")