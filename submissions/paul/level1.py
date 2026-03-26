from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side


def _sort_book(book) -> None:
    book.bids.orders.sort(key=lambda order: order.price, reverse=True)
    book.asks.orders.sort(key=lambda order: order.price)


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
    for book in initial_book.books.values():
        _sort_book(book)

    for order in orders:
        book = initial_book.get_or_create(order.asset)

        if order.side == Side.BUY:
            opposite_orders = book.asks.orders
        else:
            opposite_orders = book.bids.orders

        while order.quantity > 0 and opposite_orders:
            best_order = opposite_orders[0]

            if order.side == Side.BUY and best_order.price > order.price:
                break
            if order.side == Side.SELL and best_order.price < order.price:
                break

            traded_quantity = min(order.quantity, best_order.quantity)
            order.quantity -= traded_quantity
            best_order.quantity -= traded_quantity

            if best_order.quantity == 0:
                opposite_orders.pop(0)

        if order.quantity > 0:
            if order.side == Side.BUY:
                book.bids.add(order)
            else:
                book.asks.add(order)

            _sort_book(book)

    return initial_book
