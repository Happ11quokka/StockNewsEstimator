import pandas as pd
import json

df = pd.read_excel("/Users/imdonghyeon/Desktop/Quantlab/total.xlsx")

# B열 (두 번째 열)만 추출해서 고유 기업명 리스트 만들기
excel_names = set(df.iloc[:, 1].dropna().unique())

# matched_companies.json 읽기
with open("matched_companies.json", "r", encoding="utf-8") as f:
    matched_data = json.load(f)

# 모든 기업명 가져오기 (null 포함)
matched_all_names = list(matched_data.keys())

# 엑셀에서 찾을 수 없는 기업명 리스트 만들기
not_in_excel = []
for name in matched_all_names:
    found = False
    for excel_name in excel_names:
        if name in str(excel_name) or str(excel_name) in name:
            found = True
            break
    if not found:
        not_in_excel.append(name)

# 결과 출력
if not_in_excel:
    print("아래 기업명은 엑셀의 B열에서 찾을 수 없습니다:")
    for name in not_in_excel:
        print("-", name)
else:
    print("matched_companies.json의 모든 기업명이 엑셀 B열에 존재합니다!")
