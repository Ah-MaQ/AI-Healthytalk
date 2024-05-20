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
CODE = []

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

            # ID 추출
            link_tag = disease.find('a', href=True)
            href = link_tag['href']
            match = re.search(r'contentId=(\d+)', href)
            if match:
                code = int(match.group(1))
            else:
                code = 0

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
        CODE.append(code)

base_url = "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseList.do?searchKeyword=&pageIndex="
response = requests.get(base_url+'1')
pages = m.ceil(int(re.findall(r'총 <span class="txtGreenT">(.+?)건</span>입니다.', response.text, re.DOTALL)[0].replace(',','')) / 20)

for p in range(pages):
    url = base_url + str(p+1)
    get_disease_info(url)

df = pd.DataFrame({'질환명':TITLE, '증상':SYMPTOMS, '관련질환':RELATED_DISEASES, '진료과목':DEPARTMENTS, '코드':CODE})
df = df[(df['증상'] != '') & (df['증상'] != '무증상') & (df['진료과목'] != '')]

for index, row in df.iterrows():
    if '무증상' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('무증상, ', '').replace(', 무증상', '')
    if '손,발,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('손,발,', '손 발 ')
    if '손 발,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('손 발,', '손 발 ')
    if '손, 발,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('손, 발,', '손 발 ')
    if '손,발' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('손,발', '손 발')
    if '손, 발' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('손, 발', '손 발')
    if '4,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('4,', '4 ')
    if '눈, 코, 입' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('눈, 코, 입', '눈 코 입')
    if '눈,뺨' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('눈,뺨', '눈이나 뺨')
    if '볼,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('볼,', '볼과')
    if '원형,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('원형,', '원형 및')
    if '남:' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('남:', '남아')
    if '여:' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('여:', '여아')
    if '뼈,근육' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('뼈,근육', '뼈 또는 근육')
    if '고환,부' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('고환,부', '고환 또는 부')
    if '입술,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('입술,','입술 및')
    if '읽기,' in row['증상']:
        df.at[index, '증상'] = row['증상'].replace('읽기,','읽기 ')

df.to_csv('data/output.csv', encoding='utf-8',index=False)