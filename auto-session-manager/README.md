# Auto Session Manager

## English Description

Auto-monitor session context, detect overflow thresholds, perform intelligent summarization, and optionally auto-restart unresponsive sessions. Includes failure recovery and quota alert features.

### Features

- **Context Monitoring**: Track token usage and detect overflow
- **Auto-Summarize**: Generate summaries when threshold reached
- **Auto-Restart**: Restart gateway on session hang
- **Failure Recovery**: Multiple recovery strategies
- **Quota Alerts**: Notify before quota limits

## 中文说明

自动监控会话上下文，检测溢出阈值，执行智能摘要，可选地自动重启无响应会话。包含故障恢复和配额告警功能。

### 功能特性

- **上下文监控**：跟踪令牌使用情况并检测溢出
- **自动摘要**：达到阈值时生成摘要
- **自动重启**：会话挂起时重启网关
- **故障恢复**：多种恢复策略
- **配额告警**：在配额限制前通知

## Quick Start / 快速开始

```bash
# Run auto-session-manager
python3 ~/.openclaw/skills/auto-session-manager/scripts/session_manager.py --monitor

# Check session status
python3 ~/.openclaw/skills/auto-session-manager/scripts/session_manager.py --status
```

## Configuration / 配置

See `SKILL.md` for detailed configuration.

查看 `SKILL.md` 了解详细配置。
