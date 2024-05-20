import streamlit as st
import streamlit.components.v1 as components
import re
from streamlit_cookies_manager import EncryptedCookieManager

def find_department(msg):
    loc = re.findall(r"\.\s*([^\.]+)의 전문의에게", msg)[0]
    return loc.split(',')[0]

# 쿠키 관리자 초기화
cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()

# print(st.session_state.messages)
if "messages" not in st.session_state:
    loc = ''
else:
    text = st.session_state.messages[-1]['content']
    if "추천합니다" in text:
        loc = find_department(text)
    else:
        loc = ''

# 사이드바에 로그인 상태 표시
with st.sidebar:
    if cookies.get('name'):
        st.write(f"{cookies['name']}님이 로그인 중입니다.")  # 사용자 이름을 표시

        if st.button('로그아웃'):
            cookies['username'] = ""
            cookies['name'] = ""
            cookies.save()  # 쿠키 변경 사항 저장
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

st.header("근처 진료과를 알려드릴게요🤗")
HtmlFile = open('./templates/google_map.html', 'r', encoding='utf-8')
source_code = HtmlFile.read()
source_code = re.sub("%s", loc, source_code)
components.html(source_code, height=600)