import requests
import re
import pandas as pd
import io
from qgis.core import QgsVectorLayer, QgsProject
import os

# 1. 기상청 API URL 설정 및 데이터 수집
# 요청할 날짜와 관측지점 코드를 포함한 URL을 설정
date = '20241119'  # 데이터를 수집할 날짜
url = f'https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd.php?tm={date}&stn=252:165:164:266:174:168:261:156&disp=0&help=1&authKey=iMLKySS5RwSCyskkuXcE2A'

# API 요청 및 응답 데이터 수집
response = requests.get(url)
response_text = response.text

# 2. 응답 텍스트에서 데이터 시작 부분(YYMMDD)을 기준으로 이전 불필요한 텍스트 제거
# 응답 텍스트에는 메타데이터와 같이 불필요한 정보가 포함되어 있습니다.
# 필요한 데이터는 "YYMMDD"라는 문자열 이후부터 시작되므로, 그 이전의 내용을 제거합니다.
modified_text = re.sub(r'^.*?(?=YYMMDD)', '', response_text, flags=re.DOTALL)

# 2-1. 정규식 상세 설명:
# - '^.*?(?=YYMMDD)': 문자열의 시작부터 "YYMMDD"가 나타나는 위치 직전까지 매칭
# - 'flags=re.DOTALL': 줄바꿈 문자를 포함하여 모든 문자를 매칭할 수 있도록 설정
# 결과적으로 "YYMMDD" 이전의 텍스트는 제거되고, 이후 데이터만 남게 됩니다.

# 3. 텍스트 데이터를 DataFrame으로 변환
# 띄어쓰기를 구분자로 데이터를 DataFrame으로 변환
df = pd.read_csv(io.StringIO(modified_text), delim_whitespace=True)

# 4. 데이터 필터링 및 열 정리
# 사용할 관측지점 코드 리스트를 정의
selected_stn = ['156', '165', '168', '174', '252', '261', '266']
df_filtered = df[df['STN'].isin(selected_stn)]  # 특정 관측지점 코드만 필터링

# 필요한 열만 선택하고 한글로 열 이름을 변경
df_selected = df_filtered[['YYMMDD', 'STN', 'TA', 'TA.1', 'TA.3', 'RN', 'SD.2']].rename(columns={
    'YYMMDD': '일자',           # 날짜
    'STN': '관측지점 코드',       # 관측소 코드
    'TA': '평균 기온',           # 평균 기온
    'TA.1': '최고 기온',          # 최고 기온
    'TA.3': '최저 기온',          # 최저 기온
    'RN': '강수량(mm)',          # 강수량
    'SD.2': '강설량(cm)'         # 강설량
})

# 시도 열 추가: 모든 관측지점은 전라남도에 속한다고 가정
df_selected.insert(1, '시도', '전라남도')

# 강수량과 강설량에서 -9.0 값을 결측치를 나타내는 '-'로 변경
df_selected['강수량(mm)'] = df_selected['강수량(mm)'].astype(str).replace('-9.0', '-')
df_selected['강설량(cm)'] = df_selected['강설량(cm)'].astype(str).replace('-9.0', '-')

# 관측지점 코드에 따른 관측지점 이름 매핑
location_map = {
    '252': '전남 영광', '165': '전남 목포', '164': '전남 무안', '266': '전남 광양',
    '174': '전남 순천', '168': '전남 여수', '261': '전남 해남', '156': '광주광역시',
}
df_selected['관측지점'] = df_selected['관측지점 코드'].astype(str).map(location_map)

# 법정동 시군구 코드 추가: 관측지점에 매핑된 코드 부여
region_code_map = {
    '252': '46820',  # 전남 영광
    '165': '46830',  # 전남 목포
    '164': '46840',  # 전남 무안
    '266': '46770',  # 전남 광양
    '174': '46750',  # 전남 순천
    '168': '46730',  # 전남 여수
    '261': '46710',  # 전남 해남
    '156': '29000',  # 광주광역시
}
df_selected['법정동 시군구 코드'] = df_selected['관측지점 코드'].astype(str).map(region_code_map)

# '관측지점' 열을 '관측지점 코드' 뒤로 이동
df_selected.insert(df_selected.columns.get_loc('관측지점 코드') + 1, '관측지점', df_selected.pop('관측지점'))

# 5. CSV 파일 저장
# 파일 저장 경로 설정
csv_path = r'C:\_jupyter_notebook\observations.csv'

# DataFrame을 CSV 파일로 저장 (UTF-8 인코딩)
df_selected.to_csv(csv_path, index=False, encoding='utf-8-sig', sep=',')

# 저장 성공 여부 확인
if not os.path.exists(csv_path):
    print(f"CSV 파일이 저장되지 않았습니다: {csv_path}")
else:
    print(f"CSV 파일이 저장되었습니다: {csv_path}")

# 6. QGIS에 CSV 레이어 추가
# QGIS에서 CSV 파일을 레이어로 추가할 URI 설정
csv_layer_uri = f"file:///{csv_path}?delimiter=,&crs=EPSG:4326"
csv_layer = QgsVectorLayer(csv_layer_uri, "관측지점 데이터", "delimitedtext")

# 레이어 유효성 확인 후 QGIS 프로젝트에 추가
if not csv_layer.isValid():
    print("CSV 레이어를 불러오지 못했습니다. 파일 경로와 설정을 확인하세요.")
else:
    QgsProject.instance().addMapLayer(csv_layer)
    print("CSV 레이어가 성공적으로 추가되었습니다.")