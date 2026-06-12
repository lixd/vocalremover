---
comet_change: ai-audio-separator
role: technical-design
canonical_spec: openspec
---

# Technical Design: AI Audio Separator

## Overview

AI Audio Separator is a web application that lets users upload audio files and separate them into individual stems (vocals, drums, bass, other) using Spleeter. The result page provides per-stem waveform preview with playback controls and download options.

## Architecture

Monorepo with two main directories:

```
vocalremover/
├── backend/          # Django + DRF
├── frontend/         # Vue 3 + Vite + TypeScript
├── .gitignore
└── README.md
```

### System Architecture

```
┌──────────┐     ┌─────────────────┐     ┌──────────────┐
│  Vue 3   │────▶│    Django       │────▶│    SQLite    │
│   SPA    │     │  (API + Admin)  │     │    (DB)      │
└────┬─────┘     └────────┬────────┘     └──────┬───────┘
     │                    │                      │
     │    ┌───────────────┘                      │
     │    ▼                                      │
     │  ┌──────────────┐    poll tasks          │
     │  │   Worker     │◀───────────────────────┘
     │  │  (管理命令)   │
     │  └──────┬───────┘
     │         ▼
     │  ┌──────────────┐
     │  │  Spleeter    │
     │  │  (Python API)│
     │  └──────────────┘
     │
     └──▶  File System (media/uploads/ + media/stems/)
```

### Component Interaction

1. Vue SPA sends multipart POST (file + mode) to Django API
2. Django validates, stores upload, creates Task record (status=PENDING)
3. Frontend starts polling GET /api/tasks/{id}/ every 3 seconds
4. Worker management command polls DB every 2 seconds for PENDING tasks
5. Worker picks up task, invokes Spleeter Python API, saves stems
6. Task transitions to COMPLETED (or FAILED on error)
7. Frontend detects COMPLETED, renders StemPlayer components with waveform + playback + download

## Backend Design

### Project Structure

```
backend/
├── pyproject.toml              # uv dependencies
├── manage.py
├── config/                     # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── separator/                  # Core app
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── worker.py               # Worker polling logic
│   ├── separation.py           # Spleeter wrapper
│   └── management/
│       └── commands/
│           ├── run_worker.py
│           └── cleanup_old_tasks.py
└── media/                      # Runtime files (gitignored)
    ├── uploads/{task_id}/
    └── stems/{task_id}/
```

### Task Model

```python
class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PROCESSING = "PROCESSING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    class Mode(models.TextChoices):
        TWO_STEMS = "2stems"
        FOUR_STEMS = "4stems"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    mode = models.CharField(max_length=16, choices=Mode.choices)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    stems = models.JSONField(default=dict)
```

### API Endpoints

| Method | Path | View Action | Description |
|--------|------|------------|-------------|
| POST | `/api/tasks/` | `create` | Upload file + select mode, returns task_id |
| GET | `/api/tasks/{id}/` | `retrieve` | Task status + metadata |
| GET | `/api/tasks/{id}/stems/` | `stems` | List available stems with metadata |
| GET | `/api/tasks/{id}/stems/{name}/` | `stem_download` | Download stem file (Content-Disposition) |
| GET | `/api/tasks/{id}/stems/{name}/stream/` | `stem_stream` | Stream stem for playback (Range support) |
| GET | `/api/tasks/{id}/stems/download-all/` | `download_all` | Download all stems as ZIP |

### Worker Process

Implementation as Django management command `run_worker`:

- Infinite loop, SELECT FOR UPDATE every 2 seconds for PENDING tasks
- Single-task sequential processing (Spleeter is CPU-bound, no concurrency benefit)
- On pickup: status → PROCESSING, call `separation.separate_audio(task)`
- On success: save stems to `media/stems/{task_id}/`, update `task.stems` JSON, status → COMPLETED, set `completed_at`
- On failure: status → FAILED, populate `error_message`
- SIGTERM handler: complete current task, then exit gracefully
- Startup recovery: reset PROCESSING tasks older than 30 minutes to FAILED

### Spleeter Integration (separation.py)

```python
def separate_audio(task: Task) -> dict[str, str]:
    """Invoke Spleeter to separate audio file.

    Args:
        task: Task instance with mode and uploaded file path.

    Returns:
        Dict mapping stem names to file paths, e.g.
        {"vocals": "/path/to/vocals.wav", "accompaniment": "/path/to/accompaniment.wav"}

    Raises:
        SeparationError: If Spleeter inference fails.
    """
```

