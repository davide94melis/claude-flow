from sdlc_plans.tables import scan_tables

HDR = "| ID | Owner | Effort |\n|---|---|---|\n"

def test_missing_trailing_pipe_keeps_row():
    s = scan_tables(HDR + "| T-001 | Alice | 1\n| T-002 | Bruno | 2 |\n")
    assert [r.cells for r in s.tables[0].rows] == [("T-001", "Alice", "1"), ("T-002", "Bruno", "2")]

def test_escaped_pipe_becomes_slash():
    assert scan_tables(HDR + "| T-001 | a\\|b | 1 |\n").tables[0].rows[0].cells[1] == "a/b"

def test_control_bytes_are_made_visible():
    assert scan_tables(HDR + "| T-001 | PK\x03\x04 | 1 |\n").tables[0].rows[0].cells[1] == "PK\\x03\\x04"

def test_crlf_and_bom_parse_like_lf():
    lf = scan_tables(HDR + "| T-001 | Alice | 1 |\n")
    crlf = scan_tables("\ufeff" + (HDR + "| T-001 | Alice | 1 |\n").replace("\n", "\r\n"))
    assert crlf.tables[0].rows[0].cells == lf.tables[0].rows[0].cells

def test_blank_line_inside_table_continues_with_warning():
    s = scan_tables(HDR + "| T-001 | Alice | 1 |\n\n| T-002 | Bruno | 2 |\n")
    assert len(s.tables) == 1 and len(s.tables[0].rows) == 2
    assert [w[0] for w in s.warnings] == ["table_continued_after_blank"]

def test_heading_closes_table_and_orphans_rows():
    s = scan_tables(HDR + "| T-001 | Alice | 1 |\n\n### Wave 1\n| T-009 | Carla | 3 |\n")
    assert len(s.tables[0].rows) == 1
    assert [r.cells[0] for r in s.orphan_rows] == ["T-009"] and s.orphan_rows[0].line == 6

def test_extra_cells_joined_into_last_with_warning():
    s = scan_tables(HDR + "| T-001 | Alice | `a | b` |\n")
    assert s.tables[0].rows[0].cells == ("T-001", "Alice", "`a | b`")
    assert s.warnings[0][0] == "column_count_mismatch"

def test_multiple_tables_with_line_numbers_and_fields():
    s = scan_tables("# x\n\n" + HDR + "| T-001 | A | 1 |\n\ntesto\n\n| Metrica | Valore |\n|:--|--:|\n| a | b |\n")
    assert [t.header_line for t in s.tables] == [3, 9]
    assert s.tables[0].fields == ("id", "owner", "effort") and s.tables[1].fields == (None, None)


# --- casi limite oltre al brief -------------------------------------------

def test_header_without_rows_is_an_empty_table():
    s = scan_tables(HDR)
    assert len(s.tables) == 1 and s.tables[0].rows == () and s.orphan_rows == ()

def test_table_at_end_of_file_without_newline_is_kept():
    s = scan_tables(HDR + "| T-001 | Alice | 1 |")
    assert [r.line for r in s.tables[0].rows] == [3]

def test_fewer_cells_are_padded_without_warning():
    s = scan_tables(HDR + "| T-001 | Alice |\n")
    assert s.tables[0].rows[0].cells == ("T-001", "Alice", "") and s.warnings == ()

def test_separator_under_a_body_row_starts_a_new_table_with_warning():
    # R8 per una riga il cui primo valore non e' un ID di task (per gli ID vale R28c, sotto).
    s = scan_tables(HDR + "| x | A | 1 |\n|---|---|---|\n| T-002 | B | 2 |\n")
    assert [t.header_line for t in s.tables] == [1, 3]
    assert s.tables[0].rows == ()
    assert s.tables[1].headers == ("x", "A", "1")
    assert [r.cells[0] for r in s.tables[1].rows] == ["T-002"]
    assert [w[:2] for w in s.warnings] == [("table_header_inside_table", 3)]

def test_row_with_a_task_id_first_never_starts_a_table_even_above_a_separator_line():
    # R28c: una riga `| - | - | - |` tra due task e' una riga del corpo, non un separatore.
    s = scan_tables(HDR + "| T-001 | A | 1 |\n| T-002 | B | 2 |\n| - | - | - |\n| T-003 | C | 3 |\n")
    assert len(s.tables) == 1 and s.tables[0].header_line == 1
    assert [r.cells[0] for r in s.tables[0].rows] == ["T-001", "T-002", "-", "T-003"]
    assert s.warnings == () and s.orphan_rows == ()

def test_task_id_first_cell_is_recognised_with_markup_and_prefix():
    for first in ("`T-002`", "**T-002**", "QA-T-002"):
        s = scan_tables(HDR + f"| T-001 | A | 1 |\n| {first} | B | 2 |\n|---|---|---|\n| T-003 | C | 3 |\n")
        assert len(s.tables) == 1, first
        assert [r.cells[0] for r in s.tables[0].rows][-1] == "T-003", first

