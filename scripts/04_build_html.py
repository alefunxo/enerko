"""
04_build_html.py — Génération de docs/index.html + docs/installations/*.html
Lit les noms de sites et le contenu éditorial dans config.py et produit la page
d'accueil ainsi qu'une page dédiée par installation documentée (INSTALLATIONS).
À relancer après chaque modification de config.py.

Usage : python scripts/04_build_html.py
"""

import json
import sys
import urllib.parse
from datetime import date
from pathlib import Path

# Encodage UTF-8 pour les terminaux Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    SITES, SITE_ORDER, PV_SITE_ORDER, TYPES, TYPE_LABELS,
    INSTALLATIONS, INSTALLATION_ORDER, DOCS_DIR,
    ABOUT, AUTOCONSOMMER, INVESTIR, DEVENIR_MEMBRE, CONTACT, LIENS, EQUIPE,
)

COMPLETENESS_PATH = DOCS_DIR / "assets" / "data" / "completeness.json"
INSTALL_DIR       = DOCS_DIR / "installations"


def _completeness_json() -> str:
    """
    Contenu de completeness.json, embarqué tel quel dans la page d'accueil.

    Chargé via fetch() auparavant, mais fetch() d'un fichier local est bloqué
    par le navigateur en file:// (CORS) — la page ouverte en double-clic
    affichait alors "n/d" partout. L'embarquer directement dans le HTML
    fonctionne aussi bien en file:// qu'en http(s)://.
    """
    if not COMPLETENESS_PATH.exists():
        return "{}"
    return COMPLETENESS_PATH.read_text(encoding="utf-8")


def _completeness_dict() -> dict:
    if not COMPLETENESS_PATH.exists():
        return {}
    return json.loads(COMPLETENESS_PATH.read_text(encoding="utf-8"))


def _sites_by_type_json() -> str:
    """
    {"consommation": [{"id": "site_a", "label": "..."}, ...], "production": [...]}
    Sert à ne proposer, pour un type de données donné, que les installations
    qui possèdent effectivement ce type.
    """
    by_type = {}
    for type_key in TYPES:
        entries = []
        for sid in SITE_ORDER:
            s = SITES[sid]
            if s["files"].get(type_key) is None:
                continue
            entries.append({
                "id": sid,
                "label": f'{s["name"]} (depuis {s["online_since"]})',
            })
        by_type[type_key] = entries
    return json.dumps(by_type, ensure_ascii=False)


# ── Formatage ────────────────────────────────────────────────────────────────
def _fmt_thousands(n) -> str:
    """1234 → 1'234 (séparateur de milliers suisse)."""
    return f"{n:,.0f}".replace(",", "'")


def _fmt_kwc(v) -> str:
    """121 → '121' ; 29.9 → '29.9' (pas de décimale superflue)."""
    return f"{v:g}"


# ── Composants HTML réutilisés (toutes les pages) ────────────────────────────
# Nav unifiée : tableau de bord (Accueil, Installations → fiches mesurées) et
# pages institutionnelles (Enerko?, Autoconsommer, Investir, Devenir membre,
# Contact, Liens). Les fiches individuelles ne sont plus listées directement
# dans la nav (ça ferait 3+ entrées de plus) — on y accède depuis "Installations".
def _header_html(depth: int) -> str:
    """Logo Enerko — le fichier image porte déjà le nom + la signature
    'coopérAction énergEthique', donc pas de texte de sous-titre séparé
    (évite de dupliquer ce que le logo affiche déjà)."""
    prefix = "../" if depth else ""
    return f"""<header>
  <div class="header-inner">
    <a href="{prefix}index.html" class="brand-logo">
      <img src="{prefix}assets/images/logo-enerko.png" alt="Enerko — coopérAction énergEthique">
    </a>
  </div>
</header>"""


def _nav_links(depth: int):
    prefix = "../" if depth else ""
    return [
        ("accueil", "Accueil", f"{prefix}index.html"),
        ("enerko", "Enerko", f"{prefix}enerko.html"),
        ("equipe", "Équipe", f"{prefix}equipe.html"),
        ("installations", "Installations", f"{prefix}installations/index.html"),
        ("autoconsommer", "Autoconsommer", f"{prefix}autoconsommer.html"),
        ("investir", "Investir", f"{prefix}investir.html"),
        ("devenir-membre", "Devenir membre", f"{prefix}devenir-membre.html"),
        ("contact", "Contact", f"{prefix}contact.html"),
        ("liens", "Liens", f"{prefix}liens.html"),
    ]


