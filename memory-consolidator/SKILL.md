---
name: memory-consolidator
description: "Scheduled incremental merge of Claude and OpenClaw memory files, auto-deduplicate and generate condensed high-quality summaries using Claude API."
---

# Memory Consolidator

## Overview

Automatically merge memory files from Claude and OpenClaw systems, deduplicate content, and generate condensed high-quality summaries. Runs every 50 minutes via cron, monitors changes via hash comparison.

## Features

- **Scheduled Execution**: Runs every 50 minutes automatically
- **Incremental Update**: Only process changed files (hash comparison)
- **Smart Deduplication**: Remove duplicate and similar content
- **Claude API Integration**: Generate condensed high-quality summaries
- **Multi-source Support**: CLAUDE.md, MEMORY.md, daily memory files
- **Local Storage**: Output to `~/.openclaw/qmd_memory/`

## Usage

### Manual Execution

```bash
# Run immediately
python3 ~/.openclaw/skills/memory-consolidator/scripts/main.py --run-now
```

### Check Status

```bash
# Last run timestamp
cat ~/.openclaw/qmd_memory/.last_run

# Output files
ls -la ~/.openclaw/qmd_memory/
```

## Configuration

Modify `references/config.json`:

```json
{
  "sources": [
    "~/.claude/CLAUDE.md",
    "~/.openclaw/MEMORY.md",
    "~/.openclaw/workspace/memory/*.md"
  ],
  "output_dir": "~/.openclaw/qmd_memory",
  "cron_interval_minutes": 50,
  "claude_model": "claude-sonnet-4-20250514"
}
```

## Workflow

1. **Collect**: Read source files (CLAUDE.md, MEMORY.md, memory/*.md)
2. **Detect Changes**: Calculate file hash, determine if processing needed
3. **Condense**: Call Claude API to extract core content
4. **Deduplicate**: Compare with existing content, remove duplicates
5. **Output**: Write to `~/.openclaw/qmd_memory/` directory

## Output Structure

```
~/.openclaw/qmd_memory/
├── consolidated.md      # Merged condensed memory
├── .last_run            # Last run timestamp
├── sources/            # Source file snapshots
│   ├── CLAUDE.md
│   ├── MEMORY.md
│   └── 2026-02-05.md
└── logs/               # Runtime logs
```

## Dependencies

- Python 3.10+
- `httpx` HTTP client
- `python-dotenv`

## Install Dependencies

```bash
pip install httpx python-dotenv
```

## Cron Integration

Add to crontab:

```bash
crontab -e

# Add line (every 50 minutes)
*/50 * * * * /usr/bin/python3 ~/.openclaw/skills/memory-consolidator/scripts/main.py --run-now >> ~/.openclaw/qmd_memory/logs/cron.log 2>&1
```

## Logs

Runtime logs saved to `~/.openclaw/qmd_memory/logs/` directory.

## Source Files

| File | Description |
|------|-------------|
| `~/.claude/CLAUDE.md` | Claude Code global knowledge base |
| `~/.openclaw/MEMORY.md` | OpenClaw long-term memory |
| `~/.openclaw/workspace/memory/*.md` | Daily learning records |
