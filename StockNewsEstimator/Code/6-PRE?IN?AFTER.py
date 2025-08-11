#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import pandas as pd

input_path = '/Users/imdonghyeon/Desktop/Quantlab/DAY-IN:OFF/NewsResult_20230201-20230228_labeled.xlsx'
output_path = '/Users/imdonghyeon/Desktop/Quantlab/PRA_DAY/NewsResult_20230201-20230228_PRA_exploded.xlsx'

output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

# 1) calendar.json 불러와 off_dates 집합 생성
cal_path = '/Users/imdonghyeon/Desktop/Quantlab/calender.json'
with open(cal_path, 'r', encoding='utf-8') as f:
    cal = json.load(f)

off_dates = set()
for year_info in cal.values():
    off_dates.update(year_info.get('weekends', []))
    off_dates.update(year_info.get('holidays', []))


# 2) 라벨링 함수 정의
def label_day_time(dt_str):
    raw = re.sub(r'^(?:DAY-IN:|DAY-OFF:)', '', dt_str)
    raw = re.sub(r'_(?:PRE|IN|AFTER)$', '', raw)
    date_part, time_part = raw.split()

    if date_part in off_dates:
        return f'DAY-OFF:{raw}'

    hh, mm, ss = map(int, time_part.split(':'))
    total_sec = hh*3600 + mm*60 + ss
    if total_sec < 9*3600:
        suffix = '_PRE'
    elif total_sec <= 15*3600:
        suffix = '_IN'
    else:
        suffix = '_AFTER'

    return f'DAY-IN:{raw}{suffix}'


df = pd.read_excel(input_path, dtype=str)

# 3) 원본 datetime 정렬을 위해 파싱
raw = df['일자'].astype(str).apply(
    lambda x: re.sub(r'^(?:DAY-IN:|DAY-OFF:)', '', x)
)
raw = raw.str.replace(r'_(?:PRE|IN|AFTER)$', '', regex=True)
df['__dt_parsed__'] = pd.to_datetime(raw, format='%Y-%m-%d %H:%M:%S')
df.sort_values('__dt_parsed__', inplace=True)

# 4) 라벨링 적용
df['일자'] = raw.apply(label_day_time)

# 5) 임시 컬럼 제거
df.drop(columns=['__dt_parsed__'], inplace=True)

df.to_excel(output_path, index=False)
print(f"완료: {os.path.basename(input_path)} → {os.path.basename(output_path)}")
