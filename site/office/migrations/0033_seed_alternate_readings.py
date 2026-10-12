from django.db import migrations
from office.migrations._alternate_readings_0033 import forward, backward


class Migration(migrations.Migration):
    dependencies = [("office", "0032_alternate_reading")]
    operations = [migrations.RunPython(forward, backward)]
