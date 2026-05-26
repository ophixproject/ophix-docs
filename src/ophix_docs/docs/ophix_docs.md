---
title: Documentation System
slug: ophix-docs
order: 500
section: Extensions
---

`ophix-docs` is an optional plugin that adds inline documentation to the Django admin. Each installed app can ship its own markdown docs; a management command imports them all into the database where they are rendered in the admin UI with syntax highlighting.

---

## Installation

```bash
pip install ophix-docs
ophix-manage migrate
```

Once installed and migrated, a **Documentation** section appears in the admin.

---

## Importing documentation

The `update_docs` command imports markdown files into the database:

```bash
ophix-manage update_docs
```

By default it reads from the path set in `OPHIX_DOCS_PATH` (defaults to a `docs/` folder next to the project root). To also import docs shipped with installed apps:

```bash
# On a credential server:
ophix-manage update_docs \
  --include-app-docs ophix.core,ophix_creds,ophix_docs

# On a configuration server:
ophix-manage update_docs \
  --include-app-docs ophix.core,ophix_confs,ophix_docs
```

Each app listed must be installed and must contain a `docs/` directory inside its package folder. If the directory is not found, a warning is printed and that app is skipped. The flag does **not** auto-discover installed apps — you must name them explicitly.

`update_docs` is **additive only** — it creates and updates pages, but never deletes them. You can safely run it on different sources independently without affecting pages imported from other sources. To remove pages, use `purge_docs`.

---

## Removing documentation

The `purge_docs` command removes pages from the database. It has three modes:

### Delete specific pages by slug

```bash
ophix-manage purge_docs my-page-slug another-slug
```

### Delete all pages

```bash
ophix-manage purge_docs --all
```

This removes all pages for the default language. Use `--language` to target a specific translation.

### Delete pages whose source files have been removed

```bash
ophix-manage purge_docs --deleted
```

This scans all pages that were imported from disk and removes those whose source markdown file no longer exists. Useful after renaming or removing a docs file — run this instead of re-importing everything.

### Preview before deleting

All three modes support `--dry-run`:

```bash
ophix-manage purge_docs --deleted --dry-run
ophix-manage purge_docs --all --dry-run
```

---

## Markdown file format

Each documentation page is a single `.md` file with a YAML front matter block:

```text
---
title: My Page Title
slug: my-page-slug
order: 10
section: My Section
---

## My First Section

Content goes here...
```

### Front matter fields

| Field | Required | Description |
| --- | --- | --- |
| `title` | Yes | Display name shown in the admin navigation |
| `slug` | Yes | Unique identifier — must be unique across all imported docs |
| `order` | Yes | Sort position within the section; also determines section order (the section with the lowest page order appears first) |
| `section` | Yes | Section name this page belongs to |

If front matter is missing, the command falls back to defaults derived from the filename, but explicit front matter is strongly recommended.

---

## Sections

Sections group related pages in the admin navigation. Each app that contributes docs should also include a `sections.yaml` file alongside its markdown files:

```yaml
sections:
  - name: My Section
    collapsed: false
  - name: Extensions
    collapsed: true
```

Sections from all apps are merged in the order the apps are passed to `--include-app-docs`. Duplicate section names are deduplicated — the first definition wins, so order matters.

Each app defines only the sections it needs. Multiple apps can contribute pages to the same section — they will be merged. Section order in the navigation is determined by the lowest page `order` value within each section: a section whose earliest page has `order: 1` will appear before a section whose earliest page has `order: 10`. The `sections.yaml` controls only the section name and its collapsed default — not its position. Each server runs exactly one domain plugin, so the app list reflects what is actually installed. For a credential server:

```bash
ophix-manage update_docs \
  --include-app-docs ophix.core,ophix_creds,ophix_docs
```

For a configuration server:

```bash
ophix-manage update_docs \
  --include-app-docs ophix.core,ophix_confs,ophix_docs
```

---

## Operator custom documentation

Operators can add their own documentation pages alongside the built-in app docs.

### Adding custom pages

Create a directory containing your markdown files and run the import with `--path`:

```bash
ophix-manage update_docs --path /home/ophix/docs --include-app-docs ophix.core,ophix_creds,ophix_docs
```

Both the custom path and the app docs are imported in the same run. Markdown files follow the same front matter format as built-in docs:

```text
---
title: My Custom Page
slug: my-custom-page
order: 100
section: Operations
---

## Content goes here
```

To create a new section, include a `sections.yaml` alongside your markdown files:

```yaml
sections:
  - name: Operations
    collapsed: false
```

Without a `sections.yaml` entry the section will still appear, but its collapsed state cannot be controlled.

Your custom pages will appear in the admin alongside the built-in docs.

### Persistent custom path

If you always import from the same custom directory, set `OPHIX_DOCS_PATH` in `.env` so the path is picked up automatically without `--path`:

```ini
OPHIX_DOCS_PATH=/home/ophix/docs
```

With this set, the plain `update_docs` command (no `--path`) will include your custom directory every time.

### Removing custom pages

Because `update_docs` never deletes, removing a file from disk does not automatically remove the page from the database. After removing or renaming a file, clean up with:

```bash
ophix-manage purge_docs --deleted
```

Or delete a specific page by slug:

```bash
ophix-manage purge_docs my-custom-page
```

---

## Exporting documentation

To export a page back to a markdown file:

```bash
ophix-manage export_docs my-page-slug --output ./docs/
```

This is useful if you have edited a page in the admin and want to capture the changes back to source.

---

## Listing doc sources

To see which apps have docs directories available:

```bash
ophix-manage list_docs_sources
```

---

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `OPHIX_DOCS_ENABLED` | `true` | Set to `false` to hide the Documentation section from the admin entirely |
| `OPHIX_DOCS_PATH` | `BASE_DIR/docs` | Path to the primary docs folder |
| `OPHIX_DOCS_APP_LABEL` | `Documentation` | Admin section label |
