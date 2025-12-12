# Law Agent System with KMMLU Evaluation

## 프로젝트 리포트
[1차 프로젝트 리포트](./reports/1st_report.pdf)

## 🎯 프로젝트 개요

이 프로젝트는 **한국 형법 전문 AI 에이전트 시스템**을 구축하고, KMMLU(Korean Massive Multitask Language Understanding) 벤치마크의 Criminal-Law 카테고리를 사용하여 성능을 평가하는 완전 자동화된 시스템입니다.

## 🏗️ 시스템 아키텍처

```
Law Agent System Pipeline
├── 📊 데이터 수집 (collect_and_parse_laws.py)
│   ├── Selenium 웹 스크래핑 (9개 법령)
│   ├── 조문별 파싱 (1,347개 조문)
│   └── JSON 형태 저장 (data/raw/)
├── 🔍 벡터화 (process_documents_and_embed.py)  
│   ├── Document 처리 (1,347개 문서)
│   ├── text-embedding-3-small 임베딩
│   └── FAISS 벡터 저장소 생성
├── 🤖 Agent 평가 (create_batch_upload.py)
│   ├── KMMLU 데이터셋 로드 (200문제)
│   ├── LangGraph 에이전트 실행
│   ├── Batch 파일 생성 (input_batch.jsonl)
│   └── OpenAI Batch API 업로드
└── 📈 결과 분석 (evaluate_batch_results.py)
    ├── Batch 상태 모니터링 (최대 10분)
    ├── 결과 다운로드 (output_batch.jsonl)
    └── 최종 성능 평가 및 통계
```

## 🛠️ 설치 및 실행

### 1️⃣ 환경 설정

```bash
# 1. 환경 변수 설정
# .env 파일 생성 및 OpenAI API 키 설정
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 2️⃣ 컨테이너 셋업 및 의존성 설치

```bash
# Docker 이미지 빌드 (처음 실행 시 또는 의존성 변경 후, 약 3~4분 소요)
cd docker
docker-compose build

# Docker 컨테이너 시작
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

### 3️⃣ Agent System 구축 및 평가 실행

#### 🎯 옵션 1: 전체 파이프라인 한번에 실행

```bash
# 데이터 수집 → 벡터화 → 배치 생성 → 결과 평가 (4단계 모두 진행)
docker-compose exec law-agent ./scripts/shell/run_script_full.sh
```

#### 🔄 옵션 2: 단계별 실행 (개발/디버깅용)

```bash
# Step 1-2: 데이터 준비 (최초 1회만 필요)
docker-compose exec law-agent python3 scripts/collect_and_parse_laws.py
docker-compose exec law-agent python3 scripts/process_documents_and_embed.py

# Step 3: 배치 생성 및 업로드
docker-compose exec law-agent ./scripts/shell/make_batch.sh

# Step 4: 결과 모니터링 및 평가
# (OpenAI Batch API는 완료까지 시간이 걸리므로 충분한 시간 뒤에 실행 권장)
docker-compose exec law-agent ./scripts/shell/eval_result.sh
```

#### 🎮 옵션 3: 사용 패턴

```bash
# 데이터는 이미 준비된 상태에서 평가만 재실행
docker-compose exec law-agent ./scripts/shell/make_batch.sh
# (배치 처리 대기 - 아무리 오래 걸려도 24시간 이내)
docker-compose exec law-agent ./scripts/shell/eval_result.sh
```

### 4️⃣ 결과 확인

```bash
# 로그 확인
docker-compose logs law-agent

# 결과 파일 확인
docker-compose exec law-agent ls -la data/batch/
# → input_batch.jsonl, output_batch.jsonl, input_id.txt, output_id.txt
```

### 5️⃣ 정리

```bash
# 컨테이너 종료
docker-compose down

# 컨테이너 및 이미지 완전 삭제 (선택사항)
docker-compose down --rmi all --volumes
```

## 🐳 Docker Compose 상세 설정

### docker-compose.yml 구성 요소

