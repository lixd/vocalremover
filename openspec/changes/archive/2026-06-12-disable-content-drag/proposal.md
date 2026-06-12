# Disable Main Content Drag

## Motivation

The right-side main content area can be dragged in all directions (up, down, left, right) via touch/mouse gestures. This causes layout shifts that obscure UI elements and disrupt the user experience. The sidebar is fixed-position, but the main content lacks proper touch containment, allowing browser-native pan/drag behavior to affect the layout.

## Goals

- Prevent the main content area from being dragged in any direction
- Maintain normal vertical scrolling within the main content
- No impact on sidebar navigation or other interactive elements

## Scope

- CSS-only change in `App.vue` (`.main-content` class)
- 1 file, ~2 lines of CSS additions
- No JavaScript changes needed
