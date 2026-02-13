# Web Content Learner

## English Description

Extract content from web pages and transcribe videos to text. Uses Jina AI API for web extraction, yt-dlp for video downloads, and OpenAI Whisper (GPU-accelerated) for transcription.

### Features

- **Web Extraction**: Jina AI API with Brave Search fallback
- **Video Transcription**: yt-dlp + Whisper GPU acceleration
- **GPU Support**: Quadro RTX 5000 (16GB VRAM)
- **Multiple Formats**: Support for various video platforms

## 中文说明

从网页提取内容并将视频转文字。使用 Jina AI API 进行网页提取，yt-dlp 下载视频，OpenAI Whisper（GPU 加速）进行转录。

### 功能特性

- **网页提取**：Jina AI API，Brave Search 回退
- **视频转录**：yt-dlp + Whisper GPU 加速
- **GPU 支持**：Quadro RTX 5000（16GB VRAM）
- **多格式支持**：支持各种视频平台

## Quick Start / 快速开始

```bash
# Process URL / 处理网页
python3 ~/.openclaw/skills/web-content-learner/scripts/web_content_learner.py --url "https://example.com"

# Process video / 处理视频
python3 ~/.openclaw/skills/web-content-learner/scripts/web_content_learner.py --video "https://youtube.com/watch?v=..."

# With GPU / 使用 GPU
python3 ~/.openclaw/skills/web-content-learner/scripts/web_content_learner.py --video "..." --gpu
```

## Output / 输出

Results saved to `/media/qingshan/D/videodown/`:
- `url_YYYYMMDD_HHMMSS.json` - Web content / 网页内容
- `video_YYYYMMDD_HHMMSS.json` - Video transcription / 视频转录

See `SKILL.md` for detailed documentation.

查看 `SKILL.md` 了解详细文档。