```yaml
services:
  law-agent:
    build:
      context: ../          # law-agent 루트 디렉터리
      dockerfile: docker/Dockerfile
    container_name: law-agent
    volumes:
      - ../src:/app/src                    # 소스 코드 마운트
      - ../data:/app/data                  # 데이터 디렉터리 마운트  
      - ../scripts:/app/scripts            # 스크립트 디렉터리 마운트
      - ../.env:/app/.env                  # 환경 변수 파일 마운트
    environment:
      - DISPLAY=:99                        # 가상 디스플레이 (Chrome용)
      - PYTHONPATH=/app                    # Python 경로 설정
    env_file:
      - ../.env                           # .env 파일 자동 로드
    networks:
      - law-agent-network                  # 전용 네트워크
    command: tail -f /dev/null             # 컨테이너 유지용
```

## 📊 실행 스크립트 상세 설명

### 🎯 run_script_full.sh (전체 실행)
**용도**: 요구사항 충족을 위한 전체 파이프라인 실행
```bash
# 실행 순서
1. collect_and_parse_laws.py      # 법령 데이터 수집 (약 3분)
2. process_documents_and_embed.py # 벡터 임베딩 생성 (약 5분)  
3. create_batch_upload.py         # 배치 업로드 (약 20분)
4. evaluate_batch_results.py      # 결과 평가 (최대 10분 대기 후 강제 평가 진행)
```

### 🔄 make_batch.sh (배치 생성)
**용도**: 새로운 평가 배치 생성 (jsonl 삭제 후 새로 생성)
- 전제조건: data/embeddings 존재 확인
- 출력: input_batch.jsonl, input_id.txt
- 소요시간: 약 20분 (200문제 처리)

### 📈 eval_result.sh (결과 평가)  
**용도**: 배치 완료 후 결과 분석 (배치 상태가 completed가 아니면 강제 평가 진행)
- 전제조건: input_id.txt 존재 확인
- 기능: 배치 상태 모니터링 → 결과 다운로드 → 성능 계산
- 출력: output_batch.jsonl, output_id.txt, 최종 성능 지표

## 📈 벤치마크 성능 및 버전별 분석

### 🎯 현재 성능 (최종 버전)
```
KMMLU Criminal-Law 평가 결과
📊 총 문제 수: 200
✅ 정답 수: 55  
❌ 오답 수: 115
⚠️ 실패 수: 30
🎯 최종 정확도: 27.5%
```

### 📊 버전별 성능 비교

| 버전 | 정확도 | 정답/전체 | 입력 구성 | 주요 특징 |
|------|---------|-----------|-----------|-----------|
| **Base (v1)** | **35.0%** | 70/200 | 문제 + 선택지 | 순수 LLM, 추가 정보 없음 |
| **RAG Only (v2)** | **35.0%** | 70/200 | 문제 + 선택지 + 형법 조문 5개 | 단순 벡터 검색 RAG |
| **Agentic RAG (v3)** | **27.5%** | 55/200 | 문제 + 선택지 + Agent 정리 Context | LangGraph 기반 Agentic RAG |
| **Agentic RAG + Preprocessing (v3)** | **35.5%** | 71/200 | 전처리된 문제와 선택지 + Agent 정리 context | Agentic RAG 와 입력 전처리 및 유형 분류 |

### 🤔 성능 분석 및 개선 아이디어

#### 🔍 핵심 문제 분석

**성능 역설 현상**
- **v1 (정보 없음)**: 35% - GPT-4o-mini 자체 지식만 활용
- **v2 (관련 조문 5개)**: 35% - 동일한 성능, 조문이 도움/방해 상쇄
- **v3 (Agent 정리 정보)**: 27.5% - Agent가 정리한 정보가 오히려 **혼란 야기**
- **v4 (입력 데이터 전처리)**: 35.5% - 성능은 v1, v2와 비슷하나 정답 양상이 전혀 다름

핵심 문제점은 다음으로 파악된다.

