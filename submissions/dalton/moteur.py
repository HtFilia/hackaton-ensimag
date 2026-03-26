from __future__ import annotations

import bisect
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Iterable, Optional

from src.common.models import (
    MultiBook, Order, Side, OrderType, Action, TimeInForce
)


class ResumeOrdre(Enum):
    LIMITE = "limit"
    MARCHE = "market"
    ANNULATION = "CANCEL"
    MODIFICATION = "AMEND"
    NOUVEAU = "NEW"
    IMMEDIAT_OU_ANNULE = "IOC"
    TOUT_OU_RIEN = "FOK"
    VALABLE_ANNULATION = "GTC"
    ICEBERG = "iceberg"
    MARCHE_CLOTURE = "moc"
    LIMITE_CLOTURE = "loc"
    CLOTURE = "CLOSE"
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
    quantite_visible: Optional[float] = None
    quantite_min: Optional[float] = None
    pic_iceberg: Optional[float] = None

    def maj_quantite_visible(self):
        if self.quantite_visible is None:
            return
        if self.pic_iceberg is None:
            self.pic_iceberg = self.quantite_visible
        self.quantite_visible = min(self.pic_iceberg, self.quantite)


def _cle_offre(entree: EntreeCarnet):
    return (entree.prix, -entree.horodatage)


def _cle_demande(entree: EntreeCarnet):
    return (-entree.prix, -entree.horodatage)


class CarnetActif:
    __slots__ = ("offres", "demandes", "index", "dernier_prix")

    def __init__(self):
        self.offres: List[EntreeCarnet] = []
        self.demandes: List[EntreeCarnet] = []
        self.index: Dict[str, EntreeCarnet] = {}
        self.dernier_prix: Optional[float] = None

    def inserer_offre(self, entree: EntreeCarnet):
        bisect.insort(self.offres, entree, key=_cle_offre)
        self.index[entree.id_ordre] = entree

    def inserer_demande(self, entree: EntreeCarnet):
        bisect.insort(self.demandes, entree, key=_cle_demande)
        self.index[entree.id_ordre] = entree

    def inserer(self, entree: EntreeCarnet):
        if entree.cote == Side.BUY:
            self.inserer_offre(entree)
        else:
            self.inserer_demande(entree)

    def supprimer(self, id_ordre: str) -> Optional[EntreeCarnet]:
        entree = self.index.pop(id_ordre, None)
        if entree is None:
            return None
        if entree.cote == Side.BUY:
            self.offres.remove(entree)
        else:
            self.demandes.remove(entree)
        return entree


class FileEnchere:
    __slots__ = ("ordres", "index")

    def __init__(self):
        self.ordres: List[EntreeCarnet] = []
        self.index: Dict[str, EntreeCarnet] = {}

    def ajouter(self, entree: EntreeCarnet):
        self.ordres.append(entree)
        self.index[entree.id_ordre] = entree

    def supprimer(self, id_ordre: str) -> Optional[EntreeCarnet]:
        entree = self.index.pop(id_ordre, None)
        if entree is None:
            return None
        self.ordres.remove(entree)
        return entree

    def vider(self):
        self.ordres.clear()
        self.index.clear()


