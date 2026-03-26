from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order,Side


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
            if order.order_type=="market":
                if order.side == Side.BUY:
                    immediately_execute(order, book.asks.orders)
                    
                elif order.side == Side.SELL:
                    immediately_execute(order, book.bids.orders) 

            else:
                if order.side == Side.BUY:
                    """ On regarde les asks pour les ordres d'achat"""
                    execute_order(order, book.asks.orders)
                    if order.quantity > 0:
                        book.bids.orders.append(order)
                        book.bids.orders.sort(key=lambda x: x.price, reverse=True)
                        
                elif order.side == Side.SELL:
                    execute_order(order, book.bids.orders) 
                    if order.quantity>0:
                        book.asks.orders.append(order)
                        book.asks.orders.sort(key=lambda x: x.price )
                            

    return initial_book

def immediately_execute(order , orders):
    
    i=0
    while order.quantity>=0 and i<len(orders):
        current = orders[i]
        quantité = min(order.quantity, current.quantity)
        order.quantity -= quantité
        current.quantity -= quantité
        if current.quantity <= 0:
            orders.pop(i)  
        i+=1

         


def execute_order(order, orders):
    
    while orders and order.quantity > 0:
        current = orders[0] 
        if order.side == Side.BUY:
            possible= order.price >= current.price
        else:
            possible = order.price <= current.price
            
        if not possible:
            break
            
        quantité = min(order.quantity, current.quantity)
        order.quantity -= quantité
        current.quantity -= quantité
        
        if current.quantity <= 0:
            orders.pop(0)   