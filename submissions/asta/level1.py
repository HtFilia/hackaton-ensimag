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
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        remaining = order.quantity
        is_buy = order.side.value == "buy"

        if is_buy:
            passive = book.asks.orders
            active = book.bids.orders
        else:
            passive = book.bids.orders
            active = book.asks.orders

        i = 0
        while i < len(passive) and remaining > 0:
            best = passive[i]
            matched = is_buy and best.price <= order.price
            matched = matched or (not is_buy and best.price >= order.price)
            if not matched:
                break
            if best.quantity <= remaining:
                remaining -= best.quantity
                passive.pop(i)
            else:
                best.quantity -= remaining
                remaining = 0
                i += 1

        if remaining > 0:
            order.quantity = remaining
            i = 0
            if is_buy:
                while i < len(active) and active[i].price > order.price:
                    i += 1
            else:
                while i < len(active) and active[i].price < order.price:
                    i += 1
            active.insert(i, order)

    return initial_book
    