class Moteur:
    __slots__ = ("carnets", "files_enchere", "compteur")

    def __init__(self):
        self.carnets: Dict[str, CarnetActif] = {}
        self.files_enchere: Dict[str, FileEnchere] = {}
        self.compteur: int = 0

    def traiter_ordres(self, multi_carnet_initial: MultiBook, ordres: Iterable[Order]) -> MultiBook:
        self._charger_etat_initial(multi_carnet_initial)
        for ordre in ordres:
            self._traiter_ordre(ordre)
        return self._construire_resultat()

    def _obtenir_carnet(self, actif: str) -> CarnetActif:
        carnet = self.carnets.get(actif)
        if carnet is None:
            carnet = CarnetActif()
            self.carnets[actif] = carnet
        return carnet

    def _obtenir_file(self, actif: str) -> FileEnchere:
        file = self.files_enchere.get(actif)
        if file is None:
            file = FileEnchere()
            self.files_enchere[actif] = file
        return file

    def _prochain_horodatage(self) -> int:
        self.compteur += 1
        return self.compteur

    def _creer_entree(self, ordre: Order, horodatage: int) -> EntreeCarnet:
        return EntreeCarnet(
            id_ordre=ordre.id,
            cote=ordre.side,
            prix=ordre.price,
            quantite=ordre.quantity,
            actif=ordre.asset,
            type_ordre=ordre.order_type,
            horodatage=horodatage,
            quantite_visible=ordre.visible_quantity,
            quantite_min=ordre.min_quantity,
            pic_iceberg=ordre.visible_quantity,
        )

    def _charger_etat_initial(self, multi_carnet: MultiBook):
        for actif, livre in multi_carnet.books.items():
            carnet = self._obtenir_carnet(actif)
            for ordre in livre.bids.orders:
                entree = self._creer_entree(ordre, self._prochain_horodatage())
                entree.maj_quantite_visible()
                carnet.inserer_offre(entree)
            for ordre in livre.asks.orders:
                entree = self._creer_entree(ordre, self._prochain_horodatage())
                entree.maj_quantite_visible()
                carnet.inserer_demande(entree)

    def _vers_order(self, entree: EntreeCarnet) -> Order:
        return Order(
            id=entree.id_ordre,
            side=entree.cote,
            price=entree.prix,
            quantity=entree.quantite,
            asset=entree.actif,
            order_type=entree.type_ordre,
            min_quantity=entree.quantite_min,
            visible_quantity=entree.quantite_visible,
        )

    def _construire_resultat(self) -> MultiBook:
        resultat = MultiBook()
        for actif, carnet in self.carnets.items():
            livre = resultat.get_or_create(actif)
            for entree in reversed(carnet.offres):
                livre.bids.add(self._vers_order(entree))
            for entree in reversed(carnet.demandes):
                livre.asks.add(self._vers_order(entree))
        return resultat

    def _prix_compatible(self, entree_entrante: EntreeCarnet, entree_carnet: EntreeCarnet) -> bool:
        if entree_entrante.type_ordre == OrderType.MARKET:
            return True
        if entree_entrante.cote == Side.BUY:
            return entree_carnet.prix <= entree_entrante.prix
        return entree_carnet.prix >= entree_entrante.prix

    def _cote_opposee(self, carnet: CarnetActif, cote: Side) -> List[EntreeCarnet]:
        if cote == Side.BUY:
            return carnet.demandes
        return carnet.offres

    def _verifier_liquidite(self, entree: EntreeCarnet, cote_opposee: List[EntreeCarnet]) -> bool:
        quantite_restante = entree.quantite
        for ordre_carnet in reversed(cote_opposee):
            if not self._prix_compatible(entree, ordre_carnet):
                break
            quantite_restante -= ordre_carnet.quantite
            if quantite_restante <= 0:
                return True
        return False

    def _executer_matching(self, entree: EntreeCarnet, carnet: CarnetActif):
        opposee = self._cote_opposee(carnet, entree.cote)
        while entree.quantite > 0 and opposee:
            meilleur = opposee[-1]
            if not self._prix_compatible(entree, meilleur):
                break
            quantite_echange = min(entree.quantite, meilleur.quantite)
            entree.quantite -= quantite_echange
            meilleur.quantite -= quantite_echange
            carnet.dernier_prix = meilleur.prix
            if meilleur.quantite <= 0:
                opposee.pop()
                carnet.index.pop(meilleur.id_ordre, None)
            else:
                meilleur.maj_quantite_visible()

    def _executer_ordre(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        entree = self._creer_entree(ordre, self._prochain_horodatage())

        if ordre.time_in_force == TimeInForce.FOK:
            opposee = self._cote_opposee(carnet, entree.cote)
            if not self._verifier_liquidite(entree, opposee):
                return

        self._executer_matching(entree, carnet)

        if entree.quantite > 0:
            if ordre.time_in_force == TimeInForce.GTC and ordre.order_type != OrderType.MARKET:
                entree.maj_quantite_visible()
                carnet.inserer(entree)

    def _traiter_ordre(self, ordre: Order):
        if ordre.action == Action.CANCEL:
            self._annuler(ordre)
        elif ordre.action == Action.AMEND:
            self._modifier(ordre)
        elif ordre.action == Action.CLOSE:
            self._declencher_cloture(ordre.asset)
        else:
            self._nouveau(ordre)

    def _nouveau(self, ordre: Order):
        if ordre.order_type in (OrderType.LOC, OrderType.MOC):
            self._ajouter_file_enchere(ordre)
        else:
            self._executer_ordre(ordre)

    def _annuler(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        resultat = carnet.supprimer(ordre.id)
        if resultat is None:
            file = self._obtenir_file(ordre.asset)
            file.supprimer(ordre.id)

    def _modifier(self, ordre: Order):
        carnet = self._obtenir_carnet(ordre.asset)
        ancien = carnet.supprimer(ordre.id)
        dans_file = False
        if ancien is None:
            file = self._obtenir_file(ordre.asset)
            ancien = file.supprimer(ordre.id)
            dans_file = True
        if ancien is None:
            return

        quantite_visible = ancien.pic_iceberg if ancien.pic_iceberg is not None else ancien.quantite_visible

        nouvel_ordre = Order(
            id=ancien.id_ordre,
            side=ancien.cote,
            price=ordre.price,
            quantity=ordre.quantity,
            asset=ancien.actif,
            order_type=ancien.type_ordre,
            min_quantity=ancien.quantite_min,
            visible_quantity=quantite_visible,
        )

        if dans_file:
            self._ajouter_file_enchere(nouvel_ordre)
        else:
            self._executer_ordre(nouvel_ordre)

    def _ajouter_file_enchere(self, ordre: Order):
        file = self._obtenir_file(ordre.asset)
        entree = self._creer_entree(ordre, self._prochain_horodatage())
        file.ajouter(entree)

    def _declencher_cloture(self, actif: str):
        file = self._obtenir_file(actif)
        if not file.ordres:
            return

        carnet = self._obtenir_carnet(actif)

        achats_moc = [e for e in file.ordres if e.cote == Side.BUY and e.type_ordre == OrderType.MOC]
        ventes_moc = [e for e in file.ordres if e.cote == Side.SELL and e.type_ordre == OrderType.MOC]
        achats_loc = [e for e in file.ordres if e.cote == Side.BUY and e.type_ordre == OrderType.LOC]
        ventes_loc = [e for e in file.ordres if e.cote == Side.SELL and e.type_ordre == OrderType.LOC]

        prix_candidats = set()
        for e in achats_loc:
            prix_candidats.add(e.prix)
        for e in ventes_loc:
            prix_candidats.add(e.prix)

        if not prix_candidats:
            file.vider()
            return

        vol_moc_achat = sum(e.quantite for e in achats_moc)
        vol_moc_vente = sum(e.quantite for e in ventes_moc)

        meilleur_prix = None
        meilleur_volume = -1

        for p in sorted(prix_candidats):
            vol_achat = vol_moc_achat + sum(e.quantite for e in achats_loc if e.prix >= p)
            vol_vente = vol_moc_vente + sum(e.quantite for e in ventes_loc if e.prix <= p)
            volume = min(vol_achat, vol_vente)
            if volume > meilleur_volume:
                meilleur_volume = volume
                meilleur_prix = p
            elif volume == meilleur_volume and meilleur_prix is not None:
                if carnet.dernier_prix is not None:
                    if abs(p - carnet.dernier_prix) < abs(meilleur_prix - carnet.dernier_prix):
                        meilleur_prix = p

        if meilleur_volume <= 0 or meilleur_prix is None:
            file.vider()
            return

        liste_achats = sorted(
            achats_moc + [e for e in achats_loc if e.prix >= meilleur_prix],
            key=lambda e: (0 if e.type_ordre == OrderType.MOC else 1, -e.prix, e.horodatage)
        )
        liste_ventes = sorted(
            ventes_moc + [e for e in ventes_loc if e.prix <= meilleur_prix],
            key=lambda e: (0 if e.type_ordre == OrderType.MOC else 1, e.prix, e.horodatage)
        )

        volume_restant = meilleur_volume
        idx_achat = 0
        idx_vente = 0

        while volume_restant > 0 and idx_achat < len(liste_achats) and idx_vente < len(liste_ventes):
            achat = liste_achats[idx_achat]
            vente = liste_ventes[idx_vente]
            qte = min(achat.quantite, vente.quantite, volume_restant)
            achat.quantite -= qte
            vente.quantite -= qte
            volume_restant -= qte
            if achat.quantite <= 0:
                idx_achat += 1
            if vente.quantite <= 0:
                idx_vente += 1

        carnet.dernier_prix = meilleur_prix
        file.vider()
