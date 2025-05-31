# Can ChatGPT(4.1Nano) Forecast Stock Price Movements? Return Predictability and Large Language Models

이 저장소는 뉴스 기사 텍스트를 분석하여 주식 시장에 미치는 영향을 평가하고, 이를 기반으로 다양한 투자 전략의 성과를 시뮬레이션하는 Python 스크립트를 포함합니다.

## `GPTScore.py`

뉴스 기사 제목과 기업명을 기반으로 GPT 모델을 사용하여 감성 점수(긍정/부정/중립)를 도출하고, 이를 Excel 파일에 추가하는 스크립트입니다.

---

### 1\. 사용 기술 스택

| 범주               | 라이브러리/도구 | 역할                                          |
| :----------------- | :-------------- | :-------------------------------------------- |
| **언어**           | Python 3.x      | 전반적인 스크립트 실행                        |
| **API 클라이언트** | `openai` SDK    | OpenAI Chat Completion 호출                   |
| **데이터 처리**    | `pandas`        | Excel 파일을 DataFrame으로 읽고, 가공 후 저장 |
| **파일 입출력**    | `os`, `time`    | 환경 변수를 통한 API Key 로딩, 요청 간격 제어 |
| **포맷**           | Excel (.xlsx)   | 원본 데이터 및 결과물 저장                    |

---

### 2\. 코드 로직 단계별 설명

#### 2.1. 환경/초기 설정

- `OPENAI_API_KEY` 환경 변수를 로드하여 API 키를 설정합니다. (보안을 위해 하드코딩 대신 환경 변수 사용)
- `openai.OpenAI()` 클라이언트 객체를 생성하여 API 호출에 재사용합니다.

#### 2.2. 파일 경로 상수

- 원본 뉴스 데이터 및 메타데이터 경로 (`EXCEL_PATH`)와 결과물 저장 경로 (`OUTPUT_PATH`)를 변수로 분리하여 재활용성을 높였습니다.

#### 2.3. 프롬프트 생성 함수 (`make_prompt`)

- 시스템 메시지를 제거하고 "금융 전문가" 페르소나를 부여하여 일관된 판단을 유도합니다.
- 출력 형식을 "예/아니오/알 수 없음"으로 지정하여 후처리를 단순화합니다.
- 기업명과 기간을 프롬프트에 주입하여 관련 질문을 구성합니다.

#### 2.4. GPT 호출 함수 (`analyze_company`)

- 지정된 OpenAI 모델(예: `gpt-4.1-nano-2025-04-14`)을 사용합니다.
- `temperature=0`으로 설정하여 결정론적이고 일관된 출력을 확보합니다.
- 응답의 첫 줄을 파싱하여 감성 점수(1: 긍정, -1: 부정, 0: 중립)로 매핑하고, 실패 시 0으로 처리합니다.
- 예외 처리를 통해 안정성을 확보합니다.

#### 2.5. Excel → DataFrame 로드

- `pandas.read_excel()`을 사용하여 Excel 파일을 DataFrame으로 로드합니다.
- 모든 열을 문자열로 읽어 데이터 깨짐을 방지하고, 빈 칸을 `""`으로 채워 루프가 중단되지 않도록 합니다.

#### 2.6. 메인 루프

- 뉴스 기사 제목과 정규화된 기업명 목록을 반복 처리합니다.
- 쉼표로 구분된 다중 기업을 분리하여 각각 GPT 호출을 수행합니다.
- 각 기업에 대한 감성 점수를 획득한 후 "기업명(점수)" 형태로 포매팅합니다.
- `time.sleep(1.1)`을 사용하여 요청 속도를 제어하고 Rate Limit을 회피합니다.

#### 2.7. 결과 저장

- 계산된 GPT 감성 점수를 새 컬럼("GPT\_기업별감성")으로 DataFrame에 추가합니다.
- `to_excel()`을 사용하여 결과 DataFrame을 지정된 경로에 저장합니다.

---

### 3\. 주목할 만한 설계 포인트

| 포인트                  | 이점                                        | 향후 개선 아이디어                                                  |
| :---------------------- | :------------------------------------------ | :------------------------------------------------------------------ |
| **프롬프트 엔지니어링** | 첫 줄 = 라벨, 두 번째 줄 = 근거 → 파싱 용이 | JSON 형식으로 출력 유도하여 안정성 향상                             |
| **오류 복원력**         | `try/except`로 각 기사/기업 단위 실패 로깅  | 실패 건 캐싱 또는 지수 백오프(exponential backoff) 재시도 로직 구현 |
| **속도 제어**           | `sleep(1.1)` 고정 딜레이                    | ① `async` + `max_concurrency` 활용 ② 토큰 잔량 체크 후 동적 지연    |
| **라벨 사전 매핑**      | 대소문자 불일치, 한·영 모두 수용            | 라벨 외 텍스트 판별 Regex 강화                                      |

---

---

## `simu.py`

