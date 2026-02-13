#!/usr/bin/env python3
"""
Fetch AI-related Reddit posts via RSS feeds.
Outputs Chinese title, summary and URL.

Usage:
    python3 fetch_reddit.py [--sort hot|new|top] [--limit N] [--subreddits sub1,sub2,...]

Examples:
    python3 fetch_reddit.py --limit 10
    python3 fetch_reddit.py --subreddits LocalLLaMA,ClaudeAI --limit 5
"""

import argparse
import re
import sys
import urllib.request
import html
import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime
import time

# Default AI subreddits
DEFAULT_SUBREDDITS = [
    # Core LLM communities
    "LocalLLaMA",
    "ollama",
    # Major AI providers
    "Anthropic",
    "ClaudeAI",
    "ClaudeCode",
    "OpenAI",
    "ChatGPT",
    "DeepSeek",
    "GeminiAI",
    "google_antigravity",
    "kimi",
    # AI coding tools
    "cursor",
    "kiroIDE",
    # OpenClaw ecosystem
    "openclaw",
    "clawdbot",
    "moltbot",
    # Other AI tools
    "notebooklm",
    "LangChain",
    "nanobanana",
    # Research & general
    "MachineLearning",
    "singularity",
]

# Subreddit Chinese descriptions
SUBREDDIT_INFO = {
    # Core LLM
    "localllama": ("LocalLLaMA", "🦙 本地大模型社区"),
    "ollama": ("ollama", "🦙 Ollama本地模型"),
    # Major AI providers
    "anthropic": ("Anthropic", "🏛️ Anthropic官方"),
    "claudeai": ("ClaudeAI", "🤖 Claude讨论"),
    "claudecode": ("ClaudeCode", "💻 Claude Code"),
    "openai": ("OpenAI", "🔬 OpenAI"),
    "chatgpt": ("ChatGPT", "💬 ChatGPT讨论"),
    "deepseek": ("DeepSeek", "🔍 DeepSeek"),
    "geminiai": ("GeminiAI", "💎 Gemini AI"),
    "google_antigravity": ("google_antigravity", "🚀 Google Antigravity"),
    "kimi": ("kimi", "🌙 Kimi/月之暗面"),
    # AI coding tools
    "cursor": ("cursor", "🖱️ Cursor IDE"),
    "kiroide": ("kiroIDE", "⌨️ Kiro IDE"),
    # OpenClaw ecosystem
    "openclaw": ("openclaw", "🦞 OpenClaw"),
    "clawdbot": ("clawdbot", "🤖 Clawdbot"),
    "moltbot": ("moltbot", "🦞 Moltbot"),
    # Other AI tools
    "notebooklm": ("notebooklm", "📓 NotebookLM"),
    "langchain": ("LangChain", "🔗 LangChain"),
    "nanobanana": ("nanobanana", "🍌 Nanobanana"),
    # Research & general
    "machinelearning": ("MachineLearning", "📊 机器学习研究"),
    "artificial": ("artificial", "🧠 AI综合"),
    "singularity": ("singularity", "🚀 AGI/奇点"),
    "stablediffusion": ("StableDiffusion", "🎨 AI图像生成"),
}

# Key term translations (for title and content)
TERM_TRANSLATIONS = {
    # Actions
    "release": "发布", "released": "发布", "launching": "发布",
    "announce": "宣布", "announcing": "宣布", "introducing": "推出",
    "update": "更新", "updates": "更新", "upgrade": "升级",
    "built": "构建", "made": "制作", "created": "创建",
    "support": "支持", "supports": "支持",
    # Technical terms
    "model": "模型", "models": "模型",
    "benchmark": "基准测试", "benchmarks": "基准测试",
    "fine-tuning": "微调", "fine tuning": "微调", "finetuning": "微调",
    "quantization": "量化", "inference": "推理",
    "context": "上下文", "token": "令牌", "tokens": "令牌",
    "GPU": "显卡", "VRAM": "显存",
    "open source": "开源", "open-source": "开源", "opensource": "开源",
    "local": "本地", "locally": "本地",
    "parameter": "参数", "parameters": "参数",
    "training": "训练", "reasoning": "推理能力",
    "coding": "编程", "code": "代码",
    "agent": "智能体", "agents": "智能体", "agentic": "智能体",
    "MoE": "混合专家", "flash": "极速版",
    # Common phrases
    "how to": "如何", "why": "为什么", "what": "什么",
    "best": "最佳", "new": "新", "free": "免费",
    "faster": "更快", "better": "更好", "vs": "对比",
    "comparison": "对比", "guide": "指南", "tutorial": "教程",
    "tips": "技巧", "help": "帮助",
    "issue": "问题", "issues": "问题", "bug": "错误",
    "bugs": "错误", "error": "错误", "fix": "修复", "fixed": "已修复",
    "plugin": "插件", "plugins": "插件", "tool": "tools", "tools": "工具",
    "runtime": "运行时", "server": "服务器", "servers": "服务器",
    "api": "接口", "limit": "限制", "limits": "限制",
    "performance": "性能", "speed": "速度", "memory": "内存",
    "hallucination": "幻觉", "hallucinations": "幻觉",
    "prompt": "提示词", "prompts": "提示词", "engineering": "工程",
    "feedback": "反馈", "community": "社区", "discussion": "讨论",
    "megathread": "讨论帖", "AMA": "问答",
    "lawsuit": "诉讼", "sue": "起诉", "billion": "十亿", "million": "百万",
}

