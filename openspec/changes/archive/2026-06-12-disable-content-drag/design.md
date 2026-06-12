# Design: Disable Main Content Drag

## Problem

Browser-native touch/scroll behavior allows the main content area to be dragged beyond its bounds, causing layout shifts.

## Solution

Add CSS containment properties to `.main-content` in `App.vue`:

1. `touch-action: pan-y` — Restrict touch interactions to vertical panning only, preventing horizontal drag
2. `overscroll-behavior: contain` — Prevent scroll chaining to parent elements, containing scroll within the main content

## Files Modified

- `frontend/src/App.vue` — Add CSS properties to `.main-content` class
