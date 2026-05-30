from django.db import models
from django.utils.translation import gettext_lazy as _


class DocSection(models.Model):
    name = models.CharField(_("name"), max_length=100)
    language = models.CharField(_("language"), max_length=10, blank=True, default="")
    order = models.IntegerField(_("order"), default=999)
    collapsed = models.BooleanField(_("collapsed"), default=False)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("name", "language")
        verbose_name = _("Section")
        verbose_name_plural = _("Sections")

    def __str__(self):
        return self.name


class DocPage(models.Model):
    slug = models.SlugField(_("slug"))
    language = models.CharField(
        _("language"),
        max_length=10,
        default="",
        blank=True,
        help_text=_("Language code of the document (e.g., 'ru'). Empty = default"),
    )
    title = models.CharField(_("title"), max_length=200)
    order = models.IntegerField(_("order"), default=999)
    content_markdown = models.TextField(_("content"))
    section = models.CharField(
        _("section"),
        max_length=100,
        blank=True,
        default="",
        help_text=_("Section name to display for this page (in same language as document)"),
    )
    source_path = models.CharField(
        _("source path"),
        max_length=500,
        blank=True,
        default="",
        help_text=_("Absolute path to the source markdown file. Set by update_docs; blank for admin-created pages."),
    )
    anchors = models.JSONField(
        _("anchors"),
        default=list,
        blank=True,
        help_text=_("Extracted h2/h3 headings. Populated by update_docs."),
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = [("slug", "language")]
        verbose_name = _("Page")
        verbose_name_plural = _("Contents")

    def __str__(self):
        return f"{self.title} ({self.language or 'default'})"


class DocSearch(DocPage):
    class Meta:
        proxy = True
        verbose_name = _("Search")
        verbose_name_plural = _("Search")
