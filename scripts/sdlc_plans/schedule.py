"""Calendario di un piano: inizio, scadenza, fattore di produttivita' e milestone.

Ogni campo si risolve per conto suo, al primo livello che lo da':

1. **forma fissa**: una tabella ``Chiave | Valore`` (formato che ``sdlc-analyzer`` e
   ``sdlc-estimator`` scrivono: e' un contratto), in ogni documento nell'ordine dato;
2. **intestazione**: righe ``Etichetta: valore`` di ``PLAN.md``;
3. **testo**: prosa di ``ESTIMATE.md`` e poi ``PLAN.md`` (milestone e fattore).

Ogni valore porta la fonte da cui viene. Un dato non trovato resta ``None``: mai un
valore inventato. Solo libreria standard.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import cast

from .model import Milestone, ParseWarning, Schedule
from .tables import Table, scan_tables
from .vocab import clean_markup, norm_header

FIXED_KEYS = ("start", "deadline", "deadline_kind", "productivity_factor")
DEADLINE_KINDS = ("dev-drop", "uat", "go-live", "altro")

WARN_DATE_INVALID = "date_invalid"
WARN_FACTOR_INVALID = "factor_invalid"
WARN_FACTOR_AMBIGUOUS = "factor_ambiguous"
WARN_DEADLINE_KIND_UNKNOWN = "deadline_kind_unknown"

SOURCE_FIXED = "forma fissa"
SOURCE_HEADER = "intestazione"
SOURCE_TEXT = "testo"
NOT_PROVIDED = "non fornita"

_BOM = "\ufeff"

PLAN_FILE = "PLAN.md"
ESTIMATE_FILE = "ESTIMATE.md"
# Una milestone e' la parola chiave seguita da una data entro questi caratteri non numerici.
MAX_KEYWORD_GAP = 30
# La scadenza che si legge dal testo e' la prima milestone di questo ordine.
_DEADLINE_PRIORITY = ("dev-drop", "uat", "go-live")

_KEY_HEADERS = frozenset({"chiave", "key"})
_VALUE_HEADERS = frozenset({"valore", "value"})
_EMPTY_VALUES = frozenset({"", "-", "—", "–"})

# Data: AAAA-MM-GG, oppure GG/MM/AAAA e GG-MM-AAAA. Le cifre attorno non fanno parte della data.
_DATE_SOURCE = (
    r"(?<!\d)(?:(?P<iy>\d{4})-(?P<im>\d{2})-(?P<id>\d{2})"
    r"|(?P<dd>\d{1,2})[/-](?P<dm>\d{1,2})[/-](?P<dy>\d{4}))(?!\d)"
)
_DATE_RE = re.compile(_DATE_SOURCE)
_ISO_RE = re.compile(r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})$")
_AFTER_KEYWORD_RE = re.compile(r"[^\d]{0,%d}" % MAX_KEYWORD_GAP + _DATE_SOURCE)

_NUMBER = r"(\d+(?:[.,]\d+)?)"
_FIXED_FACTOR_RE = re.compile(r"^[÷/]?\s*" + _NUMBER + r"$")
_EXPLICIT_FACTOR_RE = re.compile(
    r"(?:fattore(?:\s+di\s+produttivit[àa]['’]?)?|productivity\s+factor)\s*[:=]\s*÷?\s*" + _NUMBER,
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(r"÷\s*" + _NUMBER)

_KEYWORD_RE = re.compile(
    r"\b(dev\s*drop|drop\s*dev|rilascio\s+dev|uat|collaudo|go[\s-]?live|produzione)\b",
    re.IGNORECASE,
)
_KIND_BY_KEYWORD = {
    "devdrop": "dev-drop",
    "dropdev": "dev-drop",
    "rilasciodev": "dev-drop",
    "uat": "uat",
    "collaudo": "uat",
    "golive": "go-live",
    "produzione": "go-live",
}

_LIST_MARKER = r"^(?:[-*>+]\s*)*"


def _header_label(label: str) -> re.Pattern[str]:
    # Qualunque qualificazione e' ammessa tra l'etichetta e i due punti.
    return re.compile(_LIST_MARKER + label + r"\b[^:]*:\s*(?P<value>.*)$", re.IGNORECASE)


_HEADER_LABELS = (
    ("start", _header_label(r"(?:data\s+(?:di\s+)?inizio(?:\s+ufficiale)?|start\s+date)")),
    ("deadline", _header_label(r"(?:deadline|scadenza|data\s+di\s+consegna|due\s+date)")),
)
_ABSENT_RE = re.compile(r"^(?:non\s+fornit[ao]|n/d|tbd|da\s+definire)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Documento e costruttore del risultato
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Doc:
    """Un documento letto: righe ripulite dal markup, senza le righe della forma fissa."""

    name: str
    lines: tuple[str, ...]
    fixed_rows: tuple[tuple[int, str, str], ...]  # (riga, chiave, valore) in ordine


class _Builder:
    """Raccoglie i valori man mano; ``build`` li consegna in un ``Schedule`` immutabile."""

    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.sources: dict[str, str] = {}
        self.from_text: set[str] = set()
        self.milestones: list[Milestone] = []
        self.warnings: list[ParseWarning] = []

    def has(self, key: str) -> bool:
        return key in self.values

    def set(self, key: str, value: object, source: str, *, from_text: bool = False) -> None:
        self.values[key] = value
        self.sources[key] = source
        if from_text:
            self.from_text.add(key)

    def warn(self, code: str, name: str, line: int | None, detail: str) -> None:
        self.warnings.append(ParseWarning(code, "", name, line, detail))

    def add_milestone(self, kind: str, day: date, source: str) -> None:
        """Una milestone con lo stesso tipo e giorno di una gia' vista e' la stessa: resta la prima."""
        if not any(m.kind == kind and m.day == day for m in self.milestones):
            self.milestones.append(Milestone(kind, day, source))

    def build(self) -> Schedule:
        return Schedule(
            start=cast("date | None", self.values.get("start")),
            deadline=cast("date | None", self.values.get("deadline")),
            deadline_kind=cast("str | None", self.values.get("deadline_kind")),
            factor=cast("float | None", self.values.get("productivity_factor")),
            sources=dict(self.sources),
            from_text=tuple(key for key in FIXED_KEYS if key in self.from_text),
            milestones=tuple(sorted(self.milestones, key=lambda m: m.day)),
            warnings=tuple(self.warnings),
        )


def _basename(name: str) -> str:
    return re.split(r"[/\\]", name)[-1]


def _is_file(name: str, expected: str) -> bool:
    return _basename(name).lower() == expected.lower()


def _cell_text(cell: str) -> str:
    """Valore di una cella senza ``**`` e backtick; un segnaposto di soli trattini e' vuoto."""
    text = cell.replace("**", "").replace("`", "").strip()
    return "" if text in _EMPTY_VALUES else text