Uses Spleeter's Python API via `spleeter.separate` module, calling `separate_to_file()` or the equivalent programmatic interface. Not CLI subprocess.

Mode mapping:
- `2stems` → `spleeter:2stems` preset → vocals.wav, accompaniment.wav
- `4stems` → `spleeter:4stems` preset → vocals.wav, drums.wav, bass.wav, other.wav

### File Storage

```
media/
├── uploads/
│   └── {task_id}/
│       └── original.{ext}        # Preserves original extension
└── stems/
    └── {task_id}/
        ├── vocals.wav
        ├── accompaniment.wav     # 2-stem mode
        ├── drums.wav             # 4-stem mode
        ├── bass.wav              # 4-stem mode
        └── other.wav             # 4-stem mode
```

Django settings:
- `MEDIA_ROOT = BASE_DIR / "media"`
- `MEDIA_URL = "/media/"`

### Admin Configuration

Custom `TaskAdmin`:
- `list_display`: id (truncated), status, mode, original_filename, file_size, created_at
- `list_filter`: status, mode
- `search_fields`: original_filename, id
- `readonly_fields`: completed_at, error_message, stems
- Actions: "Mark as Failed" for stuck PROCESSING tasks

### Cleanup Command

Management command `cleanup_old_tasks`:
- Delete tasks where `created_at < now() - 24 hours`
- Delete associated files (uploads + stems directories)
- Log deletion count
- Designed for cron execution (e.g., every hour)

## Frontend Design

### Project Structure

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts              # Proxy /api to Django
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/
│   │   └── index.ts
│   ├── api/
│   │   └── client.ts           # Axios instance + API functions
│   ├── composables/
│   │   ├── useTask.ts          # Task creation + polling
│   │   └── useAudioPlayer.ts   # Audio playback with wavesurfer.js
│   ├── components/
│   │   ├── FileUploader.vue    # Drag-and-drop + click upload
│   │   ├── ModeSelector.vue    # 2-stem / 4-stem toggle
│   │   ├── TaskProgress.vue    # Status display + polling
│   │   ├── StemPlayer.vue      # Waveform + playback + download
│   │   └── DownloadPanel.vue   # Download all (ZIP)
│   ├── views/
│   │   ├── HomeView.vue        # Upload page
│   │   └── ResultView.vue      # Result page
│   └── types/
│       └── index.ts            # TypeScript interfaces
└── public/
```

### Routing

| Path | Component | Description |
|------|-----------|-------------|
| `/` | HomeView | File upload + mode selection |
| `/result/:taskId` | ResultView | Processing progress + stem playback |

### Page Flow

**HomeView:**
1. FileUploader accepts drag-and-drop or click-to-upload
2. Client-side validation: format (mp3/wav/flac/ogg/m4a) and size (≤ 20MB)
3. ModeSelector: 2-stem (default) or 4-stem
4. On submit: POST /api/tasks/ → receive task_id → router.push(`/result/${taskId}`)

**ResultView:**
1. TaskProgress starts polling via useTask composable (3s interval)
2. Shows status text: "Waiting...", "Processing...", "Completed!" or "Failed: {error}"
3. On COMPLETED: renders StemPlayer for each stem
4. Each StemPlayer shows:
   - wavesurfer.js waveform visualization
   - Play/Pause button
   - Current time / total duration
   - Seek by clicking/dragging waveform
   - Download button for that stem
5. DownloadPanel provides "Download All" button (ZIP of all stems)

### StemPlayer Component

Core functionality using wavesurfer.js v7:

```typescript
// Each stem gets an independent WaveSurfer instance
const wavesurfer = WaveSurfer.create({
  container: waveformRef.value,
  url: `/api/tasks/${taskId}/stems/${stemName}/stream/`,
  height: 80,
  waveColor: '#409EFF',
  progressColor: '#1D9BF0',
})
```

Features:
- Independent playback per stem (user can play multiple simultaneously)
- Waveform rendering from audio stream URL
- Play/pause toggle
- Click-to-seek on waveform
- Time display (current / total)
- Loading state while waveform renders
- Error state if audio fails to load

### Composables

**useTask(taskId)**:
- `task`: reactive Task object (status, stems, error_message, etc.)
- `startPolling()`: starts 3-second interval polling
- `stopPolling()`: stops polling (called on COMPLETED/FAILED/unmount)
- `isLoading`: boolean

**useAudioPlayer(url)**:
- `wavesurfer`: WaveSurfer instance
- `isPlaying`: boolean
- `currentTime`: number
- `duration`: number
- `play() / pause() / seekTo(time)`: playback controls
- Cleanup on unmount

### Vite Proxy Configuration

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/media': 'http://localhost:8000',
    }
  }
})
```

