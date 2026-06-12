---
comet_change: ui-overhaul
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-12-ui-overhaul
status: final
---

# UI Overhaul Design — Match vocalremover.org

## Overview

Redesign the VocalRemover frontend to closely replicate the look and feel of vocalremover.org, using a global CSS variable design system and layout restructure.

## Architecture

### Design System Layer

Create `frontend/src/styles/variables.css` with CSS custom properties:

```css
:root {
  --color-bg-primary: #17171e;
  --color-bg-secondary: #1e1e28;
  --color-text-primary: #eeeeee;
  --color-text-secondary: #d8d8e2;
  --color-border: #2a2a40;
  --color-accent: #eeeeee;
  --color-active-bg: #2a2a40;
  --color-active-text: #ffffff;
  --font-family: 'Source Sans Pro', -apple-system, sans-serif;
  --sidebar-width: 80px;
}
```

Imported once in `main.ts`, available to all components.

### Layout Architecture

```
App.vue (flex row, full viewport)
├── Sidebar (fixed, 80px wide, full height)
│   ├── Logo icon (top)
│   ├── Tool navigation (4 items, SVG icon + Chinese label)
│   └── Help link (bottom)
└── Main content (margin-left: 80px, flex: 1)
    └── <router-view /> (centered content)
```

### Sidebar Component

Embedded directly in `App.vue` (not extracted to separate component to minimize changes):

- Width: 80px, `position: fixed`, `height: 100vh`
- Background: `var(--color-bg-primary)`
- Navigation items: 4 tools with SVG icons + Chinese text
  - 人声分离 → `/` (HomeView)
  - 剪辑器 → `/cutter` (CutterView)
  - 合并器 → `/merger` (MergerView)
  - BPM/调性查询 → `/bpm-key` (BpmKeyView)
- Active item: background `var(--color-active-bg)`, text `var(--color-active-text)`
- Help link at bottom

### Content Area Pattern

Each View follows vocalremover.org's content hierarchy:
- H1 title → H3 subtitle → action area → H2 section heading → description

## Component Changes

### App.vue (Major)
- Replace 220px sidebar with 80px narrow sidebar
- Replace flex layout structure
- Add SVG icons for each nav item
- Update all color references to CSS variables
- Add help link at sidebar bottom

### styles/variables.css (New)
- All design tokens as CSS custom properties

### main.ts (Light)
- Import `styles/variables.css`

### HomeView.vue (Medium)
- Update heading text to match vocalremover.org Chinese copy
- Restyle upload button to pill shape (border-radius: 32px, transparent bg + border)
- Add description paragraph below upload area
- Update all colors to use CSS variables

### CutterView.vue, MergerView.vue, BpmKeyView.vue, ResultView.vue (Light)
- Replace hardcoded colors with CSS variable references
- Update font-family to use variable
- Adjust max-width constraints for wider content area

### FileUploader.vue, ModeSelector.vue (Light)
- Update colors to use CSS variables
- Restyle upload button for pill shape

### StemPlayer.vue (Light)
- Update WaveSurfer.js waveform color to match new theme
- Replace color references with CSS variables

## Data Flow

No changes to data flow. All existing Vue composables (useTask, useAudioPlayer) and API client remain unchanged.

## Error Handling

No changes to error handling logic. ElMessage notifications may need style overrides to match new color scheme.

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Element Plus style conflicts | Override with `!important` or scoped deep selectors |
| WaveSurfer.js color config | Pass theme colors via props to StemPlayer |
| Font not loaded | Add Google Fonts link in index.html or use system fallback |
