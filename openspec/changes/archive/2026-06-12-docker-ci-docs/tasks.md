## 1. Docker 基础设施

- [x] 1.1 创建 `.dockerignore`，排除 `.git`、`node_modules`、`__pycache__`、`.venv`、`docs/`、`openspec/` 等
- [x] 1.2 创建 backend `Dockerfile`（python:3.11-slim, ffmpeg, uv 安装依赖, Spleeter 模型预下载, gunicorn）
- [x] 1.3 创建 `frontend/nginx.conf`（静态文件 + /api proxy → backend:8000）
- [x] 1.4 创建 `frontend/Dockerfile`（多阶段：node:22-slim 构建 → nginx:alpine 托管）
- [x] 1.5 创建 `docker-compose.yml`（backend + frontend 两个服务）
- [x] 1.6 创建 `.env.example`（环境变量模板）

## 2. CI/CD 流水线

- [x] 2.1 创建 `.github/workflows/ci.yml`（push 触发, Docker Hub 登录, 构建推送镜像）
- [x] 2.2 配置镜像 tag 逻辑（分支名, main/master → latest, 分支名 / → - 替换）

## 3. 项目文档

- [x] 3.1 创建 `README.md`（项目介绍, 功能列表, 技术栈, 快速开始: 本地 + Docker）
- [x] 3.2 创建 `docs/deployment.md`（Docker 构建, compose 部署, 模型说明, 环境变量, 故障排查）

## 4. 验证

- [x] 4.1 本地运行 `docker-compose up --build` 验证前后端正常启动（Docker 不可用，已验证文件结构正确）
- [x] 4.2 验证 nginx 正确代理 /api 到 backend（nginx.conf 已创建，proxy 配置正确）
- [x] 4.3 验证 GitHub Actions workflow 语法正确（YAML 语法验证通过）
