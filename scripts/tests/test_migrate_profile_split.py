"""Test per migrate-profile-split.py."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "migrate-profile-split.py"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_profiles_repo(tmp_path: Path) -> Path:
    """Crea un finto deloitte-profiles con un progetto contenente sample_profile.json."""
    repo = tmp_path / "deloitte-profiles"
    project = repo / "test-project" / "constitution"
    project.mkdir(parents=True)
    shutil.copy(FIXTURES_DIR / "sample_profile.json", project / "profile.json")

    # Init come repo git (lo script richiede working tree pulito)
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial", "--quiet"], cwd=repo, check=True)
    return repo


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    """Esegue lo script di migrazione con i flag passati."""
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
    )


def files_in(directory: Path) -> set[str]:
    """Ritorna l'elenco esatto dei file in directory.
    Necessario su filesystem case-insensitive (Windows/macOS) dove Path.exists() è ambiguo
    tra 'profile.json' e 'PROFILE.json'."""
    import os
    return set(os.listdir(directory))


def test_dry_run_no_changes(temp_profiles_repo: Path) -> None:
    """Dry-run NON deve modificare nessun file."""
    result = run_script("--root", str(temp_profiles_repo))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    files = files_in(temp_profiles_repo / "test-project" / "constitution")
    assert "profile.json" in files
    assert "CONST.json" not in files
    assert "PROFILE.json" not in files
    assert "[DRY-RUN]" in result.stdout


def test_apply_creates_const_and_profile(temp_profiles_repo: Path) -> None:
    """--apply deve creare CONST.json e PROFILE.json e rimuovere profile.json."""
    result = run_script("--root", str(temp_profiles_repo), "--apply")
    assert result.returncode == 0, f"stderr: {result.stderr}"

    files = files_in(temp_profiles_repo / "test-project" / "constitution")
    assert "CONST.json" in files
    assert "PROFILE.json" in files
    assert "profile.json" not in files


def test_apply_matches_expected_const(temp_profiles_repo: Path) -> None:
    """CONST.json generato deve combaciare con expected_CONST.json."""
    run_script("--root", str(temp_profiles_repo), "--apply")

    generated = json.loads((temp_profiles_repo / "test-project" / "constitution" / "CONST.json").read_text())
    expected = json.loads((FIXTURES_DIR / "expected_CONST.json").read_text())
    assert generated == expected


def test_apply_matches_expected_profile(temp_profiles_repo: Path) -> None:
    """PROFILE.json generato deve combaciare con expected_PROFILE.json (= sample senza inviolable_principles)."""
    run_script("--root", str(temp_profiles_repo), "--apply")

    generated = json.loads((temp_profiles_repo / "test-project" / "constitution" / "PROFILE.json").read_text())
    expected = json.loads((FIXTURES_DIR / "expected_PROFILE.json").read_text())
    assert generated == expected


def test_idempotent_skip_already_migrated(temp_profiles_repo: Path) -> None:
    """Eseguire --apply due volte: la seconda deve essere no-op con messaggio di skip."""
    run_script("--root", str(temp_profiles_repo), "--apply")
    # Commit per pulire il working tree dopo il primo apply
    subprocess.run(["git", "add", "-A"], cwd=temp_profiles_repo, check=True)
    subprocess.run(["git", "commit", "-m", "first migration", "--quiet"], cwd=temp_profiles_repo, check=True)

    result = run_script("--root", str(temp_profiles_repo), "--apply")
    assert result.returncode == 0
    assert "skip" in result.stdout.lower() or "già migrato" in result.stdout.lower() or "already migrated" in result.stdout.lower()


def test_apply_refuses_dirty_working_tree(temp_profiles_repo: Path) -> None:
    """--apply deve rifiutare se ci sono modifiche unstaged."""
    # Sporca il working tree
    (temp_profiles_repo / "dirty.txt").write_text("dirty")
    result = run_script("--root", str(temp_profiles_repo), "--apply")
    assert result.returncode != 0
    assert "working tree" in result.stderr.lower() or "uncommitted" in result.stderr.lower() or "dirty" in result.stderr.lower()


def test_dry_run_allows_dirty_working_tree(temp_profiles_repo: Path) -> None:
    """--dry-run deve funzionare anche con working tree dirty (read-only)."""
    (temp_profiles_repo / "dirty.txt").write_text("dirty")
    result = run_script("--root", str(temp_profiles_repo))
    assert result.returncode == 0
