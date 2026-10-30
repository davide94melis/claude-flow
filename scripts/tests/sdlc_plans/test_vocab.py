import pytest

from sdlc_plans.vocab import (
    canon_status,
    canonical_field,
    is_placeholder,
    normalize_id,
    owner_base,
)


@pytest.mark.parametrize("cell,expected", [
    ("✅ **Completata** (2026-09-28) · prima: 🚧 In corso", ("Completata", True)),
    ("Completata (no-op verificato)", ("Completata", True)),
    ("Chiusa (TL, 2026-10-07)", ("Completata", True)),
    ("Completed", ("Completata", True)), ("Done", ("Completata", True)),
    ("In progress", ("In corso", True)), ("Blocked", ("Bloccata", True)),
    ("Non avviabile", ("Bloccata", True)),
    ("Fuori perimetro", ("Annullata", True)), ("Ritirata", ("Annullata", True)),
    ("Superata", ("Annullata", True)), ("~~In corso~~ Completata", ("Completata", True)),
    ("**Annullata**", ("Annullata", True)), ("sospesa", ("Sospesa", True)),
    ("Draft ready", ("Draft ready", False)), ("", ("", False)),
])
def test_canon_status(cell, expected):
    assert canon_status(cell) == expected


@pytest.mark.parametrize("header,field", [
    ("Attività", "activity"), ("Attivita'", "activity"), ("Attivita’", "activity"),
    ("Titolo", "activity"), ("Activity", "activity"), ("Pri", "priority"), ("Prio", "priority"),
    ("Priority", "priority"), ("Priorità", "priority"), ("Dip.", "dependencies"),
    ("Dependencies", "dependencies"), ("Layer", "area"), ("Bloccata da", "blocked_by"),
    ("Blocked by", "blocked_by"), ("Progresso", "progress"), ("%", "progress"),
    ("Notes", "note"), ("Stato", "status"), ("Trasmesso il", None),
])
def test_canonical_field(header, field):
    assert canonical_field(header) == field


@pytest.mark.parametrize("cell,expected", [
    ("`T-020`", "T-020"), ("**T-020**", "T-020"), ("T-051-fix", "T-051-FIX"),
    ("T-MERGE-ws", "T-MERGE-WS"), ("T-VER-03", "T-VER-03"), ("Q-01", None),
    ("_gate/BASE-WAVE", None), ("TOTALE", None),
    # prefisso alfanumerico facoltativo prima di `T-`: ID tutto maiuscolo
    ("QA-T-001", "QA-T-001"), ("`QA-T-001`", "QA-T-001"), ("**QA-T-001**", "QA-T-001"),
    ("QA2-T-MERGE-1", "QA2-T-MERGE-1"),
    ("qa-t-001", None), ("t-001", None), ("XT-005", None), ("QA-001", None),
    ("QA-T-", None), ("T-001+T-002", None), ("QA-T-001 bis", None),
])
def test_normalize_id(cell, expected):
    assert normalize_id(cell) == expected


def test_owner_helpers():
    assert all(is_placeholder(x) for x in ["agent", "TBD", "—", "-", "", "n/a"])
    assert owner_base("Alice (TL, 2026-10-08; nota)") == "Alice"
    assert owner_base("Bruno — fuori perimetro") == "Bruno"
    assert owner_base("Bruno – fuori perimetro") == "Bruno"
    assert owner_base("Carla-Maria") == "Carla-Maria"  # il trattino senza spazi non separa
