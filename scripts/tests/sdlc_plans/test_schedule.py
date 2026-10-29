from datetime import date

import pytest

from sdlc_plans.schedule import read_schedule, merge_schedule

FIXED = "| Chiave | Valore |\n|---|---|\n| `start` | 2026-09-09 |\n| `deadline` | 2026-10-16 |\n| `deadline_kind` | dev-drop |\n| `productivity_factor` | 3 |\n"

def test_fixed_block_wins_over_header_and_text():
    s = read_schedule({"PLAN.md": "Deadline: 2026-12-31\n" + FIXED, "ESTIMATE.md": "DEV drop: 2026-11-30\n÷2\n"})
    assert (s.start, s.deadline, s.deadline_kind, s.factor) == (date(2026, 9, 9), date(2026, 10, 16), "dev-drop", 3.0)
    assert s.sources["deadline"] == "forma fissa · PLAN.md" and s.from_text == ()

def test_plan_header_labels_with_markup_and_italian_date():
    s = read_schedule({"PLAN.md": "**Data inizio ufficiale:** 2026-09-01\n**Deadline dichiarata nell'AFU:** 30/10/2026\n"})
    assert (s.start, s.deadline) == (date(2026, 9, 1), date(2026, 10, 30))
    assert s.sources["start"] == "intestazione · PLAN.md"

def test_header_non_fornita():
    s = read_schedule({"PLAN.md": "Deadline: non fornita\n"})
    assert s.deadline is None and s.sources["deadline"] == "intestazione · PLAN.md: non fornita"

def test_estimate_prose_dev_drop_and_milestones(plans_fixtures):
    est = (plans_fixtures / "nested/plans/in-progress/2026-07-29_wave-x/ESTIMATE.md").read_text(encoding="utf-8")
    s = read_schedule({"PLAN.md": None, "ESTIMATE.md": est})
    assert (s.deadline, s.deadline_kind) == (date(2026, 10, 16), "dev-drop")
    assert [(m.kind, m.day) for m in s.milestones] == [("dev-drop", date(2026, 10, 16)), ("uat", date(2026, 11, 6))]
    assert s.factor == 3.0 and set(s.from_text) == {"deadline", "deadline_kind", "productivity_factor"}
    assert s.sources["productivity_factor"] == "testo · ESTIMATE.md"

def test_factor_ambiguous_in_text():
    s = read_schedule({"ESTIMATE.md": "prima ÷3, poi ÷2\n"})
    assert s.factor is None and [w.code for w in s.warnings] == ["factor_ambiguous"]

def test_fixed_block_factor_forms():
    for v, f in [("2,5", 2.5), ("÷3", 3.0), ("/4", 4.0)]:
        assert read_schedule({"PLAN.md": f"| Key | Value |\n|---|---|\n| productivity_factor | {v} |\n"}).factor == f

def test_invalid_date_and_unknown_kind_warn():
    s = read_schedule({"PLAN.md": "| Chiave | Valore |\n|---|---|\n| `deadline` | 2026-02-30 |\n| `deadline_kind` | sprint |\n"})
    assert s.deadline is None and s.deadline_kind == "sprint"
    assert [w.code for w in s.warnings] == ["date_invalid", "deadline_kind_unknown"]

def test_merge_schedule_inherits_wave_fields_with_label():
    own = read_schedule({"PLAN.md": "Data inizio ufficiale: 2026-09-01\n"})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\n"})
    m = merge_schedule(own, wave, "wave 2026-07-29_wave-x")
    assert (m.start, m.deadline) == (date(2026, 9, 1), date(2026, 10, 16))
    assert m.sources["deadline"] == "wave 2026-07-29_wave-x · testo · ESTIMATE.md"


# ---------------------------------------------------------------------------
# Casi limite oltre ai test del brief
# ---------------------------------------------------------------------------

def _fixed(*rows: str) -> str:
    return "| Chiave | Valore |\n|---|---|\n" + "".join(f"| {r} |\n" for r in rows)


def _codes(s):
    return [w.code for w in s.warnings]


# --- forma fissa -----------------------------------------------------------

def test_fixed_block_title_is_irrelevant_and_unknown_keys_are_ignored():
    text = "## Un titolo qualunque\n\n" + _fixed("`start` | 2026-09-09", "`colore` | blu")
    s = read_schedule({"PLAN.md": text})
    assert s.start == date(2026, 9, 9) and s.warnings == ()

