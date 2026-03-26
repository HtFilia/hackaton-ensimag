from __future__ import annotations

import bisect
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Iterable, Optional

from src.common.models import MultiBook, Order, Side, OrderType, Action


class ResumeOrdre(Enum):
    LIMITE = "limit"
    MARCHE = "market"
    NOUVEAU = "NEW"
    ANNULATION = "CANCEL"
    MODIFICATION = "AMEND"
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
    __slots__ = ("offres", "demandes", "index")

    def __init__(self):
        self.offres: List[EntreeCarnet] = []
        self.demandes: List[EntreeCarnet] = []
        self.index: Dict[str, EntreeCarnet] = {}

    def inserer(self, entree: EntreeCarnet):
        if entree.cote == Side.BUY:
            bisect.insort(self.offres, entree, key=_cle_offre)
        else:
            bisect.insort(self.demandes, entree, key=_cle_demande)
        self.index[entree.id_ordre] = entree

    def supprimer(self, id_ordre: str) -> Optional[EntreeCarnet]:
        entree = self.index.pop(id_ordre, None)
        if entree is None:
            return None
        if entree.cote == Side.BUY:
            self.offres.remove(entree)
        else:
            self.demandes.remove(entree)
        return entree


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
                carnet.inserer(self._creer_entree(ordre))
            for ordre in livre.asks.orders:
                carnet.inserer(self._creer_entree(ordre))

    def _prix_compatible(self, entree: EntreeCarnet, meilleur: EntreeCarnet) -> bool:
        if entree.type_ordre == OrderType.MARKET:
            return True
        if entree.cote == Side.BUY:
            return meilleur.prix <= entree.prix
        return meilleur.prix >= entree.prix

    def _executer_matching(self, entree: EntreeCarnet, carnet: CarnetActif):
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
                carnet.index.pop(meilleur.id_ordre, None)

    def _executer_ordre(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        entree = self._creer_entree(ordre)
        self._executer_matching(entree, carnet)
        if entree.quantite > 0 and ordre.order_type != OrderType.MARKET:
            carnet.inserer(entree)

    def _annuler(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        carnet.supprimer(ordre.id)

    def _modifier(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        ancien = carnet.supprimer(ordre.id)
        if ancien is None:
            return
        nouvel_ordre = Order(
            id=ancien.id_ordre, side=ancien.cote,
            price=ordre.price, quantity=ordre.quantity,
            asset=ancien.actif, order_type=ancien.type_ordre,
        )
        self._executer_ordre(nouvel_ordre)

    def _traiter_ordre(self, ordre: Order):
        if ordre.action == Action.CANCEL:
            self._annuler(ordre)
        elif ordre.action == Action.AMEND:
            self._modifier(ordre)
        else:
            self._executer_ordre(ordre)

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
