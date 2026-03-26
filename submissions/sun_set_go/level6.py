from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 6 — Enchère de Clôture (LOC, MOC, CLOSE)

    Étendez votre moteur avec les ordres de clôture en mode enchère.

    Nouveaux types d'ordres :
    - LOC (Limit-on-Close) : ordre limite qui participe UNIQUEMENT à l'enchère de clôture.
      Il ne matche PAS dans le carnet continu. Il reste en file jusqu'à un événement CLOSE.
    - MOC (Market-on-Close) : ordre au marché qui participe uniquement à l'enchère de clôture.
      Il reste en file jusqu'à un événement CLOSE.

    Nouvelle action :
    - CLOSE : déclenche l'enchère de clôture pour l'actif spécifié (order.asset).

    Algorithme d'enchère de clôture (décroisement max-volume) :
    1. Collecter tous les ordres LOC et MOC en attente pour l'actif.
    2. Trouver le prix d'équilibre P* qui maximise min(volume_achat, volume_vente) :
       - Pour chaque prix candidat P (prix des ordres LOC) :
         volume_achat  = somme des qty MOC achat + LOC achat avec prix >= P
         volume_vente  = somme des qty MOC vente + LOC vente avec prix <= P
    3. Exécuter les ordres éligibles à P* (FIFO par ordre de priorité).
    4. Annuler TOUS les ordres LOC/MOC restants pour cet actif (dont les partiels).
    5. Le carnet LIMIT continu n'est PAS affecté par l'enchère.

    Note : CANCEL/AMEND peuvent cibler des ordres dans la file d'enchère.

    Toutes les fonctionnalités du Palier 5 restent applicables.

    Champs utiles :
        order.order_type  — "loc" ou "moc"
        order.action      — "CLOSE" (par actif)

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook (carnet continu uniquement ; file d'enchère vidée).
    """
    raise NotImplementedError("Implémenter le Palier 6 : Enchère de Clôture")
