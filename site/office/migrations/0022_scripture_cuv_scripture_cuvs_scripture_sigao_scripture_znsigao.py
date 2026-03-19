from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("office", "0021_add_commemoration_info_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="scripture",
            name="cuvs",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scripture",
            name="cuv",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scripture",
            name="sigao",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scripture",
            name="znsigao",
            field=models.TextField(blank=True, null=True),
        ),
    ]
