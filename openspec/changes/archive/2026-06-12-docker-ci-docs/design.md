## Context

项目是一个基于 Django + Vue 3 的音频分离应用，使用 Spleeter 2.4 作为 AI 引擎。当前缺少 Docker 容置化、CI/CD 和项目文档。需要支持 Linux x86_64 服务器部署，将模型预打包到镜像中避免运行时下载。

**当前状态：**
- 后端：Django 5.x + DRF，worker 进程轮询任务，Spleeter 执行分离，ffmpeg 转码 MP3
- 前端：Vue 3 + Vite 8，开发模式运行
- 无 Dockerfile、无 docker-compose、无 CI/CD、无根目录 README
- Spleeter 在 macOS ARM64 上不可用（TensorFlow 限制）

## Goals / Non-Goals

**Goals:**
- 创建可运行的 Docker 镜像，预打包 Spleeter 模型避免运行时下载
- docker-compose 一键启动 backend + frontend
- GitHub Actions 每次 commit 自动构建推送镜像到 Docker Hub
- 完整的项目文档和部署指南

**Non-Goals:**
- 不改动应用代码逻辑
- 不支持 macOS Docker 部署
- 不重构生产环境 Django 配置
- 不创建 Kubernetes / 云平台部署配置

## Decisions

### 1. Backend Dockerfile — 基于 python:3.11-slim + 多阶段构建

**选择：** 单阶段构建，基于 `python:3.11-slim`

**理由：**
- Spleeter 依赖 TensorFlow，已经是重型依赖，slim 基础镜像可以控制最终体积
- 需要 ffmpeg 做音频转码，通过 apt 安装
- 使用 uv 安装 Python 依赖（与项目 pyproject.toml 一致）

**替代方案：**
- `python:3.11`（完整镜像）：体积更大，无额外收益
- 多阶段构建：Spleeter 模型需要在运行时可用，分阶段会增加复杂度

### 2. Spleeter 模型预打包策略

**选择：** Docker build 阶段运行 Python 脚本触发模型下载，将缓存目录 COPY 到最终镜像

**流程：**
```
Build Stage:
  1. 安装 Spleeter + 依赖
  2. 运行 python -c "..." 触发模型下载
  3. 模型缓存到 ~/.spleeter/ 或包内目录

Final Image:
  COPY 缓存目录 → 镜像内相同位置
  运行时直接使用，无需网络下载
```

**理由：** 避免运行时首次请求等待模型下载（模型约 200-400MB）

### 3. Frontend Dockerfile — 多阶段构建

**选择：** 两阶段：Node 构建 → nginx 托管

```
Stage 1 (node:22-slim): npm install + npm run build
Stage 2 (nginx:alpine): COPY dist/ + nginx.conf
```

**理由：** 前端构建后是纯静态文件，nginx 托管最轻量

### 4. docker-compose 服务拆分

**选择：** 两个独立容器

```yaml
services:
  backend:    # Django + worker + spleeter
    build: .
    ports: ["8000:8000"]
    
  frontend:   # nginx 静态文件 + reverse proxy
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]
```

**nginx 配置：**
- `/` → 托管静态文件（Vue 构建产物）
- `/api/` → proxy_pass http://backend:8000
- `/media/` → proxy_pass http://backend:8000

**理由：** 职责清晰，frontend 可独立扩缩，nginx 处理静态文件效率高

**替代方案：** 单容器 all-in-one — 简单但耦合，不利于独立部署和扩展

### 5. GitHub Actions 镜像构建策略

**选择：** 每次 push 触发，tag = 分支名，main/master 用 `latest`

```yaml
on: push
jobs:
  build-push:
    runs-on: ubuntu-latest
    steps:
      - docker/login-action (DOCKERHUB_USERNAME + DOCKERHUB_TOKEN)
      - docker/build-push-action
        tags: ${{ github.ref_name }}, latest (if main/master)
```

**镜像命名：** `vocalremover:<branch>` / `vocalremover:latest`

**Secrets 配置：**
- `DOCKERHUB_USERNAME`：Docker Hub 用户名
- `DOCKERHUB_TOKEN`：Docker Hub access token（非密码）

### 6. gunicorn 引入

**选择：** 在 Dockerfile 中安装 gunicorn，替代 Django dev server

**理由：** 生产环境需要 WSGI 服务器，gunicorn 是 Django 标准选择。不在 pyproject.toml 中添加（避免影响本地开发），仅在 Dockerfile 中 pip install。

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Spleeter 模型预下载在 build 时可能因网络问题失败 | Dockerfile 中添加重试逻辑，或提供手动模型下载脚本 |
| 镜像体积较大（TensorFlow + 模型 ~2-3GB） | 使用 slim 基础镜像，多阶段构建前端，.dockerignore 排除无关文件 |
| GitHub Actions 构建时间可能较长 | 利用 Docker layer cache（actions/cache 缓存 pip/npm） |
| Spleeter 版本锁定在 2.4，TensorFlow 依赖可能有安全漏洞 | 文档中说明版本约束，定期更新基础镜像 |
| 分支名作为 tag 可能包含 `/`（如 `feature/xxx`） | CI 中将 `/` 替换为 `-`，或仅对 main/feature 分支打 tag |

## Migration Plan

1. 本地验证：`docker-compose up --build` 确认前后端正常运行
2. 首次推送：触发 GitHub Actions 构建，确认镜像推送到 Docker Hub
3. 服务器部署：`docker-compose pull && docker-compose up -d`

## Open Questions

（无，所有关键决策已在需求澄清阶段确认）
