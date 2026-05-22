"""
ophix-manage purge_docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Remove documentation pages from the database.

Three modes:

  Specific slugs:
    ophix-manage purge_docs my-slug another-slug

  All pages (for this language):
    ophix-manage purge_docs --all

  Pages whose source files have been removed from disk:
    ophix-manage purge_docs --deleted

  Preview without deleting:
    ophix-manage purge_docs --all --dry-run
    ophix-manage purge_docs --deleted --dry-run

Notes
-----
Sections are not automatically removed when their last page is deleted.
To clean up empty sections, re-run update_docs — it will rebuild section
ordering from whatever pages remain. Empty sections do no harm in the admin.
"""

from django.core.management.base import BaseCommand, CommandError
from ophix_docs.models import DocPage


class Command(BaseCommand):
    help = "Remove documentation pages by slug, by --all, or by --deleted (source file gone)."

    def add_arguments(self, parser):
        parser.add_argument(
            'slugs',
            nargs='*',
            metavar='slug',
            help="One or more page slugs to delete.",
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help="Delete all pages (for the selected language).",
        )
        parser.add_argument(
            '--deleted',
            action='store_true',
            help=(
                "Delete pages whose source_path was set by update_docs "
                "but the file no longer exists on disk."
            ),
        )
        parser.add_argument(
            '--language',
            default="",
            metavar='CODE',
            help="Restrict to a specific language code. Defaults to the default language ('').",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show what would be deleted without deleting anything.",
        )

    def handle(self, *args, **options):
        slugs = options['slugs']
        purge_all = options['all']
        purge_deleted = options['deleted']
        language = options['language']
        dry_run = options['dry_run']

        # Validate: exactly one mode must be selected
        modes = sum([bool(slugs), purge_all, purge_deleted])
        if modes == 0:
            raise CommandError(
                "Specify slug(s), --all, or --deleted. "
                "Run with --help for usage."
            )
        if modes > 1:
            raise CommandError("--all and --deleted cannot be combined with each other or with slug arguments.")

        if purge_all:
            self._purge_all(language, dry_run)
        elif purge_deleted:
            self._purge_deleted(language, dry_run)
        else:
            self._purge_slugs(slugs, language, dry_run)

    # ------------------------------------------------------------------
    # Mode implementations
    # ------------------------------------------------------------------

    def _purge_all(self, language: str, dry_run: bool):
        qs = DocPage.objects.filter(language=language)
        count = qs.count()
        lang_label = f"language '{language}'" if language else "default language"

        if count == 0:
            self.stdout.write(f"No pages found for {lang_label}.")
            return

        if dry_run:
            self.stdout.write(
                f"Dry run: {count} page(s) for {lang_label} would be deleted:"
            )
            for page in qs.order_by('section', 'order'):
                self.stdout.write(f"  {page.slug}  ({page.title})")
            return

        qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {count} page(s) for {lang_label}."
        ))

    def _purge_deleted(self, language: str, dry_run: bool):
        from pathlib import Path

        # Only consider pages that were imported from disk (source_path is set)
        qs = DocPage.objects.filter(language=language).exclude(source_path="")
        candidates = []
        for page in qs:
            if not Path(page.source_path).exists():
                candidates.append(page)

        if not candidates:
            self.stdout.write("No pages found with missing source files.")
            return

        if dry_run:
            self.stdout.write(
                f"Dry run: {len(candidates)} page(s) with missing source files would be deleted:"
            )
            for page in candidates:
                self.stdout.write(f"  {page.slug}  ({page.title})")
                self.stdout.write(f"    source: {page.source_path}")
            return

        for page in candidates:
            self.stdout.write(
                f"Deleting '{page.slug}' — source file gone: {page.source_path}"
            )
            page.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Deleted {len(candidates)} page(s) with missing source files."
        ))

    def _purge_slugs(self, slugs: list[str], language: str, dry_run: bool):
        found = []
        missing = []
        for slug in slugs:
            try:
                page = DocPage.objects.get(slug=slug, language=language)
                found.append(page)
            except DocPage.DoesNotExist:
                missing.append(slug)

        if missing:
            lang_label = f" (language '{language}')" if language else ""
            for slug in missing:
                self.stdout.write(self.style.WARNING(
                    f"Page not found: '{slug}'{lang_label}"
                ))

        if not found:
            self.stdout.write("No matching pages to delete.")
            return

        if dry_run:
            self.stdout.write(f"Dry run: {len(found)} page(s) would be deleted:")
            for page in found:
                self.stdout.write(f"  {page.slug}  ({page.title})")
            return

        for page in found:
            page.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted '{page.slug}' ({page.title})"))
