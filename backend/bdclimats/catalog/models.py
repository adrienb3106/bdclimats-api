from django.db import models

class Indicator(models.Model):
    code =  models.CharField(max_length=64, unique=True, default="default_name")
    name = models.CharField(max_length=64)
    unit = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name} — {self.code}"



class ComputationRule(models.Model):

    class Operation(models.TextChoices):
        AVG = 'avg', 'Average'
        MIN = 'min', 'Minimum'
        MAX = 'max', 'Maximum'
        SUM = 'sum', 'Sum'
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['indicator', 'version'],
                name="uniq_rule_indicator_version",
            ),
        ]

    indicator = models.ForeignKey("Indicator", on_delete=models.CASCADE)
    version = models.PositiveIntegerField()
    operation = models.CharField(max_length=16, choices=Operation.choices, default=Operation.AVG)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.indicator.code} {self.version}"