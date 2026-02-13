# Reddit AI Feeds

## English Description

Fetch latest and hot posts from 24 AI-related subreddits (LocalLLaMA, ClaudeAI, ChatGPT, DeepSeek, ollama, etc.) with Chinese summaries. Integrates with Telegram channel for automatic news delivery.

### Features

- **Multi-subreddit Support**: 24 AI-related subreddits
- **Chinese Summaries**: Automatic Chinese translation and summary
- **Scheduled Fetch**: Runs every 3 hours via cron
- **Telegram Integration**: Auto-post to Telegram channel
- **Hot & Latest**: Fetch both hot and latest posts

## 中文说明

从 24 个 AI 相关子版块（LocalLLaMA、ClaudeAI、ChatGPT、DeepSeek、ollama 等）获取最新/热门帖子，带中文摘要。集成 Telegram 频道实现自动资讯推送。

### 功能特性

- **多子版块支持**：24 个 AI 相关子版块
- **中文摘要**：自动翻译并生成中文摘要
- **定时获取**：每 3 小时通过 cron 执行
- **Telegram 集成**：自动发布到 Telegram 频道
- **热门+最新**：获取热门和最新帖子

## Quick Start / 快速开始

```bash
# Fetch posts / 获取帖子
python3 ~/.openclaw/skills/reddit-ai-feeds-skill/scripts/fetch_reddit.py --limit 10

# Chinese summary only / 仅中文摘要
python3 ~/.openclaw/skills/reddit-ai-feeds-skill/scripts/fetch_reddit.py --chinese-only

# Specific subreddits / 指定子版块
python3 ~/.openclaw/skills/reddit-ai-feeds-skill/scripts/fetch_reddit.py --subreddits LocalLLaMA,ClaudeAI
```

## Supported Subreddits / 支持的子版块

LocalLLaMA, ClaudeAI, ChatGPT, DeepSeek, ollama, LocalLlm, OpenAI, Anthropic, LLMNews, ArtificialInteligence, MachineLearning, datascience, llm, langchain, rag, pinecone, vectorDB, qdrant, chromadb, huggingface, StabilityAI, Midjourney, StableDiffusion, generativeai

See `SKILL.md` for detailed documentation.

查看 `SKILL.md` 了解详细文档。
