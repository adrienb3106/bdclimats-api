from django.core.exceptions import ValidationError
from django.db import models


class Dataset(models.Model):
    # Dataset = source/collection de donnees.
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    source_url = models.URLField(max_length=200)
    created_at = models.DateField(auto_now=False, auto_now_add=True)

    def clean(self):
        # Normalise le code (trim + upper) et refuse le vide.
        if self.code is not None:
            self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({"code": "Le code ne peut pas etre vide."})

    def save(self, *args, **kwargs):
        # Valide le modele avant sauvegarde.
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        # Libelle lisible (admin, logs, shell).
        return f"{self.name} - {self.code}"


class Indicator(models.Model):
    # Indicateur metier (definition, pas les valeurs).
    # Une ligne par indicateur (admin ou API).

    # Identifiant stable (ex: "T2M_MEAN", "RR_SUM").
    # Unicite assuree par la contrainte (dataset, code).
    # Pas de default: le code doit etre fourni.
    code = models.CharField(max_length=64)

    # Nom lisible (admin/UI).
    name = models.CharField(max_length=128)

    # Unite de mesure (ex: "C", "mm").
    unit = models.CharField(max_length=64)

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name="indicators",
    )

    def clean(self):
        # Normalise le code (trim + upper) et refuse le vide.
        if self.code is not None:
            self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({"code": "Le code ne peut pas etre vide."})
        if self.unit is not None:
            self.unit = self.unit.strip()
        if not self.unit:
            raise ValidationError({"unit": "L unite ne peut pas etre vide."})

    def save(self, *args, **kwargs):
        # Valide le modele avant sauvegarde.
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        # Tri par defaut et unicite par dataset.
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "code"],
                name="uniq_indicator_dataset_code",
            ),
        ]

    def __str__(self):
        # Libelle lisible (admin, logs, shell).
        return f"{self.name} - {self.code}"


class ComputationRule(models.Model):
    # Regle de calcul liee a un indicateur.
    # Un indicateur -> plusieurs regles.

    class Operation(models.TextChoices):
        # Valeurs autorisees pour operation.
        AVG = "avg", "Average"
        MIN = "min", "Minimum"
        MAX = "max", "Maximum"
        SUM = "sum", "Sum"

    class Meta:
        # Version unique par indicateur.
        constraints = [
            models.UniqueConstraint(
                fields=["indicator", "version"],
                name="uniq_rule_indicator_version",
            ),
        ]

    # Indicateur parent (suppression en cascade).
    indicator = models.ForeignKey("Indicator", on_delete=models.CASCADE)

    # Version de regle (entier positif).
    version = models.PositiveIntegerField()

    # Type d operation (contraint par choices).
    # Default: AVG.
    operation = models.CharField(max_length=16, choices=Operation.choices, default=Operation.AVG)

    # Active/inactive (utile pour l historique).
    is_active = models.BooleanField(default=True)

    def __str__(self):
        # Libelle lisible (admin, logs, shell).
        return f"{self.indicator.code} {self.version}"

    def clean(self):
        # Enforce strict positive version at model level.
        if self.version is not None and self.version <= 0:
            raise ValidationError({"version": "La version doit etre un entier strictement positif."})
