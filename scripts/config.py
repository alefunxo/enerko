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

# ── Pages éditoriales (contenu institutionnel, repris du site vitrine enerko.ch) ─
# Ce contenu est indépendant des données mesurées (SITES/INSTALLATIONS ci-dessus) :
# c'est le texte institutionnel de la coopérative — statuts, mode de financement,
# adhésion. Certaines sections du site vitrine d'origine (Gouvernance/Implication
# sous Investir, page Actus/Médias, carte Google sous Contact) sont volontairement
# omises ici : le texte réel n'a pas été fourni, mieux vaut ne pas publier de page
# incomplète que d'improviser du contenu.

ABOUT = {
    "tagline_prefix": "coopér",
    "tagline_accent1": "Action",
    "tagline_mid": " énerg",
    "tagline_accent2": "Ethique",
    "text": (
        "Enerko est une société coopérative fondée en 2016 à Genève. Elle a "
        "pour but de favoriser et développer des projets de production "
        "d'énergies renouvelables et d'économie d'énergie. Elle a également "
        "pour but de contribuer à l'émergence et l'expérimentation de "
        "nouveaux modèles de mise en œuvre de ces projets — notamment le "
        "financement d'installations photovoltaïques en autoconsommation "
        "collective."
    ),
}

AUTOCONSOMMER = {
    "intro": (
        "L'autoconsommation collective est le fait de se regrouper au sein "
        "d'un bâtiment pour autoconsommer un maximum d'électricité "
        "photovoltaïque."
    ),
    "paragraphs": [
        (
            "Dans un contexte actuel où l'électricité photovoltaïque est "
            "rachetée à bas prix par les gestionnaires de réseaux électriques "
            "suisses, il est cohérent d'essayer d'en autoconsommer "
            "instantanément un maximum. Pour ce faire, une communauté "
            "d'autoconsommateurs ou un regroupement pour consommation propre "
            "est mis en œuvre."
        ),
        (
            "La coopérative Enerko vend aux membres des communautés/"
            "regroupements d'autoconsommation d'une part l'énergie "
            "photovoltaïque instantanément consommée, mais également "
            "l'électricité soutirée du réseau électrique de SIG, au prix de "
            "la gamme vitale bleu heures pleines/creuses."
        ),
        (
            "L'autoconsommateur consomme ainsi un mix électrique comportant "
            "un quart d'électricité solaire et trois quarts d'électricité "
            "hydraulique suisse. Il s'agit d'une électricité de meilleure "
            "qualité que la gamme vitale vert de SIG, ceci au prix du vitale "
            "bleu."
        ),
        (
            "L'électricité photovoltaïque non autoconsommée instantanément "
            "est refoulée sur le réseau électrique et achetée par SIG à un "
            "tarif révisé chaque année."
        ),
    ],
    "cta_text": (
        "Vous habitez ou gérez déjà un bâtiment équipé par Enerko et "
        "souhaitez rejoindre une communauté d'autoconsommateurs, ou vous "
        "souhaitez devenir membre de la coopérative ?"
    ),
}

