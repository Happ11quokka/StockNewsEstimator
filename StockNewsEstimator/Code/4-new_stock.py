import os
import re
import pandas as pd
import datetime

input_dir = '/Users/imdonghyeon/Desktop/Quantlab/PRA_DAY'
out_dir = '/Users/imdonghyeon/Desktop/Quantlab/news_stock'
stock_path = '/Users/imdonghyeon/Desktop/Quantlab/stockdata.xlsx'
os.makedirs(out_dir, exist_ok=True)


# 0) 주가 데이터 읽기 및 전처리
def col_to_str(c):
    if isinstance(c, (pd.Timestamp, datetime.datetime, datetime.date)):
        return c.strftime('%Y-%m-%d')
    else:
        return str(c).strip()


stock_df = pd.read_excel(stock_path, dtype=str)
stock_df.columns = [col_to_str(c) for c in stock_df.columns]

date_cols = [c for c in stock_df.columns if isinstance(
    c, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', c)]
id_vars = ['Symbol', 'Symbol Name', 'Item Name']

melted = stock_df.melt(
    id_vars=id_vars,
    value_vars=date_cols,
    var_name='date',
    value_name='price'
)
melted['price'] = melted['price'].str.replace(',', '').astype(float)
melted['date'] = pd.to_datetime(melted['date'], format='%Y-%m-%d').dt.date

open_df = melted[melted['Item Name'] == '시가(원)'].rename(
    columns={'price': '시가'})[['Symbol Name', 'date', '시가']]
adj_df = melted[melted['Item Name'] == '수정주가 (현금배당반영)(원)'].rename(
    columns={'price': '수정종가'})[['Symbol Name', 'date', '수정종가']]

# 1) 뉴스 폴더 내 모든 파일 처리
for filename in os.listdir(input_dir):
    if not filename.endswith('.xlsx'):
        continue

    input_file = os.path.join(input_dir, filename)
    out_file = os.path.join(out_dir, os.path.splitext(
        filename)[0] + '_with_prices.xlsx')

    try:
        # 뉴스 데이터 불러오기
        news_df = pd.read_excel(input_file, dtype=str)

        # 뉴스 전처리
        news_df['일자_clean'] = news_df['일자'].str.extract(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')[0]
        news_df['date'] = pd.to_datetime(
            news_df['일자_clean'], format='%Y-%m-%d %H:%M:%S', errors='coerce').dt.date
        news_df['company'] = news_df['GPT_기업별감성'].str.extract(
            r'([^()]+)')[0].str.strip()
        news_df['GPT_SCORE'] = pd.to_numeric(news_df['GPT_기업별감성'].str.extract(
            r'\(([-+]?[0-9]*\.?[0-9]+)\)')[0], errors='coerce')

        # 주가 병합
        merged = pd.merge(news_df, open_df, left_on=['company', 'date'], right_on=[
                          'Symbol Name', 'date'], how='left')
        merged = pd.merge(merged, adj_df, left_on=['company', 'date'], right_on=[
                          'Symbol Name', 'date'], how='left', suffixes=('', '_drop'))
        merged.drop(columns=['Symbol Name_drop'], inplace=True)

        # 저장
        cleaned = merged.drop(
            columns=['일자_clean', 'company', 'Symbol Name', 'date'])
        cleaned.to_excel(out_file, index=False)
        print(f"처리 완료: {filename} → {os.path.basename(out_file)}")

    except Exception as e:
        print(f"오류 발생: {filename} - {e}")
