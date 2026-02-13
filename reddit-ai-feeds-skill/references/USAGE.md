# 详细用法

本文档提供 `fetch_reddit.py` 脚本的完整参数说明和使用示例。

## 命令行参数

### 基本参数

```bash
python3 scripts/fetch_reddit.py [--sort SORT] [--limit N] [--subreddits SUBS] [--total N]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--sort` | string | hot | 排序方式，可选: hot, new, top, rising |
| `--limit` | int | 5 | 每个子版块获取的帖子数量 |
| `--subreddits` | string | (全部默认) | 指定的子版块列表，逗号分隔 |
| `--total` | int | 20 | 最终显示的帖子总数上限 |

### 排序方式说明

| 排序 | 说明 |
|------|------|
| hot | 热门帖子（综合热度排序） |
| new | 最新发布的帖子 |
| top | 评分最高的帖子 |
| rising | 快速上升的热门帖子 |

## 使用示例

### 示例 1：获取热门帖子

```bash
# 默认获取所有 AI 子版块的热门帖子
python3 scripts/fetch_reddit.py --limit 10

# 只获取 5 个热门帖子
python3 scripts/fetch_reddit.py --limit 5
```

### 示例 2：指定子版块

```bash
# 只获取 LocalLLaMA 和 ClaudeAI
python3 scripts/fetch_reddit.py --subreddits LocalLLaMA,ClaudeAI --limit 10

# 获取 OpenAI 和 ChatGPT
python3 scripts/fetch_reddit.py --subreddits OpenAI,ChatGPT --limit 5
```

### 示例 3：按时间排序

```bash
# 获取最新帖子
python3 scripts/fetch_reddit.py --sort new --limit 10

# 获取评分最高的帖子
python3 scripts/fetch_reddit.py --sort top --limit 10
```

### 示例 4：组合使用

```bash
# 获取 LocalLLaMA 最新帖子，限制总数
python3 scripts/fetch_reddit.py --subreddits LocalLLaMA --sort new --limit 10 --total 10
```

## 输出格式

脚本输出包含以下信息：

```
📊 Reddit AI 社区热帖 (共 N 条)

【序号】英文标题
• 📌 中文标题翻译
• 💡 关键词翻译 (如: model=模型, release=发布)
• 🦙 子版块中文说明 · 时间
• 📝 内容摘要/类型判断
• 🔗 Reddit 链接
```

### 关键词翻译示例

脚本会自动识别并翻译以下类型的关键词：

| 英文 | 中文 |
|------|------|
| model/models | 模型 |
| release/released | 发布 |
| update/updates | 更新 |
| fine-tuning | 微调 |
| quantization | 量化 |
| inference | 推理 |
| benchmark/benchmarks | 基准测试 |
| agent/agents | 智能体 |
| prompt/prompts | 提示词 |
| plugin/plugins | 插件 |
| open source | 开源 |
| local/locally | 本地 |

### 内容摘要类型

脚本会自动判断帖子类型：

| 识别类型 | 说明 |
|----------|------|
| 问答讨论 | AMA 或问答类帖子 |
| 发布公告 | 版本/产品发布 |
| 集中讨论帖 | 社区 megathread |
| 问题修复 | bug/issue/fix 相关 |
| 教程/指南 | how to/guide/tutorial |
| 对比/评测 | vs/comparison/better |
| 工具分享 | tool/project 分享 |
| 法律新闻 | lawsuit/sue 相关 |

## 错误处理

### 常见错误

1. **网络超时**
   ```
   [Error] Failed to fetch r/LocalLLaMA: <urlopen error timed out>
   ```
   解决：检查网络连接，或减少 `--limit` 值

2. **XML 解析错误**
   ```
   [Error] XML parse error: ...
   ```
   解决：Reddit RSS 服务暂时不可用，稍后重试

### 查看错误信息

错误信息会输出到 stderr：
```bash
python3 scripts/fetch_reddit.py 2>&1 | grep -i error
```

## 性能优化

### 建议配置

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `--limit` | 5-10 | 平衡获取数量和响应时间 |
| `--total` | 20-30 | 最终显示数量 |
| 子版块数量 | 5-10 | 太多会延长获取时间 |

### 加速建议

1. 使用 `--subreddits` 指定必要子版块
2. 降低 `--limit` 值
3. 使用 `--sort new` 可能比 `--sort hot` 更快