def test_struck_or_combined_task_id_first_never_starts_a_table_either():
    # Stessa regola per un ID barrato o combinato: la riga sotto, di soli trattini, non perde i task dopo.
    for first in ("~~T-002~~", "~~`T-002`~~", "`T-002+T-003`", "[T-002](x)", "T-002 (bis)"):
        s = scan_tables(HDR + f"| T-001 | A | 1 |\n| {first} | B | 2 |\n| - | - | - |\n| T-004 | C | 3 |\n")
        assert len(s.tables) == 1 and s.warnings == (), first
        assert [r.cells[0] for r in s.tables[0].rows][-1] == "T-004", first

def test_separator_under_a_non_id_row_still_starts_a_table():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n| ID | Effort | Owner |\n|---|---|---|\n| T-002 | 5 | B |\n")
    assert [t.header_line for t in s.tables] == [1, 4]

def test_glued_header_and_separator_under_open_table_start_a_new_table():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n| ID | Effort | Owner |\n|---|---|---|\n| T-002 | 5 | Bruno |\n")
    assert [t.header_line for t in s.tables] == [1, 4]
    assert [r.cells for r in s.tables[0].rows] == [("T-001", "A", "1")]
    assert s.tables[1].fields == ("id", "effort", "owner")
    assert [r.cells for r in s.tables[1].rows] == [("T-002", "5", "Bruno")]
    assert [w[:2] for w in s.warnings] == [("table_header_inside_table", 4)]
    assert s.orphan_rows == ()

def test_new_table_after_blank_line_needs_no_warning():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n\n| ID | Effort | Owner |\n|---|---|---|\n| T-002 | 5 | Bruno |\n")
    assert [t.header_line for t in s.tables] == [1, 5] and s.warnings == ()

def test_every_row_has_at_least_one_cell():
    s = scan_tables("|\n\n" + HDR + "|\n")
    assert s.orphan_rows[0].cells == ("",)
    assert s.tables[0].rows[0].cells == ("", "", "")

def test_very_long_row_with_many_pipes_in_inline_code_is_read():
    code = "`" + "|".join(["abcd"] * 1000) + "`"  # ~5.000 caratteri, 999 `|` non protetti
    assert len(code) > 5000 - 10
    s = scan_tables(HDR + "| T-001 | Alice | " + code + " |\n")
    row = s.tables[0].rows[0]
    assert len(row.cells) == len(s.tables[0].headers) == 3
    assert row.cells[:2] == ("T-001", "Alice")
    assert row.cells[2] == "`" + " | ".join(["abcd"] * 1000) + "`"
    assert [w[:2] for w in s.warnings] == [("column_count_mismatch", 3)]

def test_blank_then_row_with_other_width_closes_table_as_orphan():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n\n| x | y |\n| z | w |\n")
    assert len(s.tables[0].rows) == 1 and s.warnings == ()
    assert [(r.line, r.cells) for r in s.orphan_rows] == [(5, ("x", "y")), (6, ("z", "w"))]

def test_blank_then_new_header_starts_a_second_table():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n\n| H1 | H2 |\n|--|--|\n| a | b |\n")
    assert [t.header_line for t in s.tables] == [1, 5] and s.warnings == ()

def test_text_line_closes_table_and_later_rows_are_orphans():
    s = scan_tables(HDR + "| T-001 | A | 1 |\ntesto\n| T-002 | B | 2 |\n")
    assert len(s.tables[0].rows) == 1 and [r.line for r in s.orphan_rows] == [5]

def test_escaped_pipe_at_end_of_line_does_not_close_the_cell():
    assert scan_tables(HDR + "| T-001 | A | b\\|\n").tables[0].rows[0].cells == ("T-001", "A", "b/")

def test_line_numbers_are_physical_with_crlf_and_bom():
    text = "\ufeff" + (HDR + "| T-001 | A | 1 |\n\n| T-002 | B | 2 |\n").replace("\n", "\r\n")
    s = scan_tables(text)
    assert [r.line for r in s.tables[0].rows] == [3, 5]
    assert s.warnings[0][:2] == ("table_continued_after_blank", 5)

def test_mismatch_warning_carries_the_row_line():
    s = scan_tables(HDR + "| T-001 | A | 1 |\n| T-002 | B | 2 | extra |\n")
    assert [w[:2] for w in s.warnings] == [("column_count_mismatch", 4)]

def test_empty_text_has_no_tables():
    s = scan_tables("")
    assert s.tables == () and s.orphan_rows == () and s.warnings == ()

def test_scan_tables_is_exported_by_the_package():
    import sdlc_plans
    assert sdlc_plans.scan_tables is scan_tables
    assert {"scan_tables", "Row", "Table", "TableScan"} <= set(sdlc_plans.__all__)
