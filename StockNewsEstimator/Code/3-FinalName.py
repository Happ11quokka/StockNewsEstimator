import os
import pandas as pd
import re

input_folder = '/Users/imdonghyeon/Desktop/Quantlab/final_newsdata'
output_folder = '/Users/imdonghyeon/Desktop/Quantlab/tmp'
mapping_file = '/Users/imdonghyeon/Desktop/Quantlab/detailName.txt'

os.makedirs(output_folder, exist_ok=True)

name_map = {}
with open(mapping_file, 'r', encoding='utf-8') as f:
    for line in f:
        if ' - ' in line:
            old, new = line.strip().split(' - ')
            name_map[old.strip()] = new.strip()


# 최신 상장 기업명 변경
def replace_company_names(text):
    if pd.isna(text):
        return text
    for old_name, new_name in name_map.items():
        pattern = re.compile(rf'\b{re.escape(old_name)}(?=\(\-?\d+\))')
        text = pattern.sub(new_name, text)
    return text


for filename in os.listdir(input_folder):
    if filename.endswith('.xlsx'):
        file_path = os.path.join(input_folder, filename)

        try:
            df = pd.read_excel(file_path, engine='openpyxl')

            if 'GPT_기업별감성' in df.columns:
                df['GPT_기업별감성'] = df['GPT_기업별감성'].apply(replace_company_names)

            output_path = os.path.join(output_folder, filename)
            df.to_excel(output_path, index=False, engine='openpyxl')

            print(f'처리 완료: {filename}')

        except Exception as e:
            print(f'처리 실패: {filename} — {e}')

print("🎉 모든 파일 처리 완료.")
