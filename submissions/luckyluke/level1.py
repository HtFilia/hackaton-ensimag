from __future__ import annotations
from typing import Iterable
from src.common.models import MultiBook, Order, Side

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
            
            if (order.side == Side.BUY and order.price >= best_opp.price) or \
               (order.side == Side.SELL and order.price <= best_opp.price):
                
                trade_qty = min(order.quantity, best_opp.quantity)
                order.quantity -= trade_qty
                best_opp.quantity -= trade_qty
                
                if best_opp.quantity <= 0:
                    opposite_side.orders.pop(0)
            else:
                break

        if order.quantity > 0:
            own_side.orders.append(order)
            own_side.orders.sort(key=lambda x: x.price, reverse=reverse_sort)

    return initial_book

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
