import yaml
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from ophix_docs.models import DocPage, DocSection

DEFAULT_LANGUAGE = getattr(settings, "LANGUAGE_CODE", "en")[:2]

class Command(BaseCommand):
    help = "Export Markdown docs and sections.yaml from database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            required=True,
            help="Directory to write exported Markdown and sections.yaml"
        )
        parser.add_argument(
            '--language',
            default=DEFAULT_LANGUAGE,
            help="Language code to export"
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        language = options['language']

        # Export sections.yaml
        sections = DocSection.objects.filter(language=language).order_by('order')
        sections_list = [{'name': s.name, 'collapsed': s.collapsed} for s in sections]
        sections_yaml = {'sections': sections_list}
        sections_file = output_dir / "sections.yaml"
        with sections_file.open('w', encoding='utf-8') as f:
            yaml.safe_dump(sections_yaml, f, sort_keys=False, allow_unicode=True)
        self.stdout.write(f"Exported {len(sections_list)} sections to {sections_file}")

        # Export pages
        pages = DocPage.objects.filter(language=language).order_by('order')
        for page in pages:
            md_file = output_dir / f"{page.slug}.md"
            front_matter = {
                'title': page.title,
                'slug': page.slug,
                'order': page.order,
                'section': page.section
            }
            content = f"---\n{yaml.safe_dump(front_matter, allow_unicode=True)}---\n\n{page.content_markdown}"
            md_file.write_text(content, encoding='utf-8')
            self.stdout.write(f"Exported page '{page.title}' -> {md_file}")

        self.stdout.write(self.style.SUCCESS(f"Export complete for language '{language}'"))
