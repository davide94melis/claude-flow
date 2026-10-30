"""Modello dati condiviso del lettore dei piani.

Solo dataclass immutabili: nessuna logica di lettura qui. Un dato assente e'
``None`` (mai 0) o una cella con valore vuoto.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Cell:
    """Una cella di tabella: testo originale e testo ripulito dal markup."""

    raw: str
    value: str


@dataclass(frozen=True)
class Effort:
    """Stima di una task: testo originale, giorni (se leggibili) e residuo."""

    raw: str
    days: float | None
    note: str


@dataclass(frozen=True)
class ParseWarning:
    """Avviso di lettura: dove, cosa e perche' una riga o un dato non e' stato letto."""

    code: str
    plan: str
    file: str
    line: int | None
    detail: str


@dataclass(frozen=True)
class PlanRef:
    """Un piano trovato nel repo: cartella, stato, ondata e file che lo compongono."""

    path: str
    state: str
    wave: str | None
    name: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class Task:
    """Una task di un piano, unita tra TASKS e PROGRESS.

    ``owner_source`` vale ``"progress"``, ``"tasks"`` oppure ``""`` (nessun owner vero).
    """

    plan: str
    id: str
    activity: Cell
    description: Cell
    stream: Cell
    area: Cell
    priority: Cell
    wave: Cell
    branch: Cell
    owner: Cell
    owner_source: str
    owner_tasks: Cell
    owner_progress: Cell
    dependencies: tuple[str, ...]
    dependencies_cell: Cell
    blocked_by: Cell
    effort: Effort
    status: str
    status_raw: str
    status_known: bool
    progress: int | None
    note: Cell
    in_tasks: bool
    in_progress: bool
    is_merge: bool
    source_lines: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PlanTasks:
    """Le task di un piano e il conto delle righe: viste contro lette."""

    plan: str
    tasks: tuple[Task, ...]
    rows_seen: int
    rows_read: int
    warnings: tuple[ParseWarning, ...]

    @property
    def degraded(self) -> bool:
        """Vero se almeno una riga con ID di task e' stata vista e non letta."""
        return self.rows_read < self.rows_seen


@dataclass(frozen=True)
class Milestone:
    """Una data intermedia del piano (tipo, giorno, file di provenienza)."""

    kind: str
    day: date
    source: str


@dataclass(frozen=True)
class Schedule:
    """Calendario di un piano: inizio, scadenza, fattore e date intermedie."""

    start: date | None
    deadline: date | None
    deadline_kind: str | None
    factor: float | None
    sources: dict[str, str]
    from_text: tuple[str, ...]
    milestones: tuple[Milestone, ...]
    warnings: tuple[ParseWarning, ...]
