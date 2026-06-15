# Deployment Guide

This guide covers deploying VocalRemover using Docker on Linux x86_64 servers.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM (Spleeter + TensorFlow requirement)
- 10GB+ disk space (models + images)

## Architecture

The application runs as **three containers**:

| Container | Description |
|-----------|-------------|
| `vocalremover-backend` | Django API server (gunicorn) |
| `vocalremover-worker` | Background audio separation worker (polls DB for tasks) |
| `vocalremover-frontend` | nginx serving Vue.js static files + reverse proxy to backend |

Backend and worker share the same Docker image, differentiated by the `WORKER_MODE` environment variable. They share a data volume for SQLite database and media files.

**Key feature:** Spleeter models are pre-baked into the backend image during build, eliminating runtime model downloads.

## Quick Deployment (Pre-built Images)

### 1. Create Project Directory

```bash
mkdir vocalremover && cd vocalremover
```

### 2. Create docker-compose.yml

```yaml
services:
  backend:
    image: lixd96/vocalremover-backend:latest
    container_name: vocalremover-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - backend-data:/app/media
    environment:
      - DJANGO_SECRET_KEY=your-random-secret-key
      - DJANGO_DEBUG=false
      - DJANGO_ALLOWED_HOSTS=*

  worker:
    image: lixd96/vocalremover-backend:latest
    container_name: vocalremover-worker
    restart: unless-stopped
    volumes:
      - backend-data:/app/media
    environment:
      - WORKER_MODE=worker
      - DJANGO_SECRET_KEY=your-random-secret-key
      - DJANGO_DEBUG=false
      - DJANGO_ALLOWED_HOSTS=*
    depends_on:
      - backend

  frontend:
    image: lixd96/vocalremover-frontend:latest
    container_name: vocalremover-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  backend-data:
```

> **For servers in China:** Replace `lixd96/` with your Docker Hub mirror prefix, e.g. `xdel6itq0zfw8s.xuanyuan.run/lixd96/`. Make sure Docker daemon is configured with `registry-mirrors` in `/etc/docker/daemon.json`.

### 3. Start Services

```bash
docker compose up -d
```

The backend container automatically runs database migrations on startup. No manual initialization needed.

### 4. Verify

```bash
# Check all three containers are running
docker compose ps

# Check backend API
curl http://localhost:8000/api/tasks/

# Check frontend
curl http://localhost

# Check worker logs
docker logs vocalremover-worker
```

## Building Images Locally

### Backend Image

```bash
docker build -t vocalremover-backend .
```

**Build process:**
1. Installs Python 3.11, ffmpeg, and system dependencies
2. Installs Python packages via uv (Django, Spleeter, etc.)
3. **Pre-downloads Spleeter models** (~200-400MB) into the image
4. Installs gunicorn for production serving

### Frontend Image

```bash
docker build -t vocalremover-frontend ./frontend
```

**Build process:**
1. Stage 1: Compiles Vue.js app with Node.js 22
2. Stage 2: Copies built assets to nginx:alpine

### Build All and Start

```bash
docker compose up --build -d
```

## Spleeter Model Service

### How Models Work

Spleeter uses pre-trained TensorFlow models for audio separation:

- **2-stem model:** Separates vocals + accompaniment
- **4-stem model:** Separates vocals + drums + bass + other

### Model Pre-baking

Models are downloaded during Docker image build and baked into the image. No runtime downloads needed.

**Model size:** ~200-400MB added to image

### Manual Model Download (Optional)

```bash
cd backend
python -c "
from spleeter.separator import Separator
import numpy as np

s2 = Separator('spleeter:2stems')
s2.separate(np.random.randn(44100 * 10, 2).astype(np.float32))

s4 = Separator('spleeter:4stems')
s4.separate(np.random.randn(44100 * 10, 2).astype(np.float32))

print('Models downloaded')
"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-key...` | Django secret key (**CHANGE THIS!**) |
| `DJANGO_DEBUG` | `false` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `FRONTEND_PORT` | `80` | Port for frontend access |
| `BACKEND_PORT` | `8000` | Port for backend API |
| `WORKER_MODE` | - | Set to `worker` to run as worker instead of API server |
| `DOCKER_REGISTRY` | `lixd96` | Docker Hub account/registry prefix |
| `IMAGE_TAG` | `latest` | Image tag to pull |
| `DOCKERHUB_USERNAME` | - | Docker Hub username (CI only) |
| `DOCKERHUB_PASSWORD` | - | Docker Hub password (CI only) |

## Production Recommendations

### Security

1. **Change secret key:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Set DEBUG=false** (already default in .env.example)

3. **Restrict ALLOWED_HOSTS** to your domain

4. **Use HTTPS** — Add nginx reverse proxy with SSL/TLS

### Performance

1. **Increase gunicorn workers** for high-traffic deployments

2. **Scale workers** — add more worker containers if separation tasks queue up:
   ```bash
   docker compose up -d --scale worker=2
   ```

3. **Enable Docker layer caching** in CI (already configured)

### Monitoring

```bash
# View logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend

# Check resource usage
docker stats
```

## Troubleshooting

### Task stuck in PENDING

**Symptom:** File uploaded but separation never starts

**Solution:** Check the worker container is running:
```bash
docker compose ps worker
docker logs vocalremover-worker
```
The worker container must be running to process separation tasks.

### Build fails at Spleeter model download

**Symptom:** `docker build` hangs or fails during model pre-download

**Solution:**
- Ensure internet access during build
- Try building with `--no-cache` flag
- Check Docker has enough disk space (10GB+)

### Backend container exits immediately

**Symptom:** `docker compose ps` shows backend as "Exit 1"

**Solution:**
```bash
docker compose logs backend
```
Common issues:
- Missing `DJANGO_SECRET_KEY`
- Port already in use

### Frontend shows 502 Bad Gateway

**Symptom:** Frontend loads but API calls fail

**Solution:**
- Check backend is running: `docker compose ps`
- Check nginx config connects to correct backend hostname
- Verify network: `docker compose exec frontend ping backend`

### Database not initialized

**Symptom:** `no such table: separator_task` error

**Solution:** Migrations run automatically on container startup. If issues persist:
```bash
docker compose exec backend .venv/bin/python manage.py migrate
```

## Updating

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

## Uninstall

```bash
# Stop and remove containers
docker compose down

# Remove images
docker rmi lixd96/vocalremover-backend lixd96/vocalremover-frontend

# Remove volumes (deletes all data)
docker volume rm vocalremover_backend-data
```
