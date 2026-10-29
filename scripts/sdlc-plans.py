#!/usr/bin/env python3
"""sdlc-plans.py - avvia la CLI del lettore dei piani (`python -m sdlc_plans`).

Serve agli interpreti isolati (ad esempio la distribuzione embeddable di Python
su Windows, con `python312._pth`): ignorano PYTHONPATH e non mettono la cartella
dello script in `sys.path`, quindi `-m sdlc_plans` non vi trova il pacchetto.
Il lanciatore aggiunge da solo la propria cartella, che contiene `sdlc_plans/`.

    python sdlc-plans.py discover (--stdin | --root DIR) [--format tsv|json]
    python sdlc-plans.py read --plan PATH [--tasks F] [--progress F] [--plan-md F] [--estimate F]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_plans.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