INVESTIR = {
    "summary": (
        "En résumé : vos parts sociales financent des installations "
        "photovoltaïques sur des toits genevois. Enerko vise un intérêt de "
        "1 à 2% par an sur ce capital, versé si les comptes de la "
        "coopérative le permettent, et vous pouvez demander à le récupérer "
        "moyennant un préavis de 6 mois. Le détail — sécurité, rendement, "
        "récupération du capital — est développé ci-dessous."
    ),
    "sections": [
        {
            "anchor": "securite",
            "nav_label": "Sécurité",
            "title": "Sécurité financière — Comment fonctionne Enerko ?",
            "paragraphs": [
                (
                    "Enerko finance des installations photovoltaïques en "
                    "autoconsommation collective grâce aux parts sociales "
                    "souscrites par ses membres."
                ),
                (
                    "L'administration d'Enerko gère autant les questions "
                    "stratégiques qu'opérationnelles. Nous étudions "
                    "actuellement la possibilité/faisabilité de déléguer une "
                    "partie des tâches opérationnelles à un bureau interne."
                ),
            ],
            "charges_title": "Financièrement, nos charges sont :",
            "charges": [
                "les intérêts sur les parts sociales",
                "les frais de gestion des communautés d'autoconsommateurs",
                "les frais d'entretien/assurances des installations PV",
                "divers frais de fonctionnement (communication, défraiement "
                "administratif, etc.)",
            ],
            "revenus_title": "Parallèlement, nos revenus proviennent de :",
            "revenus": [
                "la vente du courant autoconsommé aux membres des "
                "communautés d'autoconsommateurs",
                "la vente du courant excédentaire, injecté dans le réseau "
                "électrique, à SIG",
                "une prime de gestion/mise en place de projet pour chaque "
                "nouvelle installation photovoltaïque",
            ],
            "closing": (
                "L'électricité autoconsommée est vendue aux membres de nos "
                "communautés au tarif SIG vitale bleu (100% hydraulique "
                "suisse). L'électricité refoulée dans le réseau est vendue au "
                "distributeur d'énergie. Le taux d'autoconsommation moyen de "
                "nos installations photovoltaïques se monte à 50%, nous "
                "valorisons donc la moitié de l'électricité solaire produite "
                "via les membres de nos communautés et l'autre moitié via SIG "
                "qui a l'obligation de nous acheter l'excédent de production "
                "photovoltaïque."
            ),
        },
        {
            "anchor": "rendement",
            "nav_label": "Rendement",
            "title": "Rendement financier — Quel est le taux d'intérêt sur les parts sociales ?",
            "paragraphs": [
                (
                    "Nous visons un taux d'intérêt sur les parts sociales de "
                    "1 à 2%. Cet intérêt est :"
                ),
            ],
            "bullets": [
                "conditionnel, c'est-à-dire si les comptes de la coopérative "
                "le permettent",
                "optionnel, donc chaque membre est libre de renoncer à cet "
                "intérêt",
            ],
            "paragraphs_after": [
                (
                    "La volonté d'Enerko est de rémunérer le capital "
                    "mobilisé sous forme de parts sociales. L'assemblée "
                    "générale statue chaque année, non pas sur le fait qu'il "
                    "y ait ou n'y ait pas d'intérêt, mais sur le taux "
                    "d'intérêt que le fonctionnement d'Enerko permet de "
                    "proposer aux membres de notre coopérative."
                ),
                (
                    "À titre d'information : le taux 2017 a été de 1% et "
                    "depuis 2018 jusqu'à aujourd'hui le taux est de 2%."
                ),
            ],
        },
        {
            "anchor": "recuperation",
            "nav_label": "Récupération de capital",
            "title": (
                "Récupération du capital — Quand et sous quelles conditions "
                "puis-je récupérer le capital immobilisé en parts sociales ?"
            ),
            "paragraphs": [
                (
                    "Les parts sociales peuvent être revendues, moyennant un "
                    "délai de 6 mois après demande par courrier, pour autant "
                    "que cela ne mette pas en danger la pérennité financière "
                    "d'Enerko. Dans le cas extrême d'une mise en péril de la "
                    "coopérative, le code des obligations permet un délai de "
                    "remboursement pouvant aller jusqu'à 3 ans."
                ),
                (
                    "Dans les faits, si le nombre de parts sociales non "
                    "engagé dans des projets est suffisant, un remboursement "
                    "urgent peut être envisagé au cas par cas, s'il est "
                    "justifié."
                ),
            ],
        },
    ],
}

DEVENIR_MEMBRE = {
    "text": (
        "Pour devenir membre ou pour toute autre information, écrivez-nous "
        "à"
    ),
    "email": "info@enerko.ch",
}

CONTACT = {
    "address_lines": ["4, ch. des Terres-Noires", "1252 Meinier", "Suisse"],
    "email": "info@enerko.ch",
}

# Placeholders — noms confirmés par l'utilisateur le 2026-07-10, fonctions
# réelles à préciser (remplacer "Fonction à préciser" une fois connues).
EQUIPE = [
    {"name": "Arthur Rinaldi",       "role": "Fonction à préciser"},
    {"name": "Christophe Brunet",    "role": "Fonction à préciser"},
    {"name": "Antoine Delay",        "role": "Fonction à préciser"},
    {"name": "Elvis Redza",          "role": "Fonction à préciser"},
    {"name": "Alejandro Pena-Bello", "role": "Fonction à préciser"},
]

# Logos partenaires : fichiers attendus sous docs/assets/images/partners/<logo>.
# Fournis par l'utilisateur le 2026-07-10 — à déposer sur disque avant rebuild.
LIENS = [
    {
        "name": "Equilibre",
        "desc": "Coopérative d'habitation partenaire de plusieurs installations Enerko.",
        "url": "https://www.cooperative-equilibre.ch/",
        "logo": "partners/equilibre.png",
    },
    {
        "name": "Swissgrid",
        "desc": "Gestionnaire du réseau de transport d'électricité suisse.",
        "url": "https://www.swissgrid.ch/fr/home.html",
        "logo": "partners/swissgrid.png",
    },
    {
        "name": "SIG",
        "desc": "Services Industriels de Genève — distributeur d'électricité local.",
        "url": "https://ww2.sig-ge.ch/",
        "logo": "partners/sig.jpg",
    },
    {
        "name": "Swissolar",
        "desc": "Association professionnelle suisse de l'énergie solaire.",
        "url": "https://www.swissolar.ch/fr",
        "logo": "partners/swissolar.jpg",
    },
    {
        "name": "VESE",
        "desc": "Association des producteurs d'énergie indépendants.",
        "url": "https://www.vese.ch/fr/",
        "logo": "partners/vese.png",
    },
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
