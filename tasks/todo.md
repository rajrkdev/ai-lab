# Task: Fix Site Rendering and Theme Visibility

## Status
- [x] Update `_layouts/default.html` with correct structural IDs and classes for Slate theme <!-- id: 0 -->
- [x] Verify rendering (via code inspection/browser if possible) <!-- id: 1 -->

## Review
- Site currently renders dark text on a dark background because it lacks the structural IDs (`#header_wrap`, `#main_content_wrap`, etc.) that `jekyll-theme-slate` expects.
- The CSS uses these IDs to apply light backgrounds to content areas and light colors to header text.
