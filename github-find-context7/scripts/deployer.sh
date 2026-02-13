#!/bin/bash
#
# GitHub Deployer Module - Deployment guide generation
# Generates deployment instructions for various platforms
#

GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# Generate deployment guide
generate_deploy_guide() {
    local repo="$1"
    local platform="${2:-auto}"
    
    echo "🚀 Deployment Guide: $repo"
    echo "=============================================="
    echo ""
    
    # Get repo info
    local repo_info
    repo_info=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$repo")
    
    local language=$(echo "$repo_info" | python3 -c "import sys,json; print(json.load(sys.stdin).get('language', 'N/A'))" 2>/dev/null || echo "Unknown")
    local description=$(echo "$repo_info" | python3 -c "import sys,json; print(json.load(sys.stdin).get('description', 'N/A'))" 2>/dev/null || echo "No description")
    
    echo "📦 Repository: $repo"
    echo "💻 Language: $language"
    echo "📝 Description: $description"
    echo ""
    
    # Detect project type and suggest platforms
    echo "📋 Recommended Platforms"
    echo "------------------------"
    echo ""
    
    case "$(echo $language | tr '[:upper:]' '[:lower:]')" in
        javascript|typescript)
            echo "🌐 Frontend/Node.js Projects:"
            echo "   • Vercel (Recommended for Next.js, React)"
            echo "     https://vercel.com"
            echo "   • Netlify (Great for static sites)"
            echo "     https://netlify.com"
            echo "   • Cloudflare Pages"
            echo "     https://pages.cloudflare.com"
            ;;
        python)
            echo "🐍 Python Projects:"
            echo "   • Railway (Easy deployment)"
            echo "     https://railway.app"
            echo "   • Render"
            echo "     https://render.com"
            echo "   • Fly.io"
            echo "     https://fly.io"
            echo "   • AWS Elastic Beanstalk"
            echo "     https://aws.amazon.com/elasticbeanstalk"
            ;;
        go)
            echo "🔷 Go Projects:"
            echo "   • Fly.io (Native Go support)"
            echo "     https://fly.io"
            echo "   • Railway"
            echo "     https://railway.app"
            echo "   • Render"
            echo "     https://render.com"
            ;;
        rust)
            echo "🦀 Rust Projects:"
            echo "   • Fly.io (Native Rust support)"
            echo "     https://fly.io"
            echo "   • Railway"
            echo "     https://railway.app"
            ;;
        java)
            echo "☕ Java Projects:"
            echo "   • Railway"
            echo "     https://railway.app"
            echo "   • Render"
            echo "     https://render.com"
            echo "   • AWS Elastic Beanstalk"
            echo "     https://aws.amazon.com/elasticbeanstalk"
            ;;
        ruby)
            echo "💎 Ruby Projects:"
            echo "   • Railway"
            echo "     https://railway.app"
            echo "   • Render"
            echo "     https://render.com"
            echo "   • Fly.io"
            echo "     https://fly.io"
            ;;
        php)
            echo "🐘 PHP Projects:"
            echo "   • Railway"
            echo "     https://railway.app"
            echo "   • Render"
            echo "     https://render.com"
            echo "   • Fly.io"
            echo "     https://fly.io"
            ;;
        *)
            echo "   • Railway (General purpose)"
            echo "     https://railway.app"
            echo "   • Render (Supports many languages)"
            echo "     https://render.com"
            echo "   • Fly.io (Container-based)"
            echo "     https://fly.io"
            ;;
    esac
    
    echo ""
    echo "📝 Deployment Steps (Generic)"
    echo "------------------------------"
    echo ""
    echo "1. Clone the repository:"
    echo "   git clone https://github.com/$repo.git"
    echo "   cd $(basename $repo)"
    echo ""
    echo "2. Install dependencies:"
    case "$(echo $language | tr '[:upper:]' '[:lower:]')" in
        javascript|typescript)
            echo "   npm install"
            ;;
        python)
            echo "   pip install -r requirements.txt"
            ;;
        go)
            echo "   go mod download"
            ;;
        rust)
            echo "   cargo build --release"
            ;;
        java)
            echo "   mvn install"
            ;;
        ruby)
            echo "   bundle install"
            ;;
        php)
            echo "   composer install"
            ;;
        *)
            echo "   # Check repository for setup instructions"
            ;;
    esac
    
    echo ""
    echo "3. Set up environment variables:"
    echo "   # Create .env file with required secrets"
    echo ""
    
    echo "4. Run locally to verify:"
    case "$(echo $language | tr '[:upper:]' '[:lower:]')" in
        javascript|typescript)
            echo "   npm run dev"
            ;;
        python)
            echo "   python app.py"
            ;;
        *)
            echo "   # Check repository for running instructions"
            ;;
    esac
    
    echo ""
    echo "5. Deploy to platform:"
    echo "   # Follow platform-specific deployment guide"
    echo ""
    
    # Check for Dockerfile
    echo "🐳 Container Deployment"
    echo "------------------------"
    if curl -s -I "https://raw.githubusercontent.com/$repo/main/Dockerfile" 2>/dev/null | grep -q "200 OK"; then
        echo "✅ Dockerfile found! This project supports container deployment."
        echo ""
        echo "Deploy with Docker:"
        echo "   docker build -t myapp ."
        echo "   docker run -p 8080:8080 myapp"
    else
        echo "ℹ️ No Dockerfile found. Manual deployment required."
    fi
}

