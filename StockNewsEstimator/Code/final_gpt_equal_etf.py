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


def load_etf_data(etf_file_path):
    """
    ETF 데이터 로드 및 전처리
    """
    # ETF 데이터 읽기
    etf_df = pd.read_excel(etf_file_path)

    # 디버깅: 컬럼 정보 출력
    print(f"전체 컬럼 수: {len(etf_df.columns)}")
    print(f"처음 10개 컬럼: {list(etf_df.columns[:10])}")

    # ETF 코드별 정확한 분류 (KODEX 기준)
    etf_classification = {
        'A325010': 'SSC',  # KODEX 성장주
        'A275290': 'VSC',  # KODEX 가치주
    }

    # 날짜 컬럼 찾기 - 다양한 방법 시도
    date_columns = []
    for col in etf_df.columns:
        # 문자열 형태의 날짜
        if isinstance(col, str):
            if '-' in col and (col.startswith('20') or col.startswith('19')):
                date_columns.append(col)
        # datetime 객체
        elif isinstance(col, pd.Timestamp):
            date_columns.append(col)
        # numpy datetime
        elif hasattr(col, 'strftime'):
            date_columns.append(col)

    print(f"찾은 날짜 컬럼 수: {len(date_columns)}")
    if date_columns:
        print(f"첫 번째 날짜 컬럼: {date_columns[0]}, 타입: {type(date_columns[0])}")

    # ETF별 데이터 정리
    etf_data = {}
    processed_symbols = set()  # 중복 처리 방지

    for idx, row in etf_df.iterrows():
        symbol = row['Symbol']

        # 중복 처리 방지
        if symbol in processed_symbols:
            continue
        processed_symbols.add(symbol)

        # ETF 분류 결정 (수동 매핑 우선, 없으면 원본 Kind 사용)
        kind = etf_classification.get(symbol, row['Kind'])

        # 종가 데이터만 추출
        prices = {}
        for date_col in date_columns:
            try:
                value = row[date_col]
                if pd.notna(value) and float(value) > 0:
                    # 날짜를 datetime으로 변환
                    if isinstance(date_col, str):
                        date_key = pd.to_datetime(date_col)
                    else:
                        date_key = pd.to_datetime(date_col)
                    prices[date_key] = float(value)
            except:
                continue

        if prices:
            etf_data[f"{symbol}_{kind}"] = {
                'name': row['Symbol Name'],
                'kind': kind,
                'prices': pd.Series(prices).sort_index()
            }
            print(f"로드된 ETF: {symbol} ({kind}), 가격 데이터 수: {len(prices)}")

    return etf_data


def calculate_etf_returns(etf_prices, start_date, end_date):
    """
    ETF 일별 수익률 계산
    """
    # 기간 필터링
    mask = (etf_prices.index >= pd.to_datetime(start_date)) & (
        etf_prices.index <= pd.to_datetime(end_date))
    prices_filtered = etf_prices[mask]

    if len(prices_filtered) < 2:
        return None, None

    # 일별 수익률 계산
    daily_returns = prices_filtered.pct_change().dropna()

    # 누적 수익률 계산 (시작점 1로 정규화)
    cumulative_returns = (1 + daily_returns).cumprod()

    return daily_returns, cumulative_returns


def calculate_equal_weighted_benchmark(df, category_col='스타일'):
    """
    각 카테고리별 동일가중 벤치마크(EqualWeight) 수익률 계산
    """
    equalweight_results = {}

    # 전체 EqualWeight
    all_equalweight = calculate_category_equalweight(df)
    equalweight_results['전체'] = all_equalweight

    # 성장주 EqualWeight (성장주 + 성장주+가치주 포함)
    growth_df = df[df[category_col].isin(['성장주', '성장주+가치주'])].copy()
    if len(growth_df) > 0:
        growth_equalweight = calculate_category_equalweight(growth_df)
        equalweight_results['성장주'] = growth_equalweight
        print(f"성장주 EqualWeight 계산 완료: {len(growth_df)}개 데이터 (성장주+혼합형)")

    # 가치주 EqualWeight (가치주 + 성장주+가치주 포함)
    value_df = df[df[category_col].isin(['가치주', '성장주+가치주'])].copy()
    if len(value_df) > 0:
        value_equalweight = calculate_category_equalweight(value_df)
        equalweight_results['가치주'] = value_equalweight
        print(f"가치주 EqualWeight 계산 완료: {len(value_df)}개 데이터 (가치주+혼합형)")

    return equalweight_results


