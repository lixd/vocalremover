# Proposal: UI Overhaul — Match vocalremover.org Design

## Problem

The current application has a custom dark theme UI with green accent colors, a 220px sidebar, and a different visual language from the reference site vocalremover.org. The user wants the UI to closely replicate the look and feel of vocalremover.org/zh/, including sidebar proportions, color scheme, typography, and content text.

## Goals

1. Redesign the sidebar to match vocalremover.org's narrow (~80px) icon+text layout
2. Make the main content area wider to fill the remaining space
3. Match the color scheme: dark background (#17171e), text (#eeeeee), accents
4. Copy the Chinese text content from vocalremover.org for headings and descriptions
5. Update navigation items to match the 8-tool menu structure
6. Match typography (Source Sans Pro font family)
7. Preserve all existing functionality (audio separation, cutter, merger, BPM/key finder)

## Non-Goals

- No new backend features or API changes
- No new tool pages (pitch shifter, voice recorder, karaoke) — only existing pages get restyled
- No mobile responsive redesign (desktop-first matching the reference site)
- No changes to audio processing logic

## Scope

- **In scope**: App.vue layout, sidebar component, all View pages (HomeView, CutterView, MergerView, BpmKeyView, ResultView), router configuration, global styles
- **Out of scope**: Backend Django code, API endpoints, audio processing utilities, component logic (FileUploader, ModeSelector, StemPlayer, etc.)

## Draft Acceptance Criteria

1. Sidebar width matches reference (~80px with icons and text labels)
2. Content area fills remaining width with appropriate padding
3. Color scheme matches reference site exactly
4. All visible Chinese text matches vocalremover.org/zh/
5. Navigation menu has all 8 tool items with SVG icons
6. Upload button has rounded pill shape
7. All existing functionality still works (file upload, separation, playback, download, cutter, merger, BPM/key)
