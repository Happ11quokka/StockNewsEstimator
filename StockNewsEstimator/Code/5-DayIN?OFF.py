import os
import json
import pandas as pd

input_dir = '/Users/imdonghyeon/Desktop/Quantlab/checked_newsdata'
output_dir = '/Users/imdonghyeon/Desktop/Quantlab/DAY-IN:OFF'
os.makedirs(output_dir, exist_ok=True)

# 1) calendar.json 불러와서 off_dates 집합 생성
with open('/Users/imdonghyeon/Desktop/Quantlab/calender.json', 'r', encoding='utf-8') as f:
    cal = json.load(f)

off_dates = set()
for year_info in cal.values():
    off_dates.update(year_info.get('weekends', []))
    off_dates.update(year_info.get('holidays', []))


# 2) 날짜 라벨링 함수
def label_day(dt_str):
    # 'YYYY-MM-DD HH:MM:SS' >> 'YYYY-MM-DD'만 분리
    date_only = dt_str.split()[0]
    if date_only in off_dates:
        return f'DAY-OFF:{dt_str}'
    else:
        return f'DAY-IN:{dt_str}'


for fname in os.listdir(input_dir):
    if not fname.lower().endswith(('.xlsx', '.csv')):
        continue
    in_path = os.path.join(input_dir, fname)
    if fname.lower().endswith('.xlsx'):
        df = pd.read_excel(in_path)
    else:
        df = pd.read_csv(in_path)
    df['일자'] = df['일자'].astype(str).apply(label_day)

    base, ext = os.path.splitext(fname)
    new_name = f'{base}_labeled{ext}'
    out_path = os.path.join(output_dir, new_name)

    if ext == '.xlsx':
        df.to_excel(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)

    print(f'Processed: {fname} >> {new_name}')
