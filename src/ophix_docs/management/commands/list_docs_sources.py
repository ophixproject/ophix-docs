from pathlib import Path
from django.core.management.base import BaseCommand
from django.apps import apps
import json

class Command(BaseCommand):
    help = "List all installed apps that contain valid Ophix Project docs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help="Output list as JSON (useful for scripts)"
        )

    def handle(self, *args, **options):
        found_apps = []

        for app_config in apps.get_app_configs():
            app_path = Path(app_config.path)
            docs_path = app_path / "docs"

            if not docs_path.is_dir():
                continue

            md_files = list(docs_path.glob("*.md"))
            sections_file = docs_path / "sections.yaml"

            if md_files and sections_file.is_file():
                found_apps.append(app_config.name)

        if options['json']:
            self.stdout.write(json.dumps(found_apps))
        else:
            if found_apps:
                self.stdout.write("Apps with Ophix Project docs:")
                for app_name in found_apps:
                    self.stdout.write(f"  - {app_name}")
            else:
                self.stdout.write("No apps with valid Ophix Project docs found.")
