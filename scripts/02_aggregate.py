"""
02_aggregate.py — Calcul des agrégats à partir des Parquets
Produit, pour chaque (site, type) :
  - agrégat mensuel (MWh)
  - agrégat annuel  (MWh)
  - profil journalier typique par saison (kW, 96 points)
  - données de carte thermique pour l'année la plus récente complète (kWh/15min)

Usage : python scripts/02_aggregate.py
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import SITES, SITE_ORDER, TYPES, SAISONS, PROCESSED_DIR, AGG_DIR


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
    Carte thermique heure × jour de l'année pour l'année la plus récente avec données.
    Index = heure (0-23), colonnes = jour de l'année (1-366).
    Valeurs en kWh/15min (moyenne sur les intervalles de l'heure).
    """
    df = df.copy()

    # Trouver l'année la plus récente ayant des données non nulles
    by_year = df.groupby(df.index.year)["valeur_kwh"].sum()
    years_with_data = by_year[by_year > 0].index.tolist()
    year = int(years_with_data[-1]) if years_with_data else int(df.index.year[-1])

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


def process_all() -> None:
    AGG_DIR.mkdir(parents=True, exist_ok=True)

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

            n_mois = len(monthly)
            total_mwh = annual["valeur_mwh"].sum()
            print(f"✓  {n_mois} mois  ·  {total_mwh:.1f} MWh total  ·  heatmap {year}")

    print(f"\nAgrégats enregistrés dans : {AGG_DIR}")


if __name__ == "__main__":
    process_all()
