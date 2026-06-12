# Tasks: AI Audio Separator

## Phase 1: Project Setup

### Task 1.1: Initialize Django Project
- [x] Create Django project with `django-admin startproject`
- [x] Create `separator` app
- [x] Configure settings (database, media paths, CORS, installed apps)
- [x] Add DRF to INSTALLED_APPS
- [x] Verify Django runs with `python manage.py runserver`

### Task 1.2: Initialize Vue 3 Frontend
- [x] Create Vue 3 project with Vite + TypeScript
- [x] Install dependencies (axios, wavesurfer.js, element-plus)
- [x] Configure Vite proxy to Django backend
- [x] Set up project structure (views, components, composables, api)
- [x] Verify dev server runs

### Task 1.3: Database Models
- [x] Create Task model with UUID primary key, status, mode, file fields
- [x] Run migrations
- [x] Register model in Django Admin
- [x] Verify Admin shows Task list

## Phase 2: Backend API

### Task 2.1: Task API Endpoints
- [x] Create TaskSerializer (DRF)
- [x] Implement POST /api/tasks/ (create task with file upload)
- [x] Implement GET /api/tasks/{id}/ (task status)
- [x] Implement GET /api/tasks/{id}/stems/ (list stems)
- [x] Implement GET /api/tasks/{id}/stems/{name}/ (download stem)
- [x] Implement GET /api/tasks/{id}/stems/{name}/stream/ (stream for playback)
- [x] Add file validation (format, size)
- [x] Add CORS headers for frontend

### Task 2.2: File Storage Configuration
- [x] Configure MEDIA_ROOT and MEDIA_URL
- [x] Create upload/stem directory structure
- [x] Implement file save logic in task creation
- [x] Configure static file serving for development

### Task 2.3: Django Admin Configuration
- [x] Customize TaskAdmin with list_display, list_filter, search_fields
- [x] Add readonly_fields for completed_at, error_message
- [x] Test Admin CRUD operations

## Phase 3: AI Worker

### Task 3.1: Spleeter Integration
- [x] Install spleeter package
- [x] Create `separate_audio` function (calls spleeter CLI/API)
- [x] Handle 2-stem and 4-stem modes
- [x] Implement error handling for Spleeter failures
- [x] Test standalone separation with sample audio

### Task 3.2: Worker Process
- [x] Create worker management command (`python manage.py run_worker`)
- [x] Implement task polling loop (every 2 seconds)
- [x] Process PENDING tasks: set PROCESSING, run Spleeter, save stems
- [x] Set COMPLETED on success, FAILED on error
- [x] Handle Worker interruption gracefully (SIGTERM)
- [x] Log task processing events

### Task 3.3: Cleanup Command
- [x] Create `cleanup_old_tasks` management command
- [x] Delete tasks older than 24 hours
- [x] Delete associated files (uploads + stems)
- [x] Log cleanup actions

## Phase 4: Frontend

### Task 4.1: API Client
- [x] Create axios/fetch client with base URL
- [x] Implement `createTask(formData)` - upload file + mode
- [x] Implement `getTaskStatus(taskId)` - poll status
- [x] Implement `getStems(taskId)` - list stems
- [x] Implement stem download/stream URLs

### Task 4.2: File Upload Component
- [x] Create FileUploader.vue with drag-and-drop
- [x] Add file format validation (client-side)
- [x] Add file size validation (client-side)
- [x] Show upload progress
- [x] Emit task-created event with task_id

### Task 4.3: Mode Selector
- [x] Create ModeSelector.vue (2-stem / 4-stem toggle)
- [x] Default to 2-stem mode
- [x] Emit mode-change event

### Task 4.4: Task Progress Component
- [x] Create TaskProgress.vue
- [x] Implement polling (every 3 seconds) via useTask composable
- [x] Show progress bar / spinner
- [x] Show status text ("Processing...", "Completed", "Failed: {error}")
- [x] Auto-stop polling on COMPLETED/FAILED

### Task 4.5: Stem Player Component
- [x] Create StemPlayer.vue with wavesurfer.js
- [x] Load audio from stream URL
- [x] Play/pause/seek controls
- [x] Waveform visualization
- [x] Display stem name and duration
- [x] Download button per stem

### Task 4.6: Main Views
- [x] Create HomeView.vue (upload + mode selector)
- [x] Create ResultView.vue (progress + stem players)
- [x] Implement routing (vue-router)
- [x] Add "Download All" button (ZIP of all stems)

## Phase 5: Integration & Polish

### Task 5.1: End-to-End Testing
- [x] Upload MP3 → 2-stem separation → download vocals
- [x] Upload WAV → 4-stem separation → play each stem
- [x] Upload invalid file → show error message
- [x] Upload file > 20MB → show error message
- [x] Test task failure handling (corrupt audio)

### Task 5.2: Error Handling Polish
- [x] Frontend: user-friendly error messages (not raw exceptions)
- [x] Frontend: network error handling (offline, timeout)
- [x] Backend: proper HTTP status codes (400, 404, 413, 500)
- [x] Backend: error logging for debugging

### Task 5.3: Performance & Cleanup
- [x] Configure cleanup cron job
- [x] Test file cleanup on task deletion
- [x] Verify no memory leaks in Worker polling loop
- [x] Test concurrent task handling

### Task 5.4: Documentation
- [x] README.md with setup instructions
- [x] API documentation (auto-generated via DRF)
- [x] Deployment notes (systemd service, nginx config)