def test_fixed_block_keys_compare_without_markup_and_case():
    s = read_schedule({"PLAN.md": _fixed("**`Start`** | `2026-09-09`", "DEADLINE | 2026-10-16")})
    assert (s.start, s.deadline) == (date(2026, 9, 9), date(2026, 10, 16))

def test_fixed_block_requires_chiave_valore_header():
    s = read_schedule({"PLAN.md": "| Nome | Dato |\n|---|---|\n| start | 2026-09-09 |\n"})
    assert s.start is None and s.sources == {}

def test_fixed_block_date_must_be_iso():
    s = read_schedule({"PLAN.md": _fixed("deadline | 30/10/2026")})
    assert s.deadline is None and _codes(s) == ["date_invalid"]
    assert s.warnings[0].file == "PLAN.md" and s.warnings[0].plan == "" and s.warnings[0].line == 3

def test_fixed_block_empty_value_is_just_absent():
    s = read_schedule({"PLAN.md": _fixed("deadline | ", "start | —")})
    assert s.deadline is None and s.start is None and s.warnings == ()

@pytest.mark.parametrize("value", ["abc", "0", "-2", "÷0", "3x", "1e3"])
def test_fixed_block_invalid_factor_warns(value):
    s = read_schedule({"PLAN.md": _fixed(f"productivity_factor | {value}")})
    assert s.factor is None and _codes(s) == ["factor_invalid"]

def test_fixed_block_known_kind_is_canonical_regardless_of_case():
    s = read_schedule({"PLAN.md": _fixed("deadline_kind | UAT")})
    assert s.deadline_kind == "uat" and s.warnings == ()

def test_fixed_block_first_document_that_gives_the_field_wins():
    a = _fixed("deadline | 2026-10-16")
    b = _fixed("deadline | 2026-11-20", "start | 2026-09-01")
    s = read_schedule({"PLAN.md": a, "ESTIMATE.md": b})
    assert (s.deadline, s.start) == (date(2026, 10, 16), date(2026, 9, 1))
    assert s.sources["deadline"] == "forma fissa · PLAN.md"
    assert s.sources["start"] == "forma fissa · ESTIMATE.md"

def test_fixed_block_rows_are_not_read_again_as_text():
    # `uat` in una riga e una data nella successiva non fanno una milestone.
    s = read_schedule({"PLAN.md": _fixed("deadline_kind | uat", "start | 2026-09-09")})
    assert s.milestones == () and s.deadline is None

def test_fixed_block_factor_means_no_text_factor_warning():
    s = read_schedule({"PLAN.md": _fixed("productivity_factor | 3"), "ESTIMATE.md": "÷3 e poi ÷2\n"})
    assert s.factor == 3.0 and s.warnings == () and s.from_text == ()

def test_fixed_block_invalid_value_lets_lower_levels_answer():
    s = read_schedule({"PLAN.md": _fixed("deadline | 2026-02-30") + "Deadline: 2026-12-31\n"})
    assert s.deadline == date(2026, 12, 31) and _codes(s) == ["date_invalid"]
    assert s.sources["deadline"] == "intestazione · PLAN.md"


# --- intestazione ----------------------------------------------------------

def test_header_tbd_is_declared_absent_and_text_can_still_answer():
    s = read_schedule({"PLAN.md": "Deadline: TBD\n", "ESTIMATE.md": "DEV drop: 2026-10-16\n"})
    assert s.deadline == date(2026, 10, 16)
    assert s.sources["deadline"] == "testo · ESTIMATE.md"

@pytest.mark.parametrize("value", ["TBD", "n/d", "N/D", "da definire", "Non fornita nell'AFU"])
def test_header_absent_markers(value):
    s = read_schedule({"PLAN.md": f"Data inizio: {value}\n"})
    assert s.start is None and s.sources["start"] == "intestazione · PLAN.md: non fornita"

def test_header_is_read_only_in_plan_md():
    s = read_schedule({"ESTIMATE.md": "Deadline: 2026-10-01\n"})
    assert s.deadline is None

