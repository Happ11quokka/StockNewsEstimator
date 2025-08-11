import pandas as pd
import glob
import os

# Excel 파일들이 저장된 폴더 경로 지정
# 여기를 실제 폴더 경로로 바꿔주세요.
input_folder = '/Users/imdonghyeon/Desktop/Quantlab/news_tags'
output_file = '/Users/imdonghyeon/Desktop/Quantlab/merged_profo2.xlsx'

excel_files = sorted(glob.glob(os.path.join(input_folder, '*.xlsx')))

merged_df = pd.DataFrame()

for i, file in enumerate(excel_files):
    if i == 0:
        df = pd.read_excel(file)  # 첫 파일: 헤더 포함
    else:
        df = pd.read_excel(file, skiprows=1, header=None)  # 이후 파일: 헤더 제거
        df.columns = merged_df.columns  # 열 이름 통일
    merged_df = pd.concat([merged_df, df], ignore_index=True)

merged_df.to_excel(output_file, index=False)
print(f"모든 파일 병합 완료! 저장 위치: {output_file}")
