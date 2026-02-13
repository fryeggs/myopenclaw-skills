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
