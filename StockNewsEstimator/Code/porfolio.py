import pandas as pd
import matplotlib.pyplot as plt

# 1. Load stock data and parse company and item names
stock_df = pd.read_excel(
    "/Users/imdonghyeon/Desktop/Quantlab/0-Other/stockdata.xlsx")
stock_df.rename(columns=lambda x: x.strip()
                if isinstance(x, str) else x, inplace=True)
if stock_df['Symbol Name'].astype(str).str.contains(r'\(').any():
    parsed = stock_df['Symbol Name'].astype(
        str).str.extract(r'([^()]+)\(([^)]+)\)')
    stock_df['Company'] = parsed[0].str.strip()
    stock_df['Item'] = parsed[1].str.strip()
else:
    stock_df['Company'] = stock_df['Symbol Name'].astype(str).str.strip()
    stock_df['Item'] = stock_df['Item Name'].astype(
        str).str.split('(').str[0].str.strip()

# 2. Load news data and match company names
news_df = pd.read_excel("/Users/imdonghyeon/Desktop/Quantlab/merged_news_data.xlsx",
                        usecols=['일자', '기업명', 'GPT_SCORE', '시가', '수정종가'])
news_df = news_df.dropna(subset=['기업명', 'GPT_SCORE'])
news_df = news_df[~news_df['기업명'].astype(str).str.contains(',')]
news_df = news_df[news_df['GPT_SCORE'].isin([1.0, -1.0])]
news_df['기업명'] = news_df['기업명'].astype(str).str.strip()
news_df['Company'] = news_df['기업명']

# 3. Use open and close prices from news data
news_df['Open'] = news_df['시가']
news_df['Close'] = news_df['수정종가']
news_df = news_df.dropna(subset=['Open', 'Close'])
# Calculate return: positive if long (GPT_SCORE=1), negative if short (GPT_SCORE=-1)
news_df['Return'] = (news_df['Close'] - news_df['Open']) / \
    news_df['Open'] * news_df['GPT_SCORE']

# 4. Compute cumulative return
news_df['Date'] = pd.to_datetime(news_df['일자']).dt.date
news_df = news_df.sort_values('Date')
news_df['Cumulative_Return'] = (1 + news_df['Return']).cumprod()

# Prepare results
results = news_df[['Date', 'Company', 'Open', 'Close',
                   'GPT_SCORE', 'Return', 'Cumulative_Return']].copy()
results.columns = ['Entry Date', 'Company', 'Entry Price',
                   'Exit Price', 'Signal', 'Return', 'Cumulative Return']

# 5. Save results to Excel
results.to_excel(
    "/Users/imdonghyeon/Desktop/Quantlab/portfolio_results111.xlsx", index=False)

# Plot cumulative return
plt.figure(figsize=(8, 4))
plt.plot(results['Entry Date'], results['Cumulative Return'], color='blue')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.title('Cumulative Return Over Time')
plt.tight_layout()
plt.savefig(
    "/Users/imdonghyeon/Desktop/Quantlab/portfolio_results_cumulative.png")
plt.close()

# Plot daily long/short position counts
daily_counts = news_df.groupby(
    ['Date', 'GPT_SCORE']).size().unstack(fill_value=0)
daily_counts = daily_counts.rename(columns={1.0: 'Long', -1.0: 'Short'})
plt.figure(figsize=(8, 4))
daily_counts.plot(kind='bar', stacked=True, color=['skyblue', 'orange'])
plt.xlabel('Date')
plt.ylabel('Number of Positions')
plt.title('Daily Long/Short Position Count')
plt.tight_layout()
plt.savefig(
    "/Users/imdonghyeon/Desktop/Quantlab/portfolio_results_position_count.png")
plt.close()
