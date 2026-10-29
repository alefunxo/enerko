# Enerko 

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
    │
    ▼ 04_stats.py
stats.json + chiffres-clés réécrits dans les pages HTML (production, autoconsommation)
```

> Le pipeline ne génère pas les pages : `04_stats.py` ne met à jour que les chiffres-clés
> repérés par des marqueurs dans le HTML. Une ancienne étape `04_build_html.py` générait les
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
│   ├── 04_stats.py        ← chiffres-clés (production, autoconsommation) → stats.json + pages
│   └── build.py           ← pipeline complet (données → graphiques → chiffres-clés)
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
│       └── data/              ← completeness.json (badges codés en dur) · stats.json (chiffres-clés)
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
4. Calcul des chiffres-clés → `docs/assets/data/stats.json` + réécriture dans `docs/*.html`

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

## Chiffres-clés des installations (`04_stats.py`)

Les cartes (accueil, `installations.html`), les fiches, les descriptions `<meta>` et les
totaux de l'accueil affichent tous les mêmes valeurs, calculées une seule fois :

- **Années de référence** : les 3 dernières années civiles complètes de toutes les séries
  utilisées (hors année en cours, hors série démarrée en cours d'année, hors années touchées
  par un trou de données). Actuellement 2023–2025.
- **Production annuelle** : moyenne sur ces années, arrondie au millier de kWh.
- **Autoconsommation** = 1 − injection réseau ÷ production, sur la somme des années de
  référence. Les fichiers « consommation » mesurent le surplus injecté dans le réseau.

| Installation | Production | Autoconsommation | Remarque |
|---|---|---|---|
| Plan-les-Ouates | mesurée (≈ 101 000 kWh/an) | mesurée (≈ 55 %) | séries complètes |
| Meyrin | mesurée (≈ 78 000 kWh/an) | mesurée (≈ 60 %) | SIG relève les 3 bâtiments via 2 points de comptage (Récréations 24 et 26) : les deux séries couvrent toute l'installation. Nettement sous les 130 000 kWh/an nominaux (≈ 640 kWh/kWc contre ≈ 1 030 à Plan-les-Ouates) |
| Soubeyran | nominale (30 000 kWh/an) | nominale (93 %) | pas de fichier de production, seulement l'injection réseau : non calculable |

Les valeurs nominales viennent des dicts `brief` de `config.py`. `stats.json` contient en plus
les valeurs mesurées et les années de référence utilisées.

**Marqueurs dans le HTML** (les pages restent statiques et éditées à la main) :

- `<!--stat:cle-->valeur<!--/stat-->` : texte courant, remplacé par la valeur (ex. `plo.production_kwh`).
- `<div class="meter" data-meter="cle" …>` : jauge, dont le libellé ARIA, la valeur et la
  largeur sont réécrits.
- `<meta name="description">` des fiches : kWh/an et % réécrits.

Après un changement de données, relancer `python scripts/build.py --charts` (ou
`scripts/04_stats.py` seul) met à jour toutes les pages en une fois.

### Fichiers CSV en double

Les deux fichiers `SIG CourbeCharge 20170624 20260624 …` sont des copies exactes
(SHA-256 identique) de fichiers déjà utilisés : `2b5b1167-…` = `site_d` production
(Récréations 24 Photovoltaïque) et `81dac57f-…` = `site_c` injection (Récréations 26
Consommation). Ils n'apportent aucune donnée nouvelle ; en particulier aucun fichier de
production pour Soubeyran ni pour la troisième toiture de Meyrin n'est disponible.

## Graphiques produits

| Graphique | Description |
|---|---|
| `timeline.png` | Chronologie Gantt des installations (2017–2026) |
| `annual_overview_{type}.png` | Totaux annuels par site, empilés (MWh) |
| `{site}_monthly_{type}.png` | Évolution mensuelle — une courbe par année |
| `{site}_typical_day_{type}.png` | Profil 15 min moyen par saison (kW) |
| `{site}_heatmap_{type}.png` | Carte thermique heure × jour de l'année |

`{type}` vaut `consommation` ou `production`. Tous les PNG sont écrits dans `docs/assets/charts/`.
