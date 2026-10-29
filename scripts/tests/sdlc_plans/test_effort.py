import pytest
from sdlc_plans.effort import parse_effort

@pytest.mark.parametrize("cell,days", [
    ("`2 gg`", 2.0), ("1,5", 1.5), ("1.0", 1.0), ("~2 gg", 2.0), ("2", 2.0),
    ("~~`3 gg`~~ **0**", 0.0),
    ("`4 gg` **+3,0 gg** → **7,0 gg**", 7.0), ("4 gg -> 6 gg", 6.0),
    ("1.0-1.5", 1.5), ("2-3 gg", 3.0), ("0,5 + 1", 1.5),
    ("T-020 1 gg", 1.0),
    ("`2` + quota dei `+0,5`", 2.0),
    ("(in T-004)", None), ("—", None), ("-", None), ("", None),
    ("2026-10-07", None), ("500", None), ("parecchio", None),
])
def test_parse_effort_days(cell, days):
    assert parse_effort(cell).days == days

def test_simple_number_has_empty_note_and_keeps_raw():
    e = parse_effort("`2 gg`")
    assert e.note == "" and e.raw == "`2 gg`"

@pytest.mark.parametrize("cell,fragment", [
    ("—", "non dichiarato"), ("(in T-004)", "non dichiarato"),
    ("500", "non plausibile"), ("2026-10-07", "non plausibile"), ("parecchio", "nessun numero"),
])
def test_missing_or_unreadable_effort_explains_why(cell, fragment):
    assert fragment in parse_effort(cell).note


# Casi limite oltre ai test del brief: il dato mancante non diventa mai 0.
@pytest.mark.parametrize("cell,days", [
    ("0", 0.0), ("0,0", 0.0), ("~0,5 gg", 0.5), ("1 g", 1.0), ("2d", 2.0), ("2 D", 2.0),
    ("+2", 2.0), ("2 +", 2.0), ("200", 200.0),
    ("2gg-3gg", 3.0), ("2 – 3 gg", 3.0), ("5 + -3", 2.0), ("0,1 + 0,2", 0.3),
    ("2 → 3 → 4", 4.0), ("t-020 1 gg", 1.0), ("2 gg (dal 07/10)", 2.0),
    ("~~3 gg~~ 4 gg", 4.0),
])
def test_parse_effort_edge_values(cell, days):
    assert parse_effort(cell).days == days

@pytest.mark.parametrize("cell,fragment", [
    ("+", "nessun numero"), ("-2", "non plausibile: -2"), ("- 2 gg", "non plausibile: -2"),
    ("200,5", "non plausibile: 200.5"), ("9" * 400, "non plausibile"),
    ("1/2", "non plausibile: data"), ("2 gg 07/10", "non plausibile: data"),
    ("   ", "non dichiarato"), ("\t", "non dichiarato"), ("(a) (b)", "non dichiarato"),
    ("~~3 gg~~", "nessun numero"), ("T-004", "nessun numero"), ("4 gg →", "nessun numero"),
])
def test_parse_effort_edge_cases_are_none_with_a_reason(cell, fragment):
    e = parse_effort(cell)
    assert e.days is None and fragment in e.note

def test_raw_is_the_original_cell_unmodified():
    cell = "  ~~`3 gg`~~ **0**  "
    assert parse_effort(cell).raw == cell

def test_read_with_rules_names_them_in_the_note():
    assert parse_effort("1.0-1.5").note == "letta; intervallo, preso il massimo"
    assert parse_effort("4 gg -> 6 gg").note == "letta; freccia, preso l'ultimo valore"
    assert parse_effort("T-020 1 gg").note == "letta; riferimenti a task ignorati"


# R29: un numero seguito da un'unita' che non e' di giorni (o da `%`) non e' un numero di giorni.
@pytest.mark.parametrize("cell,token", [
    ("4 ore", "ore"), ("50%", "%"), ("2 sett", "sett"), ("2h", "h"), ("3 mesi", "mesi"),
    ("1,5 settimane", "settimane"), ("2 gg + 3 ore", "ore"), ("~2 ore", "ore"),
])
def test_unknown_unit_or_percent_gives_no_days_and_names_the_unit(cell, token):
    e = parse_effort(cell)
    assert e.days is None and e.note == f"unità non riconosciuta: {token}"


@pytest.mark.parametrize("cell,days", [
    ("2 giorni", 2.0), ("1 giorno", 1.0), ("3 giornate", 3.0), ("1 giornata", 1.0), ("2 days", 2.0),
    ("1 day", 1.0), ("2 gu", 2.0), ("2 md", 2.0), ("1,5 gg/uomo", 1.5), ("2 GG", 2.0), ("2 Giorni", 2.0),
    ("2-3 giorni", 3.0), ("1 gg + 2 giorni", 3.0), ("~~4 ore~~ 2 gg", 2.0), ("2 gg (3 ore)", 2.0),
    ("4 gg → 6 giorni", 6.0),
])
def test_day_units_are_accepted_case_insensitively(cell, days):
    assert parse_effort(cell).days == days


def test_plain_number_with_a_day_unit_has_an_empty_note():
    assert parse_effort("2 giorni").note == "" and parse_effort("1,5 gg/uomo").note == ""


def test_unknown_unit_in_a_plan_gives_an_effort_unreadable_warning():
    from sdlc_plans.tasks import read_plan
    pt = read_plan("p", "| ID | Owner | Effort |\n|---|---|---|\n| T-001 | A | 4 ore |\n| T-002 | A | 2 giorni |\n", None)
    assert [t.effort.days for t in pt.tasks] == [None, 2.0]
    (w,) = [w for w in pt.warnings if w.code == "effort_unreadable"]
    assert (w.line, w.detail) == (3, "T-001: unità non riconosciuta: ore")
