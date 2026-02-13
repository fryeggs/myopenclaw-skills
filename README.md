# My OpenClaw Skills | 我的 OpenClaw 技能集合

## English

This repository contains OpenClaw skills developed by me for personal use.

### Skills | 技能

| Skill | Description |
|-------|-------------|
| [gateway-monitor](./gateway-monitor/) | Monitor OpenClaw Gateway health and auto-restart on crash. Claude rescue protocol included. |
| [openclaw-memory-skill](./openclaw-memory-skill/) | Daily monitoring of win4r/claude-code-clawdbot-skill and local memory sync to GitHub at 2 AM. User notification at 8 AM. |
| [github-find-context7](./github-find-context7/) | GitHub operations (search, create, analyze) + Context7 documentation lookup for any library. |

### Auto-Sync

All skills are automatically synced to this repository daily at 2 AM.

### Usage

```bash
/use gateway-monitor check
/use openclaw-memory-skill check
/use github-find-context7 find react
```

---

## 中文

这个仓库包含我为个人使用开发的 OpenClaw 技能。

### 技能

| 技能 | 描述 |
|------|------|
| [gateway-monitor](./gateway-monitor/) | 监控 OpenClaw Gateway 状态，崩溃时自动重启。包含 Claude 救援协议。 |
| [openclaw-memory-skill](./openclaw-memory-skill/) | 每天凌晨 2 点监控 win4r 项目更新并同步本地内存到 GitHub。早上 8 点通知用户。 |
| [github-find-context7](./github-find-context7/) | GitHub 操作（搜索、创建、分析）+ Context7 文档查询（任意库的官方文档）。 |

### 自动同步

所有技能每天凌晨 2 点自动同步到此仓库。

### 使用方法

```bash
/use gateway-monitor check
/use openclaw-memory-skill check
/use github-find-context7 find react
```

---

## Skills Details | 技能详情

### gateway-monitor

Monitor OpenClaw Gateway health with auto-recovery. Includes:
- Process monitoring
- HTTP health checks
- Auto-restart on failure
- Claude rescue protocol

### openclaw-memory-skill

Daily sync workflow:
1. 2 AM: Check win4r project updates
2. 2 AM: Check local MEMORY.md changes
3. 2 AM: Merge and sync to GitHub
4. 8 AM: Notify user about updates

### github-find-context7

Integrated GitHub operations:
- Search repositories, code, issues, users
- Create repos, issues, PRs
- Repository health analysis
- Context7 documentation lookup
- Deployment guides

---

**Repository**: [fryeggs/myopenclaw-skills](https://github.com/fryeggs/myopenclaw-skills)
