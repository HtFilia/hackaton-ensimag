from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, OrderBook


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
        if(order.side == 'buy'):
            best_ask = book.asks.best()
            if(best_ask!=None and order.price >= best_ask.price):

                if(order.quantity >= best_ask.quantity):
                    order.quantity -= best_ask.quantity
                    book.bids.add(order)
                    book.asks.orders.remove(best_ask) 

                else:
                
                    best_ask.quantity -= order.quantity

            else:
                book.bids.add(order)


        else:
            best_bid = book.bids.best()
                
            if(best_bid!=None and order.price <= best_bid.price):
                if(order.quantity >= best_bid.quantity):
                     order.quantity -= best_ask.quantity
                     book.asks.add(order)
                     book.bids.orders.remove(best_bid)

                else:
                
                    best_bid.quantity -= order.quantity


            else:
                book.asks.add(order)

    return initial_book  




# def procees_book(order_book: OrderBook) -> OrderBook:

#     best_bid = order_book.bids.best()
#     best_ask = order_book.asks.best()
#     snap = order_book.snapshot()
#     while best_bid != None or best_ask != None:
#         if best_bid.price >= best_ask.price:

#             if best_bid.quantity > best_ask.quantity:
#                 best_bid.quantity = best_bid.quantity - best_ask.quantity
#                 best_ask.quantity = 0
#                 order_book.asks.orders.remove(best_ask)
#                 best_ask = order_book.asks.best()

#             elif best_bid.quantity < best_ask.quantity:
#                 best_ask.quantity = best_ask.quantity - best_bid.quantity 
#                 best_bid.quantity = 0
#                 order_book.bids.orders.remove(best_bid)
#                 best_bid = order_book.bids.best()

#             else:
#                 order_book.bids.orders.remove(best_bid)
#                 order_book.asks.orders.remove(best_ask)
#                 best_ask = order_book.asks.best()
#                 best_bid = order_book.bids.best()

#         else:











#     ×#return order_book

