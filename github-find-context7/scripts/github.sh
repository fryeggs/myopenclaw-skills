#!/bin/bash
#
# GitHub Core Module - GitHub operations
# Create, fix, iterate repositories, issues, PRs
#

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
API_BASE="https://api.github.com"

# Create repository
create_repo() {
    local name="$1"
    local description="${2:-Created with github-find-context7}"
    local private="${3:-false}"
    local auto_init="${4:-true}"
    
    echo "📦 Creating repository: $name"
    echo "=============================================="
    echo ""
    
    if [[ -z "$name" ]]; then
        echo "❌ Repository name is required"
        echo "Usage: github create <repo-name> [description] [private]"
        return 1
    fi
    
    # Check if repo exists
    local check_response
    check_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: token $GITHUB_TOKEN" \
        "$API_BASE/repos/$GITHUB_USER/$name" 2>/dev/null)
    
    if [[ "$check_response" == "200" ]]; then
        echo "⚠️ Repository '$name' already exists!"
        echo "   URL: https://github.com/$GITHUB_USER/$name"
        return 1
    fi
    
    # Create repository
    local payload
    payload=$(cat << EOF
{
    "name": "$name",
    "description": "$description",
    "private": $private,
    "auto_init": $auto_init
}
EOF
)
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "$payload" \
        "$API_BASE/user/repos")
    
    if echo "$response" | python3 -c "import sys,json; sys.exit(0 if 'html_url' in json.load(sys.stdin) else 1)" 2>/dev/null; then
        local repo_url
        repo_url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url', 'N/A'))")
        echo "✅ Repository created successfully!"
        echo ""
        echo "📁 Next steps:"
        echo "   git remote add origin $repo_url"
        echo "   git push -u origin main"
    else
        local error_msg
        error_msg=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message', 'Unknown error'))")
        echo "❌ Failed to create repository: $error_msg"
    fi
}

# Create issue
create_issue() {
    local repo="$1"
    local title="$2"
    local body="${3:-}"
    local labels="${4:-}"
    
    echo "📋 Creating Issue: $repo"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" || -z "$title" ]]; then
        echo "❌ Repository and title are required"
        echo "Usage: github issue-create <repo> <title> [body] [labels]"
        return 1
    fi
    
    local payload='{"title":"'"$title"'"'
    [[ -n "$body" ]] && payload="$payload,\"body\":\"$body\""
    [[ -n "$labels" ]] && payload="$payload,\"labels\":\"$labels\""
    payload="$payload}"
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "$payload" \
        "$API_BASE/repos/$repo/issues")
    
    if echo "$response" | python3 -c "import sys,json; sys.exit(0 if 'html_url' in json.load(sys.stdin) else 1)" 2>/dev/null; then
        local issue_url
        issue_url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url', 'N/A'))")
        echo "✅ Issue created successfully!"
        echo "   $issue_url"
    else
        local error_msg
        error_msg=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message', 'Unknown error'))")
        echo "❌ Failed to create issue: $error_msg"
    fi
}

