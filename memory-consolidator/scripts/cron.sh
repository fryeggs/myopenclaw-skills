#!/bin/bash
# Memory Consolidator Cron 脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.openclaw/qmd_memory/logs"

mkdir -p "$LOG_DIR"

echo "[$(date)] 开始执行 memory-consolidator" >> "$LOG_DIR/cron.log"

python3 "$SCRIPT_DIR/main.py" --verbose >> "$LOG_DIR/cron.log" 2>&1

echo "[$(date)] 执行完成" >> "$LOG_DIR/cron.log"
