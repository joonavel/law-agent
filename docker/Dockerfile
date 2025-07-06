# Python 3.11 베이스 이미지
FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome 리포지토리 키 추가
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Chrome 리포지토리 추가
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'

# Chrome 설치
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치 (최신 Chrome 버전 지원)
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) && \
    echo "Chrome version: $CHROME_VERSION" && \
    # Chrome 114+ 버전을 위한 새로운 다운로드 방식 사용
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION%%.*}") && \
    if [ -z "$CHROMEDRIVER_VERSION" ]; then \
        # fallback: 최신 stable 버전 사용
        CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE"); \
    fi && \
    echo "ChromeDriver version: $CHROMEDRIVER_VERSION" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

# 소스 코드 복사
COPY . .

# 의존성 설치 (PEP 621 표준 지원)
RUN pip install -e .

# 테스트 실행을 위한 환경 변수 설정
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# 기본 명령어 설정
CMD ["python", "scripts/create_batch_upload.py"]