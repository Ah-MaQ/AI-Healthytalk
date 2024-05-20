import streamlit as st
import sqlite3
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components
import re

# 경고 메시지 억제
st.set_option('client.showErrorDetails', False)

# 쿠키 관리자 초기화
cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()

# 데이터베이스 파일 경로
DB_PATH = "user_database.db"

def create_connection(db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        st.error(f"데이터베이스 연결 실패: {e}")
        return conn

def create_table(conn):
    try:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            gender TEXT NOT NULL
        );
        """
        conn.execute(create_table_sql)
    except Exception as e:
        st.error(f"테이블 생성 실패: {e}")

def add_user(username, password, name, birthdate, gender):
    try:
        conn = create_connection(DB_PATH)
        sql = "INSERT INTO users (username, password, name, birthdate, gender) VALUES (?, ?, ?, ?, ?)"
        conn.execute(sql, (username, password, name, birthdate, gender))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        st.error("회원가입 실패: 사용자 이름이 이미 존재합니다.")
        return False
    except Exception as e:
        st.error(f"사용자 추가 실패: {e}")
        return False

def validate_user(username, password):
    try:
        conn = create_connection(DB_PATH)
        sql = "SELECT name FROM users WHERE username=? AND password=?"
        cur = conn.cursor()
        cur.execute(sql, (username, password))
        result = cur.fetchone()
        conn.close()
        if result:
            return result[0]  # 사용자의 이름 반환
        else:
            return False
    except Exception as e:
        st.error(f"사용자 검증 실패: {e}")
        return False

def update_user(username, password, name, birthdate, gender):
    try:
        conn = create_connection(DB_PATH)
        sql = "UPDATE users SET password=?, name=?, birthdate=?, gender=? WHERE username=?"
        conn.execute(sql, (password, name, birthdate, gender, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"사용자 정보 수정 실패: {e}")
        return False

def delete_user(username):
    try:
        conn = create_connection(DB_PATH)
        sql = "DELETE FROM users WHERE username=?"
        conn.execute(sql, (username,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error("회원 탈퇴 실패: {e}")
        return False

@st.cache_resource
def initialize_db():
    conn = create_connection(DB_PATH)
    if conn is not None:
        create_table(conn)
        conn.close()

initialize_db()

if 'page' not in st.session_state:
    if cookies.get('username'):
        st.session_state['page'] = 'home'
    else:
        st.session_state['page'] = 'login'

def go_to_page(page_name):
    st.session_state['page'] = page_name
    if page_name != 'signup':
        st.session_state['signup_success'] = False

def show_login_page():
    st.title("로그인")
    with st.form("login_form"):
        username = st.text_input("사용자 이름")
        password = st.text_input("비밀번호", type="password")
        submit_button = st.form_submit_button("로그인")

    if submit_button:
        user_name = validate_user(username, password)
        if user_name:
            cookies['username'] = username
            cookies['name'] = user_name
            cookies.save()  # 쿠키 변경 사항 저장
            st.session_state['page'] = 'home'
            st.experimental_rerun()
        else:
            st.error("로그인 실패: 사용자 이름 또는 비밀번호가 잘못되었습니다.")
    st.button("회원가입 페이지로", on_click=go_to_page, args=('signup',))

def show_signup_page():
    st.title("회원가입")

    if st.session_state.get('signup_success', False):
        st.success("회원가입을 축하합니다!")
    else:
        with st.form("signup_form"):
            new_username = st.text_input("아이디")
            new_password = st.text_input("패스워드", type="password")
            name = st.text_input("이름")
            birthdate = st.date_input("생년월일", min_value=datetime(1920, 1, 1), max_value=datetime.today())
            gender = st.selectbox("성별", ["남성", "여성", "기타"])
            submit_button = st.form_submit_button("회원가입")

        if submit_button:
            if add_user(new_username, new_password, name, birthdate, gender):
                st.session_state['signup_success'] = True
                st.experimental_rerun()
            else:
                st.error("회원가입 실패")

    st.button("로그인 페이지로", on_click=go_to_page, args=('login',))

def show_home_page():
    if cookies.get('username'):
        st.write(f"{cookies['username']}님 환영합니다.")
        if st.button("내정보"):
            st.session_state['page'] = 'mypage'
            st.experimental_rerun()
        if st.button("히스토리"):
            st.session_state['page'] = 'history'
            st.experimental_rerun()
    else:
        st.write("로그인되지 않았습니다.")

def show_mypage():
    if not cookies.get('username'):
        st.error("로그인이 필요합니다.")
        return

    st.title("내 정보")
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    if st.session_state.confirm_delete:
        st.write("회원 탈퇴를 하시겠습니까?")
        if st.button("회원탈퇴하기"):
            if delete_user(cookies['username']):
                st.success("회원 탈퇴가 완료되었습니다.")
                cookies['username'] = ""
                cookies['name'] = ""
                cookies.save()  # 쿠키 변경 사항 저장
                st.session_state['page'] = 'login'
                st.experimental_rerun()
            else:
                st.error("회원 탈퇴에 실패했습니다.")
        if st.button("돌아가기"):
            st.session_state.confirm_delete = False
            st.session_state['page'] = 'home'
            st.experimental_rerun()
    else:
        conn = create_connection(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT username, password, name, birthdate, gender FROM users WHERE username=?", (cookies['username'],))
        user_data = cur.fetchone()
        conn.close()

        if not user_data:
            st.error("사용자 정보를 불러오는데 실패했습니다.")
            return

        username, password, name, birthdate, gender = user_data

        with st.form("mypage_form"):
            new_password = st.text_input("패스워드", value=password, type="password")
            new_name = st.text_input("이름", value=name)
            new_birthdate = st.date_input("생년월일", value=datetime.strptime(birthdate, "%Y-%m-%d"), min_value=datetime(1920, 1, 1), max_value=datetime.today())
            new_gender = st.selectbox("성별", ["남성", "여성", "기타"], index=["남성", "여성", "기타"].index(gender))
            submit_button = st.form_submit_button("수정")

        if submit_button:
            if update_user(username, new_password, new_name, new_birthdate, new_gender):
                st.success("회원 정보가 수정되었습니다.")
                cookies['name'] = new_name
                cookies.save()  # 쿠키 변경 사항 저장
            else:
                st.error("회원 정보 수정에 실패했습니다.")

        if st.button("홈으로"):
            st.session_state['page'] = 'home'
            st.experimental_rerun()

        if st.button("회원탈퇴"):
            st.session_state.confirm_delete = True
            st.experimental_rerun()

def show_history():
    st.write("채팅 히스토리 페이지입니다.")
    for message in st.session_state.get("messages", []):
        if message["role"] == "assistant":
            diagnosis[0] = re.findall(r"(.+?) 같은 질환이", message["content"], re.DOTALL)
            specialty[0] = re.findall(r"의심되네요. (.+?)의 전문의", message["content"], re.DOTALL)
            if diagnosis_match and specialty_match:
                diagnosis = diagnosis[0]
                specialty = specialty[0]
                st.write(f"의심되는 진단명: {diagnosis}, 추천 진료과: {specialty}")
    if st.button("홈으로"):
        st.session_state['page'] = 'home'
        st.experimental_rerun()

# 페이지 전환 로직
if 'page' not in st.session_state:
    if cookies.get('username'):
        st.session_state['page'] = 'home'
    else:
        st.session_state['page'] = 'login'
if st.session_state['page'] == 'login':
    show_login_page()
elif st.session_state['page'] == 'signup':
    show_signup_page()
elif st.session_state['page'] == 'home':
    show_home_page()
elif st.session_state['page'] == 'mypage':
    show_mypage()
elif st.session_state['page'] == 'history':
    show_history()

# 사이드바 설정
with st.sidebar:
    if cookies.get('name'):
        st.write(f"{cookies['name']}님이 로그인 중입니다.")
        if st.button('로그아웃'):
            cookies['username'] = ""
            cookies['name'] = ""
            cookies.save()
            if "messages" in st.session_state:
                del st.session_state["messages"]
            if "location" in st.session_state:
                del st.session_state["location"]
            st.session_state['page'] = 'healthytalk'
            st.session_state['page'] = 'nearby_hostpital'
            st.session_state['page'] = 'login'  # 로그인 페이지로 이동
            components.html("""
                <script>
                    window.location.reload();
                </script>
            """)
            st.experimental_rerun()
