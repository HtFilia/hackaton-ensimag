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
        remaining_qty = order.quantity
        
        if order.side == Side.BUY:
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