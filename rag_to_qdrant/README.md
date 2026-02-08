# RAG to Qdrant

## English Description

Monitor specified directory, automatically vectorize new/modified files using Ollama BGE-M3 model, and store to Qdrant vector database. Supports hybrid search (vector + keyword) and integrates with Telegram RAG channel for semantic retrieval.

### Features

- **Directory Monitoring**: Watch `/media/qingshan/D/jxh_data` for changes
- **BGE-M3 Vectorization**: 1024-dimensional vectors via Ollama
- **Qdrant Storage**: Local vector database (localhost:6333)
- **Hybrid Search**: Vector + keyword search
- **Telegram RAG**: Semantic retrieval for RAG channel

## 中文说明

监控指定目录，使用 Ollama BGE-M3 模型自动向量化新增/修改的文件，并存储到 Qdrant 向量数据库。支持混合搜索（向量 + 关键词），并与 Telegram RAG 频道集成实现语义检索。

### 功能特性

- **目录监控**：监控 `/media/qingshan/D/jxh_data` 目录变化
- **BGE-M3 向量化**：通过 Ollama 生成 1024 维向量
- **Qdrant 存储**：本地向量数据库（localhost:6333）
- **混合搜索**：向量 + 关键词搜索
- **Telegram RAG**：RAG 频道语义检索

## Quick Start / 快速开始

```bash
# Full scan and import / 全量扫描导入
python3 ~/.openclaw/skills/rag_to_qdrant/scripts/main.py -d /media/qingshan/D/jxh_data -m full

# Incremental mode / 增量模式
python3 ~/.openclaw/skills/rag_to_qdrant/scripts/main.py -d /media/qingshan/D/jxh_data -m incremental

# RAG search / RAG 搜索
python3 ~/.openclaw/skills/rag_to_qdrant/scripts/rag_search.py "your query"
```

## Supported File Types / 支持的文件类型

| Type / 类型 | Extensions / 扩展名 |
|-------------|-------------------|
| Markdown | .md |
| Text / 文本 | .txt |
| JSON | .json |

See `SKILL.md` for detailed documentation.

查看 `SKILL.md` 了解详细文档。
