# Law Agent System with KMMLU Evaluation

## 🎯 프로젝트 개요

이 프로젝트는 **한국 형법 전문 AI 에이전트 시스템**을 구축하고, KMMLU(Korean Massive Multitask Language Understanding) 벤치마크의 Criminal-Law 카테고리를 사용하여 성능을 평가하는 완전 자동화된 시스템입니다.

### 📋 주요 요구사항 (과제 기준)
- ✅ **전체 실행 시간**: 1시간 이내 (Batch API 응답시간 제외)
- ✅ **도커 환경**: 모든 코드가 도커 환경에서 실행 가능
- ✅ **의존성 관리**: Poetry & pyproject.toml 사용
- ✅ **한번에 실행**: Agent system 구축부터 KMMLU 평가까지 원클릭 실행
- ✅ **RAG 데이터**: 원시 데이터 수집부터 정제까지 모든 과정 포함
- ✅ **OpenAI Batch API**: 최종 평가에 Batch API 사용
- ✅ **제출 파일**: input/output batch 파일, 벤치마크 점수 모두 포함

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

### 📋 시스템 요구사항
- Docker & Docker Compose
- 최소 2GB RAM
- 인터넷 연결 (API 호출 및 데이터 수집)
- OpenAI API 키

### 1️⃣ 환경 설정

```bash
# 1. 환경 변수 설정
# .env 파일 생성 및 OpenAI API 키 설정
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 2️⃣ 컨테이너 셋업 및 의존성 설치

```bash
# Docker 컨테이너 빌드 및 시작
cd docker
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

### 3️⃣ Agent System 구축 및 평가 실행

#### 🎯 옵션 1: 전체 파이프라인 한번에 실행 (요구사항 충족)

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

### 주요 특징

1. **볼륨 마운트**: 개발 시 실시간 코드 변경사항 반영
2. **환경 변수**: OpenAI API 키 자동 로드
3. **네트워크 격리**: 전용 네트워크로 보안 강화  
4. **Chrome 지원**: 웹 스크래핑을 위한 headless Chrome 환경
5. **Poetry 지원**: pyproject.toml 기반 의존성 관리

### Dockerfile 구성 요소

- **베이스 이미지**: Python 3.11-slim
- **Chrome 설치**: 최신 stable Chrome + ChromeDriver 자동 설치
- **시스템 패키지**: wget, curl, xvfb 등 필수 도구
- **Python 의존성**: `pip install -e .` (PEP 621 표준)
- **환경 설정**: PYTHONPATH, DISPLAY 환경 변수

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
| **Final (v3)** | **27.5%** | 55/200 | 문제 + 선택지 + Agent 정리 Context | LangGraph 기반 Agentic RAG |

### 🤔 성능 분석 및 개선 아이디어

#### 🔍 핵심 문제 분석: "정보가 많을수록 성능 저하"

**성능 역설 현상**
- **v1 (정보 없음)**: 35% - GPT-4o-mini 자체 지식만 활용
- **v2 (관련 조문 5개)**: 35% - 동일한 성능, 조문이 도움/방해 상쇄
- **v3 (Agent 정리 정보)**: 27.5% - Agent가 정리한 정보가 오히려 **혼란 야기**

#### 현재 시스템의 구체적 한계점

1. **제한된 법령 커버리지** 
   - 현재: 9개 형법 관련 법령만 임베딩
   - 문제: Agent가 벡터DB에 없는 법령을 계속 검색 시도
   - 결과: **Recursion count 낭비** → 최종 답변 품질 저하

2. **Agent의 정보 처리 한계**
   - Agent가 수집한 정보가 LLM에게 **노이즈**로 작용
   - 복잡한 워크플로우에서 **핵심 정보 손실**
   - 법률 문제의 직관적 해결을 방해

3. **검색 범위의 제약**
   - 벡터 검색으로만 제한된 정보 접근
   - 실시간 법령/판례 업데이트 불가

#### 🚀 개선 아이디어 로드맵

**🎯 핵심 개선 전략: "단순함으로 돌아가기 + 데이터 확장"**

**1. 즉시 개선 (성능 복구 우선)**
- [ ] **워크플로우 단순화**: v1/v2의 단순한 RAG 로직 재적용
- [ ] **Agent 복잡성 제거**: 정보 요약 대신 직접적인 벡터 검색 활용
- [ ] **에러 핸들링 강화**: 실패케이스 분석으로 최대한 감소(9 미만은 불가능)

**2. 핵심 기능 확장 (데이터 한계 극복)**
- [ ] **📚 판례 데이터 통합**: 
  - 대법원 판례 크롤링 및 임베딩
  - 형법 관련 주요 판례 1,000+ 건 수집
  - 조문 + 판례 하이브리드 검색 구현

- [ ] **🔍 동적 법령 검색 시스템**:
  - **Selenium Tool 개발**: 실시간 법령/판례 URL 접근
  - **ReAct Agent 통합**: 벡터DB에 없는 법령 자동 검색
  - **Recursion 최적화**: 무한 검색 방지 로직

**3. 시스템 아키텍처 개선**
```
개선된 시스템 플로우:
1. 문제 분석 → 관련 키워드 추출
2. 벡터DB 검색 (기존 9개 법령 + 판례)
3. 검색 실패 시 → Selenium Tool 실시간 크롤링
4. 수집된 정보 → 단순 Context 구성 (Agent 정리 제거)
5. 직접 답변 생성
```

#### 🎯 예상 성능 개선 효과

| 개선 단계 | 예상 정확도 | 근거 |
|-----------|-------------|------|
| **워크플로우 단순화** | 35%+ | v1/v2 수준 복구 |
| **판례 데이터 추가** | 40%+ | 사례 기반 추론 강화 |
| **동적 검색 시스템** | 45%+ | 법령 커버리지 완전성 |

**🔧 핵심 개선 포인트**
- **"Less is More"**: Agent 복잡성 제거로 노이즈 감소
- **"Coverage Expansion"**: 실시간 데이터 접근으로 한계 극복
- **"Quality over Quantity"**: 정확한 소수 정보 > 부정확한 다량 정보

## 🎯 제출 파일 및 성과

### ✅ 필수 제출 파일 (완료)
- **배치 입력 파일**: `data/batch/input_batch.jsonl` (200개 문제)
- **배치 출력 파일**: `data/batch/output_batch.jsonl` (200개 답변)  
- **벤치마크 점수**: **Accuracy: 0.275** (55/200 정답)
- **전체 소스 코드**: < 2GB (Poetry lock 포함)

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

### 🔧 일반적인 문제들

**Q: API 키 관련 오류가 발생해요**
```bash
# .env 파일 확인
cat .env
# 컨테이너 내 환경변수 확인  
docker-compose exec law-agent printenv | grep OPENAI
```

**Q: Chrome/ChromeDriver 오류가 발생해요**
```bash
# Chrome 버전 확인
docker-compose exec law-agent google-chrome --version
docker-compose exec law-agent chromedriver --version
```

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