# VocalRemover

AI-powered audio stem separation tool. Separate vocals, drums, bass, and other instruments from any audio file.

## Features

- **Vocal Remover** — Remove vocals from songs, get instrumental tracks
- **Stem Splitter** — Split audio into 4 stems: vocals, drums, bass, other
- **Audio Cutter** — Cut and trim audio files (coming soon)
- **Audio Merger** — Merge multiple audio tracks (coming soon)
- **BPM/Key Detector** — Detect BPM and musical key (coming soon)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x + DRF 3.x |
| Frontend | Vue 3 + Vite 8 + TypeScript |
| AI Engine | Spleeter 2.4 (Deezer) |
| Audio | ffmpeg |
| Database | SQLite |
| UI | Element Plus |

## Quick Start

### Local Development

**Backend:**
```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py run_worker &  # Start background worker
uv run python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

### Docker Deployment

```bash
# Clone and start
git clone https://github.com/youruser/vocalremover.git
cd vocalremover
cp .env.example .env  # Edit with your settings
docker-compose up -d
```

Visit `http://localhost` (or your configured port)

## Docker Images

Pre-built images are available on Docker Hub:
- `youruser/vocalremover-backend`
- `youruser/vocalremover-frontend`

Or build locally:
```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/` | Create separation task |
| GET | `/api/tasks/` | List all tasks |
| GET | `/api/tasks/{id}/` | Get task details |
| GET | `/api/tasks/{id}/download/{stem}/` | Download separated stem |
| DELETE | `/api/tasks/{id}/` | Delete task |
| POST | `/api/tasks/{id}/retry/` | Retry failed task |

## Configuration

See `.env.example` for all available environment variables.

## Documentation

- [Deployment Guide](docs/deployment.md) — Detailed Docker deployment instructions
- [Design Specs](docs/superpowers/specs/) — Technical design documents

## License

MIT License — see [LICENSE](LICENSE)
