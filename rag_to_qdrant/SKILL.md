---
name: rag_to_qdrant
description: "Monitor directory changes, auto-vectorize using BGE-M3 and store to Qdrant vector database. Supports Telegram RAG retrieval."
---

# Rag_To_Qdrant

# RAG to Qdrant Skill

自动监控指定目录，新增文件 → BGE-M3 向量化 → 存入 Qdrant 向量数据库，支持 Telegram RAG 检索。

## 快速开始

```bash
# 首次运行（扫描目录并导入所有文件）
python scripts/main.py --watch-dir /media/qingshan/D/jxh_data --mode full

# 增量模式（仅处理新增/修改的文件）
python scripts/main.py --watch-dir /media/qingshan/D/jxh_data --mode incremental

# 设置 cron 每 2 小时自动执行
crontab -e
# 添加: 0 */2 * * * python ~/.openclaw/skills/rag_to_qdrant/scripts/main.py --watch-dir /media/qingshan/D/jxh_data --mode incremental
```

## 详细用法

### 命令行参数

| 参数 | 短参数 | 说明 | 默认值 |
|------|--------|------|--------|
| `--watch-dir` | `-d` | 待监控的目录路径 | 必填 |
| `--mode` | `-m` | 运行模式：`full`(全量) 或 `incremental`(增量) | `incremental` |
| `--qdrant-url` | `-q` | Qdrant 服务器地址 | `http://localhost:6333` |
| `--collection` | `-c` | Qdrant 集合名称 | `jxh_data_rag` |
| `--model` | `-M` | Ollama 模型名称 | `bge-m3` |

### 使用示例

```bash
# 首次全量导入
python scripts/main.py -d /media/qingshan/D/jxh_data -m full

# 增量监控（cron 使用）
python scripts/main.py -d /media/qingshan/D/jxh_data -m incremental

# 自定义 Qdrant 和模型
python scripts/main.py -d /data/docs -q http://192.168.1.100:6333 -c my_collection -M bge-m3
```

## 核心功能

### 1. 目录监控（Hash 对比）

- 使用 MD5/SHA256 hash 对比检测文件变化
- 增量模式仅处理新增和修改的文件
- 自动记录已处理文件的 hash 到状态文件

### 2. 文件类型支持

- **.md** - Markdown 文件
- **.txt** - 纯文本文件
- **.json** - JSON 文件

### 3. 向量化（BGE-M3）

- 调用 Ollama BGE-M3 模型生成 1024 维向量
- 支持中英文混合文本
- 默认 Ollama 地址：`http://localhost:11434`

### 4. Qdrant 存储

- 存储到本地 Qdrant（localhost:6333）
- 自动创建集合和索引
- 支持批量写入

### 5. Telegram RAG 集成

- 与 Telegram RAG 频道联动
- 支持语义检索查询

## 配置说明

### 配置文件

首次运行会在 `~/.config/rag_to_qdrant/config.json` 创建配置：

```json
{
  "qdrant_url": "http://localhost:6333",
  "ollama_url": "http://localhost:11434",
  "model": "bge-m3",
  "collection": "jxh_data_rag",
  "watch_dir": "/media/qingshan/D/jxh_data",
  "state_file": "~/.config/rag_to_qdrant/processed_files.json"
}
```

## 依赖安装

```bash
pip install qdrant-client requests hashlib watchdog
```

## 文件结构

```
rag_to_qdrant/
├── SKILL.md           # 本文档
├── requirements.txt    # Python 依赖
├── scripts/
│   ├── main.py        # 主程序入口
│   ├── scanner.py     # 目录扫描和 hash 对比
│   ├── embedder.py    # BGE-M3 向量化
│   ├── qdrant_store.py # Qdrant 存储
│   └── rag_search.py  # RAG 检索（供 Telegram 调用）
└── references/
    └── README.md      # 详细技术文档
```

## 故障排除

**问题**：Ollama 连接失败
**解决**：确保 Ollama 运行且 BGE-M3 模型已拉取
```bash
ollama pull bge-m3
```

**问题**：Qdrant 连接失败
**解决**：启动 Qdrant 服务
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**问题**：文件未检测到变化
**解决**：删除状态文件重新扫描
```bash
rm ~/.config/rag_to_qdrant/processed_files.json
```
