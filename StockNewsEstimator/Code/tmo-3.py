import pandas as pd

# 엑셀 파일 불러오기
df = pd.read_excel(
    "/Users/imdonghyeon/Desktop/Quantlab/merged_profo2.xlsx")  # 실제 파일 경로로 수정

# 1) 기업명이 비어 있지 않고
# 2) GPT_SCORE가 0이 아닌 경우만 남기기
df_cleaned = df[
    df['기업명'].notna() &
    (df['기업명'].astype(str).str.strip() != '') &
    (df['GPT_SCORE'] != 0)
]
# 결과 저장 (선택)
df_cleaned.to_excel(
    "/Users/imdonghyeon/Desktop/Quantlab/merged_profo2.xlsx", index=False)

# 결과 확인
print(f"원래 행 수: {len(df)} → 정제 후: {len(df_cleaned)}")
