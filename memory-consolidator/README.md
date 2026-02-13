# Memory Consolidator

## English Description

Scheduled incremental merge of Claude and OpenClaw memory files, auto-deduplicate and generate condensed high-quality summaries using Claude API. Runs every 50 minutes via cron, monitors changes via hash comparison, and stores consolidated memory to `~/.openclaw/qmd_memory/`.

### Features

- **Scheduled Execution**: Runs every 50 minutes automatically
- **Incremental Update**: Only process changed files (hash comparison)
- **Smart Deduplication**: Remove duplicate and similar content
- **Claude API Integration**: Generate condensed high-quality summaries
- **Multi-source Support**: CLAUDE.md, MEMORY.md, daily memory files
- **Local Storage**: Output to `~/.openclaw/qmd_memory/`

## 中文说明

定时增量合并 Claude 与 OpenClaw 的 Memory 文件，自动去重并提炼为高质量的精简摘要。使用 Claude API 生成摘要，通过 hash 对比监控变化，每 50 分钟通过 cron 执行。

### 功能特性

- **定时执行**：每 50 分钟自动运行
- **增量更新**：仅处理有变化的文件（hash 对比）
- **智能去重**：自动去除重复和相似内容
- **Claude API 集成**：生成高质量精简摘要
- **多源支持**：CLAUDE.md、MEMORY.md、每日记忆文件
- **本地存储**：输出到 `~/.openclaw/qmd_memory/`

## Quick Start / 快速开始

```bash
# Manual execution / 手动执行
python3 ~/.openclaw/skills/memory-consolidator/scripts/main.py --run-now

# Check status / 查看状态
cat ~/.openclaw/qmd_memory/.last_run

# View output / 查看输出
cat ~/.openclaw/qmd_memory/consolidated.md
```

## Source Files / 源文件

| File / 文件 | Description / 描述 |
|------------|-------------------|
| `~/.claude/CLAUDE.md` | Claude Code global knowledge base / Claude Code 全局知识库 |
| `~/.openclaw/MEMORY.md` | OpenClaw long-term memory / OpenClaw 长期记忆 |
| `~/.openclaw/workspace/memory/*.md` | Daily learning records / 每日学习记录 |

See `SKILL.md` for detailed configuration.

查看 `SKILL.md` 了解详细配置。
