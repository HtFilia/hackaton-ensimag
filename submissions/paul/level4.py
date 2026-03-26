from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 4 — IOC et FOK

    Étendez votre moteur avec les contraintes de durée de validité via order.time_in_force.

    Règles :
    - GTC (Good-Till-Cancelled, par défaut) : l'ordre repose dans le carnet s'il n'est pas
      entièrement exécuté.
    - IOC (Immediate-or-Cancel) : exécuter autant que possible immédiatement ; annuler le reste.
      La partie non exécutée n'est jamais ajoutée au carnet.
    - FOK (Fill-or-Kill) : la totalité de la quantité doit être immédiatement exécutable, sinon
      l'ordre est rejeté entièrement. Vérifier la liquidité disponible AVANT d'exécuter quoi que
      ce soit.
    - Toutes les fonctionnalités du Palier 3 (LIMIT, MARKET, CANCEL, AMEND) restent applicables.

    Champs utiles :
        order.time_in_force  — "GTC", "IOC" ou "FOK"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    raise NotImplementedError("Implémenter le Palier 4 : IOC & FOK")
