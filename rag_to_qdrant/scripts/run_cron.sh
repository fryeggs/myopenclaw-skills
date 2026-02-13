#!/bin/bash
# rag_to_qdrant cron 脚本
# 每 2 小时执行一次增量监控

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="${PYTHON_PATH:-python3}"
WATCH_DIR="/media/qingshan/D/jxh_data"
LOG_FILE="/tmp/rag_to_qdrant_$(date +%Y%m%d).log"

echo "[$(date)] 开始执行 rag_to_qdrant..." >> "$LOG_FILE"

cd "$SCRIPT_DIR"
$PYTHON_PATH main.py \
    --watch-dir "$WATCH_DIR" \
    --mode incremental \
    --qdrant-url http://localhost:6333 \
    --collection jxh_data_rag \
    --model bge-m3 \
    >> "$LOG_FILE" 2>&1

echo "[$(date)] 执行完成" >> "$LOG_FILE"
