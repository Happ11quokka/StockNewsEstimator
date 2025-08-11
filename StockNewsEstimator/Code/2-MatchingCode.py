import json
from pykrx import stock

# 1. mentioned_companies.txt
with open("/Users/imdonghyeon/Desktop/Quantlab/Normailized List/mentioned_companies.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 숫자 제거하고 기업명만 추출
company_list = []
for line in lines:
    line = line.strip()
    if line:
        parts = line.split()
        if len(parts) >= 2:
            name = " ".join(parts[1:])
            company_list.append(name)
        else:
            company_list.append(line)

# 2. 전체 상장기업 리스트 가져오기
tickers = stock.get_market_ticker_list(market="ALL")
name_to_code = {}
for ticker in tickers:
    name = stock.get_market_ticker_name(ticker)
    name_to_code[name] = ticker

# 3. Matching
result = {}

for company in company_list:
    if company in name_to_code:
        result[company] = name_to_code[company]
    else:
        result[company] = None

with open("matched_companies.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("JSON 저장 완료: matched_companies.json")
