from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 1 — Ordres Limite de Base (multi-actifs)

    Implémentez un moteur de carnet d'ordres limite gérant plusieurs actifs.

    Règles :
    - Chaque order.asset est routé vers son propre carnet indépendant dans le MultiBook.
    - Les ordres BUY matchent contre les asks (prix le plus bas en premier) si ask.price <= buy.price.
    - Les ordres SELL matchent contre les bids (prix le plus haut en premier) si bid.price >= sell.price.
    - Exécutions partielles : le reste repose dans le carnet s'il n'est pas entièrement exécuté.
    - Priorité prix-temps : même niveau de prix = FIFO.
    - Bids triés par prix décroissant ; asks par prix croissant.

    Champs utiles :
        order.id, order.side, order.price, order.quantity, order.asset

    Args :
        initial_book : État initial (MultiBook, généralement vide).
        orders : Séquence d'ordres entrants à traiter.

    Returns :
        État final du MultiBook après traitement de tous les ordres.
    """
    for order in orders :
        orderBook = initial_book.get_or_create(order.asset)
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
    return initial_book
