# Output Customization

## Default Output

The script outputs to stdout in Markdown format:
```
📊 **Reddit AI 社区热帖** (共 N 条)

【1】Post Title
• 📌 中文标题翻译
• 💡 keyword=关键词
• 📍 社区 · 时间
• 📝 摘要
• 🔗 链接
```

## Redirect to File

```bash
# Save to markdown file
python3 scripts/fetch_reddit.py > reddit_posts.md

# Append to daily log
python3 scripts/fetch_reddit.py >> $(date +%Y-%m-%d)_reddit.md
```

## Quiet Mode

Currently outputs progress to stderr. Redirect stderr to suppress:

```bash
python3 scripts/fetch_reddit.py 2>/dev/null
```

## JSON Output (Future Enhancement)

Not yet implemented. For JSON output, consider piping through jq:

```bash
# Example when JSON is available
python3 scripts/fetch_reddit.py --json | jq '.[] | {title, url}'
```
