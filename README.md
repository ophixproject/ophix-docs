# ophix-docs

**Documentation that lives where you actually need it** — searchable, in-admin docs for every [Ophix](https://ophix.io) server.

Nobody wants to tab away from the admin panel to some separate wiki or GitHub page just to remember how a feature works — and that external doc is never quite sure which version you're actually running anyway. Every installed Ophix package ships its own docs pages; `ophix-docs` makes them available right alongside the data they describe, always matching whatever's actually installed.

---

## Installation

```bash
pip install ophix-docs
```

---

## How it works

Each Ophix package that ships documentation contains a `docs/` directory with:

- One or more `.md` files with YAML front matter (`title`, `slug`, `order`, `section`)
- A `sections.yaml` file declaring the section names used by those pages

Documentation is **not loaded automatically on install** — it must be imported into the
database with `update_docs`. If you used `run_install` to deploy your server,
this was done for you. After upgrading packages, re-run the command to pick up any
new or updated pages.

---

## Loading documentation

### Automatic — via `run_install`

If `ophix-docs` is installed when you run `ophix-manage run_install`, documentation
is discovered and loaded automatically for all installed packages that ship docs.
No further action is needed for a fresh install.

### Manual — after upgrades or adding packages

Discover which installed packages have docs:

```bash
ophix-manage list_docs_sources
```

Then load them. Use the Python module names (underscores, not hyphens), not pip
package names. Include all relevant modules for your server type:

**Credential server:**

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_creds,ophix_docs
```

**Configuration server:**

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_confs,ophix_docs
```

**Certificate server:**

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_certs,ophix_docs
```

**Certificate server with in-admin CA:**

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_certs,ophix_certs_ca,ophix_docs
```

**Zone server:**

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_zones,ophix_docs
```

The command is idempotent — safe to re-run at any time. It only creates and updates;
it never deletes pages.

---

## Management commands

### `list_docs_sources`

List all installed apps that contain valid Ophix docs (a `docs/` directory with
`.md` files and a `sections.yaml`).

```bash
ophix-manage list_docs_sources
```

Use `--json` for machine-readable output:

```bash
ophix-manage list_docs_sources --json
```

This is the recommended starting point after installing or upgrading packages — run
it to confirm which app names to pass to `--include-app-docs`.

---

### `update_docs`

Import and update documentation pages from installed app docs directories.
Creates new pages and updates existing ones. Never deletes.

```bash
ophix-manage update_docs --include-app-docs <comma-separated module names>
```

**Options:**

| Option | Description |
| --- | --- |
| `--include-app-docs <apps>` | Comma-separated list of app module names to import docs from |
| `--path <dir>` | Additional docs directory to import (defaults to `BASE_DIR/docs` if it exists) |
| `--language <code>` | Language code for translated docs — omit for default language |

---

### `purge_docs`

Remove documentation pages from the database.

```bash
# Remove specific pages by slug
ophix-manage purge_docs my-slug another-slug

# Remove all pages for the default language
ophix-manage purge_docs --all

# Remove pages whose source files no longer exist on disk
ophix-manage purge_docs --deleted

# Preview without deleting
ophix-manage purge_docs --all --dry-run
ophix-manage purge_docs --deleted --dry-run
```

**Options:**

| Option | Description |
| --- | --- |
| `--all` | Delete all pages for the selected language |
| `--deleted` | Delete pages whose source file has been removed from disk |
| `--language <code>` | Restrict to a specific language (defaults to default language) |
| `--dry-run` | Preview what would be deleted without deleting anything |

---

### `export_docs`

Export documentation pages from the database back to markdown files. Useful for
backing up custom docs or extracting pages for translation.

```bash
ophix-manage export_docs --output-dir /path/to/export/
```

**Options:**

| Option | Description |
| --- | --- |
| `--output-dir <dir>` | Directory to write exported `.md` files and `sections.yaml` (required) |
| `--language <code>` | Language to export (defaults to the server's `LANGUAGE_CODE`) |

---

## Language packs

Translated documentation ships as separate pip packages
(`ophix-lang-fr-creds`, `ophix-lang-fr-confs`, etc.). Install the pack and import
with `--language`:

```bash
pip install ophix-lang-fr-creds
ophix-manage update_docs --include-app-docs ophix_lang_fr_creds --language fr
```

---

## Writing custom docs

Any markdown file placed in a `docs/` directory of an installed Django app can be
imported by `update_docs`. Each file requires YAML front matter:

```yaml
---
title: My Page Title
slug: my-page-slug
order: 10
section: My Section
---

Page content here...
```

The `sections.yaml` in the same directory must declare any sections used:

```yaml
sections:
  - name: My Section
    collapsed: false
```
