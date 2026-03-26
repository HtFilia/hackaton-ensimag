from __future__ import annotations

from typing import Iterable
from src.common.models import MultiBook, Order, OrderBook, OrderType, Side
from bisect import insort


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        if order.action == "NEW":
            _match_order(order, book)
        elif order.action == "CANCEL":
            _cancel_order(order, book)
        elif order.action == "AMEND":
            _amend_order(order, book)
    return initial_book


def _match_order(order: Order, book: OrderBook) -> None:
    is_market = order.order_type == OrderType.MARKET

    if order.side == Side.BUY:
        while order.quantity > 0 and book.asks.orders:
            best_ask = book.asks.orders[0]
            if not is_market and best_ask.price > order.price:
                break
            fill = min(order.quantity, best_ask.quantity)
            order.quantity -= fill
            best_ask.quantity -= fill
            if best_ask.quantity == 0:
                book.asks.orders.pop(0)
        if order.quantity > 0 and not is_market:
            insort(book.bids.orders, order, key=lambda o: -o.price)
    else:
        while order.quantity > 0 and book.bids.orders:
            best_bid = book.bids.orders[0]
            if not is_market and best_bid.price < order.price:
                break
            fill = min(order.quantity, best_bid.quantity)
            order.quantity -= fill
            best_bid.quantity -= fill
            if best_bid.quantity == 0:
                book.bids.orders.pop(0)
        if order.quantity > 0 and not is_market:
            insort(book.asks.orders, order, key=lambda o: o.price)


def _cancel_order(order: Order, book: OrderBook) -> None:
    for side_orders in (book.bids.orders, book.asks.orders):
        for i, existing in enumerate(side_orders):
            if existing.id == order.id:
                side_orders.pop(i)
                return


def _amend_order(order: Order, book: OrderBook) -> None:
    found = None
    for side_orders in (book.bids.orders, book.asks.orders):
        for i, existing in enumerate(side_orders):
            if existing.id == order.id:
                found = side_orders.pop(i)
                break
        if found:
            break
    if found is None:
        return
    found.price = order.price
    found.quantity = order.quantity
    _match_order(found, book)
