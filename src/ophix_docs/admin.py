import functools
import importlib
import logging
import re
from collections import OrderedDict

from django.conf import settings
from django.contrib import admin
from django.db.models import Case, When, Value, IntegerField
from django.template.response import TemplateResponse
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
import markdown

from .models import DocPage, DocSection, DocSearch

logger = logging.getLogger(__name__)


_DOC_TOKEN_RE = re.compile(r"\{\{\s*([\w-]+)\s*\}\}")


@functools.lru_cache(maxsize=1)
def _discover_plugin_doc_tokens():
    """
    {{ token }} values contributed by installed plugins via an optional
    get_doc_tokens() hook in their top-level package. Discovered the same
    way install_configure/get_revisions_targets are discovered — iterating
    entry_points(group="ophix.plugins") — deliberately holding no hardcoded
    catalog of domain packages here. A plugin simply not implementing the
    hook contributes nothing; no error. Cached for the life of the process
    (Django processes restart on deploy, so this doesn't need to react to a
    mid-process pip install).
    """
    from importlib.metadata import entry_points

    tokens = {}
    for ep in entry_points(group="ophix.plugins"):
        try:
            mod = importlib.import_module(ep.value)
        except ImportError:
            logger.warning("Could not import plugin module %r for doc token discovery", ep.value)
            continue
        hook = getattr(mod, "get_doc_tokens", None)
        if hook is None:
            continue  # optional hook — plugin simply doesn't contribute doc tokens
        try:
            contributed = hook() or {}
        except Exception:
            logger.exception("get_doc_tokens() raised in %s — skipping its tokens", ep.value)
            continue
        tokens.update(contributed)
    return tokens


def _interpolate_doc_tokens(content, request):
    """Replace {{ token }} placeholders with live values. Opt-in only — markdown
    with no tokens in it is returned unchanged. Any {{ }}-shaped pattern that
    doesn't match a known token (a typo, or an optional token whose
    contributing plugin isn't installed) renders as blank rather than
    literally — this is deliberate so an optional plugin-contributed token
    disappears cleanly when that plugin isn't present, at the cost of a
    genuine typo failing silently instead of showing broken {{ }} syntax.

    Built-in request-derived tokens are applied last so they always win over
    a same-named plugin-contributed token."""
    values = {
        **_discover_plugin_doc_tokens(),
        "server_url": request.build_absolute_uri("/").rstrip("/"),
    }
    return _DOC_TOKEN_RE.sub(lambda m: values.get(m.group(1), ""), content)


