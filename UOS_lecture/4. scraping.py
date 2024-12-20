import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import urllib3
from sqlalchemy import create_engine

# 1. HTTPS 경고 메시지 비활성화
# SSL 인증서 경고를 무시하기 위해 urllib3의 InsecureRequestWarning을 비활성화합니다.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 2. 광주광역시 서구 게시판 데이터를 크롤링하는 함수 정의
def fetch_gwangju_seogu():
    try:
        # 2-1. 광주광역시 서구 게시판 URL과 요청 헤더 설정
        url = "https://www.seogu.gwangju.kr/board.es?mid=a10801000000&bid=0034&act=listC&gon=C"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # 2-2. HTTP GET 요청으로 웹 페이지 내용 가져오기
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # 응답 코드가 200이 아닐 경우 예외 발생
        
        # 2-3. BeautifulSoup 객체 생성
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 2-4. 어제 날짜를 생성 (형식: YYYY-MM-DD)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 2-5. 데이터를 저장할 리스트 초기화
        data = []

        # 2-6. 게시판의 <tbody> 내 모든 <tr> 요소 탐색
        rows = soup.find("tbody").find_all("tr")
        for row in rows:
            # 게시글의 등록일 추출 (aria-label 속성을 기준으로 탐색)
            date_tag = row.find("td", attrs={"aria-label": "등록일"})
            if date_tag:
                # 등록일 텍스트에서 불필요한 공백 제거 및 형식 변경
                date = date_tag.get_text(strip=True).replace("/", "-")
                
                # 게시글 제목과 링크 추출
                link_tag = row.find("a")
                if link_tag and date == yesterday:  # 등록일이 어제 날짜와 일치할 경우
                    title = link_tag.get_text(strip=True)  # 게시글 제목
                    relative_link = link_tag.get("href")  # 상대 경로 링크
                    # 상대 경로를 절대 경로로 변환
                    full_link = f"https://www.seogu.gwangju.kr{relative_link}" if relative_link else None
                    # 데이터 리스트에 추가
                    data.append({"제목": title, "링크": full_link, "작성일": date, "지역": "광주광역시 서구"})

        # 2-7. 데이터가 없을 경우 출력 메시지
        if not data:
            print("광주광역시 서구: 어제 날짜에 해당하는 데이터가 없습니다.")
        
        # 크롤링된 데이터를 DataFrame으로 반환
        return pd.DataFrame(data)
    
    except Exception as e:
        # 크롤링 실패 시 예외 메시지 출력
        print(f"광주광역시 서구: 크롤링 실패 - {e}")
        return pd.DataFrame()  # 실패 시 빈 DataFrame 반환

# 3. 광주광역시 서구 데이터를 크롤링하여 DataFrame으로 저장
df_seogu = fetch_gwangju_seogu()

# 4. PostgreSQL 데이터베이스 연결 설정
# SQLAlchemy를 사용하여 PostgreSQL 데이터베이스 연결
engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')

# 5. DataFrame 데이터를 PostgreSQL 테이블에 삽입
# DataFrame 데이터를 'nb_bul_b' 테이블에 추가합니다.
# 테이블이 이미 존재할 경우 데이터를 추가(append)하며, 기존 인덱스를 저장하지 않습니다.
if not df_seogu.empty:  # DataFrame이 비어있지 않을 경우에만 데이터 삽입
    df_seogu.to_sql('nb_bul_b', engine, if_exists='append', index=False)
    print("데이터가 nb_bul_b 테이블에 성공적으로 삽입되었습니다.")
else:
    print("삽입할 데이터가 없습니다.")