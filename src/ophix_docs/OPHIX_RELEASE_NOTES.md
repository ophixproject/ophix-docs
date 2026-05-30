# Ophix Docs Release Notes

## 2026.05.30.03

- Docs index section headings and toggle buttons now lighten in dark mode using the
  same per-theme accent lightness setting as generic links.

## 2026.05.30.02

- Fix docs index bullets: replaced ul/li with div elements to prevent Django admin
  base CSS from applying list-style to page link rows.

## 2026.05.30.01

- Docs index restyled to match token policy visual quality: collapsible sections
  with header bar, page count, hover left-border accent, dark mode aware.
- Highlight.js theme now switches on Django admin dark mode toggle (data-theme
  attribute) rather than OS prefers-color-scheme media query.

## 2026.05.27.03

- Doc page headings (h1/h2) now use the theme module color; h3/h4 use the generic link color.

## 2026.05.27.02

- Docs section headings now use the theme module color to match arrows and bullets.

## 2026.05.27.01

- Docs tree arrows and bullet markers now use the theme module color
  (`--admin-interface-module-background-color`) instead of the browser default,
  so they match the active theme across all colour schemes.

## 2026.05.22.02

- Added migration 0009: `DocPage.source_path` help text updated to reference
  `update_docs` (was `ophix_docs_update`).

## 2026.05.22.01

- Management commands renamed for consistency with `ophix-manage` context:
  `ophix_docs_update` → `update_docs`, `ophix_docs_purge` → `purge_docs`,
  `ophix_docs_export` → `export_docs`, `ophix_docs_list_sources` → `list_docs_sources`.

## 2026.05.01.02

- Added `OPHIX_RELEASE_NOTES.md` for release notes delivery.
