import re
import requests
import json
import math as m
import pandas as pd
from bs4 import BeautifulSoup

TITLE = []
SYMPTOMS = []
RELATED_DISEASES = []
DEPARTMENTS = []
JSON = []

def get_disease_info(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch page {url}")
        return
    soup = BeautifulSoup(response.content, 'html.parser')
    diseases = soup.find_all('li')
    for disease in diseases:
        try:
            # 질병명 추출
            title = disease.find('strong', class_='contTitle').text.strip()
            title = re.sub(r'\([^ㄱ-힇]*\)', '', title)

            # 증상 추출
            try:
                symptoms_list = disease.find('dt', text='증상').find_next_sibling('dd').find_all('a')
                symptoms = ', '.join(item.text.strip() for item in symptoms_list)
            except AttributeError:
                symptoms = ''
            # 관련질환 추출
            try:
                related_diseases_list = disease.find('dt', text='관련질환').find_next_sibling('dd').find_all('a')
                related_diseases = ', '.join(item.text.strip() for item in related_diseases_list)
            except AttributeError:
                related_diseases = ''
            # 진료과 추출
            try:
                departments_list = disease.find('dt', text='진료과').find_next_sibling('dd').find_all('a')
                departments = ', '.join(item.text.strip() for item in departments_list)
            except AttributeError:
                departments = ''
        except AttributeError:
            continue

        TITLE.append(title)
        SYMPTOMS.append(symptoms)
        RELATED_DISEASES.append(related_diseases)
        DEPARTMENTS.append(departments)
        JSON.append({'질환명':title, '증상':symptoms, '관련질환':related_diseases, '진료과목':departments})

base_url = "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseList.do?searchKeyword=&pageIndex="
response = requests.get(base_url+'1')
pages = m.ceil(int(re.findall(r'총 <span class="txtGreenT">(.+?)건</span>입니다.', response.text, re.DOTALL)[0].replace(',','')) / 20)

for p in range(pages):
    url = base_url + str(p+1)
    get_disease_info(url)

df = pd.DataFrame({'질병명':TITLE, '증상':SYMPTOMS, '관련질환':RELATED_DISEASES, '진료과':DEPARTMENTS})
df.to_csv('data/output.csv', encoding='utf-8-sig',index=False)

dataset = []
for disease in JSON:
    if disease['증상'] != '' and disease['관련질환'] != '' and disease['진료과목'] != '':
        instruction = disease['증상'] + ' 등의 증상이 있어.'
        output = disease['질환명'] + '이 의심되네요. ' + disease['진료과목'] + '의 전문의에게 상담을 받아보시는 것을 추천합니다. 이와 관련한 질환으로는 ' + \
                 disease['관련질환'] + ' 등이 있습니다. '
        dataset.append({'instruction': instruction, 'input': '', 'output': output})
with open('data/only_diseases.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

with open('data/output.json','w', encoding='utf-8') as f:
    json.dump(JSON, f, indent=4, ensure_ascii=False)