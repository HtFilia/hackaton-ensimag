from __future__ import annotations
from typing import Iterable
from src.common.models import MultiBook, Order, Action, Side, OrderType, OrderBook, TimeInForce

def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:
        book = initial_book.get_or_create(order.asset)

        if order.action == Action.CANCEL:
            book.bids.orders = [o for o in book.bids.orders if o.id != order.id]
            book.asks.orders = [o for o in book.asks.orders if o.id != order.id]
            continue

        elif order.action == Action.AMEND:
            original = None
            for o in book.bids.orders + book.asks.orders:
                if o.id == order.id:
                    original = o
                    break
            
            if original:
                if not hasattr(order, 'side') or order.side is None:
                    order.side = original.side
                if not hasattr(order, 'order_type') or order.order_type is None:
                    order.order_type = original.order_type
                
                book.bids.orders = [o for o in book.bids.orders if o.id != order.id]
                book.asks.orders = [o for o in book.asks.orders if o.id != order.id]
            else:
                continue
        # Fill or Kill
        if order.time_in_force == TimeInForce.FOK:
            if not can_fill_fok(order, book):
                continue # On rejete l'ordre
                
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

            is_market = (order.order_type == OrderType.MARKET)
            
            price_match = (
                (order.side == Side.BUY and order.price >= best_opp.price) or
                (order.side == Side.SELL and order.price <= best_opp.price)
            )
            
            if is_market or price_match:
                trade_qty = min(order.quantity, best_opp.quantity)
                order.quantity -= trade_qty
                best_opp.quantity -= trade_qty
                
                if best_opp.quantity <= 0:
                    opposite_side.orders.pop(0)
            else:
                break

        if order.order_type == OrderType.LIMIT and order.quantity > 0:
            own_side.orders.append(order)
            own_side.orders.sort(key=lambda x: x.price, reverse=reverse_sort)

        # ajout de GTC en plus
        if order.time_in_force == TimeInForce.GTC:
            if order.order_type == OrderType.LIMIT and order.quantity > 0:
                own_side.orders.append(order)
                own_side.orders.sort(key=lambda x: x.price, reverse=(order.side == Side.BUY))

    return initial_book


def can_fill_fok(order: Order, book: OrderBook) -> bool:
    """Vérification de la liquidité"""
    needed = order.quantity
    opp_orders = book.asks.orders if order.side == Side.BUY else book.bids.orders
    
    for opp in opp_orders:
        if order.order_type == OrderType.LIMIT:
            price_ok = (order.side == Side.BUY and order.price >= opp.price) or \
                       (order.side == Side.SELL and order.price <= opp.price)
            if not price_ok:
                break
        
        needed -= opp.quantity
        if needed <= 0:
            return True
            
    return False

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
