import streamlit as st
import streamlit.components.v1 as components
import re

print(st.session_state.messages)
text = st.session_state.messages[-1]['content']

loc = re.findall(r"\.\s*([^\.]+)의 전문의에게", text)[0]
# loc = ['소아신경과'][0]
loc = loc.split(',')[0]

st.header("근처 진료과를 알려드릴게요🤗")
HtmlFile = open('./templates/google_map.html', 'r', encoding='utf-8')
source_code = HtmlFile.read()
source_code = re.sub("%s", loc, source_code)
components.html(source_code, height=600)