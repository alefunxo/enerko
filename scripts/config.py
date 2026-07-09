"""
Configuration centrale — Enerko Courbes de charge
Seul fichier à modifier pour mettre à jour les noms de sites.
"""

from pathlib import Path

# ── Répertoires ────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).parent.parent
DATA_DIR      = ROOT_DIR                          # CSVs bruts (jamais commités)
PROCESSED_DIR = ROOT_DIR / "processed"            # Parquets intermédiaires (jamais commités)
AGG_DIR       = PROCESSED_DIR / "aggregates"      # Agrégats (jamais commités)
IMAGES_DIR    = ROOT_DIR / "docs" / "assets" / "images"
DOCS_DIR      = ROOT_DIR / "docs"

# ── Définition des sites ───────────────────────────────────────────────────────
# Clé : identifiant stable (ne pas modifier)
# 'name'         : nom affiché — remplacer "Site X" par le vrai nom quand disponible
# 'online_since' : première mesure disponible (YYYY-MM)
# 'files'        : UUID du fichier CSV (sans extension) par type de mesure
#                  None = pas de données pour ce type
# 'color'        : couleur dans les graphiques — palette catégorielle validée
#                  (8 teintes, ordre fixe, cf. skill dataviz), jamais recyclée
#
# ⚠ Pour les sites C et D (2 fichiers chacun) : à confirmer quel fichier
#   correspond à la consommation et lequel à la production.

SITES = {
    "site_a": {
        "name":         "GENEVE, Rue Soubeyran 7",
        "online_since": "2017-06",
        "color":        "#2a78d6",  # slot 1 · bleu
        "files": {
            "consommation": "904ec29e-aa65-4683-ae71-dc0576ad35fe",
            "production":   None,
        },
    },
    "site_b": {
        "name":         "MEYRIN, Espl. des Récréations 24",
        "online_since": "2017-11",
        "color":        "#1baf7a",  # slot 2 · aqua
        "files": {
            "consommation": "3fa70c73-dc4c-4302-bf1c-319eb13d34a6",
            "production":   None,
        },
    },
    "site_c": {
        "name":         "MEYRIN, Espl. des Récréations 26",
        "online_since": "2018-01",
        "color":        "#eda100",  # slot 3 · jaune
        "files": {
            "consommation": "3cddead9-c129-40dd-8218-febeda1d27ef",
            # ⚠ valeurs à vérifier (anomalies signalées par l'utilisateur)
            "production":   "dc513614-6529-4245-97e1-8857e95c39cf",
        },
    },
    "site_d": {
        # Installation PV de "MEYRIN, Espl. des Récréations 24" (même adresse que site_b)
        # Nom volontairement sans suffixe "Photovoltaïque" : le type (Consommation/
        # Production) est déjà indiqué dans le titre de chaque graphique et dans la
        # légende des vues par type — dupliquer ici créait des libellés incohérents
        # entre sites (ex. site_c) et redondants (04_build_html.py, 03_charts.py).
        "name":         "MEYRIN, Espl. des Récréations 24",
        "online_since": "2018-01",
        "color":        "#008300",  # slot 4 · vert
        "files": {
            "production":   "454bab07-4f8a-485f-932d-7b315fb6f41f",
            # ⚠ UUID non identifié (2b5b1167-9d94-4ef1-b1fe-924b01f7cee2) — motif de
            # données (10% manquant, même trous que les fichiers PV) suggère un 2e
            # compteur Photovoltaïque plutôt qu'une consommation — à confirmer avant usage
            "consommation": None,
        },
    },
    "site_e": {
        # ⚠ nom non identifié dans la liste des sites — à confirmer
        "name":         "Site E",
        "online_since": "2018-02",
        "color":        "#4a3aa7",  # slot 5 · violet
        "files": {
            "consommation": "81dac57f-fa6a-4844-a67f-42d345eb777f",
            "production":   None,
        },
    },
    "site_f": {
        # Installation PV de "PLAN-LES-OUATES, Ch. de Vers 8" (même adresse que site_g)
        "name":         "PLAN-LES-OUATES, Ch. de Vers 8",
        "online_since": "2022-06",
        "color":        "#e34948",  # slot 6 · rouge
        "files": {
            "consommation": None,
            "production":   "8f9af0f3-4cc6-4518-9ca4-e213bb539eaa",
        },
    },
    "site_g": {
        "name":         "PLAN-LES-OUATES, Ch. de Vers 8",
        "online_since": "2022-06",
        "color":        "#e87ba4",  # slot 7 · magenta
        "files": {
            "consommation": "34bbd40c-90bc-4f62-bf66-58bfe440b285",
            "production":   None,
        },
    },
}

# Ordre d'affichage (chronologique)
SITE_ORDER = ["site_a", "site_b", "site_c", "site_d", "site_e", "site_f", "site_g"]

# Installations PV (production non nulle) — les autres sont des points de
# consommation associés à un bâtiment, pas des installations à proprement parler
PV_SITE_ORDER = [sid for sid in SITE_ORDER if SITES[sid]["files"]["production"] is not None]

TYPES = ["consommation", "production"]

TYPE_LABELS = {
    "consommation": "Consommation",
    "production":   "Production",
}

# ── Saisons ────────────────────────────────────────────────────────────────────
SAISONS = {
    "Hiver":     [12, 1, 2],
    "Printemps": [3, 4, 5],
    "Été":       [6, 7, 8],
    "Automne":   [9, 10, 11],
}

SAISON_COLORS = {
    "Hiver":     "#4A90D9",
    "Printemps": "#7ED321",
    "Été":       "#F5A623",
    "Automne":   "#D0821C",
}

# ── Mois en français ───────────────────────────────────────────────────────────
MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
