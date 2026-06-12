# Design: AI Audio Separator

## Architecture Overview

The system follows a classic web application architecture with an async task processing pattern. Django serves as both the API server and the Admin backend, while an independent Worker process handles AI inference.

```
┌──────────┐     ┌─────────────────┐     ┌──────────────┐
│  Vue 3   │────▶│    Django       │────▶│    SQLite    │
│   SPA    │     │  (API + Admin)  │     │    (DB)      │
└────┬─────┘     └────────┬────────┘     └──────┬───────┘
     │                    │                      │
     │                    │                      │
     │    ┌───────────────┘                      │
     │    │                                      │
     │    │                                      │
     │    ▼                                      │
     │  ┌──────────────┐    poll tasks          │
     │  │   Worker     │◀───────────────────────┘
     │  │  (独立进程)   │
     │  └──────┬───────┘
     │         │
     │         ▼
     │  ┌──────────────┐
     │  │  Spleeter    │
     │  │  (AI 推理)   │
     │  └──────────────┘
     │
     └──▶  File System (uploads + stems)
```

## Key Design Decisions

### 1. Django as Backend Framework

**Decision**: Use Django with Django REST Framework (DRF) for API endpoints.

**Rationale**:
- Built-in ORM for task state management
- Django Admin provides immediate task monitoring UI
- Mature ecosystem, extensive documentation
- Database migrations built-in

**Trade-offs**: Heavier than FastAPI, but the Admin and ORM benefits outweigh the overhead for this use case.

### 2. Independent Worker Process

**Decision**: Run Worker as a separate Python process that polls the database for pending tasks.

**Rationale**:
- API Server and Worker can be scaled independently
- Worker crash doesn't affect API availability
- Simple to implement (poll DB every N seconds)
- Easy to add more workers later (horizontal scaling)
- No external message queue dependency (Redis/RabbitMQ)

**Trade-off**: Polling adds slight latency (1-3 seconds) vs push-based queues, but acceptable for tasks that take 1-10 minutes.

### 3. Spleeter for AI Inference

**Decision**: Use Deezer's Spleeter as the initial AI model, running on CPU.

**Rationale**:
- Fastest inference on CPU among alternatives
- Low memory footprint (~2GB)
- Native Python integration
- Simple API: `spleeter separate -p spleeter:2stems -o output/ audio.mp3`
- Quality acceptable for MVP

**Upgrade path**: Architecture supports swapping to Demucs v4 or MDX-Net without changing API or Worker interface.

### 4. SQLite Database

**Decision**: Use SQLite for task state storage in MVP.

**Rationale**:
- Zero configuration / deployment overhead
- Sufficient for single-server deployment
- Django ORM abstracts the database layer
- Easy migration path to PostgreSQL when scaling

### 5. Frontend Polling for Progress

**Decision**: Frontend polls `GET /api/tasks/{id}/` every 3 seconds for status updates.

**Rationale**:
- Simple to implement (no WebSocket complexity)
- Tasks take minutes, 3-second polling is more than sufficient
- No additional server-side infrastructure needed
- Can upgrade to WebSocket/SSE later if needed

### 6. File Storage Strategy

**Decision**: Store files on local filesystem with structured directories.

```
media/
├── uploads/          # Original uploaded files
│   └── {task_id}/
│       └── original.mp3
└── stems/            # Separated stems
    └── {task_id}/
        ├── vocals.wav
        ├── accompaniment.wav
        ├── drums.wav
        ├── bass.wav
        └── other.wav
```

**Cleanup strategy**: Tasks and files auto-delete after 24 hours via Django management command (cron job).

## Data Flow

### Upload & Process Flow

```
1. User uploads audio file
2. Django API:
   a. Validate file (format, size ≤ 20MB)
   b. Save file to media/uploads/{task_id}/
   c. Create Task record (status=PENDING)
   d. Return task_id to frontend
3. Frontend starts polling GET /api/tasks/{task_id}/
4. Worker (polling loop):
   a. Picks up PENDING task
   b. Sets status=PROCESSING
   c. Invokes Spleeter
   d. Saves stems to media/stems/{task_id}/
   e. Sets status=COMPLETED, stores result metadata
5. Frontend receives COMPLETED status
6. Frontend renders stem player UI with playback/download buttons
7. User clicks download → GET /api/tasks/{task_id}/stems/{stem_name}/
```

### Error Handling Flow

```
1. Invalid file format → 400 Bad Request (immediate)
2. File too large → 413 Payload Too Large (immediate)
3. Spleeter inference failure → Task status=FAILED, error_message stored
4. Frontend shows error message with retry option
5. Cleanup: failed task files deleted by cleanup command
```

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/tasks/` | Create new separation task (multipart: file + mode) |
| `GET` | `/api/tasks/{id}/` | Get task status and metadata |
| `GET` | `/api/tasks/{id}/stems/` | List available stems |
| `GET` | `/api/tasks/{id}/stems/{name}/` | Download specific stem file |
| `GET` | `/api/tasks/{id}/stems/{name}/stream/` | Stream stem for playback |

### Task Model

```python
class Task(models.Model):
    id = UUIDField(primary_key=True)
    status = CharField(choices=[PENDING, PROCESSING, COMPLETED, FAILED])
    mode = CharField(choices=[TWO_STEMS, FOUR_STEMS])
    original_filename = CharField()
    file_size = IntegerField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    completed_at = DateTimeField(null=True)
    error_message = TextField(null=True)
    stems = JSONField(default=dict)  # {"vocals": "path", ...}
```

## Frontend Architecture

```
src/
├── components/
│   ├── FileUploader.vue      # Drag-drop + click upload
│   ├── StemPlayer.vue        # Waveform + playback controls
│   ├── TaskProgress.vue      # Progress bar + status
│   └── DownloadPanel.vue     # Download buttons
├── views/
│   ├── HomeView.vue          # Main upload page
│   └── ResultView.vue        # Task result with stems
├── composables/
│   ├── useTask.ts            # Task creation + polling
│   └── useAudioPlayer.ts     # Audio playback logic
└── api/
    └── client.ts             # Axios/fetch API client
```

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Vue 3 + Vite + TypeScript | Latest |
| UI Library | Element Plus or Naive UI | Latest |
| Audio Visualization | wavesurfer.js | 7.x |
| Backend | Django + DRF | 5.x / 3.x |
| AI Engine | Spleeter | 2.4 |
| Database | SQLite (MVP) | - |
| Process Manager | systemd / supervisord | - |