def _is_fixed_table(table: Table) -> bool:
    if len(table.headers) < 2:
        return False
    first, second = (norm_header(clean_markup(header)) for header in table.headers[:2])
    return first in _KEY_HEADERS and second in _VALUE_HEADERS


def _load(name: str, text: str) -> _Doc:
    """Legge un documento: le righe del blocco in forma fissa si estraggono e si svuotano.

    Svuotate (non tolte) cosi' i numeri di riga restano quelli del file e il blocco
    non viene riletto come prosa.
    """
    lines = re.split(r"\r?\n", text.removeprefix(_BOM))
    rows: list[tuple[int, str, str]] = []
    for table in (t for t in scan_tables(text).tables if _is_fixed_table(t)):
        for row in table.rows:
            key = clean_markup(row.cells[0]).lower()
            value = _cell_text(row.cells[1])
            if key in FIXED_KEYS and value:
                rows.append((row.line, key, value))
        last = table.rows[-1].line if table.rows else table.header_line + 1
        for number in range(table.header_line, min(last, len(lines)) + 1):
            lines[number - 1] = ""
    return _Doc(name, tuple(clean_markup(line) for line in lines), tuple(rows))


# ---------------------------------------------------------------------------
# Date e numeri
# ---------------------------------------------------------------------------

def _day_of(match: re.Match[str]) -> date | None:
    """Il giorno di una data trovata, ``None`` se la data non esiste (30 febbraio...)."""
    parts = match.groupdict()
    try:
        if parts["iy"]:
            return date(int(parts["iy"]), int(parts["im"]), int(parts["id"]))
        return date(int(parts["dy"]), int(parts["dm"]), int(parts["dd"]))
    except ValueError:
        return None


def _positive_number(literal: str) -> float | None:
    value = float(literal.replace(",", "."))
    return value if math.isfinite(value) and value > 0 else None


# ---------------------------------------------------------------------------
# Livello 1: forma fissa
# ---------------------------------------------------------------------------

def _fixed_date(b: _Builder, name: str, line: int, raw: str) -> date | None:
    match = _ISO_RE.match(raw)
    try:
        if match:
            return date(int(match["y"]), int(match["m"]), int(match["d"]))
    except ValueError:
        pass
    b.warn(WARN_DATE_INVALID, name, line, f"data «{raw}» non valida: serve AAAA-MM-GG e deve esistere")
    return None


def _fixed_kind(b: _Builder, name: str, line: int, raw: str) -> str:
    if raw.lower() in DEADLINE_KINDS:
        return raw.lower()
    b.warn(
        WARN_DEADLINE_KIND_UNKNOWN, name, line,
        f"tipo di scadenza «{raw}» non previsto (previsti: {', '.join(DEADLINE_KINDS)}): tenuto com'e'",
    )
    return raw


