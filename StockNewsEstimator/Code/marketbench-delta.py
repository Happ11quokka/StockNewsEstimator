import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy import stats

# 한글 폰트 설정 (matplotlib)
plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False


def calculate_equal_weighted_benchmark(df, category_col='Sector'):
    """
    각 카테고리별 동일가중 벤치마크 수익률 계산
    """
    benchmark_results = {}

    # 전체 벤치마크
    all_benchmark = calculate_category_benchmark(df)
    benchmark_results['전체'] = all_benchmark

    # 카테고리별 벤치마크
    categories = df[category_col].unique()
    for category in categories:
        category_df = df[df[category_col] == category].copy()
        if len(category_df) > 0:
            category_benchmark = calculate_category_benchmark(category_df)
            benchmark_results[category] = category_benchmark

    return benchmark_results


def calculate_category_benchmark(df):
    """
    특정 카테고리의 '시장 전체 평균' 동일가중 벤치마크 수익률 계산
    (long/short 포지션 유무에 관계없이 모든 종목 포함)
    """
    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 각 날짜별로 그룹화
    grouped = df.groupby('current_date')

    daily_benchmark = []

    for date, group in grouped:
        # 각 종목의 평균 수익률: (long_return + short_return) / 2
        # 포지션 유무에 관계없이 모든 종목을 포함
        group['avg_return'] = (group['long_return'] +
                               group['short_return']) / 2

        # 모든 종목의 평균 수익률을 동일가중으로 계산
        all_returns = group['avg_return']
        benchmark_return = all_returns.mean() if not all_returns.empty else 0

        daily_benchmark.append({
            'current_date': date,
            'benchmark_return': benchmark_return,
            'n_stocks': len(all_returns)  # 모든 종목 수
        })

    # 데이터프레임으로 변환
    benchmark_df = pd.DataFrame(daily_benchmark).set_index('current_date')

    # 누적 수익률 계산
    benchmark_df['cumulative_return'] = (
        1 + benchmark_df['benchmark_return']).cumprod()

    return benchmark_df


def calculate_delta_neutral_by_category_with_benchmark(df, category_col='규모구분'):
    """
    카테고리별 델타-뉴트럴 방식으로 누적 수익률 계산 (벤치마크 포함)
    """
    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 벤치마크 데이터 계산
    benchmark_results = calculate_equal_weighted_benchmark(df, category_col)

    # 전체 결과 저장
    all_results = {}

    # 1. 전체 포트폴리오 계산
    all_cum, all_daily = calculate_delta_neutral_returns(df)
    all_results['전체'] = {
        'cumulative': all_cum,
        'daily': all_daily,
        'benchmark': benchmark_results['전체'],
        'metrics': calculate_performance_metrics_with_benchmark(all_daily, benchmark_results['전체'])
    }

    # 2. 카테고리별 계산
    categories = df[category_col].unique()

    for category in categories:
        category_df = df[df[category_col] == category].copy()
        if len(category_df) > 0:
            cat_cum, cat_daily = calculate_delta_neutral_returns(category_df)
            all_results[category] = {
                'cumulative': cat_cum,
                'daily': cat_daily,
                'benchmark': benchmark_results[category],
                'metrics': calculate_performance_metrics_with_benchmark(cat_daily, benchmark_results[category])
            }

    return all_results


def calculate_delta_neutral_returns(df):
    """
    델타-뉴트럴 방식으로 누적 수익률 계산
    """
    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 각 날짜별로 그룹화
    grouped = df.groupby('current_date')

    # 일별 수익률 저장할 리스트
    daily_results = []

    for date, group in grouped:
        # 롱 포지션과 숏 포지션 분리
        long_positions = group[group['long_return'] != 0]
        short_positions = group[group['short_return'] != 0]

        # 롱과 숏 종목 수
        n_long = len(long_positions)
        n_short = len(short_positions)

        # 델타-뉴트럴 가중치 계산
        if n_long > 0:
            long_weight = 0.5 / n_long
            weighted_long_return = (
                long_positions['long_return'] * long_weight).sum()
        else:
            weighted_long_return = 0

        if n_short > 0:
            short_weight = 0.5 / n_short
            weighted_short_return = (
                short_positions['short_return'] * short_weight).sum()
        else:
            weighted_short_return = 0

        # 롱숏 합산 수익률
        long_short_return = weighted_long_return + weighted_short_return

        daily_results.append({
            'current_date': date,
            'long_return': weighted_long_return,
            'short_return': weighted_short_return,
            'long_short_return': long_short_return,
            'n_long': n_long,
            'n_short': n_short,
            'n_total': n_long + n_short
        })

    # 데이터프레임으로 변환
    daily_returns = pd.DataFrame(daily_results).set_index('current_date')

    # 누적 수익률 계산
    cumulative_returns = pd.DataFrame(index=daily_returns.index)
    cumulative_returns['Long'] = (1 + daily_returns['long_return']).cumprod()
    cumulative_returns['Short'] = (1 + daily_returns['short_return']).cumprod()
    cumulative_returns['Long+Short'] = (1 +
                                        daily_returns['long_short_return']).cumprod()

    return cumulative_returns, daily_returns


