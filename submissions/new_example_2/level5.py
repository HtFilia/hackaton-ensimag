from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 5 — Ordres Iceberg

    Étendez votre moteur avec les ordres à quantité cachée via order.visible_quantity.

    Règles :
    - Quand order.visible_quantity est défini, seule cette portion est visible dans le carnet.
    - La totalité de order.quantity est disponible pour le matching (profondeur cachée incluse).
    - Quand la tranche visible est consommée, la tranche suivante est rechargée automatiquement
      depuis le total restant, en conservant la même priorité prix-temps.
    - Si la quantité restante est inférieure à visible_quantity, la portion visible égale le reste.
    - AMEND sur un iceberg modifie le prix et la quantité totale ; visible_quantity est préservé
      (plafonné au nouveau total si nécessaire).
    - Les ordres sans visible_quantity se comportent comme des ordres limite normaux.
    - Toutes les fonctionnalités du Palier 4 restent applicables.

    Champs utiles :
        order.visible_quantity  — Optional[float], None signifie pas d'iceberg

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    raise NotImplementedError("Implémenter le Palier 5 : Ordres Iceberg")
