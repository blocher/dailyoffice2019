from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0027_seed_elevenlabs_voices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audiousage",
            name="request_path",
            field=models.TextField(blank=True, null=True),
        ),
    ]
