import re
import yaml
import markdown as md_module
from markdown.extensions.toc import TocExtension
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from ophix_docs.models import DocPage, DocSection
from importlib.util import find_spec


class Command(BaseCommand):
    help = (
        "Import and update markdown docs from the primary docs path and optional app docs.\n\n"
        "This command only creates and updates — it never deletes. "
        "To remove pages, use purge_docs."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            help=(
                "Path to the primary markdown docs folder. "
                "Defaults to OPHIX_DOCS_PATH setting, or BASE_DIR/docs if not set."
            ),
            default=getattr(settings, "OPHIX_DOCS_PATH", None) or (Path(settings.BASE_DIR) / "docs"),
        )
        parser.add_argument(
            '--include-app-docs',
            help="Comma-separated list of installed apps whose 'docs' directories should also be imported.",
            default="",
        )
        parser.add_argument(
            '--language',
            help=(
                "Language code for imported docs and sections. "
                "Leave unset for default-language docs. "
                "Only needed when importing a translation (e.g. --language ru)."
            ),
            default="",
        )

    def handle(self, *args, **options):
        language = options['language']

        # Gather all (docs_path, app_label) pairs: primary path has app_label=""
        include_apps = [a.strip() for a in options['include_app_docs'].split(',') if a.strip()]
        docs_path_apps = [(Path(options['path']), "")]

        for app_name in include_apps:
            spec = find_spec(app_name)
            if spec and spec.origin:
                app_docs = Path(spec.origin).parent / 'docs'
                if app_docs.exists():
                    self.stdout.write(f"Found docs for app '{app_name}' at {app_docs}")
                    docs_path_apps.append((app_docs, app_name))
                else:
                    self.stdout.write(self.style.WARNING(f"No 'docs' folder found for app '{app_name}'"))
            else:
                self.stdout.write(self.style.WARNING(f"App not found: {app_name}"))

        # Merge sections.yaml files — name and collapsed only.
        # First definition of a section name (for this language) wins for the collapsed flag.
        merged_sections = {}  # name -> collapsed
        for docs_path, _ in docs_path_apps:
            sections_file = docs_path / "sections.yaml"
            if sections_file.exists():
                with sections_file.open(encoding='utf-8') as f:
                    sections_yaml = yaml.safe_load(f) or {}
                for sec_def in sections_yaml.get('sections', []):
                    if isinstance(sec_def, dict):
                        name = sec_def.get('name')
                        collapsed = sec_def.get('collapsed', False)
                    else:
                        name = sec_def
                        collapsed = False
                    if name and name not in merged_sections:
                        merged_sections[name] = collapsed

        # Ensure all declared sections exist in the DB for this language.
        for name, collapsed in merged_sections.items():
            DocSection.objects.update_or_create(
                name=name,
                language=language,
                defaults={'collapsed': collapsed},
            )

        # Process all markdown files — upsert only, never delete.
        # Track the minimum page order per section to drive section ordering.
        section_min_order = {}  # section_name -> lowest page order within that section

        for docs_path, app_label in docs_path_apps:
            for md_file in sorted(docs_path.glob("*.md")):
                section_name, page_order = self.process_file(md_file, language, app_label)
                if section_name:
                    if section_name not in section_min_order or page_order < section_min_order[section_name]:
                        section_min_order[section_name] = page_order

        # Set each section's order to the minimum page order within it.
        for name, min_order in section_min_order.items():
            DocSection.objects.filter(name=name, language=language).update(order=min_order)

        self.stdout.write(self.style.SUCCESS(
            f"Documentation update complete for language '{language}'."
        ))

    def _extract_anchors(self, body):
        """Extract h2/h3 headings using Python-Markdown's toc extension for consistent slugs."""
        md = md_module.Markdown(extensions=[TocExtension()])
        md.convert(body)
        anchors = []

        def flatten(tokens):
            for token in tokens:
                if 2 <= token["level"] <= 3:
                    anchors.append({
                        "slug": token["id"],
                        "title": token["name"],
                        "level": token["level"],
                    })
                flatten(token.get("children", []))

        flatten(md.toc_tokens)
        return anchors

    def process_file(self, md_file: Path, language: str, app_label: str = ""):
        """
        Parse and upsert a single markdown file.
        Records the absolute source path on the page so purge_docs --deleted can find it.
        Returns (section_name, page_order).
        """
        text = md_file.read_text(encoding='utf-8').strip()

        front_matter_match = re.match(r'^---\s*(.*?)\s*---\s*(.*)', text, re.DOTALL)
        if front_matter_match:
            raw_yaml, body = front_matter_match.groups()
            try:
                fm = yaml.safe_load(raw_yaml) or {}
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"{md_file.name}: Failed to parse YAML front matter: {e}"
                ))
                fm = {}
        else:
            self.stdout.write(self.style.WARNING(
                f"{md_file.name}: Missing front matter, using defaults"
            ))
            body = text
            fm = {}
            first_line = body.splitlines()[0] if body.splitlines() else ""
            heading_match = re.match(r'^\s*#\s*(.+)', first_line)
            fm['title'] = (
                heading_match.group(1) if heading_match
                else md_file.stem.replace('_', ' ').replace('-', ' ').title()
            )
            fm['slug'] = md_file.stem.lower().replace('_', '-')
            fm['order'] = 0 if fm['slug'] == 'index' else 999
            fm['section'] = ""

        title = fm.get('title', md_file.stem.replace('_', ' ').replace('-', ' ').title())
        slug = fm.get('slug', md_file.stem.lower().replace('_', '-'))
        order = fm.get('order', 0 if slug == 'index' else 999)
        section = fm.get('section', '')
        source_path = str(md_file.resolve())

        self.stdout.write(
            f"Processing {md_file.name}: title='{title}', slug='{slug}', "
            f"order={order}, section='{section}', lang='{language}'"
        )

        anchors = self._extract_anchors(body)

        page, created = DocPage.objects.update_or_create(
            app_label=app_label,
            slug=slug,
            language=language,
            defaults={
                'title': title,
                'order': order,
                'content_markdown': body,
                'section': section,
                'source_path': source_path,
                'anchors': anchors,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  Created page '{title}'"))
        else:
            self.stdout.write(self.style.NOTICE(f"  Updated page '{title}'"))

        return section, order