def _nav_html(active: str, depth: int) -> str:
    """Sur mobile, 9 entrées ne tiennent pas sur une ligne — repliées derrière
    un bouton hamburger en CSS pur (case à cocher cachée + sélecteur ~), pour
    que ça marche sur toutes les pages sans dépendre du <script> du dashboard
    (qui n'est présent que sur installations/index.html)."""
    items = []
    for slug, label, href in _nav_links(depth):
        cls = ' class="active"' if slug == active else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return (
        '<nav class="top-nav"><div class="top-nav-inner">'
        '<input type="checkbox" id="nav-toggle" class="nav-toggle-checkbox">'
        '<label for="nav-toggle" class="nav-toggle-label" aria-label="Ouvrir le menu"></label>'
        f'<div class="top-nav-links">{"".join(items)}</div>'
        '</div></nav>'
    )


def _brief_list_html(brief: dict) -> str:
    rows = [
        ("Surface",                    f'{_fmt_thousands(brief["surface_m2"])} m²'),
        ("Puissance",                  f'{_fmt_kwc(brief["puissance_kwc"])} kWc'),
        ("Production électrique",      f'{_fmt_thousands(brief["production_kwh_an"])} kWh/an'),
        ("Autoconsommation PV",        f'{brief["autoconsommation_pct"]}%'),
    ]
    if brief.get("autonomie_pct") is not None:
        rows.append(("Autonomie PV du bâtiment", f'{brief["autonomie_pct"]}%'))
    rows += [
        ("Date de mise en service",    str(brief["mise_en_service"])),
        ("Coût d'installation",        f'{_fmt_thousands(brief["cout_chf"])} CHF'),
        ("Rétribution unique",         f'{_fmt_thousands(brief["retribution_chf"])} CHF'),
        ("Installateur PV",            brief["installateur"]),
    ]
    items = "".join(
        f'<li><span class="brief-label">{label}</span>'
        f'<span class="brief-value">{value}</span></li>'
        for label, value in rows
    )
    return f'<ul class="brief-list">{items}</ul>'


def _install_cards_html(depth: int) -> str:
    """depth 0 (accueil) → liens vers installations/<slug>.html ;
    depth 1 (installations/index.html) → liens vers <slug>.html directement."""
    link_prefix = "" if depth else "installations/"
    cards = []
    for iid in INSTALLATION_ORDER:
        inst = INSTALLATIONS[iid]
        cards.append(f"""
      <div class="install-card">
        <h3>{inst["name"]}</h3>
        <p class="install-address">{inst["address"]}</p>
        {_brief_list_html(inst["brief"])}
        <a class="install-card-link" href="{link_prefix}{inst["slug"]}.html">Voir la fiche complète →</a>
      </div>""")
    return "".join(cards)


def _map_embed_html(address: str) -> str:
    q = urllib.parse.quote(address)
    return (
        '<div class="map-embed">'
        f'<iframe src="https://www.google.com/maps?q={q}&output=embed" '
        'loading="lazy" title="Localisation de l\'installation"></iframe>'
        '</div>'
    )


def _data_note_html(note) -> str:
    if not note:
        return ""
    return f'<div class="data-note"><strong>À noter sur les données ci-dessous</strong><br>{note}</div>'


def _stat_tiles_html() -> str:
    """Chiffres d'impact — la plupart agrégés à partir des fiches INSTALLATIONS
    (brief), simple somme des chiffres déjà publiés par fiche. Le nombre de
    membres n'est pas connu : affiché "X" en attendant le vrai chiffre plutôt
    que de l'omettre ou de l'inventer — remplacer dans la liste `tiles`
    ci-dessous une fois disponible."""
    total_kwc = sum(INSTALLATIONS[iid]["brief"]["puissance_kwc"] for iid in INSTALLATION_ORDER)
    total_m2  = sum(INSTALLATIONS[iid]["brief"]["surface_m2"] for iid in INSTALLATION_ORDER)
    total_kwh = sum(INSTALLATIONS[iid]["brief"]["production_kwh_an"] for iid in INSTALLATION_ORDER)
    total_chf = sum(INSTALLATIONS[iid]["brief"]["cout_chf"] for iid in INSTALLATION_ORDER)
    tiles = [
        ("X",                                         "Membres de la coopérative"),
        (str(len(INSTALLATION_ORDER)),               "Installations photovoltaïques"),
        (f"{_fmt_kwc(total_kwc)} kWc",                "Puissance installée totale"),
        (f"{_fmt_thousands(total_m2)} m²",            "Surface de toiture équipée"),
        (f"{_fmt_thousands(total_kwh)} kWh/an",       "Production solaire annuelle"),
        (f"{_fmt_thousands(total_chf)} CHF",          "Capital investi dans ces installations"),
    ]
    items = "".join(
        f'<div class="stat-tile"><span class="stat-value">{v}</span>'
        f'<span class="stat-label">{l}</span></div>'
        for v, l in tiles
    )
    return f'<div class="stats-strip">{items}</div>'