def calculate_performance_metrics_with_benchmark(daily_returns, benchmark_data):
    """
    벤치마크를 포함한 성과 지표 계산
    """
    metrics = {}

    # 실제 거래일 수 계산
    start_date = daily_returns.index.min()
    end_date = daily_returns.index.max()
    total_days = (end_date - start_date).days
    trading_days = len(daily_returns)

    # 연간 거래일 수 추정
    annual_trading_days = trading_days * 365 / total_days if total_days > 0 else 252

    # 벤치마크 수익률 (날짜 매칭)
    benchmark_returns = benchmark_data['benchmark_return'].reindex(
        daily_returns.index).fillna(0)

    for column in ['long_return', 'short_return', 'long_short_return']:
        returns = daily_returns[column]

        # 기본 지표들
        annual_return = (1 + returns.mean()) ** annual_trading_days - 1
        annual_vol = returns.std() * np.sqrt(annual_trading_days)
        sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0

        # 최대 낙폭
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 누적 수익률
        total_return = (1 + returns).prod() - 1

        # 벤치마크 대비 지표들
        excess_returns = returns - benchmark_returns

        # 알파, 베타 (CAPM)
        if len(returns) > 1 and benchmark_returns.std() != 0:
            try:
                beta, alpha_intercept, r_value, p_value, std_err = stats.linregress(
                    benchmark_returns, returns)
                alpha = alpha_intercept * annual_trading_days
            except:
                beta, alpha, r_value = 0, 0, 0
        else:
            beta, alpha, r_value = 0, 0, 0

        # 정보비율 (Information Ratio)
        tracking_error = excess_returns.std() * np.sqrt(annual_trading_days)
        information_ratio = (annual_return - benchmark_returns.mean() *
                             annual_trading_days) / tracking_error if tracking_error != 0 else 0

        # 소르티노 비율 (Sortino Ratio)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std(
        ) * np.sqrt(annual_trading_days) if len(downside_returns) > 0 else 0
        sortino_ratio = annual_return / downside_vol if downside_vol != 0 else 0

        # 칼마 비율 (Calmar Ratio)
        calmar_ratio = annual_return / \
            abs(max_drawdown) if max_drawdown != 0 else 0

        # VaR & CVaR (95% 신뢰수준)
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean() if len(
            returns[returns <= var_95]) > 0 else var_95

        # 하향 변동성 (연율화)
        downside_volatility = downside_vol

        metrics[column] = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_vol': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'beta': beta,
            'alpha': alpha,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'downside_volatility': downside_volatility,
            'correlation': r_value
        }

    # 벤치마크 지표도 추가
    benchmark_annual_return = (
        1 + benchmark_returns.mean()) ** annual_trading_days - 1
    benchmark_annual_vol = benchmark_returns.std() * np.sqrt(annual_trading_days)
    benchmark_sharpe = benchmark_annual_return / \
        benchmark_annual_vol if benchmark_annual_vol != 0 else 0
    benchmark_cumulative = (1 + benchmark_returns).cumprod()
    benchmark_running_max = benchmark_cumulative.cummax()
    benchmark_drawdown = (benchmark_cumulative -
                          benchmark_running_max) / benchmark_running_max
    benchmark_max_drawdown = benchmark_drawdown.min()
    benchmark_total_return = (1 + benchmark_returns).prod() - 1

    metrics['benchmark'] = {
        'total_return': benchmark_total_return,
        'annual_return': benchmark_annual_return,
        'annual_vol': benchmark_annual_vol,
        'sharpe_ratio': benchmark_sharpe,
        'max_drawdown': benchmark_max_drawdown,
        'var_95': np.percentile(benchmark_returns, 5),
        'cvar_95': benchmark_returns[benchmark_returns <= np.percentile(benchmark_returns, 5)].mean()
    }

    return metrics


