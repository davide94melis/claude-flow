from sdlc_plans.tasks import read_plan, read_task_rows

SUBA = "plans/in-progress/2026-07-29_wave-x/sub-a"

def _txt(plans_fixtures, rel):
    return (plans_fixtures / rel).read_text(encoding="utf-8")

def test_flat_tasks_all_rows(plans_fixtures):
    p = "plans/in-progress/2026-09-01_alpha"
    pt = read_plan(p, _txt(plans_fixtures, f"flat/{p}/TASKS.md"), None)
    assert [t.id for t in pt.tasks] == ["T-001", "T-002", "T-003", "T-004", "T-005", "T-MERGE-003"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (6, 6, False)
    t4 = pt.tasks[3]
    assert t4.effort.days == 1.5 and t4.dependencies == ("T-003",) and t4.activity.value == "Filtri"
    assert pt.tasks[-1].is_merge

def test_variants_in_nested_subplan(plans_fixtures):
    pt = read_plan(SUBA, _txt(plans_fixtures, f"nested/{SUBA}/TASKS.md"), None)
    by = {t.id: t for t in pt.tasks}
    assert list(by) == ["T-001", "T-002", "T-003", "T-004", "T-051-FIX", "T-010", "T-011"]
    assert [by[i].effort.days for i in by] == [1.5, 0.0, 7.0, None, 1.5, 2.0, None]
    assert by["T-002"].description.value == "Import da file a/b"
    assert by["T-001"].priority.value == "P0" and by["T-010"].priority.value == "P1"
    assert by["T-010"].area.value == "BE" and by["T-010"].activity.value == "Notifiche"
    assert by["T-051-FIX"].dependencies == ("T-002", "crb/T-010")
    assert by["T-001"].dependencies == ()
    assert (pt.rows_seen, pt.rows_read) == (7, 7)

def test_question_tracker_is_not_a_task_table(plans_fixtures):
    pt = read_plan(SUBA, _txt(plans_fixtures, f"nested/{SUBA}/TASKS.md"), None)
    assert not any(t.id.startswith("D-") for t in pt.tasks)

def test_effort_warnings_only_for_unreadable(plans_fixtures):
    pt = read_plan(SUBA, _txt(plans_fixtures, f"nested/{SUBA}/TASKS.md"), None)
    unreadable = [w for w in pt.warnings if w.code == "effort_unreadable"]
    assert [w.detail.split(":")[0] for w in unreadable] == ["T-011"]

def test_orphan_task_row_marks_degraded():
    text = "| ID | Owner | Effort |\n|---|---|---|\n| T-001 | A | 1 |\n| T-002 | B | 1 |\n\n### Wave 2\n| T-003 | C | 1 |\n"
    pt = read_plan("p", text, None)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (3, 2, True)
    (w,) = [w for w in pt.warnings if w.code == "row_dropped"]
    assert (w.file, w.line) == ("TASKS.md", 7)

def test_empty_or_missing_texts():
    for tasks, progress in [(None, None), ("", ""), ("# solo titolo\n", None)]:
        pt = read_plan("p", tasks, progress)
        assert pt.tasks == () and not pt.degraded

HEAD = "| ID | Owner | Effort |\n|---|---|---|\n"

def test_duplicate_id_first_row_wins_and_counts_as_read():
    text = HEAD + "| T-001 | A | 1 |\n\n## Bis\n" + HEAD + "| **T-001** | B | 2 |\n| T-002 | B | 2 |\n"
    pt = read_plan("p", text, None)
    assert [(t.id, t.owner.value, t.effort.days) for t in pt.tasks] == [("T-001", "A", 1.0), ("T-002", "B", 2.0)]
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (3, 3, False)
    (w,) = [w for w in pt.warnings if w.code == "duplicate_id"]
    assert (w.file, w.line, w.detail.split(":")[0]) == ("TASKS.md", 8, "T-001")

def test_id_column_need_not_be_first():
    text = "| Owner | ID | Effort |\n|---|---|---|\n| Alice | `T-007` | 2 gg |\n"
    (t,) = read_plan("p", text, None).tasks
    assert (t.id, t.owner.value, t.effort.days, t.source_lines) == ("T-007", "Alice", 2.0, (("TASKS.md", 3),))

def test_file_with_only_non_task_tables_is_empty_and_not_degraded():
    text = "| ID | Stato |\n|---|---|\n| D-01 | Aperta |\n\n| Step | Source |\n|---|---|\n| 1 | a |\n"
    pt = read_plan("p", text, None)
    assert (pt.tasks, pt.rows_seen, pt.rows_read, pt.degraded, pt.warnings) == ((), 0, 0, False, ())

def test_empty_cells_and_placeholders_are_empty_not_zero():
    text = HEAD + "| T-001 |  |  |\n| T-002 | — | — |\n| T-003 | agent | (in T-001) |\n"
    tasks = read_plan("p", text, None).tasks
    assert [t.id for t in tasks] == ["T-001", "T-002", "T-003"]
    for t in tasks:
        assert (t.owner.value, t.owner_source, t.effort.days, t.effort.note) == ("", "", None, "non dichiarato")
        assert t.owner_tasks.raw in ("", "—", "agent") and t.owner_progress.value == ""

def test_table_warnings_kept_only_inside_task_tables():
    text = HEAD + "| T-001 | A | 1 | extra |\n\n| ID | Stato |\n|---|---|\n| D-01 | Aperta | extra |\n"
    pt = read_plan("p", text, None)
    (w,) = pt.warnings
    assert (w.code, w.file, w.line) == ("column_count_mismatch", "TASKS.md", 3)
    assert w.detail.startswith("T-001: ")

def test_defaults_without_progress_and_status_column_fallback():
    text = "| ID | Owner | Stato | Effort |\n|---|---|---|---|\n| T-001 | A | In corso | 1 |\n| T-002 | B |  | 1 |\n"
    a, b = read_plan("p", text, None).tasks
    assert (a.status, a.status_raw, a.status_known) == ("In corso", "In corso", True)
    assert (b.status, b.status_raw, b.status_known) == ("Da iniziare", "", True)
    assert (a.progress, a.in_tasks, a.in_progress, a.is_merge) == (None, True, False, False)

def _codes_of(warnings, code):
    return [w for w in warnings if w.code == code]

def test_id_shaped_but_invalid_row_in_task_table_is_dropped_with_warning():
    text = HEAD + "| T-001 | A | 1 |\n| t-002 | B | 1 |\n| **t-003** | B | 1 |\n| TOTALE |  | 2 |\n| Q-01 |  |  |\n"
    pt = read_plan("p", text, None)
    assert [t.id for t in pt.tasks] == ["T-001"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (3, 1, True)
    dropped = _codes_of(pt.warnings, "row_dropped")
    assert [(w.file, w.line, w.detail.split(":")[0]) for w in dropped] == [("TASKS.md", 4, "t-002"), ("TASKS.md", 5, "t-003")]

def test_unrecognized_table_without_id_header_warns_once_and_is_not_degraded():
    text = "| Task | Chi | Giorni |\n|---|---|---|\n| T-001 | A | 1 |\n| T-002 | B | 2 |\n"
    pt = read_plan("p", text, None)
    assert (pt.tasks, pt.rows_seen, pt.rows_read, pt.degraded) == ((), 0, 0, False)
    (w,) = pt.warnings
    assert (w.code, w.file, w.line) == ("table_not_recognized", "TASKS.md", 1)
    assert "Task | Chi | Giorni" in w.detail and "2 ID di task" in w.detail

def test_unrecognized_table_with_id_column_but_no_owner_or_effort_warns():
    text = "| ID | Stato |\n|---|---|\n| T-001 | Aperta |\n"
    pt = read_plan("p", text, None)
    assert (pt.tasks, pt.rows_seen, pt.rows_read, pt.degraded) == ((), 0, 0, False)
    (w,) = pt.warnings
    assert (w.code, w.line) == ("table_not_recognized", 1) and "1 ID di task" in w.detail

def test_unrecognized_table_uses_id_column_when_present_else_first_column():
    only_first_has_ids = "| Chi | ID |\n|---|---|\n| T-001 | D-01 |\n"
    assert read_plan("p", only_first_has_ids, None).warnings == ()
    two_tables = (
        HEAD + "| T-001 | A | 1 |\n\n| ID | Dipendenze |\n|---|---|\n| T-001 | T-002 |\n\n"
        "| Voce | Valore |\n|---|---|\n| T-009 | x |\n"
    )
    warnings = _codes_of(read_plan("p", two_tables, None).warnings, "table_not_recognized")
    assert [w.line for w in warnings] == [5, 9]

def test_question_tracker_and_summary_tables_do_not_trigger_table_not_recognized(plans_fixtures):
    tracker = _txt(plans_fixtures, f"nested/{SUBA}/TASKS.md")
    assert not _codes_of(read_task_rows("p", "TASKS.md", tracker).warnings, "table_not_recognized")
    summary = _txt(plans_fixtures, f"nested/{SUBA}/PROGRESS.md")
    assert not _codes_of(read_task_rows("p", "PROGRESS.md", summary).warnings, "table_not_recognized")

def test_fixture_files_produce_no_table_not_recognized(plans_fixtures):
    tasks_files = [
        "flat/plans/in-progress/2026-09-01_alpha/TASKS.md",
        f"nested/{SUBA}/TASKS.md",
        "nested/plans/in-progress/2026-07-29_wave-x/sub-b/TASKS.md",
    ]
    for rel in tasks_files:
        pt = read_plan("p", _txt(plans_fixtures, rel), None)
        assert pt.tasks and not _codes_of(pt.warnings, "table_not_recognized"), rel
    for path in plans_fixtures.rglob("PROGRESS.md"):
        text = path.read_text(encoding="utf-8")
        assert not _codes_of(read_task_rows("p", "PROGRESS.md", text).warnings, "table_not_recognized"), path
