# 故障恢复策略

## 1. Gateway 无响应

### 检测条件
- 3 分钟内无响应
- API 调用超时
- WebSocket 断开

### 恢复流程

```
无响应检测 → 优雅重启 → 验证恢复
                              ↓
                        成功 → 继续监控
                              ↓
                        失败 → Claude Code 介入
```

### 重启命令

```bash
# 自动重启
~/.openclaw/skills/auto-session-manager/scripts/gateway_monitor.py --restart

# 手动重启
systemctl --user restart openclaw-gateway
```

## 2. Claude Code 介入修复

### 触发条件
- Gateway 重启失败
- 连续 3 次重启失败
- 系统错误需要人工介入

### 修复流程

```bash
# Claude Code 自动介入
claude -p "Gateway 重启失败，请检查以下日志并尝试修复:
1. 检查日志: tail -100 ~/.openclaw/logs/gateway_monitor.log
2. 查看错误: ~/.openclaw/logs/openclaw.log
3. 尝试手动重启或修复配置"
```

## 3. 常见错误

### 3.1 端口占用

```bash
# 检查端口
netstat -tlnp | grep 18789

# 杀掉占用进程
pkill -9 -f "openclaw.*18789"
```

### 3.2 配置文件错误

```bash
# 验证配置
openclaw doctor --non-interactive

# 查看错误
tail -50 ~/.openclaw/logs/openclaw.log
```

## 4. 通知机制

### Telegram 通知

| 场景 | Topic | 消息 |
|------|-------|------|
| Gateway 重启成功 | work (464) | ✅ Gateway 已重启 |
| 重启失败 | work (464) | ⚠️ Gateway 重启失败 |
| Claude Code 介入 | work (464) | 🔧 Claude Code 介入修复 |
| API 额度不足 | feed (466) | ⚠️ MiniMax 额度不足 |

## 5. 日志位置

```
~/.openclaw/logs/
├── gateway_monitor.log    # Gateway 监控日志
├── openclaw.log         # OpenClaw 主日志
└── health_report.json   # 健康检查报告
```
