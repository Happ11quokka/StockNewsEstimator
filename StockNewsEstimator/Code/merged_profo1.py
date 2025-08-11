import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 한글 폰트 설정 (macOS)
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# 파일 로드
df = pd.read_excel("/Users/imdonghyeon/Desktop/Quantlab/merged_profo1.xlsx")

# 날짜만 남기기
for col in ['Date', 'Entry Date', 'Exit Date']:
    df[col] = pd.to_datetime(df[col]).dt.date

# ✅ LONG/SHORT 액션 스왑
df['Action'] = df['Action'].apply(lambda x: 'SHORT' if x == 'LONG' else 'LONG')

# ✅ 로그 수익률 계산
df['Return'] = df.apply(lambda row:
                        np.log(row['Exit'] / row['Entry']) if row['Action'] == 'LONG'
                        else np.log(row['Entry'] / row['Exit']), axis=1)

# 날짜 기준 그룹화 및 피벗
daily = df.groupby(['Date', 'Action']).agg({'Return': 'mean', 'Company': 'count'}).rename(
    columns={'Company': 'Count'}).reset_index()
pivot = daily.pivot(index='Date', columns='Action',
                    values=['Return', 'Count']).fillna(0)
pivot.columns = ['Return_LONG', 'Return_SHORT', 'Count_LONG', 'Count_SHORT']

# 비중 및 로그 포트폴리오 수익률 계산
pivot['Total'] = pivot['Count_LONG'] + pivot['Count_SHORT']
pivot['Weight_LONG'] = pivot['Count_LONG'] / pivot['Total']
pivot['Weight_SHORT'] = pivot['Count_SHORT'] / pivot['Total']
pivot['Daily_Portfolio_Return'] = (
    pivot['Return_LONG'] * pivot['Weight_LONG'] +
    pivot['Return_SHORT'] * pivot['Weight_SHORT']
)

# ✅ 로그 누적 수익률 (log → exp 누적)
pivot['Cumulative_Return'] = np.exp(
    pivot['Daily_Portfolio_Return'].cumsum()) - 1

# 주별 수익률
pivot.index = pd.to_datetime(pivot.index)
weekly = pivot.resample('W-MON').agg({
    'Return_LONG': 'mean',
    'Return_SHORT': 'mean',
    'Daily_Portfolio_Return': 'mean'
}).reset_index()

# merge용 날짜 타입 맞추기
df['Date'] = pd.to_datetime(df['Date'])
pivot_reset = pivot.reset_index()
pivot_reset['Date'] = pd.to_datetime(pivot_reset['Date'])

df_merged = df.merge(
    pivot_reset[['Date', 'Return_LONG', 'Return_SHORT', 'Weight_LONG',
                 'Weight_SHORT', 'Daily_Portfolio_Return', 'Cumulative_Return']],
    on='Date', how='left'
)

# 엑셀 저장
output_excel = "/Users/imdonghyeon/Desktop/Quantlab/포트폴리오_수익률_분석_LOG.xlsx"
df_merged.to_excel(output_excel, index=False)

# -------------------- 시각화 -------------------- #

# 누적 수익률
plt.figure(figsize=(10, 5))
plt.plot(pivot.index, pivot['Cumulative_Return'],
         label='Cumulative Return (log-based)')
plt.title('Cumulative Return (Log Scale)')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("/Users/imdonghyeon/Desktop/Quantlab/cumulative_return_log.png")

# 주별 수익률
plt.figure(figsize=(10, 5))
plt.plot(weekly['Date'], weekly['Return_LONG'], label='Weekly Long Return')
plt.plot(weekly['Date'], weekly['Return_SHORT'], label='Weekly Short Return')
plt.plot(weekly['Date'], weekly['Daily_Portfolio_Return'],
         label='Weekly Portfolio Return', linestyle='--')
plt.title('Weekly Log Returns')
plt.xlabel('Week')
plt.ylabel('Log Return')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("/Users/imdonghyeon/Desktop/Quantlab/weekly_returns_log.png")

# 포지션별 일일 수익률
plt.figure(figsize=(10, 5))
plt.plot(pivot.index, pivot['Return_LONG'], label='Daily Long Log Return')
plt.plot(pivot.index, pivot['Return_SHORT'], label='Daily Short Log Return')
plt.title('Daily Log Return per Position Type')
plt.xlabel('Date')
plt.ylabel('Log Return')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("/Users/imdonghyeon/Desktop/Quantlab/daily_position_returns_log.png")
