from openai import OpenAI
import streamlit as st
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
st.title("👨‍⚕️ AI 헬시톡")
st.caption("질환 예측 및 진료과 추천을 위한 AI 어플리케이션") # :로켓:
st.session_state.clear()
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "현재 겪고 계시는 증상을 말씀해주세요."}]
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()
    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

# streamlit run interface.py