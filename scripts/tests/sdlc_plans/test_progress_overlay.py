import pytest

from sdlc_plans.model import Cell
from sdlc_plans.tasks import read_plan

SUBA = "plans/in-progress/2026-07-29_wave-x/sub-a"

def _plan(plans_fixtures, root, rel):
    d = plans_fixtures / root / rel
    t = d / "TASKS.md"; p = d / "PROGRESS.md"
    return read_plan(rel, t.read_text(encoding="utf-8") if t.exists() else None,
                     p.read_text(encoding="utf-8") if p.exists() else None)

def _codes(pt, code):
    return [w.detail.split(":")[0] for w in pt.warnings if w.code == code]

def test_progress_overrides_status_progress_branch_note(plans_fixtures):
    pt = _plan(plans_fixtures, "flat", "plans/in-progress/2026-09-01_alpha")
    t3 = {t.id: t for t in pt.tasks}["T-003"]
    assert (t3.status, t3.progress, t3.branch.value, t3.note.value) == ("In corso", 60, "feature/alpha-ui-03", "Manca paginazione")
    assert t3.in_tasks and t3.in_progress and (pt.rows_seen, pt.rows_read) == (12, 12)

def test_decorated_and_mapped_statuses(plans_fixtures):
    by = {t.id: t for t in _plan(plans_fixtures, "nested", SUBA).tasks}
    assert by["T-001"].status == "Completata" and "prima" in by["T-001"].status_raw
    assert (by["T-002"].status, by["T-002"].progress) == ("Completata", 100)
    assert (by["T-004"].status, by["T-004"].progress) == ("Annullata", None)