뉴스 기사 기반 투자 전략(롱, 숏, 롱+숏)의 총 누적 수익률을 분석하고 시각화하는 시뮬레이션 코드입니다.

---

### 1\. 사용 기술 스택 (라이브러리/프레임워크)

| 범주            | 라이브러리                               | 주요 역할                                            |
| :-------------- | :--------------------------------------- | :--------------------------------------------------- |
| **데이터 처리** | `pandas`                                 | Excel → DataFrame 로딩, 전처리, 그룹 집계, 파일 저장 |
| **수치 연산**   | `NumPy`                                  | 벡터화된 수학·논리 연산 (`np.where`, `np.nan`)       |
| **시각화**      | `matplotlib`, `seaborn`                  | 누적 수익률·포지션 분포, 상관행렬 히트맵 생성        |
| **날짜 처리**   | `datetime`, `pandas.Timestamp`, `mdates` | 날짜 파싱, 범위 생성, 재표본화, X축 포맷팅           |
| **포맷터**      | `matplotlib.ticker.PercentFormatter`     | Y축을 % 단위로 표시                                  |

---

### 2\. 모듈·함수별 로직 흐름

| 단계                         | 함수                                                                   | 핵심 동작                                                                                                           |
| :--------------------------- | :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| **1. 데이터 로드**           | `load_data(file_path)` (경로 → DataFrame)                              | - Excel 파일 읽기\<br\>- 날짜형 컬럼 `datetime64` 변환\<br\>- GPT 점수를 sentiment 라벨링                           |
| **2. 개별 뉴스 수익률 계산** | `calculate_returns(df)` (DF → DF)                                      | - `tag1`, `tag2` 조합에 따라 진입·청산 가격 결정\<br\>- positive → `long_return`, negative → `short_return` 계산    |
| **3. 포트폴리오 구축**       | `implement_strategy(df)` (뉴스 DF → 포트폴리오 DF)                     | - 날짜 인덱스 전 범위 생성\<br\>- 각 거래일에 Long·Short 포지션 카운트 및 평균 수익률 기록\<br\>- 누적 수익률 계산  |
| **4. 통계 요약**             | `get_summary(series)` & `get_panelA_summary(df)`                       | - 평균, 표준편차, 사분위수 등 % 단위 요약\<br\>- Panel A: `daily_return`, `headline_length`, `GPT_SCORE` 3변수 요약 |
| **5. 시각화**                | `plot_cumulative_returns(portfolio)`\<br\>`plot_monthly_positions(df)` | - Long / Short / Long+Short 전략 누적 수익률 라인 차트\<br\>- 월별 Long·Short 포지션 건수 Stacked Bar               |
| **6. 메인 실행 흐름**        | `main()`                                                               | 1️⃣ Load → 2️⃣ Return 계산 → 3️⃣ Strategy 구축 → 4️⃣ Plot & Save ➕ 통계·상관관계 분석 & 파일 저장                      |

---

### 3\. 주요 출력 파일·그래프

| 파일/그래프                        | 내용                                                |
| :--------------------------------- | :-------------------------------------------------- |
| `cumulative_returns.png`           | 전략별 누적 수익률 (% 단위)                         |
| `monthly_positions.png`            | 월별 포지션 건수(롱·숏)                             |
| `long_short_portfolio_results.csv` | 일자별 포트폴리오 결과 테이블                       |
| `processed_news_data.csv`          | 원본 뉴스 + 계산된 수익률 컬럼                      |
| `cumulative_return_summary.csv`    | 롱·숏·롱+숏 누적 수익률 요약 통계                   |
| `correlation_matrix_heatmap.png`   | `daily_return`, 헤드라인 길이, GPT 점수 간 피어슨 r |
| `panelA_summary_statistics.csv`    | Panel A 요약 통계 (Table 형태)                      |

---

### 4\. 코드 설계상의 장점

- **모듈화**: 전처리, 계산, 시각화를 함수로 분리하여 재사용 및 테스트 용이성을 높였습니다.
- **결과 재현성**: 모든 중간 및 최종 산출물을 파일로 저장하여 추후 분석에 활용할 수 있습니다.
- **완결형 파이프라인**: `main()` 함수 한 번 실행으로 데이터 탐색(EDA)부터 전략 평가, 리포트 이미지 및 CSV 저장까지 일괄 수행됩니다.
- **누적/연율화 로직**: 실제 거래 발생 일자(`actual_days`)만을 기준으로 연율화하여 휴일이나 결측일로 인한 왜곡을 최소화했습니다.

---

---

## `market.py`

대형주, 중형주, 소형주 등 **규모별** 롱/숏/롱숏 투자 전략의 성과를 산출하고 시각화하며 저장하는 코드입니다. `simu.py`와 유사한 구조를 가지며, 시장 규모별 분석에 특화되어 있습니다.
(다른 뉴스별, sector별, 스타일별도 비슷함)

---

### 1\. 핵심 기술 스택 & 역할

