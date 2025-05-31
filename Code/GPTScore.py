import os
import openai
import pandas as pd
import time

# 환경 변수에서 API 키 불러오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 파일 경로 설정
EXCEL_PATH = "/Users/imdonghyeon/Desktop/Quantlab/processed_economy/updated_time_normalized/NewsResult_20220101-20220131.xlsx"
OUTPUT_PATH = "NewsResult_20220101-20220131_with_score.xlsx"


# 프롬프트
def make_prompt(title, company, period="1일"):
    return f"""
이전의 모든 지침은 잊어버리세요. 자신이 금융 전문가라고 생각하세요. 
당신은 주식 추천 경험이 있는 금융 전문가입니다. 
헤드라인 내용이 좋은 뉴스이면 "예"라고 답하고 나쁜 뉴스이면 "아니오", 불확실하면 "알 수 없음"이라고 답하세요. 
그리고, 다음 줄에 짧고 간결한 한 문장으로 자세히 설명하세요. 

이 헤드라인이 {period} 동안 {company}의 주가에 좋은가요, 나쁜가요?

헤드라인: {title}
"""


# GPT 분석
def analyze_company(title, company):
    prompt = make_prompt(title, company)
    print(f"\n[프롬프트]\n{prompt.strip()}\n")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        label = content.split("\n")[0].strip().upper()

        print(f"GPT 응답:\n{content}")
        print(f"감성 해석 결과: {company} → {label}")

        return {
            "예": 1, "YES": 1,
            "아니오": -1, "NO": -1,
            "알 수 없음": 0, "UNKNOWN": 0
        }.get(label, 0)

    except Exception as e:
        print(f"GPT 분석 실패: {company} → {e}")
        return 0


df = pd.read_excel(EXCEL_PATH, dtype=str)
titles = df["제목"].fillna("")
companies_list = df["기관(정규화)"].fillna("")

# 결과 저장 열
results = []

# 한 기사씩 분석 루프
for idx, (title, company_str) in enumerate(zip(titles, companies_list)):
    companies = [c.strip() for c in company_str.split(",") if c.strip()]
    row_result = []

    print(f"\n🚀 [{idx+1}/{len(df)}] 뉴스 제목 분석 시작: '{title}'")

    for comp in companies:
        score = analyze_company(title, comp)
        row_result.append(f"{comp}({score})")
        time.sleep(1.1)

    results.append(", ".join(row_result))
    print(f"완료 -> 결과: {results[-1]}")

# 새 열로 추가
df["GPT_기업별감성"] = results

df.to_excel(OUTPUT_PATH, index=False)
print(f"\n전체 분석 완료! 결과 저장됨 → {OUTPUT_PATH}")
