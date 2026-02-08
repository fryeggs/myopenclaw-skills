# 输出格式说明

本文档详细说明 data-organizer 的两种输出格式：JSON 和 Markdown。

## JSON 格式

### 结构概览

```json
{
  "generated_at": "ISO 时间戳",
  "summary": {
    "total_files": 整数,
    "by_type": { "类型名": 数量 },
    "total_size_bytes": 整数
  },
  "files": [
    {
      "path": "绝对路径",
      "type": "文件类型",
      "name": "文件名",
      "content": "提取的文本内容",
      "metadata": {
        "size": 文件大小(bytes),
        "modified": "修改时间 ISO 格式",
        "extension": ".扩展名"
      }
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `generated_at` | 字符串 | 整理完成的时间戳 |
| `summary` | 对象 | 统计摘要信息 |
| `summary.total_files` | 整数 | 处理的文件总数 |
| `summary.by_type` | 对象 | 按类型统计的文件数量 |
| `summary.total_size_bytes` | 整数 | 所有文件的总大小 |
| `files` | 数组 | 每个文件的详细信息 |

### 文件对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | 字符串 | 文件的绝对路径 |
| `type` | 字符串 | 识别的文件类型（pdf/excel/word 等） |
| `name` | 字符串 | 文件名（不含路径） |
| `content` | 字符串 | 提取的文本内容 |
| `metadata` | 对象 | 文件元数据 |
| `metadata.size` | 整数 | 文件大小（字节） |
| `metadata.modified` | 字符串 | 最后修改时间 |
| `metadata.extension` | 字符串 | 文件扩展名 |

### JSON 输出示例

```json
{
  "generated_at": "2024-01-15T10:30:00",
  "summary": {
    "total_files": 5,
    "by_type": {
      "pdf": 2,
      "excel": 1,
      "word": 1,
      "text": 1
    },
    "total_size_bytes": 5242880
  },
  "files": [
    {
      "path": "/home/user/docs/report.pdf",
      "type": "pdf",
      "name": "report.pdf",
      "content": "第一章\n\n本文档是年度工作报告...",
      "metadata": {
        "size": 1048576,
        "modified": "2024-01-10T08:00:00",
        "extension": ".pdf"
      }
    }
  ]
}
```

## Markdown 格式

### 结构概览

```markdown
# 文件整理报告

生成时间: YYYY-MM-DD HH:MM:SS

## 统计摘要

- 总文件数: N
- 总大小: N bytes

### 按类型统计

- 类型1: 数量
- 类型2: 数量

---

## 文件列表

### 1. 文件名

- **路径**: 绝对路径
- **类型**: 文件类型
- **大小**: 大小 bytes

**内容预览**:
```
内容预览...
```

---
```

### 字段说明

Markdown 格式更注重可读性，适合直接查看：

| 区域 | 内容 |
|------|------|
| 标题 | `# 文件整理报告` |
| 生成时间 | 整理完成的时间 |
| 统计摘要 | 总文件数、总大小 |
| 类型统计 | 每种类型的文件数量 |
| 文件列表 | 每个文件的详细信息 |

### Markdown 输出示例

```markdown
# 文件整理报告

生成时间: 2024-01-15 10:30:00

## 统计摘要
- 总文件数: 5
- 总大小: 5,242,880 bytes

### 按类型统计
- excel: 2
- pdf: 1
- word: 1
- text: 1

---

## 文件列表

### 1. budget.xlsx

- **路径**: /home/user/docs/budget.xlsx
- **类型**: excel
- **大小**: 204800 bytes

**内容预览**:
```
[工作表: Q1]
项目	预算	实际
收入	10000	12000
支出	8000	7500
```

---

### 2. report.pdf

- **路径**: /home/user/docs/report.pdf
- **类型**: pdf
- **大小**: 1048576 bytes

**内容预览**:
```
第一章

本文档是年度工作报告，
详细总结了...
...
```
```

## 格式对比

| 特性 | JSON | Markdown |
|------|------|----------|
| 可读性 | 需格式化查看 | 直观易读 |
| 程序处理 | 易于解析 | 需解析 |
| 文件大小 | 紧凑 | 稍大 |
| 查看方式 | 需工具/代码 | 任意编辑器 |
| 搜索 | 支持全文搜索 | 支持 |

## 使用建议

### 使用 JSON 格式的场景

- 需要程序进一步处理结果
- 集成到自动化流程
- 数据分析
- API 数据交换

### 使用 Markdown 格式的场景

- 快速查看整理结果
- 分享给他人
- 文档记录
- 存档备查

## 输出文件命名

如果不指定输出文件名，系统会自动生成：

- JSON: `organized_YYYYMMDD_HHMMSS.json`
- Markdown: `organized_YYYYMMDD_HHMMSS.md`

## 编码说明

- JSON 输出始终使用 UTF-8 编码
- Markdown 输出始终使用 UTF-8 编码
- 内容中的特殊字符会进行适当转义
