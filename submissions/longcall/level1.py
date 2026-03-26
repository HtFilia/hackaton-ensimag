from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side, BookSide
from src.common.models import *


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
    # raise NotImplementedError("Implémenter le Palier 1 : Ordres Limite de Base")
