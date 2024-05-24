import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components
import re
import pandas as pd
import base64
from pyparsing import empty

st.set_page_config(
    page_title="AI 헬시톡",
    page_icon="💬",
    layout="wide"
)

# 경고 메시지 억제
st.set_option('client.showErrorDetails', False)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 10px !important;
        padding-down: 50px;
    }
    .st-emotion-cache-1jicfl2 {
        padding-top: 10px !important;
        padding-down: 50px;
    }
    .ea3mdgi5 {
        padding-top: 10px !important;
        padding-down: 50px;   
    </style>
    """,
    unsafe_allow_html=True
)

# 쿠키 관리자 초기화
cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()

# 데이터베이스 파일 경로
DB_PATH = "data/user_database.db"


def create_connection(db_path):
    try:
        return sqlite3.connect(db_path)
    except Exception as e:
        st.error(f"데이터베이스 연결 실패: {e}")
        return None


def create_tables(conn):
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            gender TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_history (
            username TEXT NOT NULL,
            diagnosis_date TEXT NOT NULL,
            number INTEGER NOT NULL,
            diagnosis TEXT NOT NULL,
            specialty TEXT NOT NULL,
            PRIMARY KEY (username, diagnosis_date, number),
            FOREIGN KEY (username) REFERENCES users(username)
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hospital_history (
            username TEXT NOT NULL,
            diagnosis_date TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            hours TEXT NOT NULL,
            PRIMARY KEY (username, diagnosis_date, name, phone, hours),
            FOREIGN KEY (username) REFERENCES users(username)
        );
        """)
    except Exception as e:
        st.error(f"테이블 생성 실패: {e}")


def add_user(username, password, name, birthdate, gender):
    try:
        conn = create_connection(DB_PATH)
        conn.execute("INSERT INTO users (username, password, name, birthdate, gender) VALUES (?, ?, ?, ?, ?)",
                     (username, password, name, birthdate, gender))
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
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE username=? AND password=?", (username, password))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else False
    except Exception as e:
        st.error(f"사용자 검증 실패: {e}")
        return False


def update_user(username, password, name, birthdate, gender):
    try:
        conn = create_connection(DB_PATH)
        conn.execute("UPDATE users SET password=?, name=?, birthdate=?, gender=? WHERE username=?",
                     (password, name, birthdate, gender, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"사용자 정보 수정 실패: {e}")
        return False


def delete_user(username):
    try:
        conn = create_connection(DB_PATH)
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"회원 탈퇴 실패: {e}")
        return False


def add_diagnosis_history(username, diagnosis, specialty):
    try:
        conn = create_connection(DB_PATH)
        cur = conn.cursor()
        current_date = datetime.today().strftime('%Y-%m-%d')
        cur.execute(
            "SELECT COUNT(*) FROM diagnosis_history WHERE username=? AND diagnosis_date=? AND diagnosis=? AND specialty=?",
            (username, current_date, diagnosis, specialty))
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute(
                "SELECT COALESCE(MAX(number), 0) + 1 FROM diagnosis_history WHERE username=? AND diagnosis_date=?",
                (username, current_date))
            number = cur.fetchone()[0]
            conn.execute(
                "INSERT INTO diagnosis_history (username, diagnosis_date, number, diagnosis, specialty) VALUES (?, ?, ?, ?, ?)",
                (username, current_date, number, diagnosis, specialty))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"진단 기록 추가 실패: {e}")
        return False


@st.cache_resource
def initialize_db():
    conn = create_connection(DB_PATH)
    if conn is not None:
        create_tables(conn)
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


