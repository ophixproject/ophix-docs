from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ophix_docs", "0009_docpage_source_path_helptext"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="docpage",
            options={
                "ordering": ["order"],
                "verbose_name": "Page",
                "verbose_name_plural": "Contents",
            },
        ),
        migrations.AddField(
            model_name="docpage",
            name="anchors",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Extracted h2/h3 headings. Populated by update_docs.",
                verbose_name="anchors",
            ),
        ),
        migrations.CreateModel(
            name="DocSearch",
            fields=[],
            options={
                "verbose_name": "Search",
                "verbose_name_plural": "Search",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("ophix_docs.docpage",),
        ),
    ]
