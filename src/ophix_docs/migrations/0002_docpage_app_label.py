from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ophix_docs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='docpage',
            name='app_label',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Python module name of the app that owns this page (e.g. ophix_core). Empty for primary docs path.',
                max_length=100,
                verbose_name='app label',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='docpage',
            unique_together={('app_label', 'slug', 'language')},
        ),
    ]
