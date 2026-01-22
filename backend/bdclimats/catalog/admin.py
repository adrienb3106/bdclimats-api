from django.contrib import admin
from .models import Indicator, ComputationRule

# Ce fichier configure l'interface Django Admin pour tes modèles.
# L'idée : décider "comment" Indicator et ComputationRule s'affichent et s'éditent dans /admin.


class ComputationRuleInline(admin.TabularInline):
    # Inline = édition d'un modèle "enfant" à l'intérieur de la page du modèle "parent".
    # Ici, ComputationRule est "enfant" parce qu'il a une ForeignKey vers Indicator.
    model = ComputationRule

    # Nombre de lignes vides affichées par défaut pour ajouter de nouvelles rules.
    # 0 = aucune ligne vide tant que tu ne cliques pas "Add another".
    extra = 0  # (mettre 1 si tu veux proposer une rule vide automatiquement)


class IndicatorAdmin(admin.ModelAdmin):
    # Configuration de la page d'admin pour Indicator.
    # inlines = liste des "sous-formulaires" à afficher dans la page Indicator.
    # Résultat : quand tu ouvres/modifies un Indicator, tu peux créer/éditer ses ComputationRule sur la même page.
    inlines = [ComputationRuleInline]


# Enregistre Indicator dans l'admin en utilisant la configuration personnalisée IndicatorAdmin
# (donc avec l'inline des ComputationRule).
admin.site.register(Indicator, IndicatorAdmin)

# Enregistre aussi ComputationRule dans l'admin comme menu séparé.
# Utile pour debug/édition directe, même si en pratique tu utiliseras souvent l'inline.
admin.site.register(ComputationRule)
