# 환경 설정
import os
os.environ['HF_CODE'] = "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"

from huggingface_hub import login
login(token=os.environ.get("HF_CODE"))

# 모델 불러오기
import torch
from transformers import (
    BitsAndBytesConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    logging
)
from peft import PeftModel

def model_generator(base_model, adapter_dir):
    compute_dtype = getattr(torch, "float16")
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=False,
    )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if torch.cuda.is_available():
        device_map = {"": 0}
    else:
        device_map = {}
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant_config,
        device_map=device_map
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1
    model.to(device)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 어댑터 추가
    model = PeftModel.from_pretrained(model, adapter_dir)
    model.to(device)
    return model

base_model = "beomi/llama-2-ko-7b"
adapter_dir = "./weights/AHT_5"
model = model_generator(base_model, adapter_dir)


# 챗봇
import re
import streamlit as st
from collections import deque

hisory_lim = 5
chat_history = {'user':deque([], maxlen=hisory_lim),'assistant':deque([], maxlen=hisory_lim)}

def QA_generator(query):
    hist_query = ' '.join(hist + query for hist in chat_history['user'])
    prompt = f"<s>[INST] {hist_query} [/INST]"

    pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=100)
    result = pipe(prompt)
    response = result[0]['generated_text']
    if "추천합니다." in response:
        pattern = r'\[/INST\] (.*?) 추천합니다\. '
        match = re.search(pattern, response)
        if match:
            response = match.group(0)[8:]
            chat_history['user'].append(query)
            chat_history['assistant'].append(response)
    elif "알려드릴게요." in response:
        pattern = r'\[/INST\] (.*?) 알려드릴게요\. '
        match = re.search(pattern, response, re.DOTALL)
        if match:
            response = match.group(0)[8:]

    print(f"Q. {prompt}")
    print(f"A. {response}")

    return response

logging.set_verbosity(logging.CRITICAL)
st.title("AI 헬시톡💬")
st.caption("질환 예측 및 진료과 추천을 위한 AI 어플리케이션") # 🚀


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant",
                                     "content": "저는 사용자의 불편을 최소화 할 수 있도록 하는 의료 AI 어시스턴트 입니다. 🩺 \n" + \
                                                "현재 겪고 계시는 증상이 있다면 가감없이 말해주세요. 😃" + \
                                                "예상되는 질환과 인근의 병원을 알려드릴게요. "}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = QA_generator(st.session_state.messages[-1]['content'], chat_history)
    msg = response
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)