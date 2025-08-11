import os
from datetime import datetime
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from tqdm import tqdm

# 설정
news_folder = '/Users/imdonghyeon/Desktop/Quantlab/news_tags'
output_folder = '/Users/imdonghyeon/Desktop/Quantlab/portfolio_results'
stock_path = '/Users/imdonghyeon/Desktop/Quantlab/stockdata.xlsx'
os.makedirs(output_folder, exist_ok=True)


# ── 0. 주가 데이터 로드 & 전처리 (Wide → Long) ─────────────────────────
stock_df = pd.read_excel(stock_path, dtype=str)
stock_df.columns = [c.strip() if isinstance(
    c, str) else c for c in stock_df.columns]
# Symbol Name 컬럼도 strip
stock_df['Symbol Name'] = stock_df['Symbol Name'].str.strip()

date_cols = [c for c in stock_df.columns if isinstance(
    c, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', c)]
stock_long = stock_df.melt(
    id_vars=['Symbol Name', 'Item Name'],
    value_vars=date_cols,
    var_name='Date',
    value_name='Price'
)
stock_long['Date'] = pd.to_datetime(stock_long['Date'])
stock_long['Price'] = stock_long['Price'].str.replace(',', '').astype(float)

open_df = stock_long.query("`Item Name`=='시가(원)'")\
    .rename(columns={'Price': 'Open'}).drop(columns='Item Name')
close_df = stock_long.query("`Item Name`=='수정주가 (현금배당반영)(원)'")\
    .rename(columns={'Price': 'Close'}).drop(columns='Item Name')
price_df = pd.merge(open_df, close_df, on=['Symbol Name', 'Date'], how='inner')

# ── 1. 뉴스 로드 & 전처리 ───────────────────────────────────────────
news_df = pd.read_excel(news_path, dtype=str)
news_df.columns = [c.strip() for c in news_df.columns]

# 날짜, 점수, 기업명/심볼 처리
news_df['일자'] = pd.to_datetime(news_df['일자'])
news_df['거래일'] = news_df['일자'].dt.date
news_df['GPT_SCORE'] = pd.to_numeric(news_df['GPT_SCORE'], errors='coerce')

# 어떤 컬럼을 매칭에 쓸지 결정
# 우선 news_df에 'Symbol Name' 있으면, 그걸 쓰고, 없으면 '기업명' 사용
if 'Symbol Name' in news_df.columns:
    news_df['MatchName'] = news_df['Symbol Name'].str.strip()
else:
    news_df['MatchName'] = news_df['기업명'].str.strip()

# ── 2. 수익률 계산 함수 ──────────────────────────────────────────────


def calculate_positions_with_tags(df, price_df):
    days = sorted(price_df['Date'].dt.date.unique())
    next_map = {d: days[i+1] if i+1 <
                len(days) else None for i, d in enumerate(days)}
    records, skipped, processed = [], 0, 0

    for _, row in df.iterrows():
        d = row['거래일']
        sym = row['MatchName']
        score = row['GPT_SCORE']
        tag1, tag2 = row.get('tag1', ''), row.get('tag2', '')

        # 필터
        if pd.isna(score) or score == 0:
            skipped += 1
            continue

        # 종목 매칭
        if sym not in price_df['Symbol Name'].values:
            skipped += 1
            continue

        action = 'LONG' if score > 0 else 'SHORT'
        nxt = next_map.get(d)
        if nxt is None:
            skipped += 1
            continue

        # 진입·청산 시점 결정
        if tag1 == 'DAY-OFF':
            Ein, Eout, ti, to = nxt, nxt, 'Open', 'Close'
        elif tag1 == 'DAY-IN' and tag2 == 'PRE':
            Ein, Eout, ti, to = d, d, 'Open', 'Close'
        elif tag1 == 'DAY-IN' and tag2 == 'IN':
            Ein, Eout, ti, to = d, nxt, 'Close', 'Close'
        elif tag1 == 'DAY-IN' and tag2 == 'AFTER':
            Ein, Eout, ti, to = nxt, nxt, 'Open', 'Close'
        else:
            skipped += 1
            continue

        er = price_df[(price_df['Symbol Name'] == sym)
                      & (price_df['Date'] == Ein)]
        xr = price_df[(price_df['Symbol Name'] == sym)
                      & (price_df['Date'] == Eout)]
        if er.empty or xr.empty:
            skipped += 1
            continue

        entry, exit_ = er[ti].iat[0], xr[to].iat[0]
        if entry == 0 or pd.isna(entry) or pd.isna(exit_):
            skipped += 1
            continue

        ret = (exit_-entry)/entry if action == 'LONG' else (entry-exit_)/entry
        records.append([d, sym, action, Ein, Eout, entry, exit_, ret])
        processed += 1

    if not records:
        return pd.DataFrame(), processed, skipped

    out = pd.DataFrame(records, columns=[
        'Date', 'Company', 'Action', 'Entry Date', 'Exit Date', 'Entry', 'Exit', 'Return'
    ]).sort_values('Date')
    daily = out.groupby('Date')['Return'].mean()
    out['Cumulative Return'] = out['Date'].map((1+daily).cumprod()-1)
    return out, processed, skipped


# ── 3. 단일 뉴스 처리 ───────────────────────────────────────────
result_df, proc, skip = calculate_positions_with_tags(news_df, price_df)
print(f"✅ 처리: {proc}건, 스킵: {skip}건")

if result_df.empty:
    print("⚠️ 유효 포지션 없음 – 종료")
    exit()

# ── 4. 엑셀 저장 ───────────────────────────────────────────────
base = os.path.basename(news_path)[11:17]
out_xlsx = os.path.join(output_folder, f"portfolio_result_{base}.xlsx")
result_df.to_excel(out_xlsx, index=False)
print("✅ 엑셀 저장:", out_xlsx)

# ── 5. 시각화 ───────────────────────────────────────────────
result_df['Date'] = pd.to_datetime(result_df['Date'])
long_daily = result_df[result_df['Action'] == 'LONG'].groupby('Date')[
    'Return'].mean()
short_daily = result_df[result_df['Action'] == 'SHORT'].groupby('Date')[
    'Return'].mean()
total_daily = result_df.groupby('Date')['Return'].mean()

long_cum = (1+long_daily).cumprod()-1
short_cum = (1+short_daily).cumprod()-1
total_cum = (1+total_daily).cumprod()-1

plt.figure(figsize=(10, 5))
plt.plot(long_cum, '--', label='LONG')
plt.plot(short_cum, ':', label='SHORT')
plt.plot(total_cum, '-', label='TOTAL')
plt.title('Cumulative Returns')
plt.legend()
plt.grid(True)
plt.tight_layout()
png1 = os.path.join(output_folder, f"cum_returns_{base}.png")
plt.savefig(png1)
plt.close()
print("✅ 그래프 저장:", png1)

pos_cnt = result_df.groupby(['Date', 'Action']).size().unstack(fill_value=0)
pos_cnt.index = pd.to_datetime(pos_cnt.index)
ax = pos_cnt.plot(kind='bar', stacked=True, figsize=(12, 4), colormap='Set2')
ax.set_ylabel('Count')
plt.tight_layout()
png2 = os.path.join(output_folder, f"daily_count_{base}.png")
plt.savefig(png2)
plt.close()
print("✅ 카운트 그래프 저장:", png2)

# ── 6. 통계 요약 추가 저장 ─────────────────────────────────────────────


def get_summary(series):
    return pd.Series({
        'Mean': series.mean() * 100,
        'SD': series.std() * 100,
        'Min': series.min() * 100,
        'P25': series.quantile(0.25) * 100,
        'Median': series.median() * 100,
        'P75': series.quantile(0.75) * 100,
        'Max': series.max() * 100,
        'N': series.count()
    })


summary_df = pd.DataFrame({
    'Long Cumulative Return': get_summary(long_cum),
    'Short Cumulative Return': get_summary(short_cum),
    'Long+Short Cumulative Return': get_summary(total_cum)
}).round(3)

summary_path = os.path.join(output_folder, f"summary_stats_{base}.csv")
summary_df.to_csv(summary_path)
print("✅ 통계 요약 저장:", summary_path)
