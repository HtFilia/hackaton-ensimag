from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, OrderType, Side


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
        book = initial_book.get_or_create(order.asset)
        remaining_qty = order.quantity
        
        if order.side == Side.BUY:
            if order.order_type == OrderType.MARKET:
                i = 0
                while i < len(book.asks.orders) and remaining_qty > 0:
                    ask_order = book.asks.orders[i]

                    fill_qty = min(remaining_qty, ask_order.quantity)
                    remaining_qty -= fill_qty
                    ask_order.quantity -= fill_qty
                    
                    if ask_order.quantity == 0:
                        book.asks.orders.pop(i)
                    else:
                        i += 1
            else:
                book.asks.orders.sort(key=lambda x: (x.price, x.id))
                
                i = 0
                while i < len(book.asks.orders) and remaining_qty > 0:
                    ask_order = book.asks.orders[i]
                    
                    if ask_order.price <= order.price:
                        fill_qty = min(remaining_qty, ask_order.quantity)
                        remaining_qty -= fill_qty
                        ask_order.quantity -= fill_qty
                        
                        if ask_order.quantity == 0:
                            book.asks.orders.pop(i)
                        else:
                            i += 1
                    else:
                        break
                
                if remaining_qty > 0:
                    order.quantity = remaining_qty
                    book.bids.orders.append(order)
                    book.bids.orders.sort(key=lambda x: (-x.price, x.id))
        else: 
            if order.order_type == OrderType.MARKET:
                i = 0
                while i < len(book.bids.orders) and remaining_qty > 0:
                    ask_order = book.bids.orders[i]

                    fill_qty = min(remaining_qty, ask_order.quantity)
                    remaining_qty -= fill_qty
                    ask_order.quantity -= fill_qty
                    
                    if ask_order.quantity == 0:
                        book.bids.orders.pop(i)
                    else:
                        i += 1
            else: 
                book.bids.orders.sort(key=lambda x: (-x.price, x.id))
                
                i = 0
                while i < len(book.bids.orders) and remaining_qty > 0:
                    bid_order = book.bids.orders[i]
                    
                    if bid_order.price >= order.price:
                        fill_qty = min(remaining_qty, bid_order.quantity)
                        remaining_qty -= fill_qty
                        bid_order.quantity -= fill_qty
                        
                        if bid_order.quantity == 0:
                            book.bids.orders.pop(i)
                        else:
                            i += 1
                    else:
                        break
                
                if remaining_qty > 0:
                    order.quantity = remaining_qty
                    book.asks.orders.append(order)
                    book.asks.orders.sort(key=lambda x: (x.price, x.id))
    return initial_book