def _fixed_factor(b: _Builder, name: str, line: int, raw: str) -> float | None:
    match = _FIXED_FACTOR_RE.match(raw)
    value = _positive_number(match.group(1)) if match else None
    if value is None:
        b.warn(WARN_FACTOR_INVALID, name, line, f"fattore «{raw}» non valido: serve un numero maggiore di zero")
    return value


def _read_fixed(b: _Builder, doc: _Doc) -> None:
    for line, key, raw in doc.fixed_rows:
        if key == "deadline_kind":
            value: object = _fixed_kind(b, doc.name, line, raw)
        elif key == "productivity_factor":
            value = _fixed_factor(b, doc.name, line, raw)
        else:
            value = _fixed_date(b, doc.name, line, raw)
        if value is not None and not b.has(key):
            b.set(key, value, f"{SOURCE_FIXED} · {doc.name}")


# ---------------------------------------------------------------------------
# Livello 2: intestazione di PLAN.md
# ---------------------------------------------------------------------------

def _header_value(b: _Builder, name: str, key: str, line: int, value: str) -> bool:
    """Legge il valore dopo l'etichetta; vero se la riga ha deciso il campo."""
    if _ABSENT_RE.match(value):
        b.sources[key] = f"{SOURCE_HEADER} · {name}: {NOT_PROVIDED}"
        return True
    match = _DATE_RE.search(value)
    if match is None:
        return False
    day = _day_of(match)
    if day is None:
        b.warn(WARN_DATE_INVALID, name, line, f"data «{match.group()}» non esiste")
    else:
        b.set(key, day, f"{SOURCE_HEADER} · {name}")
    return True


def _read_header(b: _Builder, doc: _Doc) -> None:
    if not _is_file(doc.name, PLAN_FILE):
        return
    decided = {key for key, _ in _HEADER_LABELS if b.has(key)}
    for number, line in enumerate(doc.lines, start=1):
        for key, label in _HEADER_LABELS:
            match = label.match(line) if key not in decided else None
            if match and _header_value(b, doc.name, key, number, match["value"]):
                decided.add(key)


# ---------------------------------------------------------------------------
# Livello 3: testo (milestone, scadenza, fattore)
# ---------------------------------------------------------------------------

def _kind_of(keyword: str) -> str:
    return _KIND_BY_KEYWORD[re.sub(r"[\s-]", "", keyword.lower())]


def _read_milestones(b: _Builder, doc: _Doc) -> None:
    """Milestone: parola chiave e data sulla stessa riga; la data e' della parola chiave piu' vicina."""
    source = f"{SOURCE_TEXT} · {doc.name}"
    for number, line in enumerate(doc.lines, start=1):
        found = list(_KEYWORD_RE.finditer(line))
        for index, keyword in enumerate(found):
            end = found[index + 1].start() if index + 1 < len(found) else len(line)
            hit = _AFTER_KEYWORD_RE.match(line[keyword.end():end])
            if hit is None:
                continue
            day = _day_of(hit)
            if day is None:
                literal = re.sub(r"^\D+", "", hit.group(0))
                b.warn(WARN_DATE_INVALID, doc.name, number, f"data «{literal}» non esiste")
            else:
                b.add_milestone(_kind_of(keyword.group(1)), day, source)


def _resolve_deadline_from_text(b: _Builder) -> None:
    """La scadenza e' la prima milestone dell'ordine dev-drop, uat, go-live; il tipo la segue."""
    if b.has("deadline"):
        return
    for kind in _DEADLINE_PRIORITY:
        for milestone in b.milestones:
            if milestone.kind == kind:
                b.set("deadline", milestone.day, milestone.source, from_text=True)
                if not b.has("deadline_kind"):
                    b.set("deadline_kind", kind, milestone.source, from_text=True)
                return


def _factor_values(doc: _Doc) -> list[tuple[int, str, float]]:
    """Valori del fattore in un documento: quelli espliciti, altrimenti tutti i ``÷N``."""
    for pattern in (_EXPLICIT_FACTOR_RE, _DIVISION_RE):
        found = []
        for number, line in enumerate(doc.lines, start=1):
            for match in pattern.finditer(line):
                value = _positive_number(match.group(1))
                if value is not None:
                    found.append((number, match.group(1), value))
        if found:
            return found
    return []


