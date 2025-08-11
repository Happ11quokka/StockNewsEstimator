import os
import re
import pandas as pd

input_folder = '/Users/imdonghyeon/Desktop/Quantlab/news_stock'
output_folder = '/Users/imdonghyeon/Desktop/Quantlab/news_tags'
os.makedirs(output_folder, exist_ok=True)

#  정규표현식 패턴
date_pattern = re.compile(
    r'^(DAY-[A-Z]+):'           # tag1
    r'(\d{4}-\d{2}-\d{2})[ T]'  # 날짜
    r'(\d{2}:\d{2}:\d{2})'      # 시간
    r'(?:_(PRE|IN|AFTER))?$'    # tag2
)

for filename in os.listdir(input_folder):
    if filename.endswith('.xlsx'):
        input_path = os.path.join(input_folder, filename)
        if 'PRA_exploded_with_prices' in filename:
            output_filename = filename.replace(
                'PRA_exploded_with_prices', 'with_tags')
        else:
            output_filename = 'converted_' + filename  # fallback
        output_path = os.path.join(output_folder, output_filename)

        try:
            df = pd.read_excel(input_path, dtype=str)
        except Exception as e:
            print(f"실패: {filename} → {e}")
            continue

        #  date
        df[['tag1', 'date', 'time', 'tag2']
           ] = df['일자'].str.extract(date_pattern)
        df['일자'] = df['date'] + '-' + df['time']

        # name
        df['기업명'] = df['GPT_기업별감성'].str.replace(r'\(\-?1|\(0|\(1', '', regex=True)\
            .str.replace(')', '', regex=False)\
            .str.strip()

        # 필요한 열만 선택
        columns_to_keep = [
            'tag1', '일자', 'tag2',
            '제목', '통합 분류1',
            '기업명', 'GPT_SCORE', '시가', '수정종가'
        ]
        columns_to_keep = [col for col in columns_to_keep if col in df.columns]

        df[columns_to_keep].to_excel(output_path, index=False)
        print(f"저장 완료: {output_filename}")
