import json
import numpy as np
import pandas as pd

symptoms_dict = {}

with open('data/symptoms.txt', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    key, syms = line.split("\n")[0].split(":")
    symptoms_dict[key.strip()] = [key.strip()]
    for sym in syms.split(","):
        symptoms_dict[key.strip()].append(sym.strip())


synonyms = 6
dataset = []
df = pd.read_csv('data/output.csv')
for i in range(len(df['증상'])):
    query = df['증상'][i] + " 등의 증상이 있습니다."
    response = df['증상'][i] + ' [SYM]' + df['질환명'][i] + ' 같은 질환이 의심되네요. ' + \
               df['진료과목'][i] + '의 전문의에게 상담을 받아보시는 것을 추천합니다. '

    dataset.append(f'<s>[INST] {query} [/INST] {response} </s>')

    keys = []
    for key in df['증상'][i].split(","):
        keys.append(key.strip())
    num = len(keys)
    order = []
    for _ in range(num):
        order.append(list(np.random.choice(synonyms, synonyms, replace=False)))

    for j in range(synonyms):
        symptoms = []
        for k, key in enumerate(keys):
            symptoms.append(symptoms_dict[key][order[k][j]])
        
        query = ", ".join(symptoms)
        query += " 등의 증상이 있습니다."
        response = df['증상'][i] + ' [SYM]' + df['질환명'][i] + ' 같은 질환이 의심되네요. ' + df['진료과목'][i] + '의 전문의에게 상담을 받아보시는 것을 추천합니다. '

        dataset.append(f'<s>[INST] {query} [/INST] {response} </s>')

print(len(dataset))
with open('data/symptoms.json','w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)