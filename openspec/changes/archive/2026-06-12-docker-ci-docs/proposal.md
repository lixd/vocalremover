## Why

项目目前缺少容器化部署能力、项目文档和 CI/CD 流水线。需要支持 Linux x86_64 服务器的 Docker 一键部署，将 Spleeter 模型预打包到镜像中避免运行时下载，并通过 GitHub Actions 实现每次 commit 自动构建推送镜像到 Docker Hub。

## What Changes

- 新增 `Dockerfile`：打包 backend（Django + worker + Spleeter + ffmpeg + 预下载模型），基于 Linux x86_64
- 新增 `frontend/Dockerfile`：基于 nginx 托管构建后的静态文件
- 新增 `docker-compose.yml`：编排 backend + frontend 两个容器
- 新增 `frontend/nginx.conf`：nginx 配置，proxy /api 到 backend 容器
- 新增 `.dockerignore`：排除不必要文件，优化构建上下文
- 新增 `.github/workflows/ci.yml`：每次 commit 构建推送镜像到 Docker Hub，tag = 分支名，main/master 用 `latest`
- 新增 `.env.example`：环境变量模板
- 新增 `README.md`：项目介绍 + 快速开始
- 新增 `docs/deployment.md`：详细部署指南（Docker 构建、compose 部署、模型说明）

## Capabilities

### New Capabilities

- `docker-containerization`：Docker 镜像构建和容器编排，包括 Dockerfile、docker-compose、nginx 配置
- `ci-cd-pipeline`：GitHub Actions 自动构建推送 Docker 镜像到 Docker Hub
- `project-documentation`：项目 README 和部署文档

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- **代码**：无应用代码改动，仅新增配置文件和文档
- **依赖**：无新增应用依赖；Docker 构建引入 nginx、gunicorn 等运行时依赖
- **基础设施**：需要 Docker Hub 账号和 GitHub Secrets（`DOCKERHUB_USERNAME`、`DOCKERHUB_TOKEN`）
- **平台**：仅支持 Linux x86_64 部署（Spleeter + TensorFlow 限制）
