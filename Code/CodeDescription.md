# Can ChatGPT Forecast Returns in the Korean Stock Market?

**Multi-Dimensional Evidence from News-Based Long-Short Strategies**

This repository contains Python scripts that analyze news article texts to evaluate their impact on the Korean stock market and simulate various investment strategies based on these insights.

---

## `GPTScore.py`

This script uses a GPT model to generate sentiment scores (positive/negative/neutral) based on news article headlines and company names, and appends them to an Excel file.

### Technology Stack

| Category            | Library/Tool  | Purpose                                 |
| ------------------- | ------------- | --------------------------------------- |
| **Language**        | Python 3.x    | Main execution environment              |
| **API Client**      | `openai` SDK  | Call OpenAI Chat Completion API         |
| **Data Processing** | `pandas`      | Read/Write Excel as DataFrame           |
| **File I/O**        | `os`, `time`  | Load API keys, manage request intervals |
| **Format**          | Excel (.xlsx) | Store input and output data             |

### Code Workflow

- Load API key securely from environment.
- Generate prompt per article-company with consistent output structure.
- Use GPT API with deterministic settings.
- Handle errors gracefully; score as 0 if response fails.
- Store sentiment scores in Excel.

### Key Design Features

| Feature                | Benefit                                | Future Improvements                                          |
| ---------------------- | -------------------------------------- | ------------------------------------------------------------ |
| **Prompt Engineering** | Label in 1st line, reason in 2nd line  | Switch to JSON output format for stability                   |
| **Error Resilience**   | `try/except` block per article/company | Add caching and exponential backoff for retries              |
| **Speed Control**      | Fixed delay with `sleep(1.1)`          | Use async + rate limiting or token tracking for optimization |

---

## `simu.py`

Simulates total cumulative returns of long, short, and long-short strategies based on news sentiment.

### Technology Stack

| Category            | Library                 | Purpose                                              |
| ------------------- | ----------------------- | ---------------------------------------------------- |
| **Data Processing** | `pandas`                | Load Excel → DataFrame, preprocessing, export        |
| **Numerical Ops**   | `NumPy`                 | Vectorized calculations                              |
| **Visualization**   | `matplotlib`, `seaborn` | Cumulative returns, heatmaps, position distributions |
| **Date Handling**   | `datetime`, `mdates`    | Timestamp formatting, resampling                     |

### Workflow

- Load sentiment-tagged news data
- Calculate long/short return based on sentiment
- Build daily long/short/long-short portfolios
- Plot cumulative returns and monthly positions
- Output result CSVs and graphs

### Output Files

- `cumulative_returns.png`
- `monthly_positions.png`
- `long_short_portfolio_results.csv`
- `correlation_matrix_heatmap.png`

---

## `market.py`

Analyzes return performance of long, short, and long-short strategies by **market cap size** (large, mid, small).

### Technology Stack

| Category          | Library                        | Purpose                                      |
| ----------------- | ------------------------------ | -------------------------------------------- |
| **Data**          | `pandas`                       | Load and group data by size                  |
| **Computation**   | `NumPy`                        | Efficient return and volatility calculations |
| **Visualization** | `matplotlib`, `seaborn`        | Line/bar charts, correlation heatmaps        |
| **Date**          | `datetime`, `pandas.Timestamp` | Indexing and resampling                      |

### Execution Flow

1. Load and preprocess return columns
2. Compute long-short return by size category
3. Plot cumulative returns by size (large, mid, small)
4. Generate summary metrics: Sharpe, volatility, MDD, etc.
5. Save graphs and CSVs

### Output Examples

- `size_based_cumulative_returns.csv`
- `size_based_performance_metrics.csv`
- `figures/cumulative_largecap.png`
- `cum_long_by_size.csv`
- `cum_short_by_size.csv`
- `cum_longshort_by_size.csv`

---

For questions, improvements, or collaboration inquiries, feel free to open an issue or pull request!
