from __future__ import annotations

from typing import Iterable
from bisect import insort

from src.common.models import MultiBook, Order, OrderBook, OrderType, Side


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        _match_order(order, book)
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
