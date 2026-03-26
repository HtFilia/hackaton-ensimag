from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order
from submissions.dalton.moteur import Moteur


def process_orders(livre_initial: MultiBook, ordres: Iterable[Order]) -> MultiBook:
    return Moteur().traiter_ordres(livre_initial, ordres)