## Error Handling

### Backend Error Responses

| Scenario | HTTP Status | Response Body |
|----------|------------|---------------|
| Unsupported file format | 400 | `{"error": "Unsupported format. Allowed: mp3, wav, flac, ogg, m4a"}` |
| File exceeds 20MB | 413 | `{"error": "File too large. Max size: 20MB"}` |
| Missing mode parameter | 400 | `{"error": "Mode is required. Choose '2stems' or '4stems'"}` |
| Task not found | 404 | `{"error": "Task not found"}` |
| Stem not found | 404 | `{"error": "Stem not found"}` |
| Server error | 500 | `{"error": "Internal server error"}` |

### Worker Error Handling

- Spleeter inference failure → try/except → `status=FAILED` + `error_message` populated
- Worker crash (OOM, SIGKILL) → task stuck at PROCESSING → recovered on next worker startup (30-min timeout)
- SQLite write contention → Django ORM built-in retry (single-worker MVP avoids this)

### Frontend Error Handling

- Upload failure: `ElMessage.error()` with server error message
- Polling failure: 3 consecutive failures → stop polling, show "Network error, please refresh"
- Audio load failure: StemPlayer shows error state with retry option

### Edge Cases

- Empty file / non-audio content: rejected by format validation
- Filename with special characters: stored by task_id, original name for display only
- Concurrent uploads of same file: each creates independent Task (no dedup)
- Browser tab close during processing: task continues server-side, user can revisit URL

## Testing Strategy

### Backend Tests (pytest + pytest-django)

| Category | Coverage |
|----------|----------|
| Model tests | Task creation, status transitions, UUID generation |
| Serializer tests | Validation rules, field serialization |
| API tests | Each endpoint: success path + error paths |
| Worker tests | State transitions, error handling, timeout recovery |
| Separation tests | Mock Spleeter, verify file output, error scenarios |

Key test pattern: Mock Spleeter's `AudioProcessor` in unit tests to avoid real AI inference dependency.

### Frontend Tests (Vitest + Vue Test Utils)

| Category | Coverage |
|----------|----------|
| FileUploader | File selection, drag-drop, format/size validation |
| ModeSelector | Toggle behavior, default state |
| TaskProgress | Polling lifecycle, status display |
| API client | Request/response handling |

### E2E (Manual for MVP)

- Upload MP3 → 2-stem separation → play vocals waveform → download accompaniment
- Upload WAV → 4-stem separation → play each stem independently
- Upload invalid file → see error message
- Upload > 20MB → see error message

## Deployment (MVP)

| Component | Technology | Port |
|-----------|-----------|------|
| Vue frontend | `vite build` → static files served by Nginx | 80/443 |
| Django API | gunicorn | 8000 (internal) |
| Worker | systemd service (`python manage.py run_worker`) | N/A |
| Reverse proxy | Nginx | 80/443 |
| Database | SQLite | file |
| File storage | Local disk | N/A |

### Nginx Configuration

```
server {
    listen 80;

    # Frontend static files
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # Media files (with Range support for audio streaming)
    location /media/ {
        alias /path/to/backend/media/;
        add_header Accept-Ranges bytes;
    }
}
```

### systemd Services

```ini
# /etc/systemd/system/audio-separator-api.service
[Unit]
Description=Audio Separator API
After=network.target

[Service]
User=deploy
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/audio-separator-worker.service
[Unit]
Description=Audio Separator Worker
After=network.target

[Service]
User=deploy
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python manage.py run_worker
Restart=always

[Install]
WantedBy=multi-user.target
```

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Python | CPython | 3.11+ |
| Package Manager | uv | latest |
| Backend Framework | Django + DRF | 5.x / 3.x |
| AI Engine | Spleeter | 2.4 |
| Database | SQLite (MVP) | - |
| Frontend Framework | Vue 3 | 3.x |
| Build Tool | Vite | 6.x |
| Language | TypeScript | 5.x |
| UI Library | Element Plus | latest |
| Audio Visualization | wavesurfer.js | 7.x |
| HTTP Client | axios | 1.x |
| Process Manager | systemd | - |
| Reverse Proxy | Nginx | - |