def create_comprehensive_summary_table(all_results):
    """
    벤치마크를 포함한 종합 요약 테이블 생성 (Long, Short, Long+Short, Benchmark)
    """
    summary_data = []

    for category, data in all_results.items():
        if 'metrics' in data and 'daily' in data:
            long_metrics = data['metrics']['long_return']
            short_metrics = data['metrics']['short_return']
            longshort_metrics = data['metrics']['long_short_return']
            benchmark_metrics = data['metrics']['benchmark']
            daily = data['daily']

            # 일평균 거래 종목 수 (실제 포지션을 가진 종목)
            avg_trading_stocks = daily['n_total'].mean()

            # 일평균 전체 종목 수 (벤치마크에 포함된 모든 종목)
            avg_total_stocks = data['benchmark']['n_stocks'].mean()

            summary_data.append({
                '전략 유형': category,
                '최종 누적수익률': longshort_metrics['total_return'],
                '연율화 수익률': longshort_metrics['annual_return'],
                '벤치마크 대비 초과수익률': longshort_metrics['annual_return'] - benchmark_metrics['annual_return'],
                '일평균 거래 종목 수': avg_trading_stocks,
                '일평균 전체 종목 수': avg_total_stocks,
                '일 표준편차': daily['long_short_return'].std(),
                '일 분산': daily['long_short_return'].var(),
                '왜도': daily['long_short_return'].skew(),
                '첨도': daily['long_short_return'].kurtosis(),
                '최대 수익': daily['long_short_return'].max(),
                '최소 수익': daily['long_short_return'].min()
            })

    summary_df = pd.DataFrame(summary_data)

    # 전체를 맨 위로
    if '전체' in summary_df['전략 유형'].values:
        전체_row = summary_df[summary_df['전략 유형'] == '전체']
        other_rows = summary_df[summary_df['전략 유형'] !=
                                '전체'].sort_values('일평균 거래 종목 수', ascending=False)
        summary_df = pd.concat([전체_row, other_rows])

    return summary_df


def create_four_strategy_comparison_table(all_results):
    """
    각 카테고리별 Long Only, Short Only, Long+Short, Benchmark 비교 테이블
    """
    comparison_data = []

    for category, data in all_results.items():
        if 'metrics' in data:
            long_metrics = data['metrics']['long_return']
            short_metrics = data['metrics']['short_return']
            longshort_metrics = data['metrics']['long_short_return']
            benchmark_metrics = data['metrics']['benchmark']

            comparison_data.append({
                '전략 유형': category,
                'Long (50%)': long_metrics['total_return'],
                'Short (50%)': short_metrics['total_return'],
                'Long+Short (Delta-Neutral)': longshort_metrics['total_return'],
                'Market Average Benchmark': benchmark_metrics['total_return']
            })

    comparison_df = pd.DataFrame(comparison_data)

    # 전체를 맨 위로
    if '전체' in comparison_df['전략 유형'].values:
        전체_row = comparison_df[comparison_df['전략 유형'] == '전체']
        other_rows = comparison_df[comparison_df['전략 유형'] != '전체'].sort_values(
            'Long+Short (Delta-Neutral)', ascending=False)
        comparison_df = pd.concat([전체_row, other_rows])

    return comparison_df


