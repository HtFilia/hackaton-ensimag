from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, Side, OrderType, Action, TimeInForce, OrderBook


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    for order in orders:
        book = initial_book.get_or_create(order.asset)

        if order.action == Action.CANCEL:
            book.bids.orders = [o for o in book.bids.orders if o.id != order.id]
            book.asks.orders = [o for o in book.asks.orders if o.id != order.id]
            continue

        elif order.action == Action.AMEND:
            exist = False
            for o in book.bids.orders + book.asks.orders:
                if o.id == order.id:
                    exist = True
                    break
            if exist:
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
                if best_opp.visible_quantity is not None:
                    best_opp.visible_quantity = min(best_opp.quantity, best_opp.visible_quantity)
                if best_opp.quantity <= 0:
                    opposite_side.orders.pop(0)
            else:
                break

        # ajout de GTC en plus
        if order.time_in_force == TimeInForce.GTC:
            if order.order_type == OrderType.LIMIT and order.quantity > 0:
                if order.visible_quantity is not None:
                    order.visible_quantity = min(order.quantity, order.visible_quantity)
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



"""Palier 5 — Ordres Iceberg

Étendez votre moteur avec les ordres à quantité cachée via order.visible_quantity.

Règles :
- Quand order.visible_quantity est défini, seule cette portion est visible dans le carnet.
- La totalité de order.quantity est disponible pour le matching (profondeur cachée incluse).
- Quand la tranche visible est consommée, la tranche suivante est rechargée automatiquement
    depuis le total restant, en conservant la même priorité prix-temps.
- Si la quantité restante est inférieure à visible_quantity, la portion visible égale le reste.
- AMEND sur un iceberg modifie le prix et la quantité totale ; visible_quantity est préservé
    (plafonné au nouveau total si nécessaire).
- Les ordres sans visible_quantity se comportent comme des ordres limite normaux.
- Toutes les fonctionnalités du Palier 4 restent applicables.

Champs utiles :
    order.visible_quantity  — Optional[float], None signifie pas d'iceberg

Args :
    initial_book : État initial (MultiBook).
    orders : Séquence d'ordres entrants.

Returns :
    État final du MultiBook.
"""
