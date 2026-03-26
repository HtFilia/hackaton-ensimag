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
        orderBook = initial_book.get_or_create(order.asset)
        if order.action == "NEW":
            if order.order_type == "market":
                if order.side == "sell":
                    bid_index = 0
                    while bid_index < len(orderBook.bids.orders):
                        bid = orderBook.bids.orders[bid_index]
                        if bid.quantity > order.quantity:
                            bid.quantity-= order.quantity
                            order.quantity = 0
                            break
                        else:
                            order.quantity-=bid.quantity
                            orderBook.bids.orders.pop(bid_index)
                            continue
                else:
                    ask_index = 0
                    while ask_index < len(orderBook.asks.orders):
                        ask = orderBook.asks.orders[ask_index]
                        if ask.quantity > order.quantity:
                            ask.quantity-= order.quantity
                            order.quantity = 0
                            break
                        else:
                            order.quantity-=ask.quantity
                            orderBook.asks.orders.pop(ask_index)
                            continue
            else :
                if order.side == "sell":
                    bid_index = 0
                    while bid_index < len(orderBook.bids.orders):
                        bid = orderBook.bids.orders[bid_index]
                        if bid.price >= order.price:
                            if bid.quantity > order.quantity:
                                bid.quantity-= order.quantity
                                order.quantity = 0
                                break
                            else:
                                order.quantity-=bid.quantity
                                orderBook.bids.orders.pop(bid_index)
                                continue
                        break
                    if order.quantity > 0:
                        orderBook.asks.add(order)
                else :
                    ask_index = 0
                    while ask_index < len(orderBook.asks.orders):
                        ask = orderBook.asks.orders[ask_index]
                        if ask.price <= order.price:
                            if ask.quantity > order.quantity:
                                ask.quantity-= order.quantity
                                order.quantity = 0
                                break
                            else:
                                order.quantity-=ask.quantity
                                orderBook.asks.orders.pop(ask_index)
                                continue
                        break
                    if order.quantity > 0:
                        orderBook.bids.add(order)
        elif order.action =="CANCEL":
                bid_index = 0
                while bid_index < len(orderBook.bids.orders):
                    if orderBook.bids.orders[bid_index].id == order.id:
                        orderBook.bids.orders.pop(bid_index)
                        break
                    bid_index+=1
                ask_index = 0
                while ask_index < len(orderBook.asks.orders):
                    if orderBook.asks.orders[ask_index].id == order.id:
                        orderBook.asks.orders.pop(ask_index)
                        break
                    ask_index+=1
        else:
            if order.side == "buy":
                bid_index = 0
                while bid_index < len(orderBook.bids.orders):
                    bid = orderBook.bids.orders[bid_index]
                    if bid.id == order.id:
                        if bid.price == order.price:
                            bid.quantity = order.quantity
                        else:
                            bid.price = order.price
                            bid.quantity = order.quantity
                            orderBook.bids.orders.pop(bid_index)
                            orderBook.bids.add(bid)
                        break
                    bid_index+=1
            else :
                ask_index = 0
                while ask_index < len(orderBook.asks.orders):
                    ask = orderBook.asks.orders[ask_index]
                    if ask.id == order.id:
                        if ask.price == ask.price:
                            ask.quantity = order.quantity
                        else:
                            ask.price = order.price
                            ask.quantity = order.quantity
                            orderBook.asks.orders.pop(ask_index)
                            orderBook.asks.add(ask)
                        break
                    ask_index+=1
    return initial_book



