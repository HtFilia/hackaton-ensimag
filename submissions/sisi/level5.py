from __future__ import annotations
from typing import Iterable
from src.common.models import MultiBook, Order, OrderBook, OrderType, Side, TimeInForce

def _insert_bid(orders: list, order: Order) -> None:
    pos = 0
    for i, o in enumerate(orders):
        if o.price < order.price:
            pos = i + 1
    orders.insert(pos, order)

def _insert_ask(orders: list, order: Order) -> None:
    pos = 0
    for i, o in enumerate(orders):
        if o.price > order.price:
            break
        pos = i + 1
    orders.insert(pos, order)

def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        if order.action == "NEW":
            if order.visible_quantity is not None:
                order._iceberg_slice = order.visible_quantity
            _match_order(order, book)
        elif order.action == "CANCEL":
            _cancel_order(order, book)
        elif order.action == "AMEND":
            _amend_order(order, book)
    return initial_book

def _manage_iceberg(o: Order, fill: float) -> None:
    if hasattr(o, '_iceberg_slice'):
        o.visible_quantity -= fill
        if o.visible_quantity <= 0 and o.quantity > 0:
            o.visible_quantity = min(o._iceberg_slice, o.quantity)
        elif o.visible_quantity > o.quantity:
            o.visible_quantity = o.quantity

def _match_order(order: Order, book: OrderBook) -> None:
    is_market = order.order_type == OrderType.MARKET
    tif = order.time_in_force
    if tif == TimeInForce.FOK:
        avail = 0.0
        if order.side == Side.BUY:
            for ask in book.asks.orders:
                if not is_market and ask.price > order.price: break
                avail += ask.quantity
                if avail >= order.quantity: break
            if avail < order.quantity: return
        else:
            for bid in book.bids.orders:
                if not is_market and bid.price < order.price: break
                avail += bid.quantity
                if avail >= order.quantity: break
            if avail < order.quantity: return

    if order.side == Side.BUY:
        while order.quantity > 0 and book.asks.orders:
            b = book.asks.orders[0]
            if not is_market and b.price > order.price: break
            fill = min(order.quantity, b.quantity)
            order.quantity -= fill
            b.quantity -= fill
            _manage_iceberg(order, fill)
            _manage_iceberg(b, fill)
            if b.quantity == 0: book.asks.orders.pop(0)
        if order.quantity > 0 and not is_market and tif == TimeInForce.GTC:
            _insert_bid(book.bids.orders, order)
    else:
        while order.quantity > 0 and book.bids.orders:
            b = book.bids.orders[0]
            if not is_market and b.price < order.price: break
            fill = min(order.quantity, b.quantity)
            order.quantity -= fill
            b.quantity -= fill
            _manage_iceberg(order, fill)
            _manage_iceberg(b, fill)
            if b.quantity == 0: book.bids.orders.pop(0)
        if order.quantity > 0 and not is_market and tif == TimeInForce.GTC:
            _insert_ask(book.asks.orders, order)

def _cancel_order(order: Order, book: OrderBook) -> None:
    for sides in (book.bids.orders, book.asks.orders):
        for i, e in enumerate(sides):
            if e.id == order.id:
                sides.pop(i)
                return

def _amend_order(order: Order, book: OrderBook) -> None:
    f = None
    for sides in (book.bids.orders, book.asks.orders):
        for i, e in enumerate(sides):
            if e.id == order.id:
                f = sides.pop(i)
                break
        if f: break
    if not f: return
    f.price = order.price
    f.quantity = order.quantity
    if order.visible_quantity is not None:
        f._iceberg_slice = order.visible_quantity
        f.visible_quantity = min(f._iceberg_slice, f.quantity)
    elif hasattr(f, '_iceberg_slice'):
        f.visible_quantity = min(f._iceberg_slice, f.quantity)
    _match_order(f, book)
