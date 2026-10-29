"""Configurazione pytest condivisa dei test degli script di sdlc-suite."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# La cartella `scripts/` in testa a sys.path: `import sdlc_plans` funziona
# senza installare il pacchetto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def plans_fixtures() -> Path:
    """Cartella delle fixture sintetiche dei piani."""
    return Path(__file__).parent / "fixtures" / "plans"
