from django.db import models

class DocSection(models.Model):
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=10, blank=True, default="")  # '' for default
    order = models.IntegerField(default=999)
    collapsed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('name', 'language')  # same section can exist in multiple languages

    def __str__(self):
        return self.name



class DocPage(models.Model):
    """A single documentation page"""
    slug = models.SlugField()
    language = models.CharField(
        max_length=10,
        default="",  # empty string = default language
        blank=True,
        help_text="Language code of the document (e.g., 'ru'). Empty = default"
    )
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=999)
    content_markdown = models.TextField()
    section = models.CharField(max_length=100, blank=True, default="", help_text="Section name to display for this page (in same language as document)")
    source_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Absolute path to the source markdown file. Set by ophix_docs_update; blank for admin-created pages.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = [('slug', 'language')]
        verbose_name = "Page"
        verbose_name_plural = "Pages"

    def __str__(self):
        return f"{self.title} ({self.language or 'default'})"
