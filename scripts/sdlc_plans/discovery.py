"""Scoperta dei piani in un repo di specifiche.

``discover_plans`` lavora su semplici stringhe di percorso (mai sul filesystem):
cosi' si puo' alimentare con l'output di ``git ls-tree -r --name-only`` o con la
storia git. ``walk_repo`` e' l'aiuto per le cartelle locali. Solo libreria standard.

Convenzione dei percorsi: ``/`` come separatore, sia in ingresso sia in uscita.
In ingresso la barra rovescia e' trattata come ``/``, un ``./`` (iniziale o
intermedio) e i separatori doppi vengono ignorati, e una voce che termina con
``/`` (una cartella) viene saltata.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .model import PlanRef

PLAN_MARKERS = ("TASKS.md", "PROGRESS.md")

_PLANS_DIR = "plans"
# plans / <state> / <nome del piano>: almeno tre segmenti di cartella.
_MIN_PLAN_DEPTH = 3


def _segments(path: str) -> tuple[str, ...] | None:
    """Segmenti normalizzati di un percorso-file, ``None`` per le cartelle e le voci vuote."""
    posix = path.replace("\\", "/")
    if posix.endswith("/"):
        return None
    segments = tuple(s for s in posix.split("/") if s and s != ".")
    return segments or None


def discover_plans(paths: Iterable[str]) -> list[PlanRef]:
    """Trova i piani tra i percorsi dei file di un repo, ordinati per ``path``.

    Un piano e' una cartella, almeno un livello sotto ``plans/<state>/``, che
    contiene direttamente ``TASKS.md`` o ``PROGRESS.md`` (nome esatto: un
    ``TASKS.en.md`` da solo non basta). Vale il primo segmento ``plans`` del
    percorso, quindi funziona anche con un prefisso (``acme/plans/...``).
    ``wave`` sono i segmenti tra lo stato e il nome del piano (``None`` se il
    piano e' direttamente sotto lo stato). Un piano dentro un altro piano e'
    un piano a se': ``files`` elenca solo i file direttamente nella sua cartella.
    """
    # cartella -> (posizione del segmento `plans`, nomi dei file); set: i doppioni spariscono.
    folders: dict[tuple[str, ...], tuple[int, set[str]]] = {}
    for path in paths:
        segments = _segments(path)
        if segments is None:
            continue
        *folder, filename = segments
        if _PLANS_DIR not in folder:
            continue
        plans_at = folder.index(_PLANS_DIR)
        if len(folder) - plans_at < _MIN_PLAN_DEPTH:
            continue
        folders.setdefault(tuple(folder), (plans_at, set()))[1].add(filename)

    found = []
    for folder, (plans_at, names) in folders.items():
        if not names.intersection(PLAN_MARKERS):
            continue
        between = folder[plans_at + 2 : -1]
        found.append(
            PlanRef(
                path="/".join(folder),
                state=folder[plans_at + 1],
                wave="/".join(between) or None,
                name=folder[-1],
                files=tuple(sorted(names)),
            )
        )
    return sorted(found, key=lambda plan: plan.path)


def walk_repo(root: Path) -> list[str]:
    """Percorsi dei file regolari sotto ``root``: relativi, con ``/``, ordinati, senza ``.git``."""
    files = []
    for entry in Path(root).rglob("*"):
        if not entry.is_file():
            continue
        relative = entry.relative_to(root)
        if ".git" in relative.parts:
            continue
        files.append(relative.as_posix())
    return sorted(files)
