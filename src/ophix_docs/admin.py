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
            ).order_by("slug", "-priority")  # requested language first

            # Step 2: Deduplicate by slug, keep first (requested language preferred)
            pages_by_slug = {}
            for page in all_pages:
                if page.slug not in pages_by_slug:
                    pages_by_slug[page.slug] = page

            pages = list(pages_by_slug.values())

            # Step 3: Group by section name
            pages_by_section = {}
            for page in pages:
                pages_by_section.setdefault(page.section or "General", []).append(page)

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
            page = self.get_object(request, object_id)

            html = markdown.markdown(
                page.content_markdown,
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
                    page.snippet = self._get_snippet(page.content_markdown, query)
                    page.anchor, page.section_title = self._find_match_context(
                        page.content_markdown, query, page.anchors
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
