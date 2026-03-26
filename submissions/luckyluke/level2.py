from __future__ import annotations
from typing import Iterable
from src.common.models import MultiBook, Order, Side, OrderType

def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:

        book = initial_book.get_or_create(order.asset)
        
        if order.side == Side.BUY:
            opposite_side = book.asks
            own_side = book.bids
            reverse_sort = True
        else:
            opposite_side = book.bids
            own_side = book.asks
            reverse_sort = False

        while opposite_side.orders and order.quantity > 0:
            best_opp = opposite_side.orders[0]
            
            # - Si c'est MARKET : on match toujours
            # - Si c'est LIMIT : lvl 1
            is_market = (order.order_type == OrderType.MARKET)
            price_compatible = (
                (order.side == Side.BUY and order.price >= best_opp.price) or
                (order.side == Side.SELL and order.price <= best_opp.price)
            )
            
            if is_market or price_compatible:
                trade_qty = min(order.quantity, best_opp.quantity)
                order.quantity -= trade_qty
                best_opp.quantity -= trade_qty
                
                if best_opp.quantity <= 0:
                    opposite_side.orders.pop(0)
            else:
                break

        if order.order_type == OrderType.LIMIT and order.quantity > 0:
            own_side.orders.append(order)
            own_side.orders.sort(key=lambda x: x.price, reverse=reverse_sort)

    return initial_book
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
