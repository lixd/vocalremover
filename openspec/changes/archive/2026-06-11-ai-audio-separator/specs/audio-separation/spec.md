# Audio Separation Capability Spec

## Overview

This specification defines the core audio separation capability, including file upload, task management, AI inference, stem delivery, and user interface.

## ADDED: Functional Requirements

### FR-1: Audio File Upload

**Requirement**: System accepts audio file uploads via POST /api/tasks/.

**Accepted formats**: MP3, WAV, FLAC, OGG, M4A
**Max file size**: 20MB

**Validation rules**:
- File extension must be in allowed list
- File size must be ≤ 20MB
- If validation fails: return 400 with specific error message

**Storage**: Uploaded file saved to `media/uploads/{task_id}/original{ext}`

### FR-2: Separation Modes

**Requirement**: Users select separation mode when creating a task.

**2-stem mode** (`spleeter:2stems`):
- Output: vocals.wav, accompaniment.wav

**4-stem mode** (`spleeter:4stems`):
- Output: vocals.wav, drums.wav, bass.wav, other.wav

### FR-3: Task Lifecycle

**Requirement**: Tasks progress through defined states.

```
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED
```

### FR-4: Task Status Polling

**Requirement**: Frontend polls task status every 3 seconds.

**Endpoint**: `GET /api/tasks/{task_id}/`

### FR-5: Stem Delivery

**Requirement**: Separated stems available for playback and download.

- `GET /api/tasks/{task_id}/stems/` — List stems
- `GET /api/tasks/{task_id}/stems/{stem_name}/` — Download stem
- `GET /api/tasks/{task_id}/stems/{stem_name}/stream/` — Stream stem (Range support)
- `GET /api/tasks/{task_id}/stems/download-all/` — Download all as ZIP

### FR-6: Frontend UI

**Requirement**: Vue 3 SPA with FileUploader, ModeSelector, TaskProgress, StemPlayer (wavesurfer.js), DownloadPanel.

### FR-7: Admin Dashboard

**Requirement**: Django Admin for task monitoring, filtering, search, manual deletion.

### FR-8: File Cleanup

**Requirement**: Tasks older than 24 hours auto-deleted via `cleanup_old_tasks` command.

## ADDED: Non-Functional Requirements

- Task creation: < 500ms
- Status polling: < 100ms
- Worker crash recovery: stuck PROCESSING tasks reset after 30 min
- Drag-and-drop upload support
- Modern browser compatibility