def create_risk_adjusted_metrics_table(all_results):
    """
    위험조정 지표 테이블 생성
    """
    risk_data = []

    for category, data in all_results.items():
        if 'metrics' in data:
            long_metrics = data['metrics']['long_return']
            short_metrics = data['metrics']['short_return']
            longshort_metrics = data['metrics']['long_short_return']
            benchmark_metrics = data['metrics']['benchmark']

            risk_data.append({
                '전략 유형': category,
                '샤프 비율': longshort_metrics['sharpe_ratio'],
                '소르티노 비율': longshort_metrics['sortino_ratio'],
                '칼마 비율': longshort_metrics['calmar_ratio'],
                'VaR (95%)': longshort_metrics['var_95'],
                'CVaR (95%)': longshort_metrics['cvar_95'],
                '하향 변동성(연율화)': longshort_metrics['downside_volatility']
            })

    risk_df = pd.DataFrame(risk_data)

    # 전체를 맨 위로
    if '전체' in risk_df['전략 유형'].values:
        전체_row = risk_df[risk_df['전략 유형'] == '전체']
        other_rows = risk_df[risk_df['전략 유형'] !=
                             '전체'].sort_values('샤프 비율', ascending=False)
        risk_df = pd.concat([전체_row, other_rows])

    return risk_df


def plot_comprehensive_analysis(all_results, save_dir='comprehensive_analysis'):
    """
    종합 분석 그래프 생성 (Long, Short, Long+Short, Market Average Benchmark)
    """
    os.makedirs(save_dir, exist_ok=True)

    # 1. 전체 카테고리별 Long+Short vs Market Average Benchmark 비교
    fig, ax = plt.subplots(figsize=(15, 10))

    for category, data in all_results.items():
        if 'cumulative' in data and 'benchmark' in data:
            # 포트폴리오 Long+Short 누적 수익률
            ax.plot(data['cumulative'].index,
                    data['cumulative']['Long+Short'],
                    label=f'{category} (Delta-Neutral)',
                    linewidth=3 if category == '전체' else 2,
                    color='green')

            # 벤치마크 누적 수익률
            ax.plot(data['benchmark'].index,
                    data['benchmark']['cumulative_return'],
                    label=f'{category} (Market Average)',
                    linewidth=2,
                    linestyle='--',
                    color='gray',
                    alpha=0.8)

    ax.set_title('카테고리별 Delta-Neutral vs Market Average Benchmark 누적 수익률 비교',
                 fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return', fontsize=12)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y-1)))

    plt.tight_layout()
    fig.savefig(f'{save_dir}/delta_neutral_vs_market_benchmark.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 2. 카테고리별 4가지 전략 비교 (Long, Short, Long+Short, Market Average Benchmark)
    for category, data in all_results.items():
        if 'cumulative' in data and 'benchmark' in data:
            fig, ax = plt.subplots(figsize=(14, 10))

            # Long, Short, Long+Short 전략
            ax.plot(data['cumulative'].index, data['cumulative']['Long'],
                    label='Long (50%)', linewidth=2.5, color='blue')
            ax.plot(data['cumulative'].index, data['cumulative']['Short'],
                    label='Short (50%)', linewidth=2.5, color='red')
            ax.plot(data['cumulative'].index, data['cumulative']['Long+Short'],
                    label='Long+Short (Delta-Neutral)', linewidth=2.5, color='green')

            # 벤치마크
            ax.plot(data['benchmark'].index, data['benchmark']['cumulative_return'],
                    label='Market Average Benchmark', linewidth=2.5, color='gray', linestyle='--')

            ax.set_title(
                f'{category}: Delta-Neutral Portfolio vs Market Average Benchmark', fontsize=15, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Cumulative Return', fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y-1)))

            plt.tight_layout()
            safe_filename = category.replace(' ', '_').replace('/', '_')
            fig.savefig(
                f'{save_dir}/delta_neutral_{safe_filename}.png', dpi=300, bbox_inches='tight')
            plt.close()

    print(f"📊 종합 분석 그래프 저장 완료 → '{save_dir}' 폴더")


def print_formatted_table_enhanced(df, title):
    """포맷팅된 테이블 출력 (향상된 버전)"""
    print(f"\n{'='*100}")
    print(f"{title:^100}")
    print('='*100)

    # 숫자 포맷팅
    df_formatted = df.copy()
    for col in df_formatted.columns:
        if col in ['일평균 거래 종목 수', '일평균 전체 종목 수']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:,.1f}" if pd.notna(x) else '')
        elif col in ['최종 누적수익률', '연율화 수익률', '벤치마크 대비 초과수익률',
                     'Long (50%)', 'Short (50%)', 'Long+Short (Delta-Neutral)', 'Market Average Benchmark']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
        elif col in ['일 표준편차', '일 분산', '왜도', '첨도', '최대 수익', '최소 수익',
                     'VaR (95%)', 'CVaR (95%)', '하향 변동성(연율화)']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.4f}" if isinstance(x, (int, float)) else x)
        elif col in ['샤프 비율', '소르티노 비율', '칼마 비율']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x)

    print(df_formatted.to_string(index=False))
    print('='*100)


