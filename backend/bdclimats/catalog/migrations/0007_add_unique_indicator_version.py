from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_alter_computationrule_operation"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="computationrule",
            constraint=models.UniqueConstraint(
                fields=["indicator", "version"],
                name="uniq_rule_indicator_version",
            ),
        ),
    ]
