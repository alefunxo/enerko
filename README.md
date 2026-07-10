# Enerko — Courbes de charge

Site statique GitHub Pages de la coopérative solaire Enerko : présentation de la coopérative
et visualisation des courbes de charge (injection réseau et production) de ses installations
photovoltaïques.

## Principe

Les données brutes (CSV SIG) restent **strictement locales** et ne sont jamais publiées.
Seuls les graphiques (PNG) générés et les pages HTML sont commités dans `docs/`.

Le site (`docs/*.html`) est **statique et édité à la main** — ce n'est plus généré. Le
pipeline Python ne produit que les **données et les graphiques** que les pages référencent :

```
CSV bruts (local)
    │
    ▼ 01_parse.py
Parquets (local, ignorés par git)
    │
    ▼ 02_aggregate.py
Agrégats mensuels / annuels / profils + completeness.json (local)
    │
    ▼ 03_charts.py
PNG dans docs/assets/charts/  ── commités → référencés par les pages statiques → GitHub Pages
```

> Le pipeline s'arrête aux graphiques. Une ancienne étape `04_build_html.py` générait les
> pages depuis `config.py` ; elle a été retirée quand la refonte « Signal » est devenue le
> site officiel, statique.

## Structure

```
Enerko/
├── scripts/
│   ├── config.py          ← source de vérité des DONNÉES (quel CSV → quel site/type, couleurs)
│   ├── 01_parse.py        ← lecture des CSV → Parquets
│   ├── 02_aggregate.py    ← calcul des agrégats + completeness.json
│   ├── 03_charts.py       ← génération des PNG → docs/assets/charts/
│   └── build.py           ← pipeline complet (données → graphiques)
├── docs/                  ← racine GitHub Pages (commité)
│   ├── index.html         ← accueil
│   ├── enerko.html · equipe.html · installations.html
│   ├── installation-soubeyran.html · installation-meyrin.html · installation-plan-les-ouates.html
│   ├── autoconsommer.html · investir.html · devenir-membre.html · contact.html · liens.html
│   ├── styles.css
│   └── assets/
│       ├── charts/        ← PNG générés par le pipeline (+ charts/partners/, logos partenaires)
│       ├── fonts/         ← polices auto-hébergées
│       ├── logos/ · photos/
│       └── data/completeness.json  ← généré, non consommé au runtime (badges codés en dur)
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
2. Calcul des agrégats → `processed/aggregates/*.parquet` + `docs/assets/data/completeness.json`
3. Génération des graphiques → `docs/assets/charts/*.png`

Durée indicative : quelques secondes à quelques minutes selon la machine.

### Régénérer uniquement les graphiques (sans relire les CSV)

```bash
python scripts/build.py --charts
```

### Modifier le contenu du site

Les pages sont statiques : éditer directement les fichiers `docs/*.html` (et `docs/styles.css`
pour la mise en forme). Il n'y a pas d'étape de génération HTML à relancer.

> Sur cette machine, utiliser le venv du projet : `.venv\Scripts\python.exe scripts\build.py`
> (le `python` système est Miniconda, sans `pyarrow` → échec sur les Parquets).

## Déploiement GitHub Pages

1. *Settings → Pages → Source* : `main` / `docs`
2. Commiter `docs/` après chaque changement (graphiques régénérés ou pages éditées) :
   ```bash
   git add docs/
   git commit -m "Mise à jour du site"
   git push
   ```
3. La page est accessible à `https://<utilisateur>.github.io/<dépôt>/`

## Données des sites (`config.py`)

`scripts/config.py` reste la source de vérité pour les **données** : quel fichier CSV
correspond à quel site et quel type (`consommation` = injection réseau / `production`),
les couleurs des séries, les saisons. Modifier ce fichier puis relancer le pipeline régénère
les graphiques en conséquence. La **copie éditoriale des pages** (noms affichés, chiffres,
textes) vit désormais dans `docs/*.html` et se met à jour à la main.

### Confirmer consommation vs production (sites C et D)

Les sites C et D disposent chacun de deux fichiers CSV ; l'assignation actuelle dans
`config.py` est une hypothèse à confirmer. Pour inverser, échanger les deux UUID dans
`files`, puis relancer le pipeline complet.

## Graphiques produits

| Graphique | Description |
|---|---|
| `timeline.png` | Chronologie Gantt des installations (2017–2026) |
| `annual_overview_{type}.png` | Totaux annuels par site, empilés (MWh) |
| `{site}_monthly_{type}.png` | Évolution mensuelle — une courbe par année |
| `{site}_typical_day_{type}.png` | Profil 15 min moyen par saison (kW) |
| `{site}_heatmap_{type}.png` | Carte thermique heure × jour de l'année |

`{type}` vaut `consommation` ou `production`. Tous les PNG sont écrits dans `docs/assets/charts/`.
