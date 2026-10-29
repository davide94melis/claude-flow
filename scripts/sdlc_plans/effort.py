"""Lettura della cella Effort di una task.

Un valore assente o illeggibile non diventa mai 0: ``days`` e' ``None`` e ``note``
spiega perche'. ``0`` resta possibile solo se la cella lo dichiara (``0``, ``0,0``).
Solo libreria standard.
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable

from .model import Effort
from .vocab import clean_markup

MAX_EFFORT_DAYS = 200.0

NOTE_UNDECLARED = "non dichiarato"
NOTE_NO_NUMBER = "nessun numero leggibile"
NOTE_NOT_PLAUSIBLE = "valore non plausibile"
NOTE_READ = "letta"

_NUM = r"\d+(?:[.,]\d+)?"
_UNIT = r"(?:gg|g|d)"
# Trattino lungo (U+2014) e medio (U+2013): intervallo, mai segno meno.
_LONG_DASHES = "–—"

# Numero semplice: `~` e unita' (gg, g, d) facoltativi, virgola o punto decimale.
_SIMPLE_RE = re.compile(rf"~?\s*({_NUM})\s*{_UNIT}?", re.IGNORECASE)
_STRIKE_RE = re.compile(r"~~.*?~~")
_PAREN_RE = re.compile(r"\([^()]*\)")
_DATE_RE = re.compile(
    r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"
    r"|(?<![\d/])\d{1,2}/\d{1,2}(?:/\d{2,4})?(?![\d/])"
)
_TASK_ID_RE = re.compile(r"(?<![A-Za-z0-9])[Tt]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
_QUOTA_RE = re.compile(
    rf"quota\s+(?:dei|del|della|delle|degli|di)\s+[+-]?\s*{_NUM}(?:\s*{_UNIT}\b)?",
    re.IGNORECASE,
)
_ARROW_RE = re.compile(r"→|->")
# Un addendo: segno facoltativo, numero, unita' facoltativa, secondo estremo di un
# intervallo `a-b` / `a–b` facoltativo.
_TOKEN_RE = re.compile(
    rf"(?P<sign>[+-])?\s*(?P<a>{_NUM})(?:\s*{_UNIT}\b)?"
    rf"(?:(?:-|\s*[{_LONG_DASHES}]\s*)(?P<b>{_NUM}))?",
    re.IGNORECASE,
)

_Step = tuple[str, Callable[[str], str]]


def _to_float(number: str) -> float:
    return float(number.replace(",", "."))


def _unmarked(text: str) -> str:
    """Toglie il markup con ``clean_markup`` ma senza perdere un segno meno iniziale.

    ``clean_markup`` toglie i trattini ai bordi (per riconoscere i segnaposto):
    il sentinella ``\\0`` in testa li protegge, cosi' ``-2`` resta ``-2``.
    """
    return clean_markup("\0" + text)[1:].strip()


def _drop_parens(text: str) -> str:
    """Toglie i testi tra parentesi, anche annidati."""
    while True:
        stripped = _PAREN_RE.sub(" ", text)
        if stripped == text:
            return text
        text = stripped


def _last_arrow_segment(text: str) -> str:
    return _ARROW_RE.split(text)[-1]


def _sub(pattern: re.Pattern[str]) -> Callable[[str], str]:
    return lambda text: pattern.sub(" ", text)


_BEFORE_DATE_STEPS: tuple[_Step, ...] = (
    ("segmenti barrati ignorati", _sub(_STRIKE_RE)),
    ("testo tra parentesi ignorato", _drop_parens),
)
_AFTER_DATE_STEPS: tuple[_Step, ...] = (
    ("riferimenti a task ignorati", _sub(_TASK_ID_RE)),
    ("quota ignorata", _sub(_QUOTA_RE)),
    ("freccia, preso l'ultimo valore", _last_arrow_segment),
)


def _apply(text: str, steps: tuple[_Step, ...]) -> tuple[str, tuple[str, ...]]:
    """Applica i passi in ordine: testo risultante e etichette dei passi che l'hanno cambiato."""
    applied: list[str] = []
    for label, step in steps:
        changed = step(text)
        if changed != text:
            applied.append(label)
            text = changed
    return text, tuple(applied)


def _format_days(value: float) -> str:
    if value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return str(value)


def _finish(cell: str, total: float, note: str) -> Effort:
    """Controllo di plausibilita': vale per ogni risultato numerico."""
    days = round(total, 6) + 0.0  # + 0.0 normalizza -0.0
    if not math.isfinite(days) or days < 0 or days > MAX_EFFORT_DAYS:
        return Effort(cell, None, f"{NOTE_NOT_PLAUSIBLE}: {_format_days(days)}")
    return Effort(cell, days, note)


def _is_undeclared(cell: str) -> bool:
    """Vuota, solo un segnaposto (``—``, ``-``) o solo un rimando tra parentesi."""
    cleaned = clean_markup(cell)
    return not cleaned or not _drop_parens(cleaned).strip()


def _read_tokens(cell: str, text: str, applied: tuple[str, ...]) -> Effort:
    tokens = list(_TOKEN_RE.finditer(text))
    if not tokens:
        return Effort(cell, None, NOTE_NO_NUMBER)
    total = 0.0
    has_range = False
    for token in tokens:
        value = _to_float(token["a"])
        if token["b"] is not None:
            value = max(value, _to_float(token["b"]))
            has_range = True
        total += -value if token["sign"] == "-" else value
    rules = list(applied)
    if has_range:
        rules.append("intervallo, preso il massimo")
    if len(tokens) > 1:
        rules.append(f"somma di {len(tokens)} valori")
    return _finish(cell, total, "; ".join([NOTE_READ, *rules]))


def parse_effort(cell: str) -> Effort:
    """Legge la cella Effort: ``raw`` e' la cella originale, ``days`` mai 0 per un dato mancante.

    Con ``days=None`` la nota dice perche' (``non dichiarato``, ``nessun numero
    leggibile``, ``valore non plausibile: <n>``). Un numero semplice ha nota vuota;
    un valore letto con regole (barrati, intervallo, freccia, somma...) ha nota
    ``letta; <regole>``.
    """
    if _is_undeclared(cell):
        return Effort(cell, None, NOTE_UNDECLARED)
    text = _unmarked(cell)
    simple = _SIMPLE_RE.fullmatch(text)
    if simple:
        return _finish(cell, _to_float(simple.group(1)), "")
    text, before = _apply(text, _BEFORE_DATE_STEPS)
    if _DATE_RE.search(text):
        return Effort(cell, None, f"{NOTE_NOT_PLAUSIBLE}: data")
    text, after = _apply(text, _AFTER_DATE_STEPS)
    return _read_tokens(cell, text, before + after)
