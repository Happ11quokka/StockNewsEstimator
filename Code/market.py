import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False


def calculate_size_based_returns(df):
    """
    사이즈별 동일가중 방식 누적 수익률 계산

    Parameters:
    df: 뉴스 기반 수익률 데이터프레임

    Returns:
    results: 사이즈별 누적 수익률 데이터프레임
    """

    # long_return과 short_return이 있는지 확인하고 long_short_return 계산
    if 'long_return' in df.columns and 'short_return' in df.columns:
        df['long_short_return'] = df['long_return'] + df['short_return']
    elif 'long_short_return' not in df.columns:
        raise ValueError(
            "long_return과 short_return 또는 long_short_return 컬럼이 필요합니다.")

    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 규모구분별로 그룹화하고 일별 평균 수익률 계산
    daily_returns = df.groupby(['current_date', '규모구분'])[
        'long_short_return'].mean().reset_index()

    # 피벗 테이블로 변환 (날짜별, 사이즈별)
    pivot_returns = daily_returns.pivot(
        index='current_date', columns='규모구분', values='long_short_return')

    # 결측치를 0으로 채우기 (거래가 없는 날)
    pivot_returns = pivot_returns.fillna(0)

    # 누적 수익률 계산 (1 + return의 누적곱)
    cumulative_returns = (1 + pivot_returns).cumprod()

    # 전체 포트폴리오 수익률 (모든 사이즈 평균)
    pivot_returns['전체'] = pivot_returns.mean(axis=1)
    cumulative_returns['전체'] = (1 + pivot_returns['전체']).cumprod()

    return cumulative_returns, pivot_returns


def analyze_size_distribution(df):
    """
    사이즈별 종목 분포 분석
    """
    # 규모구분별 종목 수
    size_counts = df['규모구분'].value_counts()

    # 규모구분별 일별 거래 종목 수
    daily_counts = df.groupby(
        ['current_date', '규모구분']).size().unstack(fill_value=0)

    print("사이즈별 전체 거래 건수:")
    print(size_counts)
    print("\n사이즈별 일평균 거래 종목 수:")
    print(daily_counts.mean())

    return size_counts, daily_counts


