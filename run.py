# TODO:
# 로그인시 pc 웹 사이트에서 처리가 어려율 경우 -> 모바일 로그인 진입
# 모듈 가져오기
from selenium import webdriver as wd
from bs4 import BeautifulSoup as bs
# for waiting
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

from DBMgr import DBHelper as DB
from tour import TourInfo

# 사전에 필요한 정보를 로드 -> 디비 혹은 쉘, 배피 파일에서 인자로 받아서 세팅
db = DB()
main_url = 'https://tour.interpark.com/'
keyword = '로마'

# 상품 정도를 담는 리스트 (TourInfo class 리스트)
tour_list = []

# 드라이버 로드
driver = wd.Chrome(executable_path='chromedriver.exe')

# 차후 -> 옵션 부여하여 (프록시, 에이전트 조작, 이미지를 배제)
# 클롤링을 오래 돌리면 -> 임시파일들이 쌓인다!! -> 템프 파일 삭제

# 사이트 접속( (Get)
driver.get(main_url)

# 검색창을 찾아서 검색어 입력
# id : SearchGNBText
driver.find_element_by_id('SearchGNBText').send_keys(keyword)
# 수정할 경우 => 뒤에 내용이 붙어버림 => .clear() -> send_key()


# 검색 버튼 클릭
driver.find_element_by_css_selector('.search-btn').click()

# 잠시 대기 => 페이지가 로드되고 즉각적으로 데이트를 획득하는 행위는 자제
# 명시적 대기 => 특정 요소가 로케이트 될 때까지 대기
try:
    element = WebDriverWait(driver, 10).until(
        # 지정한 한개 요소가 올라오면 웨이트 종료
        EC.presence_of_element_located((By.CLASS_NAME, 'oTravelBox'))
    )

except Exception as e:
    print('오류 발생', e)

# 암묵적 대기 => DOM이 다 로드 될때까지 대기 하고 먼저 로드되면 바로 진행
# 요소ㅡㄹ 찾을 특정 시간 동안 DOM 풀링을 지시
driver.implicitly_wait(10)
# 절대적 대기 => time.sleep(10) -> 

# 더보기 눌러서 => 게시판 진입
driver.find_element_by_css_selector('.oTravelBox>.boxList>.moreBtnWrap>.moreBtn').click()


# 게시판에서 데이터를 가져올때 데이터가 많으면 세션(혹시 로그인을 해서 접근하는 사이트일 경우) 관리 => 특정단위별로 로그아웃 로그인 계속 시도
# 특정 게시물이 사라질 경우 => 팝업 발생 => 팝업 처리 검토
# 게시판 스캔시 => 임계점을 모름!!
# 게시판을 스캔 => 메타 정보 획득 => loop 돌려 일괄적으로 방문 접근 처리

# searchModule.SetCategoryList(1, '') 스크립트 실행
for page in range(1, 2): #21):
    try:
        # 자바스크립트 구동하기
        driver.execute_script("searchModule.SetCategoryList(%s, '')" % page)
        time.sleep(2)
        print("{} 페이지 이동".format(page))
        #######################################
        # 여러 사이트에서 정보를 수집할 경우 공통 정보 정의 단계 필요
        # 상품명 / 코멘트 / 기간 1, 기간 2 / 가격 / 평점 / 썸네일 / 링크(상품 상세 정보)
        boxItems = driver.find_elements_by_css_selector('.panelZone>.oTravelBox>.boxList>li')
        # 상품 하나 하나 접근
        for li in boxItems:
            # 이미지를 링크값을 사용할 것인가? 
            # 직접 다운로드 해서 우리서버에 업로드(ftp) 할것인가?
            print("썸네일 : ", li.find_element_by_css_selector('img').get_attribute('src'))
            print("링크 : ",   li.find_element_by_css_selector('a').get_attribute('onclick'))
            print("상품명 : ", li.find_element_by_css_selector('h5.proTit').text)
            print("코멘트 : ", li.find_element_by_css_selector('.proSub').text)
            print("가격 : ",   li.find_element_by_css_selector('.proPrice').text)
            for info in li.find_elements_by_css_selector('.info-row .proInfo'):
                print(info.text)
            print('='*50)

            # 데이터 모음
            # li.find_elements_by_css_selector('.info-row .proInfo')[1] -> 뽑을 때부터 신경써야한다.
            # 데이터가 부족하거나 없을 수도 있으므로 직접 인덱스로 표현은 위험
            obj = TourInfo(
                li.find_element_by_css_selector('h5.proTit').text,
                li.find_element_by_css_selector('.proPrice').text,
                li.find_elements_by_css_selector('.info-row .proInfo')[1].text,
                li.find_element_by_css_selector('a').get_attribute('onclick'),
                li.find_element_by_css_selector('img').get_attribute('src')
            )
            tour_list.append(obj)
    except Exception as e1:
        print('오류', e1)


print(tour_list, len(tour_list))

# 수집한 정보 개수를 루프 => 페이지 방문 => 콘텐츠 획득(상품 상세 정보) => DB
for tour in tour_list:
    # tour is TourInfo
    print("tour list data type is ", type(tour))
    # 링크 전처리 >>> 전처리 하지 않으면 새창이 계속 열려 리소스를 잡아 먹는다.
    # 부해
    arr = tour.link.split(',')
    if arr:
        # 대체
        link = arr[0].replace('searchModule.OnClickDetail(','')
        # 슬라이싱
        detail_url = link[1:-1]
        # 상세 페이지 이동 :  full url 값 필요
        driver.get(detail_url)
        time.sleep(2)

        # 현재 페이지를 beautiful soup 의 DOM으로 구성
        soup = bs(driver.page_source, 'html.parser')
        # 현재 상세 정보 페이지에서 스케쥴 정보 획득
        # TODO:
        # data type, content style 확인해서 전처리가 필요하다.
        data = soup.select('.recom-schedule')
        print("soup data is ", data[0].contents)

        # DB 입력 => pymysql
        # 콘텐츠 내용에 따라서 전처리
        db.db_insertCrawlingData(
            tour.title,
            tour.price,
            tour.area,
            data[0].contents,
            keyword )

print("Complete")

# 종료
driver.close()
driver.quit()
import sys
sys.exit()