def calculate_category_equalweight(df):
    """
    특정 카테고리의 '시장 전체 평균' 동일가중 EqualWeight 수익률 계산
    (long/short 포지션 유무에 관계없이 모든 종목 포함)
    """
    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 각 날짜별로 그룹화
    grouped = df.groupby('current_date')

    daily_equalweight = []

    for date, group in grouped:
        # 각 종목의 평균 수익률: (long_return + short_return) / 2
        # 포지션 유무에 관계없이 모든 종목을 포함
        group['avg_return'] = (group['long_return'] +
                               group['short_return']) / 2

        # 모든 종목의 평균 수익률을 동일가중으로 계산
        all_returns = group['avg_return']
        equalweight_return = all_returns.mean() if not all_returns.empty else 0

        daily_equalweight.append({
            'current_date': date,
            'equalweight_return': equalweight_return,
            'n_stocks': len(all_returns)  # 모든 종목 수
        })

    # 데이터프레임으로 변환
    equalweight_df = pd.DataFrame(daily_equalweight).set_index('current_date')

    # 누적 수익률 계산
    equalweight_df['cumulative_return'] = (
        1 + equalweight_df['equalweight_return']).cumprod()

    return equalweight_df


def calculate_delta_neutral_by_category(df, category_col='스타일'):
    """
    카테고리별 델타-뉴트럴 방식으로 누적 수익률 계산
    """
    # current_date를 datetime으로 변환
    df['current_date'] = pd.to_datetime(df['current_date'])

    # 전체 결과 저장
    all_results = {}

    # 1. 전체 포트폴리오 계산
    all_cum, all_daily = calculate_delta_neutral_returns(df)
    all_results['전체'] = {
        'cumulative': all_cum,
        'daily': all_daily,
        'metrics': calculate_performance_metrics(all_daily)
    }

    # 2. 성장주 계산 (성장주 + 성장주+가치주 포함)
    growth_df = df[df[category_col].isin(['성장주', '성장주+가치주'])].copy()
    if len(growth_df) > 0:
        growth_cum, growth_daily = calculate_delta_neutral_returns(growth_df)
        all_results['성장주'] = {
            'cumulative': growth_cum,
            'daily': growth_daily,
            'metrics': calculate_performance_metrics(growth_daily)
        }
        print(f"성장주 GPT 계산 완료: {len(growth_df)}개 데이터 (성장주+혼합형)")

    # 3. 가치주 계산 (가치주 + 성장주+가치주 포함)
    value_df = df[df[category_col].isin(['가치주', '성장주+가치주'])].copy()
    if len(value_df) > 0:
        value_cum, value_daily = calculate_delta_neutral_returns(value_df)
        all_results['가치주'] = {
            'cumulative': value_cum,
            'daily': value_daily,
            'metrics': calculate_performance_metrics(value_daily)
        }
        print(f"가치주 GPT 계산 완료: {len(value_df)}개 데이터 (가치주+혼합형)")

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


def calculate_performance_metrics(daily_returns):
    """
    성과 지표 계산
    """
    metrics = {}

    # 실제 거래일 수 계산
    start_date = daily_returns.index.min()
    end_date = daily_returns.index.max()
    total_days = (end_date - start_date).days
    trading_days = len(daily_returns)

    # 연간 거래일 수 추정
    annual_trading_days = trading_days * 365 / total_days if total_days > 0 else 252

    for column in ['long_return', 'short_return', 'long_short_return']:
        returns = daily_returns[column]

        # 기본 지표들
        mean_daily_return = returns.mean()
        std_daily_return = returns.std()
        annual_return = (1 + mean_daily_return) ** annual_trading_days - 1
        annual_vol = std_daily_return * np.sqrt(annual_trading_days)
        sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0

        # 최대 낙폭
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 누적 수익률
        total_return = (1 + returns).prod() - 1

        # 소르티노 비율 (Sortino Ratio)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std(
        ) * np.sqrt(annual_trading_days) if len(downside_returns) > 0 else 0
        sortino_ratio = annual_return / downside_vol if downside_vol != 0 else 0

        # 왜도와 첨도
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        metrics[column] = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_vol': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'mean_daily_return': mean_daily_return,
            'std_daily_return': std_daily_return,
            'skewness': skewness,
            'kurtosis': kurtosis
        }

    return metrics


