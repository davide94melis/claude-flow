"""R28: nessuna riga con ID di task si perde in silenzio (testi sintetici).

Prefissi dell'ID (`QA-T-001`), celle ID non valide o barrate, righe `| - | - |` tra
i task, tabelle di stato nel PROGRESS.md e file senza tabella di task.
"""
from sdlc_plans.tasks import read_plan

HEAD = "| ID | Owner | Effort |\n|---|---|---|\n"
TASKS_HEAD = "| ID | Owner | Effort | Dipendenze | Stato | Branch |\n|---|---|---|---|---|---|\n"
PROGRESS_HEAD = "| ID | Owner | Progresso | Stato | Branch | Bloccata da | Note |\n|---|---|---|---|---|---|---|\n"
STATE_ONLY_HEAD = "| ID | Stato | Branch | Dipendenze | Note |\n|---|---|---|---|---|\n"


def _codes_of(warnings, code):
    return [w for w in warnings if w.code == code]


# --- (a) prefisso dell'ID ----------------------------------------------------

def test_prefixed_ids_are_read_and_stay_distinct_from_unprefixed():
    text = HEAD + "| `QA-T-001` | A | 1 |\n| QA-T-002 | B | 2 |\n| T-001 | C | 3 |\n| qa2-T-004 | D | 4 |\n"
    pt = read_plan("p", text, None)
    assert [t.id for t in pt.tasks] == ["QA-T-001", "QA-T-002", "T-001", "QA2-T-004"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded, pt.warnings) == (4, 4, False, ())


def test_merge_flag_looks_at_the_t_part_of_a_prefixed_id():
    text = HEAD + "| QA-T-MERGE-1 | A | 1 |\n| QA-T-001 | A | 1 |\n| T-MERGE-2 | A | 1 |\n| T-001 | A | 1 |\n"
    assert {t.id: t.is_merge for t in read_plan("p", text, None).tasks} == {
        "QA-T-MERGE-1": True, "QA-T-001": False, "T-MERGE-2": True, "T-001": False,
    }


def test_dependencies_read_prefixed_ids_whole_and_ignore_words_ending_in_t():
    head = "| ID | Owner | Effort | Dipendenze |\n|---|---|---|---|\n"
    text = head + "| T-001 | A | 1 | QA-T-002, XT-005, ext/QA-T-002, ext/T-010, T-003/T-004 |\n| QA-T-002 | A | 1 |  |\n"
    first, _ = read_plan("p", text, None).tasks
    assert first.dependencies == ("QA-T-002", "ext/QA-T-002", "ext/T-010", "T-003/T-004")


def test_prefixed_dependency_is_checked_against_the_plan_ids():
    head = "| ID | Owner | Effort | Dipendenze |\n|---|---|---|---|\n"
    text = head + "| T-001 | A | 1 | QA-T-002, QA-T-009 |\n| QA-T-002 | A | 1 |  |\n"
    unknown = _codes_of(read_plan("p", text, None).warnings, "dependency_unknown")
    assert [w.detail for w in unknown] == ["T-001: QA-T-009"]


def test_tasks_and_progress_with_prefixed_ids_overlay_into_one_task():
    pt = read_plan(
        "p",
        TASKS_HEAD + "| `QA-T-001` | A | 1 |  |  |  |\n",
        PROGRESS_HEAD + "| QA-T-001 | A | 40% | In corso |  |  |  |\n",
    )
    (t,) = pt.tasks
    assert (t.id, t.in_tasks, t.in_progress, t.progress, t.status) == ("QA-T-001", True, True, 40, "In corso")
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (2, 2, False)
    assert not _codes_of(pt.warnings, "progress_only_id")


# --- (b) celle ID non valide o barrate ----------------------------------------

