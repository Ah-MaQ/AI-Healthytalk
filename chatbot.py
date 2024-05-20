import re
import streamlit as st
from collections import deque

import torch
from transformers import (
    BitsAndBytesConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    logging
)
from peft import PeftModel

# 모델 불러오기
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

base_model = "beomi/llama-2-ko-7b"
adapter_dir = "./weights/AHT_8"
pipe = model_generator(base_model, adapter_dir)

# 챗봇
import re
from collections import deque

hisory_lim = 5
chat_history = {'sym': deque([], maxlen=hisory_lim), 'dis': deque([], maxlen=hisory_lim),
                'dep': deque([], maxlen=hisory_lim)}
pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=128)


def QA_generator(query):
    # hist_query = ', '.join(hist for hist in chat_history['user'])
    # if hist_query != '': hist_query += ', '
    # hist_query += query
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
                chat_history['sym'].append(symptom)
                chat_history['dis'].append(re.findall(r"(.+?) 같은 질환이", answer, re.DOTALL)[0])
                chat_history['dep'].append(re.findall(r"의심되네요. (.+?)의 전문의", answer, re.DOTALL)[0])
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
    print(chat_history)

    return response

# 인터페이스
st.title("AI 헬시톡💬")
st.caption("질환 예측 및 진료과 추천을 위한 AI 어플리케이션") # 🚀

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant",
                                     "content": "저는 사용자의 불편을 최소화 할 수 있도록 하는 의료 AI 어시스턴트 입니다. 🩺\n" + \
                                                "현재 겪고 계시는 증상이 있다면 가감없이 말해주세요. 😃\n" + \
                                                "예상되는 질환과 인근의 병원을 알려드릴게요. "}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = QA_generator(st.session_state.messages[-1]['content'])
    msg = response
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)