from django.db import migrations


def forwards(apps, schema_editor):
    Dataset = apps.get_model("catalog", "Dataset")
    Dataset.objects.get_or_create(
        code="DEFAULT",
        defaults={"name": "Default dataset"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_indicator_dataset"),
    ]
    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
