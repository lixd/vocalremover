# Comet Design Handoff

- Change: ai-audio-separator
- Phase: design
- Mode: compact
- Context hash: 21413c3a8daf50ec3b467fa92b2f75c33ded238fabc4e52a50050c33c6f0e838

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/ai-audio-separator/proposal.md

- Source: openspec/changes/ai-audio-separator/proposal.md
- Lines: 1-64
- SHA256: a0d7220854530ecb9ee562b55fea69a7635eb26078ce04cdf400fa59b31289c1

```md
# AI Audio Separator

## Problem Background

Music producers, karaoke enthusiasts, and audio engineers frequently need to separate individual instruments or vocals from mixed audio tracks. Existing tools like vocalremover.org provide this capability through AI-powered source separation, but there's an opportunity to build an open, self-hosted alternative with a modern tech stack.

This project aims to create a free, publicly accessible web application that allows users to upload audio files and automatically separate them into individual stems (vocals, drums, bass, other) using AI models.

## Goals

1. Build a free, publicly accessible AI audio separation website
2. Support 2-stem (vocals/accompaniment) and 4-stem (vocals/drums/bass/other) separation
3. Provide real-time processing progress feedback
4. Enable independent playback and download of each separated stem
5. Support common audio formats (MP3, WAV, FLAC)
6. Include an Admin backend for monitoring tasks and system health

## Non-Goals

- **No user registration/login system** (MVP phase)
- **No paid/premium features** or commercial monetization
- **No mobile native app** (responsive web only)
- **No real-time/streaming processing** (async upload-then-process)
- **No audio editing features** (no pitch/tempo adjustment, no trimming)
- **No social features** (no sharing, no user profiles)

## Scope

### Included

- Audio file upload (MP3, WAV, FLAC, max 20MB / ~5 minutes)
- 2-stem separation (vocals + accompaniment)
- 4-stem separation (vocals + drums + bass + other)
- Per-stem audio playback with waveform visualization
- Per-stem download (individual + bundled ZIP)
- Processing progress polling (frontend polls task status)
- Django Admin panel for task monitoring
- Support for common audio formats

### Excluded

- User accounts and authentication
- Payment processing
- Audio editing (pitch, tempo, trimming)
- Mobile native apps
- Batch processing (multiple files at once)
- API key / developer API access

## Target Users

- Music producers needing isolated stems for remixing
- Karaoke enthusiasts creating instrumental tracks
- Audio engineers doing post-production
- Music students studying individual parts
- General users curious about separating audio

## Technical Approach

- **Frontend**: Vue 3 SPA
- **Backend**: Django (ORM + Admin + task management)
- **AI Engine**: Spleeter (CPU, upgradeable to Demucs/MDX-Net)
- **Database**: SQLite (MVP) -> PostgreSQL (scaling)
- **Storage**: Local filesystem
- **Architecture**: API Server + independent Worker process, communicating through database task queue
```

## openspec/changes/ai-audio-separator/design.md

- Source: openspec/changes/ai-audio-separator/design.md
- Lines: 1-202
- SHA256: ea00d15301500ade0ca3dcc32f60a5dd205156170ed85669e1d9d3130d307da7

[TRUNCATED]

```md
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
```

Full source: openspec/changes/ai-audio-separator/design.md

## openspec/changes/ai-audio-separator/tasks.md

- Source: openspec/changes/ai-audio-separator/tasks.md
- Lines: 1-137
- SHA256: 45c9cd6883115b6e16abc2a871e779debaf816795efa2051e2b3b02fba3526d3

[TRUNCATED]

