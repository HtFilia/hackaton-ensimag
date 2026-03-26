from __future__ import annotations

from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side, TimeInForce

from .level2 import crosses, initialize_book, insert_order
from .level3 import amend_order, pop_order
from .level4 import can_fully_execute


def get_sides(book: OrderBook, side: Side):
    if side == Side.BUY:
        return book.asks, book.bids
    return book.bids, book.asks



def visible_quantity(order: Order) -> None:
    if order.visible_quantity is not None:
        order.visible_quantity = min(order.visible_quantity, order.quantity)


def prepare_existing_icebergs(multibook: MultiBook) -> None:
    for book in multibook.books.values():
        for side in (book.bids, book.asks):
            for order in side.orders:
                visible_quantity(order)


def match_book(resting_side, incoming: Order) -> None:
    while incoming.quantity > 0 and resting_side.orders:
        best_resting = resting_side.orders[0]
        if not crosses(incoming, best_resting):
            break

        traded_quantity = min(incoming.quantity, best_resting.quantity)
        incoming.quantity -= traded_quantity
        best_resting.quantity -= traded_quantity
        visible_quantity(best_resting)

        if best_resting.quantity <= 0:
            resting_side.orders.pop(0)


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
    visible_quantity(order)

    if (
        order.quantity > 0
        and order.order_type != OrderType.MARKET
        and order.time_in_force == TimeInForce.GTC
    ):
        insert_order(resting_side, order)


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 5 — Ordres Iceberg

    Étendez votre moteur avec les ordres à quantité cachée via order.visible_quantity.

    Règles :
    - Quand order.visible_quantity est défini, seule cette portion est visible dans le carnet.
    - La totalité de order.quantity est disponible pour le matching (profondeur cachée incluse).
    - Quand la tranche visible est consommée, la tranche suivante est rechargée automatiquement
      depuis le total restant, en conservant la même priorité prix-temps.
    - Si la quantité restante est inférieure à visible_quantity, la portion visible égale le reste.
    - AMEND sur un iceberg modifie le prix et la quantité totale ; visible_quantity est préservé
      (plafonné au nouveau total si nécessaire).
    - Les ordres sans visible_quantity se comportent comme des ordres limite normaux.
    - Toutes les fonctionnalités du Palier 4 restent applicables.

    Champs utiles :
        order.visible_quantity  — Optional[float], None signifie pas d'iceberg

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    initialize_book(initial_book)
    prepare_existing_icebergs(initial_book)

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
            visible_quantity(amended)
            process_new_order(initial_book, amended)

    return initial_book