def calculate_etf_metrics(daily_returns):
    """
    ETF 성과 지표 계산
    """
    if daily_returns is None or len(daily_returns) == 0:
        return None

    # 연율화 계수 (252 거래일 가정)
    annual_factor = np.sqrt(252)

    # 기본 지표
    mean_daily_return = daily_returns.mean()
    std_daily_return = daily_returns.std()
    total_return = (1 + daily_returns).prod() - 1
    annual_return = (1 + mean_daily_return) ** 252 - 1
    annual_vol = std_daily_return * annual_factor
    sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0

    # 최대 낙폭
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # 하방 변동성
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std(
    ) * annual_factor if len(downside_returns) > 0 else 0
    sortino_ratio = annual_return / downside_vol if downside_vol != 0 else 0

    # 왜도와 첨도
    skewness = daily_returns.skew()
    kurtosis = daily_returns.kurtosis()

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_drawdown,
        'mean_daily_return': mean_daily_return,
        'std_daily_return': std_daily_return,
        'skewness': skewness,
        'kurtosis': kurtosis
    }


def calculate_equalweight_metrics(daily_returns):
    """
    EqualWeight 성과 지표 계산
    """
    if daily_returns is None or len(daily_returns) == 0:
        return None

    # 연율화 계수 (252 거래일 가정)
    annual_factor = np.sqrt(252)

    # 기본 지표
    mean_daily_return = daily_returns.mean()
    std_daily_return = daily_returns.std()
    total_return = (1 + daily_returns).prod() - 1
    annual_return = (1 + mean_daily_return) ** 252 - 1
    annual_vol = std_daily_return * annual_factor
    sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0

    # 최대 낙폭
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # 하방 변동성
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std(
    ) * annual_factor if len(downside_returns) > 0 else 0
    sortino_ratio = annual_return / downside_vol if downside_vol != 0 else 0

    # 왜도와 첨도
    skewness = daily_returns.skew()
    kurtosis = daily_returns.kurtosis()

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_drawdown,
        'mean_daily_return': mean_daily_return,
        'std_daily_return': std_daily_return,
        'skewness': skewness,
        'kurtosis': kurtosis
    }


