import os
os.environ['HF_CODE'] = "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"

from huggingface_hub import login

login(token=os.environ.get("HF_CODE"))

import json
import numpy as np
from datasets import Dataset
# disease['질환명'] + ' 같은 질환이 의심되네요. ' + disease['진료과목'] + '의 전문의에게 상담을 받아보시는 것을 추천합니다. '
with open('data/only_diseases.json','r',encoding='utf-8') as f:
    ori_data = json.load(f)
dataset = []
for disease in ori_data:
    inputs = disease["instruction"]
    response = disease["output"]
    dataset.append(f'<s>[INST] {inputs} [/INST] {response} </s>')

with open('data/alpaca_data.json','r',encoding='utf-8') as f:
    data = json.load(f)

selected_list = np.random.choice(len(data), 1000, replace=False)

for i in selected_list:
    if data[i]["input"] == "":
        inputs = data[i]["instruction"]
        response = "저는 사용자의 불편을 최소화 할 수 있도록 하는 의료 AI 어시스턴트 입니다. 🩺 \n" + \
                   "현재 겪고 계시는 증상이 있다면 가감없이 말해주세요. 😃 \n" + \
                   "예상되는 질환과 인근의 병원을 알려드릴게요. "
        dataset.append(f'<s>[INST] {inputs} [/INST] {response} </s>')

dataset = Dataset.from_dict({"text": dataset})
dataset.save_to_disk("data")

print('데이터셋 info 확인')
print(dataset)

dataset.push_to_hub('Jinsuu/AHT_custom_dataset_4')