#!/bin/bash
# Cron 安装脚本
# 安装后每 50 分钟自动执行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="/usr/bin/python3"

echo "安装 memory-consolidator cron 任务..."

# 添加 cron 任务
(crontab -l 2>/dev/null | grep -v "memory-consolidator"; echo "*/50 * * * * $PYTHON_PATH $SCRIPT_DIR/main.py >> ~/.openclaw/logs/memory-consolidator-cron.log 2>&1") | crontab -

echo "Cron 任务已安装:"
crontab -l | grep memory-consolidator

echo ""
echo "日志位置: ~/.openclaw/logs/memory-consolidator-cron.log"
