# docker-containerization Specification

## Purpose
TBD - created by archiving change docker-ci-docs. Update Purpose after archive.
## Requirements
### Requirement: Backend Docker image
The system SHALL provide a Dockerfile at project root that builds a runnable backend image containing Django, the worker process, Spleeter 2.4, ffmpeg, and pre-downloaded Spleeter models. The image SHALL be based on `python:3.11-slim` and target Linux x86_64.

#### Scenario: Build backend image
- **WHEN** developer runs `docker build -t vocalremover-backend .` at project root
- **THEN** image builds successfully without errors

#### Scenario: Backend starts without model download
- **WHEN** backend container starts for the first time on a machine with no internet
- **THEN** Spleeter models SHALL be available in the image and no download occurs

#### Scenario: Backend serves API
- **WHEN** backend container is running
- **THEN** Django dev server (or gunicorn) SHALL listen on port 8000 and respond to health check

### Requirement: Frontend Docker image
The system SHALL provide a Dockerfile at `frontend/Dockerfile` that builds a two-stage image: Node.js for building Vue assets, nginx:alpine for serving static files.

#### Scenario: Build frontend image
- **WHEN** developer runs `docker build -t vocalremover-frontend ./frontend`
- **THEN** image builds successfully with Vue app compiled and served by nginx

#### Scenario: Nginx serves static files
- **WHEN** frontend container is running
- **THEN** nginx SHALL serve Vue app on port 80 and proxy `/api/` requests to `backend:8000`

### Requirement: Docker Compose orchestration
The system SHALL provide a `docker-compose.yml` at project root that orchestrates backend and frontend containers.

#### Scenario: One-command startup
- **WHEN** developer runs `docker-compose up --build` at project root
- **THEN** both containers start, frontend is accessible on port 80, and backend API is accessible via `/api/`

#### Scenario: Backend dependency
- **WHEN** docker-compose starts
- **THEN** frontend container SHALL wait for backend to be ready before accepting traffic

### Requirement: Nginx reverse proxy configuration
The system SHALL provide an `nginx.conf` that serves Vue static files and proxies API requests to the backend container.

#### Scenario: Static file serving
- **WHEN** request hits `GET /`
- **THEN** nginx serves the Vue app's `index.html`

#### Scenario: API proxy
- **WHEN** request hits `GET /api/tasks/`
- **THEN** nginx proxies the request to `http://backend:8000/api/tasks/`

### Requirement: Docker ignore rules
The system SHALL provide a `.dockerignore` file that excludes `.git`, `node_modules`, `__pycache__`, `.venv`, `docs/`, `openspec/`, and other non-essential files from the Docker build context.

#### Scenario: Build context excluded
- **WHEN** Docker builds any image
- **THEN** excluded directories SHALL NOT be included in build context