def create_comprehensive_comparison_table(gpt_results, etf_data, equalweight_results, start_date, end_date):
    """
    GPT, ETF, EqualWeight 종합 비교 테이블 생성
    """
    comparison_data = []

    # 카테고리 순서 정의
    categories = ['전체', '성장주', '가치주']

    for category in categories:
        # GPT 데이터 추가 (LongShort, Long, Short)
        if category in gpt_results:
            gpt_data = gpt_results[category]

            # GPT LongShort
            if 'metrics' in gpt_data:
                metrics = gpt_data['metrics']['long_short_return']
                comparison_data.append({
                    '구분': f'GPT_{category}_LongShort',
                    '유형': 'GPT',
                    '최종 누적수익률': metrics['total_return'],
                    '연율화 수익률': metrics['annual_return'],
                    '연율화 변동성': metrics['annual_vol'],
                    '샤프 비율': metrics['sharpe_ratio'],
                    '소르티노 비율': metrics['sortino_ratio'],
                    '최대 낙폭': metrics['max_drawdown'],
                    '일별 평균수익률': metrics['mean_daily_return'],
                    '일별 표준편차': metrics['std_daily_return'],
                    '왜도': metrics['skewness'],
                    '첨도': metrics['kurtosis']
                })

                # GPT Long
                metrics_long = gpt_data['metrics']['long_return']
                comparison_data.append({
                    '구분': f'GPT_{category}_Long',
                    '유형': 'GPT',
                    '최종 누적수익률': metrics_long['total_return'],
                    '연율화 수익률': metrics_long['annual_return'],
                    '연율화 변동성': metrics_long['annual_vol'],
                    '샤프 비율': metrics_long['sharpe_ratio'],
                    '소르티노 비율': metrics_long['sortino_ratio'],
                    '최대 낙폭': metrics_long['max_drawdown'],
                    '일별 평균수익률': metrics_long['mean_daily_return'],
                    '일별 표준편차': metrics_long['std_daily_return'],
                    '왜도': metrics_long['skewness'],
                    '첨도': metrics_long['kurtosis']
                })

                # GPT Short
                metrics_short = gpt_data['metrics']['short_return']
                comparison_data.append({
                    '구분': f'GPT_{category}_Short',
                    '유형': 'GPT',
                    '최종 누적수익률': metrics_short['total_return'],
                    '연율화 수익률': metrics_short['annual_return'],
                    '연율화 변동성': metrics_short['annual_vol'],
                    '샤프 비율': metrics_short['sharpe_ratio'],
                    '소르티노 비율': metrics_short['sortino_ratio'],
                    '최대 낙폭': metrics_short['max_drawdown'],
                    '일별 평균수익률': metrics_short['mean_daily_return'],
                    '일별 표준편차': metrics_short['std_daily_return'],
                    '왜도': metrics_short['skewness'],
                    '첨도': metrics_short['kurtosis']
                })

        # EqualWeight 데이터 추가
        if category in equalweight_results:
            ew_data = equalweight_results[category]
            ew_metrics = calculate_equalweight_metrics(
                ew_data['equalweight_return'])
            if ew_metrics:
                comparison_data.append({
                    '구분': f'EqualWeight_{category}',
                    '유형': 'EqualWeight',
                    '최종 누적수익률': ew_metrics['total_return'],
                    '연율화 수익률': ew_metrics['annual_return'],
                    '연율화 변동성': ew_metrics['annual_vol'],
                    '샤프 비율': ew_metrics['sharpe_ratio'],
                    '소르티노 비율': ew_metrics['sortino_ratio'],
                    '최대 낙폭': ew_metrics['max_drawdown'],
                    '일별 평균수익률': ew_metrics['mean_daily_return'],
                    '일별 표준편차': ew_metrics['std_daily_return'],
                    '왜도': ew_metrics['skewness'],
                    '첨도': ew_metrics['kurtosis']
                })

        # ETF 데이터 추가
        if category == '전체':
            # ETF 전체 평균 계산
            etf_metrics_list = []
            for etf_name, etf_info in etf_data.items():
                daily_returns, _ = calculate_etf_returns(
                    etf_info['prices'], start_date, end_date
                )
                if daily_returns is not None:
                    metrics = calculate_etf_metrics(daily_returns)
                    if metrics:
                        etf_metrics_list.append(metrics)

            if etf_metrics_list:
                # 평균 계산
                avg_metrics = {}
                for key in etf_metrics_list[0].keys():
                    avg_metrics[key] = np.mean(
                        [m[key] for m in etf_metrics_list])

                comparison_data.append({
                    '구분': 'ETF_전체',
                    '유형': 'ETF',
                    '최종 누적수익률': avg_metrics['total_return'],
                    '연율화 수익률': avg_metrics['annual_return'],
                    '연율화 변동성': avg_metrics['annual_vol'],
                    '샤프 비율': avg_metrics['sharpe_ratio'],
                    '소르티노 비율': avg_metrics['sortino_ratio'],
                    '최대 낙폭': avg_metrics['max_drawdown'],
                    '일별 평균수익률': avg_metrics['mean_daily_return'],
                    '일별 표준편차': avg_metrics['std_daily_return'],
                    '왜도': avg_metrics['skewness'],
                    '첨도': avg_metrics['kurtosis']
                })

        else:
            # 개별 ETF 찾기
            etf_kind_map = {'성장주': 'SSC', '가치주': 'VSC'}
            target_kind = etf_kind_map.get(category)

            if target_kind:
                for etf_name, etf_info in etf_data.items():
                    if etf_info['kind'] == target_kind:
                        daily_returns, _ = calculate_etf_returns(
                            etf_info['prices'], start_date, end_date
                        )
                        if daily_returns is not None:
                            metrics = calculate_etf_metrics(daily_returns)
                            if metrics:
                                comparison_data.append({
                                    '구분': f'ETF_{category}',
                                    '유형': 'ETF',
                                    '최종 누적수익률': metrics['total_return'],
                                    '연율화 수익률': metrics['annual_return'],
                                    '연율화 변동성': metrics['annual_vol'],
                                    '샤프 비율': metrics['sharpe_ratio'],
                                    '소르티노 비율': metrics['sortino_ratio'],
                                    '최대 낙폭': metrics['max_drawdown'],
                                    '일별 평균수익률': metrics['mean_daily_return'],
                                    '일별 표준편차': metrics['std_daily_return'],
                                    '왜도': metrics['skewness'],
                                    '첨도': metrics['kurtosis']
                                })
                                break

    comparison_df = pd.DataFrame(comparison_data)
    return comparison_df


