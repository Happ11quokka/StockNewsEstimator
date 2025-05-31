import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import timedelta
from matplotlib.ticker import PercentFormatter

# 1. Load and preprocess the data


def load_data(file_path):
    df = pd.read_excel(file_path)
    date_cols = ['current_date', 'entry_date', 'exit_date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
    df['sentiment'] = np.where(df['GPT_SCORE'] > 0, 'positive',
                               np.where(df['GPT_SCORE'] < 0, 'negative', 'neutral'))
    return df

# 2. Calculate returns based on rules


def calculate_returns(df):
    df['long_return'] = np.nan
    df['short_return'] = np.nan

    for idx, row in df.iterrows():
        tag1 = row['tag1']
        tag2 = row['tag2'] if pd.notna(row['tag2']) else ""
        sentiment = row['sentiment']
        if sentiment == 'neutral':
            continue

        prev_open = row.iloc[12] if pd.notna(row.iloc[12]) else np.nan
        prev_close = row.iloc[13] if pd.notna(row.iloc[13]) else np.nan
        curr_open = row.iloc[14] if pd.notna(row.iloc[14]) else np.nan
        curr_close = row.iloc[15] if pd.notna(row.iloc[15]) else np.nan

        if all(np.isnan([prev_open, prev_close, curr_open, curr_close])):
            continue

        entry_price, exit_price = np.nan, np.nan

        if tag1 == 'DAY-OFF':
            entry_price, exit_price = curr_open, curr_close
        elif tag1 == 'DAY-IN':
            if tag2 == 'PRE':
                entry_price, exit_price = curr_open, curr_close
            elif tag2 == 'IN':
                entry_price, exit_price = curr_close, prev_close
            elif tag2 == 'AFTER':
                entry_price, exit_price = prev_open, prev_close

        if pd.notna(entry_price) and pd.notna(exit_price) and entry_price != 0:
            if sentiment == 'positive':
                df.at[idx, 'long_return'] = (exit_price / entry_price) - 1
            else:
                df.at[idx, 'short_return'] = 1 - (exit_price / entry_price)
    return df

# 3. Implement portfolio strategy


def implement_strategy(df):
    start_date = df['current_date'].min()
    end_date = df['exit_date'].max()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    portfolio = pd.DataFrame(index=date_range)
    portfolio['long_positions'] = 0
    portfolio['short_positions'] = 0
    portfolio['long_return'] = 0.0
    portfolio['short_return'] = 0.0

    for _, row in df.iterrows():
        if pd.notna(row['long_return']):
            exit_date = pd.to_datetime(row['exit_date'])
            portfolio.loc[exit_date, 'long_positions'] += 1
            portfolio.loc[exit_date, 'long_return'] += row['long_return']
        if pd.notna(row['short_return']):
            exit_date = pd.to_datetime(row['exit_date'])
            portfolio.loc[exit_date, 'short_positions'] += 1
            portfolio.loc[exit_date, 'short_return'] += row['short_return']

    portfolio['long_return'] = np.where(
        portfolio['long_positions'] > 0,
        portfolio['long_return'] / portfolio['long_positions'], 0)
    portfolio['short_return'] = np.where(
        portfolio['short_positions'] > 0,
        portfolio['short_return'] / portfolio['short_positions'], 0)

    both_positions = portfolio['long_positions'] + portfolio['short_positions']
    long_weight = np.where(
        both_positions > 0, portfolio['long_positions'] / both_positions, 0)
    short_weight = np.where(
        both_positions > 0, portfolio['short_positions'] / both_positions, 0)

    portfolio['long_short_return'] = (portfolio['long_return'] * long_weight +
                                      portfolio['short_return'] * short_weight)

    portfolio['cum_long_return'] = (1 + portfolio['long_return']).cumprod() - 1
    portfolio['cum_short_return'] = (
        1 + portfolio['short_return']).cumprod() - 1
    portfolio['cum_long_short_return'] = (
        1 + portfolio['long_short_return']).cumprod() - 1

    return portfolio.fillna(0)

# 4. Summary statistics


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


def get_panelA_summary(df):
    panel_df = df[['daily_return', 'headline_length',
                   'GPT_SCORE']].dropna().copy()
    panel_df['daily_return'] = panel_df['daily_return'] * 100
    summary_stats = {
        'Mean': panel_df.mean(),
        'SD': panel_df.std(),
        'Min': panel_df.min(),
        'P25': panel_df.quantile(0.25),
        'Median': panel_df.median(),
        'P75': panel_df.quantile(0.75),
        'Max': panel_df.max(),
        'N': panel_df.count()
    }
    panel_summary = pd.DataFrame(summary_stats).T.round(3)
    panel_summary.index.name = 'Metric'
    panel_summary.columns = [
        'Daily Return(%)', 'Headline Length', 'GPT4.1Nano Score']
    return panel_summary

# 5. Plot cumulative returns


def plot_cumulative_returns(portfolio):
    plt.figure(figsize=(14, 8))
    plt.plot(portfolio.index, portfolio['cum_long_return']
             * 100, 'b-', label='Long Only', linewidth=2)
    plt.plot(portfolio.index, portfolio['cum_short_return']
             * 100, 'r-', label='Short Only', linewidth=2)
    plt.plot(portfolio.index, portfolio['cum_long_short_return']
             * 100, 'g-', label='Long+Short', linewidth=2.5)
    plt.title('Cumulative Returns of Long-Short Portfolio Strategies', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Return (%)')
    plt.gca().yaxis.set_major_formatter(PercentFormatter())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('cumulative_returns.png', dpi=300)
    plt.show()

# 6. Plot monthly position counts


def plot_monthly_positions(df):
    df['year_month'] = df['current_date'].dt.strftime('%Y-%m')
    monthly_counts = df.groupby(
        ['year_month', 'sentiment']).size().unstack().fillna(0)
    monthly_counts = monthly_counts.rename(
        columns={'positive': 'Long', 'negative': 'Short'}).fillna(0)
    for col in ['Long', 'Short']:
        if col not in monthly_counts.columns:
            monthly_counts[col] = 0
    monthly_counts[['Long', 'Short']].plot(kind='bar', stacked=True, figsize=(14, 8),
                                           color=['blue', 'red'], alpha=0.7)
    plt.title('Monthly Position Counts (Long vs Short)')
    plt.xlabel('Month')
    plt.ylabel('Number of Positions')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('monthly_positions.png', dpi=300)
    plt.show()

# 7. Main runner


def main():
    file_path = "/Users/imdonghyeon/Desktop/Quantlab/final_수정/combined_result_deduplicated.xlsx"
    print("Loading and preprocessing data...")
    news_data = load_data(file_path)
    print("Calculating returns...")
    news_data = calculate_returns(news_data)
    print("Building portfolio...")
    portfolio = implement_strategy(news_data)
    print("Plotting results...")
    plot_cumulative_returns(portfolio)
    plot_monthly_positions(news_data)

    portfolio.to_csv("long_short_portfolio_results.csv")
    news_data.to_csv("processed_news_data.csv")

    print("\nSummary Statistics:")
    print(f"Total news: {len(news_data)}")
    print(f"Long positions: {news_data['long_return'].notna().sum()}")
    print(f"Short positions: {news_data['short_return'].notna().sum()}")

    actual_days = len(
        portfolio[portfolio['long_positions'] + portfolio['short_positions'] > 0])

    def annualized(x): return ((1 + x.iloc[-1]) ** (365 / actual_days)) - 1

    print("\nAnnualized Returns (based on actual trading days):")
    print(f"Long-only: {annualized(portfolio['cum_long_return']):.2%}")
    print(f"Short-only: {annualized(portfolio['cum_short_return']):.2%}")
    print(
        f"Long-Short Combined: {annualized(portfolio['cum_long_short_return']):.2%}")

    summary_df = pd.DataFrame({
        'Long Cumulative Return': get_summary(portfolio['cum_long_return']),
        'Short Cumulative Return': get_summary(portfolio['cum_short_return']),
        'Long+Short Cumulative Return': get_summary(portfolio['cum_long_short_return'])
    }).round(3)

    summary_df.to_csv("cumulative_return_summary.csv")
    print("\nSummary statistics saved to 'cumulative_return_summary.csv'")

    # Correlation matrix & Panel A Summary
    df = news_data.copy()
    df['headline_length'] = df['제목'].astype(str).str.len()
    portfolio_returns = portfolio[['long_short_return']].copy()
    portfolio_returns = portfolio_returns.rename(
        columns={'long_short_return': 'daily_return'})
    portfolio_returns.index.name = 'current_date'
    df['current_date'] = pd.to_datetime(df['current_date'])
    df = df.merge(portfolio_returns, left_on='current_date',
                  right_index=True, how='left')
    df_clean = df[['daily_return', 'headline_length', 'GPT_SCORE']].dropna()

    correlation_matrix = df_clean.corr()
    print("\n📊 변수 간 상관관계 (피어슨):")
    print(correlation_matrix.round(3))

    # Heatmap 저장
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('Correlation Matrix (Pearson)')
    plt.tight_layout()
    plt.savefig("correlation_matrix_heatmap.png", dpi=300)
    plt.show()

    # Panel A Summary 저장
    panel_summary = get_panelA_summary(df_clean)
    panel_summary.to_csv("panelA_summary_statistics.csv")
    print("\nPanel A summary statistics saved to 'panelA_summary_statistics.csv'")
    print(panel_summary)

    return portfolio, news_data


if __name__ == "__main__":
    portfolio_results, processed_data = main()