@pytest.mark.parametrize("line,field,expected", [
    ("Start date: 01-09-2026", "start", date(2026, 9, 1)),
    ("> Scadenza: 15/11/2026", "deadline", date(2026, 11, 15)),
    ("* Due date: 2026-11-15", "deadline", date(2026, 11, 15)),
    ("- **Data di consegna:** 5/1/2027", "deadline", date(2027, 1, 5)),
    ("Data di inizio ufficiale: 2026-09-01", "start", date(2026, 9, 1)),
    ("Data inizio: 2026-09-01", "start", date(2026, 9, 1)),
    ("Data di consegna: 01/09/2026", "deadline", date(2026, 9, 1)),
])
def test_header_labels_and_date_formats(line, field, expected):
    s = read_schedule({"PLAN.md": line + "\n"})
    other = "deadline" if field == "start" else "start"
    assert getattr(s, field) == expected and getattr(s, other) is None
    assert s.sources == {field: "intestazione · PLAN.md"}

def test_header_label_must_start_the_line():
    s = read_schedule({"PLAN.md": "La nostra deadline: 2026-10-01\nNessuna scadenza: 2026-11-01\n"})
    assert s.deadline is None

def test_header_impossible_dates_warn_and_set_nothing():
    s = read_schedule({"PLAN.md": "Deadline: 2026-02-30\nData inizio: 31/02/2026\n"})
    assert (s.start, s.deadline) == (None, None) and _codes(s) == ["date_invalid", "date_invalid"]
    assert [w.line for w in s.warnings] == [1, 2]

def test_header_label_without_date_or_marker_is_ignored():
    s = read_schedule({"PLAN.md": "Deadline: entro fine ottobre\n"})
    assert s.deadline is None and s.sources == {} and s.warnings == ()


# --- testo: milestone e scadenza ------------------------------------------

def test_milestone_keywords_and_kinds():
    text = "Rilascio DEV 2026-10-01\ncollaudo 2026-10-20\nGo-Live 2026-11-01\nproduzione 2026-11-15\ndrop dev 2026-09-20\n"
    s = read_schedule({"ESTIMATE.md": text})
    assert [(m.kind, m.day) for m in s.milestones] == [
        ("dev-drop", date(2026, 9, 20)), ("dev-drop", date(2026, 10, 1)), ("uat", date(2026, 10, 20)),
        ("go-live", date(2026, 11, 1)), ("go-live", date(2026, 11, 15)),
    ]
    assert all(m.source == "testo · ESTIMATE.md" for m in s.milestones)

def test_milestone_keywords_use_word_boundaries():
    s = read_schedule({"ESTIMATE.md": "Il sito situato qui, lavoro attuato 2026-10-01\n"})
    assert s.milestones == () and s.deadline is None

def test_milestone_date_must_be_within_30_non_numeric_chars():
    near = "UAT" + "." * 29 + " 2026-11-06\n"   # 30 caratteri tra parola e data
    far = "UAT" + "." * 30 + " 2026-11-06\n"    # 31
    assert [m.day for m in read_schedule({"ESTIMATE.md": near}).milestones] == [date(2026, 11, 6)]
    assert read_schedule({"ESTIMATE.md": far}).milestones == ()

def test_milestone_gap_with_a_digit_does_not_match():
    assert read_schedule({"ESTIMATE.md": "UAT sprint 4: 2026-11-06\n"}).milestones == ()

def test_milestone_with_impossible_date_warns_and_is_dropped():
    s = read_schedule({"ESTIMATE.md": "ok\nUAT: 31/02/2026\n"})
    assert s.milestones == () and s.deadline is None
    assert _codes(s) == ["date_invalid"] and s.warnings[0].line == 2 and s.warnings[0].file == "ESTIMATE.md"

def test_milestone_date_never_crosses_a_line():
    s = read_schedule({"ESTIMATE.md": "| UAT | n/d |\n| Go-live | 2026-12-01 |\n"})
    assert [(m.kind, m.day) for m in s.milestones] == [("go-live", date(2026, 12, 1))]

def test_milestone_date_belongs_to_the_nearest_keyword_on_the_line():
    s = read_schedule({"ESTIMATE.md": "UAT: n/d, Go-live 2026-12-01\n"})
    assert [(m.kind, m.day) for m in s.milestones] == [("go-live", date(2026, 12, 1))]

def test_same_milestone_mentioned_twice_is_listed_once():
    s = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\nin sintesi: Dev drop 16/10/2026\n"})
    assert [(m.kind, m.day, m.source) for m in s.milestones] == [("dev-drop", date(2026, 10, 16), "testo · ESTIMATE.md")]

