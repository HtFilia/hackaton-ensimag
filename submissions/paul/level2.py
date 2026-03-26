from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, OrderType, Side


def _sort_book(book) -> None:
    book.bids.orders.sort(key=lambda order: order.price, reverse=True)
    book.asks.orders.sort(key=lambda order: order.price)


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

            if order.order_type != OrderType.MARKET:
                if order.side == Side.BUY and best_order.price > order.price:
                    break
                if order.side == Side.SELL and best_order.price < order.price:
                    break

            traded_quantity = min(order.quantity, best_order.quantity)
            order.quantity -= traded_quantity
            best_order.quantity -= traded_quantity

            if best_order.quantity == 0:
                opposite_orders.pop(0)

        if order.quantity > 0 and order.order_type != OrderType.MARKET:
            if order.side == Side.BUY:
                book.bids.add(order)
            else:
                book.asks.add(order)

            _sort_book(book)

    return initial_book
