"""
웹 스크래핑 모듈
법령 정보 웹사이트에서 데이터를 수집하는 모듈
"""

import logging
import time
from typing import List, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawScraper:
    """법령 정보 웹 스크래핑 클래스"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        초기화
        
        Args:
            headless: 브라우저를 백그라운드에서 실행할지 여부
            timeout: 웹 요소 대기 시간 (초)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Chrome WebDriver 설정"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Chrome 옵션 설정
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(10)
            return driver
        except WebDriverException as e:
            logger.error(f"Chrome WebDriver 설정 실패: {e}")
            raise
            
    def scrape_law_content(self, url: str, max_retries: int = 3) -> Optional[Tuple[List, List]]:
        """
        법령 URL에서 내용을 스크래핑
        
        Args:
            url: 스크래핑할 법령 URL
            max_retries: 최대 재시도 횟수
            
        Returns:
            (main_rules, appendix) 튜플 또는 None (실패 시)
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"스크래핑 시도 {attempt + 1}/{max_retries}: {url}")
                
                # WebDriver 초기화
                self.driver = self._setup_driver()
                
                # 페이지 로드
                self.driver.get(url)
                
                # iframe 대기 및 전환
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                )
                
                iframe = self.driver.find_element(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(iframe)
                
                # 본문 대기
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, "conScroll"))
                )
                
                # 페이지 소스 가져오기
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                # 콘텐츠 추출
                main_rules, appendix = self._extract_content(soup)
                
                logger.info(f"스크래핑 성공: {url}")
                return main_rules, appendix
                
            except TimeoutException:
                logger.warning(f"시간 초과 (시도 {attempt + 1}/{max_retries}): {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                    
            except WebDriverException as e:
                logger.error(f"WebDriver 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"예상치 못한 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    
        logger.error(f"스크래핑 실패: {url}")
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Tuple[List, List]:
        """
        BeautifulSoup 객체에서 법령 내용 추출
        
        Args:
            soup: BeautifulSoup 객체
            
        Returns:
            (main_rules, appendix) 튜플
        """
        # 전체 형법 추출
        con_scroll = soup.find(id="conScroll")
        if not con_scroll:
            logger.warning("conScroll 요소를 찾을 수 없습니다.")
            return [], []
        
        # 부칙 추출
        appendix = []
        appendix_length = 0
        
        ar_div = con_scroll.find(id="arDivArea")
        if ar_div:
            appendix = ar_div.find_all('div', class_="pgroup")
            appendix_length = len(appendix)
            logger.info(f"부칙 {appendix_length}개 추출")
        
        # 총칙 추출
        main_rules = []
        if con_scroll:
            all_pgroups = con_scroll.find_all('div', class_="pgroup")
            if appendix_length > 0:
                main_rules = all_pgroups[:-appendix_length]
            else:
                main_rules = all_pgroups
            logger.info(f"본문 {len(main_rules)}개 추출")
        
        return main_rules, appendix
    
    def scrape_multiple_laws(self, url_dict: dict) -> dict:
        """
        여러 법령 URL에서 데이터 스크래핑
        
        Args:
            url_dict: {법령명: URL} 딕셔너리
            
        Returns:
            {법령명: (main_rules, appendix)} 딕셔너리
        """
        results = {}
        
        for law_name, url in url_dict.items():
            logger.info(f"스크래핑 시작: {law_name}")
            
            result = self.scrape_law_content(url)
            if result:
                results[law_name] = result
                logger.info(f"스크래핑 완료: {law_name}")
            else:
                logger.error(f"스크래핑 실패: {law_name}")
                results[law_name] = ([], [])
                
        return results
    
    def __del__(self):
        """소멸자 - WebDriver 정리"""
        if self.driver:
            self.driver.quit()


# 법령 URL 딕셔너리 (사용자 프로토타입에서 가져옴)
LAW_URL_DICT = {
    "형법": "https://www.law.go.kr/법령/형법",
    "형사소송법": "https://www.law.go.kr/법령/형사소송법",
    "폭력행위등처벌에관한법률": "https://www.law.go.kr/법령/폭력행위등처벌에관한법률",
    "부정수표단속법": "https://www.law.go.kr/법령/부정수표단속법",
    "도로교통법": "https://www.law.go.kr/법령/도로교통법",
    "특정범죄가중처벌등에관한법률": "https://www.law.go.kr/법령/특정범죄가중처벌등에관한법률",
    "마약류불법거래방지에관한특례법": "https://www.law.go.kr/법령/마약류불법거래방지에관한특례법/",
    "소송촉진등에관한특례법": "https://www.law.go.kr/법령/소송촉진등에관한특례법",
    "벌금미납자의사회봉사집행에관한특례법": "https://www.law.go.kr/법령/벌금미납자의사회봉사집행에관한특례법"
}


def main():
    """메인 함수 - 테스트용"""
    scraper = LawScraper(headless=True)
    
    # 테스트 약 1분 소요
    for decree in LAW_URL_DICT.keys():
        test_url = LAW_URL_DICT[decree]
        result = scraper.scrape_law_content(test_url)
    
        if result:
            main_rules, _ = result
            print(f"{decree} 조문 수: {len(main_rules)}")
        else:
            print(f"{decree} 스크래핑 실패")


if __name__ == "__main__":
    main() 