def test_same_kind_with_different_dates_keeps_both():
    s = read_schedule({"ESTIMATE.md": "UAT 2026-11-06\nUAT 2026-11-20\n"})
    assert [m.day for m in s.milestones] == [date(2026, 11, 6), date(2026, 11, 20)]
    assert s.deadline == date(2026, 11, 6) and s.sources["deadline"] == "testo · ESTIMATE.md"

def test_text_deadline_prefers_dev_drop_then_uat_then_go_live():
    s = read_schedule({"ESTIMATE.md": "Go-live: 2026-12-01\nUAT: 2026-11-06\n"})
    assert (s.deadline, s.deadline_kind) == (date(2026, 11, 6), "uat")
    s = read_schedule({"ESTIMATE.md": "Go-live: 2026-12-01\nUAT: 2026-11-06\nDEV drop: 2026-12-15\n"})
    assert (s.deadline, s.deadline_kind) == (date(2026, 12, 15), "dev-drop")

def test_deadline_kind_is_not_set_when_deadline_comes_from_header():
    s = read_schedule({"PLAN.md": "Deadline: 2026-12-31\n", "ESTIMATE.md": "DEV drop: 2026-11-30\n"})
    assert s.deadline == date(2026, 12, 31) and s.deadline_kind is None
    assert s.from_text == () and [m.kind for m in s.milestones] == ["dev-drop"]

def test_kind_from_fixed_form_stays_when_text_gives_the_deadline():
    s = read_schedule({"PLAN.md": _fixed("deadline_kind | altro"), "ESTIMATE.md": "UAT: 2026-11-06\n"})
    assert (s.deadline, s.deadline_kind) == (date(2026, 11, 6), "altro")
    assert s.from_text == ("deadline",)

def test_text_level_reads_only_estimate_md_never_plan_md_prose():
    # R25 (spec 5.6): la prosa di PLAN.md non da' date; PLAN.md vale per forma fissa e intestazione.
    s = read_schedule({"PLAN.md": "UAT: 2026-11-06\nGo-live 2026-12-01\n÷2\n", "ESTIMATE.md": "DEV drop: 2026-10-16\n"})
    assert [m.kind for m in s.milestones] == ["dev-drop"]
    assert (s.deadline, s.factor) == (date(2026, 10, 16), None)
    only_plan = read_schedule({"PLAN.md": "UAT: 2026-11-06\nGo-live 2026-12-01\nfattore: 3\n÷2\n"})
    assert only_plan.milestones == () and only_plan.deadline is None and only_plan.factor is None
    assert only_plan.sources == {} and only_plan.from_text == () and only_plan.warnings == ()

def test_declared_absent_deadline_is_not_invented_from_incidental_plan_prose():
    plan = "Deadline: non fornita\n\nAmbiente di produzione aggiornato il 12/03/2026.\nCollaudo del 2026-04-02.\n"
    s = read_schedule({"PLAN.md": plan})
    assert s.deadline is None and s.milestones == () and s.deadline_kind is None
    assert s.sources["deadline"] == "intestazione · PLAN.md: non fornita"

def test_fixed_form_and_header_still_come_from_plan_md_while_text_comes_from_estimate():
    s = read_schedule({"PLAN.md": "Data inizio: 2026-09-01\nDeadline: non fornita\n", "ESTIMATE.md": "UAT: 2026-11-06\n÷3\n"})
    assert s.start == date(2026, 9, 1) and s.sources["start"] == "intestazione · PLAN.md"
    assert (s.deadline, s.deadline_kind, s.factor) == (date(2026, 11, 6), "uat", 3.0)


# --- testo: fattore --------------------------------------------------------

@pytest.mark.parametrize("text,factor", [
    ("÷2,5\n", 2.5), ("÷2.5\n", 2.5), ("÷3 e ancora ÷3,0\n", 3.0), ("÷ 4\n", 4.0),
    ("Fattore di produttività: 3\n", 3.0), ("**Fattore di produttività:** ÷2,5\n", 2.5),
    ("productivity factor = 4\n", 4.0), ("fattore: 3 ma anche ÷2\n", 3.0),
])
def test_text_factor_forms(text, factor):
    s = read_schedule({"ESTIMATE.md": text})
    assert s.factor == factor and s.warnings == ()
    assert s.sources["productivity_factor"] == "testo · ESTIMATE.md" and s.from_text == ("productivity_factor",)

