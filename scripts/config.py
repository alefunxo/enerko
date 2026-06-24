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
# 'color'        : couleur dans les graphiques
#
# ⚠ Pour les sites C et D (2 fichiers chacun) : à confirmer quel fichier
#   correspond à la consommation et lequel à la production.

SITES = {
    "site_a": {
        "name":         "Site A",
        "online_since": "2017-06",
        "color":        "#F5A623",
        "files": {
            "consommation": "904ec29e-aa65-4683-ae71-dc0576ad35fe",
            "production":   None,
        },
    },
    "site_b": {
        "name":         "Site B",
        "online_since": "2017-11",
        "color":        "#E07B0A",
        "files": {
            "consommation": "3fa70c73-dc4c-4302-bf1c-319eb13d34a6",
            "production":   None,
        },
    },
    "site_c": {
        "name":         "Site C",
        "online_since": "2018-01",
        "color":        "#1B6CA8",
        "files": {
            # À confirmer : inverser si nécessaire
            "consommation": "3cddead9-c129-40dd-8218-febeda1d27ef",
            "production":   "81dac57f-fa6a-4844-a67f-42d345eb777f",
        },
    },
    "site_d": {
        "name":         "Site D",
        "online_since": "2018-01",
        "color":        "#2E9E6B",
        "files": {
            # À confirmer : inverser si nécessaire
            "consommation": "2b5b1167-9d94-4ef1-b1fe-924b01f7cee2",
            "production":   "454bab07-4f8a-485f-932d-7b315fb6f41f",
        },
    },
    "site_e": {
        "name":         "Site E",
        "online_since": "2018-02",
        "color":        "#8E44AD",
        "files": {
            "consommation": "dc513614-6529-4245-97e1-8857e95c39cf",
            "production":   None,
        },
    },
    "site_f": {
        "name":         "Site F",
        "online_since": "2022-06",
        "color":        "#1B3A5C",
        "files": {
            "consommation": "8f9af0f3-4cc6-4518-9ca4-e213bb539eaa",
            "production":   None,
        },
    },
    "site_g": {
        "name":         "Site G",
        "online_since": "2022-06",
        "color":        "#C0392B",
        "files": {
            "consommation": "34bbd40c-90bc-4f62-bf66-58bfe440b285",
            "production":   None,
        },
    },
}

# Ordre d'affichage (chronologique)
SITE_ORDER = ["site_a", "site_b", "site_c", "site_d", "site_e", "site_f", "site_g"]

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
