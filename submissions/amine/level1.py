from __future__ import annotations

from typing import Iterable

from src.common.models import BookSide, MultiBook, Order, Side


def sort_side(side: BookSide) -> None:
    if side.side == Side.BUY:
        side.orders.sort(key=lambda order: order.price, reverse=True)
    else:
        side.orders.sort(key=lambda order: order.price)


def initialize_book(book: MultiBook) -> None:
    for order_book in book.books.values():
        sort_side(order_book.bids)
        sort_side(order_book.asks)


def crosses(incoming: Order, resting: Order) -> bool:
    if incoming.side == Side.BUY:
        return resting.price <= incoming.price
    return resting.price >= incoming.price


def match_book(resting_side: BookSide, incoming: Order) -> None:
    while incoming.quantity > 0 and resting_side.orders:
        best_resting = resting_side.orders[0]
        if not crosses(incoming, best_resting):
            break

        traded_quantity = min(incoming.quantity, best_resting.quantity)
        incoming.quantity -= traded_quantity
        best_resting.quantity -= traded_quantity

        if best_resting.quantity <= 0:
            resting_side.orders.pop(0)


def insert_order(side: BookSide, order: Order) -> None:
    insert_at = len(side.orders)

    for index, resting_order in enumerate(side.orders):
        
        if side.side == Side.BUY and order.price > resting_order.price:
            insert_at = index
            break
        if side.side == Side.SELL and order.price < resting_order.price:
            insert_at = index
            break

    side.orders.insert(insert_at, order)


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
    initialize_book(initial_book)

    for order in orders:
        book = initial_book.get_or_create(order.asset)

        if order.side == Side.BUY:
            opposing_side = book.asks
            resting_side = book.bids
        else:
            opposing_side = book.bids
            resting_side = book.asks

        match_book(opposing_side, order)

        if order.quantity > 0:
            insert_order(resting_side, order)

    return initial_book
