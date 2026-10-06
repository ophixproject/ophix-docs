# Ophix Docs Release Notes

## Unreleased

- Added opt-in `{{ server_url }}` token substitution to the DocPage change view and to the
  search results snippet/match-context logic (`DocSearchAdmin`), so a search preview shows
  the interpolated value rather than the literal token. Markdown content with no tokens in
  it renders exactly as before — this lands the mechanism only; no shipped doc content uses
  the token yet. Intended for self-referential operational examples (e.g.
  `cred-client quickstart {{ server_url }} my-client-name`), not for passages describing a
  different or not-yet-existing server (install instructions should stay generic).

## 2026.10.04.01

- Reworked `README.md`'s opening with a hook-first pitch — docs that live where you actually
  need them, right alongside the data they describe — as part of the 16-package
  taskserver-release-wave README overhaul.

## 2026.09.26.02

- i18n regression check: the `"General"` fallback section label shown in the admin Table of Contents when a page has no `section` set was unwrapped. Wrapped in `gettext_lazy`.

## 2026.09.26.01

- Verified real compatibility under Python 3.14 (not just added the classifier) as part of the taskserver-release-wave compatibility sweep, and added `Programming Language :: Python :: 3.14` to the package classifiers.

## 2026.08.30.01

- Table of Contents (docpage changelist): removed the `font-size` overrides on
  `.doc-anchor-link` (0.875em) and `.doc-anchor-link.level-3` (0.83em) so page titles
  and every level of anchor sub-item render at the same, standard body font size.
  Indentation and opacity are still used to convey nesting depth.

## 2026.05.30.09

- Search snippet stripping now also handles markdown tables: separator rows (`| --- |`)
  are removed entirely and content rows have their pipe delimiters stripped, leaving
  just the cell values as readable text.

## 2026.05.30.08

- Search snippets are now stripped of markdown syntax before display — headings, bold,
  italic, code fences, links, list markers, and blockquotes are all removed, leaving
  clean readable plain text. The monospace/pre-wrap styling on snippets is removed accordingly.

## 2026.05.30.07

- Search V2: results now link to the specific section (h2/h3) within a page that
  contains the match, with `?q=` forwarded so the page highlights all occurrences.
- Doc page view: when opened via a search result link, all occurrences of the search
  term are highlighted with `<mark>` (skipping code blocks). Scrolls to the first
  match automatically if no anchor is present in the URL.

## 2026.05.30.06

- Page name hover in docs index now uses the generic link hover colour, consistent
  with anchor sub-link colours.

## 2026.05.30.05

- Fix section collapsed/expanded state not persisting: switched from sessionStorage
  to localStorage, and fixed restore logic to correctly re-expand sections that were
  collapsed by default but expanded by the user.

## 2026.05.30.04

- Renamed "Pages" to "Contents" in sidebar; docs index heading changed to "Table
  of Contents".
- Page links in docs index are now collapsible; h2/h3 anchors appear as sub-links
  under each page. Anchors extracted and stored by update_docs (run after upgrade).
- Added "Search" entry in sidebar: full-text search across page titles and content.
- Dark mode: h1/h2 headings in doc pages now lighten with the same per-theme accent
  lightness setting as links.
- "Back to Index" renamed to "Back to Contents".

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