- 형법 추론의 기본은 구성요건-위법성-책임 이라는 3단계 구조를 중심으로 접근해야 하는 것이지만, 프롬프트에 적용되지 않았다.
- 이외에도 추가적으로 쟁점 정리, 죄수론, 공범, 판례 및 학설 검토 등의 복잡한 추론 과정이 포함되어야하는 경우가 있음에도 이를 적용할 시스템이 미비했다.
- 복잡한 추론 과정을 단일 agent가 처리하게 됨으로써 복잡도 증가에 따른 전체 context의 증가로 Agent의 성능이 하락했다.

결과적으로 복잡한 로직을 요구하는 형법 추론 task에서 **기초적인 프롬프트 및 workflow**로는 적절한 정보를 가지고 있더라도 높은 성능을 기대하기 어렵다. 

#### 현재 시스템의 구체적 한계점

1. **제한된 법령 커버리지** 
   - 현재: 9개 형법 관련 법령만 임베딩
   - 문제: Agent가 벡터DB에 없는 법령을 계속 검색 시도
   - 결과: **Recursion count 낭비** → 최종 답변 품질 저하

2. **Agent의 정보 처리 한계**
   - Agent가 수집한 정보가 LLM에게 **노이즈**로 작용
   - 하나의 Agent에게 너무 많은 task를 할당 **핵심 정보 손실**
   - 결과적으로 참조 정보 없이 하는 추론보다 성능이 감소함

#### 🚀 개선 아이디어 로드맵

**🎯 핵심 개선 전략**

**1. Single to Multi-Agent**
- [ ] **Multi-Agent 시스템 구축**:
- 각 추론 단계(구성요건-위법성-책임)을 담당하는 전문 agent들로 구성된 시스템을 구축한다.
- 각 전문 agent들이 실제 전문가의 추론 과정을 모사할 수 있도록 프롬프트를 설계하고 tool을 개발하여 적용한다.

**2. 핵심 기능 확장 (데이터 한계 극복)**
- [ ] **📚 판례 데이터 통합**: 
  - 대법원 판례 크롤링 및 임베딩
  - 형법 관련 주요 판례 1,000+ 건 수집
  - 조문 + 판례 하이브리드 검색 구현

### 📁 프로젝트 구조
```
law-agent/
├── 📄 README.md                    # 이 파일
├── 📄 pyproject.toml               # Poetry 의존성 관리
├── 📄 .env                         # OpenAI API 키 설정
├── 🐳 docker/
│   ├── 📄 Dockerfile               # 컨테이너 이미지 정의
│   └── 📄 docker-compose.yml       # 멀티 컨테이너 설정
├── 📁 scripts/
│   ├── 🔧 shell/                   # 실행 스크립트들
│   │   ├── 📄 run_script_full.sh   # 전체 파이프라인
│   │   ├── 📄 make_batch.sh        # 배치 생성
│   │   └── 📄 eval_result.sh       # 결과 평가
│   ├── 📄 collect_and_parse_laws.py      # 1단계: 데이터 수집
│   ├── 📄 process_documents_and_embed.py # 2단계: 벡터화
│   ├── 📄 create_batch_upload.py         # 3단계: 배치 업로드
│   └── 📄 evaluate_batch_results.py      # 4단계: 결과 평가
├── 📁 src/                         # 소스 코드
│   ├── 📁 data_collector/          # 웹 스크래핑 & 파싱
│   ├── 📁 vector_db/               # 벡터 저장소 관리
│   ├── 📁 agent/                   # LangGraph 에이전트
│   └── 📁 evaluation/              # KMMLU 평가기
└── 📁 data/                        # 데이터 저장소
    ├── 📁 raw/                     # 원시 법령 데이터 (9개 파일)
    ├── 📁 embeddings/              # FAISS 벡터 저장소
    └── 📁 batch/                   # 배치 입출력 파일
```

## 💡 사용 팁 및 문제 해결

**Q: 배치가 너무 오래 걸려요**
```bash
# 배치 상태 확인
docker-compose exec law-agent python3 -c "
from src.evaluation.kmmlu_evaluator import KMMLUEvaluator
evaluator = KMMLUEvaluator()
batch_id = open('data/batch/input_id.txt').read().strip()
print(evaluator.monitor_batch(batch_id))
"
```