# def show_login_page():
#     st.title("로그인")
#
#     ##### CSS를 이용하여 테두리를 제거하는 스타일 추가
#     st.markdown(
#         """
#         <style>
#         /* st.form 기본 테두리 제거 */
#         div[data-testid="stForm"] {
#             border: none !important;
#             box-shadow: none !important;
#             padding: 0px !important; /* 패딩 추가 */
#         }
#
#         /* 아이디, 비밀번호 입력창을 감싸는 div의 크기 및 스타일 조정 */
#         div[data-testid="stTextInput"], div[data-testid="stPassword"] {
#             width: 500px !important;
#             background-color: #ffffff !important; /* 배경색 변경 */
#             color: #333 !important; /* 텍스트 색상 변경 */
#             border: none !important; /* 테두리 색상 및 두께 변경 */
#             border-radius: 5px !important; /* 테두리 둥글게 */
#             padding: 0px !important; /* 패딩 추가 */
#             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
#             margin-top: 10px !important; /* 위쪽 여백 추가 */
#             position: relative;
#         }
#
#         /* 입력 필드의 크기 및 스타일 조정 */
#         div[data-testid="stTextInput"] input, div[data-testid="stPassword"] input {
#             width: 100% !important;
#             background-color: #F0F2F6 !important; /* 배경색 변경 */
#             color: #333 !important; /* 텍스트 색상 변경 */
#             border: 1px #E0E4E8 !important; /* 입력 필드 자체의 테두리 제거 */
#             border-radius: 5px !important; /* 테두리 둥글게 */
#             padding: 10px !important; /* 패딩 추가 */
#             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
#             box-shadow: inset 4px 3px 4px rgba(0, 0, 0, 0.25); /* 안쪽 그림자 효과 추가 */
#         }
#
#
#         /* 로그인 버튼의 스타일 조정 */
#         div[data-testid="stFormSubmitButton"] button {
#             width: 500px !important;
#             background-color: #50E3C2 !important; /* 배경색 변경 */
#             color: #fff !important; /* 텍스트 색상 변경 */
#             border: none !important; /* 테두리 색상 및 두께 변경 */
#             border-radius: 5px !important; /* 테두리 둥글게 */
#             padding: 10px !important; /* 패딩 추가 */
#             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
#             margin-top: 10px !important; /* 위쪽 여백 추가 */
#         }
#
#         /* 회원가입 버튼의 스타일 조정 */
#         div[data-testid="stButton"] button {
#             width: 500px !important;
#             background-color: #50E3C2 !important; /* 배경색 변경 */
#             color: #fff !important; /* 텍스트 색상 변경 */
#             border: none !important; /* 테두리 색상 및 두께 변경 */
#             border-radius: 5px !important; /* 테두리 둥글게 */
#             padding: 10px !important; /* 패딩 추가 */
#             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
#             margin-top: -200px !important; /* 위쪽 여백 추가 */
#         }
#
#         </style>
#         """,
#         unsafe_allow_html=True
#     )
#
#     with st.form("login_form"):
#         st.markdown('<div class="login-form-container">', unsafe_allow_html=True)
#         st.write("user id")
#         username = st.text_input("사용자 이름", placeholder="id를 입력하세요", label_visibility="collapsed")
#         st.write("password")
#         password = st.text_input("비밀번호", label_visibility="collapsed", type="password")
#         submit_button = st.form_submit_button("로그인")
#         st.markdown('</div>', unsafe_allow_html=True)
#
#     if submit_button:
#         user_name = validate_user(username, password)
#         if user_name:
#             cookies['username'] = username
#             cookies['name'] = user_name
#             cookies.save()
#             st.session_state['page'] = 'home'
#             st.experimental_rerun()
#         else:
#             st.error("로그인 실패: 사용자 이름 또는 비밀번호가 잘못되었습니다.")
#     st.button("회원가입 페이지로", on_click=go_to_page, args=('signup',))

