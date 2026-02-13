---
name: reddit-ai-feeds-skill
description: "Fetch latest/hot posts from 24 AI subreddits (LocalLLaMA, ClaudeAI, ChatGPT, DeepSeek, ollama, etc.) with Chinese summaries. Use when user asks to check Reddit AI news, browse AI communities, get LocalLLaMA updates, or see what's trending in AI subreddits."
---

# Reddit AI Feeds Skill

Fetch and summarize posts from top AI-related subreddits via RSS feeds with Chinese translations.

## Quick Start

```bash
cd ~/reddit-ai-feeds-skill
python3 scripts/fetch_reddit.py --limit 10
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 5 | Posts per subreddit |
| `--subreddits` | (all 24) | Comma-separated list |
| `--sort` | hot | Sort: hot, new, top, rising |
| `--total` | 20 | Max total posts |

## Examples

```bash
# Default: hot posts from all AI subs
python3 scripts/fetch_reddit.py --limit 10

# Specific subreddits only
python3 scripts/fetch_reddit.py --subreddits LocalLLaMA,ClaudeAI --limit 5

# New posts from specific subs
python3 scripts/fetch_reddit.py --sort new --subreddits OpenAI,ChatGPT --limit 5
```

## Default Subreddits (24 communities)

**Core LLM:** LocalLLaMA, ollama

**Major AI Providers:** Anthropic, ClaudeAI, ClaudeCode, OpenAI, ChatGPT, DeepSeek, GeminiAI, google_antigravity, kimi

**AI Coding Tools:** cursor, kiroIDE

**OpenClaw Ecosystem:** openclaw, clawdbot, moltbot

**Other AI Tools:** notebooklm, LangChain, nanobanana

**Research & General:** MachineLearning, singularity

## Output Format

```
📊 共 10 条 Reddit AI 相关帖子

============================================================
【1】Llama 3.2 released - 1B and 3B models now available
   💡 关键词: release=发布, model=模型
   📍 🦙 本地大模型社区 · 2小时前
   📝 新版本/产品发布公告
   🔗 https://reddit.com/r/LocalLLaMA/comments/...
```

Each result includes:
- English title
- Chinese title translation
- Key AI terms with Chinese translations
- Subreddit description in Chinese
- Post summary type
- Time ago
- Direct Reddit link

## Advanced

- **Custom search**: See [SEARCH.md](references/SEARCH.md)
- **Subreddit details**: See [SUBREDDITS.md](references/SUBREDDITS.md)
- **Output customization**: See [OUTPUT.md](references/OUTPUT.md)
