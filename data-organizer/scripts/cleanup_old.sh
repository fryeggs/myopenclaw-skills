#!/bin/bash
# 清理 7 天前的已处理文件
LOG_FILE="/tmp/data_organizer_cleanup.log"
PROCESSED_DIR="$HOME/.openclaw/media/inbound/.processed"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

echo "[$DATE] 开始清理..." >> "$LOG_FILE"

if [ -d "$PROCESSED_DIR" ]; then
    COUNT=$(find "$PROCESSED_DIR -type f -mtime +7" 2>/dev/null | wc -l)
    find "$PROCESSED_DIR" -type f -mtime +7 -delete 2>/dev/null
    echo "[$DATE] 已清理 $COUNT 个文件" >> "$LOG_FILE"
else
    echo "[$DATE] 目录不存在，跳过清理" >> "$LOG_FILE"
fi