def _cta_band_html(heading: str, text: str, buttons, depth: int = 0) -> str:
    """buttons : liste de (label, href, css_class) — css_class = 'btn-primary'|'btn-secondary'."""
    prefix = "../" if depth else ""
    btns = "".join(
        f'<a class="btn {cls}" href="{prefix}{href}">{label}</a>'
        for label, href, cls in buttons
    )
    return f"""
    <div class="cta-band">
      <h3>{heading}</h3>
      <p>{text}</p>
      <div class="cta-buttons">{btns}</div>
    </div>"""


def _hero_html() -> str:
    return f"""
  <section id="sec-hero" class="hero-band">
    <p class="hero-tagline">
      {ABOUT["tagline_prefix"]}<span class="accent">{ABOUT["tagline_accent1"]}</span
      >{ABOUT["tagline_mid"]}<span class="accent">{ABOUT["tagline_accent2"]}</span>
    </p>
    <p class="hero-text">{ABOUT["text"]}</p>
    <div class="cta-buttons">
      <a class="btn btn-primary" href="devenir-membre.html">Devenir membre</a>
      <a class="btn btn-secondary" href="investir.html">Investir</a>
      <a class="btn btn-secondary" href="enerko.html">En savoir plus sur Enerko</a>
    </div>
  </section>"""


def _photo_gallery_html(photos, depth: int) -> str:
    if not photos:
        return ""
    prefix = "../" if depth else ""
    imgs = "".join(
        f'<img src="{prefix}assets/images/{p}" alt="Photo de l\'installation">'
        for p in photos
    )
    return f'<div class="photo-gallery">{imgs}</div>'


def _completeness_badge_html(comp) -> str:
    if not comp:
        return '<p class="completeness-detail">Complétude des données&nbsp;: n/d</p>'
    pct_present = 100 - comp["pct_missing"]
    cls = "good" if comp["pct_missing"] < 2 else "warn" if comp["pct_missing"] < 15 else "bad"
    badge = (
        f'<span class="completeness-badge {cls}">'
        f'{pct_present:.1f}% complet ({comp["start"]} → {comp["end"]})</span>'
    )
    if comp["gaps"]:
        detail = "Trous : " + "  ·  ".join(
            f'{g["start"]} → {g["end"]} ({g["days"]:.0f} j)' for g in comp["gaps"]
        )
    else:
        detail = "Aucun trou significatif détecté."
    return f'{badge}<p class="completeness-detail completeness-standalone">{detail}</p>'


def _building_measured_html(building: dict, depth: int, completeness: dict) -> str:
    site_ids = building["site_ids"]
    types_present = [t for t in TYPES if site_ids.get(t) is not None]
    blocks = "".join(
        _measured_type_block_html(site_ids[t], t, depth, completeness)
        for t in types_present
    )
    if building.get("label"):
        return f'<h3 class="measured-building-title">{building["label"]}</h3>{blocks}'
    return blocks


def _measured_type_block_html(site_id: str, type_key: str, depth: int, completeness: dict) -> str:
    prefix = "../" if depth else ""
    base   = f"{prefix}assets/images/{site_id}"
    label  = TYPE_LABELS[type_key]
    comp   = completeness.get(f"{site_id}_{type_key}")

    return f"""
    <h3 class="measured-subtitle">{label}</h3>
    {_completeness_badge_html(comp)}
    <div class="charts-row two-col">
      <div class="chart-panel">
        <h3 class="panel-title">Évolution mensuelle</h3>
        <div class="chart-wrap">
          <img src="{base}_monthly_{type_key}.png" alt="Évolution mensuelle — {label}" class="chart-img">
        </div>
      </div>
      <div class="chart-panel">
        <h3 class="panel-title">Profil journalier typique</h3>
        <div class="chart-wrap">
          <img src="{base}_typical_day_{type_key}.png" alt="Profil journalier typique — {label}" class="chart-img">
        </div>
      </div>
    </div>
    <div class="chart-panel">
      <h3 class="panel-title">Carte thermique</h3>
      <div class="chart-wrap">
        <img src="{base}_heatmap_{type_key}.png" alt="Carte thermique — {label}" class="chart-img">
      </div>
    </div>
"""


