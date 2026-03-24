# Hackathon Flash Trading — Carnet d'Ordres

Bienvenue ! Votre objectif est de construire un moteur de carnet d'ordres performant et déterministe, qui évolue à travers 6 paliers de complexité croissante.

## Démarrage rapide

### Prérequis
- Python 3.11+
- Node.js (pour le dashboard)

### Enregistrement

```bash
make register
```

Cette commande vous guide pas à pas : elle crée l'environnement Python, vous permet de choisir votre équipe dans la liste, bascule sur votre branche git et installe les hooks automatiquement.

## Guide de participation

### 1. Les paliers

Tous les paliers utilisent la même signature :

```python
def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
```

| Palier | Concept | Nouveautés |
|--------|---------|------------|
| 1 | Ordres limite de base | Ordres LIMIT, priorité prix-temps |
| 2 | Ordres au marché | Ordres MARKET (non placés si non exécutés) |
| 3 | Annulation et modification | CANCEL supprime ; AMEND = annuler + réinsérer |
| 4 | IOC et FOK | IOC exécute puis annule le reste ; FOK tout-ou-rien |
| 5 | Ordres iceberg | `visible_quantity` cache la profondeur ; rechargement automatique |
| 6 | Enchère de clôture | LOC/MOC en file jusqu'au CLOSE → décroisement max-volume |

Voir `docs/levels.md` pour les spécifications complètes.

### 2. Workflow

1. **S'enregistrer** : `make register` — à faire une seule fois au début.
2. **Implémenter** : écrivez votre solution dans `submissions/<votre_equipe>/level1.py` jusqu'à `level6.py`.
3. **Tester** : `make test` ou `make test LEVEL=N` pour valider sur les tests publics (sortie terminal).
4. **Voir sa progression** : `make web` lance le dashboard live avec résultats mis à jour toutes les 5s.
5. **Soumettre** : `git commit` puis `git push origin <votre_equipe>` pour envoyer au classement.

```bash
make register              # première fois seulement
make test                  # tous les tests publics (terminal)
make test LEVEL=3          # un palier spécifique
make web                   # dashboard live
make clean                 # arrêter les processus en arrière-plan
git push origin <equipe>   # soumettre au classement
```

## Notation

Les équipes sont classées par :
1. **Palier le plus élevé réussi** (les paliers 1 à N doivent tous passer consécutivement)
2. **Première équipe à valider ce palier** (horodatage machine organisateur)
3. **Nombre total de fixtures réussies** (deuxième départage)

## Règles

1. **Déterminisme** : votre moteur doit être déterministe. Pas de graine aléatoire ni d'heure système.
2. **Performance** : chaque fixture a un timeout de 5 secondes.
3. **Pas de secrets** : ne commitez pas de clés API ou autres secrets.
4. **Style de code** : PEP 8 recommandé.

## Dépannage

- Vérifiez le message d'erreur dans la sortie des tests.
- Assurez-vous que votre implémentation gère les cas limites (exécutions partielles, carnets vides).
- Consultez `submissions/_template/` pour les signatures de fonctions correctes.
- Lisez `docs/levels.md` pour les spécifications détaillées.

Bonne chance !
