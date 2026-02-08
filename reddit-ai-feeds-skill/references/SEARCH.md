# Custom Search Guide

## Basic Search

```bash
# Search within specific subreddits
python3 scripts/fetch_reddit.py --subreddits LocalLLaMA,ClaudeAI --limit 5
```

## Advanced Query Patterns

### By Keywords
```bash
python3 scripts/fetch_reddit.py --query "Llama 3.2 release" --limit 5
```

### By Post Type
```bash
# Release announcements
python3 scripts/fetch_reddit.py --query "release" --limit 10

# Tutorials/Guides
python3 scripts/fetch_reddit.py --query "how to guide tutorial" --limit 10

# Comparisons
python3 scripts/fetch_reddit.py --query "vs comparison" --limit 10
```

## Combining Filters

```bash
# New posts about Claude in specific subreddits
python3 scripts/fetch_reddit.py --sort new --subreddits ClaudeAI,ClaudeCode --limit 5
```

## Rate Limiting

- Default: 0.3s delay between subreddit requests
- Respects Reddit's RSS feed limits
