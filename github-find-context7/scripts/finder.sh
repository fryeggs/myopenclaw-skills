#!/bin/bash
#
# GitHub Find Module - Vercel-style discovery
# Searches GitHub projects and ClawHub skills
#

GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# Python helper for API calls with auth
py_curl() {
    local url="$1"
    local token="$2"
    curl -s -H "Authorization: token $token" "$url" 2>/dev/null
}

# Search GitHub repositories
search_github() {
    local query="$1"
    local language="${2:-}"
    local sort="${3:-stars}"
    
    echo "🔍 Searching GitHub for: $query"
    [[ -n "$language" ]] && echo "   Language: $language"
    echo ""
    
    local url="https://api.github.com/search/repositories?q=${query}"
    [[ -n "$language" ]] && url="${url}+language:${language}"
    url="${url}&sort=${sort}&per_page=10"
    
    py_curl "$url" "$GITHUB_TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    if not items:
        print('No results found.')
    else:
        print(f\"Found {data.get('total_count', 0)} repositories:\")
        print('')
        for i, item in enumerate(items[:10], 1):
            name = item.get('full_name', 'N/A')
            desc = (item.get('description') or 'No description')[:80]
            stars = item.get('stargazers_count', 0)
            forks = item.get('forks_count', 0)
            lang = item.get('language', 'N/A')
            url = item.get('html_url', '')
            print(f\"{i}. {name}\")
            print(f\"   Stars: {stars} | Forks: {forks} | Lang: {lang}\")
            print(f\"   {desc}\")
            print(f\"   {url}\")
            print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Search code in repositories
search_code() {
    local query="$1"
    local repo="${2:-}"
    
    echo "🔍 Searching code for: $query"
    [[ -n "$repo" ]] && echo "   In: $repo"
    echo ""
    
    local url="https://api.github.com/search/code?q=${query}"
    [[ -n "$repo" ]] && url="${url}+repo:${repo}"
    
    py_curl "$url" "$GITHUB_TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])[:10]
    if not items:
        print('No code results found.')
    else:
        print(f\"Found {data.get('total_count', 0)} files:\")
        print('')
        for item in items:
            path = item.get('path', 'N/A')
            repo = item.get('repository', {}).get('full_name', 'N/A')
            url = item.get('html_url', '')
            print(f\"File: {path}\")
            print(f\"   Repo: {repo}\")
            print(f\"   {url}\")
            print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Search issues and PRs
search_issues() {
    local query="$1"
    local type="${2:-issue}"
    
    echo "🔍 Searching ${type}s for: $query"
    echo ""
    
    local url="https://api.github.com/search/issues?q=${query}+type:${type}"
    
    py_curl "$url" "$GITHUB_TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])[:10]
    if not items:
        print('No results found.')
    else:
        print(f\"Found {data.get('total_count', 0)} {type}s:\")
        print('')
        for item in items:
            title = item.get('title', 'N/A')[:70]
            state = item.get('state', 'N/A')
            user = item.get('user', {}).get('login', 'N/A')
            url = item.get('html_url', '')
            print(f\"Title: {title}\")
            print(f\"   State: {state} | User: {user}\")
            print(f\"   {url}\")
            print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Search users
search_users() {
    local query="$1"
    
    echo "🔍 Searching users for: $query"
    echo ""
    
    local url="https://api.github.com/search/users?q=${query}&per_page=10"
    
    py_curl "$url" "$GITHUB_TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    if not items:
        print('No users found.')
    else:
        print(f\"Found {data.get('total_count', 0)} users:\")
        print('')
        for item in items:
            login = item.get('login', 'N/A')
            name = item.get('name', '') or 'No name'
            repos = item.get('public_repos', 0)
            followers = item.get('followers', 0)
            url = item.get('html_url', '')
            print(f\"User: {login} ({name})\")
            print(f\"   Repos: {repos} | Followers: {followers}\")
            print(f\"   {url}\")
            print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Get repository details
get_repo_details() {
    local repo="$1"
    
    echo "📊 Repository Details: $repo"
    echo ""
    
    local url="https://api.github.com/repos/$repo"
    
    py_curl "$url" "$GITHUB_TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Name: {data.get('full_name', 'N/A')}\")
    print(f\"Description: {data.get('description', 'N/A')}\")
    print(f\"Stars: {data.get('stargazers_count', 0)}\")
    print(f\"Forks: {data.get('forks_count', 0)}\")
    print(f\"Watchers: {data.get('watchers_count', 0)}\")
    print(f\"Language: {data.get('language', 'N/A')}\")
    print(f\"Created: {data.get('created_at', 'N/A')[:10]}\")
    print(f\"Updated: {data.get('updated_at', 'N/A')[:10]}\")
    print(f\"License: {data.get('license', {}).get('spdx_id', 'N/A')}\")
    print(f\"URL: {data.get('html_url', 'N/A')}\")
    
    topics = data.get('topics', [])
    if topics:
        print(f\"\nTopics: {', '.join(topics)}\")
    
    owner = data.get('owner', {})
    print(f\"\nOwner: {owner.get('login', 'N/A')}\")
    print(f\"   Type: {owner.get('type', 'N/A')}\")
except Exception as e:
    print(f'Error: {e}')
"
}

# Main finder command
finder_main() {
    local command="$1"
    shift
    
    case "$command" in
        repo|repos|repository)
            search_github "$@"
            ;;
        code)
            search_code "$@"
            ;;
        issues|issue|prs|pr)
            search_issues "$@"
            ;;
        users|user)
            search_users "$@"
            ;;
        trending)
            echo "Trending: Use GitHub Explore https://github.com/trending"
            ;;
        details|info)
            get_repo_details "$1"
            ;;
        help|--help|-h)
            echo "GitHub Finder Commands:"
            echo "  repo [query] [language]  - Search repositories"
            echo "  code [query] [repo]      - Search code"
            echo "  issues [query] [type]    - Search issues/PRs"
            echo "  users [query]            - Search users"
            echo "  details [repo]           - Get repo details"
            ;;
        *)
            echo "Unknown finder command: $command"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    finder_main "$@"
fi
