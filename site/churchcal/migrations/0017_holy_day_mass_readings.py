from django.db import migrations
from churchcal.migrations._holy_day_mass_readings_0017 import forward, backward


class Migration(migrations.Migration):
    dependencies = [
        ("churchcal", "0016_commemoration_ai_generation_instructions"),
        ("office", "0033_seed_alternate_readings"),
    ]
    operations = [migrations.RunPython(forward, backward)]
