#!/bin/bash
#
# GitHub Context7 Module - Library documentation lookup
# Uses Context7 MCP to get official documentation for popular libraries
#

# Resolve library ID from name
resolve_library_id() {
    local library="$1"
    
    # Map common library names to Context7 IDs
    declare -A LIBRARY_MAP=(
        ["react"]="facebook-react"
        ["nextjs"]="vercel-nextjs"
        ["next"]="vercel-nextjs"
        ["typescript"]="microsoft-typescript"
        ["vue"]="vuejs-core"
        ["vue3"]="vuejs-core"
        ["angular"]="angular"
        ["node"]="nodejs"
        ["nodejs"]="nodejs"
        ["express"]="expressjs"
        ["fastify"]="fastify"
        ["django"]="django"
        ["flask"]="pallets-flask"
        ["fastapi"]="tiangolo-fastapi"
        ["spring"]="spring-projects-spring-framework"
        ["springboot"]="spring-projects-spring-boot"
        ["rust"]="rust-lang-rust"
        ["go"]="golang-go"
        ["golang"]="golang-go"
        ["python"]="python-cpython"
        ["pandas"]="pandas-dev-pandas"
        ["numpy"]="numpy-numpy"
        ["tensorflow"]="tensorflow-tensorflow"
        ["pytorch"]="pytorch-pytorch"
        ["aws"]="awsdocs-aws-doc-sdk-developer-guide"
        ["docker"]="docker-docs"
        ["kubernetes"]="kubernetes-docs"
        ["graphql"]="graphql-docs"
        ["prisma"]="prisma-prisma"
        ["typeorm"]="typeorm-typeorm"
        ["sequelize"]="sequelize-sequelize"
        ["mongoose"]="Automattic-mongoose"
        ["jquery"]="jqueryjquery"
        ["bootstrap"]="twbs-bootstrap"
        ["tailwind"]="tailwindlabs-tailwind-css"
        ["webpack"]="webpack-webpack"
        ["vite"]="vitejs-vite"
        ["esbuild"]="evanwallace-esbuild"
        ["rollup"]="rollup-rollup"
        ["jest"]="facebook-jest"
        ["mocha"]="mochajs-mocha"
        ["cypress"]="cypress-io-cypress"
        ["playwright"]="microsoft-playwright"
        ["supabase"]="supabase-supabase"
        ["firebase"]="firebase-firebase-js-sdk"
        ["stripe"]="stripe-stripe-js"
        ["axios"]="axios-axios"
        ["socket.io"]="socketio-socket.io"
        ["redis"]="redis-redis"
        ["mongodb"]="mongodb-docs"
        ["postgresql"]="postgresql-postgresql"
        ["mysql"]="mysql-js-mysql"
    )
    
    local lower_library=$(echo "$library" | tr '[:upper:]' '[:lower:]')
    
    if [[ -n "${LIBRARY_MAP[$lower_library]}" ]]; then
        echo "${LIBRARY_MAP[$lower_library]}"
        return 0
    fi
    
    # Try to search for the library
    echo "$library"
}

# Search for library (Context7 resolve-library-id)
search_library() {
    local query="$1"
    
    echo "🔍 Searching Context7 for: $query"
    echo ""
    echo "💡 Tip: Context7 provides official documentation for popular libraries."
    echo "   Common queries: react, nextjs, typescript, django, express, etc."
    echo ""
    echo "Try: context7 docs <library-name>"
}

# Get library documentation (Context7 get-library-docs)
get_library_docs() {
    local library="$1"
    local section="${2:-}"
    
    echo "📚 Documentation: $library"
    echo "=============================================="
    echo ""
    echo "💡 Context7 provides structured documentation from official sources."
    echo ""
    echo "To get full documentation, use the Context7 MCP integration:"
    echo "   1. Ensure Context7 MCP is configured in OpenClaw"
    echo "   2. Use: /use github-find-context7 context7 <library-name>"
    echo ""
    echo "Common libraries supported:"
    echo "   Frontend: react, nextjs, vue, angular, svelte"
    echo "   Backend:  express, django, flask, fastapi, spring"
    echo "   Database: prisma, typeorm, mongoose, sequelize"
    echo "   DevOps:   docker, kubernetes, aws"
    echo "   Tools:    jest, cypress, playwright"
    echo ""
    
    # Show basic info from GitHub if available
    local lib_id
    lib_id=$(resolve_library_id "$library")
    
    if [[ "$lib_id" != "$library" ]]; then
        echo "📦 Resolved to: $lib_id"
        echo ""
    fi
    
    # Try to get info from GitHub
    echo "🔗 Related GitHub Resources:"
    echo ""
    
    # Search for official repositories
    local search_results
    search_results=$(curl -s -H "Authorization: token ${GITHUB_TOKEN:-}" \
        "https://api.github.com/search/repositories?q=topic:official+${library}&per_page=5" 2>/dev/null)
    
    if echo "$search_results" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('items') else 1)" 2>/dev/null; then
        echo "$search_results" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', [])[:5]:
    name = item.get('full_name', 'N/A')
    desc = item.get('description', 'N/A')[:60]
    stars = item.get('stargazers_count', 0)
    print(f'   📦 {name} (⭐{stars})')
    print(f'      {desc}')
