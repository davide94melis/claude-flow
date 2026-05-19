#!/usr/bin/env python3
"""
migrate-profile-split.py

Splitta deloitte-profiles/<progetto>/constitution/profile.json in:
  - CONST.json (principi/standard di archetipo)
  - PROFILE.json (dettagli specifici progetto, rinominato da profile.json)

Default: dry-run. Usa --apply per applicare le modifiche.

Idempotente: skip dei progetti già migrati (CONST.json + PROFILE.json esistono, profile.json assente).
Safety: rifiuta di applicare se il working tree git di <profiles_repo> ha modifiche unstaged.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path("C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles")
TEMPLATE_PATH = Path(__file__).parent.parent / "skills" / "sdlc-profile-setup" / "_const-template.json"

DEFAULT_PRINCIPLE_SCOPES = {
    "security": {
        "scope": "ogni endpoint, input utente, query, gestione dati sensibili",
        "verification": "verifica obbligatoria prima del merge",
    },
    "accessibility": {
        "requirements": [
            "navigabile da tastiera",
            "compatibile screen reader",
            "contrasto AA",
            "attributi ARIA corretti",
        ],
    },
    "responsiveness": {
        "breakpoints": ["mobile", "tablet", "desktop"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split profile.json into CONST.json + PROFILE.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default: dry-run.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"Path to deloitte-profiles repo. Default: {DEFAULT_ROOT}")
    return parser.parse_args()


def load_template() -> dict:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"ERROR: template not found at {TEMPLATE_PATH}")
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def is_dirty(repo: Path) -> bool:
    """True se il working tree git ha modifiche unstaged o file untracked.

    Raise SystemExit se git non è installato o la directory non è un repo git
    (in tal caso il safety gate '--apply rifiuta dirty tree' sarebbe silenziosamente
    bypassato, perché git fallirebbe con stdout vuoto).
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        raise SystemExit(f"ERROR: git not found in PATH. Install git to use this script.") from e
    if result.returncode != 0:
        raise SystemExit(
            f"ERROR: 'git status' failed in {repo} (exit {result.returncode}). "
            f"Is this a git repository? stderr: {result.stderr.strip()}"
        )
    return bool(result.stdout.strip())


def find_legacy_profiles(root: Path) -> list[Path]:
    """Trova tutti i <progetto>/constitution/profile.json."""
    return sorted(root.glob("*/constitution/profile.json"))


def is_already_migrated(constitution_dir: Path) -> bool:
    """True se CONST.json + PROFILE.json esistono e profile.json no."""
    import os
    files = set(os.listdir(constitution_dir))
    return (
        "profile.json" not in files
        and "CONST.json" in files
        and "PROFILE.json" in files
    )


def wrap_principle(name: str, value) -> dict:
    """Trasforma una stringa di principio nello shape oggetto del nuovo schema."""
    if isinstance(value, dict):
        # Già nel formato nuovo? Restituisci com'è.
        return value
    wrapped = {"rule": value}
    wrapped.update(DEFAULT_PRINCIPLE_SCOPES.get(name, {}))
    return wrapped


def build_const(legacy_principles: dict, template: dict) -> dict:
    """Costruisce CONST.json combinando i principi legacy con il template di default."""
    const = json.loads(json.dumps(template))  # deep copy

    # Sovrascrivi i principi del template con quelli legacy (preservando le stringhe originali in `rule`)
    for name in ("security", "accessibility", "responsiveness", "data_privacy"):
        if name in legacy_principles:
            const["inviolable_principles"][name] = wrap_principle(name, legacy_principles[name])
        # Se il principio non era nel legacy ma è nel template, resta com'è nel template.

    return const


def strip_inviolable_principles(profile: dict) -> dict:
    """Rimuove conventions.inviolable_principles dal profilo. Restituisce copia."""
    new_profile = json.loads(json.dumps(profile))  # deep copy
    if "conventions" in new_profile and "inviolable_principles" in new_profile["conventions"]:
        del new_profile["conventions"]["inviolable_principles"]
    return new_profile


