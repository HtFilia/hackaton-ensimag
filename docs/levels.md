# Spécifications des Paliers

Tous les paliers utilisent la signature :

```python
def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
```

Les ordres sont routés par `order.asset` vers des carnets indépendants par actif dans le `MultiBook`.

---

## Palier 1 — Ordres Limite de Base

**Types autorisés** : LIMIT

### Règles
- Les ordres BUY matchent contre les asks (prix le plus bas en premier) si `ask.price <= buy.price`.
- Les ordres SELL matchent contre les bids (prix le plus haut en premier) si `bid.price >= sell.price`.
- Exécutions partielles : le reste repose dans le carnet.
- Priorité prix-temps : FIFO au sein d'un niveau de prix.
- Bids triés par prix décroissant ; asks par prix croissant.

### Champs concernés
`order.id`, `order.side`, `order.price`, `order.quantity`, `order.asset`

---

## Palier 2 — Ordres au Marché

**Types autorisés** : LIMIT, MARKET

### Règles
- Les ordres MARKET (`order.order_type == "market"`) s'exécutent immédiatement à n'importe quel prix disponible.
- Les ordres MARKET ne reposent **pas** dans le carnet ; la quantité non exécutée est annulée.
- Les ordres LIMIT se comportent comme au Palier 1.

### Champs concernés
`order.order_type` — `"limit"` ou `"market"`

---

## Palier 3 — Annulation et Modification

**Types autorisés** : LIMIT, MARKET
**Actions autorisées** : NEW, CANCEL, AMEND

### Règles
- **NEW** (par défaut) : traitement normal de l'ordre comme au Palier 2.
- **CANCEL** : supprime l'ordre reposant dont `id == order.id` du carnet. Ignorer silencieusement si introuvable.
- **AMEND** : met à jour le prix et/ou la quantité d'un ordre existant.
  Sémantique : annuler + réinsérer (perte de priorité temporelle).
  L'ordre modifié peut croiser immédiatement le carnet si le nouveau prix le permet.
  Seuls le prix et la quantité changent ; le côté et le type d'ordre sont préservés.

Note : pour CANCEL/AMEND, `order.id` désigne l'ordre cible dans le carnet.

### Champs concernés
`order.action` — `"NEW"`, `"CANCEL"` ou `"AMEND"`

---

## Palier 4 — IOC et FOK

**Types autorisés** : LIMIT, MARKET
**Actions autorisées** : NEW, CANCEL, AMEND
**Durées de validité autorisées** : GTC, IOC, FOK

### Règles
- **GTC** (Good-Till-Cancelled, par défaut) : repose dans le carnet si non exécuté.
- **IOC** (Immediate-or-Cancel) : exécuter autant que possible immédiatement ; annuler le reste. La portion non exécutée n'est jamais ajoutée au carnet.
- **FOK** (Fill-or-Kill) : la totalité de la quantité doit être immédiatement exécutable, sinon l'ordre est rejeté entièrement. Vérifier la liquidité disponible **avant** d'exécuter quoi que ce soit.

### Champs concernés
`order.time_in_force` — `"GTC"`, `"IOC"` ou `"FOK"`

---

## Palier 5 — Ordres Iceberg

**Types autorisés** : LIMIT, MARKET, ICEBERG (= LIMIT avec visible_quantity)
**Actions autorisées** : NEW, CANCEL, AMEND
**Durées de validité autorisées** : GTC, IOC, FOK

### Règles
- Quand `order.visible_quantity` est défini, seule cette portion est visible dans le carnet.
- La totalité de `order.quantity` est disponible pour le matching.
- Quand la tranche visible est consommée, la tranche suivante est rechargée depuis le total restant (même position dans le carnet — pas de perte de priorité).
- Si la quantité restante < `visible_quantity`, la portion visible égale la quantité restante.
- AMEND sur un iceberg modifie la quantité totale ; `visible_quantity` est préservé (plafonné si nécessaire).

### Champs concernés
`order.visible_quantity` — `Optional[float]`, `None` signifie pas d'iceberg

---

## Palier 6 — Enchère de Clôture (LOC, MOC, CLOSE)

**Types autorisés** : LIMIT, MARKET, ICEBERG, LOC, MOC
**Actions autorisées** : NEW, CANCEL, AMEND, CLOSE
**Durées de validité autorisées** : GTC, IOC, FOK

### Règles

**LOC (Limit-on-Close)** : mis en file pour la prochaine enchère de clôture. Ne matche PAS dans le carnet continu.

**MOC (Market-on-Close)** : identique à LOC mais au prix du marché (pas de contrainte de prix dans l'enchère).

**CLOSE** (`action == "CLOSE"`) : déclenche l'enchère de clôture pour l'actif donné (`order.asset`).

### Algorithme d'enchère de clôture (décroisement max-volume)

1. Collecter tous les ordres LOC et MOC en attente pour l'actif.
2. Trouver le prix d'équilibre `P*` qui maximise `min(volume_achat, volume_vente)` :
   - Prix candidats = tous les prix des ordres LOC
   - `volume_achat(P)`  = qty des MOC achat + qty des LOC achat avec `price >= P`
   - `volume_vente(P)` = qty des MOC vente + qty des LOC vente avec `price <= P`
3. Exécuter les ordres à `P*` (MOC en premier, puis LOC par meilleur prix, puis FIFO).
4. **Annuler** tous les LOC/MOC restants pour cet actif (dont les partiellement exécutés).
5. Le carnet LIMIT continu n'est pas affecté.

Départage lorsque plusieurs prix donnent le même volume maximum : préférer le prix le plus proche du dernier prix échangé sur le marché continu.

CANCEL/AMEND peuvent cibler des ordres dans la file d'enchère.

### Champs concernés
`order.order_type` — `"loc"` ou `"moc"`
`order.action` — `"CLOSE"`
