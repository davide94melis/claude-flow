"""Lettura delle task di un piano a partire da TASKS.md.

``read_task_rows`` legge le righe di task di un solo file (tabelle di task piu'
righe orfane) e restituisce righe, conteggi e avvisi: e' il pezzo riusabile per
ogni file del piano. ``read_plan`` lo applica a TASKS.md e a PROGRESS.md e unisce
le righe per ID: TASKS.md da' la struttura, PROGRESS.md stato, avanzamento, owner,
branch e note, con gli avvisi di coerenza tra i due file. Solo libreria standard.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace

from .effort import NOTE_UNDECLARED, parse_effort
from .model import Cell, ParseWarning, PlanTasks, Task
from .tables import Table, scan_tables
from .vocab import (
    TASK_ID_RE, canon_status, clean_markup, is_placeholder, normalize_id, owner_base,
)

TASKS_FILE = "TASKS.md"
PROGRESS_FILE = "PROGRESS.md"

WARN_ROW_DROPPED = "row_dropped"
WARN_DUPLICATE_ID = "duplicate_id"
WARN_EFFORT_UNREADABLE = "effort_unreadable"
WARN_TABLE_NOT_RECOGNIZED = "table_not_recognized"
WARN_STATUS_UNKNOWN = "status_unknown"
WARN_STATUS_PROGRESS_MISMATCH = "status_progress_mismatch"
WARN_PROGRESS_UNREADABLE = "progress_unreadable"
WARN_OWNER_DIVERGENT = "owner_divergent"
WARN_TASK_WITHOUT_PROGRESS_ROW = "task_without_progress_row"
WARN_PROGRESS_ONLY_ID = "progress_only_id"
WARN_DEPENDENCY_UNKNOWN = "dependency_unknown"

DEFAULT_STATUS = "Da iniziare"
COMPLETED_STATUS = "Completata"
MERGE_ID_PREFIX = "T-MERGE"

_EMPTY = Cell("", "")
# Forma di un ID di task senza guardare le maiuscole: `t-002` ha la forma ma non e' un ID valido.
_ID_SHAPE_RE = re.compile(TASK_ID_RE.pattern, re.IGNORECASE)
# ID di task, con prefisso di repo facoltativo (`crb/T-010`).
_DEPENDENCY_RE = re.compile(r"(?:[\w.-]+/)?T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
_PERCENT_RE = re.compile(r"[0-9]+")


@dataclass(frozen=True)
class TaskRow:
    """Una riga di task: ID normalizzato, riga nel file e celle per campo canonico.

    Un campo senza colonna non e' tra le chiavi di ``cells``.
    """

    id: str
    line: int
    cells: Mapping[str, Cell]


@dataclass(frozen=True)
class FileRows:
    """Righe di task di un file.

    ``rows`` ha una riga per ID (la prima, nell'ordine del file). ``seen`` conta
    le righe con ID di task viste (nelle tabelle di task e orfane), ``read`` quelle
    lette: un ID ripetuto conta come letto, anche se vale solo la prima riga.
    ``has_task_table`` e' vero se il file ha almeno una tabella di task, anche senza righe.
    """

    rows: tuple[TaskRow, ...]
    seen: int
    read: int
    warnings: tuple[ParseWarning, ...]
    has_task_table: bool = False


def _is_task_table(table: Table) -> bool:
    """Una tabella di task ha il campo ``id`` e almeno uno tra ``owner`` ed ``effort``."""
    fields = table.fields
    return "id" in fields and ("owner" in fields or "effort" in fields)


def _row_cells(table: Table, cells: tuple[str, ...]) -> dict[str, Cell]:
    """Celle per campo canonico; se due colonne hanno lo stesso campo vale la prima."""
    by_field: dict[str, Cell] = {}
    for field, raw in zip(table.fields, cells):
        if field is not None and field not in by_field:
            by_field[field] = Cell(raw, clean_markup(raw))
    return by_field


def _warning(
    plan: str, filename: str, code: str, line: int, task_id: str | None, detail: str,
) -> ParseWarning:
    """Avviso con il dettaglio che inizia con ``<ID>: `` quando e' legato a una task."""
    return ParseWarning(code, plan, filename, line, f"{task_id}: {detail}" if task_id else detail)


def _unrecognized_table_warning(plan: str, filename: str, table: Table) -> ParseWarning | None:
    """Avviso informativo per una tabella non di task che ha ID di task nella colonna ID.

    Colonna ID: quella del campo ``id``, altrimenti la prima. Un solo avviso per
    tabella, sulla riga dell'intestazione; non cambia i conteggi delle righe.
    """
    column = table.fields.index("id") if "id" in table.fields else 0
    count = sum(1 for row in table.rows if normalize_id(row.cells[column]) is not None)
    if not count:
        return None
    return ParseWarning(
        WARN_TABLE_NOT_RECOGNIZED, plan, filename, table.header_line,
        f"{' | '.join(table.headers)}: {count} ID di task nella colonna "
        f"'{table.headers[column]}', ma la tabella non e' di task (servono la colonna ID "
        "e almeno una tra Owner ed Effort): righe non lette",
    )


def read_task_rows(plan: str, filename: str, text: str | None) -> FileRows:
    """Legge le righe di task di un file.

    Tabelle di task dello stesso file si uniscono nell'ordine. Una riga entra se
    la sua cella ID e' un ID di task. Sono viste e non lette (avviso
    ``row_dropped``, lettura degradata): le righe orfane con un ID di task nella
    prima cella e le righe di una tabella di task il cui ID ha la forma di un ID
    ma non e' valido (``t-002``). Una tabella non di task con ID di task nella
    colonna ID da' un avviso informativo ``table_not_recognized`` e non cambia i
    conteggi. Gli avvisi della lettura delle tabelle si tengono se cadono in una
    tabella di task.
    """
    if not text:
        return FileRows((), 0, 0, ())
    scan = scan_tables(text)
    warnings: list[ParseWarning] = []
    rows: dict[str, TaskRow] = {}
    # riga -> ID della task (None: intestazione o riga senza ID) per le righe delle tabelle di task
    task_lines: dict[int, str | None] = {}
    seen = read = 0
    has_task_table = False

    for table in scan.tables:
        if not _is_task_table(table):
            unrecognized = _unrecognized_table_warning(plan, filename, table)
            if unrecognized is not None:
                warnings.append(unrecognized)
            continue
        has_task_table = True
        task_lines[table.header_line] = None
        for row in table.rows:
            cells = _row_cells(table, row.cells)
            task_id = normalize_id(cells["id"].raw)
            task_lines[row.line] = task_id
            if task_id is None:
                if _ID_SHAPE_RE.match(cells["id"].value):
                    seen += 1
                    warnings.append(_warning(
                        plan, filename, WARN_ROW_DROPPED, row.line, cells["id"].value,
                        "ID con la forma di una task ma non valido (serve `T-` maiuscolo e "
                        "nessun altro carattere): riga non letta",
                    ))
                continue
            seen += 1
            read += 1
            if task_id in rows:
                warnings.append(_warning(
                    plan, filename, WARN_DUPLICATE_ID, row.line, task_id,
                    f"ID ripetuto (prima a riga {rows[task_id].line}): vale la prima riga",
                ))
            else:
                rows[task_id] = TaskRow(task_id, row.line, cells)

    for row in scan.orphan_rows:
        task_id = normalize_id(row.cells[0])
        if task_id is None:
            continue
        seen += 1
        task_lines[row.line] = task_id
        warnings.append(_warning(
            plan, filename, WARN_ROW_DROPPED, row.line, task_id,
            "riga con ID di task fuori da una tabella (nessuna intestazione sopra): non letta",
        ))

    for code, line, detail in scan.warnings:
        if line in task_lines:
            warnings.append(_warning(plan, filename, code, line, task_lines[line], detail))

    ordered = tuple(sorted(warnings, key=lambda w: w.line or 0))
    return FileRows(tuple(rows.values()), seen, read, ordered, has_task_table)


def _parse_dependencies(cell: str) -> tuple[str, ...]:
    """ID di task trovati nella cella, normalizzati; il prefisso di repo resta com'e'."""
    found = []
    for match in _DEPENDENCY_RE.finditer(cell):
        prefix, _, ident = match.group().rpartition("/")
        normalized = normalize_id(ident) or ident
        found.append(f"{prefix}/{normalized}" if prefix else normalized)
    return tuple(found)


def _is_merge_id(task_id: str) -> bool:
    """Le task di unione dei branch hanno un ID che inizia con ``T-MERGE``."""
    return task_id.startswith(MERGE_ID_PREFIX)


def _resolve_status(*candidates: Cell) -> tuple[str, str, bool]:
    """Stato dal primo candidato non vuoto: ``(stato, testo originale, riconosciuto)``.

    Senza candidati utili: ``Da iniziare``, testo originale vuoto, riconosciuto.
    """
    for cell in candidates:
        if cell.value:
            label, known = canon_status(cell.raw)
            if label:
                return label, cell.raw, known
    return DEFAULT_STATUS, "", True


def _task_from_tasks_row(plan: str, filename: str, row: TaskRow) -> Task:
    """Task con i soli dati di TASKS.md e i valori di partenza per il resto."""
    cells = row.cells

    def cell(field: str) -> Cell:
        return cells.get(field, _EMPTY)

    owner_tasks = cell("owner")
    owner_is_name = not is_placeholder(owner_tasks.raw)
    status, status_raw, status_known = _resolve_status(cell("status"))
    dependencies_cell = cell("dependencies")
    return Task(
        plan=plan,
        id=row.id,
        activity=cell("activity"),
        description=cell("description"),
        stream=cell("stream"),
        area=cell("area"),
        priority=cell("priority"),
        wave=cell("wave"),
        branch=cell("branch"),
        owner=owner_tasks if owner_is_name else _EMPTY,
        owner_source="tasks" if owner_is_name else "",
        owner_tasks=owner_tasks,
        owner_progress=_EMPTY,
        dependencies=_parse_dependencies(dependencies_cell.raw),
        dependencies_cell=dependencies_cell,
        blocked_by=cell("blocked_by"),
        effort=parse_effort(cell("effort").raw),
        status=status,
        status_raw=status_raw,
        status_known=status_known,
        progress=None,
        note=cell("note"),
        in_tasks=True,
        in_progress=False,
        is_merge=_is_merge_id(row.id),
        source_lines=((filename, row.line),),
    )


def _effort_warnings(plan: str, tasks: tuple[Task, ...]) -> tuple[ParseWarning, ...]:
    """Avviso per ogni effort dichiarato e non leggibile (vuoto e ``non dichiarato`` no).

    Il file e la riga sono quelli della prima riga usata per la task.
    """
    found = []
    for task in tasks:
        if task.effort.days is None and task.effort.note != NOTE_UNDECLARED:
            filename, line = task.source_lines[0]
            found.append(_warning(
                plan, filename, WARN_EFFORT_UNREADABLE, line, task.id, task.effort.note,
            ))
    return tuple(found)


# ---------------------------------------------------------------------------
# Sovrapposizione di PROGRESS.md
# ---------------------------------------------------------------------------

def _progress_only_task(plan: str, row: TaskRow) -> Task:
    """Task per un ID che c'e' solo nel PROGRESS: i campi che la riga ha, il resto vuoto.

    Effort non dichiarato e nessuna dipendenza; stato, owner, branch, note e
    ``blocked_by`` li mette la sovrapposizione.
    """
    cells = row.cells

    def cell(field: str) -> Cell:
        return cells.get(field, _EMPTY)

    return Task(
        plan=plan,
        id=row.id,
        activity=cell("activity"),
        description=cell("description"),
        stream=cell("stream"),
        area=cell("area"),
        priority=cell("priority"),
        wave=cell("wave"),
        branch=_EMPTY,
        owner=_EMPTY,
        owner_source="",
        owner_tasks=_EMPTY,
        owner_progress=_EMPTY,
        dependencies=(),
        dependencies_cell=_EMPTY,
        blocked_by=_EMPTY,
        effort=parse_effort(""),
        status=DEFAULT_STATUS,
        status_raw="",
        status_known=True,
        progress=None,
        note=_EMPTY,
        in_tasks=False,
        in_progress=False,
        is_merge=_is_merge_id(row.id),
        source_lines=(),
    )


def _progress_status(cell: Cell) -> tuple[str, str, bool] | None:
    """Stato della cella del PROGRESS, ``None`` se vuota o senza testo utile."""
    label, raw, known = _resolve_status(cell)
    return (label, raw, known) if raw else None


def _parse_percent(cell: Cell) -> tuple[int | None, str]:
    """Avanzamento dalla cella: ``(percentuale, dettaglio dell'avviso o "")``.

    Vale il primo intero; sopra 100 diventa 100 con un avviso. Cella vuota: nessun
    dato e nessun avviso; testo senza numeri: nessun dato e un avviso.
    """
    if not cell.value:
        return None, ""
    match = _PERCENT_RE.search(cell.value)
    if match is None:
        return None, f"{cell.value} non contiene un numero: avanzamento non letto"
    number = int(match.group())
    if number > 100:
        return 100, f"{cell.value} limitato a 100"
    return number, ""


def _pick_owner(tasks_owner: Cell, progress_owner: Cell) -> tuple[Cell, str]:
    """Owner e sua origine: vince il PROGRESS se e' un nome, poi il TASKS, poi nessuno."""
    if not is_placeholder(progress_owner.raw):
        return progress_owner, "progress"
    if not is_placeholder(tasks_owner.raw):
        return tasks_owner, "tasks"
    return _EMPTY, ""


def _prefer(progress: Cell, tasks: Cell) -> Cell:
    """La cella del PROGRESS se ha un valore, altrimenti quella del TASKS."""
    return progress if progress.value else tasks


def _owners_diverge(task: Task) -> bool:
    """Vero se TASKS e PROGRESS hanno entrambi un nome e i due nomi sono persone diverse."""
    if is_placeholder(task.owner_tasks.raw) or is_placeholder(task.owner_progress.raw):
        return False
    in_tasks = owner_base(task.owner_tasks.raw).casefold()
    in_progress = owner_base(task.owner_progress.raw).casefold()
    return in_tasks != in_progress


def _status_unknown(plan: str, task: Task, where: tuple[str, int]) -> list[ParseWarning]:
    """Avviso se lo stato non e' del vocabolario; ``where`` e' la riga da cui viene lo stato."""
    if task.status_known:
        return []
    filename, line = where
    return [_warning(
        plan, filename, WARN_STATUS_UNKNOWN, line, task.id,
        f"stato '{task.status}' fuori dal vocabolario: tenuto com'e'",
    )]


def _overlay_progress(plan: str, task: Task, row: TaskRow) -> tuple[Task, list[ParseWarning]]:
    """Sovrappone una riga del PROGRESS alla task; ritorna la task e gli avvisi di coerenza."""
    cells = row.cells

    def cell(field: str) -> Cell:
        return cells.get(field, _EMPTY)

    here = (PROGRESS_FILE, row.line)
    progress_status = _progress_status(cell("status"))
    if progress_status is not None:
        status, status_raw, status_known = progress_status
        status_where = here
    else:  # stato dalla colonna del TASKS, o quello di partenza se la task e' solo nel PROGRESS
        status, status_raw, status_known = task.status, task.status_raw, task.status_known
        status_where = task.source_lines[0] if task.source_lines else here
    percent, percent_detail = _parse_percent(cell("progress"))
    owner, owner_source = _pick_owner(task.owner_tasks, cell("owner"))
    merged = replace(
        task,
        branch=_prefer(cell("branch"), task.branch),
        owner=owner,
        owner_source=owner_source,
        owner_progress=cell("owner"),
        blocked_by=_prefer(cell("blocked_by"), task.blocked_by),
        status=status,
        status_raw=status_raw,
        status_known=status_known,
        progress=percent,
        note=_prefer(cell("note"), task.note),
        in_progress=True,
        source_lines=(*task.source_lines, here),
    )

    found = _status_unknown(plan, merged, status_where)
    if percent_detail:
        found.append(_warning(
            plan, PROGRESS_FILE, WARN_PROGRESS_UNREADABLE, row.line, task.id, percent_detail,
        ))
    if merged.status == COMPLETED_STATUS and merged.progress is not None and merged.progress < 100:
        found.append(_warning(
            plan, PROGRESS_FILE, WARN_STATUS_PROGRESS_MISMATCH, row.line, task.id,
            f"stato {COMPLETED_STATUS} con avanzamento al {merged.progress}%",
        ))
    if _owners_diverge(merged):
        found.append(_warning(
            plan, PROGRESS_FILE, WARN_OWNER_DIVERGENT, row.line, task.id,
            f"owner '{merged.owner_tasks.value}' in {TASKS_FILE} e "
            f"'{merged.owner_progress.value}' in {PROGRESS_FILE}: vale {PROGRESS_FILE}",
        ))
    return merged, found


def _unmatched_warnings(plan: str, task: Task, progress_has_table: bool) -> list[ParseWarning]:
    """Avvisi per una task del TASKS senza riga nel PROGRESS."""
    filename, line = task.source_lines[0]
    found = []
    if progress_has_table:
        found.append(_warning(
            plan, filename, WARN_TASK_WITHOUT_PROGRESS_ROW, line, task.id,
            f"nessuna riga in {PROGRESS_FILE}: avanzamento non dichiarato",
        ))
    return found + _status_unknown(plan, task, (filename, line))


def _dependency_warnings(plan: str, task: Task, known_ids: set[str]) -> list[ParseWarning]:
    """Un avviso per ogni dipendenza non qualificata verso un ID che il piano non ha.

    Le dipendenze con prefisso di repo (``crb/T-010``) puntano a un altro piano e
    non si controllano.
    """
    found = []
    for dependency in dict.fromkeys(task.dependencies):
        if "/" not in dependency and dependency not in known_ids:
            filename, line = task.source_lines[0]
            found.append(_warning(
                plan, filename, WARN_DEPENDENCY_UNKNOWN, line, task.id, dependency,
            ))
    return found


def _merge_progress(
    plan: str, base: tuple[Task, ...], tasks_file: FileRows, progress_file: FileRows,
) -> tuple[tuple[Task, ...], list[ParseWarning]]:
    """Unisce per ID le task del TASKS e le righe del PROGRESS.

    Prima le task del TASKS (con la loro riga del PROGRESS, se c'e'), poi quelle
    solo del PROGRESS nel loro ordine. Gli avvisi seguono l'ordine delle task.
    ``task_without_progress_row`` serve un PROGRESS con una tabella di task,
    ``progress_only_id`` un TASKS con una tabella di task.
    """
    progress_rows = {row.id: row for row in progress_file.rows}
    tasks_ids = {task.id for task in base}
    only_progress = tuple(row for row in progress_file.rows if row.id not in tasks_ids)
    known_ids = tasks_ids | {row.id for row in only_progress}
    merged: list[Task] = []
    warnings: list[ParseWarning] = []

    for task in base:
        row = progress_rows.get(task.id)
        if row is None:
            result, found = task, _unmatched_warnings(plan, task, progress_file.has_task_table)
        else:
            result, found = _overlay_progress(plan, task, row)
        merged.append(result)
        warnings += [*found, *_dependency_warnings(plan, result, known_ids)]

    for row in only_progress:
        result, found = _overlay_progress(plan, _progress_only_task(plan, row), row)
        merged.append(result)
        if tasks_file.has_task_table:
            warnings.append(_warning(
                plan, PROGRESS_FILE, WARN_PROGRESS_ONLY_ID, row.line, row.id,
                f"ID presente in {PROGRESS_FILE} e non in {TASKS_FILE}: task aggiunta fuori piano",
            ))
        warnings += found
    return tuple(merged), warnings


def read_plan(plan: str, tasks_text: str | None, progress_text: str | None) -> PlanTasks:
    """Le task di un piano: ``plan`` e' il percorso della cartella; i testi possono mancare.

    TASKS.md da' le task e PROGRESS.md le completa per ID (stato, avanzamento, owner,
    branch, note). Righe viste e lette sommano i due file. Gli avvisi sono in
    quest'ordine: quelli di TASKS.md per riga, quelli di PROGRESS.md per riga, poi
    quelli della sovrapposizione nell'ordine delle task. Testi assenti o vuoti
    danno una lettura vuota e non degradata.
    """
    tasks_file = read_task_rows(plan, TASKS_FILE, tasks_text)
    progress_file = read_task_rows(plan, PROGRESS_FILE, progress_text)
    base = tuple(_task_from_tasks_row(plan, TASKS_FILE, row) for row in tasks_file.rows)
    tasks_warnings = sorted(
        (*tasks_file.warnings, *_effort_warnings(plan, base)),
        key=lambda w: w.line or 0,
    )
    tasks, overlay_warnings = _merge_progress(plan, base, tasks_file, progress_file)
    return PlanTasks(
        plan,
        tasks,
        tasks_file.seen + progress_file.seen,
        tasks_file.read + progress_file.read,
        (*tasks_warnings, *progress_file.warnings, *overlay_warnings),
    )
