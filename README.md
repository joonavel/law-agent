# Law Agent System with KMMLU Evaluation

## 🎯 프로젝트 개요

이 프로젝트는 **한국 형법 전문 AI 에이전트 시스템**을 구축하고, KMMLU(Korean Massive Multitask Language Understanding) 벤치마크의 Criminal-Law 카테고리를 사용하여 성능을 평가하는 시스템입니다.

### 주요 기능
- 🤖 **AI 에이전트 시스템**: GPT-4o-mini 기반 한국 형법 전문 에이전트
- 🔍 **RAG 시스템**: 한국 형법 조문 및 판례 검색 시스템
- 📊 **자동 평가**: KMMLU Criminal-Law 데이터셋을 활용한 자동 평가
- ☁️ **OpenAI Batch API**: 대용량 평가를 위한 배치 처리 시스템
- 🐳 **Docker 환경**: 완전 컨테이너화된 실행 환경

## 🏗️ 시스템 아키텍처

```
Law Agent System
├── 🤖 Agent Core (GPT-4o-mini)
│   ├── Question Validator
│   ├── Problem Classifier  
│   └── RAG Retriever
├── 🔍 RAG System
│   ├── Vector DB (text-embedding-3-small)
│   ├── Legal Document Store
│   └── Semantic Search
├── 📊 Evaluation System
│   ├── KMMLU Dataset Loader
│   ├── Batch File Generator
│   └── OpenAI Batch API Client
└── 🐳 Docker Environment
    ├── Chrome/ChromeDriver
    ├── Python 3.11
    └── Poetry Dependencies
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd law-agent

# 환경 변수 설정
cp .env.example .env
# .env 파일에 OpenAI API 키 설정
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

### 2. 전체 시스템 실행 (원클릭)

```bash
# Docker 환경에서 전체 시스템 구축 및 평가 실행
cd docker
docker-compose up --build

# 또는 개별 스크립트 실행
docker-compose run law-agent python scripts/create_batch_upload.py
docker-compose run law-agent python scripts/evaluate_batch_results.py
```

### 3. 수동 실행 (단계별)

```bash
# 1단계: 배치 파일 생성 및 업로드
cd docker
docker-compose run law-agent python scripts/create_batch_upload.py

# 2단계: 배치 결과 평가 (배치 완료 후)
docker-compose run law-agent python scripts/evaluate_batch_results.py
```

## 📋 요구사항

### 시스템 요구사항
- Docker & Docker Compose
- 최소 2GB RAM
- 인터넷 연결 (API 호출 및 데이터 다운로드)

## 🔄 워크플로우

### 1. 데이터 수집 및 전처리
```bash
# 한국 형법 조문 및 판례 데이터 수집
python scripts/process_documents_and_embed.py
```

### 2. 벡터 데이터베이스 구축
- 📚 **원본 데이터**: 한국 형법 조문, 판례 문서
- 🔄 **전처리**: 문서 분할, 정제, 구조화
- 🎯 **임베딩**: text-embedding-3-small로 벡터화
- 💾 **저장**: FAISS 벡터 데이터베이스 생성

### 3. 에이전트 시스템 구축
- 🔍 **질문 유효성 검사**: 법률 질문 적합성 판단
- 🏷️ **문제 분류**: 법률 문제 유형 분류
- 🔎 **RAG 검색**: 관련 조문 및 판례 검색
- 🤖 **답변 생성**: GPT-4o-mini 기반 답변 생성

### 4. KMMLU 평가 실행
```bash
# 전체 평가 워크플로우
python scripts/create_batch_upload.py      # 배치 업로드
python scripts/evaluate_batch_results.py   # 결과 평가
```

## 🎯 주요 스크립트

### 1. `scripts/create_batch_upload.py`
- **기능**: KMMLU 데이터셋 처리 및 OpenAI 배치 업로드
- **프로세스**:
  1. KMMLU Criminal-Law 데이터셋 로드
  2. Parent Graph로 평가 실행
  3. 배치 파일 생성 (`input_batch.jsonl`)
  4. OpenAI Batch API 업로드
  5. 배치 ID 저장 (`input_id.txt`)

### 2. `scripts/evaluate_batch_results.py`
- **기능**: 배치 결과 모니터링 및 최종 평가
- **프로세스**:
  1. 배치 ID 확인 (`input_id.txt`)
  2. 배치 상태 모니터링 (최대 10분)
  3. 완료시 결과 다운로드 (`output_batch.jsonl`)
  4. 출력 배치 ID 저장 (`output_id.txt`)
  5. 최종 평가 실행 및 결과 출력

## 🐳 Docker 설정

### Dockerfile 구성
```dockerfile
FROM python:3.11-slim

# Chrome 및 ChromeDriver 설치
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/

# Poetry 설치 및 의존성 관리
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev
```

### Docker Compose 구성
```yaml
version: '3.8'

services:
  law-agent:
    build:
      context: ../
      dockerfile: docker/Dockerfile
    container_name: law-agent
    volumes:
      - ../src:/app/src
      - ../data:/app/data
      - ../scripts:/app/scripts
      - ../.env:/app/.env
    environment:
      - PYTHONPATH=/app
    command: >
      bash -c "
        echo '🚀 Law Agent 통합 워크플로우 테스트 시작...' &&
        python scripts/create_batch_upload.py &&
        python scripts/evaluate_batch_results.py
      "
```

## 📊 제출 파일

### 필수 제출 파일 ✅
- **배치 입력 파일**: `data/batch/input_batch.jsonl`
- **배치 출력 파일**: `data/batch/output_batch.jsonl`
- **벤치마크 점수**: Accuracy: 0.275
- **전체 소스 코드**: 2GB 이내

Agentic Flow 없이 진행한 결과 base
correct: 70, fails: 2, wrong_preds: 128
accuracy: 0.35

형법만을 이용해서 간단한 RAG를 진행한 결과
correct: 70, fails: 9, wrong_preds: 121
accuracy: 0.35

최종 버전의 결과
correct: 55, fails: 30, wrong_preds: 115
accuracy: 0.275
