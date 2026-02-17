#!/bin/bash
# Data Organizer Cron 任务
# 每小时运行一次，检查 inbound 文件夹

INBOUND_DIR="$HOME/.openclaw/media/inbound"
OUTPUT_DIR="/media/qingshan/D/jxh_data"
LOG_FILE="$HOME/.openclaw/logs/data-organizer-cron.log"

echo "=== $(date) ===" >> "$LOG_FILE"

# 检查是否有待处理文件
file_count=$(ls -1 "$INBOUND_DIR" 2>/dev/null | grep -v "^\.processed$" | wc -l)

if [ "$file_count" -eq 0 ]; then
    echo "无待处理文件" >> "$LOG_FILE"
    exit 0
fi

echo "发现 $file_count 个文件待处理" >> "$LOG_FILE"

# 运行 data-organizer
cd "$INBOUND_DIR"
/usr/bin/python3 "$HOME/.openclaw/skills/data-organizer/scripts/organizer.py" \
    --input "$INBOUND_DIR" \
    --output "$OUTPUT_DIR" \
    --format json \
    >> "$LOG_FILE" 2>&1

# 检查处理结果
if [ $? -eq 0 ]; then
    echo "处理完成" >> "$LOG_FILE"

    # 发送通知到 feed topic (1816)
    /usr/bin/openclaw message send \
        --channel telegram \
        --target "-1003856805564" \
        --thread-id 1816 \
        --message "📂 Data Organizer: 处理完成，$file_count 个文件已整理" \
        >> "$LOG_FILE" 2>&1
else
    echo "处理失败" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
