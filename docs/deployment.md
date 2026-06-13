# Deployment Guide

This guide covers deploying VocalRemover using Docker on Linux x86_64 servers.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM (Spleeter + TensorFlow requirement)
- 10GB+ disk space (models + images)

## Docker Image Overview

The application is split into two Docker images:

| Image | Description |
|-------|-------------|
| `vocalremover-backend` | Django API + background worker + Spleeter AI engine |
| `vocalremover-frontend` | nginx serving Vue.js static files + reverse proxy |

**Key feature:** Spleeter models are pre-baked into the backend image during build, eliminating runtime model downloads.

## Quick Deployment

### 1. Clone and Configure

```bash
git clone https://github.com/youruser/vocalremover.git
cd vocalremover
cp .env.example .env
```

Edit `.env` with your settings:
```bash
DJANGO_SECRET_KEY=your-random-secret-key
DJANGO_ALLOWED_HOSTS=your-domain.com
FRONTEND_PORT=80
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Verify

```bash
# Check containers are running
docker-compose ps

# Check backend health
curl http://localhost:8000/api/tasks/

# Check frontend
curl http://localhost
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

### Docker Compose Build

```bash
docker-compose up --build
```

## Spleeter Model Service

### How Models Work

Spleeter uses pre-trained TensorFlow models for audio separation:

- **2-stem model:** Separates vocals + accompaniment
- **4-stem model:** Separates vocals + drums + bass + other

### Model Pre-baking

Models are downloaded during Docker image build and baked into the image:

```dockerfile
# This runs during docker build
RUN python -c "from spleeter.separator import Separator; ..."
```

**Benefits:**
- No runtime downloads
- Faster container startup
- Works in air-gapped environments

**Model size:** ~200-400MB added to image

### Manual Model Download (Optional)

If you need to pre-download models without Docker:

```bash
cd backend
python -c "
from spleeter.separator import Separator
import numpy as np

# Download 2-stem model
s = Separator('spleeter:2stems')
s.separate(np.random.randn(1, 44100 * 10, 2).astype(np.float32))

# Download 4-stem model
s = Separator('spleeter:4stems')
s.separate(np.random.randn(1, 44100 * 10, 2).astype(np.float32))

print('Models downloaded to cache')
"
```

Models are cached in `~/.spleeter/` or Python's cache directory.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-key...` | Django secret key (CHANGE THIS!) |
| `DJANGO_DEBUG` | `false` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `FRONTEND_PORT` | `80` | Port for frontend access |
| `DOCKERHUB_USERNAME` | - | Docker Hub username (CI only) |
| `DOCKERHUB_PASSWORD` | - | Docker Hub token (CI only) |

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

1. **Increase gunicorn workers:**
   ```yaml
   # In docker-compose.yml
   command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 8
   ```

2. **Add volume for media persistence:**
   Already configured in docker-compose.yml

3. **Enable Docker layer caching** in CI (already configured)

### Monitoring

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check resource usage
docker stats
```

## Troubleshooting

### Build fails at Spleeter model download

**Symptom:** `docker build` hangs or fails during model pre-download

**Solution:**
- Ensure internet access during build
- Try building with `--no-cache` flag
- Check Docker has enough disk space (10GB+)

### Backend container exits immediately

**Symptom:** `docker-compose ps` shows backend as "Exit 1"

**Solution:**
```bash
docker-compose logs backend
```
Common issues:
- Missing `DJANGO_SECRET_KEY`
- Port 8000 already in use

### Frontend shows 502 Bad Gateway

**Symptom:** Frontend loads but API calls fail

**Solution:**
- Check backend is running: `docker-compose ps`
- Check nginx config connects to correct backend hostname
- Verify network: `docker-compose exec frontend ping backend`

### Models not found error

**Symptom:** `spleeter` raises model not found error

**Solution:**
- Models should be pre-baked. If missing, rebuild image:
  ```bash
  docker-compose build --no-cache backend
  ```

## Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Uninstall

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi vocalremover-backend vocalremover-frontend

# Remove volumes
docker volume rm vocalremover_backend-media
```
