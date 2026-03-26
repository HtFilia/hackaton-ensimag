from __future__ import annotations

from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderType, Side, TimeInForce


def _sort_book(book) -> None:
    book.bids.orders.sort(key=lambda order: order.price, reverse=True)
    book.asks.orders.sort(key=lambda order: order.price)


def _find_order(initial_book: MultiBook, order_id: str):
    for book in initial_book.books.values():
        for orders_list in (book.bids.orders, book.asks.orders):
            for index, existing_order in enumerate(orders_list):
                if existing_order.id == order_id:
                    return orders_list, index, existing_order

    return None, None, None


def _can_match(incoming_order: Order, resting_order: Order) -> bool:
    if incoming_order.order_type == OrderType.MARKET:
        return True

    if incoming_order.side == Side.BUY:
        return resting_order.price <= incoming_order.price

    return resting_order.price >= incoming_order.price


def _update_visible_quantity(order: Order) -> None:
    if order.visible_quantity is None:
        return

    # On garde la taille de tranche d'origine pour pouvoir la réutiliser après un AMEND.
    if not hasattr(order, "_iceberg_peak"):
        order._iceberg_peak = order.visible_quantity

    order.visible_quantity = min(order._iceberg_peak, order.quantity)


def _has_enough_liquidity(order: Order, opposite_orders) -> bool:
    remaining_quantity = order.quantity

    for resting_order in opposite_orders:
        if not _can_match(order, resting_order):
            break

        traded_quantity = min(remaining_quantity, resting_order.quantity)
        remaining_quantity -= traded_quantity

        if remaining_quantity == 0:
            return True

    return False


def _process_new_order(book, order: Order) -> None:
    if order.side == Side.BUY:
        opposite_orders = book.asks.orders
    else:
        opposite_orders = book.bids.orders

    if order.time_in_force == TimeInForce.FOK and not _has_enough_liquidity(order, opposite_orders):
        return

    while order.quantity > 0 and opposite_orders:
        best_order = opposite_orders[0]

        if not _can_match(order, best_order):
            break

        traded_quantity = min(order.quantity, best_order.quantity)
        order.quantity -= traded_quantity
        best_order.quantity -= traded_quantity

        if best_order.quantity == 0:
            opposite_orders.pop(0)
        else:
            _update_visible_quantity(best_order)

    if order.quantity > 0 and order.order_type != OrderType.MARKET and order.time_in_force == TimeInForce.GTC:
        _update_visible_quantity(order)

        if order.side == Side.BUY:
            book.bids.add(order)
        else:
            book.asks.add(order)

        _sort_book(book)


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
    for book in initial_book.books.values():
        for resting_order in book.bids.orders + book.asks.orders:
            _update_visible_quantity(resting_order)
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

            visible_quantity = None
            if existing_order.visible_quantity is not None:
                visible_quantity = getattr(existing_order, "_iceberg_peak", existing_order.visible_quantity)

            amended_order = Order(
                id=existing_order.id,
                side=existing_order.side,
                price=order.price,
                quantity=order.quantity,
                asset=existing_order.asset,
                order_type=existing_order.order_type,
                min_quantity=existing_order.min_quantity,
                time_in_force=existing_order.time_in_force,
                visible_quantity=visible_quantity,
                stop_price=existing_order.stop_price,
                trader_id=existing_order.trader_id,
            )

            book = initial_book.get_or_create(amended_order.asset)
            _process_new_order(book, amended_order)
            continue

        book = initial_book.get_or_create(order.asset)
        _process_new_order(book, order)

    return initial_book