# ── Explorateur de données (chronologie, vue annuelle, par site) ────────────
# Vit sur installations/index.html, sous les fiches "en bref" — pas sur la
# page d'accueil, qui reste une page d'atterrissage (mission + CTA + cartes).
def _dashboard_sections_html(depth: int) -> str:
    prefix = "../" if depth else ""
    conso_label = TYPE_LABELS["consommation"]
    prod_label  = TYPE_LABELS["production"]
    first_site  = next(
        sid for sid in SITE_ORDER if SITES[sid]["files"].get("consommation") is not None
    )
    return f"""
  <!-- ── Chronologie ─────────────────────────────────────────────────────── -->
  <section id="sec-timeline">
    <h2>Évolution des installations</h2>
    <p class="section-intro">
      {len(PV_SITE_ORDER)} installations photovoltaïques actives, de juin&nbsp;2017 à aujourd'hui.
      Chaque barre représente la période de mesure disponible pour une installation.
    </p>
    <div class="chart-wrap">
      <img src="{prefix}assets/images/timeline.png"
           alt="Chronologie des installations Enerko"
           class="chart-img">
    </div>
  </section>

  <!-- ── Vue d'ensemble annuelle ─────────────────────────────────────────── -->
  <section id="sec-annual">
    <h2>Vue d'ensemble annuelle</h2>
    <p class="section-intro">
      Totaux annuels par site, en MWh. Utilisez les boutons pour
      basculer entre {conso_label.lower()} et production.
    </p>
    <div class="toggle-group" id="annual-toggle" role="group" aria-label="Type de données">
      <button class="toggle-btn active" data-type="consommation">{conso_label}</button>
      <button class="toggle-btn"        data-type="production">{prod_label}</button>
    </div>
    <div class="chart-wrap">
      <img src="{prefix}assets/images/annual_overview_consommation.png"
           alt="{conso_label} annuelle par site"
           class="annual-img chart-img" data-type="consommation">
      <img src="{prefix}assets/images/annual_overview_production.png"
           alt="Production annuelle par site"
           class="annual-img chart-img" data-type="production" style="display:none">
    </div>
  </section>

  <!-- ── Explorateur par site ────────────────────────────────────────────── -->
  <section id="sec-sites">
    <h2>Explorer par site</h2>
    <p class="section-intro">
      Choisissez d'abord le type de données, puis le site — seuls ceux
      disposant de ce type de mesure sont proposés. Un site d'{conso_label.lower()}
      est un bâtiment raccordé au réseau ; un site de production est une
      installation photovoltaïque.
    </p>

    <div class="controls">
      <div class="control-group">
        <label>Type de données</label>
        <div class="toggle-group" id="site-type-toggle" role="group" aria-label="Type de données">
          <button class="toggle-btn active" data-type="consommation">{conso_label}</button>
          <button class="toggle-btn"        data-type="production">{prod_label}</button>
        </div>
      </div>
      <div class="control-group">
        <label for="site-select">Site</label>
        <select id="site-select" aria-label="Sélection du site"></select>
      </div>

      <div class="control-group">
        <label>Complétude des données</label>
        <div class="completeness-badge" id="completeness-badge">
          <span id="completeness-pct">–</span>
        </div>
      </div>
    </div>

    <p class="completeness-detail" id="completeness-detail"></p>

    <!-- Ligne 1 : mensuel + profil journalier -->
    <div class="charts-row two-col">

      <div class="chart-panel">
        <h3 class="panel-title">Évolution mensuelle</h3>
        <p class="panel-desc">Totaux mensuels en MWh — une courbe par année.</p>
        <div class="chart-wrap">
          <img id="chart-monthly"
               src="{prefix}assets/images/{first_site}_monthly_consommation.png"
               alt="Évolution mensuelle"
               class="chart-img">
        </div>
      </div>

      <div class="chart-panel">
        <h3 class="panel-title">Profil journalier typique</h3>
        <p class="panel-desc">Puissance moyenne sur 15 min, par saison (kW).</p>
        <div class="chart-wrap">
          <img id="chart-typical"
               src="{prefix}assets/images/{first_site}_typical_day_consommation.png"
               alt="Profil journalier typique"
               class="chart-img">
        </div>
      </div>

    </div>

    <!-- Ligne 2 : heatmap pleine largeur -->
    <div class="chart-panel">
      <h3 class="panel-title">Carte thermique</h3>
      <p class="panel-desc">Intensité heure par heure sur l'année la plus récente disponible.</p>
      <div class="chart-wrap">
        <img id="chart-heatmap"
             src="{prefix}assets/images/{first_site}_heatmap_consommation.png"
             alt="Carte thermique"
             class="chart-img">
      </div>
    </div>

  </section>"""


