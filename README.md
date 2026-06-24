# Enerko — Courbes de charge

Page statique GitHub Pages pour visualiser les courbes de charge (consommation et production)
des installations photovoltaïques de la coopérative solaire Enerko.

## Principe

Les données brutes (CSV SIG) restent **strictement locales** et ne sont jamais publiées.
Seuls les graphiques (PNG) et la page HTML générés sont commités dans `docs/`.

```
CSV bruts (local)
    │
    ▼ 01_parse.py
Parquets (local, ignorés par git)
    │
    ▼ 02_aggregate.py
Agrégats mensuels / annuels / profils (local)
    │
    ▼ 03_charts.py
PNG dans docs/assets/images/  ──┐
    │                            ├── commités → GitHub Pages
    ▼ 04_build_html.py           │
docs/index.html ────────────────┘
```

## Structure

```
Enerko/
├── scripts/
│   ├── config.py          ← seul fichier à modifier pour les noms de sites
│   ├── 01_parse.py        ← lecture des CSV → Parquets
│   ├── 02_aggregate.py    ← calcul des agrégats
│   ├── 03_charts.py       ← génération des PNG
│   ├── 04_build_html.py   ← génération de docs/index.html
│   └── build.py           ← pipeline complet
├── docs/                  ← racine GitHub Pages (commité)
│   ├── index.html
│   └── assets/
│       ├── css/style.css
│       └── images/        ← PNG générés
├── .gitignore
├── requirements.txt
└── README.md
```

## Prérequis

```bash
pip install -r requirements.txt
```

Les CSV SIG doivent se trouver à la racine du projet (même dossier que `scripts/`).

## Utilisation

### Pipeline complet (première exécution ou mise à jour des données)

```bash
python scripts/build.py
```

Étapes exécutées :
1. Lecture de tous les CSV → `processed/*.parquet`
2. Calcul des agrégats → `processed/aggregates/*.parquet`
3. Génération des graphiques → `docs/assets/images/*.png`
4. Génération de la page → `docs/index.html`

Durée indicative : 5–15 minutes selon la machine (260 Mo de CSV).

### Mettre à jour uniquement les noms de sites

1. Modifier `scripts/config.py` — champ `"name"` de chaque site
2. Exécuter :
   ```bash
   python scripts/build.py --html
   ```

### Régénérer uniquement les graphiques (sans relire les CSV)

```bash
python scripts/build.py --charts
```

## Déploiement GitHub Pages

1. Créer un dépôt GitHub (ex. `enerko-dashboard`)
2. Aller dans *Settings → Pages → Source* : `main` / `docs`
3. Commiter `docs/` après chaque génération :
   ```bash
   git add docs/
   git commit -m "Mise à jour des graphiques"
   git push
   ```
4. La page est accessible à `https://<utilisateur>.github.io/enerko-dashboard/`

## Mettre à jour les noms de sites

Ouvrir `scripts/config.py` et modifier la clé `"name"` de chaque entrée :

```python
"site_a": {
    "name": "Toiture Carouge",   # ← remplacer "Site A"
    ...
}
```

Puis régénérer le HTML :

```bash
python scripts/build.py --html
git add docs/index.html && git commit -m "Noms de sites mis à jour" && git push
```

## Confirmer consommation vs production (sites C et D)

Les sites C et D disposent chacun de deux fichiers CSV.
L'assignation actuelle dans `config.py` est une hypothèse à confirmer.
Pour inverser :

```python
"site_c": {
    "files": {
        "consommation": "81dac57f-...",   # ← échanger les deux UUID
        "production":   "3cddead9-...",
    }
}
```

Puis relancer le pipeline complet.

## Graphiques produits

| Graphique | Description |
|---|---|
| `timeline.png` | Chronologie Gantt des installations (2017–2026) |
| `annual_overview_{type}.png` | Totaux annuels par site, empilés (MWh) |
| `{site}_monthly_{type}.png` | Évolution mensuelle — une courbe par année |
| `{site}_typical_day_{type}.png` | Profil 15 min moyen par saison (kW) |
| `{site}_heatmap_{type}.png` | Carte thermique heure × jour de l'année |

`{type}` vaut `consommation` ou `production`.