# List issues
list_issues() {
    local repo="$1"
    local state="${2:-open}"
    
    echo "📋 Issues: $repo (State: $state)"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" ]]; then
        echo "❌ Repository is required"
        echo "Usage: github issues <repo> [state]"
        return 1
    fi
    
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "$API_BASE/repos/$repo/issues?state=$state&per_page=20" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if not data:
        print('No issues found.')
        sys.exit(0)
    print(f\"Found {len(data)} issues:\")
    print('')
    for item in data:
        number = item.get('number', 'N/A')
        title = item.get('title', 'N/A')[:70]
        state = item.get('state', 'N/A')
        user = item.get('user', {}).get('login', 'N/A')
        labels = ', '.join([l.get('name', '') for l in item.get('labels', [])[:3]])
        url = item.get('html_url', '')
        print(f\"#{number} {title}\")
        print(f\"   State: {state} | User: {user}\")
        [[ -n \"$labels\" ]] and print(f\"   Labels: {labels}\")
        print(f\"   🔗 {url}\")
        print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Create pull request
create_pr() {
    local repo="$1"
    local title="$2"
    local head="$3"
    local base="${4:-main}"
    local body="${5:-}"
    
    echo "🔀 Creating Pull Request: $repo"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" || -z "$title" || -z "$head" ]]; then
        echo "❌ Repository, title, and head branch are required"
        echo "Usage: github pr-create <repo> <title> <head-branch> [base] [body]"
        return 1
    fi
    
    local payload='{"title":"'"$title"'","head":"'"$head"'","base":"'"$base"'"'
    [[ -n "$body" ]] && payload="$payload,\"body\":\"$body\""
    payload="$payload}"
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "$payload" \
        "$API_BASE/repos/$repo/pulls")
    
    if echo "$response" | python3 -c "import sys,json; sys.exit(0 if 'html_url' in json.load(sys.stdin) else 1)" 2>/dev/null; then
        local pr_url
        pr_url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url', 'N/A'))")
        echo "✅ Pull Request created successfully!"
        echo "   $pr_url"
    else
        local error_msg
        error_msg=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message', 'Unknown error'))")
        echo "❌ Failed to create PR: $error_msg"
    fi
}

# List pull requests
list_prs() {
    local repo="$1"
    local state="${2:-open}"
    
    echo "🔀 Pull Requests: $repo (State: $state)"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" ]]; then
        echo "❌ Repository is required"
        echo "Usage: github prs <repo> [state]"
        return 1
    fi
    
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "$API_BASE/repos/$repo/pulls?state=$state&per_page=20" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if not data:
        print('No pull requests found.')
        sys.exit(0)
    print(f\"Found {len(data)} PRs:\")
    print('')
    for item in data:
        number = item.get('number', 'N/A')
        title = item.get('title', 'N/A')[:70]
        state = item.get('state', 'N/A')
        user = item.get('user', {}).get('login', 'N/A')
        head = item.get('head', {}).get('ref', 'N/A')
        base = item.get('base', {}).get('ref', 'N/A')
        url = item.get('html_url', '')
        print(f\"#{number} {title}\")
        print(f\"   State: {state} | User: {user}\")
        print(f\"   {head} → {base}\")
        print(f\"   🔗 {url}\")
        print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Clone repository
clone_repo() {
    local repo="$1"
    local directory="${2:-}"
    
    echo "📥 Cloning: $repo"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" ]]; then
        echo "❌ Repository is required"
        echo "Usage: github clone <repo> [directory]"
        return 1
    fi
    
    local clone_url="https://github.com/$repo.git"
    local target_dir="${directory:-$repo}"
    
    if [[ -d "$target_dir" ]]; then
        echo "⚠️ Directory '$target_dir' already exists!"
        return 1
    fi
    
    if git clone "$clone_url" "$target_dir"; then
        echo "✅ Cloned successfully to: $target_dir"
        echo ""
        echo "📁 Next steps:"
        echo "   cd $target_dir"
        echo "   # Make your changes"
        echo "   git add ."
        echo "   git commit -m 'Your commit message'"
        echo "   git push origin main"
    else
        echo "❌ Failed to clone repository"
    fi
}

# Fork repository
fork_repo() {
    local repo="$1"
    
    echo "🍴 Forking: $repo"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" ]]; then
        echo "❌ Repository is required"
        echo "Usage: github fork <repo>"
        return 1
    fi
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "$API_BASE/repos/$repo/forks")
    
    if echo "$response" | python3 -c "import sys,json; sys.exit(0 if 'html_url' in json.load(sys.stdin) else 1)" 2>/dev/null; then
        local fork_url
        fork_url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url', 'N/A'))")
        echo "✅ Fork created successfully!"
        echo "   $fork_url"
        echo ""
        echo "📁 Clone your fork:"
        echo "   git clone $fork_url"
    else
        local error_msg
        error_msg=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message', 'Unknown error'))")
        echo "❌ Failed to fork: $error_msg"
    fi
}

# Get repository info
get_repo_info() {
    local repo="$1"
    
    echo "📊 Repository Info: $repo"
    echo "=============================================="
    echo ""
    
    if [[ -z "$repo" ]]; then
        echo "❌ Repository is required"
        echo "Usage: github info <repo>"
        return 1
    fi
    
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "$API_BASE/repos/$repo" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Name: {data.get('full_name', 'N/A')}\")
    print(f\"Description: {data.get('description', 'N/A')}\")
    print(f\"⭐ Stars: {data.get('stargazers_count', 0)}\")
    print(f\"🍴 Forks: {data.get('forks_count', 0)}\")
    print(f\"👀 Watchers: {data.get('watchers_count', 0)}\")
    print(f\"💻 Language: {data.get('language', 'N/A')}\")
    print(f\"📅 Created: {data.get('created_at', 'N/A')[:10]}\")
    print(f\"🔄 Updated: {data.get('updated_at', 'N/A')[:10]}\")
    print(f\"🛡️ License: {data.get('license', {}).get('spdx_id', 'None')}\")
    print(f\"🔗 URL: {data.get('html_url', 'N/A')}\")
    print(f\"\")
    print(f\"📋 Default Branch: {data.get('default_branch', 'main')}\")
    print(f\"📂 Open Issues: {data.get('open_issues_count', 0)}\")
    print(f\"👥 Contributors: {data.get('subscribers_count', 0)} watchers\")
except Exception as e:
    print(f'Error: {e}')
"
}

# Main github command
github_main() {
    local command="$1"
    shift
    
    case "$command" in
        create|new)
            create_repo "$@"
            ;;
        clone)
            clone_repo "$@"
            ;;
        fork)
            fork_repo "$@"
            ;;
        info|details)
            get_repo_info "$@"
            ;;
        issue-create)
            create_issue "$@"
            ;;
        issues)
            list_issues "$@"
            ;;
        pr-create)
            create_pr "$@"
            ;;
        prs|pull-requests)
            list_prs "$@"
            ;;
        help|--help|-h)
            echo "GitHub Core Commands:"
            echo "  create [name] [desc] [private]  - Create repository"
            echo "  clone [repo] [dir]              - Clone repository"
            echo "  fork [repo]                     - Fork repository"
            echo "  info [repo]                     - Get repository info"
            echo "  issue-create [repo] [title]     - Create issue"
            echo "  issues [repo] [state]           - List issues"
            echo "  pr-create [repo] [title] [head] - Create pull request"
            echo "  prs [repo] [state]              - List pull requests"
            echo ""
            echo "Examples:"
            echo "  github create myproject \"My new project\""
            echo "  github clone facebook/react"
            echo "  github fork facebook/react"
            echo "  github issue-create owner/repo \"Bug found\" \"Description\" bug"
            echo ""
            echo "Note: GITHUB_TOKEN environment variable must be set"
            ;;
        *)
            echo "Unknown github command: $command"
            echo "Use: github help"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    github_main "$@"
fi
