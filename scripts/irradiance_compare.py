"""
irradiance_compare.py — Irradiance PVGIS vs production sites C & D (Genève 2018–2023)

Télécharge les données horaires PVGIS (cache local), lit les CSV de production
des sites C et D, puis génère 4 PNG dans output/irradiance/.

Usage : python scripts/irradiance_compare.py
"""

import io
import sys
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from config import SITES, DATA_DIR

PVGIS_URL = (
    "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
    "?lat=46.2&lon=6.15&startyear=2018&endyear=2023&outputformat=csv"
)
CACHE_PATH = ROOT / "pvgis_geneva_2018_2023.csv"
OUT_DIR    = ROOT / "output" / "irradiance"

MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


# ── Data loading ─────────────────────────────────────────────────────────────

def fetch_pvgis() -> pd.DataFrame:
    if not CACHE_PATH.exists():
        print(f"  Téléchargement PVGIS → {CACHE_PATH.name} …", flush=True)
        with urllib.request.urlopen(PVGIS_URL, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
        CACHE_PATH.write_text(raw, encoding="utf-8")
        print("  OK")
    else:
        print(f"  Cache PVGIS : {CACHE_PATH.name}")
        raw = CACHE_PATH.read_text(encoding="utf-8")

    lines = raw.splitlines()
    header_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("time,")), None
    )
    if header_idx is None:
        raise ValueError("Format PVGIS inattendu — colonne 'time' introuvable")

    # Keep header + rows that look like data (YYYYMMDD:HHMM,...); skip blanks and legend
    import re as _re
    _data_pat = _re.compile(r"^\d{8}:\d{4},")
    data_lines = [lines[header_idx]]
    for ln in lines[header_idx + 1:]:
        if _data_pat.match(ln.strip()):
            data_lines.append(ln.strip())

    df = pd.read_csv(io.StringIO("\n".join(data_lines)))
    df["timestamp"] = pd.to_datetime(df["time"].str.strip(), format="%Y%m%d:%H%M")
    df = df.set_index("timestamp").sort_index()

    # Locate the global irradiance column: G(i) or G(h)
    irr_col = next((c for c in df.columns if c.strip().startswith("G(")), None)
    if irr_col is None:
        raise ValueError(f"Colonne irradiance introuvable. Colonnes dispo : {list(df.columns)}")
    print(f"  Colonne irradiance : '{irr_col}'")

    df = df[[irr_col]].rename(columns={irr_col: "irr_wm2"})
    df["irr_wm2"] = pd.to_numeric(df["irr_wm2"], errors="coerce").clip(lower=0)
    return df


def parse_sig_csv(filepath: Path) -> pd.DataFrame:
    raw = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            raw = pd.read_csv(filepath, sep=";", encoding=enc, header=0,
                              low_memory=False, dtype=str)
            break
        except UnicodeDecodeError:
            continue

    date_str  = raw.iloc[:, 3].astype(str).str.strip()
    heure_str = raw.iloc[:, 4].astype(str).str.strip()
    val_str   = raw.iloc[:, 9].astype(str).str.strip().str.replace(",", ".", regex=False)

    mask = date_str.str.match(r"\d{2}\.\d{2}\.\d{4}")
    ts   = pd.to_datetime(
        date_str[mask] + " " + heure_str[mask],
        format="%d.%m.%Y %H:%M:%S", errors="coerce",
    )
    vals = pd.to_numeric(val_str[mask], errors="coerce")

    df = pd.DataFrame({"timestamp": ts.values, "valeur_kwh": vals.values})
    df = df.dropna().set_index("timestamp").sort_index()
    return df[~df.index.duplicated(keep="first")]


def load_production(site_id: str) -> pd.Series:
    uuid = SITES[site_id]["files"]["production"]
    candidates = list(DATA_DIR.glob(f"*{uuid}*.csv"))
    if not candidates:
        raise FileNotFoundError(f"CSV production introuvable pour {site_id}")
    df = parse_sig_csv(candidates[0])
    df = df["2018":"2023"]
    # min_count=1: months with no rows at all become NaN (not 0) — true missing data
    monthly = df["valeur_kwh"].resample("MS").sum(min_count=1) / 1000.0  # kWh → MWh
    monthly.name = site_id
    return monthly


# ── Plots ─────────────────────────────────────────────────────────────────────

def _year_colors(years):
    cmap = plt.cm.plasma
    return {yr: cmap(i / max(len(years) - 1, 1)) for i, yr in enumerate(sorted(years))}