def plot_comprehensive_comparison(gpt_results, etf_data, equalweight_results, start_date, end_date, save_dir='comprehensive_analysis'):
    """
    GPT, EqualWeight, ETF 누적수익률 비교 그래프 (전체, 성장주, 가치주)
    """
    os.makedirs(save_dir, exist_ok=True)

    # 카테고리 리스트
    categories = ['전체', '성장주', '가치주']
    category_names_eng = {'전체': 'Total',
                          '성장주': 'Growth', '가치주': 'Value'}
    etf_kind_map = {'성장주': 'SSC', '가치주': 'VSC'}

    for category in categories:
        fig, ax = plt.subplots(figsize=(15, 10))

        # GPT 누적수익률
        if category in gpt_results and 'cumulative' in gpt_results[category]:
            gpt_data = gpt_results[category]['cumulative']['Long+Short']
            ax.plot(gpt_data.index, gpt_data,
                    label='GPT (Delta-Neutral)', linewidth=3, color='darkgreen')

        # EqualWeight 누적수익률
        if category in equalweight_results:
            ew_data = equalweight_results[category]['cumulative_return']
            ax.plot(ew_data.index, ew_data,
                    label='EqualWeight', linewidth=3, color='darkred')

        # ETF 누적수익률
        if category == '전체':
            # ETF 전체 평균 누적수익률
            etf_combined_daily_returns = None
            for etf_name, etf_info in etf_data.items():
                daily_returns, _ = calculate_etf_returns(
                    etf_info['prices'], start_date, end_date
                )
                if daily_returns is not None:
                    if etf_combined_daily_returns is None:
                        etf_combined_daily_returns = pd.DataFrame(
                            index=daily_returns.index)
                    etf_combined_daily_returns[etf_name] = daily_returns

            if etf_combined_daily_returns is not None and not etf_combined_daily_returns.empty:
                etf_avg_daily_returns = etf_combined_daily_returns.mean(axis=1)
                etf_cumulative = (1 + etf_avg_daily_returns).cumprod()
                ax.plot(etf_cumulative.index, etf_cumulative,
                        label='ETF Average', linewidth=3, color='darkblue')
        else:
            # 개별 ETF 찾기
            target_kind = etf_kind_map.get(category)
            if target_kind:
                for etf_name, etf_info in etf_data.items():
                    if etf_info['kind'] == target_kind:
                        daily_returns, cumulative_returns = calculate_etf_returns(
                            etf_info['prices'], start_date, end_date
                        )
                        if cumulative_returns is not None:
                            ax.plot(cumulative_returns.index, cumulative_returns,
                                    label='ETF', linewidth=3, color='darkblue')
                            break

        # 영어 제목 사용
        category_eng = category_names_eng.get(category, category)
        ax.set_title(f'{category_eng} - GPT vs EqualWeight vs ETF Cumulative Return Comparison',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return', fontsize=12)
        ax.legend(loc='upper left')  # 왼쪽 위로 고정
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y-1)))

        plt.tight_layout()

        # 파일명에 카테고리 추가
        safe_filename = category.replace(' ', '_').replace('/', '_')
        fig.savefig(f'{save_dir}/gpt_vs_equalweight_vs_etf_{safe_filename}.png',
                    dpi=300, bbox_inches='tight')
        plt.close()

    print(f"📊 비교 그래프 저장 완료 → '{save_dir}' 폴더")


