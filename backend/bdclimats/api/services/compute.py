from typing import Iterable


class ComputeError(ValueError):
    """Erreur levée quand le calcul ne peut pas être effectué (op invalide, valeurs vides, etc.)."""


def compute(operation: str, values: Iterable[float]) -> float:
    """
    Applique une opération (avg|min|max|sum) sur une séquence de valeurs numériques.

    - operation: chaîne (ex: "avg", "min", "max", "sum")
    - values: itérable de floats (déjà nettoyé: pas de None si dropna a été appliqué)

    Retourne un float.
    Lève ComputeError si operation inconnue ou values vide.
    """
    values_list = list(values)

    if not values_list:
        raise ComputeError("Impossible de calculer: aucune valeur.")

    op = operation.strip().lower()

    if op == "avg":
        return sum(values_list) / len(values_list)
    if op == "sum":
        return sum(values_list)
    if op == "min":
        return min(values_list)
    if op == "max":
        return max(values_list)
    raise ComputeError(f"Opération inconnue: {operation!r}")
