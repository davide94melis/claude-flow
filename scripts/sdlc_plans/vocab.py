"""Vocabolario condiviso: ripulitura del markup, intestazioni, stati, ID e owner.

Funzioni pure sul testo; solo libreria standard.
"""
from __future__ import annotations

import re
import unicodedata

STATUSES: tuple[str, ...] = (
    "Da iniziare",
    "In corso",
    "Completata",
    "Bloccata",
    "Annullata",
    "Sospesa",
)

# ---------------------------------------------------------------------------
# Ripulitura del markup
# ---------------------------------------------------------------------------

# Emoji, simboli e pittogrammi (anche ✅ ✔ ⏳), selettori di variante,
# zero-width joiner e keycap. Le frecce e i segni di punteggiatura restano.
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # emoji e pittogrammi
    "\u2300-\u23FF"          # tecnici vari
    "\u2600-\u27BF"          # simboli vari e dingbats
    "\u2B00-\u2BFF"          # frecce e simboli vari
    "\uFE00-\uFE0F"          # selettori di variante
    "\u200D\u20E3"           # joiner e keycap
    "]"
)
_SPACES_RE = re.compile(r"\s+")
# spazio, trattino lungo (U+2014), trattino medio (U+2013), trattino
_BORDER_CHARS = " \u2014\u2013-"


def clean_markup(text: str) -> str:
    """Toglie ``**``, backtick, emoji e selettori di variante.

    Comprime gli spazi e toglie spazio, trattino lungo, trattino medio e trattino
    ai bordi, cosi' un segnaposto fatto di un solo trattino diventa vuoto.
    """
    out = text.replace("**", "").replace("`", "")
    out = _EMOJI_RE.sub("", out)
    out = _SPACES_RE.sub(" ", out)
    return out.strip(_BORDER_CHARS)


# ---------------------------------------------------------------------------
# Intestazioni di colonna
# ---------------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def norm_header(text: str) -> str:
    """Forma di confronto di un'intestazione.

    Minuscolo, senza accenti, l'apostrofo tipografico diventa ``'``, senza spazi e
    senza ``'`` e ``.`` finali: ``"Attivita’"`` -> ``"attivita"``,
    ``"Bloccata da"`` -> ``"bloccatada"``.
    """
    out = _strip_accents(text.lower()).replace("’", "'")
    out = _SPACES_RE.sub("", out)
    return out.rstrip("'.")


# Chiavi nella forma di norm_header (minuscole, senza accenti e senza spazi).
_FIELD_ALIASES: dict[str, str] = {
    "id": "id",
    "stream": "stream",
    "attivita": "activity",
    "activity": "activity",
    "titolo": "activity",
    "descrizione": "description",
    "description": "description",
    "owner": "owner",
    "sviluppatore": "owner",
    "developer": "owner",
    "area": "area",
    "layer": "area",
    "priorita": "priority",
    "priority": "priority",
    "pri": "priority",
    "prio": "priority",
    "wave": "wave",
    "dipendenze": "dependencies",
    "dependencies": "dependencies",
    "dip": "dependencies",
    "effort": "effort",
    "stima": "effort",
    "branch": "branch",
    "progresso": "progress",
    "progress": "progress",
    "%": "progress",
    "stato": "status",
    "status": "status",
    "note": "note",
    "nota": "note",
    "notes": "note",
    "bloccatada": "blocked_by",
    "blockedby": "blocked_by",
}


def canonical_field(header: str) -> str | None:
    """Campo canonico di un'intestazione di colonna, ``None`` se non e' nota."""
    return _FIELD_ALIASES.get(norm_header(clean_markup(header)))


# ---------------------------------------------------------------------------
# Stati
# ---------------------------------------------------------------------------

