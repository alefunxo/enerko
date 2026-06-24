"""
01_parse.py — Lecture des CSV SIG et export en Parquet
Lit chaque fichier source défini dans config.py et produit un Parquet
par (site, type) dans processed/.

Usage : python scripts/01_parse.py
"""

import sys
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import SITES, SITE_ORDER, TYPES, DATA_DIR, PROCESSED_DIR


# Colonnes utilisées par position (indépendant de l'encodage des noms)
COL_DATE  = 3   # "Date de début"
COL_HEURE = 4   # "Heure de début"
COL_VALEUR = 9  # "Valeur"


def _find_csv(uuid: str) -> Optional[Path]:
    """Trouve le fichier CSV correspondant à un UUID, quelle que soit l'extension exacte."""
    for candidate in DATA_DIR.glob(f"*{uuid}*"):
        if candidate.suffix.lower() == ".csv":
            return candidate
    return None


def parse_csv(filepath: Path) -> pd.DataFrame:
    """
    Lit un export SIG CourbeCharge.
    Retourne un DataFrame indexé par timestamp (heure locale CH) avec la colonne 'valeur_kwh'.
    """
    raw = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            raw = pd.read_csv(
                filepath,
                sep=";",
                encoding=enc,
                header=0,
                low_memory=False,
                dtype=str,
            )
            break
        except UnicodeDecodeError:
            continue

    if raw is None:
        raise ValueError(f"Impossible de lire {filepath.name}")

    # Extraction par position pour éviter les problèmes d'encodage sur les noms
    date_str  = raw.iloc[:, COL_DATE].astype(str).str.strip()
    heure_str = raw.iloc[:, COL_HEURE].astype(str).str.strip()
    val_str   = raw.iloc[:, COL_VALEUR].astype(str).str.strip().str.replace(",", ".", regex=False)

    # Filtrer les lignes d'en-tête résiduelles ou vides
    mask = date_str.str.match(r"\d{2}\.\d{2}\.\d{4}")
    date_str  = date_str[mask]
    heure_str = heure_str[mask]
    val_str   = val_str[mask]

    timestamps = pd.to_datetime(
        date_str + " " + heure_str,
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce",
    )
    values = pd.to_numeric(val_str, errors="coerce")

    df = pd.DataFrame({"timestamp": timestamps, "valeur_kwh": values})
    df = df.dropna().set_index("timestamp").sort_index()

    # Supprimer les doublons d'horodatage (DST)
    df = df[~df.index.duplicated(keep="first")]

    return df


def process_all() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    total = sum(
        1 for sid in SITE_ORDER
        for t in TYPES
        if SITES[sid]["files"].get(t) is not None
    )
    done = 0

    for site_id in SITE_ORDER:
        site = SITES[site_id]
        for type_key in TYPES:
            uuid = site["files"].get(type_key)
            if uuid is None:
                continue

            out_path = PROCESSED_DIR / f"{site_id}_{type_key}.parquet"
            done += 1
            print(f"[{done}/{total}] {site['name']} — {type_key} ({uuid[:8]}…)", end=" ", flush=True)

            csv_path = _find_csv(uuid)
            if csv_path is None:
                print(f"⚠ fichier introuvable : {uuid}.csv")
                continue

            try:
                df = parse_csv(csv_path)
                df.to_parquet(out_path)
                n = len(df)
                start = df.index.min().strftime("%Y-%m")
                end   = df.index.max().strftime("%Y-%m")
                print(f"✓  {n:,} mesures  [{start} → {end}]")
            except Exception as exc:
                print(f"✗  erreur : {exc}")

    print(f"\nParquets enregistrés dans : {PROCESSED_DIR}")


if __name__ == "__main__":
    process_all()
