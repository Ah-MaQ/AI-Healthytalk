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
import requests
from bs4 import BeautifulSoup
import csv

st.set_page_config(
    page_title="AI 헬시톡",
    page_icon="💬",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0 !important;
        padding-down: 50px;
    }
    .st-emotion-cache-7tauuy {
        padding-top: 0 !important;
        padding-down: 50px;
    }
    .ea3mdgi5 {
        padding-top: 0 !important;
        padding-down: 50px;
    }
    
    .st-emotion-cache-qcqlej.ea3mdgi1{
        height: 10px !important;
    }
    
    st-emotion-cache-qdbtli.ea3mdgi2{
        height: 200px;
        padding-down: 200px;       
    }
        

    </style>
    """,
    unsafe_allow_html=True
)

cookies = EncryptedCookieManager(prefix="my_project", password="my_super_secret_password")
if not cookies.ready():
    st.stop()


@st.cache_resource
def load_model():
    base_model = "beomi/llama-2-ko-7b"

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
    adapter_dir = "model/AHT_8"
    model = PeftModel.from_pretrained(model, adapter_dir)

    return pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=80)


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
    print("@@@ result:", result)
    try:
        response = result[0]['generated_text'].split("[/INST] ")[1]
        if "추천합니다." in response:
            pattern = r'(.*?) 추천합니다\. '
            match = re.search(pattern, response)
            if match:
                response = match.group(0)
                print("@@@ here is response:", response)
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

    return answer


@st.cache_data
def getcodedb():
    data_dict = {}
    # CSV 파일 읽어오기
    with open("./data/output.csv", mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 각 행의 '컬럼 a'를 키로, '컬럼 b'를 값으로 하는 딕셔너리에 추가
            data_dict[row['질환명'].strip()] = row['코드'].strip()
    return data_dict


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

##### 여기가 추가된 곳
st.markdown(
    """
    <style>

    /* 입력 필드의 크기 및 스타일 조정 */
    div[data-testid="stChatInput"] textarea {
        width: 100% !important;
        background-color: #F0F2F6 !important; /* 배경색 변경 */
        color: #333 !important; /* 텍스트 색상 변경 */
        border: 1px solid #E0E4E8 !important; /* 입력 필드 자체의 테두리 추가 */
        border-radius: 5px !important; /* 테두리 둥글게 */
        height: 45px;
        box-shadow: inset 4px 3px 4px rgba(0, 0, 0, 0.25); /* 안쪽 그림자 효과 추가 */
    }

    /* 사용자 말풍선 스타일 */
    .user-message {
        background-color: #D4EFE6; /* 사용자 말풍선의 배경색 */
        color: #333; /* 사용자 말풍선의 텍스트 색상 */
        border-radius: 15px; /* 말풍선의 모서리를 둥글게 만듭니다. */
        padding: 15px; /* 말풍선 안의 내용과 테두리 사이의 여백을 조절합니다. */
        margin-bottom: 20px; /* 말풍선 사이의 간격을 조절합니다. */
        align-self: flex-end; /* 사용자 말풍선을 오른쪽에 정렬합니다. */
        margin-left: 65px; /* 사용자 말풍선의 외부 여백을 조정하여 왼쪽 여백 추가 */
    }

    /* 챗봇 말풍선 스타일 */
    .assistant-message {
        background-color: #FEE6D5; /* 챗봇 말풍선의 배경색 */
        color: #333; /* 챗봇 말풍선의 텍스트 색상 */
        border-radius: 15px; /* 말풍선의 모서리를 둥글게 만듭니다. */
        padding: 15px; /* 말풍선 안의 내용과 테두리 사이의 여백을 조절합니다. */
        margin-bottom: 20px; /* 말풍선 사이의 간격을 조절합니다. */
        align-self: flex-start; /* 챗봇 말풍선을 왼쪽에 정렬합니다. */
        margin-right: 65px; /* 사용자 말풍선의 외부 여백을 조정하여 왼쪽 여백 추가 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("AI 헬시톡💬")
st.caption("질환 예측 및 진료과 추천을 위한 AI 어플리케이션")  # 🚀

chat_col, detail_col = st.columns([2, 3])

history_lim = 5
chat_history = {'user': deque([""], maxlen=history_lim), 'assistant': deque([""], maxlen=history_lim)}
pipe = load_model()
loading_text = st.empty()

with chat_col:
    with st.container(height=600):
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant",
                                             "content": "저는 사용자의 불편을 최소화 할 수 있도록 하는 의료 AI 어시스턴트 입니다. 🩺 \n" + \
                                                        "현재 겪고 계시는 증상이 있다면 가감없이 말해주세요. 😃" + \
                                                        "예상되는 질환과 인근의 병원을 알려드릴게요."}]

        # for msg in st.session_state.messages:
        #     st.chat_message(msg["role"]).write(msg["content"])
        #####
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
        #####
        if prompt := st.chat_input():

            if not cookies.get('username'):
                st.error("로그인이 필요합니다.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
                # st.chat_message("user").write(prompt)
                loading_text = st.empty()
                loading_text.write("적절한 증상, 진료과를 찾고 있습니다. 잠시만 기다려주세요~")
                print("###prompt###: ", prompt)
                # response = get_llama_response(st.session_state.messages[-1]['content'], chat_history)
                response = QA_generator(st.session_state.messages[-1]['content'])
                msg = response
                loading_text.write("찾았습니다!")
                loading_text.empty()  # 로딩 메시지 삭제
                print("###QA result###: ", response)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message("assistant").write(msg)
                print("###this is state", st.session_state)
                # print("###this is messages", st.session_state.messages)
                # print("###this is msg from user", st.session_state.messages["user"])
                st.experimental_rerun()

with detail_col:
    with st.container(height=600):
        data_dict = getcodedb()
        key = re.findall(r'([가-힣 ]+) 같은 질환이 의심되네요.', st.session_state.messages[-1][
            'content'])  # '상기도 감염 같은 질환이 의심되네요. 신경과의 전문의에게 상담을 받아보시는 것을 추천합니다.'
        if key != []:
            # st.subheader(f"{key[0]}의 상세정보")
            code = data_dict.get(key[0])  # key[0]
            if code is not None:
                st.markdown(f"<h3 style='font-size: 22px;'>{key[0]}의 상세정보</h3>", unsafe_allow_html=True)
                print(f"키 '{key[0]}'에 해당하는 값: {code}")
                url = f'https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId={code}'
                response = requests.get(url)

                # BeautifulSoup으로 HTML 파싱
                soup = BeautifulSoup(response.content, 'html.parser')

                # # 이미지 태그 제거
                # for img in soup.find_all('img'):
                #     img.decompose()

                # 특정 부분 가져오기
                target_element = soup.find('div', class_='contDescription')
                target_html = str(target_element)

                # Streamlit에 HTML ]
                st.components.v1.html(target_html, height=540, scrolling=True)
            else:
                st.markdown(f"<h3 style='font-size: 22px;'>{key[0]}은(는) 실제 존재하지 않는 병이거나 추가될 예정입니다.</h3>",
                            unsafe_allow_html=True)
                print(f"키 '{key}'에 해당하는 값이 존재하지 않습니다.")
        else:
            st.markdown(f"<h3 style='font-size: 22px;'>어디가 불편하신지 말씀해주시면, 해당 증상에 대해 자세히 안내해드리겠습니다.</h3>",
                        unsafe_allow_html=True)
            # st.subheader("어디가 불편하신지 말씀해주시면, 해당 증상에 대해 자세히 안내해 드리겠습니다.", )