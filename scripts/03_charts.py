"""
03_charts.py — Génération des graphiques PNG
Produit tous les graphiques dans docs/assets/images/.
Si les agrégats sont absents, génère un PNG "données non disponibles".

Usage : python scripts/03_charts.py
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    SITES, SITE_ORDER, PV_SITE_ORDER, TYPES, TYPE_LABELS,
    SAISONS, SAISON_COLORS, MOIS,
    AGG_DIR, IMAGES_DIR, DOCS_DIR,
)


def _load_completeness() -> dict:
    f = DOCS_DIR / "assets" / "data" / "completeness.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def _gap_years(comp) -> set:
    """Années civiles chevauchant un trou de données significatif (≥ 2 jours)."""
    if not comp:
        return set()
    years = set()
    for g in comp.get("gaps", []):
        start, end = pd.Timestamp(g["start"]), pd.Timestamp(g["end"])
        years.update(range(start.year, end.year + 1))
    return years

# ── Style global — couleurs institutionnelles Enerko (noir + orange) ────────────
NAVY   = "#181614"   # noir Enerko (titres, axes) — anciennement bleu marine
YELLOW = "#E8720C"   # orange Enerko (accents)   — anciennement jaune
BG     = "#FFFFFF"
GRID   = "#E8E8E8"
TEXT   = "#2C3E50"

plt.rcParams.update({
    "figure.facecolor":   BG,
    "axes.facecolor":     BG,
    "axes.grid":          True,
    "grid.color":         GRID,
    "grid.linewidth":     0.8,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   True,
    "axes.spines.bottom": True,
    "axes.edgecolor":     "#CCCCCC",
    "axes.labelcolor":    TEXT,
    "axes.titlecolor":    NAVY,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.titlepad":      12,
    "xtick.color":        TEXT,
    "ytick.color":        TEXT,
    "font.family":        "DejaVu Sans",
    "font.size":          10,
    "legend.frameon":     False,
    "legend.fontsize":    9,
    "figure.dpi":         150,
    "savefig.dpi":        150,
    "savefig.bbox":       "tight",
    "savefig.facecolor":  BG,
    "savefig.pad_inches": 0.15,
})


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def make_placeholder(output_path: Path, site_name: str, type_label: str) -> None:
    """PNG 'Données non disponibles' pour les combinaisons sans fichier source."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_axis_off()
    ax.text(0.5, 0.55, "Données non disponibles",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=16, color="#AAAAAA", fontweight="bold")
    ax.text(0.5, 0.38, f"{site_name} — {type_label}",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=11, color="#CCCCCC")
    _save(fig, output_path)


# ── 1. Chronologie ─────────────────────────────────────────────────────────────
def chart_timeline() -> None:
    """Uniquement les installations PV — les points de consommation associés
    à un même bâtiment ne sont pas des installations."""
    today = pd.Timestamp.today().normalize()
    sites = [SITES[sid] for sid in reversed(PV_SITE_ORDER)]  # du bas vers le haut

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_facecolor(BG)

    for i, site in enumerate(sites):
        start = pd.Timestamp(site["online_since"] + "-01")
        dur   = (today - start).days
        bar = ax.barh(
            site["name"], dur, left=start,
            color=site["color"], height=0.55, zorder=3,
        )
        # Étiquette "depuis AAAA"
        label_x = start + pd.Timedelta(days=30)
        ax.text(
            label_x, i, f"  {site['online_since']}",
            va="center", ha="left", fontsize=8.5, color="white", fontweight="bold",
        )

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(pd.Timestamp("2017-01-01"), today + pd.Timedelta(days=120))
    ax.set_xlabel("Année", color=TEXT)
    ax.set_title("Chronologie des installations Enerko")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)

    _save(fig, IMAGES_DIR / "timeline.png")
    print("  ✓  timeline.png")