def _resolve_factor_from_text(b: _Builder, docs: list[_Doc]) -> None:
    """Decide il primo documento che ha valori: un solo valore distinto o ``factor_ambiguous``."""
    if b.has("productivity_factor"):
        return
    for doc in docs:
        found = _factor_values(doc)
        if not found:
            continue
        distinct = list(dict.fromkeys(value for _, _, value in found))
        if len(distinct) == 1:
            b.set("productivity_factor", distinct[0], f"{SOURCE_TEXT} · {doc.name}", from_text=True)
        else:
            firsts = {value: (line, literal) for line, literal, value in reversed(found)}
            listed = ", ".join(f"{firsts[v][1]} (riga {firsts[v][0]})" for v in distinct)
            b.warn(WARN_FACTOR_AMBIGUOUS, doc.name, found[0][0], f"valori diversi nel documento: {listed}")
        return


def _text_rank(doc: _Doc) -> int:
    return 0 if _is_file(doc.name, ESTIMATE_FILE) else 1


# ---------------------------------------------------------------------------
# Interfaccia pubblica
# ---------------------------------------------------------------------------

def read_schedule(docs: Mapping[str, str | None]) -> Schedule:
    """Calendario di un piano dai suoi documenti (nome del file -> testo).

    ``docs`` e' nell'ordine di priorita' del chiamante (``PLAN.md`` prima di
    ``ESTIMATE.md``): vale per la forma fissa. Il testo si legge sempre prima in
    ``ESTIMATE.md``. I documenti con testo ``None`` si saltano.
    """
    b = _Builder()
    loaded = [_load(name, text) for name, text in docs.items() if text is not None]
    for doc in loaded:
        _read_fixed(b, doc)
    for doc in loaded:
        _read_header(b, doc)
    text_docs = sorted(loaded, key=_text_rank)
    for doc in text_docs:
        _read_milestones(b, doc)
    _resolve_deadline_from_text(b)
    _resolve_factor_from_text(b, text_docs)
    return b.build()


_MERGE_FIELDS = (
    ("start", "start"),
    ("deadline", "deadline"),
    ("deadline_kind", "deadline_kind"),
    ("productivity_factor", "factor"),
)


def _taken_keys(own: Schedule, inherited: Schedule) -> set[str]:
    """Campi che ``own`` prende da ``inherited``: quelli ``None``; il tipo solo se manca anche la scadenza."""
    taken = set()
    if own.start is None and inherited.start is not None:
        taken.add("start")
    if own.deadline is None and inherited.deadline is not None:
        taken.add("deadline")
    if own.deadline is None and own.deadline_kind is None and inherited.deadline_kind is not None:
        taken.add("deadline_kind")
    if own.factor is None and inherited.factor is not None:
        taken.add("productivity_factor")
    return taken


def _merged_sources(own: Schedule, inherited: Schedule, label: str, taken: set[str]) -> dict[str, str]:
    """Fonti del risultato: una per ogni valore preso da ``inherited``, piu' quelle di ``own``.

    Senza valore la fonte c'e' solo se dice «non fornita»: quella dichiarata da ``own``, o,
    se ``own`` non dice nulla e il campo resta ``None``, quella dichiarata dalla wave.
    """
    sources = dict(own.sources)
    for key, attr in _MERGE_FIELDS:
        inherited_source = inherited.sources.get(key)
        if key in taken:
            sources[key] = f"{label} · {inherited_source}" if inherited_source else label
        elif (
            key not in sources
            and getattr(own, attr) is None
            and getattr(inherited, attr) is None
            and inherited_source
        ):
            sources[key] = f"{label} · {inherited_source}"
    return sources


def merge_schedule(own: Schedule, inherited: Schedule, label: str) -> Schedule:
    """``own`` con i campi mancanti presi da ``inherited``, con la fonte prefissata da ``label``.

    Il tipo di scadenza si eredita solo se ``own`` non ha ne' scadenza ne' tipo.
    Milestone e avvisi sono quelli di ``own`` piu' quelli di ``inherited`` (milestone
    ordinate per data; una milestone con stesso tipo e giorno resta una sola).
    """
    taken = _taken_keys(own, inherited)
    picked = {attr: getattr(inherited if key in taken else own, attr) for key, attr in _MERGE_FIELDS}
    milestones = list(own.milestones)
    for milestone in inherited.milestones:
        if not any(m.kind == milestone.kind and m.day == milestone.day for m in milestones):
            milestones.append(Milestone(milestone.kind, milestone.day, f"{label} · {milestone.source}"))
    from_text = set(own.from_text) | {key for key in inherited.from_text if key in taken}
    return Schedule(
        start=picked["start"],
        deadline=picked["deadline"],
        deadline_kind=picked["deadline_kind"],
        factor=picked["factor"],
        sources=_merged_sources(own, inherited, label, taken),
        from_text=tuple(key for key in FIXED_KEYS if key in from_text),
        milestones=tuple(sorted(milestones, key=lambda m: m.day)),
        warnings=own.warnings + inherited.warnings,
    )
