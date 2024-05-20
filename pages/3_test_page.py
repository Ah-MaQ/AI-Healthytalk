import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(layout="wide")
# embed streamlit docs in a streamlit app
components.iframe("https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31969", width=1300, height=1080, scrolling=True)