def test_text_factor_conflicting_explicit_values_are_ambiguous():
    s = read_schedule({"ESTIMATE.md": "fattore: 3\nproductivity factor = ÷4\n"})
    assert s.factor is None and _codes(s) == ["factor_ambiguous"] and s.warnings[0].line == 1

def test_text_factor_zero_is_ignored():
    s = read_schedule({"ESTIMATE.md": "÷0 poi ÷3\n"})
    assert s.factor == 3.0 and s.warnings == ()

def test_text_factor_comes_from_estimate_even_when_plan_md_prose_differs():
    s = read_schedule({"PLAN.md": "÷2\n", "ESTIMATE.md": "÷3\n"})
    assert s.factor == 3.0 and s.sources["productivity_factor"] == "testo · ESTIMATE.md" and s.warnings == ()

def test_text_factor_in_plan_md_prose_is_not_used_when_estimate_has_none():
    s = read_schedule({"PLAN.md": "÷2\nfattore: 4\n", "ESTIMATE.md": "nessun fattore\n"})
    assert s.factor is None and "productivity_factor" not in s.sources and s.warnings == ()

def test_text_factor_ambiguity_is_judged_on_estimate_alone():
    s = read_schedule({"PLAN.md": "÷2\n", "ESTIMATE.md": "÷3 ÷4\n"})
    assert s.factor is None and _codes(s) == ["factor_ambiguous"] and s.warnings[0].file == "ESTIMATE.md"
    s = read_schedule({"PLAN.md": "÷2 ÷5\n", "ESTIMATE.md": "÷3\n"})
    assert s.factor == 3.0 and s.warnings == ()


# --- input -----------------------------------------------------------------

def test_empty_and_none_documents_give_an_empty_schedule():
    for docs in ({}, {"PLAN.md": None}, {"PLAN.md": None, "ESTIMATE.md": None}, {"PLAN.md": ""}):
        s = read_schedule(docs)
        assert (s.start, s.deadline, s.deadline_kind, s.factor) == (None, None, None, None)
        assert s.sources == {} and s.from_text == () and s.milestones == () and s.warnings == ()

def test_crlf_and_bom_do_not_change_the_result():
    plan = "\ufeffData inizio: 2026-09-01\r\nDeadline: 30/10/2026\r\n"
    estimate = "\ufeffUAT: 2026-11-06\r\n÷3\r\n"
    s = read_schedule({"PLAN.md": plan, "ESTIMATE.md": estimate})
    assert (s.start, s.deadline, s.factor) == (date(2026, 9, 1), date(2026, 10, 30), 3.0)
    assert [m.day for m in s.milestones] == [date(2026, 11, 6)]
    s = read_schedule({"PLAN.md": FIXED.replace("\n", "\r\n")})
    assert (s.start, s.deadline, s.deadline_kind, s.factor) == (date(2026, 9, 9), date(2026, 10, 16), "dev-drop", 3.0)


# --- merge -----------------------------------------------------------------

def test_merge_keeps_own_values_and_does_not_take_what_is_set():
    own = read_schedule({"PLAN.md": _fixed("deadline | 2026-12-31", "productivity_factor | 2")})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\n÷3\n"})
    m = merge_schedule(own, wave, "wave w")
    assert (m.deadline, m.factor) == (date(2026, 12, 31), 2.0)
    assert m.sources["deadline"] == "forma fissa · PLAN.md"
    # `own` ha una scadenza ma non un tipo: il tipo della wave non c'entra.
    assert m.deadline_kind is None
    assert m.from_text == ()
    # Una fonte solo per i valori che ci sono: niente fonte per il tipo non ereditato.
    assert m.sources == {"deadline": "forma fissa · PLAN.md", "productivity_factor": "forma fissa · PLAN.md"}

def test_merge_records_no_kind_source_when_the_kind_is_not_inherited():
    own = read_schedule({"PLAN.md": _fixed("deadline | 2026-12-31")})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\n"})
    m = merge_schedule(own, wave, "wave w")
    assert (m.deadline, m.deadline_kind) == (date(2026, 12, 31), None)
    assert "deadline_kind" not in m.sources
    assert m.sources == {"deadline": "forma fissa · PLAN.md"}

