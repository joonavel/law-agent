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
    "형법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%98%95%EB%B2%95",
    "형사소송법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%98%95%EC%82%AC%EC%86%8C%EC%86%A1%EB%B2%95",
    "폭력행위등처벌에관한법률": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%8F%AD%EB%A0%A5%ED%96%89%EC%9C%84%EB%93%B1%EC%B2%98%EB%B2%8C%EC%97%90%EA%B4%80%ED%95%9C%EB%B2%95%EB%A5%A0",
    "부정수표단속법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%B6%80%EC%A0%95%EC%88%98%ED%91%9C%EB%8B%A8%EC%86%8D%EB%B2%95",
    "도로교통법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%8F%84%EB%A1%9C%EA%B5%90%ED%86%B5%EB%B2%95",
    "특정범죄가중처벌등에관한법률": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%8A%B9%EC%A0%95%EB%B2%94%EC%A3%84%EA%B0%80%EC%A4%91%EC%B2%98%EB%B2%8C%EB%93%B1%EC%97%90%EA%B4%80%ED%95%9C%EB%B2%95%EB%A5%A0",
    "마약류불법거래방지에관한특례법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%A7%88%EC%95%BD%EB%A5%98%EB%B6%88%EB%B2%95%EA%B1%B0%EB%9E%98%EB%B0%A9%EC%A7%80%EC%97%90%EA%B4%80%ED%95%9C%ED%8A%B9%EB%A1%80%EB%B2%95/",
    "소송촉진등에관한특례법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%86%8C%EC%86%A1%EC%B4%89%EC%A7%84%20%EB%93%B1%EC%97%90%20%EA%B4%80%ED%95%9C%20%ED%8A%B9%EB%A1%80%EB%B2%95",
    "벌금미납자의사회봉사집행에관한특례법": "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%B2%8C%EA%B8%88%EB%AF%B8%EB%82%A9%EC%9E%90%EC%9D%98%EC%82%AC%ED%9A%8C%EB%B4%89%EC%82%AC%EC%A7%91%ED%96%89%EC%97%90%EA%B4%80%ED%95%9C%ED%8A%B9%EB%A1%80%EB%B2%95/"
}


def main():
    """메인 함수 - 테스트용"""
    scraper = LawScraper(headless=True)
    
    # 단일 법령 테스트
    test_url = LAW_URL_DICT["형법"]
    result = scraper.scrape_law_content(test_url)
    
    if result:
        main_rules, _ = result
        print(f"메인 규칙 수: {len(main_rules)}")
    else:
        print("스크래핑 실패")


if __name__ == "__main__":
    main() 