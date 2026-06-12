# Comet Design Handoff

- Change: ui-overhaul
- Phase: design
- Mode: compact
- Context hash: 50b7f3faba774d7478bf0b7b980d3a2eca15dba1481cbb159afc759bdb1e43be

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/ui-overhaul/proposal.md

- Source: openspec/changes/ui-overhaul/proposal.md
- Lines: 1-37
- SHA256: d56fb465abca7c01cd81bd491f0db341a1bb3433626cda9d4d63b9ec5a030f90

```md
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
```

## openspec/changes/ui-overhaul/design.md

- Source: openspec/changes/ui-overhaul/design.md
- Lines: 1-57
- SHA256: 6ff3ae5d8276c009f51f1e04035e96fd0d787894e7941d99d5e52d9ec9f0cc95

```md
# Design: UI Overhaul — Match vocalremover.org

## Architecture Decisions

### 1. Sidebar Layout
- **Decision**: Narrow sidebar (~80px) with vertical icon+text navigation
- **Rationale**: Matches vocalremover.org's compact tool navigation pattern
- **Structure**: Logo icon at top, 8 tool links (each with SVG icon + Chinese label), "帮助" link at bottom

### 2. Color System
- **Decision**: Adopt vocalremover.org's color palette globally
- **Colors**:
  - Body background: `#17171e`
  - Sidebar background: `#17171e` (same as body)
  - Text primary: `#eeeeee`
  - Text secondary: `#d8d8e2`
  - Active menu item: highlighted with lighter background
  - Button: transparent with border `#eeeeee`, border-radius `32px`
- **Migration**: Replace current green accent (#00e676) and card backgrounds (#1a1a2e)

### 3. Typography
- **Decision**: Switch to `Source Sans Pro, sans-serif`
- **Rationale**: Matches reference site's font family
- **Fallback**: System sans-serif stack

### 4. Content Area Layout
- **Decision**: Full-width content area with centered max-width container
- **Rationale**: Reference site uses wide content area with centered page content
- **Implementation**: Remove max-width constraints from views, use `flex: 1` on main area

### 5. Page Structure
- **Decision**: Each page follows vocalremover.org's content hierarchy
- **Pattern**: H1 title → H3 subtitle → action button → H2 section heading → description paragraph
- **Rationale**: Matches the reference site's information architecture

### 6. Navigation Items
- **Decision**: Add placeholder/label items for tools we don't implement
- **Items**: 去人声, 分离器, 变调器, 调BPM查询器, 剪辑器, 合并器, 录音, 卡拉OK
- **Mapping**: 去人声→HomeView, 分离器→HomeView(stems), 剪辑器→CutterView, 合并器→MergerView, 调BPM查询器→BpmKeyView
- **Non-functional items**: 变调器, 录音, 卡拉OK (link to home or show "coming soon")

## Data Flow

No data flow changes. All existing Vue composables (useTask, useAudioPlayer) and API client remain unchanged.

## Component Changes

| Component | Change Type | Description |
|-----------|------------|-------------|
| App.vue | Major | Sidebar + layout restructure |
| HomeView.vue | Medium | Style updates, text matching |
| CutterView.vue | Light | Style color/font updates |
| MergerView.vue | Light | Style color/font updates |
| BpmKeyView.vue | Light | Style color/font updates |
| ResultView.vue | Light | Style color/font updates |
| router/index.ts | Light | Add routes for new nav items |
| All components | Light | Scoped style updates for color/font |
```

## openspec/changes/ui-overhaul/tasks.md

- Source: openspec/changes/ui-overhaul/tasks.md
- Lines: 1-10
- SHA256: 97507381f48244083f75b349c8137237648337b084122df8ecd82b3356f7996a

```md
# Tasks: UI Overhaul

- [ ] 1. Restructure App.vue sidebar layout (80px width, icon+text nav, 8 tools, help link)
- [ ] 2. Update global color scheme (background, text, borders to match vocalremover.org)
- [ ] 3. Switch typography to Source Sans Pro font family
- [ ] 4. Restyle HomeView with vocalremover.org text content and layout (H1/H3/button/H2/paragraph)
- [ ] 5. Update router to add navigation entries for all 8 tools (placeholder routes for non-implemented tools)
- [ ] 6. Restyle CutterView, MergerView, BpmKeyView, ResultView with updated colors/fonts
- [ ] 7. Restyle upload button to pill shape (border-radius: 32px, transparent with border)
- [ ] 8. Build and verify all pages render correctly with new design
```

