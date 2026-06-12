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
