# Data Organizer

## English Description

Automatically scan folders, intelligently identify common file types (PDF, Excel, Word, CSV, JSON, images), extract content, and organize into unified JSON or Markdown format output.

### Features

- **Multi-format Support**: PDF, Excel, Word, CSV, JSON, images
- **Content Extraction**: Extract text content from documents
- **Metadata**: Capture file size, modification time, etc.
- **Unified Output**: JSON or Markdown format

## 中文说明

自动扫描指定文件夹，智能识别 PDF、Excel、Word、CSV、JSON、图片等常见文件类型，提取内容并整理成统一格式输出。

### 功能特性

- **多格式支持**：PDF、Excel、Word、CSV、JSON、图片
- **内容提取**：从文档中提取文本内容
- **元数据**：捕获文件大小、修改时间等
- **统一输出**：JSON 或 Markdown 格式

## Quick Start / 快速开始

```bash
# Interactive mode / 交互式模式
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py --interactive

# Specify folder / 指定文件夹
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py -i /path/to/files -f markdown

# Recursive scan / 递归扫描
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py -i /path/to/files -r -f json
```

## Supported File Types / 支持的文件类型

| Type / 类型 | Extensions / 扩展名 |
|-------------|-------------------|
| PDF | .pdf |
| Excel | .xlsx, .xls |
| Word | .docx |
| CSV | .csv |
| JSON | .json |
| Image / 图片 | .png, .jpg, .jpeg |

See `SKILL.md` for detailed documentation.

查看 `SKILL.md` 了解详细文档。
