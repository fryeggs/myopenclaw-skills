---
name: web-content-learner
description: "Extract content from web pages using Jina AI, transcribe videos using yt-dlp + Whisper GPU acceleration."
---

# Web Content Learner

# web-content-learner Skill

从网页和视频中提取内容并转文字。

## 功能

- **网页提取**: Jina AI API → Brave Search 回退
- **视频转文字**: yt-dlp + Whisper GPU 加速

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 处理网页
python scripts/web_content_learner.py --url "https://example.com"

# 处理视频
python scripts/web_content_learner.py --video "https://youtube.com/watch?v=..."
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--url` | 网页 URL |
| `--video` | 视频 URL |
| `--output` | 输出目录 (默认: /media/qingshan/D/videodown) |
| `--gpu` | 使用 GPU (默认: True) |

## Python API

```python
from web_content_learner import ContentLearner

learner = ContentLearner(
    output_dir="/media/qingshan/D/videodown",
    jina_api_key="your-jina-key",
    use_gpu=True
)

# 处理网页
result = learner.process_url("https://example.com")

# 处理视频
result = learner.process_video("https://youtube.com/watch?v=...")
```

## 环境要求

- **Python**: 3.12+ (需要 CUDA 支持)
- **GPU**: Quadro RTX 5000 (16GB)
- **依赖**: 见 requirements.txt

## 配置

- `JINA_API_KEY`: Jina AI API Key (可选)
- `BRAVE_API_KEY`: Brave Search API Key (可选)

## 输出

结果保存到 `/media/qingshan/D/videodown/`:
- `url_YYYYMMDD_HHMMSS.json` - 网页内容
- `video_YYYYMMDD_HHMMSS.json` - 视频转录

## 智能搜索功能

### IntelligentHandler

自动判断用户意图，调用对应功能：

```python
from web_content_learner import IntelligentHandler

handler = IntelligentHandler()

# 自动判断意图并处理
result = handler.process("什么是 AI")  # 意图: question
result = handler.process("https://github.com/...")  # 意图: webpage
result = handler.process("这个视频说了什么: https://...")  # 意图: video_transcribe
```

### 支持的意图

| 意图 | 关键词 | 处理 |
|------|--------|------|
| search | 搜索、找 | Brave搜索 + LLM总结 |
| question | 什么是、怎么、? | 搜索 + 总结 |
| webpage | URL | 网页抓取 + LLM总结 |
| video_download | 下载 | 视频下载 |
| video_transcribe | 转文字、字幕 | 视频转文字 |

### SmartSearcher

类似 Tavily 的搜索功能：

```python
from web_content_learner import SmartSearcher, ContentLearner

# 方法1：通过 ContentLearner
learner = ContentLearner()
result = learner.smart_search("什么是 GraphRAG")

# 返回
{
    "success": True,
    "query": "什么是 GraphRAG",
    "answer": "GraphRAG 是微软的...",  # LLM 总结
    "sources": [{"title": "...", "url": "..."}]
}
```

### Brave Search

直接使用 Brave API 搜索：

```python
from web_content_learner import BraveSearcher

searcher = BraveSearcher()
result = searcher.search("AI news", count=5)
# 返回: [{"title": "...", "url": "...", "description": "..."}]
```
