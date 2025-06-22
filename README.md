# Can ChatGPT Forecast Returns in the Korean Stock Market?

## Multi-Dimensional Evidence from News-Based Long-Short Strategies

### Project Overview

Before introducing the project, I would like to express my sincere gratitude to Dr. Sungwoo Park and Professor Hyoung-Goo Kang for their invaluable guidance and support throughout the semester.

This project explores the viability of using a Large Language Model (LLM), specifically GPT-4.1 Nano, to predict stock returns in the Korean market through news-based sentiment analysis. Inspired by recent studies in the U.S. (e.g., Lopez-Lira and Tang, 2023) that utilized ChatGPT to analyze news sentiment for stock prediction, we apply a similar approach to Korean financial news. We collected a comprehensive dataset of Korean news articles and stock prices, developed a sentiment-scoring mechanism using GPT-4.1 Nano, and designed long-short trading strategies based on these sentiment signals. The performance of these strategies is evaluated across multiple dimensions – including different news categories, company sizes, investment styles, and industry sectors – to identify where the LLM-driven approach is most effective. The goal is to assess whether AI-based sentiment analysis can offer predictive power in the Korean stock market and how its efficacy varies in a multi-dimensional context.

## Data

### News Data

We sourced approximately 500,000 Korean news articles from BigKinds (a public news database) focusing on the Maeil Business Newspaper (매일경제) from 2022 through March 2025. These articles were primarily in the economics/business domain and include metadata such as publication date and category. We particularly filtered for news categorized under economy/finance to ensure relevance to stock market movements. Each article’s headline and timestamp were used for sentiment analysis.

### Stock Data

We obtained daily stock price data from FnGuide, including daily open and close prices for all stocks listed on KOSPI and KOSDAQ (the main Korean stock exchanges). This allows us to quantify stock return movements. By aligning news timestamps with stock price data, we can analyze how news sentiment corresponds to actual stock performance following the news release.

### Market Cap Groups

Companies were classified by market capitalization to examine size effects:

- **Large-cap**: Market cap ≥ 1 trillion KRW (approximately \$1B USD).
- **Mid-cap**: 300 billion ≤ Market cap < 1 trillion KRW.
- **Small-cap**: Market cap < 300 billion KRW.

This grouping follows FnGuide’s criteria and lets us test if the strategy performs differently for large, medium, or small companies.

### Investment Style Categories

We used the classification from KODEX (an index provider) to label each stock as Value, Growth, or Mixed (Blend):

- **Growth stocks** are those oriented towards high growth metrics.
- **Value stocks** are those appearing undervalued based on fundamentals.
- **Mixed** have characteristics of both.

This allows analysis of whether the sentiment strategy works better for growth-oriented companies versus value-oriented ones.

### Sector Classification

Stocks were also grouped into industry sectors using the Korea Exchange (KRX) sector scheme (26 sectors, such as Finance, Chemicals, IT, Retail, etc.). This enables a sector-by-sector performance analysis to see if news sentiment is more predictive in certain industries (e.g., tech vs. utilities).

## Sentiment Analysis with GPT-4.1 Nano

We employed GPT-4.1 Nano – a variant of the GPT-4 LLM – to conduct sentiment analysis on news headlines. The model was used to determine whether a given news headline about a company conveys a positive, negative, or neutral/irrelevant sentiment regarding that company’s stock.

- **Prompt Design**: We crafted a specialized prompt (in Korean) to guide GPT-4.1 Nano’s analysis. The prompt instructed the model to “act as a financial expert” and evaluate if a news headline is good or bad for a company’s stock price, responding with “예” (yes) for positive news, “아니오” (no) for negative news, or “알 수 없음” (unknown) for neutral/unclear cases. The model was also asked to provide a brief explanation on the next line.
- **Scoring Scheme**: The textual output was mapped to numeric sentiment scores: +1 (yes), -1 (no), 0 (unknown). If multiple articles about the same company were published in one day, we averaged their scores.
- **LLM Choice**: GPT-4.1 Nano was chosen for its nuanced understanding of financial text. Earlier models often overfit obvious sentiment words, but GPT-4.1 Nano provided context-sensitive interpretations, aligning with prior research (e.g., Lopez-Lira & Tang, 2023).

## Data Preprocessing

- Filtered out unlisted entities and irrelevant sectors.
- Crawled full article URLs to extract precise publication times and classified them as PRE, IN, AFTER, or DAY-OFF.
- Removed reporter names and non-content metadata.
- Applied GPT-4.1 and GPT-3.5 for company name/entity recognition and ticker alignment using semantic similarity.

## Long-Short Trading Strategy

- **Position Rules**:

  - Sentiment > 0 → Long
  - Sentiment < 0 → Short
  - Sentiment = 0 → No trade

- **Rebalancing**: Performed daily.
- **Timing**:

  - PRE → Trade open to close same day
  - IN → Trade next day close to close
  - AFTER/DAY-OFF → Next day open to close

- **Holding Period**: 1 day (short-term)
- **Return Calculation**: Based on daily changes, using appropriate open/close prices depending on timing.

## Portfolio Methodologies

- **Single Position**: No market exposure hedging.
- **Delta-Neutral**: Equal long/short capital allocation daily. Returns = 0.5 \* (avg. long return) + 0.5 \* (avg. short return)

## Experimental Results

### By News Category

- **Best**: General Economics (+118.7%), Retail (+79%), Finance/Investing (+53%)
- **Worst**: Resources (-53.8%), Real Estate (-42.6%), International (-26%)

### By Company Size

- **Large-Cap**: +26% (delta-neutral); best on short-side.
- **Mid-Cap**: +41.99% (delta-neutral); strong alpha.
- **Small-Cap**: -28.7% (delta-neutral); high volatility, low signal quality.

### By Investment Style

- **Growth**: +54.4% (delta-neutral); best shorting opportunities.
- **Value**: -8.5% (delta-neutral); underperforms.
- **Mixed**: +59.9% (delta-neutral); best Sharpe ratio (\~1.22).

### By Sector

- **Best Sectors (Delta-Neutral)**: Chemicals (+106.7%, Sharpe 1.26), Textiles, Insurance, Construction, Retail
- **Worst**: General Services (-70.2%), Utilities, Paper/Wood

## Key Performance Highlights

- **Naive all-news strategy** = near-zero gain
- **Targeted strategies** (filtered by category/sector) = strong alpha
- **Delta-neutral portfolios** outperformed raw long/short setups
- **Short-side predictive power** generally higher than long-side
- **High Sharpe** in filtered portfolios (\~1.1–1.3)
- **Risk Management** is essential to avoid high drawdowns in weak sectors
- **LLM Nuance**: GPT-4.1 showed value even when linear correlation with returns was low – indicating context-aware forecasting power

## References

1. Lopez-Lira, A., & Tang, Y. (2023). _Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models_. SSRN Paper No. 4412788.
2. KakaoBank Tech Blog. (2024). _ChatGPT와 주가 예측: 대형 언어 모델은 주가를 맞출 수 있을까?_

---

For further inquiries, contact limdonghyun@hanyang.ac.kr. For more details, please refer to the full Korean report.

---

If you require access to the detailed dataset, please contact me directly. (Note: the dataset is large—approximately 7GB in a ZIP file.)
