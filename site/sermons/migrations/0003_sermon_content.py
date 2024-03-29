# Generated by Django 2.2.3 on 2019-08-08 01:41

from django.db import migrations
import djrichtextfield.models


class Migration(migrations.Migration):
    dependencies = [("sermons", "0002_auto_20190802_0229")]

    operations = [
        migrations.AddField(
            model_name="sermon",
            name="content",
            field=djrichtextfield.models.RichTextField(
                blank=True,
                help_text="The formatted content of the sermon",
                null=True,
                verbose_name="Formatted Content",
            ),
        )
    ]
