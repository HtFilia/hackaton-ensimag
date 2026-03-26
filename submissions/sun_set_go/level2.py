from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side, OrderType


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
        
        if (order.order_type == OrderType.MARKET):
            if order.side == Side.BUY:
                while order.quantity > 0 and book.asks.orders:
                    best = book.asks.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.asks.orders.pop(0)
            else:
                while order.quantity > 0 and book.bids.orders:
                    best = book.bids.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.bids.orders.pop(0)
        else :    
            if (order.side == Side.BUY):
                while order.quantity > 0 and book.asks.orders and book.asks.orders[0].price <= order.price :
                    best = book.asks.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.asks.orders.pop(0)
            
                if order.quantity > 0:       
                    book.bids.add(order)
                    book.bids.orders.sort(key=lambda el: el.price, reverse=True)
            else:
                while order.quantity > 0 and book.bids.orders and book.bids.orders[0].price >= order.price:
                    best = book.bids.orders[0]
                    vente = min(order.quantity, best.quantity)
                    best.quantity -= vente
                    order.quantity -= vente
                    if best.quantity == 0:
                        book.bids.orders.pop(0)
                
                if order.quantity > 0:    
                    book.asks.add(order)
                    book.asks.orders.sort(key=lambda el: el.price)
                
    return initial_book

