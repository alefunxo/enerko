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

# Cache PVGIS (irradiance Genève) — jamais commité (*.csv), généré via
# scripts/irradiance_compare.py. Absent = le panneau irradiance de la vue
# d'ensemble annuelle (03_charts.py) est simplement omis.
PVGIS_CACHE   = ROOT_DIR / "pvgis_geneva_2018_2023.csv"

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
            # ⚠ Ce bâtiment a bien une installation PV (29.9 kWc, cf.
            # INSTALLATIONS["install_soubeyran"]) mais nous ne disposons que de la
            # part autoconsommée mesurée ici — pas d'un fichier production séparé.
            # Ne pas interpréter cette série comme la consommation totale du
            # bâtiment ni comme la production PV brute.
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

# "consommation" reste la clé technique interne (fichiers, dict, cmap) — seul le
# libellé affiché change. Renommé "Autoconsommation" à la demande de l'utilisateur :
# un pur changement de texte (les valeurs mesurées ne changent pas), car les
# communautés d'autoconsommateurs Enerko mesurent en priorité l'électricité
# solaire consommée sur place plutôt que le soutirage réseau brut.
TYPE_LABELS = {
    "consommation": "Autoconsommation",
    "production":   "Production",
}

# ── Fiches installations ────────────────────────────────────────────────────────
# Contenu éditorial (texte Enerko) pour les pages détaillées "une installation,
# une page". Trois installations documentées pour l'instant — les sites sans
# fiche ici (site_c, site_e) restent accessibles via l'explorateur de la page
# d'accueil mais n'ont pas de page dédiée.
#
# 'site_ids'   : {"consommation": site_id|None, "production": site_id|None} —
#                quels SITES fournissent les graphiques mesurés de cette fiche.
# 'brief'      : chiffres de la fiche "en bref" (valeurs éditoriales Enerko,
#                indépendantes des séries mesurées — ne pas les recalculer).
# 'photos'     : liste de noms de fichiers dans docs/assets/images/ (vide pour
#                l'instant ; ajouter les fichiers puis lister leur nom ici).
# 'data_note'  : avertissement affiché en tête de fiche si les données mesurées
#                disponibles ne couvrent pas ce que la fiche décrit.

