import pandas as pd

# 엑셀 불러오기
# 파일명은 실제로 맞게 수정하세요
df = pd.read_excel("/Users/imdonghyeon/Desktop/Quantlab/merged_profo2.xlsx")

# '제목' + 'GPT_SCORE' 기준으로 중복 제거 → 각 조합당 첫 번째만 남김
df_dedup = df.drop_duplicates(subset=['제목', 'GPT_SCORE'])

# 결과 저장 (선택)
df_dedup.to_excel("뉴스_중복제거_제목_GPT별.xlsx", index=False)

# 확인
print(df_dedup.head())