def _dashboard_script_html(depth: int) -> str:
    prefix        = "../" if depth else ""
    sites_by_type = _sites_by_type_json()
    completeness  = _completeness_json()
    first_site    = next(
        sid for sid in SITE_ORDER if SITES[sid]["files"].get("consommation") is not None
    )
    return f"""<script>
(function () {{
  "use strict";

  var siteSel   = document.getElementById("site-select");
  var imgMonth  = document.getElementById("chart-monthly");
  var imgTyp    = document.getElementById("chart-typical");
  var imgHeat   = document.getElementById("chart-heatmap");
  var compBadge  = document.getElementById("completeness-badge");
  var compPct    = document.getElementById("completeness-pct");
  var compDetail = document.getElementById("completeness-detail");

  var SITES_BY_TYPE = {sites_by_type};

  var currentType = "consommation";
  var currentSite = "{first_site}";
  var completenessData = {completeness};

  function populateSiteSelect() {{
    var options = SITES_BY_TYPE[currentType] || [];
    var keepSite = options.some(function (o) {{ return o.id === currentSite; }});
    if (!keepSite) {{
      currentSite = options.length ? options[0].id : null;
    }}
    siteSel.innerHTML = "";
    options.forEach(function (o) {{
      var opt = document.createElement("option");
      opt.value = o.id;
      opt.textContent = o.label;
      if (o.id === currentSite) opt.selected = true;
      siteSel.appendChild(opt);
    }});
  }}

  function refreshSiteCharts() {{
    if (!currentSite) return;
    var base   = "{prefix}assets/images/" + currentSite;
    var suffix = "_" + currentType + ".png";
    imgMonth.src = base + "_monthly"     + suffix;
    imgTyp.src   = base + "_typical_day" + suffix;
    imgHeat.src  = base + "_heatmap"     + suffix;
  }}

  function refreshCompleteness() {{
    var c = (completenessData && currentSite)
      ? completenessData[currentSite + "_" + currentType] : null;
    compBadge.classList.remove("good", "warn", "bad");

    if (!c) {{
      compPct.textContent = "n/d";
      compDetail.textContent = "";
      return;
    }}

    var pctPresent = (100 - c.pct_missing).toFixed(1);
    compPct.textContent = pctPresent + "% complet (" + c.start + " → " + c.end + ")";
    compBadge.classList.add(c.pct_missing < 2 ? "good" : c.pct_missing < 15 ? "warn" : "bad");

    if (c.gaps.length) {{
      compDetail.textContent = "Trous : " + c.gaps.map(function (g) {{
        return g.start + " → " + g.end + " (" + g.days + " j)";
      }}).join("  ·  ");
    }} else {{
      compDetail.textContent = "Aucun trou significatif détecté.";
    }}
  }}

  // Sélecteur de site
  siteSel.addEventListener("change", function () {{
    currentSite = this.value;
    refreshSiteCharts();
    refreshCompleteness();
  }});

  // Toggle type (section sites) : refiltre la liste des installations
  document.querySelectorAll("#site-type-toggle .toggle-btn").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      document.querySelectorAll("#site-type-toggle .toggle-btn")
              .forEach(function (b) {{ b.classList.remove("active"); }});
      this.classList.add("active");
      currentType = this.dataset.type;
      populateSiteSelect();
      refreshSiteCharts();
      refreshCompleteness();
    }});
  }});

  populateSiteSelect();
  refreshSiteCharts();
  refreshCompleteness();

  // Toggle type (section annuelle — indépendant)
  document.querySelectorAll("#annual-toggle .toggle-btn").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      document.querySelectorAll("#annual-toggle .toggle-btn")
              .forEach(function (b) {{ b.classList.remove("active"); }});
      this.classList.add("active");
      var t = this.dataset.type;
      document.querySelectorAll(".annual-img").forEach(function (img) {{
        img.style.display = (img.dataset.type === t) ? "block" : "none";
      }});
    }});
  }});

}})();
</script>"""


# ── Page d'accueil ───────────────────────────────────────────────────────────
# Page d'atterrissage uniquement : mission + CTA + cartes "en bref". Le
# tableau de bord (chronologie, vue annuelle, explorateur par site) vit sur
# installations/index.html, pas ici — cf. _dashboard_sections_html().
def build_index_html() -> str:
    today   = date.today().strftime("%d/%m/%Y")
    address = ", ".join(CONTACT["address_lines"])

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Enerko — Coopérative Solaire</title>
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

{_header_html(0)}

{_nav_html("accueil", 0)}

<main>
{_hero_html()}

  <section id="sec-installations-brief">
    <h2>Les installations en un coup d'œil</h2>
    <p class="section-intro">
      Surface, puissance, autoconsommation et financement de chaque installation
      photovoltaïque Enerko. Cliquez sur une fiche pour le détail complet.
    </p>
    <div class="install-cards">{_install_cards_html(0)}
    </div>
  </section>

</main>

<footer>
  <p>Enerko Coopérative Solaire &mdash; {address} &mdash;
     <a href="mailto:{CONTACT["email"]}">{CONTACT["email"]}</a></p>
</footer>