def plot_cumulative_returns(cumulative_returns):
    """
    사이즈별 누적 수익률 시각화
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # 각 사이즈별로 플롯
    for column in cumulative_returns.columns:
        ax.plot(cumulative_returns.index, cumulative_returns[column],
                label=column, linewidth=2)

    ax.set_title('Size-based Equal-weighted Cumulative Returns', fontsize=16)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # y축을 백분율로 표시
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y-1)))

    plt.tight_layout()
    return fig


def calculate_performance_metrics(returns_df):
    """
    성과 지표 계산
    """
    metrics = {}

    for column in returns_df.columns:
        returns = returns_df[column]

        # 연율화 수익률 (252 거래일 기준)
        annual_return = (1 + returns.mean()) ** 252 - 1

        # 연율화 변동성
        annual_vol = returns.std() * np.sqrt(252)

        # 샤프 비율 (무위험 수익률 0 가정)
        sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0

        # 최대 낙폭
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        metrics[column] = {
            '연율화 수익률': f'{annual_return:.2%}',
            '연율화 변동성': f'{annual_vol:.2%}',
            '샤프 비율': f'{sharpe_ratio:.2f}',
            '최대 낙폭': f'{max_drawdown:.2%}'
        }

    return pd.DataFrame(metrics).T


def analyze_period_returns(cumulative_returns, daily_returns):
    """
    기간별 수익률 분석
    """
    results = {}

    for column in cumulative_returns.columns:
        # 전체 기간 수익률
        total_return = cumulative_returns[column].iloc[-1] - 1

        # 월별 수익률
        monthly_returns = daily_returns[column].resample(
            'M').apply(lambda x: (1 + x).prod() - 1)

        # 분기별 수익률
        quarterly_returns = daily_returns[column].resample(
            'Q').apply(lambda x: (1 + x).prod() - 1)

        results[column] = {
            '전체 기간 수익률': f'{total_return:.2%}',
            '월평균 수익률': f'{monthly_returns.mean():.2%}',
            '분기평균 수익률': f'{quarterly_returns.mean():.2%}'
        }

    return pd.DataFrame(results).T

# ──────────────────────────────────────────────────────────
# NEW 1. Long / Short / Long+Short 누적 수익률 계산 함수
# ──────────────────────────────────────────────────────────


def calculate_size_based_cumulative(df):
    """
    사이즈별 Long · Short · Long+Short 누적 수익률을 모두 계산.
    Returns
    -------
    dict of DataFrame
        {'long': cum_long_df,
         'short': cum_short_df,
         'long_short': cum_total_df}
        각 DF는 index=날짜, columns=규모구분
    """
    df['current_date'] = pd.to_datetime(df['current_date'])

    def _pivot_daily(col):
        daily = (
            df.groupby(['current_date', '규모구분'])[col]
            .mean()                      # 일별 평균
            .reset_index()
            .pivot(index='current_date', columns='규모구분', values=col)
            .fillna(0)
        )
        return (1 + daily).cumprod()       # 누적수익률

    cum_long = _pivot_daily('long_return')
    cum_short = _pivot_daily('short_return')
    cum_total = _pivot_daily('long_short_return')

    return {'long': cum_long, 'short': cum_short, 'long_short': cum_total}


# ──────────────────────────────────────────────────────────
# NEW 2. 사이즈별 Long/Short/롱숏 누적 그래프 그리기
# ──────────────────────────────────────────────────────────
def plot_size_long_short(cum_dict):
    """
    cum_dict : calculate_size_based_cumulative()의 반환값
    """
    from matplotlib.ticker import FuncFormatter

    sizes = cum_dict['long'].columns.tolist()   # ['대형주', '중형주', '소형주', ...]
    for size in sizes:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(cum_dict['long'].index,  cum_dict['long']
                [size],  label='Long',  linewidth=2)
        ax.plot(cum_dict['short'].index, cum_dict['short']
                [size], label='Short', linewidth=2)
        ax.plot(cum_dict['long_short'].index,
                cum_dict['long_short'][size], label='Long+Short', linewidth=2, linestyle='--')

        ax.set_title(f'{size} 누적 수익률 (Long / Short / Long+Short)', fontsize=15)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return', fontsize=12)
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda y, _: f'{(y-1)*100:.0f}%'))
        ax.grid(alpha=0.3)
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()
# ──────────────────────────────────────────────────────────


def plot_size_long_short(cum_dict, save_dir='figures'):
    """
    사이즈별 Long / Short / Long+Short 누적 수익률 시각화 및 저장 (색상 지정 포함)

    Parameters
    ----------
    cum_dict : dict
        {'long': ..., 'short': ..., 'long_short': ...}
    save_dir : str
        저장할 폴더 경로 (기본: 'figures')
    """
    import os
    from matplotlib.ticker import FuncFormatter

    os.makedirs(save_dir, exist_ok=True)  # 저장 폴더 생성

    sizes = cum_dict['long'].columns.tolist()

    for size in sizes:
        fig, ax = plt.subplots(figsize=(12, 6))

        # 색상 지정: blue, red, green
        ax.plot(cum_dict['long'].index,
                cum_dict['long'][size],
                label='Long',
                linewidth=2,
                color='blue')

        ax.plot(cum_dict['short'].index,
                cum_dict['short'][size],
                label='Short',
                linewidth=2,
                color='red')

        ax.plot(cum_dict['long_short'].index,
                cum_dict['long_short'][size],
                label='Long+Short',
                linewidth=2.5,
                linestyle='--',
                color='green')

        ax.set_title(f'{size} 누적 수익률 (Long / Short / Long+Short)', fontsize=15)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return', fontsize=12)
        ax.yaxis.set_major_formatter(FuncFormatter(
            lambda y, _: f'{(y - 1) * 100:.0f}%'))
        ax.grid(alpha=0.3)
        ax.legend(loc='best')
        plt.tight_layout()

        # 파일명 저장
        filename = f"{save_dir}/cumulative_{size.replace(' ', '')}.png"
        fig.savefig(filename, dpi=300)
        plt.close(fig)

    print(f"📊 색상 포함 누적 수익률 그래프 저장 완료 → '{save_dir}'")


# 사용 예시
if __name__ == "__main__":
    # 실제 사용 방법:

    # 1. 데이터 불러오기
    df = pd.read_csv(
        '/Users/imdonghyeon/Desktop/Quantlab/final_수정/news_with_group.csv')

    df['long_return'] = pd.to_numeric(
        df['long_return'], errors='coerce').fillna(0)
    df['short_return'] = pd.to_numeric(
        df['short_return'], errors='coerce').fillna(0)
    df['long_short_return'] = df['long_return'] + df['short_return']

    # 2. 데이터 기본 정보 확인
    print("데이터 shape:", df.shape)
    print("\n규모구분 분포:")
    print(df['규모구분'].value_counts())

    # 3. 사이즈별 분포 분석
    size_counts, daily_counts = analyze_size_distribution(df)

    # 4. 누적 수익률 계산
    cumulative_returns, daily_returns = calculate_size_based_returns(df)

    # 5. 결과 출력
    print("\n사이즈별 누적 수익률 (최근 10일):")
    print(cumulative_returns.tail(10))

    # 6. 성과 지표 계산
    metrics = calculate_performance_metrics(daily_returns)
    print("\n사이즈별 성과 지표:")
    print(metrics)

    # 7. 기간별 수익률 분석
    period_returns = analyze_period_returns(cumulative_returns, daily_returns)
    print("\n기간별 수익률 분석:")
    print(period_returns)

    # 8. 시각화
    fig = plot_cumulative_returns(cumulative_returns)
    plt.show()

    # 9. 결과 저장 (선택사항)
    cumulative_returns.to_csv(
        'size_based_cumulative_returns.csv', encoding='utf-8-sig')
    metrics.to_csv('size_based_performance_metrics.csv', encoding='utf-8-sig')
    daily_returns.to_csv('size_based_daily_returns.csv', encoding='utf-8-sig')

    # (1) 기존 누적 수익률 계산(롱숏 평균) ─ 변경 없음
    cumulative_returns, daily_returns = calculate_size_based_returns(df)

    # (2) NEW: 롱·숏·롱숏 누적 수익률까지 모두 계산
    cum_dict = calculate_size_based_cumulative(df)

    # (3) NEW: 사이즈별 Long / Short / Long+Short 시각화
    plot_size_long_short(cum_dict)

    # (4) 필요하면 저장
    cum_dict['long']       .to_csv(
        'cum_long_by_size.csv',       encoding='utf-8-sig')
    cum_dict['short']      .to_csv(
        'cum_short_by_size.csv',      encoding='utf-8-sig')
    cum_dict['long_short'] .to_csv(
        'cum_longshort_by_size.csv',  encoding='utf-8-sig')

    plot_size_long_short(cum_dict)  # save_dir 기본값 'figures'

    print("\n분석 완료!")
