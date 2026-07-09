"""
02_aggregate.py — Calcul des agrégats à partir des Parquets
Produit, pour chaque (site, type) :
  - agrégat mensuel (MWh)
  - agrégat annuel  (MWh)
  - profil journalier typique par saison (kW, 96 points)
  - données de carte thermique pour l'année la plus récente complète (kWh/15min)

Usage : python scripts/02_aggregate.py
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import SITES, SITE_ORDER, TYPES, SAISONS, PROCESSED_DIR, AGG_DIR, DOCS_DIR


def compute_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Totaux mensuels en MWh."""
    monthly = df["valeur_kwh"].resample("MS").sum() / 1000.0
    monthly.name = "valeur_mwh"
    return monthly.to_frame()


def compute_annual(df: pd.DataFrame) -> pd.DataFrame:
    """Totaux annuels en MWh."""
    annual = df["valeur_kwh"].resample("YS").sum() / 1000.0
    annual.index = annual.index.year
    annual.index.name = "annee"
    annual.name = "valeur_mwh"
    return annual.to_frame()


def compute_typical_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Profil moyen sur 96 intervalles de 15 min, par saison.
    Valeurs en kW (kWh × 4).
    Colonnes = noms de saisons, index = slot 0-95.
    """
    df = df.copy()
    df["slot"] = df.index.hour * 4 + df.index.minute // 15
    df["mois"] = df.index.month

    frames = {}
    for saison, months in SAISONS.items():
        sub = df[df["mois"].isin(months)]
        if sub.empty:
            frames[saison] = pd.Series(np.zeros(96), index=range(96))
        else:
            profile = sub.groupby("slot")["valeur_kwh"].mean() * 4.0  # kWh → kW
            profile = profile.reindex(range(96), fill_value=0.0)
            frames[saison] = profile

    return pd.DataFrame(frames)


def compute_heatmap(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Carte thermique heure × jour de l'année pour l'année la plus récente COMPLÈTE
    (l'année en cours est toujours partielle, donc exclue si une année antérieure
    avec données existe).
    Index = heure (0-23), colonnes = jour de l'année (1-366).
    Valeurs en kWh/15min (moyenne sur les intervalles de l'heure).
    """
    df = df.copy()

    current_year = pd.Timestamp.today().year
    by_year = df.groupby(df.index.year)["valeur_kwh"].sum()
    years_with_data = sorted(by_year[by_year > 0].index.tolist())
    complete_years = [y for y in years_with_data if y < current_year]

    if complete_years:
        year = int(complete_years[-1])
    elif years_with_data:
        year = int(years_with_data[-1])
    else:
        year = int(df.index.year[-1])

    year_df = df[df.index.year == year].copy()
    year_df["heure"]      = year_df.index.hour
    year_df["jour_annee"] = year_df.index.dayofyear

    heatmap = year_df.pivot_table(
        index="heure",
        columns="jour_annee",
        values="valeur_kwh",
        aggfunc="mean",
    )
    # Assurer que toutes les heures sont présentes
    heatmap = heatmap.reindex(range(24), fill_value=np.nan)

    return heatmap, year


def compute_completeness(df: pd.DataFrame) -> dict:
    """
    Taux de complétude des données à intervalle de 15 min.
    Les trous < 2 jours (ex. passage heure d'été/hiver) sont ignorés dans
    la liste des trous, mais comptent dans le pourcentage manquant.
    """
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="15min")
    missing_idx = full_range.difference(df.index)

    expected = len(full_range)
    present  = len(df)
    missing  = expected - present
    pct_missing = round(100 * missing / expected, 2) if expected else 0.0

    gaps = []
    if len(missing_idx):
        s = missing_idx.to_series()
        block_id = (s.diff() != pd.Timedelta("15min")).cumsum()
        for _, block in s.groupby(block_id):
            if len(block) < 96 * 2:  # < 2 jours : ignoré (probable DST)
                continue
            gaps.append({
                "start": block.iloc[0].strftime("%Y-%m-%d"),
                "end":   block.iloc[-1].strftime("%Y-%m-%d"),
                "days":  round(len(block) / 96, 1),
            })
        gaps.sort(key=lambda g: g["days"], reverse=True)

    return {
        "start":       df.index.min().strftime("%Y-%m-%d"),
        "end":         df.index.max().strftime("%Y-%m-%d"),
        "expected":    expected,
        "present":     present,
        "missing":     missing,
        "pct_missing": pct_missing,
        "gaps":        gaps,
    }


def process_all() -> None:
    AGG_DIR.mkdir(parents=True, exist_ok=True)

    completeness: dict[str, dict] = {}

    for site_id in SITE_ORDER:
        site = SITES[site_id]
        for type_key in TYPES:
            parquet_path = PROCESSED_DIR / f"{site_id}_{type_key}.parquet"
            if not parquet_path.exists():
                continue

            print(f"  {site['name']} — {type_key}", end=" … ", flush=True)

            df = pd.read_parquet(parquet_path)

            # Mensuel
            monthly = compute_monthly(df)
            monthly.to_parquet(AGG_DIR / f"monthly_{site_id}_{type_key}.parquet")

            # Annuel
            annual = compute_annual(df)
            annual.to_parquet(AGG_DIR / f"annual_{site_id}_{type_key}.parquet")

            # Profil journalier typique
            typical = compute_typical_day(df)
            typical.to_parquet(AGG_DIR / f"typical_day_{site_id}_{type_key}.parquet")

            # Carte thermique
            heatmap, year = compute_heatmap(df)
            heatmap.to_parquet(AGG_DIR / f"heatmap_{site_id}_{type_key}.parquet")

            # Méta : année utilisée pour la heatmap
            pd.Series({"annee": year}).to_json(
                AGG_DIR / f"heatmap_year_{site_id}_{type_key}.json"
            )

            # Complétude
            comp = compute_completeness(df)
            completeness[f"{site_id}_{type_key}"] = comp

            n_mois = len(monthly)
            total_mwh = annual["valeur_mwh"].sum()
            gap_note = f"  ⚠ {len(comp['gaps'])} trou(s)" if comp["gaps"] else ""
            print(
                f"✓  {n_mois} mois  ·  {total_mwh:.1f} MWh total  ·  heatmap {year}"
                f"  ·  {100 - comp['pct_missing']:.1f}% complet{gap_note}"
            )

    data_dir = DOCS_DIR / "assets" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓  completeness.json ({len(completeness)} entrées)")

    print(f"\nAgrégats enregistrés dans : {AGG_DIR}")


if __name__ == "__main__":
    process_all()