# Tabella ordinata: la prima etichetta con un prefisso che combacia vince.
_STATUS_PREFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Completata", ("completata", "completed", "complete", "done", "chiusa", "closed")),
    ("In corso", ("in corso", "in progress", "in lavorazione", "wip")),
    ("Da iniziare", ("da iniziare", "da fare", "todo", "to do", "not started", "non iniziata")),
    ("Bloccata", ("bloccata", "blocked", "non avviabile", "da non lavorare")),
    (
        "Annullata",
        (
            "annullata", "cancelled", "canceled", "fuori perimetro",
            "out of scope", "ritirata", "superata", "withdrawn",
        ),
    ),
    ("Sospesa", ("sospesa", "suspended", "on hold", "in pausa")),
)

_STRIKE_RE = re.compile(r"~~.*?~~")
_HISTORY_SPLIT_RE = re.compile(r"\s·\s|prima:", re.IGNORECASE)
_PAREN_SUFFIX_RE = re.compile(r"\s*\(.*$")


def canon_status(cell: str) -> tuple[str, bool]:
    """Stato canonico di una cella: ``(etichetta, riconosciuto)``.

    Toglie i segmenti barrati, tiene la parte prima di `` · `` e di ``prima:``,
    toglie il markup e i suffissi tra parentesi, poi confronta per prefisso.
    Senza corrispondenza restituisce ``(testo pulito, False)``.
    """
    text = _STRIKE_RE.sub("", cell)
    text = _HISTORY_SPLIT_RE.split(text, maxsplit=1)[0]
    text = clean_markup(text)
    without_suffix = _PAREN_SUFFIX_RE.sub("", text)
    if without_suffix:
        text = clean_markup(without_suffix)
    folded = _strip_accents(text.lower())
    for label, prefixes in _STATUS_PREFIXES:
        if folded.startswith(prefixes):
            return label, True
    return text, False


# ---------------------------------------------------------------------------
# ID di task
# ---------------------------------------------------------------------------

# Un ID di task e' `T-<sigla>`, con un prefisso alfanumerico facoltativo (`QA-T-001`).
# `T-` resta maiuscolo: `qa-t-001` ha la forma di un ID ma non e' valido.
TASK_ID_RE = re.compile(r"^(?:[A-Za-z0-9]+-)?T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
# Un ID di task dentro un testo: `T-` non preceduto da una lettera o da una cifra.
TASK_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z0-9]+-)?T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
# Il nucleo dell'ID: la parte da `T-` in poi.
_ID_CORE_PREFIX = "-T-"


def normalize_id(cell: str) -> str | None:
    """ID di task in forma canonica, ``None`` se la cella non e' un ID.

    Toglie backtick, ``*`` e spazi ai bordi; l'ID va tutto in maiuscolo, prefisso compreso.
    """
    text = cell.strip().strip("`*").strip()
    if not TASK_ID_RE.match(text):
        return None
    return text.upper()


def id_core(task_id: str) -> str:
    """La parte dell'ID da ``T-`` in poi: ``QA-T-MERGE-1`` -> ``T-MERGE-1``, ``T-001`` resta com'e'."""
    if task_id.startswith("T-"):
        return task_id
    _, separator, rest = task_id.partition(_ID_CORE_PREFIX)
    return f"T-{rest}" if separator else task_id


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

OWNER_PLACEHOLDERS: frozenset[str] = frozenset(
    {"agent", "tbd", "-", "\u2014", "\u2013", "n/a", "na", "?", "nessuno", ""}
)

_OWNER_CUT_RE = re.compile(r"\(| — | – | - |;|,")


def is_placeholder(text: str) -> bool:
    """Vero se il testo e' un segnaposto e non il nome di una persona."""
    return clean_markup(text).lower() in OWNER_PLACEHOLDERS


def owner_base(text: str) -> str:
    """Nome dell'owner senza ruolo, data o note: il testo prima del primo separatore."""
    head = _OWNER_CUT_RE.split(clean_markup(text), maxsplit=1)[0]
    return clean_markup(head)
