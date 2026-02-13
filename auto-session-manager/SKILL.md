---
name: auto-session-manager
description: "Auto-manage OpenClaw session lifecycle: context summarization on overflow, auto-restart on unresponsive gateway, quota alert notifications."
---

# Auto Session Manager

## Overview

Background daemon that automatically manages OpenClaw session lifecycle, handling context management, failure recovery, and resource monitoring.

## Features

- **Context Management**: Monitor OpenClaw, Claude Code, OpenCode conversation contexts; automatically extract key information when exceeding 80% threshold
- **Multi-platform Monitoring**: Simultaneously monitor context usage across OpenClaw, Claude Code, and OpenCode platforms
- **Session Continuity**: Automatically create new sessions inheriting topic and historical summaries
- **Failure Recovery**: Restart gateway service when unresponsive for 3+ minutes; trigger Claude Code repair on repeated failures
- **Resource Monitoring**: Detect MiniMax API quota, pause work and notify when quota is low

## Usage

### Foreground Mode (Testing)

```bash
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode foreground
```

### Daemon Mode

```bash
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode daemon --interval 60
```

### Health Check

```bash
~/.openclaw/skills/auto-session-manager/scripts/health_check.py
```

## Workflow

### 1. Context Monitoring & Summarization

```
OpenClaw Context Check → > 80%?
Claude Code Context Check → > 80%?
OpenCode Context Check → > 80%?

Triggered:
  ├─ Yes: Extract key information → Save to ~/.openclaw/.session_memory/{session_id}.json
  └─ No: Continue monitoring
```

### 2. Feed Notifications (All Summary Switches)

```
Any platform triggers summary switch → Notify feed topic (466)
  ├─ OpenClaw: "OpenClaw context usage reached XX%, switched to new session"
  ├─ Claude Code: "Claude Code context usage reached XX%, summary switch triggered"
  └─ OpenCode: "OpenCode context usage reached XX%, summary switch triggered"
```

### 3. Session Switching

```
Context exceeded → Create new session (inherit topic) → Read historical summary → Inject system prompt
```

### 4. Failure Recovery

```
Gateway unresponsive > 3min → Restart gateway service → Verify recovery
  └─ Failed > 3 times → Trigger Claude Code repair
```

### 5. Resource Alerts

```
Detect MiniMax quota → Below threshold → Pause work → Notify feed topic 466
```

## Scripts

| Script | Purpose |
|--------|---------|
| `monitor.py` | Main monitoring process, coordinates all modules |
| `session_manager.py` | Session creation, query, switch management |
| `memory_manager.py` | Key information extraction and long-term memory access |
| `gateway_monitor.py` | Gateway service health check and restart |
| `health_check.py` | Complete system health check |

## Configuration

Adjust via environment variables:

```bash
# Context threshold (default 80%)
export ASM_CONTEXT_THRESHOLD=80

# Gateway unresponsive timeout (default 180 seconds)
export ASM_GATEWAY_TIMEOUT=180

# Monitoring interval (default 60 seconds)
export ASM_MONITOR_INTERVAL=60

# MiniMax quota alert threshold (default 100 calls)
export ASM_MINIMAX_QUOTA_THRESHOLD=100

# Claude Code session estimated tokens (default 10000)
export ASM_CC_ESTIMATE_TOKENS=10000

# OpenCode session estimated tokens (default 8000)
export ASM_OC_ESTIMATE_TOKENS=8000
```

## Manual Operations

### Force Context Summarization

```bash
~/.openclaw/skills/auto-session-manager/scripts/memory_manager.py \
  --action extract \
  --session-id <SESSION_ID>
```

### Manual Gateway Restart

```bash
~/.openclaw/skills/auto-session-manager/scripts/gateway_monitor.py --restart
```

### List Current Sessions

```bash
~/.openclaw/skills/auto-session-manager/scripts/session_manager.py --list
```

## Output Locations

- Session memory: `~/.openclaw/.session_memory/*.json`
- Monitoring logs: `~/.openclaw/logs/asm_*.log`
- State file: `~/.openclaw/.asm_state.json`

## Troubleshooting

### Monitor Process Not Running

```bash
# Check process
ps aux | grep asm_monitor

# Restart
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode daemon
```

### Gateway Restart Failed

```bash
# Check detailed error
~/.openclaw/skills/auto-session-manager/scripts/gateway_monitor.py --debug

# Manual intervention
systemctl --user restart openclaw-gateway
```

## Related Documentation

- `references/context-management.md`: Context management detailed design
- `references/session-flow.md`: Session switch flow explanation
- `references/failure-recovery.md`: Failure recovery strategy