def show_login_page():
    st.title("로그인")
    con1, con2= st.columns([0.7, 0.3])

    #     ##### CSS를 이용하여 테두리를 제거하는 스타일 추가
    #     st.markdown(
    #         """
    #         <style>
    #         /* 로그인 버튼의 스타일 조정 */
    #         div[data-testid="stFormSubmitButton"] button {
    #             width: 500px !important;
    #             background-color: #50E3C2 !important; /* 배경색 변경 */
    #             color: #fff !important; /* 텍스트 색상 변경 */
    #             border: none !important; /* 테두리 색상 및 두께 변경 */
    #             border-radius: 5px !important; /* 테두리 둥글게 */
    #             padding: 10px !important; /* 패딩 추가 */
    #             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
    #             margin-top: 10px !important; /* 위쪽 여백 추가 */
    #         }
    #
    #         /* 회원가입 버튼의 스타일 조정 */
    #         div[data-testid="stButton"] button {
    #             width: 500px !important;
    #             background-color: #50E3C2 !important; /* 배경색 변경 */
    #             color: #fff !important; /* 텍스트 색상 변경 */
    #             border: none !important; /* 테두리 색상 및 두께 변경 */
    #             border-radius: 5px !important; /* 테두리 둥글게 */
    #             padding: 10px !important; /* 패딩 추가 */
    #             box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
    #             margin-top: -200px !important; /* 위쪽 여백 추가 */
    #         }
    #
    #         </style>
    #         """,
    #         unsafe_allow_html=True
    #     )


    with con1:

        st.markdown(
            """
            <style>
            
            /* st.form 기본 테두리 제거 */
            div[data-testid="stForm"] {
                border: none !important;
                box-shadow: none !important;
                padding: 0px !important; /* 패딩 추가 */
            }
            
            /* 공통 부모 div의 스타일 조정 */
            div[data-testid="stTextInput"], 
            div[data-testid="stPassword"], 
            div[data-testid="stFormSubmitButton"], 
            div[data-testid="stButton"] {
                width: 90%; /* 너비를 100%로 설정 */
                margin: 0 auto; /* 중앙 정렬 */
                border-radius: 5px !important; /* 테두리 둥글게 */
                padding: 0px !important; /* 패딩 추가 */
                box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
                position: relative;
            }
            
            div[data-testid="stTextInput"], 
            div[data-testid="stPassword"] {
                margin-left: -3px !important; /* 위쪽 여백 추가 */
            }
            
            
            /* 입력 필드의 크기 및 스타일 조정 */
            div[data-testid="stTextInput"] input, 
            div[data-testid="stPassword"] input {
                width: 100% !important;
                background-color: #F0F2F6 !important; /* 배경색 변경 */
                color: #333 !important; /* 텍스트 색상 변경 */
                border: 1px #E0E4E8 !important; /* 입력 필드 자체의 테두리 제거 */
                border-radius: 5px !important; /* 테두리 둥글게 */
                padding: 10px !important; /* 패딩 추가 */
                box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
                box-shadow: inset 4px 3px 4px rgba(0, 0, 0, 0.25); /* 안쪽 그림자 효과 추가 */
            }
            
            /* 로그인 버튼의 스타일 조정 */
            div[data-testid="stFormSubmitButton"] button {
                width: 90% !important; /* 너비를 100%로 설정 */
                background-color: #909393 !important; /* 배경색 변경 */
                color: #fff !important; /* 텍스트 색상 변경 */
                font-weight: 900;
                border: none !important; /* 테두리 색상 및 두께 변경 */
                border-radius: 5px !important; /* 테두리 둥글게 */
                padding: 10px !important; /* 패딩 추가 */
                box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
                margin-top: 10px !important; /* 위쪽 여백 추가 */
            }
            
            /* 회원가입 버튼의 스타일 조정 */
            div[data-testid="stButton"] button {
                width: 90% !important; /* 너비를 95%로 설정 */
                background-color: #909393 !important; /* 배경색 변경 */
                color: #fff !important; /* 텍스트 색상 변경 */
                border: none !important; /* 테두리 색상 및 두께 변경 */
                border-radius: 5px !important; /* 테두리 둥글게 */
                padding: 10px !important; /* 패딩 추가 */
                box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
                margin-top: -2px !important; /* 위쪽 여백 추가 */
            }


            </style>
            """,
            unsafe_allow_html=True
        )



        with st.form("login_form"):
            st.markdown('<div class="login-form-container">', unsafe_allow_html=True)
            st.write("user id")
            username = st.text_input("사용자 이름", placeholder="id를 입력하세요", label_visibility="collapsed")
            st.write("password")
            password = st.text_input("비밀번호", placeholder="password를 입력하세요", label_visibility="collapsed", type="password")
            submit_button = st.form_submit_button("로그인")
            st.markdown('</div>', unsafe_allow_html=True)

        if submit_button:
            user_name = validate_user(username, password)
            if user_name:
                cookies['username'] = username
                cookies['name'] = user_name
                cookies.save()
                st.session_state['page'] = 'home'
                st.experimental_rerun()
            else:
                st.error("로그인 실패: 사용자 이름 또는 비밀번호가 잘못되었습니다.")
        st.button("회원가입 페이지로", on_click=go_to_page, args=('signup',))

    with con2:
        img_path = 'logo/healthytalk.png'
        css_style = """
        <style>
            .custom-image1 {
                margin-left: -60px;  /* 이미지 위에 마진 추가 */
                margin-top: -50px;  /* 이미지 위에 마진 추가 */
                width: 530px;  /* 이미지 너비 조절 */
                height: auto;  /* 이미지 높이는 비율에 맞춰 자동 조절 */
            }
        </style>
        """
        st.markdown(css_style, unsafe_allow_html=True)
        st.markdown(
            f'<img src="data:image/png;base64,{img_to_base64(img_path)}" width="300" height="300" class="custom-image1">',
            unsafe_allow_html=True,
        )


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
    # st.markdown(
    #     """
    #     <style>
    #
    #     /* 내정보, 히스토리의 스타일 조정 */
    #     div[data-testid="stButton"] button {
    #         width: 500px !important;
    #         background-color: #50E3C2 !important; /* 배경색 변경 */
    #         color: #fff !important; /* 텍스트 색상 변경 */
    #         border: none !important; /* 테두리 색상 및 두께 변경 */
    #         border-radius: 5px !important; /* 테두리 둥글게 */
    #         padding: 10px !important; /* 패딩 추가 */
    #         box-sizing: border-box; /* 테두리와 패딩을 포함한 크기 조정 */
    #         margin-top: 10px !important; /* 위쪽 여백 추가 */
    #     }
    #
    #     </style>
    #     """,
    #     unsafe_allow_html=True
    # )

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
                cookies.save()
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
        cur.execute("SELECT username, password, name, birthdate, gender FROM users WHERE username=?",
                    (cookies['username'],))
        user_data = cur.fetchone()
        conn.close()

        if not user_data:
            st.error("사용자 정보를 불러오는데 실패했습니다.")
            return

        username, password, name, birthdate, gender = user_data

        with st.form("mypage_form"):
            new_password = st.text_input("패스워드", value=password, type="password")
            new_name = st.text_input("이름", value=name)
            new_birthdate = st.date_input("생년월일", value=datetime.strptime(birthdate, "%Y-%m-%d"),
                                          min_value=datetime(1920, 1, 1), max_value=datetime.today())
            new_gender = st.selectbox("성별", ["남성", "여성", "기타"], index=["남성", "여성", "기타"].index(gender))
            submit_button = st.form_submit_button("수정")

        if submit_button:
            if update_user(username, new_password, new_name, new_birthdate, new_gender):
                st.success("회원 정보가 수정되었습니다.")
                cookies['name'] = new_name
                cookies.save()
            else:
                st.error("회원 정보 수정에 실패했습니다.")

        if st.button("홈으로"):
            st.session_state['page'] = 'home'
            st.experimental_rerun()

        if st.button("회원탈퇴"):
            st.session_state.confirm_delete = True
            st.experimental_rerun()


