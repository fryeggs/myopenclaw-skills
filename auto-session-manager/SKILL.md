---
name: auto-session-manager
description: "自动管理 OpenClaw 会话生命周期：上下文超限自动摘要记忆、无响应自动重启、额度不足自动通知。使用场景：当对话上下文接近 80% 阈值、gateway 无响应超过 3 分钟、或需要定期维护会话状态时。"
---

# Auto Session Manager

自动管理 OpenClaw 会话生命周期的后台守护进程，负责上下文管理、故障恢复和资源监控。

## 核心功能

- **上下文管理**：监测对话窗口上下文使用率，超 80% 时自动提炼关键信息并保存至长期记忆
- **会话续接**：自动创建新会话并继承原 topic 和历史摘要，保持对话连贯性
- **故障恢复**：gateway 与 tg 通信超 3 分钟无响应时自动重启，重启失败时触发 Claude Code 介入修复
- **资源监控**：检测 MiniMax API 额度，额度不足时暂停工作并通知 feed topic (466)

## 快速开始

### 前台运行（测试用）

```bash
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode foreground
```

### 后台守护进程

```bash
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode daemon --interval 60
```

### 检查服务状态

```bash
~/.openclaw/skills/auto-session-manager/scripts/health_check.py
```

## 工作流程

### 1. 上下文监测与摘要

```
检测上下文使用率 → 超 80%?
  ├─ 是：提炼关键信息 → 保存到 ~/.openclaw/.session_memory/{session_id}.json
  └─ 否：继续监控
```

### 2. 会话切换

```
上下文超限 → 创建新会话(继承 topic) → 读取历史摘要 → 注入系统提示
```

### 3. 故障恢复

```
Gateway 无响应 > 3min → 重启 gateway 服务 → 验证恢复
  └─ 失败 > 3 次 → 触发 Claude Code 修复
```

### 4. 资源告警

```
检测 MiniMax 额度 → 不足阈值 → 暂停工作 → 通知 feed topic 466
```

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `monitor.py` | 主监控进程，协调各模块工作 |
| `session_manager.py` | 会话创建、查询、切换管理 |
| `memory_manager.py` | 关键信息提取与长期记忆存取 |
| `gateway_monitor.py` | gateway 服务健康检查与重启 |
| `health_check.py` | 完整系统健康检查 |

## 配置项

可通过环境变量或配置文件调整：

```bash
# 上下文阈值（默认 80%）
export ASM_CONTEXT_THRESHOLD=80

# Gateway 无响应超时（默认 180 秒）
export ASM_GATEWAY_TIMEOUT=180

# 监控间隔（默认 60 秒）
export ASM_MONITOR_INTERVAL=60

# MiniMax 额度告警阈值（默认 100 次调用）
export ASM_MINIMAX_QUOTA_THRESHOLD=100
```

## 手动操作

### 强制触发上下文摘要

```bash
~/.openclaw/skills/auto-session-manager/scripts/memory_manager.py \
  --action extract \
  --session-id <会话ID>
```

### 手动重启 Gateway

```bash
~/.openclaw/skills/auto-session-manager/scripts/gateway_monitor.py --restart
```

### 查看当前会话列表

```bash
~/.openclaw/skills/auto-session-manager/scripts/session_manager.py --list
```

## 输出位置

- 会话记忆：`~/.openclaw/.session_memory/*.json`
- 监控日志：`~/.openclaw/logs/asm_*.log`
- 状态文件：`~/.openclaw/.asm_state.json`

## 故障排查

### 监控进程未运行

```bash
# 检查进程
ps aux | grep asm_monitor

# 重新启动
~/.openclaw/skills/auto-session-manager/scripts/monitor.py --mode daemon
```

### Gateway 重启失败

```bash
# 查看详细错误
~/.openclaw/skills/auto-session-manager/scripts/gateway_monitor.py --debug

# 手动介入
systemctl --user restart openclaw-gateway
```

## 相关文档

- `references/context-management.md`：上下文管理详细设计
- `references/session-flow.md`：会话切换流程说明
- `references/failure-recovery.md`：故障恢复策略
