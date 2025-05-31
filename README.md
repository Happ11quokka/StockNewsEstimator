# Can ChatGPT Forecast Returns in the Korean Stock Market? Multi-Dimensional Evidence from News-Based Long-Short Strategies

# **Research Background**

With the growing popularity of Large Language Models (LLMs) like ChatGPT, these tools have become integral to daily life, assisting in tasks ranging from academic assignments to routine activities. This widespread adoption naturally raises questions about their potential application in financial forecasting, specifically stock market prediction.

While prior studies have explored the effectiveness of LLMs in markets like the United States, their predictive capabilities within the Korean stock market remain relatively unexplored. This research addresses this gap by evaluating the predictive power of LLMs within the Korean financial context.

---

# **Abstract**

This research is inspired by the pioneering work of Lopez-Lira and Tang (2023), who gained significant attention for applying ChatGPT-based sentiment analysis to predict stock price movements from news articles. Building upon this foundation, we utilize the advanced GPT-4.1 Nano model to perform sentiment analysis on Korean news articles and evaluate its predictive capability in the Korean stock market.

We undertake a multi-dimensional performance evaluation, examining not only overall return metrics but also detailed returns segmented by news type, firm size, investment style, and industry sector.

---

## **Core Components**

1. **ChatGPT 4.1-Nano (LLM-based approach)**: Leveraging LLMs’ language comprehension to interpret financial news.
2. **Sentiment Analysis of News Headlines**: Categorizing the sentiment of headlines to forecast their impact on stock prices.
3. **Application to the Korean Stock Market**: Extending LLM-based sentiment analysis methodologies to the Korean market.
4. **Multi-dimensional Performance Evaluation**: Evaluating predictive performance across multiple dimensions, including overall returns, news categories, firm size, investment style, and industry sectors.

---

# **Data Collection and Preprocessing**

## **Data Collection**

- **News Data**: Approximately 500,000 articles from *Maeil Business Newspaper*, sourced via the BigKinds database (2022 to March 2025).
- **Stock Price Data**: Daily open and close prices obtained from FnGuide.
- **Firm Size Classification** (FnGuide market cap criteria):
    - **Large-cap**: > KRW 1 trillion
    - **Mid-cap**: KRW 300 billion – KRW 1 trillion
    - **Small-cap**: < KRW 300 billion
- **Investment Style Classification**: Value/Growth distinctions sourced from KODEX.
- **Industry Classification**: Provided by the Korea Exchange (KRX) Information Data System.

## **Data Preprocessing Workflow**

- **Data Cleaning**: Exclusion of entities not listed in FnGuide (e.g., REITs, KONEX firms).
1. **Timestamp Extraction**:
    - Precise publication timestamps collected via URL crawling, enabling news categorization.
2. **News Categorization**:
    - **PRE (Pre-market)**
    - **IN (Intraday)**
    - **AFTER (Post-market)**
    - **DAY-OFF (Holidays)**
3. **Noise Removal**:
    - Removal of irrelevant metadata (e.g., journalist names).
    - Focused on articles tagged “Economy”
4. **Company Name Refinement**:
    - GPT-4.1 Nano utilized to filter non-listed entities.
    - GPT-3.5 Turbo leveraged to enrich company descriptions using FnGuide metadata.
5. **Entity Matching**:
    - Combined semantic embeddings and GPT-4-based approaches to accurately match news-mentioned companies to FnGuide stock data.

---

# **GPT Sentiment Scoring Process**

1. **Model Selection**:
    - GPT-4.1-Nano-2025-04-14
2. **Sentiment Evaluation**:
    - Sentiment assessed for each news headline per company.
    - Scores assigned: **+1** (positive), **1** (negative), **0** (neutral/irrelevant).
3. **Aggregate Company Sentiment**:
    - Average sentiment score computed for companies mentioned in multiple headlines daily.

---

# **Trading Strategy and Return Calculation**

1. **Position Allocation**:
    - **Positive sentiment (> 0)**: Equal-weighted **Long** positions.
    - **Negative sentiment (< 0)**: Equal-weighted **Short** positions.
    - **Neutral sentiment (0)**: Excluded from portfolio.
2. **Portfolio Construction**:
    - Daily rebalancing based on sentiment scores.
3. **Trading Execution by News Timing**:

| **News Timing** | **Long Strategy** | **Short Strategy** |
| --- | --- | --- |
| **PRE** | Buy at open, sell at close (same day) | Short at open, cover at close (same day) |
| **IN** | Buy at close, sell at close (next day) | Short at close, cover at close (next day) |
| **AFTER** | Buy at next day’s open, sell at next close | Short at next day’s open, cover at next close |
| **DAY-OFF** | Buy at next trading day’s open, sell at close | Short at next trading day’s open, cover at close |

---

# **Detailed Analysis Methodology**

1. **Performance by News Category**:
    - Evaluated sentiment-based returns segmented by news category.
2. **Performance by Firm Size**:
    - Analysis of predictive accuracy for large-, mid-, and small-cap firms.
3. **Performance by Investment Style**:
    - Separate evaluation for **value**, **growth**, and **hybrid** stocks based on KODEX classifications.
4. **Performance by Industry Sector**:
    - Analysis across KRX-defined industry sectors to assess predictive consistency.

---

> 📩 **Dataset Access**
Researchers interested in accessing the dataset used in this study may contact the author at **limdonghyun@hanyang.ac.kr.** Due to its large size, the dataset is not hosted on GitHub but will be shared upon request.
>