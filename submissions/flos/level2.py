from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order


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
    for order in orders:
        orderBook = initial_book.get_or_create(order.asset)
        if order.order_type == "market":
            if order.side == "sell":
                bid_index = 0
                while bid_index < len(orderBook.bids.orders):
                    bid = orderBook.bids.orders[bid_index]
                    if bid.quantity > order.quantity:
                        bid.quantity-= order.quantity
                        order.quantity = 0
                        break
                    else:
                        order.quantity-=bid.quantity
                        orderBook.bids.orders.pop(bid_index)
                        continue
            else:
                ask_index = 0
                while ask_index < len(orderBook.asks.orders):
                    ask = orderBook.asks.orders[ask_index]
                    if ask.quantity > order.quantity:
                        ask.quantity-= order.quantity
                        order.quantity = 0
                        break
                    else:
                        order.quantity-=ask.quantity
                        orderBook.asks.orders.pop(ask_index)
                        continue
        else :
            if order.side == "sell":
                bid_index = 0
                while bid_index < len(orderBook.bids.orders):
                    bid = orderBook.bids.orders[bid_index]
                    if bid.price >= order.price:
                        if bid.quantity > order.quantity:
                            bid.quantity-= order.quantity
                            order.quantity = 0
                            break
                        else:
                            order.quantity-=bid.quantity
                            orderBook.bids.orders.pop(bid_index)
                            continue
                    break
                if order.quantity > 0:
                    orderBook.asks.add(order)
            else :
                ask_index = 0
                while ask_index < len(orderBook.asks.orders):
                    ask = orderBook.asks.orders[ask_index]
                    if ask.price <= order.price:
                        if ask.quantity > order.quantity:
                            ask.quantity-= order.quantity
                            order.quantity = 0
                            break
                        else:
                            order.quantity-=ask.quantity
                            orderBook.asks.orders.pop(ask_index)
                            continue
                    break
                if order.quantity > 0:
                    orderBook.bids.add(order)
    return initial_book

                    