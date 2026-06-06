from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ophix_docs", "0008_alter_docsection_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="docpage",
            name="source_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Absolute path to the source markdown file. Set by update_docs; blank for admin-created pages.",
                max_length=500,
                verbose_name="source path",
            ),
        ),
    ]
