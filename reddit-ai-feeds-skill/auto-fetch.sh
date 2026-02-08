#!/bin/bash
# Reddit AI Feeds - 自动抓取并发送到 Telegram
# 每 3 小时执行一次

SKILL_DIR="$HOME/.openclaw/skills/reddit-ai-feeds-skill"
OPENCLAW_CMD="/usr/bin/openclaw"
TELEGRAM_TOPIC_ID="466"
TELEGRAM_CHAT_ID="-1003856805564"

# 执行抓取
OUTPUT=$(cd "$SKILL_DIR" && python3 scripts/fetch_reddit.py --limit 5 2>&1)

# 获取时间戳
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

# 构建消息
MESSAGE="📊 **Reddit AI 社区热帖** (自动抓取)
⏰ 抓取时间: $TIMESTAMP

---
$OUTPUT
---
🤖 自动抓取自 r/LocalLLaMA, r/ClaudeAI, r/ChatGPT 等 24 个 AI 社区"

# 发送到 Telegram feed (topic 466)
echo "⏳ 正在发送到 Telegram..."
$OPENCLAW_CMD message send \
  --channel telegram \
  --target "$TELEGRAM_CHAT_ID" \
  --thread-id "$TELEGRAM_TOPIC_ID" \
  --message "$MESSAGE"

RESULT=$?
if [ $RESULT -eq 0 ]; then
  echo "✅ 已发送到 Telegram Feed (topic $TELEGRAM_TOPIC_ID)"
else
  echo "❌ 发送失败 (退出码: $RESULT)"
fi
