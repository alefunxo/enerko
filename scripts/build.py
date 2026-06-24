"""
build.py — Pipeline complet Enerko
Exécute les quatre étapes dans l'ordre :
  01_parse       → Parquets par (site, type)
  02_aggregate   → Agrégats mensuels/annuels/profils/heatmaps
  03_charts      → PNGs dans docs/assets/images/
  04_build_html  → docs/index.html

Usage :
  python scripts/build.py           # pipeline complet
  python scripts/build.py --html    # régénère uniquement le HTML (noms de sites)
  python scripts/build.py --charts  # régénère uniquement les graphiques
"""

import sys
import time
from pathlib import Path

# S'assurer que les imports relatifs fonctionnent
sys.path.insert(0, str(Path(__file__).parent))


def _run(label: str, fn) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        fn()
        elapsed = time.time() - t0
        print(f"\n  → Terminé en {elapsed:.1f}s")
        return True
    except Exception as exc:
        print(f"\n  ✗  ERREUR : {exc}")
        import traceback
        traceback.print_exc()
        return False


def run_full() -> None:
    import importlib

    steps = [
        ("01 — Lecture des CSV",           "01_parse",      "process_all"),
        ("02 — Calcul des agrégats",       "02_aggregate",  "process_all"),
        ("03 — Génération des graphiques", "03_charts",     "main"),
        ("04 — Génération du HTML",        "04_build_html", "main"),
    ]

    success = 0
    for label, module, fn_name in steps:
        mod = importlib.import_module(module)
        fn  = getattr(mod, fn_name)
        ok  = _run(label, fn)
        if ok:
            success += 1
        else:
            print(f"\n  Pipeline interrompu à l'étape : {label}")
            print("  Corrigez l'erreur et relancez.")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Pipeline terminé : {success}/{len(steps)} étapes réussies")
    print("  Commitez docs/ puis poussez vers GitHub pour mettre à jour la page.")
    print(f"{'='*60}\n")


def run_html_only() -> None:
    import importlib
    mod = importlib.import_module("04_build_html")
    _run("04 — Génération du HTML", mod.main)


def run_charts_only() -> None:
    import importlib
    for name, fn_name in [("02_aggregate", "process_all"), ("03_charts", "main")]:
        mod = importlib.import_module(name)
        _run(name, getattr(mod, fn_name))


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--html" in args:
        run_html_only()
    elif "--charts" in args:
        run_charts_only()
    else:
        run_full()
