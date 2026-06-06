from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ophix_docs", "0006_rename_language_code_docpage_language_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="docpage",
            name="source_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Absolute path to the source markdown file. Set by ophix_docs_update; blank for admin-created pages.",
                max_length=500,
            ),
        ),
    ]
