#!/bin/bash
#
# GitHub Analyzer Module - Project health analysis
# Analyzes repository health, activity, and quality metrics
#

GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# Python helper with auth
py_curl() {
    local url="$1"
    curl -s -H "Authorization: token $GITHUB_TOKEN" "$url" 2>/dev/null
}

# Analyze repository health
analyze_health() {
    local repo="$1"
    
    echo "🏥 Health Analysis: $repo"
    echo "=============================================="
    echo ""
    
    local basic_info=$(py_curl "https://api.github.com/repos/$repo")
    local commits=$(py_curl "https://api.github.com/repos/$repo/commits?since=$(date -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)")
    local issues=$(py_curl "https://api.github.com/repos/$repo/issues?state=open&per_page=1")
    local contributors=$(py_curl "https://api.github.com/repos/$repo/contributors?per_page=10")
    
    echo "📊 Metrics Summary"
    echo "-----------------"
    
    py_curl "https://api.github.com/repos/$repo" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    
    # Basic metrics
    stars = data.get('stargazers_count', 0)
    forks = data.get('forks_count', 0)
    watchers = data.get('watchers_count', 0)
    open_issues = data.get('open_issues_count', 0)
    language = data.get('language', 'N/A')
    license = data.get('license', {}).get('spdx_id', 'None')
    created = data.get('created_at', '')[:10]
    updated = data.get('updated_at', '')[:10]
    
    print(f\"Stars: {stars}\")
    print(f\"Forks: {forks}\")
    print(f\"Watchers: {watchers}\")
    print(f\"Open Issues: {open_issues}\")
    print(f\"Language: {language}\")
    print(f\"License: {license}\")
    print(f\"Created: {created}\")
    print(f\"Updated: {updated}\")
    
except Exception as e:
    print(f'Error: {e}')
"
    
    echo ""
    echo "💡 Note: Full health scoring requires additional data processing"
}

# Compare two repositories
compare_repos() {
    local repo1="$1"
    local repo2="$2"
    
    echo "⚖️ Repository Comparison"
    echo "=============================================="
    echo ""
    echo "Comparing: $repo1 vs $repo2"
    echo ""
    
    py_curl "https://api.github.com/repos/$repo1" > /tmp/repo1.json
    py_curl "https://api.github.com/repos/$repo2" > /tmp/repo2.json
    
    python3 << 'PYEOF'
import json

with open('/tmp/repo1.json') as f:
    r1 = json.load(f)
with open('/tmp/repo2.json') as f:
    r2 = json.load(f)

def get_val(repo, key, default=0):
    if key == 'license':
        return repo.get(key, {}).get('spdx_id', 'None')
    return repo.get(key, default)

print(f"{'Metric':<20} {'Repo 1':<25} {'Repo 2':<25}")
print("-" * 70)
print(f"{'Stars':<20} {get_val(r1, 'stargazers_count'):<25} {get_val(r2, 'stargazers_count'):<25}")
print(f"{'Forks':<20} {get_val(r1, 'forks_count'):<25} {get_val(r2, 'forks_count'):<25}")
print(f"{'Watchers':<20} {get_val(r1, 'watchers_count'):<25} {get_val(r2, 'watchers_count'):<25}")
print(f"{'Open Issues':<20} {get_val(r1, 'open_issues_count'):<25} {get_val(r2, 'open_issues_count'):<25}")
print(f"{'Language':<20} {get_val(r1, 'language'):<25} {get_val(r2, 'language'):<25}")
print(f"{'License':<20} {get_val(r1, 'license'):<25} {get_val(r2, 'license'):<25}")
print(f"{'Created':<20} {get_val(r1, 'created_at')[:10]:<25} {get_val(r2, 'created_at')[:10]:<25}")
print(f"{'Updated':<20} {get_val(r1, 'updated_at')[:10]:<25} {get_val(r2, 'updated_at')[:10]:<25}")
PYEOF
}

# Analyze commit activity
analyze_activity() {
    local repo="$1"
    local days="${2:-30}"
    
    echo "📈 Activity Analysis: $repo (Last $days days)"
    echo "=============================================="
    echo ""
    
    local since_date
    since_date=$(date -d "$days days ago" +%Y-%m-%dT%H:%M:%SZ)
    
    py_curl "https://api.github.com/repos/$repo/commits?since=$since_date&per_page=100" | python3 -c "
import sys, json
from collections import Counter
from datetime import datetime

try:
    data = json.load(sys.stdin)
    print(f\"Total commits: {len(data)}\")
    print('')
    
    # By author
    authors = [c.get('commit', {}).get('author', {}).get('name', 'Unknown') for c in data]
    author_counts = Counter(authors)
    print('Top Contributors:')
    for author, count in author_counts.most_common(10):
        print(f\"   {author}: {count} commits\")
    
    print('')
    print('Daily Activity:')
    dates = [c.get('commit', {}).get('author', {}).get('date', '')[:10] for c in data]
    date_counts = Counter(dates)
    for date, count in sorted(date_counts.items())[-7:]:
        bar = '█' * max(1, count // max(1, len(data) // 50))
        print(f\"   {date}: {bar} {count}\")
except Exception as e:
    print(f'Error: {e}')
"
}

# List contributors
list_contributors() {
    local repo="$1"
    local limit="${2:-20}"
    
    echo "👥 Contributors: $repo"
    echo "=============================================="
    echo ""
    
    py_curl "https://api.github.com/repos/$repo/contributors?per_page=$limit" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if not data:
        print('No public contributors found.')
    else:
        print(f\"Found {len(data)} contributors:\")
        print('')
        for i, c in enumerate(data, 1):
            login = c.get('login', 'N/A')
            contributions = c.get('contributions', 0)
            url = c.get('html_url', '')
            print(f\"{i}. {login}\")
            print(f\"   Contributions: {contributions}\")
            print(f\"   {url}\")
            print('')
except Exception as e:
    print(f'Error: {e}')
"
}

# Main analyzer command
analyzer_main() {
    local command="$1"
    shift
    
    case "$command" in
        health|analyze)
            analyze_health "$@"
            ;;
        compare|comparison)
            compare_repos "$@"
            ;;
        activity)
            analyze_activity "$@"
            ;;
        contributors)
            list_contributors "$@"
            ;;
        help|--help|-h)
            echo "Analyzer Commands:"
            echo "  health [repo]           - Analyze repository health"
            echo "  compare [repo1] [repo2] - Compare two repositories"
            echo "  activity [repo] [days]  - Analyze commit activity"
            echo "  contributors [repo]     - List contributors"
            ;;
        *)
            echo "Unknown analyzer command: $command"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    analyzer_main "$@"
fi
