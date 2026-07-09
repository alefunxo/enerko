"""
04_build_html.py — Génération de docs/index.html
Lit les noms de sites dans config.py et produit la page finale.
À relancer après chaque modification de config.py.

Usage : python scripts/04_build_html.py
"""

import sys
from datetime import date
from pathlib import Path

# Encodage UTF-8 pour les terminaux Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from config import SITES, SITE_ORDER, PV_SITE_ORDER, TYPES, TYPE_LABELS, DOCS_DIR


def _sites_by_type_json() -> str:
    """
    {"consommation": [{"id": "site_a", "label": "..."}, ...], "production": [...]}
    Sert à ne proposer, pour un type de données donné, que les installations
    qui possèdent effectivement ce type.
    """
    import json as _json

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
    return _json.dumps(by_type, ensure_ascii=False)


def build_html() -> str:
    today          = date.today().strftime("%d/%m/%Y")
    sites_by_type  = _sites_by_type_json()
    first_site     = next(
        sid for sid in SITE_ORDER if SITES[sid]["files"].get("consommation") is not None
    )

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

<main>

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
      Totaux annuels par installation, en MWh. Utilisez les boutons pour
      basculer entre consommation et production.
    </p>
    <div class="toggle-group" id="annual-toggle" role="group" aria-label="Type de données">
      <button class="toggle-btn active" data-type="consommation">Consommation</button>
      <button class="toggle-btn"        data-type="production">Production</button>
    </div>
    <div class="chart-wrap">
      <img src="assets/images/annual_overview_consommation.png"
           alt="Consommation annuelle par site"
           class="annual-img chart-img" data-type="consommation">
      <img src="assets/images/annual_overview_production.png"
           alt="Production annuelle par site"
           class="annual-img chart-img" data-type="production" style="display:none">
    </div>
  </section>

  <!-- ── Section 3 : Explorateur par installation ──────────────────────────── -->
  <section id="sec-sites">
    <h2>Explorer par installation</h2>
    <p class="section-intro">
      Choisissez d'abord le type de données, puis l'installation — seules
      celles disposant de ce type de mesure sont proposées.
    </p>

    <div class="controls">
      <div class="control-group">
        <label>Type de données</label>
        <div class="toggle-group" id="site-type-toggle" role="group" aria-label="Type de données">
          <button class="toggle-btn active" data-type="consommation">Consommation</button>
          <button class="toggle-btn"        data-type="production">Production</button>
        </div>
      </div>
      <div class="control-group">
        <label for="site-select">Installation</label>
        <select id="site-select" aria-label="Sélection de l'installation"></select>
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
  var completenessData = null;

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

  fetch("assets/data/completeness.json")
    .then(function (r) {{ return r.json(); }})
    .then(function (data) {{ completenessData = data; refreshCompleteness(); }})
    .catch(function () {{ /* pas de données de complétude disponibles */ }});

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


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    html = build_html()
    out  = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✓  {out} généré ({len(html):,} caractères)")


if __name__ == "__main__":
    main()
