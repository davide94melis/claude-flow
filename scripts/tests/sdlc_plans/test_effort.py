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