# ── 2. Vue d'ensemble annuelle ─────────────────────────────────────────────────
def chart_annual_overview(type_key: str) -> None:
    completeness = _load_completeness()

    # Collecter les données annuelles de tous les sites
    all_years = set()
    site_data: dict[str, pd.Series] = {}

    for site_id in SITE_ORDER:
        f = AGG_DIR / f"annual_{site_id}_{type_key}.parquet"
        if not f.exists():
            continue
        s = pd.read_parquet(f)["valeur_mwh"]
        site_data[site_id] = s
        all_years.update(s.index.tolist())

    if not all_years:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_axis_off()
        ax.text(0.5, 0.5, "Aucune donnée disponible",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=14, color="#AAAAAA")
        _save(fig, IMAGES_DIR / f"annual_overview_{type_key}.png")
        print(f"  ⚠  annual_overview_{type_key}.png (vide)")
        return

    years = sorted(all_years)
    x     = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(years))
    any_gap_year = False

    for site_id in SITE_ORDER:
        if site_id not in site_data:
            continue
        site = SITES[site_id]
        vals = np.array([site_data[site_id].get(y, 0.0) for y in years])
        bars = ax.bar(x, vals, bottom=bottom, label=site["name"],
                       color=site["color"], width=0.65, zorder=3)

        gap_years = _gap_years(completeness.get(f"{site_id}_{type_key}"))
        for xi, yr in enumerate(years):
            if yr in gap_years and vals[xi] > 0:
                bars[xi].set_hatch("///")
                bars[xi].set_edgecolor("white")
                bars[xi].set_linewidth(0.6)
                any_gap_year = True

        bottom += vals

    # Total au-dessus de chaque barre, avec marge proportionnelle au maximum
    top = bottom.max() if bottom.max() > 0 else 1.0
    label_offset = top * 0.012
    for xi, tot in enumerate(bottom):
        if tot > 0:
            ax.text(xi, tot + label_offset, f"{tot:.0f}", ha="center", va="bottom",
                    fontsize=8, color=TEXT)

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_ylabel("MWh", color=TEXT)
    ax.set_title(f"{TYPE_LABELS[type_key]} annuelle totale par installation (MWh)")
    # Légende hors zone de tracé pour ne jamais chevaucher les barres/étiquettes
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18),
              ncol=min(len(site_data), 3), frameon=False, fontsize=9)
    ax.set_ylim(0, top * 1.15)

    if any_gap_year:
        ax.text(0.0, -0.13, "///  Année avec trou de données significatif (voir badge de complétude)",
                transform=ax.transAxes, fontsize=7.5, color=TEXT, ha="left")

    _save(fig, IMAGES_DIR / f"annual_overview_{type_key}.png")
    print(f"  ✓  annual_overview_{type_key}.png")


# ── 3. Évolution mensuelle par site ───────────────────────────────────────────
def chart_monthly(site_id: str, type_key: str) -> None:
    site = SITES[site_id]
    out  = IMAGES_DIR / f"{site_id}_monthly_{type_key}.png"
    f    = AGG_DIR / f"monthly_{site_id}_{type_key}.parquet"

    if not f.exists():
        make_placeholder(out, site["name"], TYPE_LABELS[type_key])
        return

    df = pd.read_parquet(f)
    df.index = pd.to_datetime(df.index)
    df["annee"] = df.index.year
    df["mois"]  = df.index.month

    years = sorted(df["annee"].unique())
    cmap  = plt.cm.get_cmap("Blues", max(len(years) + 2, 4))

    fig, ax = plt.subplots(figsize=(12, 5))

    for i, year in enumerate(years):
        sub = df[df["annee"] == year].set_index("mois")["valeur_mwh"]
        sub = sub.reindex(range(1, 13), fill_value=np.nan)
        color = cmap(0.3 + 0.7 * i / max(len(years) - 1, 1))
        lw = 2.0 if year == years[-1] else 1.2
        ax.plot(range(1, 13), sub.values, marker="o", markersize=3,
                linewidth=lw, color=color, label=str(year), zorder=3)

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MOIS)
    ax.set_ylabel("MWh", color=TEXT)
    ax.set_title(f"{site['name']} — {TYPE_LABELS[type_key]} mensuelle (MWh)")
    ax.legend(title="Année", loc="upper right", ncol=3, fontsize=8)
    ax.set_xlim(0.5, 12.5)

    _save(fig, out)
    print(f"  ✓  {out.name}")


