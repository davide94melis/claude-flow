from sdlc_plans.discovery import discover_plans, walk_repo

W = "plans/in-progress/2026-07-29_wave-x"
NESTED = [f"{W}/ESTIMATE.md", f"{W}/sub-a/TASKS.md", f"{W}/sub-a/PROGRESS.md", f"{W}/sub-a/TASKS.en.md",
          f"{W}/sub-c/PROGRESS.md", f"{W}/_artifacts/merge-release/INTEGRATION.md", "CHANGELOG.md"]

def test_nested_subplans_are_plans_with_wave():
    plans = discover_plans(NESTED)
    assert [(p.name, p.state, p.wave) for p in plans] == [
        ("sub-a", "in-progress", "2026-07-29_wave-x"), ("sub-c", "in-progress", "2026-07-29_wave-x")]
    assert plans[0].path == f"{W}/sub-a"
    assert plans[0].files == ("PROGRESS.md", "TASKS.en.md", "TASKS.md")

def test_flat_plan_has_no_wave():
    (p,) = discover_plans(["plans/todo/2026-10-05_alpha/TASKS.md"])
    assert (p.state, p.wave, p.name) == ("todo", None, "2026-10-05_alpha")

def test_legacy_profile_layout():
    (p,) = discover_plans(["acme/plans/done/2026-05-01_beta/TASKS.md"])
    assert (p.path, p.state) == ("acme/plans/done/2026-05-01_beta", "done")

def test_en_mirror_alone_is_not_a_plan():
    assert discover_plans(["plans/todo/x/TASKS.en.md"]) == []

def test_draft_state_is_kept():
    assert discover_plans(["plans/draft/2026-10-20_gamma/TASKS.md"])[0].state == "draft"

def test_walk_repo_skips_git_dir(tmp_path):
    (tmp_path / ".git").mkdir(); (tmp_path / ".git" / "HEAD").write_text("x")
    (tmp_path / "plans/todo/a").mkdir(parents=True); (tmp_path / "plans/todo/a/TASKS.md").write_text("x")
    assert walk_repo(tmp_path) == ["plans/todo/a/TASKS.md"]


# --- casi limite aggiunti in fase di revisione ---

def test_marker_directly_under_state_is_not_a_plan():
    assert discover_plans(["plans/todo/TASKS.md", "plans/todo/PROGRESS.md"]) == []

def test_empty_input_and_non_plan_paths():
    assert discover_plans([]) == []
    assert discover_plans(["README.md", "docs/TASKS.md", "plans"]) == []

def test_duplicate_paths_do_not_duplicate_files_or_plans():
    paths = ["plans/todo/a/TASKS.md"] * 3 + ["plans/todo/a/ESTIMATE.md"]
    (p,) = discover_plans(paths)
    assert p.files == ("ESTIMATE.md", "TASKS.md")

def test_plan_nested_under_another_plan_is_its_own_plan():
    plans = discover_plans(["plans/todo/a/TASKS.md", "plans/todo/a/sub/PROGRESS.md"])
    assert [(p.path, p.wave, p.name, p.files) for p in plans] == [
        ("plans/todo/a", None, "a", ("TASKS.md",)),
        ("plans/todo/a/sub", "a", "sub", ("PROGRESS.md",)),
    ]

def test_first_plans_segment_wins():
    (p,) = discover_plans(["plans/done/plans/x/TASKS.md"])
    assert (p.state, p.wave, p.name) == ("done", "plans", "x")

def test_separators_are_normalized_to_slash():
    (p,) = discover_plans([r".\plans\todo\a\TASKS.md", "plans/todo/a/ESTIMATE.md"])
    assert (p.path, p.files) == ("plans/todo/a", ("ESTIMATE.md", "TASKS.md"))

def test_directory_entries_are_skipped():
    assert discover_plans(["plans/todo/a/"]) == []

def test_result_is_sorted_by_path():
    plans = discover_plans(["plans/todo/b/TASKS.md", "plans/done/z/TASKS.md", "plans/todo/a/PROGRESS.md"])
    assert [p.path for p in plans] == ["plans/done/z", "plans/todo/a", "plans/todo/b"]

def test_walk_repo_is_sorted_posix_and_relative(tmp_path):
    (tmp_path / "b").mkdir(); (tmp_path / "b" / "z.md").write_text("x")
    (tmp_path / "a" / "deep").mkdir(parents=True); (tmp_path / "a" / "deep" / "y.md").write_text("x")
    (tmp_path / "a.md").write_text("x")
    assert walk_repo(tmp_path) == ["a.md", "a/deep/y.md", "b/z.md"]
