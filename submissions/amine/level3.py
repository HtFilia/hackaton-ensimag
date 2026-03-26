

from __future__ import annotations

from copy import copy
from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side

from .level2 import initialize_book, insert_order, match_book


def get_side(book: OrderBook, side: Side):
    if side == Side.BUY:
        return book.asks, book.bids
    return book.bids, book.asks


def process_new_order(multibook: MultiBook, order: Order) -> None:
    book = multibook.books.get(order.asset)

    if book is None and order.order_type == OrderType.MARKET:
        return
    if book is None:
        book = multibook.get_or_create(order.asset)

    opposing_side , resting_side = get_side(book, order.side)
    match_book(opposing_side, order)

    if order.quantity > 0 and order.order_type != OrderType.MARKET:
        insert_order(resting_side, order)


def pop_order(book: OrderBook, order_id: str) -> Order | None:
    for side in (book.bids, book.asks):
        for index, resting_order in enumerate(side.orders):
            if resting_order.id == order_id:
                return side.orders.pop(index)
    return None


def amend_order(original: Order, request: Order) -> Order:
    amended = copy(original)

    if request.price not in (None, 0):
        amended.price = request.price
    if request.quantity not in (None, 0):
        amended.quantity = request.quantity

    amended.action = Action.NEW
    return amended


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
    initialize_book(initial_book)

    for order in orders:
        if order.action == Action.NEW:
            process_new_order(initial_book, order)
            continue

        book = initial_book.books.get(order.asset)
        if book is None:
            continue

        if order.action == Action.CANCEL:
            pop_order(book, order.id)
            continue

        if order.action == Action.AMEND:
            original = pop_order(book, order.id)
            if original is None:
                continue

            amended = amend_order(original, order)
            process_new_order(initial_book, amended)

    return initial_book
