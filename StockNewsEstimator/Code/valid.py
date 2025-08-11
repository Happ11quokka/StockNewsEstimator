import pandas as pd

# 엑셀 파일 불러오기
df = pd.read_excel(
    "/Users/imdonghyeon/Desktop/Quantlab/final_수정/adjustedStock.xlsx")  # 파일명에 맞게 수정

# Symbol 기준으로 작업
date_columns = df.columns[6:]  # G열부터가 날짜라고 가정

# 날짜별로 유효한 Symbol 수 세기
date_symbol_counts = {}

for date in date_columns:
    valid_rows = df[df[date].notna()]         # 해당 날짜에 값이 있는 행만 필터링
    unique_symbols = valid_rows['Symbol'].nunique()  # Symbol 기준 고유 기업 수
    date_symbol_counts[date] = unique_symbols

# 가장 많은 Symbol 수를 가진 날짜 찾기
max_count = max(date_symbol_counts.values())
max_dates = [date for date, count in date_symbol_counts.items()
             if count == max_count]

# 출력
print(f"가장 많은 Symbol을 가진 날짜 (총 {max_count}개 기업):")
for date in max_dates:
    print(date)
