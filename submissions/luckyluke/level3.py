from __future__ import annotations
from typing import Iterable
from src.common.models import MultiBook, Order, Action, Side, OrderType

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

    return initial_book
    """Palier 3 — Annulation et Modification

    Étendez votre moteur avec la gestion du cycle de vie des ordres via order.action.

    Règles :
    - NEW (par défaut) : traitement normal de l'ordre.
    - CANCEL : supprime l'ordre reposant dont l'id est égal à order.id du carnet.
      Chercher dans les bids et les asks. Ignorer silencieusement si introuvable.
    - AMEND : met à jour le prix et/ou la quantité d'un ordre existant.
      Sémantique : annuler l'ancien ordre puis réinsérer avec les nouvelles valeurs
      (perte de priorité temporelle).
      Si le nouveau prix croise le côté opposé, l'ordre s'exécute immédiatement.
      Seuls le prix et la quantité changent ; le côté et le type d'ordre sont préservés.

    Note : pour CANCEL/AMEND, order.id est l'id de l'ordre à modifier (ref_id dans le CSV).

    Champs utiles :
        order.action  — "NEW", "CANCEL" ou "AMEND"

    Args :
        initial_book : État initial (MultiBook).
        orders : Séquence d'ordres entrants.

    Returns :
        État final du MultiBook.
    """
