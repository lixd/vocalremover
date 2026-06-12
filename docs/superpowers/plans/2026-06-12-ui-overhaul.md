---
change: ui-overhaul
design-doc: docs/superpowers/specs/2026-06-12-ui-overhaul-design.md
base-ref: 15a525ff9b1a2878c76d283a1b181012e1b497d5
archived-with: 2026-06-12-ui-overhaul
---

# Implementation Plan: UI Overhaul

## Task 1: Create global CSS variables and import font
- Create `frontend/src/styles/variables.css` with all design tokens
- Add Google Fonts link for Source Sans Pro in `index.html`
- Import `variables.css` in `main.ts`

## Task 2: Restructure App.vue layout and sidebar
- Replace 220px sidebar with 80px fixed sidebar
- Add SVG icons for each nav item (人声分离, 剪辑器, 合并器, BPM/调性查询)
- Add help link at bottom
- Update flex layout: sidebar fixed + main content with margin-left

## Task 3: Update global color scheme across all views
- Replace hardcoded colors in HomeView, CutterView, MergerView, BpmKeyView, ResultView
- Replace `#00e676` (green accent) with new accent color
- Replace `#1a1a2e` (card bg) with new bg color
- Update font-family references

## Task 4: Restyle HomeView with vocalremover.org text and layout
- Update H1/H3/H2 headings with Chinese copy from reference
- Restyle upload button to pill shape (border-radius: 32px)
- Add description paragraph below upload area

## Task 5: Update component styles (FileUploader, ModeSelector, StemPlayer, etc.)
- Update colors to use CSS variables
- Adjust WaveSurfer waveform colors for new theme
- Update ElMessage styles if needed

## Task 6: Build and verify
- Run `npm run build` in frontend/
- Verify all pages render correctly
- Commit final changes
