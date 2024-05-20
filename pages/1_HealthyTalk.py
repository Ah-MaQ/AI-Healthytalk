import torch
from transformers import (
    BitsAndBytesConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline
)
from peft import PeftModel
from collections import deque
import re
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AI 헬시톡",
    page_icon="💬",
    layout="wide"
)

cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()

@st.cache_resource
def model_generator(base_model, adapter_dir):
    compute_dtype = getattr(torch, "float16")
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=False,
    )


    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant_config,
        device_map={"": 0}
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 어댑터 추가
    model = PeftModel.from_pretrained(model, adapter_dir)
    pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=128)

    return pipe


def getHistroy():
    history = ''
    for c in st.session_state.messages:
        r, m = c.values()
        if r == 'user':
            history += m + ' '
    return history

def QA_generator(query):
    prompt = f"<s>[INST] {query} [/INST]"

    result = pipe(prompt)
    try:
        response = result[0]['generated_text'].split("[/INST] ")[1]
        if "추천합니다." in response:
            pattern = r'(.*?) 추천합니다\. '
            match = re.search(pattern, response)
            if match:
                response = match.group(0)
                symptom, answer = response.split(" [SYM]")
            else:
                answer = response

        elif "알려드릴게요." in response:
            pattern = r'(.*?) 알려드릴게요\. '
            match = re.search(pattern, response, re.DOTALL)
            if match:
                answer = match.group(0)
            else:
                answer = response
        else:
            answer = result[0]['generated_text']
    except:
        answer = result[0]['generated_text']

    print(f"Q. {query}")
    print(f"A. {answer}")

    return response

# ================================

# 사이드바 설정
with st.sidebar:
    if cookies.get('name'):
        st.write(f"{cookies['name']}님이 로그인 중입니다.")
    if cookies.get('name'):
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

st.header("AI 헬시톡💬")
st.subheader("질환 예측 및 진료과 추천을 위한 AI 어플리케이션") # 🚀

chat_col, detail_col = st.columns([2, 3])


base_model = "beomi/llama-2-ko-7b"
adapter_dir = "./weights/AHT_8"
pipe = model_generator(base_model, adapter_dir)

css = """
<style>
    .custom-column {
        height: 400px;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# padding: 10
# px;
# margin: 10
# px;
# border - radius: 10
# px;
with chat_col:
    chat_col.markdown('<div class="custom-column"></div>', unsafe_allow_html=True)
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant",
                                         "content": "저는 사용자의 불편을 최소화 할 수 있도록 하는 의료 AI 어시스턴트 입니다. 🩺 \n" + \
                                                    "현재 겪고 계시는 증상이 있다면 가감없이 말해주세요. 😃" + \
                                                    "예상되는 질환과 인근의 병원을 알려드릴게요."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not cookies.get('username'):
            st.error("로그인이 필요합니다.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            print("###prompt###: ", prompt)
            # response = get_llama_response(st.session_state.messages[-1]['content'], chat_history)
            response = QA_generator(st.session_state.messages[-1]['content'])
            msg = response
            print("###QA result###: ", response)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
            print("###this is state", st.session_state)
            # print("###this is messages", st.session_state.messages)
            # print("###this is msg from user", st.session_state.messages["user"])

with detail_col:
    components.iframe("https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31969", scrolling=True, height=600)