" 2>/dev/null
    else
        echo "   Try searching on GitHub for official resources:"
        echo "   /use github-find-context7 find ${library} official"
    fi
}

# Get API reference
get_api_reference() {
    local library="$1"
    
    echo "📖 API Reference: $library"
    echo "=============================================="
    echo ""
    echo "To get API reference documentation:"
    echo ""
    echo "1. Using Context7 MCP (if configured):"
    echo "   /use github-find-context7 context7 <library>"
    echo ""
    echo "2. Common API reference links:"
    
    case "$(echo $library | tr '[:upper:]' '[:lower:]')" in
        react*)
            echo "   https://react.dev/reference/react"
            echo "   https://legacy.reactjs.org/docs/react-api.html"
            ;;
        nextjs*|next*)
            echo "   https://nextjs.org/docs/app/api-reference"
            echo "   https://nextjs.org/docs/pages/api-reference"
            ;;
        vue*|vue3)
            echo "   https://vuejs.org/api/"
            echo "   https://composition-api.vuejs.org/"
            ;;
        typescript)
            echo "   https://www.typescriptlang.org/docs/"
            echo "   https://www.typescriptlang.org/tsconfig"
            ;;
        node*|nodejs)
            echo "   https://nodejs.org/en/docs/"
            echo "   https://nodejs.org/api/"
            ;;
        express)
            echo "   https://expressjs.com/en/4x/api.html"
            ;;
        django)
            echo "   https://docs.djangoproject.com/en/stable/ref/"
            ;;
        flask)
            echo "   https://flask.palletsprojects.com/en/stable/api/"
            ;;
        fastapi)
            echo "   https://fastapi.tiangolo.com/reference/"
            ;;
        prisma)
            echo "   https://www.prisma.io/docs/reference/api-reference"
            ;;
        jest)
            echo "   https://jestjs.io/docs/api"
            ;;
        *)
            echo "   Search GitHub for official API docs:"
            echo "   /use github-find-context7 find $library api reference"
            ;;
    esac
}

# Get code examples
get_examples() {
    local library="$1"
    
    echo "💻 Code Examples: $library"
    echo "=============================================="
    echo ""
    echo "Searching for code examples..."
    echo ""
    
    curl -s -H "Authorization: token ${GITHUB_TOKEN:-}" \
        "https://api.github.com/search/code?q=example+${library}+language:javascript+extension:js&per_page=10" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])[:5]
    if not items:
        print('No examples found in public repos.')
        sys.exit(0)
    print('📁 Example files found:')
    print('')
    for item in items:
        path = item.get('path', 'N/A')
        repo = item.get('repository', {}).get('full_name', 'N/A')
        url = item.get('html_url', '')
        print(f'   📄 {path}')
        print(f'      Repo: {repo}')
        print(f'      🔗 {url}')
        print('')
except Exception as e:
    print('Could not fetch examples.')
" 2>/dev/null
    
    echo "💡 For more examples, visit:"
    echo "   - Official docs: https://docs.github.com/en/search-github/searching-on-github"
    echo "   - Search: /use github-find-context7 code examples ${library}"
}

# Main context7 command
context7_main() {
    local command="$1"
    shift
    
    case "$command" in
        docs|documentation)
            get_library_docs "$@"
            ;;
        api|reference)
            get_api_reference "$@"
            ;;
        examples|code)
            get_examples "$@"
            ;;
        search|find)
            search_library "$@"
            ;;
        help|--help|-h)
            echo "Context7 Documentation Commands:"
            echo "  docs [library]          - Get library documentation"
            echo "  api [library]           - Get API reference links"
            echo "  examples [library]      - Find code examples"
            echo "  search [library]        - Search for library"
            echo ""
            echo "Examples:"
            echo "  context7 docs react"
            echo "  context7 api express"
            echo "  context7 examples nextjs"
            ;;
        *)
            echo "Unknown context7 command: $command"
            echo "Use: context7 help"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    context7_main "$@"
fi
