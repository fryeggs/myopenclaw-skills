# Memory Consolidator - 开发归档

## 任务信息
- **名称**: memory-consolidator
- **开发时间**: 2026-02-07 00:30 GMT+8
- **遵循标准**: Anthropic Agent Skills + OpenSpec

## 开发流程

### 1. /opsx:onboard
- 分析 CLAUDE.md 和 workspace/memory/*.md
- 确定源文件和目标目录

### 2. /opsx:new
- 创建项目结构
- 定义 SKILL.yaml 和 config.json

### 3. /opsx:apply
- 实现 5 个核心模块
- 部署到 ~/.openclaw/skills/memory-consolidator/
- 测试验证通过

### 4. 功能验证
✅ cron 定时触发（每 50 分钟）
✅ 文件变化检测（SHA256 hash 对比）
✅ 增量更新（仅处理变更文件）
✅ 去重（相似度 0.85 阈值）

## 文件清单

```
~/.openclaw/skills/memory-consolidator/
├── SKILL.md              ← Anthropic Skills 标准文档
├── SKILL.yaml            ← YAML frontmatter
├── scripts/
│   ├── main.py           ← 主入口
│   ├── collector.py      ← 文件收集
│   ├── analyzer.py       ← Claude API 提炼
│   ├── deduplicator.py   ← 内容去重
│   └── storage.py        ← 存储管理
├── references/
│   └── config.json       ← 配置文件
├── tests/
│   └── test_memory_consolidator.py
├── install-cron.sh       ← Cron 安装脚本
└── verify.py             ← 快速验证

~/.openclaw/qmd_memory/
├── consolidated.md       ← 合并输出
└── .hashes.json         ← 文件 hash 记录
```

## 待用户操作

1. 设置环境变量:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

2. 安装 cron:
   ```bash
   bash ~/.openclaw/skills/memory-consolidator/install-cron.sh
   ```

## 已知问题

- Claude API 需要 ANTHROPIC_API_KEY 环境变量
- 无 API key 时仍可运行（跳过提炼步骤）
