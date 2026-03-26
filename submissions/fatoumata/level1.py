from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 1 — Ordres Limite de Base (multi-actifs)

    Implémentez un moteur de carnet d'ordres limite gérant plusieurs actifs.

    Règles :
    - Chaque order.asset est routé vers son propre carnet indépendant dans le MultiBook.
    - Les ordres BUY matchent contre les asks (prix le plus bas en premier) si ask.price <= buy.price.
    - Les ordres SELL matchent contre les bids (prix le plus haut en premier) si bid.price >= sell.price.
    - Exécutions partielles : le reste repose dans le carnet s'il n'est pas entièrement exécuté.
    - Priorité prix-temps : même niveau de prix = FIFO.
    - Bids triés par prix décroissant ; asks par prix croissant.

    Champs utiles :
        order.id, order.side, order.price, order.quantity, order.asset

    Args :
        initial_book : État initial (MultiBook, généralement vide).
        orders : Séquence d'ordres entrants à traiter.

    Returns :
        État final du MultiBook après traitement de tous les ordres.
    """

    for order in orders:
        """chaque order.asset routé vers son propre carnet"""
        book = initial_book.get_or_create(order.asset)
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