def test_out_of_vocabulary_status_kept_with_warning(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    t10 = {t.id: t for t in pt.tasks}["T-010"]
    assert (t10.status, t10.status_known) == ("Draft ready", False)
    assert _codes(pt, "status_unknown") == ["T-010"]

def test_owner_rule(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    by = {t.id: t for t in pt.tasks}
    assert (by["T-001"].owner.value, by["T-001"].owner_source) == ("Alice", "tasks")
    assert (by["T-002"].owner.value, by["T-002"].owner_source) == ("Bruno", "progress")
    assert _codes(pt, "owner_divergent") == ["T-002"]

def test_english_progress_table(plans_fixtures):
    by = {t.id: t for t in _plan(plans_fixtures, "nested", "plans/in-progress/2026-07-29_wave-x/sub-b").tasks}
    assert (by["T-001"].status, by["T-001"].progress) == ("Completata", 100)
    assert (by["T-002"].status, by["T-002"].progress) == ("In corso", 50)

def test_progress_only_id_is_kept(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    t99 = {t.id: t for t in pt.tasks}["T-099"]
    assert (t99.in_tasks, t99.in_progress, t99.activity.value) == (False, True, "Hotfix")
    assert _codes(pt, "progress_only_id") == ["T-099"]

def test_task_without_progress_row(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    assert _codes(pt, "task_without_progress_row") == ["T-011"]
    assert {t.id: t for t in pt.tasks}["T-011"].status == "Da iniziare"

def test_ids_match_across_decoration(plans_fixtures):
    t = {t.id: t for t in _plan(plans_fixtures, "nested", SUBA).tasks}["T-051-FIX"]
    assert t.in_tasks and t.in_progress

def test_status_progress_mismatch_warning(plans_fixtures):
    assert _codes(_plan(plans_fixtures, "nested", SUBA), "status_progress_mismatch") == ["T-051-FIX"]

def test_progress_is_clamped_with_warning(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    assert {t.id: t for t in pt.tasks}["T-010"].progress == 100
    assert _codes(pt, "progress_unreadable") == ["T-010"]

def test_blocked_by_and_dependency_unknown(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", SUBA)
    assert {t.id: t for t in pt.tasks}["T-010"].blocked_by.value == "T-004"
    assert _codes(pt, "dependency_unknown") == ["T-011"]

def test_plan_with_only_progress(plans_fixtures):
    pt = _plan(plans_fixtures, "nested", "plans/in-progress/2026-07-29_wave-x/sub-c")
    (t,) = pt.tasks
    assert (t.id, t.status, t.in_tasks) == ("T-001", "Completata", False)


# ---------------------------------------------------------------------------
# Casi limite della sovrapposizione (testi sintetici)
# ---------------------------------------------------------------------------

TASKS_HEAD = "| ID | Owner | Effort | Dipendenze | Stato | Branch |\n|---|---|---|---|---|---|\n"
PROGRESS_HEAD = "| ID | Owner | Progresso | Stato | Branch | Bloccata da | Note |\n|---|---|---|---|---|---|---|\n"


def _read(tasks_rows, progress_rows, tasks_head=TASKS_HEAD, progress_head=PROGRESS_HEAD):
    tasks = tasks_head + tasks_rows if tasks_rows is not None else None
    progress = progress_head + progress_rows if progress_rows is not None else None
    return read_plan("p", tasks, progress)


def _warns(pt, code):
    return [w for w in pt.warnings if w.code == code]


def _by_id(pt):
    return {t.id: t for t in pt.tasks}


def test_duplicate_id_in_progress_first_row_wins_and_warns_on_progress_file():
    pt = _read(
        "| T-001 | A | 1 |  |  |  |\n",
        "| T-001 | A | 30% | In corso |  |  | prima |\n| T-001 | A | 90% | Completata |  |  | seconda |\n",
    )
    (t,) = pt.tasks
    assert (t.progress, t.status, t.note.value) == (30, "In corso", "prima")
    (w,) = _warns(pt, "duplicate_id")
    assert (w.file, w.line) == ("PROGRESS.md", 4)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (3, 3, False)


def test_progress_text_none_empty_or_without_task_table_adds_no_row_warning():
    only_summary = "| Metrica | Valore |\n|---|---|\n| Completate | 1 |\n"
    for progress in (None, "", only_summary):
        pt = read_plan("p", TASKS_HEAD + "| T-001 | A | 1 |  |  |  |\n", progress)
        assert _warns(pt, "task_without_progress_row") == [], progress
        t = pt.tasks[0]
        assert (t.in_progress, t.progress, t.status) == (False, None, "Da iniziare")


def test_progress_with_an_empty_task_table_flags_every_task_without_row():
    pt = _read("| T-001 | A | 1 |  |  |  |\n| T-002 | A | 1 |  |  |  |\n", "")
    assert [w.detail.split(":")[0] for w in _warns(pt, "task_without_progress_row")] == ["T-001", "T-002"]


def test_zero_percent_completed_is_a_mismatch_but_unknown_percent_is_not():
    pt = _read(
        "| T-001 | A | 1 |  |  |  |\n| T-002 | A | 1 |  |  |  |\n| T-003 | A | 1 |  |  |  |\n",
        "| T-001 | A | 0% | Completata |  |  |  |\n| T-002 | A | — | Completata |  |  |  |\n"
        "| T-003 | A | 99% | Completata |  |  |  |\n",
    )
    assert [w.detail.split(":")[0] for w in _warns(pt, "status_progress_mismatch")] == ["T-001", "T-003"]
    by = _by_id(pt)
    assert (by["T-001"].progress, by["T-002"].progress) == (0, None)


def test_percent_rules_and_warning_details():
    pt = _read(
        "".join(f"| T-00{n} | A | 1 |  |  |  |\n" for n in range(1, 7)),
        "| T-001 | A | 45% | In corso |  |  |  |\n| T-002 | A | circa metà | In corso |  |  |  |\n"
        "| T-003 | A | — | In corso |  |  |  |\n| T-004 | A |  | In corso |  |  |  |\n"
        "| T-005 | A | 250 | In corso |  |  |  |\n| T-006 | A | 12,5% | In corso |  |  |  |\n",
    )
    by = _by_id(pt)
    # R26: un solo intero, con % facoltativo; "12,5%" non e' un intero e non si arrotonda in silenzio.
    assert [by[f"T-00{n}"].progress for n in range(1, 7)] == [45, None, None, None, 100, None]
    unreadable = _warns(pt, "progress_unreadable")
    assert [w.detail.split(":")[0] for w in unreadable] == ["T-002", "T-005", "T-006"]
    assert unreadable[1].detail == "T-005: 250 limitato a 100"
    assert unreadable[2].detail.startswith("T-006: 12,5%")
    assert {w.file for w in unreadable} == {"PROGRESS.md"}


def test_status_unknown_from_tasks_fallback_points_to_tasks_file():
    pt = _read(
        "| T-001 | A | 1 |  | Boh |  |\n| T-002 | A | 1 |  | In corso |  |\n",
        "| T-001 | A | 10% |  |  |  |  |\n| T-002 | A | 10% | Strano |  |  |  |\n",
    )
    by = _by_id(pt)
    assert (by["T-001"].status, by["T-001"].status_raw, by["T-001"].status_known) == ("Boh", "Boh", False)
    assert (by["T-002"].status, by["T-002"].status_raw) == ("Strano", "Strano")
    assert [(w.file, w.line, w.detail.split(":")[0]) for w in _warns(pt, "status_unknown")] == [
        ("TASKS.md", 3, "T-001"), ("PROGRESS.md", 4, "T-002"),
    ]


def test_status_unknown_also_for_task_without_progress_row_and_tasks_only_plan():
    pt = read_plan("p", TASKS_HEAD + "| T-001 | A | 1 |  | Boh |  |\n", None)
    (w,) = _warns(pt, "status_unknown")
    assert (w.file, w.line, w.detail.split(":")[0]) == ("TASKS.md", 3, "T-001")


def test_owner_placeholders_and_divergence_rules():
    pt = _read(
        "".join(f"| T-00{n} | {o} | 1 |  |  |  |\n" for n, o in
                [(1, "Alice"), (2, "Alice (BE)"), (3, "agent"), (4, "Alice"), (5, "—"), (6, "Alice")]),
        "| T-001 | alice | 10% |  |  |  |  |\n| T-002 | Alice - dev | 10% |  |  |  |  |\n"
        "| T-003 | Bruno | 10% |  |  |  |  |\n| T-004 | TBD | 10% |  |  |  |  |\n"
        "| T-005 | agent | 10% |  |  |  |  |\n| T-006 | Carla | 10% |  |  |  |  |\n",
    )
    by = _by_id(pt)
    assert [(by[f"T-00{n}"].owner.value, by[f"T-00{n}"].owner_source) for n in range(1, 7)] == [
        ("alice", "progress"), ("Alice - dev", "progress"), ("Bruno", "progress"),
        ("Alice", "tasks"), ("", ""), ("Carla", "progress"),
    ]
    assert by["T-005"].owner == Cell("", "")
    assert by["T-004"].owner_progress.raw == "TBD" and by["T-004"].owner_tasks.value == "Alice"
    assert [w.detail.split(":")[0] for w in _warns(pt, "owner_divergent")] == ["T-006"]


def test_branch_note_blocked_by_keep_tasks_value_when_progress_is_empty_or_dash():
    head = "| ID | Owner | Effort | Branch | Note | Bloccata da |\n|---|---|---|---|---|---|\n"
    pt = _read(
        "| T-001 | A | 1 | feature/t | nota t | T-002 |\n| T-002 | A | 1 | feature/u | nota u | T-001 |\n",
        "| T-001 | A | 10% | In corso | — |  | - |\n| T-002 | A | 10% | In corso | fb | T-003 | n2 |\n",
        tasks_head=head,
    )
    by = _by_id(pt)
    assert (by["T-001"].branch.value, by["T-001"].blocked_by.value, by["T-001"].note.value) == ("feature/t", "T-002", "nota t")
    assert (by["T-002"].branch.value, by["T-002"].blocked_by.value, by["T-002"].note.value) == ("fb", "T-003", "n2")


def test_progress_only_task_takes_its_row_fields_and_defaults_the_rest():
    pt = _read(
        "| T-001 | A | 1 |  |  |  |\n",
        "| T-001 | A | 10% | In corso |  |  |  |\n| T-MERGE-001 | Bruno | 20% | In corso | merge/x | T-001 | unione |\n",
    )
    m = _by_id(pt)["T-MERGE-001"]
    assert [t.id for t in pt.tasks] == ["T-001", "T-MERGE-001"]
    assert (m.in_tasks, m.in_progress, m.is_merge) == (False, True, True)
    assert (m.owner.value, m.owner_source, m.owner_tasks.value, m.owner_progress.value) == ("Bruno", "progress", "", "Bruno")
    assert (m.branch.value, m.blocked_by.value, m.note.value, m.progress) == ("merge/x", "T-001", "unione", 20)
    assert (m.effort.days, m.effort.note, m.dependencies, m.source_lines) == (None, "non dichiarato", (), (("PROGRESS.md", 4),))
    assert _warns(pt, "effort_unreadable") == []
    (w,) = _warns(pt, "progress_only_id")
    assert (w.file, w.line, w.detail.split(":")[0]) == ("PROGRESS.md", 4, "T-MERGE-001")


def test_progress_only_ids_are_not_flagged_when_tasks_has_no_task_table():
    question_tracker = "| ID | Stato |\n|---|---|\n| D-01 | Aperta |\n"
    for tasks in (None, "", question_tracker):
        pt = read_plan("p", tasks, PROGRESS_HEAD + "| T-001 | A | 10% | In corso |  |  |  |\n")
        (t,) = pt.tasks
        assert (t.in_tasks, t.in_progress) == (False, True), tasks
        assert _warns(pt, "progress_only_id") == [], tasks


def test_dependency_unknown_rules():
    pt = _read(
        "| T-001 | A | 1 | T-002, T-002, T-009 |  |  |\n| T-002 | A | 1 | other/T-777, T-003 |  |  |\n",
        "| T-003 | A | 10% | In corso |  |  |  |\n",
    )
    found = _warns(pt, "dependency_unknown")
    assert [w.detail for w in found] == ["T-001: T-009"]
    assert (found[0].file, found[0].line) == ("TASKS.md", 3)


def test_warning_order_is_tasks_then_progress_then_overlay():
    tasks = (
        "| ID | Owner | Effort | Dipendenze |\n|---|---|---|---|\n"
        "| T-001 | A | boh | T-050 |\n| T-001 | A | 1 |  |\n| T-002 | A | 1 |  |\n"
    )
    progress = (
        PROGRESS_HEAD + "| T-001 | B | 150% | Strano |  |  |  |\n| T-009 | A | 10% | In corso |  |  |  |\n"
        "| T-009 | A | 10% | In corso |  |  |  |\n"
    )
    pt = read_plan("p", tasks, progress)
    sequence = [(w.code, w.file) for w in pt.warnings]
    assert sequence[:3] == [
        ("effort_unreadable", "TASKS.md"), ("duplicate_id", "TASKS.md"), ("duplicate_id", "PROGRESS.md"),
    ]
    overlay = [code for code, _ in sequence[3:]]
    # T-001 (stato, avanzamento, owner, dipendenza), T-002 (riga mancante), T-009 (solo PROGRESS)
    assert overlay == [
        "status_unknown", "progress_unreadable", "owner_divergent", "dependency_unknown",
        "task_without_progress_row", "progress_only_id",
    ]


def test_source_lines_list_tasks_row_then_progress_row():
    pt = _read("| T-001 | A | 1 |  |  |  |\n| T-002 | A | 1 |  |  |  |\n", "| T-002 | A | 10% | In corso |  |  |  |\n")
    by = _by_id(pt)
    assert by["T-001"].source_lines == (("TASKS.md", 3),)
    assert by["T-002"].source_lines == (("TASKS.md", 4), ("PROGRESS.md", 3))


# ---------------------------------------------------------------------------
# R26: l'avanzamento si legge solo se resta un solo intero (con % facoltativo)
# ---------------------------------------------------------------------------

def _progress_of(cell):
    """Avanzamento e avvisi `progress_unreadable` per una cella del PROGRESS di T-001."""
    pt = _read("| T-001 | A | 1 |  |  |  |\n", f"| T-001 | A | {cell} | In corso |  |  |  |\n")
    return pt.tasks[0].progress, [w.detail for w in _warns(pt, "progress_unreadable")]


@pytest.mark.parametrize("cell,expected", [
    ("60%", 60), ("60", 60), ("60 %", 60), ("**60%**", 60), ("0%", 0), ("100", 100),
    ("~~30%~~ 60%", 60), ("30% → 60%", 60), ("30% -> 60%", 60), ("**30%** → **60%**", 60),
    ("T-004 60%", 60), ("~~`3/5`~~ 40%", 40),
])
def test_progress_cell_with_one_integer_is_read(cell, expected):
    assert _progress_of(cell) == (expected, [])


@pytest.mark.parametrize("cell", ["—", "-", "", "  "])
def test_empty_or_dash_progress_is_none_without_warning(cell):
    assert _progress_of(cell) == (None, [])


@pytest.mark.parametrize("cell", [
    "3/5", "In attesa di T-004", "12,5%", "30 60", "circa 60%", "~~30%~~", "60% e 70%", "QA-T-004", "T-004 → ",
])
def test_progress_cell_that_is_not_one_integer_is_none_with_warning(cell):
    progress, details = _progress_of(cell)
    assert progress is None
    (detail,) = details
    assert detail.startswith("T-001: " + cell.strip())


@pytest.mark.parametrize("cell,detail", [("120%", "T-001: 120% limitato a 100"), ("250", "T-001: 250 limitato a 100")])
def test_progress_over_100_is_clamped_with_warning(cell, detail):
    assert _progress_of(cell) == (100, [detail])
