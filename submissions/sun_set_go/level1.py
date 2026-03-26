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
        book = initial_book.get_or_create(order.asset)
        
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