# Title translation patterns
TITLE_PATTERNS = [
    (r"(?i)^released[:\s]", "发布："),
    (r"(?i)^announcing[:\s]", "宣布："),
    (r"(?i)^introducing[:\s]", "推出："),
    (r"(?i)^how to\s", "如何"),
    (r"(?i)^why\s", "为什么"),
    (r"(?i)^what\s", "什么是"),
    (r"(?i)\bAMA\b", "问答"),
    (r"(?i)\bmegathread\b", "讨论帖"),
    (r"(?i)\bopen[- ]?source\b", "开源"),
    (r"(?i)\bhallucination[s]?\b", "幻觉"),
    (r"(?i)\bplugin[s]?\b", "插件"),
]


def translate_title(title: str) -> str:
    """Create Chinese title translation using pattern matching."""
    zh_title = title
    for pattern, replacement in TITLE_PATTERNS:
        zh_title = re.sub(pattern, replacement, zh_title)
    for en, zh in sorted(TERM_TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        zh_title = re.sub(r'(?i)\b' + re.escape(en) + r'\b', zh, zh_title)
    return zh_title


def summarize_content(title: str, content: str) -> str:
    """Generate brief Chinese summary based on content detection."""
    full_text = (title + " " + content).lower()
    
    if "ama" in full_text or "ask me anything" in full_text:
        return "问答讨论，开发者/团队回答社区问题"
    elif any(x in full_text for x in ["release", "launching", "announcing"]):
        return "新版本/产品发布公告"
    elif "megathread" in full_text:
        return "社区集中讨论帖"
    elif any(x in full_text for x in ["bug", "issue", "error", "fix"]):
        return "问题报告/修复讨论"
    elif any(x in full_text for x in ["how to", "guide", "tutorial"]):
        return "教程/指南"
    elif any(x in full_text for x in ["vs", "comparison", "better"]):
        return "对比/评测讨论"
    elif any(x in full_text for x in ["tool", "built", "made"]):
        return "工具/项目分享"
    elif "lawsuit" in full_text or "sue" in full_text:
        return "法律/诉讼相关新闻"
    elif "feedback" in full_text:
        return "用户反馈收集"
    elif "update" in full_text:
        return "更新/改进公告"
    elif "limit" in full_text or "quota" in full_text:
        return "使用限制相关讨论"
    elif "hallucination" in full_text:
        return "AI幻觉问题讨论"
    elif "plugin" in full_text:
        return "插件功能更新"
    elif any(x in full_text for x in ["agent", "agentic"]):
        return "AI智能体相关"
    elif any(x in full_text for x in ["code", "coding"]):
        return "编程/代码相关"
    elif "model" in full_text:
        return "模型讨论"
    
    return content[:60] + "..." if content and len(content) > 10 else "社区讨论"


def get_subreddit_desc(subreddit: str) -> str:
    """Get Chinese description for subreddit."""
    key = subreddit.lower()
    return SUBREDDIT_INFO.get(key, (subreddit, f"📍 r/{subreddit}"))[1]


def translate_keywords(text: str) -> str:
    """Add Chinese translations for key AI terms."""
    hints = []
    text_lower = text.lower()
    for en, zh in TERM_TRANSLATIONS.items():
        if en.lower() in text_lower and len(hints) < 4:
            hints.append(f"{en}={zh}")
    return f"💡 {', '.join(hints)}" if hints else ""


def clean_html(raw_html: str) -> str:
    """Remove HTML tags and clean text."""
    clean = re.sub(r'<[^>]+>', '', raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def parse_rss(xml_content: str, subreddit: str) -> List[Dict]:
    """Parse RSS feed XML into post list."""
    posts = []
    try:
        root = ET.fromstring(xml_content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns)
            link = entry.find('atom:link', ns)
            content = entry.find('atom:content', ns)
            published = entry.find('atom:published', ns)
            author = entry.find('atom:author/atom:name', ns)
            
            title_text = title.text if title is not None else "无标题"
            url = link.get('href', '') if link is not None else ""
            content_text = clean_html(content.text or "") if content is not None else ""
            
            # Skip pinned/announcement posts
            if "Announcing" in title_text and "discord" in url.lower():
                continue
                
            posts.append({
                "title": title_text,
                "url": url,
                "content": content_text[:300],
                "published": published.text if published is not None else "",
                "author": (author.text or "").replace("/u/", ""),
                "subreddit": subreddit,
            })
    except ET.ParseError as e:
        print(f"[Error] XML parse error: {e}", file=sys.stderr)
    return posts


def fetch_subreddit_rss(subreddit: str, sort: str = "hot", limit: int = 10) -> List[Dict]:
    """Fetch posts from subreddit RSS feed."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.rss?limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return parse_rss(response.read().decode("utf-8", errors="ignore"), subreddit)
    except Exception as e:
        print(f"[Error] Failed to fetch r/{subreddit}: {e}", file=sys.stderr)
        return []


def format_time_ago(iso_time: str) -> str:
    """Convert ISO time to relative time in Chinese."""
    try:
        dt = datetime.fromisoformat(iso_time.replace('+00:00', '+0000').replace('Z', '+0000'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)}分钟前"
        elif hours < 24:
            return f"{int(hours)}小时前"
        return f"{int(hours / 24)}天前"
    except:
        return ""


def format_output(posts: List[Dict]) -> str:
    """Format posts with Chinese summaries. Limited to 3000 chars for Telegram."""
    if not posts:
        return "❌ 未找到相关帖子"
    
    lines = []
    for i, post in enumerate(posts, 1):
        title = post.get("title", "无标题")
        url = post.get("url", "")
        content = post.get("content", "")
        subreddit = post.get("subreddit", "")
        published = post.get("published", "")
        
        sub_desc = get_subreddit_desc(subreddit)
        keywords = translate_keywords(title + " " + content)
        time_ago = format_time_ago(published)
        zh_title = translate_title(title)
        zh_summary = summarize_content(title, content)
        
        lines.append(f"**【{i}】{title[:50]}**")
        lines.append(f"• 📌 {zh_title}")
        if keywords:
            lines.append(f"• {keywords}")
        time_str = f" · {time_ago}" if time_ago else ""
        lines.append(f"• {sub_desc}{time_str}")
        short_url = url.replace("https://www.reddit.com", "https://reddit.com")
        lines.append(f"• 🔗 {short_url}\n")
    
    # 限制总长度
    result = "\n".join(lines)
    if len(result) > 3000:
        result = result[:3000] + "\n...（内容过长已截断）"
    
    return f"📊 **Reddit AI 社区热帖** (共 {len(posts)} 条)\n\n{result}"


def main():
    parser = argparse.ArgumentParser(description="Fetch Reddit AI posts via RSS")
    parser.add_argument("--sort", choices=["hot", "new", "top", "rising"], default="hot")
    parser.add_argument("--limit", type=int, default=3, help="Posts per subreddit")
    parser.add_argument("--subreddits", type=str, default=None, help="Comma-separated list")
    parser.add_argument("--total", type=int, default=10, help="Max total posts")
    args = parser.parse_args()
    
    subreddits = [s.strip() for s in args.subreddits.split(",")] if args.subreddits else DEFAULT_SUBREDDITS
    all_posts = []
    
    print(f"🔍 抓取 Reddit AI 社区 ({args.sort})...\n", file=sys.stderr)
    for sub in subreddits:
        print(f"   📡 r/{sub}...", file=sys.stderr, end=" ", flush=True)
        posts = fetch_subreddit_rss(sub, args.sort, args.limit)
        print(f"✓ {len(posts)} 篇", file=sys.stderr)
        all_posts.extend(posts)
        time.sleep(0.3)
    
    all_posts = all_posts[:args.total]
    print(f"\n📊 共获取 {len(all_posts)} 篇帖子\n", file=sys.stderr)
    print(format_output(all_posts))


if __name__ == "__main__":
    main()
