from __future__ import annotations

from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side, TimeInForce

from .level2 import crosses, initialize_book, insert_order, match_book
from .level3 import amend_order, pop_order


def get_sides(book: OrderBook, side: Side):
    if side == Side.BUY:
        return book.asks, book.bids
    return book.bids, book.asks


def can_fully_execute(resting_side, incoming: Order) -> bool:
    available_quantity = 0.0

    for resting_order in resting_side.orders:
        if not crosses(incoming, resting_order):
            break
        available_quantity += resting_order.quantity
        if available_quantity >= incoming.quantity:
            return True

    return False


def process_new_order(multibook: MultiBook, order: Order) -> None:
    book = multibook.books.get(order.asset)

    if book is None:
        if order.order_type == OrderType.MARKET or order.time_in_force != TimeInForce.GTC:
            return
        book = multibook.get_or_create(order.asset)

    opposing_side, resting_side = get_sides(book, order.side)

    if order.time_in_force == TimeInForce.FOK and not can_fully_execute(opposing_side, order):
        return

    match_book(opposing_side, order)

    if (
        order.quantity > 0
        and order.order_type != OrderType.MARKET
        and order.time_in_force == TimeInForce.GTC
    ):
        insert_order(resting_side, order)


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 4 — IOC et FOK

    Étendez votre moteur avec les contraintes de durée de validité via order.time_in_force.

    Règles :
    - GTC (Good-Till-Cancelled, par défaut) : l'ordre repose dans le carnet s'il n'est pas
      entièrement exécuté.
    - IOC (Immediate-or-Cancel) : exécuter autant que possible immédiatement ; annuler le reste.
      La partie non exécutée n'est jamais ajoutée au carnet.
    - FOK (Fill-or-Kill) : la totalité de la quantité doit être immédiatement exécutable, sinon
      l'ordre est rejeté entièrement. Vérifier la liquidité disponible AVANT d'exécuter quoi que
      ce soit.
    - Toutes les fonctionnalités du Palier 3 (LIMIT, MARKET, CANCEL, AMEND) restent applicables.

    Champs utiles :
        order.time_in_force  — "GTC", "IOC" ou "FOK"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    initialize_book(initial_book)

    for order in orders:
        if order.action == Action.NEW:
            process_new_order(initial_book, order)
            continue

        book = initial_book.books.get(order.asset)
        if book is None:
            continue

        if order.action == Action.CANCEL:
            pop_order(book, order.id)
            continue

        if order.action == Action.AMEND:
            original = pop_order(book, order.id)
            if original is None:
                continue

            amended = amend_order(original, order)
            process_new_order(initial_book, amended)

    return initial_book
