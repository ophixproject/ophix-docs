from django.apps import AppConfig
from django.conf import settings


class OphixDocsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ophix_docs"

    @property
    def verbose_name(self):
        return getattr(
            settings,
            "OPHIX_DOCS_APP_LABEL",
            "Documentation"
        )
