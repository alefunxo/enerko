"""
04_stats.py — Chiffres-clés par installation (production annuelle, autoconsommation)

Lit les agrégats annuels (02_aggregate) et completeness.json, calcule les chiffres
affichés sur les pages, écrit docs/assets/data/stats.json puis réécrit ces valeurs
dans les pages HTML statiques, de sorte qu'une même valeur apparaisse partout
(cartes, fiches, descriptions meta, total de la page d'accueil).

Méthode
  - Années de référence : les 3 dernières années civiles COMPLÈTES de toutes les
    séries utilisées (hors année en cours, hors séries démarrées en cours d'année,
    hors années touchées par un trou de données).
  - Production annuelle : moyenne sur ces années, arrondie au millier de kWh.
    Mesurée seulement si TOUS les toits de l'installation ont une série de
    production ; sinon valeur nominale de config.INSTALLATIONS[...]["brief"].
  - Autoconsommation = 1 − injection réseau / production, sur les mêmes années
    (somme des années, pas moyenne de pourcentages). Les fichiers « consommation »
    mesurent le surplus injecté dans le réseau (voir config.TYPE_LABELS). Valeur
    nominale du brief si aucune série de production n'est associée.

Marqueurs dans le HTML (hand-maintained) :
  <!--stat:CLE-->valeur<!--/stat-->      texte courant, remplacé par la valeur
  <div class="meter" data-meter="CLE" …> jauge : libellé ARIA, valeur et largeur
  <meta name="description" …>            kWh/an et % réécrits (fiches installation)
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import AGG_DIR, DOCS_DIR, INSTALLATIONS  # noqa: E402

DATA_DIR_OUT = DOCS_DIR / "assets" / "data"
N_REF_YEARS = 3
MIN_REF_YEARS = 2
# Équivalent « logements genevois » : ~2 900 kWh/an par logement (déduit des
# textes d'origine : 35 000 kWh ≈ 12 logements, 140 000 kWh ≈ 50 logements).
KWH_PAR_LOGEMENT = 2900

# Installation → config.INSTALLATIONS, séries de production et séries d'injection
# réseau ("consommation") du même périmètre. Meyrin : SIG relève les 3 bâtiments
# via 2 points de comptage (Récréations 24 et 26), donc ces 2 séries couvrent
# toute l'installation (cf. config.INSTALLATIONS[...]["data_note"]).
# production_complete=False : pas de série de production → valeur nominale du brief.
INSTALLS = {
    "soubeyran": {
        "config": "install_soubeyran",
        "page": "installation-soubeyran.html",
        "production": [],
        "injection": ["site_a_consommation"],
        "production_complete": False,
        "toitures": 1,
    },
    "meyrin": {
        "config": "install_meyrin_recreations_24",
        "page": "installation-meyrin.html",
        "production": ["site_c_production", "site_d_production"],
        "injection": ["site_b_consommation", "site_c_consommation"],
        "production_complete": True,
        "toitures": 3,
    },
    "plo": {
        "config": "install_plan_les_ouates_vers_8",
        "page": "installation-plan-les-ouates.html",
        "production": ["site_f_production"],
        "injection": ["site_g_consommation"],
        "production_complete": True,
        "toitures": 1,
    },
}


def _annual(key: str) -> pd.Series:
    path = AGG_DIR / f"annual_{key}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} introuvable — lancer 02_aggregate.py d'abord")
    return pd.read_parquet(path)["valeur_mwh"]


def _full_years(comp: dict) -> set:
    """Années civiles entièrement couvertes par une série (cf. completeness.json)."""
    start = date.fromisoformat(comp["start"])
    end = date.fromisoformat(comp["end"])
    gaps = [(date.fromisoformat(g["start"]), date.fromisoformat(g["end"]))
            for g in comp.get("gaps", [])]
    years = set()
    for y in range(start.year, end.year + 1):
        first, last = date(y, 1, 1), date(y, 12, 31)
        if start > first or end < last:
            continue
        if any(g0 <= last and g1 >= first for g0, g1 in gaps):
            continue
        years.add(y)
    return years


def _round_int(x: float) -> int:
    return int(x + 0.5)


def compute() -> dict:
    comp = json.loads((DATA_DIR_OUT / "completeness.json").read_text(encoding="utf-8"))
    stats = {}

    for name, spec in INSTALLS.items():
        brief = INSTALLATIONS[spec["config"]]["brief"]
        series = spec["production"] + spec["injection"]
        years = set.intersection(*(_full_years(comp[k]) for k in series))
        ref = sorted(years)[-N_REF_YEARS:]
        have_ref = len(ref) >= MIN_REF_YEARS
        have_prod = bool(spec["production"])

        entry = {
            "puissance_kwc": brief["puissance_kwc"],
            "surface_m2": brief["surface_m2"],
            "toitures": spec["toitures"],
            "cout_chf": brief["cout_chf"],
            "reference_years": ref if have_prod and have_ref else [],
        }

        if have_prod and have_ref:
            prod_mwh = sum(_annual(k).loc[ref].sum() for k in spec["production"])
            inj_mwh = sum(_annual(k).loc[ref].sum() for k in spec["injection"])
            entry["measured_production_mwh_an"] = round(prod_mwh / len(ref), 1)
            entry["measured_injection_mwh_an"] = round(inj_mwh / len(ref), 1)
            entry["autoconso_pct"] = _round_int((1 - inj_mwh / prod_mwh) * 100)
            entry["autoconso_source"] = "measured"
        else:
            entry["autoconso_pct"] = brief["autoconsommation_pct"]
            entry["autoconso_source"] = "nominal"

        if entry["autoconso_source"] == "measured" and spec["production_complete"]:
            entry["production_kwh"] = _round_int(entry["measured_production_mwh_an"]) * 1000
            entry["production_source"] = "measured"
        else:
            entry["production_kwh"] = brief["production_kwh_an"]
            entry["production_source"] = "nominal"

        entry["logements"] = _round_int(entry["production_kwh"] / KWH_PAR_LOGEMENT)
        stats[name] = entry

    sites = list(stats.values())
    prod_kwh = sum(s["production_kwh"] for s in sites)
    autoconso = sum(s["production_kwh"] * s["autoconso_pct"] for s in sites) / prod_kwh
    stats["total"] = {
        "kwc": round(sum(s["puissance_kwc"] for s in sites), 1),
        "surface_m2": sum(s["surface_m2"] for s in sites),
        "toitures": sum(s["toitures"] for s in sites),
        "production_mwh": _round_int(prod_kwh / 1000),
        "cout_kchf": _round_int(sum(s["cout_chf"] for s in sites) / 1000),
        # moyenne pondérée par la production, arrondie à 5 % (texte courant)
        "autoconso_pct": 5 * _round_int(autoconso / 5),
    }
    return stats


# ── Réécriture des pages HTML ────────────────────────────────────────────────

def _nbsp_thousands(n: int) -> str:
    return f"{n:,}".replace(",", "&nbsp;")


def _fmt(key: str, value) -> str:
    leaf = key.split(".")[-1]
    if leaf in ("production_kwh", "surface_m2"):
        return _nbsp_thousands(value)
    if leaf in ("puissance_kwc", "kwc"):  # virgule décimale, sans « ,0 »
        return f"{value:g}".replace(".", ",")
    return str(value)


def _lookup(stats: dict, key: str):
    node = stats
    for part in key.split("."):
        node = node[part]
    return node


MARKER = re.compile(r"<!--stat:([\w.]+)-->.*?<!--/stat-->", re.DOTALL)
METER = re.compile(
    r'(<div class="meter" data-meter="([\w.]+)" role="img" aria-label=")[^"]*'
    r'("[^>]*>\s*<div class="meter__head"><span>([^<]*)</span>'
    r'<span class="meter__value">)[^<]*'
    r'(</span></div>\s*<div class="meter__track"><div class="meter__fill" style="width:)[\d.]+(%)'
)
META_DESC = re.compile(r"[\d,]+ kWc,\s*[\d ]+ kWh/an, \d+% d'autoconsommation")


def patch_html(path: Path, stats: dict, install: str = None) -> bool:
    with open(path, encoding="utf-8", newline="") as f:
        src = f.read()

    def marker(m):
        key = m.group(1)
        return f"<!--stat:{key}-->{_fmt(key, _lookup(stats, key))}<!--/stat-->"

    def meter(m):
        pct = _lookup(stats, m.group(2))
        label = m.group(4)
        return (f"{m.group(1)}{label} : {pct} pour cent{m.group(3)}{pct}&nbsp;%"
                f"{m.group(5)}{pct}{m.group(6)}")

    out = MARKER.sub(marker, src)
    out = METER.sub(meter, out)
    if install:
        s = stats[install]
        prod = f"{s['production_kwh']:,}".replace(",", " ")
        kwc = _fmt("puissance_kwc", s["puissance_kwc"])
        out = META_DESC.sub(
            f"{kwc} kWc, {prod} kWh/an, {s['autoconso_pct']}% d'autoconsommation", out)

    if out != src:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(out)
        return True
    return False


def main() -> None:
    stats = compute()
    DATA_DIR_OUT.mkdir(parents=True, exist_ok=True)
    (DATA_DIR_OUT / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("✓  stats.json")
    for name, s in stats.items():
        if name == "total":
            print(f"   total : {s['kwc']} kWc, {s['surface_m2']} m², {s['production_mwh']} MWh/an, "
                  f"{s['cout_kchf']} k CHF, autoconsommation moyenne ≈ {s['autoconso_pct']} %")
        else:
            print(f"   {name:10s} production {s['production_kwh']:>7,} kWh/an ({s['production_source']}), "
                  f"autoconsommation {s['autoconso_pct']} % ({s['autoconso_source']}"
                  f"{', ' + '–'.join(map(str, [s['reference_years'][0], s['reference_years'][-1]])) if s['reference_years'] else ''})")

    page_to_install = {spec["page"]: name for name, spec in INSTALLS.items()}
    for path in sorted(DOCS_DIR.glob("*.html")):
        if patch_html(path, stats, page_to_install.get(path.name)):
            print(f"✓  {path.name} mis à jour")


if __name__ == "__main__":
    main()