# 메인 실행 코드
if __name__ == "__main__":
    # 1. 데이터 불러오기
    df = pd.read_csv(
        '/Users/imdonghyeon/Desktop/Quantlab/final_수정/news_with_sector.csv')

    # 데이터 타입 변환
    df['long_return'] = pd.to_numeric(
        df['long_return'], errors='coerce').fillna(0)
    df['short_return'] = pd.to_numeric(
        df['short_return'], errors='coerce').fillna(0)

    # 2. 기본 정보 출력
    print("📊 데이터 기본 정보")
    print("-" * 50)
    print(f"데이터 shape: {df.shape}")
    print(f"기간: {df['current_date'].min()} ~ {df['current_date'].max()}")
    print(f"규모구분 종류: {df['규모구분'].nunique()}개")
    print(f"규모구분 목록: {sorted(df['규모구분'].dropna().unique())}")

    # 3. 벤치마크를 포함한 카테고리별 델타-뉴트럴 분석
    all_results = calculate_delta_neutral_by_category_with_benchmark(df)

    # 4. Long Only, Short Only, Long+Short, Market Average Benchmark 비교 테이블
    four_strategy_df = create_four_strategy_comparison_table(all_results)
    print_formatted_table_enhanced(
        four_strategy_df, "Delta-Neutral Portfolio vs Market Average Benchmark 최종 누적수익률 비교")

    # 5. 종합 요약 테이블 (Statistical Measures)
    summary_df = create_comprehensive_summary_table(all_results)
    print_formatted_table_enhanced(summary_df, "Statistical Measures")

    # 6. 위험조정 지표 테이블 (Risk-Adjusted Metrics)
    risk_df = create_risk_adjusted_metrics_table(all_results)
    print_formatted_table_enhanced(risk_df, "Risk-Adjusted Metrics")

    # 7. 종합 분석 그래프 생성
    plot_comprehensive_analysis(all_results)

    # 8. 결과 저장
    four_strategy_df.to_csv(
        'delta_neutral_strategy_comparison.csv', encoding='utf-8-sig', index=False)
    summary_df.to_csv('statistical_measures.csv',
                      encoding='utf-8-sig', index=False)
    risk_df.to_csv('risk_adjusted_metrics.csv',
                   encoding='utf-8-sig', index=False)

    # 9. 각 카테고리별 상세 성과 분석
    print("\n" + "="*100)
    print("카테고리별 상세 성과 분석")
    print("="*100)

    for category, data in all_results.items():
        if 'metrics' in data:
            print(f"\n📊 {category} 전략 분석:")
            print("-" * 50)

            long_metrics = data['metrics']['long_return']
            short_metrics = data['metrics']['short_return']
            longshort_metrics = data['metrics']['long_short_return']
            benchmark_metrics = data['metrics']['benchmark']

            print(
                f"Long (50%)         수익률: {long_metrics['total_return']:.2%}")
            print(
                f"Short (50%)        수익률: {short_metrics['total_return']:.2%}")
            print(
                f"Delta-Neutral      수익률: {longshort_metrics['total_return']:.2%}")
            print(
                f"Market Average Benchmark: {benchmark_metrics['total_return']:.2%}")
            print(
                f"초과 수익률 (vs Benchmark): {longshort_metrics['total_return'] - benchmark_metrics['total_return']:.2%}")
            print(f"샤프 비율: {longshort_metrics['sharpe_ratio']:.3f}")
            print(f"최대 낙폭: {longshort_metrics['max_drawdown']:.2%}")

    print("\n✅ Delta-Neutral vs Market Average Benchmark 분석 완료!")
    print("📁 생성된 파일:")
    print("  - delta_neutral_strategy_comparison.csv")
    print("  - statistical_measures.csv")
    print("  - risk_adjusted_metrics.csv")
    print("  - comprehensive_analysis/ (그래프 폴더)")