def show_history():
    if not cookies.get('username'):
        st.error("로그인이 필요합니다.")
        return

    st.markdown(
        """
        <style>
        .h1 {
            padding-down: 300px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    st.title(f"{cookies['name']}님의 헬시톡 이용 기록입니다.")

    # 커스텀 CSS 추가
    st.markdown("""
        <style>

        .custom-table {
            margin-bottom: 50px;
        }        
        
        .custom-table thead th {
            text-align: center;
        }
        .custom-table tbody tr th {
            text-align: center;
        }
        .custom-table tbody tr td {
            text-align: center;
            width: 150px; /* 열 너비 조정 */
        }
        .custom-table tbody tr td:nth-child(1) {
            width: 100px; /* 마지막 열의 너비 조정 */
        }        

        .custom-table tbody tr td:nth-child(4) {
            width: 400px; /* 마지막 열의 너비 조정 */
        }

        .custom-table tbody tr td:nth-child(5) {
            width: 400px; /* 마지막 열의 너비 조정 */
        }

        </style>
    """, unsafe_allow_html=True)

    # 버튼 및 기간 선택
    col_text, empty2, col1, col2, col3, col4, col5, col6, col7 = st.columns([0.8, 0.1, 0.5, 0.5, 0.5, 0.5, 1, 0.1, 1])

    with col_text:
        st.write("")
        st.write("")
        st.subheader("기간 설정")
        st.write("")
        st.write("")

    with empty2:
        st.write("")
        st.write("")
        st.empty()

    with col1:
        st.write("")
        st.write("")
        if st.button("최근 1주일"):
            st.session_state['start_date'] = datetime.today() - timedelta(days=7)
            st.session_state['end_date'] = datetime.today()
    with col2:
        st.write("")
        st.write("")
        if st.button("최근 1개월"):
            st.session_state['start_date'] = datetime.today() - timedelta(days=30)
            st.session_state['end_date'] = datetime.today()
    with col3:
        st.write("")
        st.write("")
        if st.button("최근 3개월"):
            st.session_state['start_date'] = datetime.today() - timedelta(days=90)
            st.session_state['end_date'] = datetime.today()
    with col4:
        st.write("")
        st.write("")
        if st.button("최근 6개월"):
            st.session_state['start_date'] = datetime.today() - timedelta(days=180)
            st.session_state['end_date'] = datetime.today()
    with col5:
        st.write("")
        st.write("")
        start_date = st.date_input("시작 날짜",
                                   value=st.session_state.get('start_date', datetime.today() - timedelta(days=30)),
                                   min_value=datetime(1920, 1, 1), max_value=datetime.today(),
                                   label_visibility="collapsed")
    with col6:
        st.write("")
        st.write("")
        st.write("~")
    with col7:
        st.write("")
        st.write("")
        end_date = st.date_input("종료 날짜", value=st.session_state.get('end_date', datetime.today()),
                                 min_value=datetime(1920, 1, 1), max_value=datetime.today(),
                                 label_visibility="collapsed")


    col8, col9 = st.columns([39, 10])

    with col8:
        record_type = st.selectbox("기록 유형 선택", ["기록 전체", "진단 기록", "병원 기록"], label_visibility="collapsed")
        st.write("")
        st.write("")

    with col9:
        if st.button("조회", use_container_width=True):
            conn = create_connection(DB_PATH)
            if conn is None:
                return

            cur = conn.cursor()

            diagnosis_data = []
            hospital_data = []

            if record_type == "기록 전체" or record_type == "진단 기록":
                cur.execute(
                    "SELECT diagnosis_date, number, diagnosis, specialty FROM diagnosis_history WHERE username=? AND diagnosis_date BETWEEN ? AND ? ORDER BY diagnosis_date, number",
                    (cookies['username'], start_date, end_date))
                rows = cur.fetchall()
                if rows:
                    for row in rows:
                        diagnosis_date, number, diagnosis, specialty = row
                        diagnosis_data.append({
                            "날짜": diagnosis_date,
                            "진단명": diagnosis,
                            "진료과": specialty
                        })

            if record_type == "기록 전체" or record_type == "병원 기록":
                cur.execute(
                    "SELECT diagnosis_date, name, phone, hours FROM hospital_history WHERE username=? AND diagnosis_date BETWEEN ? AND ? ORDER BY diagnosis_date",
                    (cookies['username'], start_date, end_date))
                hospital_rows = cur.fetchall()
                if hospital_rows:
                    for row in hospital_rows:
                        diagnosis_date, name, phone, hours = row
                        hospital_data.append({
                            "날짜": diagnosis_date,
                            "병원명": name,
                            "전화번호": phone,
                            "운영시간": hours
                        })

            conn.close()

            # 현재 날짜에 저장된 진단 정보를 가져옴
            existing_today_diagnoses = get_today_diagnoses(cookies['username'])

            new_entries = []
            for message in st.session_state.get("messages", []):
                if message["role"] == "assistant":
                    diagnosis_match = re.search(r'(.+?) 같은 질환이 의심되네요', message["content"])
                    specialty_match = re.search(r'\.\s*([^\.]+)의 전문의에게', message["content"])
                    if diagnosis_match and specialty_match:
                        diagnosis = diagnosis_match.group(1)
                        specialty = specialty_match.group(1)
                        if (diagnosis, specialty) not in existing_today_diagnoses:
                            new_entry = (diagnosis, specialty)
                            new_entries.append(new_entry)

            if new_entries:
                for diagnosis, specialty in new_entries:
                    add_diagnosis_history(cookies['username'], diagnosis, specialty)
                    st.write(f"의심되는 진단명: {diagnosis}, 추천 진료과: {specialty}")


    # 결과 출력
    if 'diagnosis_data' in locals():
        if diagnosis_data:
            st.text("진단 기록:")
            diagnosis_df = pd.DataFrame(diagnosis_data)
            diagnosis_df.index += 1  # Make index start from 1
            st.markdown(diagnosis_df.to_html(classes='custom-table'), unsafe_allow_html=True)
        else:
            st.write(f"{start_date}부터 {end_date}까지 진단 기록이 없습니다.")

    if 'hospital_data' in locals():
        if hospital_data:
            st.text("병원 정보:")
            hospital_df = pd.DataFrame(hospital_data)
            hospital_df.index += 1  # Make index start from 1
            st.markdown(hospital_df.to_html(classes='custom-table'), unsafe_allow_html=True)
        else:
            st.write(f"{start_date}부터 {end_date}까지 병원 정보가 없습니다.")

    if st.button("홈으로"):
        st.session_state['page'] = 'home'
        st.experimental_rerun()



def get_today_diagnoses(username):
    conn = create_connection(DB_PATH)
    cur = conn.cursor()
    current_date = datetime.today().strftime('%Y-%m-%d')
    cur.execute("SELECT diagnosis, specialty FROM diagnosis_history WHERE username=? AND diagnosis_date=?",
                (username, current_date))
    rows = cur.fetchall()
    conn.close()
    return set(rows)  # 중복 확인을 위해 set 사용


def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


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
            st.session_state['page'] = 'healthytalk'
            st.session_state['page'] = 'nearby_hospital'
            st.session_state['page'] = 'login'
            components.html("""
                <script>
                    window.location.reload();
                </script>
            """)
            st.experimental_rerun()
    img_path = 'logo/ahmaq.png'
    css_style = """
    <style>
        .custom-image2 {
            width: 300px;  /* 이미지 너비 조절 */
            height: auto;  /* 이미지 높이는 비율에 맞춰 자동 조절 */
        }
    </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)
    st.markdown(
        f'<img src="data:image/png;base64,{img_to_base64(img_path)}" width="100" height="100" class="custom-image2">',
        unsafe_allow_html=True,
    )

# 페이지 전환 로직
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

print(st.session_state)