INSTALLATIONS = {
    "install_soubeyran": {
        "name":    "GENÈVE, Rue Soubeyran 7",
        "slug":    "soubeyran-7",
        "address": "Rue Soubeyran 7, 1202 Genève, Suisse",
        "site_ids": {"consommation": "site_a", "production": None},
        "description": (
            "La coopérative Enerko a financé l'installation photovoltaïque sur la "
            "toiture du bâtiment des coopératives Equilibre et Luciole, à la rue "
            "Soubeyran 7. La coopérative Enerko a également monté et gère "
            "l'exploitation d'une communauté d'autoconsommateurs au sein du "
            "bâtiment, ceci afin de maximiser l'autoconsommation de l'électricité "
            "solaire produite en toiture."
        ),
        "sections": {
            "installation_pv": (
                "Cette installation se compose de 115 modules polycristallins "
                "(Canadian Solar 260 Wc) disposés sur la casquette solaire du "
                "bâtiment ainsi que sur une partie de la toiture plate. Les "
                "modules PV sont disposés en shed à 10° d'inclinaison, orientés "
                "Sud-Sud-Ouest (35°). Deux onduleurs SMA (Sunny Tripower "
                "20000TL+7000TL), positionnés en toiture, transforment le courant "
                "continu en courant alternatif utilisable dans le bâtiment et "
                "compatible avec le réseau électrique. La production d'électricité "
                "solaire annuelle se monte à 35'000 kWh, soit l'équivalent de la "
                "consommation d'environ 12 logements genevois."
            ),
            "financement": (
                "L'investissement de CHF 60'000.- est porté par la coopérative "
                "Enerko. Deux tiers des locataires de l'immeuble sont membres "
                "d'Enerko et leurs parts sociales représentent deux tiers du "
                "financement de cette installation."
            ),
            "communaute_titre": "La communauté d'autoconsommateurs",
            "communaute": [
                "Tous les locataires (ménages et activités), ainsi que les "
                "consommateurs techniques (pompe à chaleur, ventilation, communs "
                "d'immeubles, etc.) sont regroupés dans une communauté "
                "d'autoconsommateurs (société simple). La coopérative Enerko est "
                "la représentante de la communauté vis-à-vis de SIG, donc elle "
                "reçoit de la part de SIG une facture globale électrique, qu'elle "
                "refacture à chaque membre selon sa propre consommation électrique "
                "au tarif du produit soutiré (Vitale Bleu tarif double).",
                "Du fait de la configuration des installations électriques, la "
                "consommation instantanée d'électricité PV est priorisée par "
                "rapport à l'électricité provenant du réseau électrique. Ce "
                "regroupement permet ainsi d'autoconsommer plus de 90% de la "
                "production PV. L'électricité PV couvre environ 20% de la "
                "consommation électrique totale du bâtiment.",
            ],
        },
        "brief": {
            "surface_m2":            180,
            "puissance_kwc":         29.9,
            "production_kwh_an":     30000,
            "autoconsommation_pct":  93,
            "autonomie_pct":         19,
            "mise_en_service":       2016,
            "cout_chf":              60000,
            "retribution_chf":       16000,
            "installateur":          "Solstis SA",
        },
        "data_note": (
            "Les données mesurées disponibles pour ce site ne couvrent que la "
            "part d'électricité autoconsommée relevée au compteur — nous ne "
            "disposons pas d'un relevé séparé de la consommation totale du "
            "bâtiment ni de la production PV brute. Le graphique ci-dessous "
            "reflète donc uniquement cette part autoconsommée, pas l'installation "
            "PV dans son ensemble."
        ),
        "photos": [],
    },
    "install_meyrin_recreations_24": {
        "name":    "MEYRIN, Espl. des Récréations 24",
        "slug":    "meyrin-recreations-24",
        "address": "Esplanade des Récréations 24, 1217 Meyrin, Suisse",
        "site_ids": {"consommation": "site_b", "production": "site_d"},
        "description": (
            "La coopérative Enerko a financé les installations photovoltaïques "
            "sur les toitures des trois bâtiments de la coopérative équilibre, à "
            "la promenade de l'Aubier 19-20-21. La coopérative Enerko a également "
            "monté et gère l'exploitation des trois communautés "
            "d'autoconsommateurs au sein des bâtiments, ceci afin de maximiser "
            "l'autoconsommation de l'électricité solaire produite en toiture."
        ),
        "sections": {
            "installation_pv": (
                "Ces installations se composent au total de 447 modules "
                "polycristallins (Canadian Solar 270 Wc) pour une puissance "
                "totale de 121 kWc. Les modules PV sont disposés sur les "
                "toitures plates soit en dômes Est-Ouest, soit en shed orientés "
                "Sud-Ouest (45°), à 10° d'inclinaison. Six onduleurs SMA (Sunny "
                "Tripower 25000TL/20000TL/5000TL), positionnés en toiture, "
                "transforment le courant continu en courant alternatif "
                "utilisable dans le bâtiment et compatible avec le réseau "
                "électrique. La production d'électricité solaire annuelle se "
                "monte à 140'000 kWh, soit l'équivalent de la consommation "
                "d'environ 50 logements genevois."
            ),
            "financement": (
                "L'investissement de CHF 200'000.- est porté par la coopérative "
                "Enerko."
            ),
            "communaute_titre": "Les communautés d'autoconsommateurs",
            "communaute": [
                "Tous les locataires (ménages et activités), ainsi que les "
                "consommateurs techniques (pompe à chaleur, ventilation, communs "
                "d'immeubles, etc.) sont regroupés dans une communauté "
                "d'autoconsommateurs. La coopérative Enerko est la représentante "
                "de la communauté vis-à-vis de SIG, donc elle reçoit de la part "
                "de SIG une facture globale électrique, qu'elle refacture à "
                "chaque membre selon sa propre consommation électrique au tarif "
                "du produit soutiré (Vitale Bleu tarif double).",
                "Du fait de la configuration des installations électriques, la "
                "consommation instantanée d'électricité PV est priorisée par "
                "rapport à l'électricité provenant du réseau électrique. Ce "
                "regroupement permet ainsi d'autoconsommer plus de la moitié de "
                "la production PV. L'électricité PV couvre environ un tiers de "
                "la consommation électrique totale des bâtiments.",
                "Les trois bâtiments sont raccordés au même compteur SIG : sur "
                "le plan des données mesurées ci-dessous, ils apparaissent donc "
                "comme un seul point d'autoconsommation et un seul point de "
                "production, et non comme trois installations distinctes.",
            ],
        },
        "brief": {
            "surface_m2":            740,
            "puissance_kwc":         121,
            "production_kwh_an":     130000,
            "autoconsommation_pct":  59,
            "autonomie_pct":         31,
            "mise_en_service":       2017,
            "cout_chf":              200000,
            "retribution_chf":       55000,
            "installateur":          "Solstis SA",
        },
        "data_note": None,
        "photos": [],
    },
    "install_plan_les_ouates_vers_8": {
        "name":    "PLAN-LES-OUATES, Ch. de Vers 8",
        "slug":    "plan-les-ouates-vers-8",
        "address": "Chemin de Vers 8, 1228 Plan-les-Ouates, Suisse",
        "site_ids": {"consommation": "site_g", "production": "site_f"},
        "description": (
            "La coopérative Enerko a financé l'installation photovoltaïque sur "
            "la toiture du bâtiment de la commune de Plan-les-Ouates, au chemin "
            "de Vers 8. La coopérative Enerko a également monté une communauté "
            "d'autoconsommateurs au sein du bâtiment, ceci afin de maximiser "
            "l'autoconsommation de l'électricité solaire produite en toiture."
        ),
        "sections": {
            "installation_pv": (
                "Cette installation se compose de 260 modules monocristallins "
                "(Bisol 375 Wc) disposés sur la toiture plate. Les modules PV "
                "sont posés en shed à 10° d'inclinaison, orientés Sud-Ouest "
                "(55°). Un onduleur Solarmax 110 SXT, positionné en toiture, "
                "transforme le courant continu en courant alternatif utilisable "
                "dans le bâtiment et compatible avec le réseau électrique. La "
                "production d'électricité solaire est estimée à environ "
                "100'000 kWh."
            ),
            "financement": (
                "L'investissement de CHF 180'000.- est porté par la coopérative "
                "Enerko avec une subvention de la commune de Plan-les-Ouates "
                "équivalente à la rétribution unique (32'000.- CHF)."
            ),
            "communaute_titre": "La communauté d'autoconsommateurs",
            "communaute": [
                "Certains locataires (ménages et activités) qui le souhaitent, "
                "ainsi que les consommateurs techniques (ventilation, communs "
                "d'immeubles, etc.) sont regroupés dans une communauté "
                "d'autoconsommateurs (société simple). La coopérative Enerko "
                "est la représentante de la communauté vis-à-vis de SIG, qui "
                "s'occupe de la facturation. Enerko vend l'électricité produite "
                "aux membres de la communauté et le prix est indexé 2 centimes "
                "plus bas que le tarif SIG Vitale Bleu.",
                "Du fait de la configuration des installations électriques, la "
                "consommation instantanée d'électricité PV est priorisée par "
                "rapport à l'électricité provenant du réseau électrique. Ce "
                "regroupement permet ainsi, selon les premières estimations, "
                "d'autoconsommer 40% de la production PV.",
            ],
        },
        "brief": {
            "surface_m2":            483,
            "puissance_kwc":         97.5,
            "production_kwh_an":     100000,
            "autoconsommation_pct":  40,
            "autonomie_pct":         None,
            "mise_en_service":       2022,
            "cout_chf":              180000,
            "retribution_chf":       32000,
            "installateur":          "Solstis SA",
        },
        "data_note": None,
        "photos": [],
    },
}

INSTALLATION_ORDER = [
    "install_soubeyran",
    "install_meyrin_recreations_24",
    "install_plan_les_ouates_vers_8",
]

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
