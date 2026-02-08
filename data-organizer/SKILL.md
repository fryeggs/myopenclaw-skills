---
name: data-organizer
description: "Automatically scan folders, extract content from PDF, Excel, Word, CSV, JSON, and images, output as JSON or Markdown format."
---

# Data Organizer

## Overview

Automatically scan specified folders, intelligently identify common file types (PDF, Excel, Word, CSV, JSON, images), extract content, and organize into unified JSON or Markdown format output.

## Features

- **Multi-format Support**: PDF, Excel, Word, CSV, JSON, images
- **Content Extraction**: Extract text content from documents
- **Metadata Capture**: File size, modification time, etc.
- **Unified Output**: JSON or Markdown format
- **Recursive Scanning**: Scan subdirectories optionally

## Usage

### Interactive Mode

```bash
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py
```

### Command Line

```bash
# Specify input folder and output format
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py --input /path/to/files --format json

# Recursive scan with Markdown output
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py --input /path/to/files --recursive --format markdown

# Specify output path
python3 ~/.openclaw/skills/data-organizer/scripts/organizer.py --input /path/to/files --output /path/to/output.json
```

## Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--input` | `-i` | Input folder path | Interactive |
| `--output` | `-o` | Output file path (without extension) | Auto-generated |
| `--format` | `-f` | Output format: `json` or `markdown` | `json` |
| `--recursive` | `-r` | Scan subdirectories recursively | `false` |

## Supported File Types

| Type | Extensions |
|------|------------|
| PDF | .pdf |
| Excel | .xlsx, .xls |
| Word | .docx |
| CSV | .csv |
| JSON | .json |
| Image | .png, .jpg, .jpeg |
| Text | .txt, .md, .log |

## Output Formats

### JSON Output

```json
{
  "summary": {
    "total_files": 10,
    "by_type": {
      "pdf": 3,
      "excel": 2,
      "word": 1
    }
  },
  "files": [
    {
      "path": "/path/to/file.pdf",
      "type": "pdf",
      "name": "document.pdf",
      "content": "Extracted text content...",
      "metadata": {
        "size": 1024,
        "modified": "2024-01-15T10:30:00"
      }
    }
  ]
}
```

### Markdown Output

```markdown
# File Organization Report

## Summary
- Total files: 10
- PDF: 3
- Excel: 2

## File List

### document.pdf
- **Path**: /path/to/file.pdf
- **Type**: PDF
- **Size**: 1024 bytes

**Content**:
Extracted text content...
```

## Dependencies

```bash
pip install openpyxl python-docx pdfplumber pillow
```

## Troubleshooting

**Issue**: pdfplumber returns empty PDF
**Solution**: Ensure PDF is not a scanned image, use OCR

**Issue**: Excel file read error
**Solution**: Install openpyxl: `pip install openpyxl`

**Issue**: File type not detected
**Solution**: File type determined by extension, ensure files have correct extensions
