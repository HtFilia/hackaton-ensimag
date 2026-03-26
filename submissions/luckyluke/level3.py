from __future__ import annotations

from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderType, Side


def _sort_book(book) -> None:
    book.bids.orders.sort(key=lambda order: order.price, reverse=True)
    book.asks.orders.sort(key=lambda order: order.price)


def _process_new_order(book, order: Order) -> None:
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


def _find_order(initial_book: MultiBook, order_id: str):
    for book in initial_book.books.values():
        for orders_list in (book.bids.orders, book.asks.orders):
            for index, existing_order in enumerate(orders_list):
                if existing_order.id == order_id:
                    return orders_list, index, existing_order

    return None, None, None


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for book in initial_book.books.values():
        _sort_book(book)

    for order in orders:
        if order.action == Action.CANCEL:
            orders_list, index, _ = _find_order(initial_book, order.id)
            if orders_list is not None:
                orders_list.pop(index)
            continue

        if order.action == Action.AMEND:
            orders_list, index, existing_order = _find_order(initial_book, order.id)
            if existing_order is None:
                continue

            orders_list.pop(index)

            amended_order = Order(
                id=existing_order.id,
                side=existing_order.side,
                price=order.price,
                quantity=order.quantity,
                asset=existing_order.asset,
                order_type=existing_order.order_type,
            )

            book = initial_book.get_or_create(amended_order.asset)
            _process_new_order(book, amended_order)
            continue

        book = initial_book.get_or_create(order.asset)
        _process_new_order(book, order)

    return initial_book

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
