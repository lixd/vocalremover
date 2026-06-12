# Brainstorm Summary

- Change: ai-audio-separator
- Date: 2026-06-10

## Confirmed Technical Approach

**Monorepo structure**: `backend/` (Django) + `frontend/` (Vue 3) in one repository.

**Backend stack**:
- Django 5.x + DRF 3.x for API
- SQLite (MVP) with Task model (UUID PK, status state machine, JSONField for stems)
- Spleeter 2.4 via Python API (CPU, ~2GB memory)
- Worker as Django management command (`run_worker`), single-task sequential processing
- uv for Python dependency management

**Frontend stack**:
- Vue 3 + Vite + TypeScript
- Element Plus for UI components
- wavesurfer.js v7 for stem waveform playback
- Composable pattern (useTask, useAudioPlayer) — no Pinia for MVP
- Two pages: HomeView (upload) → ResultView (progress + stems)

**Key design choices**:
- Single-task sequential Worker (CPU-bound, no benefit from concurrency)
- Django FileResponse + HTTP Range for audio streaming (no Nginx X-Accel for MVP)
- Polling (3s interval) for task status updates (no WebSocket)
- Local filesystem storage with structured directory layout

## Key Trade-offs and Risks

1. **Spleeter quality**: CPU-only, quality is acceptable but not best-in-class. Architecture supports swapping to Demucs later.
2. **SQLite concurrency**: Single-write limitation acceptable for MVP single-server. Migration path to PostgreSQL exists.
3. **Worker crash recovery**: PROCESSING tasks stuck > 30 min are auto-reset to FAILED on worker startup.
4. **Django serving audio**: Acceptable for MVP file sizes (~50MB WAV). Production should use Nginx direct serving.

## Testing Strategy

- **Backend**: pytest + pytest-django for models, serializers, API endpoints, Worker logic
- **Spleeter mocking**: Mock AudioProcessor in unit tests to avoid real AI inference
- **Frontend**: Vitest + Vue Test Utils for components (FileUploader, ModeSelector, TaskProgress)
- **E2E**: Manual for MVP (upload → separate → play → download)
- **MVP focus**: Task lifecycle state transitions, file validation, error handling

## Spec Patches

None — delta spec already covers the identified requirements adequately.
