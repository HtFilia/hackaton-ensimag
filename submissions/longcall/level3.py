from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order
from src.common.models import *


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
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


    def insert_in_book(side: BookSide, order: Order) -> None:
        """Insert order into BookSide keeping price-time priority.

        Simple approach: linear scan. Bids: descending price; Asks: ascending price.
        FIFO for same price (we append after existing same-price orders).
        """
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
        book = initial_book.get_or_create(order.asset)

        if order.action == Action.CANCEL:
            for side in [book.bids, book.asks]:
                for i, existing in enumerate(side.orders):
                    if existing.id == order.id:
                        side.orders.pop(i)
                        break

        elif order.action == Action.AMEND:
            existing_order = None
            for side in [book.bids, book.asks]:
                for i, ex in enumerate(side.orders):
                    if ex.id == order.id:
                        existing_order = ex
                        side.orders.pop(i)
                        break
                if existing_order is not None:
                    break

            if existing_order is None:
                continue

            new_order = Order(
                id=existing_order.id,
                asset=existing_order.asset,
                side=existing_order.side,
                order_type=existing_order.order_type,
                price=order.price,
                quantity=order.quantity,
            )

            
            if new_order.side == Side.BUY:
                asks = book.asks
                while new_order.quantity > 0:
                    best_ask = asks.best()
                    if best_ask is None:
                        break
                    if best_ask.price <= new_order.price:
                        if new_order.quantity < best_ask.quantity:
                            best_ask.quantity -= new_order.quantity
                            new_order.quantity = 0
                        elif new_order.quantity == best_ask.quantity:
                            new_order.quantity = 0
                            asks.orders.pop(0)
                        else:
                            new_order.quantity -= best_ask.quantity
                            asks.orders.pop(0)
                    else:
                        break
                if new_order.quantity > 0:
                    insert_in_book(book.bids, new_order)

            else:
                bids = book.bids
                while new_order.quantity > 0:
                    best_bid = bids.best()
                    if best_bid is None:
                        break
                    if best_bid.price >= new_order.price:
                        if new_order.quantity < best_bid.quantity:
                            best_bid.quantity -= new_order.quantity
                            new_order.quantity = 0
                        elif new_order.quantity == best_bid.quantity:
                            new_order.quantity = 0
                            bids.orders.pop(0)
                        else:
                            new_order.quantity -= best_bid.quantity
                            bids.orders.pop(0)
                    else:
                        break
                if new_order.quantity > 0:
                    insert_in_book(book.asks, new_order)

        
        else:
            if order.side == Side.BUY:
                asks = book.asks
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
                    insert_in_book(book.bids, order)

            elif order.side == Side.SELL:
                bids = book.bids
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
                    insert_in_book(book.asks, order)



    return initial_book