if getattr(settings, "SHOW_DOCS_MODEL", True):
    @admin.register(DocPage)
    class DocPageAdmin(admin.ModelAdmin):

        list_display = ("title",)
        ordering = ("order",)

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def get_urls(self):
            from django.urls import path
            urls = super().get_urls()
            custom = [
                path(
                    "crosslink/<str:app_label>/<slug:slug>/",
                    self.admin_site.admin_view(self.crosslink_redirect_view),
                    name="ophix_docs_docpage_crosslink",
                ),
            ]
            return custom + urls

        def crosslink_redirect_view(self, request, app_label, slug):
            # Stable cross-link target: (app_label, slug) never changes even
            # though the underlying DocPage's pk depends on import order and
            # can differ between servers. Only usable for docs guaranteed to
            # exist on the installing server — same-package docs, or docs
            # belonging to ophix.core (an unconditional dependency of every
            # domain) — since a missing target 404s with no fallback.
            from django.http import Http404
            from django.shortcuts import redirect
            from django.urls import reverse

            language = translation.get_language() or ""
            page = (
                DocPage.objects.filter(app_label=app_label, slug=slug, language=language).first()
                or DocPage.objects.filter(app_label=app_label, slug=slug, language="").first()
            )
            if page is None:
                raise Http404(f"No documentation page found for app_label={app_label!r} slug={slug!r}")
            return redirect(reverse("admin:ophix_docs_docpage_change", args=[page.pk]))

        # Documentation index
        def changelist_view(self, request, extra_context=None):
            # Determine requested language (fallback to default)
            language = translation.get_language() or ""

            # Step 1: Fetch all pages in either requested language or default
            # Annotate with priority so requested language comes first
            all_pages = DocPage.objects.filter(
                language__in=[language, ""]
            ).annotate(
                priority=Case(
                    When(language=language, then=Value(1)),
                    When(language="", then=Value(0)),
                    default=Value(-1),
                    output_field=IntegerField(),
                )
            ).order_by("app_label", "slug", "-priority")  # requested language first

            # Step 2: Deduplicate by (app_label, slug), keep first (requested language preferred)
            pages_by_key = {}
            for page in all_pages:
                key = (page.app_label, page.slug)
                if key not in pages_by_key:
                    pages_by_key[key] = page

            pages = list(pages_by_key.values())

            # Step 3: Group by section name
            pages_by_section = {}
            for page in pages:
                pages_by_section.setdefault(page.section or str(_("General")), []).append(page)

            # Step 4: Apply DocSection ordering
            ordered_sections = OrderedDict()
            for section in DocSection.objects.all():
                name = section.name
                if name in pages_by_section:
                    ordered_sections[name] = {
                        "collapsed": section.collapsed,
                        "pages": sorted(pages_by_section[name], key=lambda p: p.order),
                    }

            # Include any sections not defined in DocSection
            for name, section_pages in pages_by_section.items():
                if name not in ordered_sections:
                    ordered_sections[name] = {
                        "collapsed": False,
                        "pages": sorted(section_pages, key=lambda p: p.order),
                    }

            context = {
                **self.admin_site.each_context(request),
                "pages_by_section": ordered_sections,
                "title": _("Table of Contents"),
                "language": language,
            }

            return TemplateResponse(
                request,
                "admin/ophix_docs/docpage/change_list.html",
                context,
            )

        # Render markdown page
        def change_view(self, request, object_id, form_url="", extra_context=None):
            from django.http import Http404
            page = self.get_object(request, object_id)
            if page is None:
                raise Http404

            html = markdown.markdown(
                _interpolate_doc_tokens(page.content_markdown, request),
                extensions=["fenced_code", "tables", "toc"]
            )

            context = {
                **self.admin_site.each_context(request),
                "page": page,
                "rendered_markdown": mark_safe(html),
                "title": page.title,
                "search_query": request.GET.get("q", ""),
            }

            return TemplateResponse(
                request,
                "admin/ophix_docs/docpage/change_form.html",
                context,
            )

    @admin.register(DocSearch)
    class DocSearchAdmin(admin.ModelAdmin):

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def changelist_view(self, request, extra_context=None):
            query = request.GET.get("q", "").strip()
            results = []

            if query:
                from django.db.models import Q
                pages = DocPage.objects.filter(
                    Q(title__icontains=query) | Q(content_markdown__icontains=query),
                    language="",
                ).order_by("order")
                for page in pages:
                    content = _interpolate_doc_tokens(page.content_markdown, request)
                    page.snippet = self._get_snippet(content, query)
                    page.anchor, page.section_title = self._find_match_context(
                        content, query, page.anchors
                    )
                    results.append(page)

            context = {
                **self.admin_site.each_context(request),
                "title": _("Search Documentation"),
                "query": query,
                "results": results,
            }

            return TemplateResponse(
                request,
                "admin/ophix_docs/docsearch/change_list.html",
                context,
            )

        def _find_match_context(self, text, query, anchors):
            import re
            idx = text.lower().find(query.lower())
            if idx == -1:
                return None, None
            title_to_slug = {a["title"]: a["slug"] for a in (anchors or [])}
            heading_re = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
            last_heading = None
            for m in heading_re.finditer(text):
                if m.start() > idx:
                    break
                last_heading = m
            if not last_heading:
                return None, None
            title = last_heading.group(2).strip()
            slug = title_to_slug.get(title)
            return slug, title

        def _strip_markdown(self, text):
            import re
            # Fenced code blocks → remove content, keep nothing
            text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
            # Inline code → unwrap
            text = re.sub(r"`([^`]+)`", r"\1", text)
            # Headings
            text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
            # Bold / italic
            text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
            text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
            # Images → remove; links → keep text
            text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
            text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
            # Horizontal rules
            text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
            # List markers
            text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
            text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
            # Blockquotes
            text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
            # Table separator rows
            text = re.sub(r"^\|[\s|:-]+\|\s*$", "", text, flags=re.MULTILINE)
            # Table content rows → strip pipes, join cells
            text = re.sub(r"^\|(.+)\|$", lambda m: "  ".join(c.strip() for c in m.group(1).split("|")), text, flags=re.MULTILINE)
            # Collapse whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()

        def _get_snippet(self, text, query, context_chars=150):
            plain = self._strip_markdown(text)
            idx = plain.lower().find(query.lower())
            if idx == -1:
                return plain[:200].strip() + "…"
            start = max(0, idx - context_chars // 2)
            end = min(len(plain), idx + len(query) + context_chars // 2)
            snippet = plain[start:end].strip()
            if start > 0:
                snippet = "…" + snippet
            if end < len(plain):
                snippet = snippet + "…"
            return snippet