def migrate_one(profile_path: Path, template: dict, apply: bool, prefix: str) -> tuple[bool, list[str]]:
    """Migra un singolo profile.json. Restituisce (migrato, log_lines)."""
    log: list[str] = []
    constitution = profile_path.parent
    rel = profile_path.relative_to(profile_path.parent.parent.parent)
    log.append(f"{prefix} {rel.parent}/")

    if is_already_migrated(constitution):
        log.append(f"{prefix}   skip (già migrato: CONST.json + PROFILE.json presenti)")
        return False, log

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    legacy_principles = profile.get("conventions", {}).get("inviolable_principles", {})
    n_principles = len(legacy_principles)

    log.append(f"  read  profile.json ({profile_path.stat().st_size} bytes)")
    if n_principles:
        names = ", ".join(legacy_principles.keys())
        log.append(f"  extract conventions.inviolable_principles → CONST.inviolable_principles ({n_principles} principi: {names})")
    else:
        log.append(f"  no conventions.inviolable_principles nel profilo legacy")
    log.append(f"  add default sections from template (quality_standards, code_style, git_workflow, architectural_patterns, data_privacy)")

    const_json = build_const(legacy_principles, template)
    new_profile = strip_inviolable_principles(profile)

    log.append(f"  write CONST.json")
    log.append(f"  remove conventions.inviolable_principles from profile.json")
    log.append(f"  git mv profile.json PROFILE.json")

    if apply:
        (constitution / "CONST.json").write_text(json.dumps(const_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        # Rinomina profile.json → PROFILE.json via git mv (preserva la storia).
        # Su filesystem case-insensitive (Windows NTFS, macOS default) il rename case-only
        # va fatto in due passi, altrimenti git rifiuta con "fatal: bad source".
        repo_root = constitution.parent.parent
        src_rel = str(profile_path.relative_to(repo_root)).replace("\\", "/")
        tmp_rel = src_rel + ".tmprename"
        dst_rel = str((constitution / "PROFILE.json").relative_to(repo_root)).replace("\\", "/")
        subprocess.run(["git", "-C", str(repo_root), "mv", src_rel, tmp_rel], check=True)
        subprocess.run(["git", "-C", str(repo_root), "mv", tmp_rel, dst_rel], check=True)
        # Riscrivi PROFILE.json senza inviolable_principles
        (constitution / "PROFILE.json").write_text(json.dumps(new_profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return True, log


def main() -> int:
    # Force UTF-8 on stdout/stderr (Windows cp1252 can't encode `→` in log messages).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    args = parse_args()
    prefix = "[APPLY]" if args.apply else "[DRY-RUN]"

    if not args.root.is_dir():
        print(f"ERROR: root directory not found: {args.root}", file=sys.stderr)
        return 1

    if args.apply and is_dirty(args.root):
        print(f"ERROR: working tree di {args.root} ha modifiche non committate. Committa o stash prima di applicare.", file=sys.stderr)
        return 2

    template = load_template()
    legacy_profiles = find_legacy_profiles(args.root)

    print(f"{prefix} Scansiono {args.root}/*/constitution/profile.json")
    print()

    if not legacy_profiles:
        print(f"{prefix} Nessun profile.json legacy trovato. Forse già tutti migrati?")
        return 0

    total = 0
    migrated_count = 0
    for path in legacy_profiles:
        total += 1
        migrated, log_lines = migrate_one(path, template, args.apply, prefix)
        for line in log_lines:
            print(line)
        print()
        if migrated:
            migrated_count += 1

    print(f"{prefix} Summary: {total} profili scansionati, {migrated_count} da migrare, 0 errori.")
    print()

    if not args.apply:
        print(f"{prefix} Run with --apply to execute.")
        print()
        print(f"{prefix} Suggested commit after apply:")
        print(f"{prefix}   git -C {args.root} add -A")
        print(f"{prefix}   git -C {args.root} commit -m \"refactor: split profile.json into CONST.json + PROFILE.json\"")
    else:
        print(f"{prefix} Done.")
        print(f"{prefix} IMPORTANT: Rivedi a mano CONST.json appena generato — le stringhe originali sono nei campi 'rule', ma 'scope'/'requirements'/'breakpoints' sono valori di default e potrebbero non riflettere esattamente la policy originale.")
        print(f"{prefix} Commit suggerito:")
        print(f"{prefix}   git -C {args.root} add -A")
        print(f"{prefix}   git -C {args.root} commit -m \"refactor: split profile.json into CONST.json + PROFILE.json\"")

    return 0


if __name__ == "__main__":
    sys.exit(main())
