# Ophix Docs Release Notes

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
