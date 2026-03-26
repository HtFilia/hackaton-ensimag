from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side, BookSide, OrderType
from src.common.models import *


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

    def insert_in_book(side: BookSide, order: Order) -> None:
        inserted = False
        for i, existing in enumerate(side.orders):
            if side.side == Side.BUY:
                if existing.price < order.price:
                    side.orders.insert(i, order)
                    inserted = True
                    break
            else:
                if existing.price > order.price:
                    side.orders.insert(i, order)
                    inserted = True
                    break
        if not inserted:
            side.orders.append(order)

    for order in orders:
        my_order_book = initial_book.get_or_create(order.asset)

        
        if order.order_type == OrderType.MARKET :
            if order.side == Side.BUY:
                asks = my_order_book.asks
                while order.quantity > 0:
                    best_ask = asks.best()
                    if best_ask is None:
                        break
                    trade_qty = min(order.quantity, best_ask.quantity)
                    order.quantity -= trade_qty
                    best_ask.quantity -= trade_qty
                    if best_ask.quantity == 0:
                        asks.orders.pop(0)
            elif order.side == Side.SELL:
                bids = my_order_book.bids
                while order.quantity > 0:
                    best_bid = bids.best()
                    if best_bid is None:
                        break
                    trade_qty = min(order.quantity, best_bid.quantity)
                    order.quantity -= trade_qty
                    best_bid.quantity -= trade_qty
                    if best_bid.quantity == 0:
                        bids.orders.pop(0)
            

        else:
            # pareioll que level1
            if order.side == Side.BUY:
                asks = my_order_book.asks
                while order.quantity > 0:
                    best_ask = asks.best()
                    if best_ask is None:
                        break
                    if best_ask.price <= order.price:
                        if order.quantity < best_ask.quantity:
                            best_ask.quantity -= order.quantity
                            order.quantity = 0
                        elif order.quantity == best_ask.quantity:
                            order.quantity = 0
                            asks.orders.pop(0)
                        else:
                            order.quantity -= best_ask.quantity
                            asks.orders.pop(0)
                    else:
                        break
                if order.quantity > 0:
                    insert_in_book(my_order_book.bids, order)

            elif order.side == Side.SELL:
                bids = my_order_book.bids
                while order.quantity > 0:
                    best_bid = bids.best()
                    if best_bid is None:
                        break
                    if best_bid.price >= order.price:
                        if order.quantity < best_bid.quantity:
                            best_bid.quantity -= order.quantity
                            order.quantity = 0
                        elif order.quantity == best_bid.quantity:
                            order.quantity = 0
                            bids.orders.pop(0)
                        else:
                            order.quantity -= best_bid.quantity
                            bids.orders.pop(0)
                    else:
                        break
                if order.quantity > 0:
                    insert_in_book(my_order_book.asks, order)
    return initial_book
    #raise NotImplementedError("Implémenter le Palier 2 : Ordres au Marché")