</body>
</html>
"""


# ── Pages installations ───────────────────────────────────────────────────────
def build_installation_html(iid: str, completeness: dict, today: str) -> str:
    inst  = INSTALLATIONS[iid]
    depth = 1

    measured_blocks = "".join(
        _building_measured_html(b, depth, completeness) for b in inst["buildings"]
    )

    sections = inst["sections"]
    communaute_paragraphs = "".join(f"<p>{p}</p>" for p in sections["communaute"])

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{inst["name"]} — Enerko</title>
  <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>

{_header_html(depth)}

{_nav_html("installations", depth)}

<main>

  <section id="install-overview">
    <a class="back-link" href="../index.html">← Retour au tableau de bord</a>
    <div class="install-hero">
      <h2>{inst["name"]}</h2>
      <p class="install-address">{inst["address"]}</p>
    </div>

    {_photo_gallery_html(inst["photos"], depth)}

    <div class="install-layout">
      <div class="install-main">
        <h3>Description</h3>
        <p>{inst["description"]}</p>

        <h3>Plus de détails</h3>
        <h4>L'installation PV</h4>
        <p>{sections["installation_pv"]}</p>
        <h4>Le financement</h4>
        <p>{sections["financement"]}</p>
        <h4>{sections["communaute_titre"]}</h4>
        {communaute_paragraphs}
      </div>

      <div class="install-sidebar">
        <h3>L'installation en bref</h3>
        {_brief_list_html(inst["brief"])}
        {_map_embed_html(inst["address"])}
      </div>
    </div>
  </section>

  <section id="install-data">
    <h2>Données mesurées</h2>
    <p class="section-intro">
      Séries mesurées SIG au pas de 15 minutes pour cette installation —
      mêmes graphiques que l'explorateur de la page d'accueil.
    </p>
    {_data_note_html(inst["data_note"])}
    <div class="measured-section">{measured_blocks}
    </div>
  </section>

</main>

<footer>
  <p>Données&nbsp;: SIG (Services Industriels de Genève) &mdash;
     Enerko Coopérative Solaire &mdash;
     Visualisation générée le {today}</p>
</footer>

</body>
</html>
"""


# ── Pages institutionnelles (contenu éditorial, cf. config.py) ──────────────
def _page_shell(
    title: str, active: str, depth: int, body: str, today: str,
    data_footer: bool = False, extra_html: str = "",
) -> str:
    """Squelette commun (header/nav/main/footer) pour les pages de contenu
    éditorial — évite de répéter le header/footer 6 fois.

    data_footer=False (défaut) : footer "coordonnées de contact" — pour les
    pages qui n'affichent aucune visualisation générée.
    data_footer=True : footer "Visualisation générée le [date]" — réservé aux
    pages qui affichent effectivement des graphiques générés par le pipeline
    (ex. installations/index.html, qui héberge l'explorateur de données).

    extra_html : contenu additionnel injecté après le footer, avant
    </body> — utilisé pour le <script> de l'explorateur de données.
    """
    prefix = "../" if depth else ""
    if data_footer:
        footer_html = f"""<footer>
  <p>Données&nbsp;: SIG (Services Industriels de Genève) &mdash;
     Enerko Coopérative Solaire &mdash;
     Visualisation générée le {today}</p>
</footer>"""
    else:
        address = ", ".join(CONTACT["address_lines"])
        footer_html = f"""<footer>
  <p>Enerko Coopérative Solaire &mdash; {address} &mdash;
     <a href="mailto:{CONTACT["email"]}">{CONTACT["email"]}</a></p>
</footer>"""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Enerko</title>
  <link rel="stylesheet" href="{prefix}assets/css/style.css">
</head>
<body>

{_header_html(depth)}

{_nav_html(active, depth)}

<main>
{body}
</main>

{footer_html}

