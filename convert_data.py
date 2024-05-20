import os
os.environ['HF_CODE'] = "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"

from huggingface_hub import login

login(token=os.environ.get("HF_CODE"))

import json
import numpy as np
from datasets import Dataset

with open('data/symptoms.json','r',encoding='utf-8') as f:
    dataset = json.load(f)

with open('data/alpaca_data.json','r',encoding='utf-8') as f:
    data = json.load(f)

selected_list = np.random.choice(len(data), 3000, replace=False)

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

dataset.push_to_hub('Jinsuu/AHT_custom_dataset_6')