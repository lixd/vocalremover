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