_MERGE_CASES = [
    ({"PLAN.md": _fixed("deadline | 2026-12-31")}, {"ESTIMATE.md": "DEV drop: 2026-10-16\n÷3\n"}),
    ({"PLAN.md": _fixed("deadline_kind | altro")}, {"ESTIMATE.md": "DEV drop: 2026-10-16\n"}),
    ({"PLAN.md": _fixed("start | 2026-09-01")}, {"ESTIMATE.md": "UAT: 2026-11-06\n÷2\n"}),
    ({"PLAN.md": "Deadline: TBD\nData inizio: n/d\n"}, {"ESTIMATE.md": "UAT: 2026-11-06\n"}),
    ({"PLAN.md": "Deadline: TBD\n"}, {"PLAN.md": "Deadline: non fornita\nData inizio: TBD\n"}),
    ({"PLAN.md": "Deadline: TBD\n"}, {}),
    ({}, {"PLAN.md": _fixed("deadline_kind | uat")}),
    ({"PLAN.md": _fixed("deadline | 2026-12-31", "productivity_factor | 2")}, {"PLAN.md": FIXED}),
    ({}, {}),
]

@pytest.mark.parametrize("own_docs,wave_docs", _MERGE_CASES)
def test_merge_sources_exist_only_for_values_taken_or_declared_absent(own_docs, wave_docs):
    own, wave = read_schedule(own_docs), read_schedule(wave_docs)
    for schedule in (own, wave, merge_schedule(own, wave, "w")):
        values = {"start": schedule.start, "deadline": schedule.deadline,
                  "deadline_kind": schedule.deadline_kind, "productivity_factor": schedule.factor}
        for key, source in schedule.sources.items():
            assert values[key] is not None or (key in ("start", "deadline") and source.endswith(": non fornita")), key
        for key, value in values.items():
            assert value is None or key in schedule.sources, key

def test_merge_inherits_kind_with_deadline_and_carries_from_text():
    own = read_schedule({"PLAN.md": "Data inizio: 2026-09-01\n"})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\n÷3\n"})
    m = merge_schedule(own, wave, "wave w")
    assert (m.deadline_kind, m.factor) == ("dev-drop", 3.0)
    assert m.sources["deadline_kind"] == "wave w · testo · ESTIMATE.md"
    assert m.sources["start"] == "intestazione · PLAN.md"
    assert set(m.from_text) == {"deadline", "deadline_kind", "productivity_factor"}

def test_merge_does_not_inherit_kind_when_own_has_one():
    own = read_schedule({"PLAN.md": _fixed("deadline_kind | altro")})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\n"})
    m = merge_schedule(own, wave, "w")
    assert (m.deadline, m.deadline_kind) == (date(2026, 10, 16), "altro")
    assert m.from_text == ("deadline",)

def test_merge_milestones_and_warnings_are_combined_and_sorted():
    own = read_schedule({"ESTIMATE.md": "UAT: 2026-11-06\nGo-live: 31/02/2026\n"})
    wave = read_schedule({"ESTIMATE.md": "DEV drop: 2026-10-16\nUAT: 2026-11-06\n"})
    m = merge_schedule(own, wave, "wave w")
    assert [(x.kind, x.day, x.source) for x in m.milestones] == [
        ("dev-drop", date(2026, 10, 16), "wave w · testo · ESTIMATE.md"),
        ("uat", date(2026, 11, 6), "testo · ESTIMATE.md"),
    ]
    assert _codes(m) == ["date_invalid"]

def test_merge_with_nothing_to_inherit_changes_nothing_and_does_not_mutate():
    own = read_schedule({"PLAN.md": "Deadline: TBD\n"})
    wave = read_schedule({})
    before = dict(own.sources)
    m = merge_schedule(own, wave, "w")
    assert (m.start, m.deadline, m.factor) == (None, None, None)
    assert m.sources == before and own.sources == before

def test_merge_declared_absent_is_replaced_when_the_wave_has_a_value():
    own = read_schedule({"PLAN.md": "Deadline: TBD\n"})
    wave = read_schedule({"ESTIMATE.md": "UAT: 2026-11-06\n"})
    m = merge_schedule(own, wave, "w")
    assert m.deadline == date(2026, 11, 6) and m.sources["deadline"] == "w · testo · ESTIMATE.md"
