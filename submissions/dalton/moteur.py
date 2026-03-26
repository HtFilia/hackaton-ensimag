from __future__ import annotations

import bisect
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Iterable

from src.common.models import MultiBook, Order, Side, OrderType


class ResumeOrdre(Enum):
    LIMITE = "limit"
    MARCHE = "market"
    ACHAT = "buy"
    VENTE = "sell"


@dataclass
class EntreeCarnet:
    id_ordre: str
    cote: Side
    prix: float
    quantite: float
    actif: str
    type_ordre: OrderType
    horodatage: int


def _cle_offre(e: EntreeCarnet):
    return (e.prix, -e.horodatage)


def _cle_demande(e: EntreeCarnet):
    return (-e.prix, -e.horodatage)


class CarnetActif:
    __slots__ = ("offres", "demandes")

    def __init__(self):
        self.offres: List[EntreeCarnet] = []
        self.demandes: List[EntreeCarnet] = []

    def inserer(self, entree: EntreeCarnet):
        if entree.cote == Side.BUY:
            bisect.insort(self.offres, entree, key=_cle_offre)
        else:
            bisect.insort(self.demandes, entree, key=_cle_demande)


class Moteur:
    __slots__ = ("carnets", "compteur")

    def __init__(self):
        self.carnets: Dict[str, CarnetActif] = {}
        self.compteur: int = 0

    def traiter_ordres(self, livre_initial: MultiBook, ordres: Iterable[Order]) -> MultiBook:
        self._charger_etat_initial(livre_initial)
        for ordre in ordres:
            self._traiter_ordre(ordre)
        return self._construire_resultat()

    def _obtenir_carnet(self, actif: str) -> CarnetActif:
        carnet = self.carnets.get(actif)
        if carnet is None:
            carnet = CarnetActif()
            self.carnets[actif] = carnet
        return carnet

    def _prochain_horodatage(self) -> int:
        self.compteur += 1
        return self.compteur

    def _creer_entree(self, ordre: Order) -> EntreeCarnet:
        return EntreeCarnet(
            ordre.id, ordre.side, ordre.price, ordre.quantity,
            ordre.asset, ordre.order_type, self._prochain_horodatage()
        )

    def _charger_etat_initial(self, multi_carnet: MultiBook):
        for actif, livre in multi_carnet.books.items():
            carnet = self._obtenir_carnet(actif)
            for ordre in livre.bids.orders:
                bisect.insort(carnet.offres, self._creer_entree(ordre), key=_cle_offre)
            for ordre in livre.asks.orders:
                bisect.insort(carnet.demandes, self._creer_entree(ordre), key=_cle_demande)

    def _prix_compatible(self, entree: EntreeCarnet, meilleur: EntreeCarnet) -> bool:
        if entree.type_ordre == OrderType.MARKET:
            return True
        if entree.cote == Side.BUY:
            return meilleur.prix <= entree.prix
        return meilleur.prix >= entree.prix

    def _traiter_ordre(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        entree = self._creer_entree(ordre)
        opposee = carnet.demandes if entree.cote == Side.BUY else carnet.offres

        while entree.quantite > 0 and opposee:
            meilleur = opposee[-1]
            if not self._prix_compatible(entree, meilleur):
                break
            qte = min(entree.quantite, meilleur.quantite)
            entree.quantite -= qte
            meilleur.quantite -= qte
            if meilleur.quantite <= 0:
                opposee.pop()

        if entree.quantite > 0 and ordre.order_type != OrderType.MARKET:
            carnet.inserer(entree)

    def _construire_resultat(self) -> MultiBook:
        resultat = MultiBook()
        for actif, carnet in self.carnets.items():
            livre = resultat.get_or_create(actif)
            for e in reversed(carnet.offres):
                livre.bids.add(Order(
                    id=e.id_ordre, side=e.cote, price=e.prix,
                    quantity=e.quantite, asset=e.actif, order_type=e.type_ordre
                ))
            for e in reversed(carnet.demandes):
                livre.asks.add(Order(
                    id=e.id_ordre, side=e.cote, price=e.prix,
                    quantity=e.quantite, asset=e.actif, order_type=e.type_ordre
                ))
        return resultat
