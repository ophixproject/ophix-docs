"""
ophix_docs.settings
~~~~~~~~~~~~~~~~~~~
Default settings contributed by the ophix-docs plugin.
Loaded non-destructively by ophix.settings.plugins.
"""

import os
from pathlib import Path

from ophix.settings.utils import get_bool_env

# Show or hide the Documentation section in admin.
SHOW_DOCS_MODEL = get_bool_env("SHOW_DOCS_MODEL", default=True)

# Primary docs folder (server-level docs, not app docs).
# Defaults to BASE_DIR/docs; overridden by OPHIX_DOCS_PATH in .env.
_docs_path_env = os.getenv("OPHIX_DOCS_PATH")
OPHIX_DOCS_PATH = Path(_docs_path_env).resolve() if _docs_path_env else None

# Admin section label.
OPHIX_DOCS_APP_LABEL = os.getenv("OPHIX_DOCS_APP_LABEL", "Documentation")