{extra_html}
</body>
</html>
"""


def build_installations_index_html(today: str) -> str:
    depth = 1
    body = f"""
  <section id="sec-installations">
    <a class="back-link" href="../index.html">← Retour à l'accueil</a>
    <h2>Nos installations photovoltaïques</h2>
    <p class="section-intro">
      Enerko finance et exploite des installations photovoltaïques en
      autoconsommation collective à Genève. Cliquez sur une fiche pour le
      détail complet — description technique, financement, communauté
      d'autoconsommateurs et données mesurées.
    </p>
    <nav class="subnav" aria-label="Sections de cette page">
      <a href="#sec-installations">Vue d'ensemble</a>
      <a href="#sec-timeline">Chronologie</a>
      <a href="#sec-annual">Vue annuelle</a>
      <a href="#sec-sites">Données par site</a>
    </nav>
    <div class="install-cards">{_install_cards_html(depth)}
    </div>
  </section>
{_dashboard_sections_html(depth)}"""
    return _page_shell(
        "Installations", "installations", depth, body, today,
        data_footer=True, extra_html=_dashboard_script_html(depth),
    )


def build_enerko_html(today: str) -> str:
    depth = 0
    body = f"""
  <section id="sec-about">
    <h2>Enerko</h2>
    <div class="about-layout">
      <div class="about-tagline">
        <img class="about-logo" src="assets/images/logo-enerko.png" alt="Enerko — coopérAction énergEthique">
      </div>
      <div class="about-text">
        <p>{ABOUT["text"]}</p>
      </div>
    </div>
    {_stat_tiles_html()}
    {_cta_band_html(
        "Envie de rejoindre l'aventure ?",
        "Devenez sociétaire d'Enerko pour financer de futures installations "
        "photovoltaïques, ou consultez le détail de nos conditions d'investissement.",
        [
            ("Devenir membre", "devenir-membre.html", "btn-primary"),
            ("Investir",        "investir.html",        "btn-secondary"),
        ],
        depth,
    )}
  </section>"""
    return _page_shell("Enerko", "enerko", depth, body, today)


def _autoconsommer_diagram_html() -> str:
    return """
    <div class="diagram-wrap">
      <img class="diagram-img" src="assets/images/autoconsommation_collective.png"
           alt="Schéma de l'autoconsommation collective : l'électricité solaire produite en toiture est autoconsommée par le bâtiment, le surplus est vendu à SIG (12 cts/kWh) et le manque est acheté à SIG (24 cts/kWh).">
    </div>"""


def build_autoconsommer_html(today: str) -> str:
    depth = 0
    paragraphs = "".join(f"<p>{p}</p>" for p in AUTOCONSOMMER["paragraphs"])
    body = f"""
  <section id="sec-autoconsommer">
    <h2>Autoconsommer</h2>
    <p class="section-intro">{AUTOCONSOMMER["intro"]}</p>
    {paragraphs}
    {_autoconsommer_diagram_html()}
    {_cta_band_html(
        "Déjà locataire d'un bâtiment équipé ?",
        AUTOCONSOMMER["cta_text"],
        [
            ("Devenir membre", "devenir-membre.html", "btn-primary"),
            ("Nous contacter",  "contact.html",          "btn-secondary"),
        ],
        depth,
    )}
  </section>"""
    return _page_shell("Autoconsommer", "autoconsommer", depth, body, today)


def _investir_section_html(s: dict, idx: int) -> str:
    paragraphs = "".join(f"<p>{p}</p>" for p in s.get("paragraphs", []))
    charges_revenus = ""
    if "charges" in s:
        charges_items = "".join(f"<li>{c}</li>" for c in s["charges"])
        revenus_items = "".join(f"<li>{r}</li>" for r in s["revenus"])
        charges_revenus = f"""
    <div class="charges-revenus-grid">
      <div class="charges-box">
        <h4>{s["charges_title"]}</h4>
        <ul>{charges_items}</ul>
      </div>
      <div class="revenus-box">
        <h4>{s["revenus_title"]}</h4>
        <ul>{revenus_items}</ul>
      </div>
    </div>"""
    bullets = ""
    if "bullets" in s:
        bullet_items = "".join(f"<li>{b}</li>" for b in s["bullets"])
        bullets = f'<ul class="plain-bullets">{bullet_items}</ul>'
    paragraphs_after = "".join(f"<p>{p}</p>" for p in s.get("paragraphs_after", []))
    closing = f'<p>{s["closing"]}</p>' if "closing" in s else ""

    return f"""
    <div id="{s["anchor"]}" class="investir-section">
      <div class="investir-section-head">
        <span class="investir-step" aria-label="Étape {idx} : {s["nav_label"]}">{idx}</span>
        <h3>{s["title"]}</h3>
      </div>
      {paragraphs}
      {charges_revenus}
      {closing}
      {bullets}
      {paragraphs_after}
    </div>"""


def build_investir_html(today: str) -> str:
    depth = 0
    sections_html = "".join(
        _investir_section_html(s, idx) for idx, s in enumerate(INVESTIR["sections"], start=1)
    )
    body = f"""
  <section id="sec-investir">
    <h2>Investir</h2>
    <p class="section-intro">{INVESTIR["summary"]}</p>
    {sections_html}
    {_cta_band_html(
        "Prêt·e à investir ?",
        "Souscrivez des parts sociales pour financer de futures installations "
        "photovoltaïques, ou contactez-nous si vous avez des questions.",
        [
            ("Devenir membre", "devenir-membre.html", "btn-primary"),
            ("Nous contacter",  "contact.html",          "btn-secondary"),
        ],
        depth,
    )}
  </section>"""
    return _page_shell("Investir", "investir", depth, body, today)


def _devenir_membre_script_html() -> str:
    return f"""<script>
