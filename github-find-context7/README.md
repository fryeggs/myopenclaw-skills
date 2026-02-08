# GitHub Find Context7

## English Description

Search GitHub code and repositories, query official documentation for 50+ libraries/frameworks (React, Django, Express, etc.), analyze repository health, and get deployment guides. Integrates with GitHub API and Context7 documentation system.

### Features

- **GitHub Search**: Search code, repos, issues
- **Documentation Lookup**: 50+ library docs (React, Django, Express, etc.)
- **Repository Analysis**: Health checks, contributor stats
- **Deployment Guides**: Get deployment instructions

## 中文说明

搜索 GitHub 代码和仓库，查询 50+ 库/框架的官方文档（React、Django、Express 等），分析仓库健康状况，获取部署指南。集成 GitHub API 和 Context7 文档系统。

### 功能特性

- **GitHub 搜索**：搜索代码、仓库、Issues
- **文档查询**：50+ 库文档（React、Django、Express 等）
- **仓库分析**：健康检查、贡献者统计
- **部署指南**：获取部署说明

## Quick Start / 快速开始

```bash
# Search GitHub / 搜索 GitHub
python3 ~/.openclaw/skills/github-find-context7/scripts/search.py --query "react useEffect" --type code

# Get documentation / 获取文档
python3 ~/.openclaw/skills/github-find-context7/scripts/docs.py --framework react

# Analyze repository / 分析仓库
python3 ~/.openclaw/skills/github-find-context7/scripts/analyze.py --repo owner/repo

# Deployment guide / 部署指南
python3 ~/.openclaw/skills/github-find-context7/scripts/deploy.py --project docker-nodejs
```

## Supported Frameworks / 支持的框架

React, Django, Express, Vue, Angular, Next.js, Flask, Spring, Ruby on Rails, Laravel, Gin, Echo, FastAPI, Phoenix, NestJS, Svelte, SolidJS, Nuxt, Remix, Astro, Tailwind CSS, Bootstrap, Material-UI, Ant Design, Styled Components, Redux, MobX, Zustand, Recoil, TanStack Query, Axios, Request, Express.js, Koa, Hapi, Fastify, Socket.IO, Prisma, TypeORM, Sequelize, Mongoose, Drizzle, Knex, Django ORM, SQLAlchemy, Hibernate, JPA, Entity Framework Core, NHibernate, Pydantic, Marshmallow, Cattrs, attrs, dataclasses

See `SKILL.md` for detailed documentation.

查看 `SKILL.md` 了解详细文档。