def print_formatted_table_enhanced(df, title):
    """포맷팅된 테이블 출력 (향상된 버전)"""
    print(f"\n{'='*140}")
    print(f"{title:^140}")
    print('='*140)

    # 숫자 포맷팅
    df_formatted = df.copy()
    for col in df_formatted.columns:
        if col in ['최종 누적수익률', '연율화 수익률', '연율화 변동성']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
        elif col in ['일별 평균수익률', '일별 표준편차']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.4%}" if isinstance(x, (int, float)) else x)
        elif col in ['샤프 비율', '소르티노 비율']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x)
        elif col in ['최대 낙폭']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
        elif col in ['왜도', '첨도']:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.4f}" if isinstance(x, (int, float)) else x)

    print(df_formatted.to_string(index=False))
    print('='*140)


# 메인 실행 코드
if __name__ == "__main__":
    # 1. 데이터 불러오기
    df = pd.read_csv(
        '/Users/imdonghyeon/Desktop/Quantlab/final_수정/news_with_style.csv')

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
    print(f"스타일 종류: {df['스타일'].nunique()}개")
    print(f"스타일 목록: {sorted(df['스타일'].dropna().unique())}")

    # 스타일별 종목 수 확인
    style_counts = df.groupby('스타일').size()
    print("\n스타일별 종목 수:")
    for style, count in style_counts.items():
        print(f"  - {style}: {count}개")

    # 날짜 범위
    start_date = df['current_date'].min()
    end_date = df['current_date'].max()

    # 3. GPT (델타-뉴트럴) 분석
    print("\n📈 GPT (델타-뉴트럴) 분석 시작...")
    gpt_results = calculate_delta_neutral_by_category(df)
    print("✓ GPT 분석 완료: 전체, 성장주(혼합형 포함), 가치주(혼합형 포함)")

    # 4. EqualWeight 분석
    print("\n📊 EqualWeight 분석 시작...")
    equalweight_results = calculate_equal_weighted_benchmark(df)
    print("✓ EqualWeight 분석 완료: 전체, 성장주(혼합형 포함), 가치주(혼합형 포함)")

    # 5. ETF 데이터 로드
    etf_file_path = '/Users/imdonghyeon/Desktop/Quantlab/final_수정/KODEX_섹터.xlsx'

    try:
        etf_data = load_etf_data(etf_file_path)
        print(f"\n✅ ETF 데이터 로드 완료: {len(etf_data)}개 ETF")

        # 6. 종합 비교 테이블 생성
        comparison_df = create_comprehensive_comparison_table(
            gpt_results, etf_data, equalweight_results, start_date, end_date
        )

        # 7. 테이블 출력
        print_formatted_table_enhanced(
            comparison_df, "GPT vs EqualWeight vs ETF 성과 비교")

        # 8. 그래프 생성
        plot_comprehensive_comparison(
            gpt_results, etf_data, equalweight_results, start_date, end_date
        )

        # 9. 결과 저장
        comparison_df.to_csv('gpt_equalweight_etf_comparison.csv',
                             encoding='utf-8-sig', index=False)

        print("\n✅ 통합 분석 완료!")
        print("📁 생성된 파일:")
        print("  - gpt_equalweight_etf_comparison.csv")
        print("  - comprehensive_analysis/gpt_vs_equalweight_vs_etf_전체.png")
        print("  - comprehensive_analysis/gpt_vs_equalweight_vs_etf_성장주.png")
        print("  - comprehensive_analysis/gpt_vs_equalweight_vs_etf_가치주.png")

    except FileNotFoundError:
        print(f"\n⚠️ ETF 파일을 찾을 수 없습니다: {etf_file_path}")
        print("ETF 비교 분석을 건너뜁니다.")
    except Exception as e:
        print(f"\n⚠️ ETF 데이터 처리 중 오류 발생: {str(e)}")
        print("ETF 비교 분석을 건너뜁니다.")
        import traceback
        traceback.print_exc()