(function () {{
  "use strict";

  var form = document.getElementById("membership-form");
  if (!form) return;

  form.addEventListener("submit", function (e) {{
    e.preventDefault();
    if (!form.reportValidity()) return;

    var name  = document.getElementById("member-name").value.trim();
    var email = document.getElementById("member-email").value.trim();

    var subject = "Demande d'adhésion — Enerko";
    var body =
      "Nom : " + name + "\\n" +
      "Email : " + email + "\\n\\n" +
      "Je souhaite devenir membre d'Enerko.";

    window.location.href =
      "mailto:{DEVENIR_MEMBRE["email"]}" +
      "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(body);
  }});
}})();
</script>"""


def build_devenir_membre_html(today: str) -> str:
    depth = 0
    body = f"""
  <section id="sec-devenir-membre">
    <h2>Devenir membre</h2>
    <p>{DEVENIR_MEMBRE["text"]}
       <a href="mailto:{DEVENIR_MEMBRE["email"]}">{DEVENIR_MEMBRE["email"]}</a></p>

    <form id="membership-form" class="membership-form" novalidate>
      <div class="form-field">
        <label for="member-name">Nom</label>
        <input type="text" id="member-name" name="name" autocomplete="name" required>
      </div>
      <div class="form-field">
        <label for="member-email">Email</label>
        <input type="email" id="member-email" name="email" autocomplete="email" required>
      </div>
      <button type="submit" class="btn btn-primary">Envoyer ma demande</button>
    </form>
  </section>"""
    return _page_shell(
        "Devenir membre", "devenir-membre", depth, body, today,
        extra_html=_devenir_membre_script_html(),
    )


def build_contact_html(today: str) -> str:
    depth = 0
    address = "<br>".join(CONTACT["address_lines"])
    body = f"""
  <section id="sec-contact">
    <h2>Contact</h2>
    <div class="contact-block">
      <p>{address}</p>
      <p><a href="mailto:{CONTACT["email"]}">{CONTACT["email"]}</a></p>
    </div>
  </section>"""
    return _page_shell("Contact", "contact", depth, body, today)


def build_liens_html(today: str) -> str:
    depth = 0
    cards = "".join(
        f"""
      <a class="lien-card" href="{l["url"]}" target="_blank" rel="noopener">
        <img class="lien-logo" src="assets/images/{l["logo"]}" alt="{l["name"]}">
        <h3>{l["name"]}</h3>
        <p>{l["desc"]}</p>
      </a>""" for l in LIENS
    )
    body = f"""
  <section id="sec-liens">
    <h2>Liens utiles</h2>
    <div class="liens-grid">{cards}
    </div>
  </section>"""
    return _page_shell("Liens utiles", "liens", depth, body, today)


def _initials(name: str) -> str:
    return "".join(p[0] for p in name.split()[:2]).upper()


def build_equipe_html(today: str) -> str:
    depth = 0
    cards = "".join(
        f"""
      <div class="equipe-card">
        <div class="equipe-avatar">{_initials(m["name"])}</div>
        <h3>{m["name"]}</h3>
        <p class="equipe-role">{m["role"]}</p>
      </div>""" for m in EQUIPE
    )
    body = f"""
  <section id="sec-equipe">
    <h2>L'équipe</h2>
    <p class="section-intro">Les membres du comité et de l'équipe opérationnelle d'Enerko.</p>
    <div class="equipe-grid">{cards}
    </div>
  </section>"""
    return _page_shell("Équipe", "equipe", depth, body, today)


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    index_html = build_index_html()
    index_out  = DOCS_DIR / "index.html"
    index_out.write_text(index_html, encoding="utf-8")
    print(f"✓  {index_out} généré ({len(index_html):,} caractères)")

    today        = date.today().strftime("%d/%m/%Y")
    completeness = _completeness_dict()
    for iid in INSTALLATION_ORDER:
        inst = INSTALLATIONS[iid]
        html = build_installation_html(iid, completeness, today)
        out  = INSTALL_DIR / f"{inst['slug']}.html"
        out.write_text(html, encoding="utf-8")
        print(f"✓  {out} généré ({len(html):,} caractères)")

    pages = [
        (build_installations_index_html(today), INSTALL_DIR / "index.html"),
        (build_enerko_html(today),               DOCS_DIR / "enerko.html"),
        (build_equipe_html(today),                DOCS_DIR / "equipe.html"),
        (build_autoconsommer_html(today),         DOCS_DIR / "autoconsommer.html"),
        (build_investir_html(today),              DOCS_DIR / "investir.html"),
        (build_devenir_membre_html(today),        DOCS_DIR / "devenir-membre.html"),
        (build_contact_html(today),               DOCS_DIR / "contact.html"),
        (build_liens_html(today),                 DOCS_DIR / "liens.html"),
    ]
    for html, out in pages:
        out.write_text(html, encoding="utf-8")
        print(f"✓  {out} généré ({len(html):,} caractères)")


if __name__ == "__main__":
    main()