```md
# Tasks: AI Audio Separator

## Phase 1: Project Setup

### Task 1.1: Initialize Django Project
- [ ] Create Django project with `django-admin startproject`
- [ ] Create `separator` app
- [ ] Configure settings (database, media paths, CORS, installed apps)
- [ ] Add DRF to INSTALLED_APPS
- [ ] Verify Django runs with `python manage.py runserver`

### Task 1.2: Initialize Vue 3 Frontend
- [ ] Create Vue 3 project with Vite + TypeScript
- [ ] Install dependencies (axios, wavesurfer.js, element-plus)
- [ ] Configure Vite proxy to Django backend
- [ ] Set up project structure (views, components, composables, api)
- [ ] Verify dev server runs

### Task 1.3: Database Models
- [ ] Create Task model with UUID primary key, status, mode, file fields
- [ ] Run migrations
- [ ] Register model in Django Admin
- [ ] Verify Admin shows Task list

## Phase 2: Backend API

### Task 2.1: Task API Endpoints
- [ ] Create TaskSerializer (DRF)
- [ ] Implement POST /api/tasks/ (create task with file upload)
- [ ] Implement GET /api/tasks/{id}/ (task status)
- [ ] Implement GET /api/tasks/{id}/stems/ (list stems)
- [ ] Implement GET /api/tasks/{id}/stems/{name}/ (download stem)
- [ ] Implement GET /api/tasks/{id}/stems/{name}/stream/ (stream for playback)
- [ ] Add file validation (format, size)
- [ ] Add CORS headers for frontend

### Task 2.2: File Storage Configuration
- [ ] Configure MEDIA_ROOT and MEDIA_URL
- [ ] Create upload/stem directory structure
- [ ] Implement file save logic in task creation
- [ ] Configure static file serving for development

### Task 2.3: Django Admin Configuration
- [ ] Customize TaskAdmin with list_display, list_filter, search_fields
- [ ] Add readonly_fields for completed_at, error_message
- [ ] Test Admin CRUD operations

## Phase 3: AI Worker

### Task 3.1: Spleeter Integration
- [ ] Install spleeter package
- [ ] Create `separate_audio` function (calls spleeter CLI/API)
- [ ] Handle 2-stem and 4-stem modes
- [ ] Implement error handling for Spleeter failures
- [ ] Test standalone separation with sample audio

### Task 3.2: Worker Process
- [ ] Create worker management command (`python manage.py run_worker`)
- [ ] Implement task polling loop (every 2 seconds)
- [ ] Process PENDING tasks: set PROCESSING, run Spleeter, save stems
- [ ] Set COMPLETED on success, FAILED on error
- [ ] Handle Worker interruption gracefully (SIGTERM)
- [ ] Log task processing events

### Task 3.3: Cleanup Command
- [ ] Create `cleanup_old_tasks` management command
- [ ] Delete tasks older than 24 hours
- [ ] Delete associated files (uploads + stems)
- [ ] Log cleanup actions

## Phase 4: Frontend

### Task 4.1: API Client
- [ ] Create axios/fetch client with base URL
- [ ] Implement `createTask(formData)` - upload file + mode
- [ ] Implement `getTaskStatus(taskId)` - poll status
- [ ] Implement `getStems(taskId)` - list stems
- [ ] Implement stem download/stream URLs

### Task 4.2: File Upload Component
```

Full source: openspec/changes/ai-audio-separator/tasks.md

## openspec/changes/ai-audio-separator/specs/audio-separation/spec.md

- Source: openspec/changes/ai-audio-separator/specs/audio-separation/spec.md
- Lines: 1-135
- SHA256: f78070dfd47badccc87ad29bfb97ceb4c1a66120a1a4df622a488b31acb3703e

[TRUNCATED]

```md
# Audio Separation Capability Spec

## Overview

This specification defines the core audio separation capability, including file upload, task management, AI inference, stem delivery, and user interface.

## Functional Requirements

### FR-1: Audio File Upload

**Requirement**: System accepts audio file uploads via POST /api/tasks/.

**Accepted formats**: MP3, WAV, FLAC, OGG, M4A
**Max file size**: 20MB
**Max duration**: ~5 minutes (enforced via file size limit)

**Validation rules**:
- File extension must be in allowed list
- File MIME type must match audio/*
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

**State transitions**:
- `PENDING`: Task created, waiting for Worker pickup
- `PROCESSING`: Worker picked up task, Spleeter running
- `COMPLETED`: All stems generated, ready for download
- `FAILED`: Error during processing, error_message populated

### FR-4: Task Status Polling

**Requirement**: Frontend polls task status every 3 seconds.

**Endpoint**: `GET /api/tasks/{task_id}/`

**Response includes**:
- `id`: Task UUID
- `status`: PENDING | PROCESSING | COMPLETED | FAILED
- `mode`: TWO_STEMS | FOUR_STEMS
- `original_filename`: Original file name
- `created_at`: ISO 8601 timestamp
- `completed_at`: ISO 8601 timestamp (null if not complete)
- `error_message`: Error details (null if no error)
- `stems`: Object mapping stem names to metadata

### FR-5: Stem Delivery

**Requirement**: Separated stems available for playback and download.

**List stems**: `GET /api/tasks/{task_id}/stems/`
- Returns array of stem objects with name, file_size, duration

**Download stem**: `GET /api/tasks/{task_id}/stems/{stem_name}/`
- Returns WAV file with appropriate Content-Disposition header

**Stream stem**: `GET /api/tasks/{task_id}/stems/{stem_name}/stream/`
- Returns audio/mpeg or audio/wav with Range header support for seeking

### FR-6: Frontend UI

```

Full source: openspec/changes/ai-audio-separator/specs/audio-separation/spec.md

