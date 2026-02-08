---
name: github-find-context7
description: "GitHub operations and documentation lookup. Use when user wants to search GitHub projects, analyze code, get official documentation for any library/framework, or perform GitHub operations like creating repos, issues, or PRs."
---

# GitHub Find Context7

Integrated GitHub operations and documentation lookup skill.

## When to Use

Use this skill when:
- User wants to search GitHub projects or code
- User needs official documentation for a library/framework (React, Next.js, Django, etc.)
- User wants to create or manage GitHub repositories
- User wants to analyze repository health and activity
- User needs deployment guides for a project

## Features

### Discovery (GitHub Search)
- Search repositories by keyword
- Search code within repositories
- Search issues and pull requests
- Search users

### GitHub Operations
- Create repositories
- Create issues and pull requests
- Clone and fork repositories
- List issues and PRs

### Documentation (Context7)
- Query official documentation for any library
- Get API references and code examples
- Find usage patterns and best practices

### Analysis
- Repository health scoring
- Activity analysis
- Contributor statistics
- Repository comparison

### Deployment
- Platform-specific deployment guides
- Docker and container deployment
- Database setup guides

## Commands

### Discovery
```bash
/use github-find-context7 find react performance
/use github-find-context7 code "useState" facebook/react
/use github-find-context7 issues bug state:open
/use github-find-context7 users facebook
```

### GitHub Operations
```bash
/use github-find-context7 create myproject "My new project"
/use github-find-context7 clone facebook/react
/use github-find-context7 issue-create owner/repo "Bug found" "Description"
```

### Documentation
```bash
/use github-find-context7 docs react
/use github-find-context7 api express
/use github-find-context7 examples nextjs
```

### Analysis
```bash
/use github-find-context7 health facebook/react
/use github-find-context7 compare facebook/react vuejs/core
/use github-find-context7 activity facebook/react 30
```

### Deployment
```bash
/use github-find-context7 guide facebook/react
/use github-find-context7 docker my-org/myapp
```

## Context7 Integration

Context7 provides official, up-to-date documentation for:
- Frontend: React, Next.js, Vue, Angular, Svelte
- Backend: Express, Django, Flask, FastAPI, Spring
- Database: Prisma, TypeORM, Mongoose, Sequelize
- DevOps: Docker, Kubernetes, AWS
- Testing: Jest, Cypress, Playwright

## Examples

**Search for a React performance library:**
```bash
/use github-find-context7 find react performance ui
```

**Get React documentation:**
```bash
/use github-find-context7 docs react
```

**Compare two repositories:**
```bash
/use github-find-context7 compare facebook/react google/prettier
```

**Create a new repository:**
```bash
/use github-find-context7 create my-awesome-project "My project description"
```

**Generate deployment guide:**
```bash
/use github-find-context7 guide facebook/react
```
