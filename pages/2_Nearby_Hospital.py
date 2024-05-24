import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import re
from streamlit_cookies_manager import EncryptedCookieManager
from datetime import datetime

st.set_page_config(
    page_title="AI 헬시톡",
    page_icon="💬",
    layout="wide"
)

st.markdown(
    """
    <style>
    ."block-container.st-emotion-cache-1jicfl2.ea3mdgi5" {
        padding-top: 10px !important;
        padding-down: 50px;
        padding-right: 80px !important;
        padding-left: 80px !important;
    }
    .st-emotion-cache-1jicfl2 {
        padding-top: 10px !important;
        padding-down: 50px;
        padding-right: 80px !important;
        padding-left: 80px !important;
    }
    .ea3mdgi5 {
        padding-top: 10px !important;
        padding-down: 50px;
        padding-right: 80px !important;
        padding-left: 80px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

print(st.session_state)

def find_department(msg):
    loc = re.findall(r"\.\s*([^\.]+)의 전문의에게", msg)[0]
    return loc.split(',')[0]

# 쿠키 관리자 초기화
cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()

if "messages" not in st.session_state:
    loc = ''
else:
    text = st.session_state.messages[-1]['content']
    if "추천합니다" in text:
        loc = find_department(text)
    else:
        loc = ''
print("this is loc:", loc)

# 데이터베이스 연결
def get_db_connection():
    conn = sqlite3.connect('data/user_database.db')
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과를 반환하기 위해 추가
    return conn

def initialize_db():
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE hospitals ADD COLUMN username TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            st.error(f"데이터베이스 초기화 오류: {e}")
    try:
        conn.execute("ALTER TABLE hospitals ADD COLUMN date TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            st.error(f"데이터베이스 초기화 오류: {e}")
    conn.commit()
    conn.close()

def update_empty_usernames(username):
    conn = get_db_connection()
    current_date = datetime.today().strftime('%Y-%m-%d')
    conn.execute("UPDATE hospitals SET username = ?, date = ? WHERE username IS NULL OR username = ''", (username, current_date))
    conn.commit()
    conn.close()

def delete_hospital(name, phone, hours, username, date):
    conn = get_db_connection()
    conn.execute("DELETE FROM hospitals WHERE name=? AND phone=? AND hours=? AND username=? AND date=?", (name, phone, hours, username, date))
    conn.commit()
    conn.close()

def send_to_history(name, phone, hours, username, date):
    conn = get_db_connection()
    current_date = datetime.today().strftime('%Y-%m-%d')
    conn.execute("INSERT INTO hospital_history (username, diagnosis_date, name, phone, hours) VALUES (?, ?, ?, ?, ?)",
                 (username, current_date, name, phone, hours))
    conn.commit()
    conn.close()

# 사이드바에 로그인 상태 표시
with st.sidebar:
    if cookies.get('name'):
        st.write(f"{cookies['name']}님이 로그인 중입니다.")  # 사용자 이름을 표시

        if st.button('로그아웃'):
            cookies['username'] = ""
            cookies['name'] = ""
            cookies.save()  # 쿠키 변경 사항 저장
            if "messages" in st.session_state:
                del st.session_state["messages"]  # 챗봇 메시지 초기화
            if "location" in st.session_state:
                del st.session_state["location"]
            st.session_state['page'] = 'healthytalk'  # 헬시톡 초기화면으로 이동
            st.session_state['page'] = 'nearby_hospital'  # 근처 병원 초기화면으로 이동
            st.session_state['page'] = 'login'
            components.html("""
                <script>
                    window.location.reload();
                </script>
            """)

st.title("근처 진료과를 알려드릴게요🤗")
HtmlFile = open('templates/google_map.html', 'r', encoding='utf-8')
source_code = HtmlFile.read()
source_code = re.sub("%s", loc, source_code)
components.html(source_code, height=550)

# 저장된 병원 정보 표시
st.subheader("저장된 병원 정보")

# 데이터베이스 초기화
initialize_db()

# 새로고침 버튼 추가
if st.button("북마크한 병원 정보 업데이트"):
    if cookies.get('username'):
        update_empty_usernames(cookies['username'])
    else:
        st.error("로그인이 필요합니다.")

# 현재 날짜 가져오기
current_date = datetime.today().strftime('%Y-%m-%d')

# 데이터베이스에서 병원 정보 불러오기
conn = get_db_connection()
hospitals = conn.execute("SELECT name, phone, hours FROM hospitals WHERE username=? AND date=?", (cookies['username'], current_date)).fetchall()
conn.close()

# 병원 정보 표시 및 버튼 클릭 처리
if hospitals:
    for hospital in hospitals:
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            st.write(f"병원명: {hospital['name']}")
            st.write(f"전화번호: {hospital['phone']}")
            st.write(f"운영시간: {hospital['hours']}")
        with col2:
            send_clicked = st.button("저장", key=f"send_{hospital['name']}", use_container_width=True)
            if send_clicked:
                send_to_history(hospital['name'], hospital['phone'], hospital['hours'], cookies['username'], current_date)
                st.experimental_rerun()  # 페이지 리로드
        with col3:
            delete_clicked = st.button("삭제", key=f"delete_{hospital['name']}", use_container_width=True)
            if delete_clicked:
                delete_hospital(hospital['name'], hospital['phone'], hospital['hours'], cookies['username'], current_date)
                st.experimental_rerun()  # 페이지 리로드

        st.write("---")
else:
    st.write("저장된 병원 정보가 없습니다.")
