from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 3 — Annulation et Modification

    Étendez votre moteur avec la gestion du cycle de vie des ordres via order.action.

    Règles :
    - NEW (par défaut) : traitement normal de l'ordre.
    - CANCEL : supprime l'ordre reposant dont l'id est égal à order.id du carnet.
      Chercher dans les bids et les asks. Ignorer silencieusement si introuvable.
    - AMEND : met à jour le prix et/ou la quantité d'un ordre existant.
      Sémantique : annuler l'ancien ordre puis réinsérer avec les nouvelles valeurs
      (perte de priorité temporelle).
      Si le nouveau prix croise le côté opposé, l'ordre s'exécute immédiatement.
      Seuls le prix et la quantité changent ; le côté et le type d'ordre sont préservés.

    Note : pour CANCEL/AMEND, order.id est l'id de l'ordre à modifier (ref_id dans le CSV).

    Champs utiles :
        order.action  — "NEW", "CANCEL" ou "AMEND"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        
        if (order.order_type == OrderType.MARKET):
            if order.side == Side.BUY:
                while order.quantity > 0 and book.asks.orders:
                    best = book.asks.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.asks.orders.pop(0)
            else:
                while order.quantity > 0 and book.bids.orders:
                    best = book.bids.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.bids.orders.pop(0)
        else :    
            if (order.side == Side.BUY):
                while order.quantity > 0 and book.asks.orders and book.asks.orders[0].price <= order.price :
                    best = book.asks.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.asks.orders.pop(0)
            
                if order.quantity > 0:       
                    book.bids.add(order)
                    book.bids.orders.sort(key=lambda el: el.price, reverse=True)
            else:
                while order.quantity > 0 and book.bids.orders and book.bids.orders[0].price >= order.price:
                    best = book.bids.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.bids.orders.pop(0)
                
                if order.quantity > 0:    
                    book.asks.add(order)
                    book.asks.orders.sort(key=lambda el: el.price)
                
    return initial_book