# Generate Vercel guide
generate_vercel_guide() {
    local repo="$1"
    
    echo "🚀 Vercel Deployment Guide"
    echo "=============================================="
    echo ""
    echo "Repository: $repo"
    echo ""
    echo "📋 Steps to Deploy on Vercel:"
    echo ""
    echo "1. Push your code to GitHub"
    echo ""
    echo "2. Go to https://vercel.com and sign up"
    echo ""
    echo "3. Click 'Add New Project' and select your repository"
    echo ""
    echo "4. Configure project settings:"
    echo "   • Framework Preset: Auto-detect (Next.js, Create React App, etc.)"
    echo "   • Build Command: npm run build (or custom)"
    echo "   • Output Directory: .next or dist (or custom)"
    echo ""
    echo "5. Add environment variables if needed"
    echo ""
    echo "6. Click 'Deploy'"
    echo ""
    echo "💡 Quick Deploy Command:"
    echo "   npx vercel --yes"
    echo ""
    echo "📖 Documentation: https://vercel.com/docs"
}

# Generate Docker guide
generate_docker_guide() {
    local repo="$1"
    
    echo "🐳 Docker Deployment Guide"
    echo "=============================================="
    echo ""
    echo "Repository: $repo"
    echo ""
    echo "📋 Steps to Deploy with Docker:"
    echo ""
    echo "1. Ensure Docker is installed:"
    echo "   docker --version"
    echo ""
    echo "2. Create Dockerfile if not exists:"
    echo "   # See: https://docs.docker.com/get-docker/"
    echo ""
    echo "3. Build the image:"
    echo "   docker build -t myapp ."
    echo ""
    echo "4. Run locally:"
    echo "   docker run -p 8080:8080 myapp"
    echo ""
    echo "5. Push to container registry:"
    echo "   docker tag myapp registry.example.com/myapp"
    echo "   docker push registry.example.com/myapp"
    echo ""
    echo "6. Deploy to cloud:"
    echo "   • AWS ECS: https://aws.amazon.com/ecs/"
    echo "   • Google Cloud Run: https://cloud.google.com/run"
    echo "   • Azure Container Instances: https://azure.microsoft.com/container-instances"
    echo ""
    echo "💡 Tips:"
    echo "   • Use .dockerignore to exclude unnecessary files"
    echo "   • Multi-stage builds reduce image size"
    echo "   • Use specific tags, not 'latest'"
}

# Generate database setup guide
generate_db_guide() {
    local database="${1:-}"
    
    echo "🗄️ Database Setup Guide"
    echo "=============================================="
    echo ""
    
    if [[ -n "$database" ]]; then
        echo "Database: $database"
        echo ""
    fi
    
    echo "📋 Common Database Platforms:"
    echo ""
    echo "🐘 PostgreSQL:"
    echo "   • Managed: Supabase, Neon, Railway, Render"
    echo "   • Self-hosted: Docker, cloud VMs"
    echo ""
    echo "🍃 MongoDB:"
    echo "   • Managed: MongoDB Atlas (Free tier available)"
    echo "   • Self-hosted: Docker, cloud VMs"
    echo ""
    echo "🔴 Redis:"
    echo "   • Managed: Redis Cloud, Railway, Render"
    echo "   • Self-hosted: Docker, cloud VMs"
    echo ""
    echo "🐬 MySQL:"
    echo "   • Managed: PlanetScale, ClearDB, Railway"
    echo "   • Self-hosted: Docker, cloud VMs"
    echo ""
    echo "💡 Connection Best Practices:"
    echo "   • Use connection pooling"
    echo "   • Store credentials in environment variables"
    echo "   • Use SSL/TLS for connections"
    echo "   • Implement proper error handling"
}

# Main deployer command
deployer_main() {
    local command="$1"
    shift
    
    case "$command" in
        guide|deploy)
            generate_deploy_guide "$@"
            ;;
        vercel)
            generate_vercel_guide "$@"
            ;;
        docker|container)
            generate_docker_guide "$@"
            ;;
        database|db)
            generate_db_guide "$@"
            ;;
        help|--help|-h)
            echo "Deployer Commands:"
            echo "  guide [repo] [platform]  - Generate deployment guide"
            echo "  vercel [repo]            - Vercel-specific guide"
            echo "  docker [repo]            - Docker deployment guide"
            echo "  database [type]          - Database setup guide"
            echo ""
            echo "Examples:"
            echo "  deployer guide facebook/react vercel"
            echo "  deployer docker my-org/myapp"
            echo "  deployer database postgresql"
            ;;
        *)
            echo "Unknown deployer command: $command"
            echo "Use: deployer help"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    deployer_main "$@"
fi
