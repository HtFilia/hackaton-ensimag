from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side

from submissions.coloc.level2 import process_orders as process_level_2


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

        new_orders = []

        if order.action == "NEW":
            new_orders.append(order)

    initial_book = process_level_2(initial_book, new_orders)

    for order in orders: 
        if order.action == "CANCEL":
            i = 0
            while i < len(book.asks.orders):
                ask_order = book.asks.orders[i]

                if ask_order.id == order.id:
                    book.asks.orders.pop(i)
                    break
                else:
                    i += 1
            i = 0
            while i < len(book.bids.orders):
                bid_order = book.bids.orders[i]

                if bid_order.id == order.id:
                    book.bids.orders.pop(i)
                    break
                else:
                    i += 1
        elif order.action == "NEW":
            if order.asset in book:
                if order.side == Side.BUY:
                    book.asks.orders.sort(key=lambda x: (x.price, x.id))
                    
                    i = 0
                    while i < len(book.asks.orders) and remaining_qty > 0:
                        ask_order = book.asks.orders[i]
                        
                        if ask_order.price <= order.price:
                            fill_qty = min(remaining_qty, ask_order.quantity)
                            remaining_qty -= fill_qty
                            ask_order.quantity -= fill_qty
                            
                            if ask_order.quantity == 0:
                                book.asks.orders.pop(i)
                            else:
                                i += 1
                        else:
                            break
                    
                    if remaining_qty > 0:
                        order.quantity = remaining_qty
                        book.bids.orders.append(order)
                        book.bids.orders.sort(key=lambda x: (-x.price, x.id))
                
                else: 
                    book.bids.orders.sort(key=lambda x: (-x.price, x.id))
                    
                    i = 0
                    while i < len(book.bids.orders) and remaining_qty > 0:
                        bid_order = book.bids.orders[i]
                        
                        if bid_order.price >= order.price:
                            fill_qty = min(remaining_qty, bid_order.quantity)
                            remaining_qty -= fill_qty
                            bid_order.quantity -= fill_qty
                            
                            if bid_order.quantity == 0:
                                book.bids.orders.pop(i)
                            else:
                                i += 1
                        else:
                            break
                    
                    if remaining_qty > 0:
                        order.quantity = remaining_qty
                        book.asks.orders.append(order)
                        book.asks.orders.sort(key=lambda x: (x.price, x.id))
            
        

        return initial_book
            
    
