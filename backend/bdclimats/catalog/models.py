from django.db import models

class Dataset(models.Model):
    # "Dataset" = echantillon de données
    code = models.CharField(max_length=64, unique=True, default="default_name")
    name = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    source_url = models.URLField(max_length=200)
    created_at = models.DateField(auto_now=False, auto_now_add=True)

    def __str__(self):
        # Texte utilisé par Django Admin pour afficher un Dataset.
        return f"{self.name} — {self.code}"

class Indicator(models.Model):
    # "Indicator" = définition d'un indicateur métier (pas les données elles-mêmes).
    # Chaque instance correspond à une ligne en base (créée via /admin ou API plus tard).

    # Identifiant stable de l'indicateur (ex: "T2M_MEAN", "RR_SUM").
    # unique=True garantit qu'il n'y a jamais deux indicateurs avec le même code.
    #
    # En prod, on évite souvent un default "faux" et on préfère renseigner le champ explicitement.
    code = models.CharField(max_length=64)

    # Nom lisible pour l'admin et l'affichage (ex: "Température moyenne 2m").
    name = models.CharField(max_length=128)

    # Unité de mesure (ex: "°C", "mm"). Ici obligatoire (pas de blank=True).
    unit = models.CharField(max_length=64, blank=True)

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name="indicators",
    )

    class Meta:
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "code"],
                name="uniq_indicator_dataset_code",
            ),
        ]

    def __str__(self):
        # Texte utilisé par Django Admin (et ailleurs) pour afficher un Indicator.
        return f"{self.name} — {self.code}"
    

class ComputationRule(models.Model):
    # "ComputationRule" = une règle (ou recette simplifiée) liée à un Indicator.
    # Le champ indicator (ForeignKey) fait la relation 1 Indicator -> N Rules.

    class Operation(models.TextChoices):
        # TextChoices = ensemble de valeurs autorisées pour operation.
        # La valeur stockée en DB est le 1er élément (ex: "avg"),
        # le label affiché dans l'admin est le 2e (ex: "Average").
        #
        # Important : ça ne fait pas le calcul tout seul, c'est juste une valeur contrôlée.
        AVG = "avg", "Average"
        MIN = "min", "Minimum"
        MAX = "max", "Maximum"
        SUM = "sum", "Sum"

    class Meta:
        # Contraintes au niveau "table" (DB).
        # Ici : pour un même indicator, on interdit deux rules avec la même version.
        # => (indicator, version) doit être unique.
        constraints = [
            models.UniqueConstraint(
                fields=["indicator", "version"],
                name="uniq_rule_indicator_version",
            ),
        ]

    # Lien vers l'indicateur parent.
    # on_delete=models.CASCADE => si l'Indicator est supprimé, ses rules le sont aussi.
    indicator = models.ForeignKey("Indicator", on_delete=models.CASCADE)

    # Numéro de version de la recette/règle (1, 2, 3...). PositiveIntegerField évite les versions négatives.
    version = models.PositiveIntegerField()

    # Type d'opération (contrainte par Operation.choices).
    # default=Operation.AVG => si tu ne choisis rien, ça met "avg".
    operation = models.CharField(max_length=16, choices=Operation.choices, default=Operation.AVG)

    # Permet d'activer/désactiver une règle (pratique si tu gardes un historique).
    is_active = models.BooleanField(default=True)

    def __str__(self):
        # Affichage lisible en admin : code de l'indicator + version.
        return f"{self.indicator.code} {self.version}"
