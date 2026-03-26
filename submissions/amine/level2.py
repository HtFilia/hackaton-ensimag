from __future__ import annotations

from typing import Iterable

from src.common.models import BookSide, MultiBook, Order, OrderType, Side


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
    if incoming.order_type == OrderType.MARKET:
        return True
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
    """Palier 2 — Ordres au Marché

    Étendez votre moteur du Palier 1 avec la gestion des ordres au marché.

    Règles :
    - Les ordres MARKET (order.order_type == "market") s'exécutent immédiatement à n'importe quel
      prix disponible.
    - Les ordres MARKET ne reposent PAS dans le carnet. La quantité non exécutée est annulée.
    - Les ordres LIMIT se comportent exactement comme au Palier 1.

    Champs utiles :
        order.order_type  — "limit" ou "market"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
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

        if order.quantity > 0 and order.order_type != OrderType.MARKET:
            insert_order(resting_side, order)

    return initial_book
