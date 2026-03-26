from __future__ import annotations

from typing import Iterable
from bisect import insort

from src.common.models import MultiBook, Order


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
    book = initial_book.get_or_create(Order.asset)
    for order in orders : 
        orders_match(order, book)
    return initial_book
    
def orders_match(order : Order, book : OrderBook):
    if order.side==Side.buy:
        while order.quantity>0 and book.asks.order:
            best_ask=book.asks.best
            if best_ask.price>order.price:
                break
            quantity_gone=min(order.quantity, best_ask.price)
            order.quantity-=quantity_gone
            best_ask.quantity-=quantity_gone
            if best_ask.quantity==0:
                book.asks.pop(0)
        if order.quantity>0:
           insort(book.bids.order, order, key= lambda o : o.price, reverse = True)
    else :
        while order.quantity>0 and book.bids.order:
            best_bid=book.bids.best
            if best_bid.price<order.price:
                break
            quantity_gone=min(order.quantity, best_bid.price)
            order.quantity-=quantity_gone
            best_bid.quantity-=quantity_gone
            if best_bid.quantity==0:
                book.bids.pop(0)
        if order.quantity>0:
           insort(book.asks.order, order, key= lambda o : o.price)


        
    

    
        