# ── 4. Profil journalier typique ───────────────────────────────────────────────
def chart_typical_day(site_id: str, type_key: str) -> None:
    site = SITES[site_id]
    out  = IMAGES_DIR / f"{site_id}_typical_day_{type_key}.png"
    f    = AGG_DIR / f"typical_day_{site_id}_{type_key}.parquet"

    if not f.exists():
        make_placeholder(out, site["name"], TYPE_LABELS[type_key])
        return

    df = pd.read_parquet(f)  # index = slot 0-95, colonnes = saisons
    heures = np.arange(96) / 4.0  # 0.00, 0.25, 0.50, …, 23.75

    fig, ax = plt.subplots(figsize=(12, 5))

    for saison in SAISONS:
        if saison not in df.columns:
            continue
        vals = df[saison].values
        ax.plot(heures, vals, linewidth=2, color=SAISON_COLORS[saison],
                label=saison, zorder=3)
        ax.fill_between(heures, vals, alpha=0.08, color=SAISON_COLORS[saison])

    ax.set_xlabel("Heure", color=TEXT)
    ax.set_ylabel("kW (puissance moyenne)", color=TEXT)
    ax.set_title(f"{site['name']} — Profil journalier typique par saison")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}h" for h in range(0, 25, 2)])
    ax.legend(loc="upper right")

    _save(fig, out)
    print(f"  ✓  {out.name}")


# ── 5. Carte thermique ─────────────────────────────────────────────────────────
def chart_heatmap(site_id: str, type_key: str) -> None:
    site = SITES[site_id]
    out  = IMAGES_DIR / f"{site_id}_heatmap_{type_key}.png"
    f    = AGG_DIR / f"heatmap_{site_id}_{type_key}.parquet"
    fyr  = AGG_DIR / f"heatmap_year_{site_id}_{type_key}.json"

    if not f.exists():
        make_placeholder(out, site["name"], TYPE_LABELS[type_key])
        return

    heatmap = pd.read_parquet(f)   # index=heure(0-23), cols=jour_annee(1-366)
    year    = int(json.loads(fyr.read_text())["annee"]) if fyr.exists() else "?"

    # Repères des mois sur l'axe X
    try:
        month_starts = [
            pd.Timestamp(f"{year}-{m:02d}-01").dayofyear for m in range(1, 13)
        ]
    except Exception:
        month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]

    cmap = "YlOrRd" if type_key == "consommation" else "YlGn"

    fig, ax = plt.subplots(figsize=(16, 5))
    data = heatmap.values
    vmax = np.nanpercentile(data[data > 0], 98) if np.any(data > 0) else 1.0

    im = ax.imshow(
        data,
        aspect="auto",
        origin="lower",
        cmap=cmap,
        interpolation="nearest",
        vmin=0,
        vmax=vmax,
    )

    ax.set_yticks(range(0, 24, 3))
    ax.set_yticklabels([f"{h:02d}h" for h in range(0, 24, 3)])
    ax.set_ylabel("Heure", color=TEXT)

    # Étiquettes des mois
    valid_starts = [d - 1 for d in month_starts if 1 <= d <= heatmap.shape[1]]
    ax.set_xticks(valid_starts)
    ax.set_xticklabels(MOIS[: len(valid_starts)], fontsize=9)

    ax.set_title(
        f"{site['name']} — Carte thermique {TYPE_LABELS[type_key]} {year} (kWh / 15 min)"
    )
    plt.colorbar(im, ax=ax, fraction=0.018, pad=0.02, label="kWh")

    _save(fig, out)
    print(f"  ✓  {out.name}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/5] Chronologie")
    chart_timeline()

    print("\n[2/5] Vues d'ensemble annuelles")
    for t in TYPES:
        chart_annual_overview(t)

    print("\n[3/5] Évolution mensuelle")
    for site_id in SITE_ORDER:
        for t in TYPES:
            chart_monthly(site_id, t)

    print("\n[4/5] Profil journalier typique")
    for site_id in SITE_ORDER:
        for t in TYPES:
            chart_typical_day(site_id, t)

    print("\n[5/5] Cartes thermiques")
    for site_id in SITE_ORDER:
        for t in TYPES:
            chart_heatmap(site_id, t)

    print(f"\nImages enregistrées dans : {IMAGES_DIR}")


if __name__ == "__main__":
    main()
