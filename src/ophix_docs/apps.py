from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OphixDocsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ophix_docs"
    verbose_name = _("Documentation")
