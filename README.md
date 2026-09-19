# IoT-MCDM-PFA2 — Sélection de réseau IoT par AHP-TOPSIS

Outil en ligne de commande (Python) d'aide à la décision multicritère : il classe six technologies réseau IoT selon un scénario d'usage, en combinant deux méthodes MCDM.

Projet réalisé dans le cadre du PFA (projet de fin d'année), ENSA El Jadida.

## Principe

1. **AHP** (*Analytic Hierarchy Process*) — à partir d'une matrice de comparaisons par paires (échelle de Saaty 1–9), calcule le poids de chaque critère et vérifie la cohérence des jugements (ratio de cohérence CR, seuil 0,10).
2. **TOPSIS** — normalise la matrice de décision, applique les poids AHP, calcule la distance de chaque alternative à la solution idéale / anti-idéale et en déduit un coefficient de proximité `Ci` qui donne le classement.

## Ce qui est comparé

- **Alternatives (6)** : LoRaWAN, Sigfox, NB-IoT, LTE-M, Wi-Fi, BLE
- **Critères (5)** : consommation d'énergie (min), portée (max), débit (max), coût annuel (min), latence (min)
- **Scénarios prédéfinis** : agriculture intelligente, usine intelligente, ville intelligente (suivi d'actifs) — plus un scénario personnalisé où l'on saisit soi-même la matrice de comparaisons (les fractions du type `1/3` sont acceptées)

## Organisation du code

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée : choix du scénario, enchaînement AHP → TOPSIS, affichage, graphique |
| `ahp.py` | Calcul des poids, λ_max, CI/CR, validation de la matrice, saisie manuelle |
| `topsis.py` | Normalisation, matrice pondérée, solutions idéales, distances, classement |
| `chart.py` | Diagramme en barres des scores `Ci`, exporté dans `ranking_chart.png` |
| `data/networks.py` | Matrice de décision, métadonnées des critères et matrices des scénarios |

Les données sont isolées dans `data/networks.py` : ajouter un réseau ou modifier une valeur ne demande pas de toucher au moteur de calcul.

## Utilisation

```bash
pip install -r requirements.txt
python3 main.py
```

Le programme propose ensuite de choisir un scénario, d'afficher (ou non) les matrices intermédiaires, puis de générer le graphique.

Exemple, scénario 1 (agriculture intelligente) : poids AHP cohérents (CR ≈ 0,024), portée et énergie dominantes, et classement TOPSIS avec Sigfox en tête (`Ci` ≈ 0,875), suivi de LoRaWAN (≈ 0,441).

## Limites

- Les valeurs de `DECISION_MATRIX` sont des ordres de grandeur écrits en dur dans `data/networks.py` ; le code n'en cite pas de source précise. Le classement n'a de sens que pour ces données.
- Pas de tests automatisés.
- `requirements.txt` liste aussi `pandas` et `tabulate`, que le code actuel n'importe pas.
