from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, OrderType, Side, Action, TimeInForce


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    """Palier 4 — IOC et FOK

    Étendez votre moteur avec les contraintes de durée de validité via order.time_in_force.

    Règles :
    - GTC (Good-Till-Cancelled, par défaut) : l'ordre repose dans le carnet s'il n'est pas
      entièrement exécuté.
    - IOC (Immediate-or-Cancel) : exécuter autant que possible immédiatement ; annuler le reste.
      La partie non exécutée n'est jamais ajoutée au carnet.
    - FOK (Fill-or-Kill) : la totalité de la quantité doit être immédiatement exécutable, sinon
      l'ordre est rejeté entièrement. Vérifier la liquidité disponible AVANT d'exécuter quoi que
      ce soit.
    - Toutes les fonctionnalités du Palier 3 (LIMIT, MARKET, CANCEL, AMEND) restent applicables.

    Champs utiles :
        order.time_in_force  — "GTC", "IOC" ou "FOK"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
    
    def check_liquidity(book, order):
        dispo = 0
        if order.order_type == OrderType.MARKET:
            if order.side == Side.BUY:
                dispo = sum(ord.quantity for ord in book.asks.orders)
            else:
                dispo = sum(ord.quantity for ord in book.bids.orders)
        else: 
            if order.side == Side.BUY:
                dispo = sum(ord.quantity for ord in book.asks.orders if ord.price <= order.price)
            else:
                dispo = sum(ord.quantity for ord in book.bids.orders if ord.price >= order.price)
        return dispo >= order.quantity
    
    def add_new_order(book, order):
        if order.time_in_force == TimeInForce.FOK:
            if not check_liquidity(book, order):
                return 
        
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
            
                if order.quantity > 0 and order.time_in_force == TimeInForce.GTC:
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
                
                if order.quantity > 0 and order.time_in_force == TimeInForce.GTC:  
                    book.asks.add(order)
                    book.asks.orders.sort(key=lambda el: el.price)
    
    for order in orders:
        book = initial_book.get_or_create(order.asset)
        
        if (order.action == Action.NEW):
            add_new_order(book,order)
        elif (order.action == Action.CANCEL or order.action == Action.AMEND):
            for i in range(len(book.bids.orders)):
                if book.bids.orders[i].id == order.id:
                    book.bids.orders.pop(i)
                    break
            for i in range(len(book.asks.orders)):
                if book.asks.orders[i].id == order.id:
                    book.asks.orders.pop(i)
                    break
            if (order.action == Action.AMEND):
                add_new_order(book, order)
                
                
    return initial_book

