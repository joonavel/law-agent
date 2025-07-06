#!/bin/bash

# law-agent scripts 실행 스크립트
# scripts 디렉터리의 파이썬 파일들을 지정된 순서로 실행합니다.

# 스크립트가 위치한 디렉터리로 이동
cd "$(dirname "$0")"

# scripts 디렉터리 경로 (상위 디렉터리)
SCRIPTS_DIR="../"

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Law-Agent Scripts 실행 시작"
echo "=========================================="

# scripts 디렉터리 존재 확인
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo -e "${RED}오류: scripts 디렉터리를 찾을 수 없습니다.${NC}"
    exit 1
fi

# 실행할 스크립트들 (순서대로)
scripts=(
    "collect_and_parse_laws.py"
    "process_documents_and_embed.py"
    "create_batch_upload.py"
    "evaluate_batch_results.py"
)

# 각 스크립트 실행
for script in "${scripts[@]}"; do
    script_path="$SCRIPTS_DIR/$script"
    
    # 파일 존재 확인
    if [ ! -f "$script_path" ]; then
        echo -e "${RED}오류: $script_path 파일을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}실행 중: $script${NC}"
    echo "------------------------------------------"
    
    # Python 스크립트 실행
    python3 "$script_path"
    
    # 실행 결과 확인
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $script 실행 완료${NC}"
    else
        echo -e "${RED}✗ $script 실행 실패${NC}"
        echo -e "${RED}스크립트 실행을 중단합니다.${NC}"
        exit 1
    fi
    
    echo ""
done

echo "=========================================="
echo -e "${GREEN}모든 스크립트 실행 완료!${NC}"
echo "==========================================" 