| 범주          | 라이브러리                     | 주요 용도                                     |
| :------------ | :----------------------------- | :-------------------------------------------- |
| **데이터**    | `pandas`                       | CSV/Excel 로드, 그룹/피벗/리샘플링, 파일 저장 |
| **수치 연산** | `NumPy`                        | 벡터화 계산 (`np.where`, `np.sqrt`, `np.nan`) |
| **시각화**    | `matplotlib`, `seaborn`        | 라인/바 차트, 축 포맷터, 상관행렬 히트맵      |
| **날짜**      | `datetime`, `pandas.Timestamp` | 거래일 인덱스, 월/분기 재표본화               |
| **스타일**    | AppleGothic 폰트 설정          | macOS에서 한글 폰트 깨짐 방지                 |

---

### 2\. 함수별 로직 요약

| \#  | 함수 (입력 → 출력)                                                                    | 핵심 알고리즘 / 특징                                                                                                             |
| :-- | :------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `calculate_size_based_returns(df)` (뉴스 DF → (cumulative_returns, daily_returns))    | - `long_short_return` 자동 생성\<br\>- 규모구분/`current_date` 그룹 → 일별 평균 → 피벗\<br\>- 누적수익률: `(1+return).cumprod()` |
| 2   | `analyze_size_distribution(df)` (DF → (size_counts, daily_counts))                    | - 전체·일평균 종목 수로 거래 볼륨 진단                                                                                           |
| 3   | `plot_cumulative_returns(cum_df)` (누적수익률 DF → `matplotlib.figure`)               | - 모든 사이즈를 한 그래프에\<br\>- y축을 "%" 단위(`y-1`)로 포맷                                                                  |
| 4   | `calculate_performance_metrics(ret_df)` (일일 수익률 DF → 요약 DataFrame)             | - 연율화 수익률·변동성·Sharpe·최대 낙폭 계산\<br\>- 252 거래일/년 가정                                                           |
| 5   | `analyze_period_returns(cum_df, ret_df)` (누적·일일 DF → 요약 DF)                     | - 전체·월평균·분기평균 수익률 계산                                                                                               |
| 6   | `NEW calculate_size_based_cumulative(df)` (뉴스 DF → {'long', 'short', 'long_short'}) | - 롱·숏·롱숏 각각 누적수익률 계산\<br\>- 내부 헬퍼 `_pivot_daily(col)` 재사용                                                    |
| 7   | `NEW plot_size_long_short(cum_dict, save_dir)` (cum_dict → PNG 파일)                  | - 사이즈별로 개별 그림 생성\<br\>- 색상 고정(blue / red / green) 및 파일 자동 저장                                               |

---

### 3\. 메인 실행 흐름 (`if __name__ == "__main__":`)

1.  **데이터 로드 & 클렌징**:
    - `long_return`, `short_return`을 숫자형으로 변환하고 `fillna(0)` 처리합니다.
    - `long_short_return`을 즉시 합산합니다.
    - DataFrame의 `shape`와 규모구분 분포를 탐색적으로 확인합니다.
2.  **거래 규모 분석**: `analyze_size_distribution` 함수를 호출하여 거래 볼륨을 진단합니다.
3.  **기본 누적수익률 계산**: `calculate_size_based_returns` 함수를 호출하여 전체(Size-Weighted) 컬럼을 포함한 롱숏 합산 누적 수익률을 계산합니다.
4.  **성과 지표 및 기간별 통계**: `calculate_performance_metrics`와 `analyze_period_returns`를 호출하여 연율화 수익률, 변동성, 샤프 비율, 최대 낙폭 등 주요 성과 지표와 월/분기 평균 수익률을 계산합니다.
5.  **그래프 생성**:
    - `plot_cumulative_returns`를 사용하여 전체 사이즈에 대한 누적 수익률 그래프를 생성합니다.
    - `NEW plot_size_long_short`를 사용하여 사이즈별(대형/중형/소형) 롱/숏/롱숏 누적 그래프를 개별적으로 생성합니다.
6.  **파일 저장**:
    - 누적/일별 수익률 및 성과 지표 CSV 파일들을 저장합니다.
    - 생성된 그래프들을 PNG 형식으로 `figures` 폴더에 저장합니다.

---

### 4\. 산출물 예시

| 파일 내용                            | 내용                                    |
| :----------------------------------- | :-------------------------------------- |
| `size_based_cumulative_returns.csv`  | 각 날짜 × 사이즈별 누적 수익률          |
| `size_based_performance_metrics.csv` | 연율화 수익률·변동성·Sharpe·MDD         |
| `figures/cumulative_대형주.png` (등) | 대형·중형·소형별 롱/숏/롱숏 누적 그래프 |
| `cum_long_by_size.csv`               | 롱 전략 누적 수익률                     |
| `cum_short_by_size.csv`              | 숏 전략 누적 수익률                     |
| `cum_longshort_by_size.csv`          | 롱+숏 전략 누적 수익률                  |