def test_id_cell_with_a_task_id_token_but_not_a_valid_id_is_dropped_with_warning():
    text = (HEAD + "| T-001 | A | 1 |\n| `T-001+T-002` | A | 1 |\n| T-002 (bis) | A | 1 |\n"
            "| [T-007](x) | A | 1 |\n| TOTALE |  | 2 |\n| ext/T-010 | A | 1 |\n")
    pt = read_plan("p", text, None)
    assert [t.id for t in pt.tasks] == ["T-001"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (5, 1, True)
    dropped = _codes_of(pt.warnings, "row_dropped")
    assert [(w.file, w.line, w.detail.split(":")[0]) for w in dropped] == [
        ("TASKS.md", 4, "T-001+T-002"), ("TASKS.md", 5, "T-002 (bis)"),
        ("TASKS.md", 6, "[T-007](x)"), ("TASKS.md", 8, "ext/T-010"),
    ]


def test_wholly_struck_id_is_informational_and_not_counted():
    text = HEAD + "| T-001 | A | 1 |\n| ~~T-004~~ | A | 1 |\n| ~~`T-005`~~ | A | 1 |\n| `~~T-006~~` | A | 1 |\n"
    pt = read_plan("p", text, None)
    assert [t.id for t in pt.tasks] == ["T-001"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (1, 1, False)
    struck = _codes_of(pt.warnings, "row_struck")
    assert [(w.file, w.line, w.detail.split(":")[0]) for w in struck] == [
        ("TASKS.md", 4, "~~T-004~~"), ("TASKS.md", 5, "~~T-005~~"), ("TASKS.md", 6, "~~T-006~~"),
    ]
    assert not _codes_of(pt.warnings, "row_dropped")


def test_partly_struck_id_is_not_wholly_struck():
    pt = read_plan("p", HEAD + "| ~~T-004~~ T-005 | A | 1 |\n", None)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (1, 0, True)
    assert _codes_of(pt.warnings, "row_struck") == []
    assert len(_codes_of(pt.warnings, "row_dropped")) == 1


# --- (c) riga di soli trattini tra due task -----------------------------------

def test_dash_line_between_task_rows_is_a_body_row_and_every_task_is_read():
    text = HEAD + "| T-001 | A | 1 |\n| T-002 | B | 2 |\n| - | - | - |\n| T-003 | C | 3 |\n"
    pt = read_plan("p", text, None)
    assert [t.id for t in pt.tasks] == ["T-001", "T-002", "T-003"]
    assert (pt.rows_seen, pt.rows_read, pt.degraded, pt.warnings) == (3, 3, False, ())


# --- (d) PROGRESS.md con sola tabella di stato --------------------------------

def test_progress_table_with_only_id_and_status_is_read_as_task_table():
    progress = STATE_ONLY_HEAD + "| T-001 | Completata | feature/a | - | ok |\n| QA-T-002 | In corso | feature/b | T-001 |  |\n"
    tasks = HEAD + "| T-001 | A | 1 |\n| QA-T-002 | B | 2 |\n"
    pt = read_plan("p", tasks, progress)
    by = {t.id: t for t in pt.tasks}
    assert (by["T-001"].status, by["T-001"].branch.value, by["T-001"].note.value) == ("Completata", "feature/a", "ok")
    assert (by["QA-T-002"].status, by["QA-T-002"].in_progress) == ("In corso", True)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (4, 4, False)
    assert not _codes_of(pt.warnings, "table_not_recognized")


def test_progress_table_with_id_and_progress_column_is_read_too():
    progress = "| ID | Progresso |\n|---|---|\n| T-001 | 40% |\n"
    (t,) = read_plan("p", HEAD + "| T-001 | A | 1 |\n", progress).tasks
    assert (t.progress, t.in_progress) == (40, True)


def test_progress_status_fallback_is_not_used_when_a_standard_table_exists():
    progress = (
        "| ID | Owner | Progresso | Stato |\n|---|---|---|---|\n| T-001 | A | 10% | In corso |\n\n"
        "## Storico\n| ID | Stato | Note |\n|---|---|---|\n| T-001 | Completata | vecchio |\n| T-009 | Sospesa | x |\n"
    )
    pt = read_plan("p", HEAD + "| T-001 | A | 1 |\n", progress)
    (t,) = pt.tasks
    assert (t.status, t.progress, t.note.value) == ("In corso", 10, "")
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (2, 2, False)
    (w,) = _codes_of(pt.warnings, "table_not_recognized")
    assert w.file == "PROGRESS.md" and "2 ID di task" in w.detail


def test_status_fallback_is_for_progress_md_only():
    pt = read_plan("p", "| ID | Stato |\n|---|---|\n| T-001 | Completata |\n", None)
    assert (pt.tasks, pt.degraded) == ((), True)


# --- (e) file senza tabella di task --------------------------------------------

def test_file_without_task_table_degrades_for_ids_in_id_column_but_not_for_other_ids():
    text = "| Voce | ID |\n|---|---|\n| T-001 | D-01 |\n\n| ID | Note |\n|---|---|\n| QA-T-002 | x |\n| D-02 | y |\n"
    pt = read_plan("p", text, None)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (1, 0, True)
    (w,) = _codes_of(pt.warnings, "row_dropped")
    assert (w.line, w.detail.split(":")[0]) == (7, "QA-T-002")


def test_side_tables_stay_informational_when_the_file_has_a_task_table():
    text = HEAD + "| T-001 | A | 1 |\n\n| ID | Dipendenze |\n|---|---|\n| T-001 | T-002 |\n"
    pt = read_plan("p", text, None)
    assert (pt.rows_seen, pt.rows_read, pt.degraded) == (1, 1, False)
    assert [w.code for w in pt.warnings] == ["table_not_recognized"]