def plot_timeseries(irr_m: pd.Series, prod: dict[str, pd.Series]) -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Irradiance PVGIS vs Production PV — Genève 2018–2023", fontsize=13)

    axes[0].bar(irr_m.index, irr_m.values, width=25, color="#F5A623", alpha=0.85)
    axes[0].set_ylabel("kWh/m²/mois")
    axes[0].set_title("Irradiance horizontale globale (PVGIS)")
    axes[0].grid(axis="y", alpha=0.3)

    for ax, site_id in zip(axes[1:], ("site_c", "site_d")):
        site    = SITES[site_id]
        monthly = prod[site_id].dropna()          # exclude months with no data at all
        common  = irr_m.index.intersection(monthly.index)
        ax.bar(common, monthly.loc[common], width=25, color=site["color"], alpha=0.85,
               label=f"Production {site['name']}")
        n_gap = (~prod[site_id].reindex(irr_m.index).notna()).sum()
        title = f"Production {site['name']}"
        if n_gap > 0:
            title += f"  ({n_gap} mois manquants dans la source)"
        ax.set_ylabel("MWh/mois")
        ax.set_title(title, fontsize=10)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha="right")

    fig.tight_layout()
    out = OUT_DIR / "01_monthly_timeseries.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_monthly_profile(irr_m: pd.Series, prod: dict[str, pd.Series]) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Profil mensuel moyen 2018–2023 (toutes années confondues)", fontsize=12)

    series_list = [
        ("Irradiance G(h)\n(kWh/m²/mois)", irr_m, "#F5A623"),
        (f"Production {SITES['site_c']['name']}\n(MWh/mois)", prod["site_c"], SITES["site_c"]["color"]),
        (f"Production {SITES['site_d']['name']}\n(MWh/mois)", prod["site_d"], SITES["site_d"]["color"]),
    ]

    for ax, (title, series, color) in zip(axes, series_list):
        by_m = series.groupby(series.index.month).mean().reindex(range(1, 13), fill_value=0)
        ax.bar(range(1, 13), by_m.values, color=color, alpha=0.85)
        ax.set_title(title)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MOIS, rotation=45, ha="right")
        ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    out = OUT_DIR / "02_monthly_profile.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_year_overlay(irr_m: pd.Series, prod: dict[str, pd.Series]) -> Path:
    years  = sorted(set(irr_m.index.year) | set(prod["site_c"].index.year) | set(prod["site_d"].index.year))
    colors = _year_colors(years)

    series_list = [
        ("Irradiance G(h) (kWh/m²)", irr_m),
        (f"Production {SITES['site_c']['name']} (MWh)", prod["site_c"]),
        (f"Production {SITES['site_d']['name']} (MWh)", prod["site_d"]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Profil mensuel par année — comparaison", fontsize=12)

    for ax, (title, series) in zip(axes, series_list):
        for yr in sorted(series.index.year.unique()):
            sub = series[series.index.year == yr].dropna()
            if sub.empty:
                continue
            ax.plot(sub.index.month, sub.values, marker="o", markersize=4,
                    label=str(yr), color=colors[yr], alpha=0.85, linewidth=1.5)
        ax.set_title(title)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MOIS, rotation=45, ha="right")
        ax.legend(fontsize=8, ncol=2)
        ax.grid(alpha=0.3)

    fig.tight_layout()
    out = OUT_DIR / "03_year_overlay.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_scatter(irr_m: pd.Series, prod: dict[str, pd.Series]) -> Path:
    years  = sorted(irr_m.index.year.unique())
    colors = _year_colors(years)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Corrélation mensuelle Irradiance ↔ Production", fontsize=12)

    for ax, site_id in zip(axes, ("site_c", "site_d")):
        site    = SITES[site_id]
        monthly = prod[site_id]
        # Align on common index then drop NaN (months missing from the source)
        both   = pd.DataFrame({"irr": irr_m, "prod": monthly}).dropna()
        x, y   = both["irr"], both["prod"]

        for yr in sorted(x.index.year.unique()):
            mask = x.index.year == yr
            ax.scatter(x[mask], y[mask], label=str(yr), color=colors.get(yr, "grey"),
                       alpha=0.85, s=55, zorder=3, edgecolors="white", linewidths=0.4)

        if len(x) > 2:
            coeffs = np.polyfit(x.values, y.values, 1)
            x_fit  = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_fit, np.polyval(coeffs, x_fit), "k--", alpha=0.45, linewidth=1.2)
            r2 = float(np.corrcoef(x.values, y.values)[0, 1] ** 2)
            n_skip = monthly.isna().sum()
            label  = f"R² = {r2:.3f}  (n={len(x)}"
            label += f", {n_skip} mois exclus)" if n_skip else ")"
            ax.text(0.05, 0.95, label, transform=ax.transAxes,
                    fontsize=9, va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.75))

        ax.set_xlabel("Irradiance (kWh/m²/mois)")
        ax.set_ylabel("Production (MWh/mois)")
        ax.set_title(site["name"])
        ax.legend(title="Année", fontsize=8, ncol=2)
        ax.grid(alpha=0.3)

    fig.tight_layout()
    out = OUT_DIR / "04_scatter_correlation.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("── PVGIS ────────────────────────────────────────")
    irr_raw = fetch_pvgis()
    # W/m² hourly → kWh/m² per hour, then sum to monthly
    irr_raw["irr_kwh_m2"] = irr_raw["irr_wm2"] / 1000.0
    irr_monthly = irr_raw["irr_kwh_m2"].resample("MS").sum()
    print(f"  {len(irr_monthly)} mois d'irradiance  "
          f"[{irr_monthly.index.min().strftime('%Y-%m')} → {irr_monthly.index.max().strftime('%Y-%m')}]")

    print("\n── Production ───────────────────────────────────")
    prod = {}
    for site_id in ("site_c", "site_d"):
        monthly = load_production(site_id)
        prod[site_id] = monthly
        total = monthly.sum()
        print(f"  {SITES[site_id]['name']}: {len(monthly)} mois — {total:.1f} MWh total")

    print("\n── Graphiques ───────────────────────────────────")
    for fn in (plot_timeseries, plot_monthly_profile, plot_year_overlay, plot_scatter):
        out = fn(irr_monthly, prod)
        print(f"  ✓  {out.name}")

    print(f"\n  PNG dans : {OUT_DIR}")


if __name__ == "__main__":
    main()
