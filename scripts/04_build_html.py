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


# ── Composants HTML réutilisés (accueil + fiches installations) ─────────────
def _nav_links(depth: int):
    prefix = "../" if depth else ""
    links = [("accueil", "Accueil", f"{prefix}index.html")]
    for iid in INSTALLATION_ORDER:
        inst = INSTALLATIONS[iid]
        links.append((inst["slug"], inst["name"], f"{prefix}installations/{inst['slug']}.html"))
    return links


def _nav_html(active: str, depth: int) -> str:
    items = []
    for slug, label, href in _nav_links(depth):
        cls = ' class="active"' if slug == active else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return f'<nav class="top-nav"><div class="top-nav-inner">{"".join(items)}</div></nav>'


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


def _install_cards_html() -> str:
    cards = []
    for iid in INSTALLATION_ORDER:
        inst = INSTALLATIONS[iid]
        cards.append(f"""
      <div class="install-card">
        <h3>{inst["name"]}</h3>
        <p class="install-address">{inst["address"]}</p>
        {_brief_list_html(inst["brief"])}
        <a class="install-card-link" href="installations/{inst["slug"]}.html">Voir la fiche complète →</a>
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
    return f'{badge}<p class="completeness-detail">{detail}</p>'


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


# ── Page d'accueil ───────────────────────────────────────────────────────────
def build_index_html() -> str:
    today          = date.today().strftime("%d/%m/%Y")
    sites_by_type  = _sites_by_type_json()
    completeness   = _completeness_json()
    first_site     = next(
        sid for sid in SITE_ORDER if SITES[sid]["files"].get("consommation") is not None
    )
    conso_label = TYPE_LABELS["consommation"]
    prod_label  = TYPE_LABELS["production"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Enerko — Courbes de charge</title>
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

<header>
  <div class="header-inner">
    <h1>Enerko</h1>
    <p class="subtitle">Coopérative Solaire — Courbes de charge des installations photovoltaïques</p>
  </div>
</header>

{_nav_html("accueil", 0)}

<main>

  <!-- ── Section 0 : Installations en bref ────────────────────────────────── -->
  <section id="sec-installations-brief">
    <h2>Les installations en un coup d'œil</h2>
    <p class="section-intro">
      Surface, puissance, autoconsommation et financement de chaque installation
      photovoltaïque Enerko. Cliquez sur une fiche pour le détail complet.
    </p>
    <div class="install-cards">{_install_cards_html()}
    </div>
  </section>

  <!-- ── Section 1 : Chronologie ─────────────────────────────────────────── -->
  <section id="sec-timeline">
    <h2>Évolution des installations</h2>
    <p class="section-intro">
      {len(PV_SITE_ORDER)} installations photovoltaïques actives, de juin&nbsp;2017 à aujourd'hui.
      Chaque barre représente la période de mesure disponible pour une installation.
    </p>
    <div class="chart-wrap">
      <img src="assets/images/timeline.png"
           alt="Chronologie des installations Enerko"
           class="chart-img">
    </div>
  </section>

  <!-- ── Section 2 : Vue d'ensemble annuelle ──────────────────────────────── -->
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
      <img src="assets/images/annual_overview_consommation.png"
           alt="{conso_label} annuelle par site"
           class="annual-img chart-img" data-type="consommation">
      <img src="assets/images/annual_overview_production.png"
           alt="Production annuelle par site"
           class="annual-img chart-img" data-type="production" style="display:none">
    </div>
  </section>

  <!-- ── Section 3 : Explorateur par site ──────────────────────────────────── -->
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
               src="assets/images/{first_site}_monthly_consommation.png"
               alt="Évolution mensuelle"
               class="chart-img">
        </div>
      </div>

      <div class="chart-panel">
        <h3 class="panel-title">Profil journalier typique</h3>
        <p class="panel-desc">Puissance moyenne sur 15 min, par saison (kW).</p>
        <div class="chart-wrap">
          <img id="chart-typical"
               src="assets/images/{first_site}_typical_day_consommation.png"
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
             src="assets/images/{first_site}_heatmap_consommation.png"
             alt="Carte thermique"
             class="chart-img">
      </div>
    </div>

  </section>

</main>

<footer>
  <p>Données&nbsp;: SIG (Services Industriels de Genève) &mdash;
     Enerko Coopérative Solaire &mdash;
     Visualisation générée le {today}</p>
</footer>

<script>
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
    var base   = "assets/images/" + currentSite;
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
</script>

</body>
</html>
"""


# ── Pages installations ───────────────────────────────────────────────────────
def build_installation_html(iid: str, completeness: dict, today: str) -> str:
    inst  = INSTALLATIONS[iid]
    depth = 1

    types_present = [t for t in TYPES if inst["site_ids"].get(t) is not None]
    measured_blocks = "".join(
        _measured_type_block_html(inst["site_ids"][t], t, depth, completeness)
        for t in types_present
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

<header>
  <div class="header-inner">
    <h1>Enerko</h1>
    <p class="subtitle">Coopérative Solaire — Courbes de charge des installations photovoltaïques</p>
  </div>
</header>

{_nav_html(inst["slug"], depth)}

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


if __name__ == "__main__":
    main()
