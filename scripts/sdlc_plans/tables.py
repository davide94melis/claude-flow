"""Tabelle markdown dei piani: lettura tollerante, con righe orfane e avvisi.

``scan_tables`` non interpreta il significato delle colonne (lo fanno i lettori
di TASKS e PROGRESS): restituisce celle normalizzate, numeri di riga reali e gli
avvisi di cio' che ha dovuto aggiustare. Solo libreria standard.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .vocab import TASK_TOKEN_RE, canonical_field, normalize_id

WARN_COLUMN_COUNT_MISMATCH = "column_count_mismatch"
WARN_TABLE_CONTINUED_AFTER_BLANK = "table_continued_after_blank"
WARN_TABLE_HEADER_INSIDE_TABLE = "table_header_inside_table"

_BOM = "\ufeff"
_LINE_BREAK_RE = re.compile(r"\r?\n")
# Byte di controllo, esclusi tab, a capo e ritorno a capo.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")
_SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")

ScanWarning = tuple[str, int, str]


@dataclass(frozen=True)
class Row:
    """Una riga di tabella: numero di riga (da 1) e celle normalizzate."""

    line: int
    cells: tuple[str, ...]


@dataclass(frozen=True)
class Table:
    """Una tabella: riga dell'intestazione, intestazioni, campi canonici e righe."""

    header_line: int
    headers: tuple[str, ...]
    fields: tuple[str | None, ...]
    rows: tuple[Row, ...]


@dataclass(frozen=True)
class TableScan:
    """Esito della lettura: tabelle, righe senza tabella e avvisi (codice, riga, dettaglio)."""

    tables: tuple[Table, ...]
    orphan_rows: tuple[Row, ...]
    warnings: tuple[ScanWarning, ...]


def _prepare_lines(text: str) -> list[str]:
    """Toglie il BOM, rende visibili i byte di controllo e divide in righe fisiche."""
    if text.startswith(_BOM):
        text = text[len(_BOM):]
    text = _CONTROL_RE.sub(lambda m: f"\\x{ord(m.group()):02x}", text)
    return _LINE_BREAK_RE.split(text)


def _split_row(stripped: str) -> list[str]:
    """Celle di una riga di tabella (gia' senza spazi ai bordi), con `\\|` reso `/`.

    Mai vuota: una riga con il solo `|` ha una cella vuota, cosi' `cells[0]` esiste sempre.
    """
    tokens = _UNESCAPED_PIPE_RE.split(stripped[1:])
    if tokens[-1] == "":  # riga chiusa da `|`
        tokens.pop()
    return [token.replace("\\|", "/").strip() for token in tokens] or [""]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL_RE.match(cell) for cell in cells)


def _is_table_line(line: str) -> bool:
    return line.strip().startswith("|")


def _fit(cells: list[str], width: int) -> tuple[str, ...]:
    """Porta le celle alla larghezza dell'intestazione: unisce l'eccesso o completa con ``""``."""
    if len(cells) > width:
        return (*cells[: width - 1], " | ".join(cells[width - 1:]))
    return (*cells, *([""] * (width - len(cells))))


class _Scanner:
    """Stato della lettura riga per riga; il risultato e' fatto di dataclass immutabili."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self._tables: list[Table] = []
        self._orphans: list[Row] = []
        self._warnings: list[ScanWarning] = []
        # Tabella aperta: intestazioni (None se non c'e') e righe raccolte finora.
        self._header_line = 0
        self._headers: list[str] | None = None
        self._rows: list[Row] = []
        self._after_blank = False

    def scan(self) -> TableScan:
        skip_separator = False
        for index, line in enumerate(self._lines):
            if skip_separator:
                skip_separator = False
                continue
            if not line.strip():
                self._after_blank = True
            elif not _is_table_line(line):
                self._close()
            else:
                skip_separator = self._table_line(index, _split_row(line.strip()))
        self._close()
        return TableScan(tuple(self._tables), tuple(self._orphans), tuple(self._warnings))

    def _starts_table(self, index: int, cells: list[str]) -> bool:
        """Una riga di tabella con subito sotto un separatore e' un'intestazione.

        Fa eccezione la riga il cui primo valore e' un ID di task valido, o contiene
        comunque un ID di task (barrato, combinato, con un link): e' una riga di dati, e
        la riga di trattini sotto (``| - | - |``) e' una riga come le altre.
        """
        if normalize_id(cells[0]) is not None or TASK_TOKEN_RE.search(cells[0]):
            return False
        if index + 1 >= len(self._lines):
            return False
        below = self._lines[index + 1]
        return _is_table_line(below) and _is_separator(_split_row(below.strip()))

    def _table_line(self, index: int, cells: list[str]) -> bool:
        """Gestisce una riga di tabella; vero se la riga sotto (separatore) va saltata."""
        number = index + 1
        is_open = self._headers is not None
        starts = self._starts_table(index, cells)
        if starts:
            if is_open and not self._after_blank:
                self._warnings.append((
                    WARN_TABLE_HEADER_INSIDE_TABLE,
                    number,
                    f"intestazione con separatore sotto una tabella aperta (intestazione a riga "
                    f"{self._header_line}): inizia una nuova tabella",
                ))
            self._close()
            self._headers = cells
            self._header_line = number
            return True
        if not is_open:
            self._orphans.append(Row(number, tuple(cells)))
        elif self._after_blank and len(cells) != len(self._headers):
            self._close()
            self._orphans.append(Row(number, tuple(cells)))
        else:
            self._add_row(number, cells)
        self._after_blank = False
        return False

    def _add_row(self, number: int, cells: list[str]) -> None:
        width = len(self._headers)
        if self._after_blank:
            self._warnings.append((
                WARN_TABLE_CONTINUED_AFTER_BLANK,
                number,
                f"riga dopo una riga vuota: continua la tabella con intestazione a riga {self._header_line}",
            ))
        elif len(cells) > width:
            self._warnings.append((
                WARN_COLUMN_COUNT_MISMATCH,
                number,
                f"{len(cells)} celle contro {width} dell'intestazione: le celle in piu' sono unite all'ultima",
            ))
        self._rows.append(Row(number, _fit(cells, width)))

    def _close(self) -> None:
        if self._headers is not None:
            headers = tuple(self._headers)
            fields = tuple(canonical_field(header) for header in headers)
            self._tables.append(Table(self._header_line, headers, fields, tuple(self._rows)))
        self._headers = None
        self._rows = []
        self._after_blank = False


def scan_tables(text: str) -> TableScan:
    """Legge tutte le tabelle markdown di un testo.

    Righe senza `|` finale restano valide; `\\|` diventa `/`; BOM e CRLF non
    cambiano l'esito; i numeri di riga sono quelli fisici del testo originale.
    Una riga vuota non chiude la tabella (avviso ``table_continued_after_blank``
    se dopo la riga vuota riprende con lo stesso numero di colonne); una riga di
    testo la chiude e le righe di tabella successive diventano orfane. Una riga di
    tabella con un separatore subito sotto inizia sempre una nuova tabella; se ne
    interrompe una aperta, senza riga vuota in mezzo, scatta l'avviso
    ``table_header_inside_table``. Non vale per una riga con un ID di task nella
    prima cella (anche barrato o combinato): e' una riga di dati e non apre mai una
    tabella. Ogni riga, orfana o no, ha almeno una cella.
    """
    return _Scanner(_prepare_lines(text)).scan()
