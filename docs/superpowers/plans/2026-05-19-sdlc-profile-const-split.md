# SDLC Profile Split (CONST + PROFILE) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Splittare `deloitte-profiles/<progetto>/constitution/profile.json` in due file separati (`CONST.json` = principi/standard di archetipo, `PROFILE.json` = dettagli specifici progetto), refactorare le 9 skill SDLC per caricare entrambi i file, e migrare il profilo `banca-agente` esistente.

**Architecture:** Split big-bang con migrazione automatica via script Python. Le skill SDLC caricano CONST + PROFILE all'avvio (sezione standard duplicata in ogni SKILL.md). Nessun compat layer — un solo profilo esistente sotto controllo locale. Auto-update di `sdlc-analyzer` tocca solo PROFILE; CONST è policy stabile gestita manualmente.

**Tech Stack:** Python 3.12 (script migrazione, scelto su bash perché `jq` non è installato), JSON Schema Draft 2020-12 (validazione), pytest (test fixture migrazione), bash (sync skill locali, già esistente).

**Repo coinvolte:**
- `C:/Users/davmelis/Documents/MyGitHub/claude-flow` (skill SDLC + script + design docs)
- `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles` (schemi + profili progetto)

**Riferimento al design:** `docs/superpowers/specs/2026-05-19-sdlc-profile-const-split-design.md`

**Note operative:**
- L'utente ha detto: "non ti inserire nei commit". I task NON eseguono `git commit` automaticamente. Al termine di ogni fase logica, il plan indica "i file sono pronti per il commit" e suggerisce il comando, ma l'utente decide se/quando lanciarlo.
- Tutte le path sono assolute (Windows con `/` come separator, compatibile con bash su git-bash).

---

## File Structure

### File NUOVI da creare

| Path | Responsabilità |
|---|---|
| `deloitte-profiles/const-schema.json` | JSON Schema per CONST.json (Draft 2020-12) |
| `claude-flow/skills/sdlc-profile-setup/_const-template.json` | Template precompilato di default per nuovi CONST.json. Letto sia dalla skill (Step 8) sia dallo script di migrazione (per popolare le sezioni mancanti) |
| `claude-flow/scripts/migrate-profile-split.py` | Script Python di migrazione `profile.json` → `CONST.json` + `PROFILE.json` |
| `claude-flow/scripts/tests/test_migrate_profile_split.py` | Test pytest per lo script di migrazione |
| `claude-flow/scripts/tests/fixtures/sample_profile.json` | Fixture: profile.json di test (subset di banca-agente) |
| `claude-flow/scripts/tests/fixtures/expected_CONST.json` | Fixture: CONST.json atteso dopo migrazione |
| `claude-flow/scripts/tests/fixtures/expected_PROFILE.json` | Fixture: PROFILE.json atteso dopo migrazione |

### File da MODIFICARE

| Path | Modifica |
|---|---|
| `deloitte-profiles/profile-schema.json` | Aggiornare `description` di `conventions` (rimuove menzione di `inviolable_principles`) |
| `deloitte-profiles/README.md` | Aggiornare sezione "Profile Sections" → "Constitution Files", documentare CONST + PROFILE |
| `claude-flow/skills/sdlc-reviewer/SKILL.md` | Aggiungere sezione "Caricamento contesto progetto (CONST + PROFILE)" |
| `claude-flow/skills/sdlc-clarify/SKILL.md` | Idem |
| `claude-flow/skills/sdlc-executor/SKILL.md` | Idem |
| `claude-flow/skills/sdlc-debug/SKILL.md` | Idem (rimuove il vecchio riferimento a `constitution/profile.json` linea 75) |
| `claude-flow/skills/sdlc-updater/SKILL.md` | Idem |
| `claude-flow/skills/sdlc-estimator/SKILL.md` | Idem |
| `claude-flow/skills/sdlc-progress-report/SKILL.md` | Idem |
| `claude-flow/skills/sdlc-analyzer/SKILL.md` | Loader + chiarimento auto-update solo su PROFILE + nuova sezione "Violazioni principi CONST" nel template PLAN.md |
| `claude-flow/skills/sdlc-profile-setup/SKILL.md` | Loader + Step 8 raddoppiato (genera CONST + PROFILE), template precompilato letto da `_const-template.json` |
| `claude-flow/SDLC_SKILLS_DOCUMENTATION.md` | Sezione "Profilo" → "CONST + PROFILE" + glossario aggiornato |

### File generati DOPO la migrazione (output dello script)

| Path | Generato da |
|---|---|
| `deloitte-profiles/banca-agente/constitution/CONST.json` | `migrate-profile-split.py --apply` |
| `deloitte-profiles/banca-agente/constitution/PROFILE.json` | `migrate-profile-split.py --apply` (rinomina di `profile.json`) |
| `deloitte-profiles/banca-agente/constitution/profile.json` | **ELIMINATO** dalla migrazione |

---

# FASE 1 — Foundation (schemi + template)

## Task 1: Creare `deloitte-profiles/const-schema.json`

**Files:**
- Create: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/const-schema.json`

- [ ] **Step 1: Scrivere il file `const-schema.json`**

Crea il file con esattamente questo contenuto:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/deloitte/deloitte-profiles/const-schema.json",
  "title": "Deloitte Project Constitution — Archetypal Principles",
  "description": "Schema for CONST.json. Contains principles, quality standards, code style, git workflow, and architectural patterns. Read by all SDLC skills as inviolable constraints on every generated output.",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "$schema": { "type": "string" },
    "inviolable_principles": {
      "type": "object",
      "description": "Non-negotiable rules every output must respect",
      "additionalProperties": true,
      "properties": {
        "security": { "$ref": "#/$defs/principle" },
        "accessibility": { "$ref": "#/$defs/principle" },
        "responsiveness": { "$ref": "#/$defs/principle" },
        "data_privacy": { "$ref": "#/$defs/principle" }
      }
    },
    "quality_standards": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "test_coverage": {
          "type": "object",
          "properties": {
            "minimum_percent": { "type": "integer", "minimum": 0, "maximum": 100 },
            "applies_to": { "type": "array", "items": { "type": "string" } }
          }
        },
        "error_handling": { "type": "string" },
        "logging": {
          "type": "object",
          "properties": {
            "format": { "type": "string" },
            "never_log": { "type": "array", "items": { "type": "string" } }
          }
        },
        "performance": { "type": "object", "additionalProperties": true }
      }
    },
    "code_style": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "max_function_lines": { "type": "integer", "minimum": 1 },
        "max_file_lines": { "type": "integer", "minimum": 1 },
        "max_nesting_depth": { "type": "integer", "minimum": 1 },
        "no_magic_numbers": { "type": "boolean" },
        "no_debug_statements_in_prod": { "type": "boolean" }
      }
    },
    "git_workflow": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "branch_pattern": { "type": "string" },
        "commit_convention": { "type": "string" }
      }
    },
    "architectural_patterns": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "layered_separation": { "type": "string" },
        "api_response_envelope": { "type": "string" },
        "test_pattern": { "type": "string" },
        "input_validation": { "type": "string" }
      }
    }
  },
  "$defs": {
    "principle": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "rule": { "type": "string" },
        "scope": { "type": "string" },
        "verification": { "type": "string" },
        "requirements": { "type": "array", "items": { "type": "string" } },
        "breakpoints": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["rule"]
    }
  }
}
```

- [ ] **Step 2: Validare che il file sia JSON valido**

Run:
```bash
python -c "import json; json.load(open('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/const-schema.json')); print('OK: valid JSON')"
```

Expected: `OK: valid JSON`

---

## Task 2: Aggiornare `deloitte-profiles/profile-schema.json`

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json` (linea ~93-95, description di `conventions`)

- [ ] **Step 1: Leggere lo stato attuale della description di `conventions`**

Run:
```bash
grep -n "Project coding conventions" "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json"
```

Expected output: `94:      "description": "Project coding conventions and structural patterns",`

- [ ] **Step 2: Sostituire la description**

Edit file `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json`:

OLD:
```json
      "description": "Project coding conventions and structural patterns",
```

NEW:
```json
      "description": "Project coding conventions and structural patterns. NOTE: inviolable_principles is no longer accepted here — moved to CONST.json (see const-schema.json).",
```

- [ ] **Step 3: Validare che il file sia ancora JSON valido**

Run:
```bash
python -c "import json; json.load(open('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json')); print('OK: valid JSON')"
```

Expected: `OK: valid JSON`

---

## Task 3: Creare `_const-template.json` (template precompilato)

**Files:**
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-profile-setup/_const-template.json`

Il template viene letto sia da `sdlc-profile-setup` (Step 8 — generazione di CONST.json per nuovi progetti) sia da `migrate-profile-split.py` (per popolare le sezioni mancanti durante la migrazione).

- [ ] **Step 1: Scrivere il file `_const-template.json`**

Crea il file con esattamente questo contenuto:

```json
{
  "$schema": "../../const-schema.json",
  "inviolable_principles": {
    "security": {
      "rule": "Tutto il codice deve rispettare OWASP Top 10",
      "scope": "ogni endpoint, input utente, query, gestione dati sensibili",
      "verification": "verifica obbligatoria prima del merge"
    },
    "accessibility": {
      "rule": "Tutto il codice frontend deve rispettare WCAG 2.1 AA",
      "requirements": [
        "navigabile da tastiera",
        "compatibile screen reader",
        "contrasto AA",
        "attributi ARIA corretti"
      ]
    },
    "responsiveness": {
      "rule": "Tutto il codice frontend deve essere responsive",
      "breakpoints": ["mobile", "tablet", "desktop"]
    },
    "data_privacy": {
      "rule": "Mai loggare PII; rispettare GDPR per ogni dato personale",
      "scope": "log applicativi, error tracking, analytics"
    }
  },
  "quality_standards": {
    "test_coverage": {
      "minimum_percent": 80,
      "applies_to": ["unit", "integration"]
    },
    "error_handling": "Gestire ogni errore esplicitamente, mai swallow; user-facing friendly, server-side con context",
    "logging": {
      "format": "structured",
      "never_log": ["PII", "credenziali", "token"]
    },
    "performance": {
      "api_latency_p95_ms": 200,
      "frontend_lcp_ms": 2500
    }
  },
  "code_style": {
    "max_function_lines": 50,
    "max_file_lines": 800,
    "max_nesting_depth": 4,
    "no_magic_numbers": true,
    "no_debug_statements_in_prod": true
  },
  "git_workflow": {
    "branch_pattern": "feature/<desc> | fix/<desc> | release/sprint-wave-X.Y",
    "commit_convention": "conventional commits (feat:, fix:, refactor:, docs:, test:, chore:)"
  },
  "architectural_patterns": {
    "layered_separation": "controller/service/repository (o equivalenti) con dipendenze unidirezionali",
    "api_response_envelope": "shape consistente: { status, data|null, error|null, meta? }",
    "test_pattern": "Arrange-Act-Assert; nomi test descrittivi del comportamento atteso",
    "input_validation": "validare sempre ai boundary del sistema"
  }
}
```

- [ ] **Step 2: Validare che il template sia conforme a `const-schema.json`**

Run:
```bash
python -c "
import json, sys
template = json.load(open('C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-profile-setup/_const-template.json'))
schema = json.load(open('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/const-schema.json'))
# Basic sanity check (jsonschema lib may not be installed — verify structure manually)
required_top = ['inviolable_principles', 'quality_standards', 'code_style', 'git_workflow', 'architectural_patterns']
missing = [k for k in required_top if k not in template]
if missing:
    print(f'FAIL: missing sections {missing}')
    sys.exit(1)
required_principles = ['security', 'accessibility', 'responsiveness', 'data_privacy']
missing = [k for k in required_principles if k not in template['inviolable_principles']]
if missing:
    print(f'FAIL: missing principles {missing}')
    sys.exit(1)
for name, p in template['inviolable_principles'].items():
    if 'rule' not in p:
        print(f'FAIL: principle {name} missing required field rule')
        sys.exit(1)
print('OK: template structure valid against schema requirements')
"
```

Expected: `OK: template structure valid against schema requirements`

---

**Fine FASE 1.** Stato: schemi e template pronti. **I file sono pronti per il commit (utente).**

Comando suggerito (l'utente decide):
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" add const-schema.json profile-schema.json
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" commit -m "feat: add const-schema.json for CONST/PROFILE split"

git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" add skills/sdlc-profile-setup/_const-template.json
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" commit -m "feat: add CONST template for sdlc-profile-setup"
```

---

# FASE 2 — Script di migrazione (Python, TDD)

## Task 4: Creare scheletro CLI di `migrate-profile-split.py`

**Files:**
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py`

- [ ] **Step 1: Scrivere lo scheletro CLI**

Crea il file con questo contenuto:

```python
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
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path("C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles")
TEMPLATE_PATH = Path(__file__).parent.parent / "skills" / "sdlc-profile-setup" / "_const-template.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split profile.json into CONST.json + PROFILE.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Default: dry-run.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Path to deloitte-profiles repo. Default: {DEFAULT_ROOT}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prefix = "[APPLY]" if args.apply else "[DRY-RUN]"

    if not args.root.is_dir():
        print(f"ERROR: root directory not found: {args.root}", file=sys.stderr)
        return 1

    print(f"{prefix} Scansiono {args.root}/*/constitution/profile.json")
    print()

    # Placeholder: la logica vera arriva nei Task successivi
    print(f"{prefix} (logica non ancora implementata)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verificare che lo script si esegua senza errori (dry-run)**

Run:
```bash
python "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py"
```

Expected output:
```
[DRY-RUN] Scansiono C:\Users\davmelis\Documents\MyGitHub\deloitte-profiles/*/constitution/profile.json

[DRY-RUN] (logica non ancora implementata)
```

- [ ] **Step 3: Verificare help**

Run:
```bash
python "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py" --help
```

Expected: help text mostra `--apply` e `--root` con i defaults.

---

## Task 5: Creare fixture di test (profile sample + expected outputs)

**Files:**
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/fixtures/sample_profile.json`
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/fixtures/expected_CONST.json`
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/fixtures/expected_PROFILE.json`

- [ ] **Step 1: Creare la directory delle fixture**

Run:
```bash
mkdir -p "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/fixtures"
```

- [ ] **Step 2: Scrivere `sample_profile.json`** (subset minimale di banca-agente con tutti i campi rilevanti per la migrazione)

Crea il file con questo contenuto:

```json
{
  "project": {
    "name": "Test Project",
    "client": "Test Client"
  },
  "tech_stack": {
    "backend": {
      "language": "Java 21",
      "framework": "Spring Boot 3.2.0"
    },
    "frontend": {
      "language": "TypeScript 4.9",
      "framework": "Angular 15"
    }
  },
  "conventions": {
    "package_structure": "com.test.app.<layer>",
    "layers": ["controller", "service", "repository"],
    "test_framework": "JUnit 5 + Mockito",
    "branch_convention": "feature/<description>",
    "commit_convention": "conventional commits",
    "inviolable_principles": {
      "security": "Tutto il codice deve rispettare gli standard OWASP Top 10. Nessuna eccezione.",
      "accessibility": "Tutto il codice frontend deve rispettare i requisiti di accessibilita' (WCAG).",
      "responsiveness": "Tutto il codice frontend deve essere responsive."
    }
  },
  "design_system": {
    "palette": {"--primary-color": "blue"}
  }
}
```

- [ ] **Step 3: Scrivere `expected_CONST.json`** (output atteso dopo migrazione)

Crea il file con questo contenuto:

```json
{
  "$schema": "../../const-schema.json",
  "inviolable_principles": {
    "security": {
      "rule": "Tutto il codice deve rispettare gli standard OWASP Top 10. Nessuna eccezione.",
      "scope": "ogni endpoint, input utente, query, gestione dati sensibili",
      "verification": "verifica obbligatoria prima del merge"
    },
    "accessibility": {
      "rule": "Tutto il codice frontend deve rispettare i requisiti di accessibilita' (WCAG).",
      "requirements": [
        "navigabile da tastiera",
        "compatibile screen reader",
        "contrasto AA",
        "attributi ARIA corretti"
      ]
    },
    "responsiveness": {
      "rule": "Tutto il codice frontend deve essere responsive.",
      "breakpoints": ["mobile", "tablet", "desktop"]
    },
    "data_privacy": {
      "rule": "Mai loggare PII; rispettare GDPR per ogni dato personale",
      "scope": "log applicativi, error tracking, analytics"
    }
  },
  "quality_standards": {
    "test_coverage": {
      "minimum_percent": 80,
      "applies_to": ["unit", "integration"]
    },
    "error_handling": "Gestire ogni errore esplicitamente, mai swallow; user-facing friendly, server-side con context",
    "logging": {
      "format": "structured",
      "never_log": ["PII", "credenziali", "token"]
    },
    "performance": {
      "api_latency_p95_ms": 200,
      "frontend_lcp_ms": 2500
    }
  },
  "code_style": {
    "max_function_lines": 50,
    "max_file_lines": 800,
    "max_nesting_depth": 4,
    "no_magic_numbers": true,
    "no_debug_statements_in_prod": true
  },
  "git_workflow": {
    "branch_pattern": "feature/<desc> | fix/<desc> | release/sprint-wave-X.Y",
    "commit_convention": "conventional commits (feat:, fix:, refactor:, docs:, test:, chore:)"
  },
  "architectural_patterns": {
    "layered_separation": "controller/service/repository (o equivalenti) con dipendenze unidirezionali",
    "api_response_envelope": "shape consistente: { status, data|null, error|null, meta? }",
    "test_pattern": "Arrange-Act-Assert; nomi test descrittivi del comportamento atteso",
    "input_validation": "validare sempre ai boundary del sistema"
  }
}
```

- [ ] **Step 4: Scrivere `expected_PROFILE.json`** (output atteso dopo migrazione)

Crea il file con questo contenuto:

```json
{
  "project": {
    "name": "Test Project",
    "client": "Test Client"
  },
  "tech_stack": {
    "backend": {
      "language": "Java 21",
      "framework": "Spring Boot 3.2.0"
    },
    "frontend": {
      "language": "TypeScript 4.9",
      "framework": "Angular 15"
    }
  },
  "conventions": {
    "package_structure": "com.test.app.<layer>",
    "layers": ["controller", "service", "repository"],
    "test_framework": "JUnit 5 + Mockito",
    "branch_convention": "feature/<description>",
    "commit_convention": "conventional commits"
  },
  "design_system": {
    "palette": {"--primary-color": "blue"}
  }
}
```

- [ ] **Step 5: Verificare che tutte e tre le fixture siano JSON validi**

Run:
```bash
python -c "
import json
for f in ['sample_profile.json', 'expected_CONST.json', 'expected_PROFILE.json']:
    json.load(open(f'C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/fixtures/{f}'))
    print(f'OK: {f}')
"
```

Expected:
```
OK: sample_profile.json
OK: expected_CONST.json
OK: expected_PROFILE.json
```

---

## Task 6: Scrivere il test pytest (TDD — RED)

**Files:**
- Create: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/tests/test_migrate_profile_split.py`

- [ ] **Step 1: Scrivere i test**

Crea il file con questo contenuto:

```python
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
```

- [ ] **Step 2: Eseguire i test per verificare che FALLISCANO (RED — lo script non ha ancora la logica)**

Run:
```bash
cd "C:/Users/davmelis/Documents/MyGitHub/claude-flow" && python -m pytest scripts/tests/test_migrate_profile_split.py -v
```

Expected: tutti i test FALLISCONO (eccetto magari `test_dry_run_no_changes` che potrebbe passare per caso). Test attesi in fallimento:
- `test_apply_creates_const_and_profile` — FAIL (lo script non crea nulla)
- `test_apply_matches_expected_const` — FAIL
- `test_apply_matches_expected_profile` — FAIL
- `test_idempotent_skip_already_migrated` — FAIL
- `test_apply_refuses_dirty_working_tree` — FAIL
- `test_dry_run_allows_dirty_working_tree` — può PASSARE (lo script non controlla niente)

Se pytest non è installato, prima:
```bash
python -m pip install pytest
```

---

## Task 7: Implementare la logica di migrazione (TDD — GREEN)

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py`

- [ ] **Step 1: Sostituire interamente il contenuto dello script con l'implementazione completa**

Sovrascrivi il file con questo contenuto:

```python
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
    """True se il working tree git ha modifiche unstaged o file untracked."""
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def find_legacy_profiles(root: Path) -> list[Path]:
    """Trova tutti i <progetto>/constitution/profile.json."""
    return sorted(root.glob("*/constitution/profile.json"))


def is_already_migrated(constitution_dir: Path) -> bool:
    """True se CONST.json + PROFILE.json esistono e profile.json no."""
    return (
        not (constitution_dir / "profile.json").exists()
        and (constitution_dir / "CONST.json").exists()
        and (constitution_dir / "PROFILE.json").exists()
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
```

- [ ] **Step 2: Eseguire i test per verificare che PASSINO (GREEN)**

Run:
```bash
cd "C:/Users/davmelis/Documents/MyGitHub/claude-flow" && python -m pytest scripts/tests/test_migrate_profile_split.py -v
```

Expected: tutti i 7 test PASSANO. Se qualche test fallisce, debugga prima di proseguire.

- [ ] **Step 3: Verifica manuale del dry-run sul `banca-agente` reale**

Run:
```bash
python "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py"
```

Expected output (parziale):
```
[DRY-RUN] Scansiono C:\Users\davmelis\Documents\MyGitHub\deloitte-profiles/*/constitution/profile.json

[DRY-RUN] banca-agente/constitution/
  read  profile.json (14316 bytes)
  extract conventions.inviolable_principles → CONST.inviolable_principles (3 principi: security, accessibility, responsiveness)
  add default sections from template (...)
  write CONST.json
  remove conventions.inviolable_principles from profile.json
  git mv profile.json PROFILE.json

[DRY-RUN] Summary: 1 profili scansionati, 1 da migrare, 0 errori.
...
```

**Non eseguire `--apply` ancora**. La migrazione vera avverrà alla FASE 5.

---

**Fine FASE 2.** Stato: script di migrazione testato e pronto. **I file sono pronti per il commit (utente).**

Comando suggerito:
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" add scripts/migrate-profile-split.py scripts/tests/
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" commit -m "feat: add migrate-profile-split.py with pytest coverage"
```

---

# FASE 3 — Refactor delle 9 skill SDLC

## Task 8: Aggiungere sezione "Caricamento contesto progetto" alle 7 skill base

**Files (7 file da modificare con la stessa sezione):**
- Modify: `claude-flow/skills/sdlc-reviewer/SKILL.md`
- Modify: `claude-flow/skills/sdlc-clarify/SKILL.md`
- Modify: `claude-flow/skills/sdlc-executor/SKILL.md`
- Modify: `claude-flow/skills/sdlc-debug/SKILL.md` (anche rimozione vecchio riferimento)
- Modify: `claude-flow/skills/sdlc-updater/SKILL.md`
- Modify: `claude-flow/skills/sdlc-estimator/SKILL.md`
- Modify: `claude-flow/skills/sdlc-progress-report/SKILL.md`

### Blocco standard da inserire

In ogni SKILL.md, subito DOPO la sezione `## Risoluzione Path — deloitte-profiles` (e prima della sezione successiva, tipicamente `## Auto-sync della repo profili` o equivalente), inserire questo blocco:

````markdown
---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path (`profiles_repo`, `profilo`) e prima di eseguire qualsiasi altra fase, carica i due file di costituzione del progetto:

```bash
git -C "<profiles_repo>" pull origin main --quiet
cat "<profiles_repo>/<profilo>/constitution/CONST.json"
cat "<profiles_repo>/<profilo>/constitution/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| `.br-local.json` manca | "Esegui prima `/sdlc-profile-setup`" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il profilo `<nome>` non ha CONST.json. Eseguire `bash claude-flow/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il profilo `<nome>` non ha PROFILE.json. Stato inconsistente — il profilo è incompleto. Ripristinare da git history o rifare il setup." | Stop |
| Entrambi mancano, esiste `profile.json` (legacy) | "Profilo in formato vecchio (pre-split CONST/PROFILE). Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per fare lo split automaticamente." | Stop |
| JSON malformed | Mostra errore di parse + path | Stop |

**Semantica d'uso:**

- **CONST** = vincoli inviolabili per ogni output generato. Ogni piano, task, fix, review, bug analysis che produci DEVE rispettare:
  - `inviolable_principles` (security/a11y/responsiveness/privacy)
  - `quality_standards` (coverage, error handling, logging, performance)
  - `code_style` (limiti dimensionali, no magic numbers)
  - `git_workflow` (branch/commit pattern)
  - `architectural_patterns` (layering, response envelope, AAA, validazione boundary)
- **PROFILE** = "lingua" del progetto. Usa i dettagli (tech stack, repositories con sigle, dominio, glossario, design system) per nominare le task con le sigle corrette, proporre snippet con il framework/versione giusti, usare il vocabolario di dominio, e riferire componenti del design system.

Entrambi i file restano disponibili come contesto per tutta la durata della skill.

---
````

### Sub-step per ogni file

- [ ] **Step 1: sdlc-reviewer**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-reviewer/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-reviewer/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 2: sdlc-clarify**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-clarify/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-clarify/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 3: sdlc-executor**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-executor/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-executor/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 4: sdlc-debug (variante: include anche cleanup di un vecchio riferimento)**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-debug/SKILL.md`.

**Substep 4a:** Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

**Substep 4b:** Trova la riga (intorno alla linea 75) che dice:
```
1. Leggi `<profiles_repo>/<profilo>/constitution/profile.json`
```
e sostituiscila con:
```
1. Carica CONST.json + PROFILE.json secondo la sezione "Caricamento contesto progetto"
```

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-debug/SKILL.md"
grep -n "constitution/profile.json" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-debug/SKILL.md" || echo "OK: no legacy ref"
```
Expected: una riga "Caricamento contesto progetto" presente, e "OK: no legacy ref" stampato (nessuna menzione di `constitution/profile.json` singolare).

- [ ] **Step 5: sdlc-updater**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-updater/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-updater/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 6: sdlc-estimator**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-estimator/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-estimator/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 7: sdlc-progress-report**

Apri `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-progress-report/SKILL.md`. Trova la fine della sezione `## Risoluzione Path — deloitte-profiles`. Inserisci il blocco standard tra essa e la sezione successiva.

Verifica:
```bash
grep -n "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-progress-report/SKILL.md"
```
Expected: una linea con la nuova sezione.

- [ ] **Step 8: Verifica globale che tutte e 7 le skill abbiano la sezione**

Run:
```bash
for f in sdlc-reviewer sdlc-clarify sdlc-executor sdlc-debug sdlc-updater sdlc-estimator sdlc-progress-report; do
  if grep -q "Caricamento contesto progetto" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/$f/SKILL.md"; then
    echo "OK: $f"
  else
    echo "FAIL: $f mancante"
  fi
done
```

Expected:
```
OK: sdlc-reviewer
OK: sdlc-clarify
OK: sdlc-executor
OK: sdlc-debug
OK: sdlc-updater
OK: sdlc-estimator
OK: sdlc-progress-report
```

- [ ] **Step 9: Verifica che NESSUN file menzioni più `profile.json` (singolare, vecchio)**

Run:
```bash
grep -rn "constitution/profile.json" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/" || echo "OK: no legacy references"
```

Expected: `OK: no legacy references`

---

## Task 9: Refactor di `sdlc-analyzer` (loader + auto-update solo PROFILE + sezione "Violazioni principi")

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-analyzer/SKILL.md`

- [ ] **Step 1: Inserire la sezione "Caricamento contesto progetto"**

Come per le 7 skill base (Task 8). Inserisci il blocco standard dopo la sezione `## Risoluzione Path — deloitte-profiles`.

- [ ] **Step 2: Aggiungere chiarimento sul perimetro dell'auto-update**

Trova la sezione di sdlc-analyzer che descrive l'auto-aggiornamento del profilo (cerca con `grep -n "aggiorna" skills/sdlc-analyzer/SKILL.md` o equivalente). Aggiungi questo blocco dopo la descrizione esistente:

```markdown
### Perimetro dell'auto-update

**L'auto-update riguarda esclusivamente `PROFILE.json`.**

I principi di `CONST.json` sono policy stabili, gestite manualmente dall'utente. Non vanno mai modificati in automatico dall'analisi del codebase.

Se durante l'analisi rilevi che un principio CONST non è rispettato dal codice esistente (es. test coverage < soglia minima dichiarata, log con PII, funzioni > max_function_lines, endpoint senza validazione), **segnalalo come finding nel `PLAN.md` sotto la sezione "Violazioni principi CONST rilevate"**, NON modificare `CONST.json`.
```

- [ ] **Step 3: Aggiungere "Violazioni principi CONST rilevate" al template di PLAN.md**

Trova nello SKILL.md la sezione che descrive lo schema di `PLAN.md` generato. Aggiungi questa nuova sezione standard come ultima parte del template di PLAN.md:

```markdown
## Violazioni principi CONST rilevate

Elenco dei punti in cui il codebase corrente NON rispetta i principi dichiarati in `CONST.json`. Sono finding informativi (non blocking — il piano va avanti comunque), ma vanno mostrati al team funzionale e di sviluppo perché documentano gap di conformità da chiudere nel medio termine.

Formato di ogni finding:
- **Principio violato:** `<categoria.regola>` (es. `quality_standards.test_coverage.minimum_percent`)
- **Dove:** `<repo>/<path>:<linea>` o `<repo>/<modulo>` se diffuso
- **Evidenza:** snippet di codice o metrica osservata
- **Impatto sul BR corrente:** `BLOCCA il task X` | `Da fixare in coda al BR` | `Solo segnalazione (gap pregresso)`

Se nessuna violazione è stata rilevata, lascia la sezione vuota con il testo: "Nessuna violazione dei principi CONST rilevata durante l'analisi."
```

- [ ] **Step 4: Verifica grep**

Run:
```bash
grep -n "Caricamento contesto progetto\|Perimetro dell'auto-update\|Violazioni principi CONST" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-analyzer/SKILL.md"
```

Expected: 3 righe (o più), una per ognuna delle nuove sezioni.

---

## Task 10: Refactor di `sdlc-profile-setup` (loader + Step 8 raddoppiato + template precompilato)

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-profile-setup/SKILL.md`

- [ ] **Step 1: Inserire la sezione "Caricamento contesto progetto" — VARIANTE PER PROFILE-SETUP**

Per `sdlc-profile-setup` la sezione standard NON si applica così com'è (la skill CREA il profilo, quindi all'inizio CONST/PROFILE non esistono ancora). Inserisci invece questo blocco subito dopo l'intro della skill (dopo la riga `# SDLC Profile Setup — Creazione Guidata Profilo Progetto`):

```markdown
> **Nota su CONST + PROFILE:** Questa skill è l'**eccezione** al loader standard delle skill SDLC: NON carica CONST + PROFILE all'avvio (li sta creando). Tutte le altre 8 skill (`sdlc-analyzer`, `sdlc-reviewer`, `sdlc-clarify`, `sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-estimator`, `sdlc-progress-report`) caricano CONST + PROFILE dopo la "Risoluzione Path".
>
> Output di questa skill: **due file** nella folder `constitution/` del progetto:
> - `CONST.json` — principi/standard di archetipo (template precompilato di default, adattato in base al codebase)
> - `PROFILE.json` — dettagli specifici del progetto (tech stack, dominio, design system)
```

- [ ] **Step 2: Sostituire interamente lo Step 8**

Trova nello SKILL.md la sezione `## Step 8 — Genera profile.json` e tutta la sua zona (fino allo Step 9). Sostituiscila con:

````markdown
## Step 8 — Genera CONST.json + PROFILE.json

In questo step generi DUE file separati: un `CONST.json` (principi/standard di archetipo, template precompilato) e un `PROFILE.json` (dettagli specifici progetto).

### 8.1 — Genera CONST.json dal template precompilato

Leggi il template precompilato:

```bash
cat "<path-al-repo-claude-flow>/skills/sdlc-profile-setup/_const-template.json"
```

Adatta il template in base ai codebase rilevati negli Step 3-5:

| Condizione | Modifica al template |
|---|---|
| Nessun codebase frontend rilevato | Rimuovi `inviolable_principles.accessibility` e `inviolable_principles.responsiveness` |
| Nessuna API REST rilevata | Rimuovi `architectural_patterns.api_response_envelope` |
| Nessun database con dati personali | Mantieni `data_privacy` come default conservativo (l'utente può rimuoverlo dopo) |

Presenta il CONST.json risultante:

> Ecco il **CONST.json** generato (template di default adattato al tuo codebase):
>
> ```json
> [JSON completo]
> ```
>
> Va bene così o vuoi modificare qualche principio prima di scrivere il file? (es. cambiare la soglia di test coverage, aggiungere un principio personalizzato, rimuovere uno dei default)

Aspetta la risposta. Se l'utente vuole modifiche, applicale e ripresenta il JSON. Solo dopo OK procedi.

### 8.2 — Genera PROFILE.json dai dati raccolti negli Step 1-7

Assembla i dati raccolti negli Step 1-7 in `PROFILE.json` (struttura come da `profile-schema.json`). Include solo le sezioni con dati reali — ometti campi vuoti o sezioni saltate.

Struttura del JSON:

```json
{
  "$schema": "../../profile-schema.json",
  "project": {
    "name": "<nome>",
    "client": "<client>",
    "description": "<description>"
  },
  "tech_stack": { ... dati dagli Step 3-5 ... },
  "conventions": { ... dati rilevati o forniti ... },
  "design_system": { ... },
  "domain": { ... dati dallo Step 6 ... },
  "custom_agents": [...]
}
```

**NOTA IMPORTANTE:** in `conventions` NON inserire più `inviolable_principles` — quei dati ora vivono in `CONST.json`.

Presenta `PROFILE.json` all'utente:

> Ecco il **PROFILE.json** generato per **<nome>**:
>
> ```json
> [JSON completo]
> ```
>
> Confermo e scrivo i due file?

Aspetta la risposta finale.

### 8.3 — Scrivi entrambi i file

Dopo conferma, scrivi i file:

```bash
mkdir -p "<profiles_repo>/<nome>/constitution"
mkdir -p "<profiles_repo>/<nome>/agents"
mkdir -p "<profiles_repo>/<nome>/references"
mkdir -p "<profiles_repo>/<nome>/plans/todo"
mkdir -p "<profiles_repo>/<nome>/plans/in-progress"
mkdir -p "<profiles_repo>/<nome>/plans/done"
# Scrivi CONST.json con il contenuto confermato in 8.1
# Scrivi PROFILE.json con il contenuto confermato in 8.2
```

Conferma finale:

> Profilo **<nome>** creato:
> - `<profiles_repo>/<nome>/constitution/CONST.json` (principi)
> - `<profiles_repo>/<nome>/constitution/PROFILE.json` (dettagli)
> - Struttura: `constitution/`, `agents/`, `references/`, `plans/todo|in-progress|done/`
````

- [ ] **Step 3: Aggiornare lo Step 9 (commit message)**

Trova nello SKILL.md `## Step 9 — Commit e push` e modifica il commit message suggerito:

OLD:
```bash
git commit -m "feat: add profile for <nome>"
```

NEW:
```bash
git commit -m "feat: add profile for <nome> (CONST + PROFILE)"
```

- [ ] **Step 4: Aggiornare lo Step 10 (conferma finale)**

Trova nello SKILL.md `## Step 10 — Aggiorna .br-local.json` e modifica il messaggio di conferma finale. Sostituisci:

OLD:
```
> - Profilo: `<profiles_repo>/<nome>/constitution/profile.json`
```

NEW:
```
> - Profilo: `<profiles_repo>/<nome>/constitution/CONST.json` + `PROFILE.json`
```

- [ ] **Step 5: Verifica finale**

Run:
```bash
grep -n "profile.json\|CONST\|PROFILE\|_const-template" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/sdlc-profile-setup/SKILL.md" | head -30
```

Expected: niente più menzioni di `constitution/profile.json` (singolare, legacy); molte menzioni di `CONST.json`, `PROFILE.json`, `_const-template.json`.

---

**Fine FASE 3.** Stato: tutte le 9 skill caricano CONST + PROFILE. **I file sono pronti per il commit (utente).**

Comando suggerito:
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" add skills/sdlc-*/SKILL.md
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" commit -m "refactor(sdlc): all skills load CONST + PROFILE, split profile.json into constitution files"
```

---

# FASE 4 — Documentazione

## Task 11: Aggiornare `deloitte-profiles/README.md`

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/README.md`

- [ ] **Step 1: Aggiornare la sezione "Directory Structure"**

Trova il blocco ASCII tree (intorno alla riga 10-37) e modifica la voce del `constitution/`:

OLD:
```
│   ├── constitution/
│   │   └── profile.json         # configurazione progetto (tech stack, dominio, design system)
```

NEW:
```
│   ├── constitution/
│   │   ├── CONST.json           # principi/standard di archetipo (OWASP, WCAG, test coverage, ecc.)
│   │   └── PROFILE.json         # dettagli specifici progetto (tech stack, dominio, design system)
```

- [ ] **Step 2: Sostituire la sezione "Profile Sections"**

Trova la sezione `## Profile Sections` (intorno alla riga 51). Sostituiscila con:

```markdown
## Constitution Files

Ogni progetto ha due file nella sua folder `constitution/`:

### `CONST.json` — principi e standard di archetipo

Contiene le regole non-negoziabili e gli standard di qualità ripetibili tra progetti simili. Mai modificato in automatico dalle skill — è policy stabile gestita dall'utente.

| Section | Content | Required |
|---|---|---|
| `inviolable_principles` | Security (OWASP), accessibility (WCAG), responsiveness, data privacy (GDPR) | Almeno uno |
| `quality_standards` | Test coverage minima, error handling, logging, performance budget | No |
| `code_style` | Max function/file lines, nesting depth, no magic numbers | No |
| `git_workflow` | Branch pattern, commit convention | No |
| `architectural_patterns` | Layered separation, API response envelope, AAA test pattern, input validation | No |

Validato contro `const-schema.json`. Template di default in `claude-flow/skills/sdlc-profile-setup/_const-template.json`.

### `PROFILE.json` — dettagli specifici del progetto

Contiene tutto ciò che è unico del progetto. Auto-aggiornato da `sdlc-analyzer` quando rileva nuove convenzioni dal codice.

| Section | Content | Required |
|---|---|---|
| `project` | Name, client, description | Yes |
| `tech_stack` | Backend, frontend, repositories (multi-repo con sigle), infrastructure, integrations | Yes |
| `conventions` | Package structure, layers, base entity, API prefix, test framework, branch/commit specifici, naming | No |
| `design_system` | Palette, typography, spacing, components, reference files | No |
| `domain` | Glossary, business rules, entity state machines | No |
| `custom_agents` | Paths to custom agent `.md` files | No |

Validato contro `profile-schema.json`.
```

- [ ] **Step 3: Aggiornare la sezione "Local Configuration"**

Trova la sezione `### Local Configuration` (intorno alla riga 74). Aggiungi alla fine, dopo il blocco di esempio `.br-local.json`:

```markdown
Le SDLC skills risolvono **entrambi** i file:
- `<profiles_repo>/<profilo>/constitution/CONST.json`
- `<profiles_repo>/<profilo>/constitution/PROFILE.json`

Entrambi devono esistere per il funzionamento. Se manca uno dei due, le skill segnalano errore e suggeriscono `python claude-flow/scripts/migrate-profile-split.py --apply` (per profili in formato legacy) oppure `/sdlc-profile-setup` (per nuovi progetti).
```

- [ ] **Step 4: Aggiornare la sezione "Auto-Maintenance"**

Trova la sezione `### Auto-Maintenance` (intorno alla riga 94). Sostituiscila con:

```markdown
### Auto-Maintenance

`sdlc-analyzer` aggiorna automaticamente **solo `PROFILE.json`** quando rileva nuove convenzioni, dipendenze o termini di dominio durante la gap analysis. `CONST.json` è policy stabile e va modificato manualmente dall'utente.

Le modifiche a PROFILE.json vengono committate in questo repo. Quando una skill rileva che il codice viola un principio CONST, lo segnala come finding nel `PLAN.md` sotto la sezione "Violazioni principi CONST rilevate", NON modifica CONST.json.
```

- [ ] **Step 5: Aggiornare la sezione "Schema Validation"**

Trova la sezione `## Schema Validation` (in fondo al file, riga ~128). Sostituiscila con:

```markdown
## Schema Validation

I file di costituzione sono validati contro JSON Schema Draft 2020-12:
- `CONST.json` → `const-schema.json`
- `PROFILE.json` → `profile-schema.json`

Le SDLC skills validano al caricamento e segnalano gli errori con il path del campo invalido prima di procedere.
```

- [ ] **Step 6: Verifica finale**

Run:
```bash
grep -n "profile.json\|CONST.json\|PROFILE.json" "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/README.md" | head -20
```

Expected: niente menzioni di `constitution/profile.json` (singolare); molte menzioni di `CONST.json` e `PROFILE.json`.

---

## Task 12: Aggiornare `claude-flow/SDLC_SKILLS_DOCUMENTATION.md`

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/SDLC_SKILLS_DOCUMENTATION.md`

- [ ] **Step 1: Cercare le menzioni di `profile.json` (singolare) e capire dove sono**

Run:
```bash
grep -n "profile.json\|constitution\|inviolable" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/SDLC_SKILLS_DOCUMENTATION.md" | head -30
```

Salva l'output. Per ogni occorrenza:

- [ ] **Step 2: Sostituire ogni menzione di `constitution/profile.json` con `constitution/CONST.json + PROFILE.json`**

Usa Edit (o sed) per ogni occorrenza. Esempi tipici di sostituzione:
- `constitution/profile.json` → `constitution/CONST.json + PROFILE.json`
- `profile.json` (in contesto di SDLC) → `CONST.json + PROFILE.json`
- "il profilo" → "i file di costituzione (CONST + PROFILE)" dove rilevante

- [ ] **Step 3: Aggiungere una nuova sezione/sottosezione "Constitution Files (CONST + PROFILE)"**

Se non esiste già una sezione che descrive cos'è il profilo, aggiungila (vicino alla descrizione generale del workflow). Suggerimento di contenuto (adatta al tono del file esistente):

```markdown
### Constitution Files: CONST + PROFILE

Ogni progetto ha due file nella folder `constitution/`:

- **`CONST.json`** — Principi e standard di archetipo (OWASP, WCAG, test coverage, code style, git workflow, architectural patterns). Policy stabile, gestita manualmente.
- **`PROFILE.json`** — Dettagli specifici del progetto (tech stack, repositories, dominio, design system, glossario). Auto-aggiornato da `sdlc-analyzer`.

Tutte le 9 skill SDLC caricano entrambi i file all'avvio. CONST funziona come vincolo per ogni output (PLAN, TASKS, REVIEW, fix), PROFILE come "lingua" del progetto.

Per migrare un profilo legacy (formato `profile.json` singolare), eseguire `python claude-flow/scripts/migrate-profile-split.py --apply`.
```

- [ ] **Step 4: Verifica finale**

Run:
```bash
grep -n "constitution/profile.json" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/SDLC_SKILLS_DOCUMENTATION.md" || echo "OK: no legacy references"
```

Expected: `OK: no legacy references`

Run:
```bash
grep -cE "CONST\.json|PROFILE\.json" "C:/Users/davmelis/Documents/MyGitHub/claude-flow/SDLC_SKILLS_DOCUMENTATION.md"
```

Expected: numero > 0 (le nuove menzioni esistono).

---

**Fine FASE 4.** Stato: documentazione aggiornata. **I file sono pronti per il commit (utente).**

Comando suggerito:
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" add README.md
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" commit -m "docs: document CONST + PROFILE split in constitution/"

git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" add SDLC_SKILLS_DOCUMENTATION.md
git -C "C:/Users/davmelis/Documents/MyGitHub/claude-flow" commit -m "docs: update SDLC docs to reflect CONST + PROFILE split"
```

---

# FASE 5 — Migrazione effettiva + sync + smoke test

## Task 13: Dry-run dello script di migrazione sul banca-agente reale

**Pre-requisito:** L'utente deve aver committato tutti i lavori delle Fasi 1-4 (oppure averli stashati). Verifica:

- [ ] **Step 1: Verifica working tree di `deloitte-profiles`**

Run:
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" status --short
```

Expected: vuoto (working tree pulito) o solo `?? const-schema.json` se l'utente ha aggiunto lo schema ma non ancora committato.

**Se ci sono modifiche unstaged**: chiedi all'utente di committarle o stashalle prima di proseguire (lo script di migrazione rifiuterà di applicare su working tree dirty per safety).

- [ ] **Step 2: Eseguire il dry-run**

Run:
```bash
python "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py"
```

Expected output:
```
[DRY-RUN] Scansiono C:\Users\davmelis\Documents\MyGitHub\deloitte-profiles/*/constitution/profile.json

[DRY-RUN] banca-agente/constitution/
  read  profile.json (14316 bytes)
  extract conventions.inviolable_principles → CONST.inviolable_principles (3 principi: security, accessibility, responsiveness)
  add default sections from template (quality_standards, code_style, git_workflow, architectural_patterns, data_privacy)
  write CONST.json
  remove conventions.inviolable_principles from profile.json
  git mv profile.json PROFILE.json

[DRY-RUN] Summary: 1 profili scansionati, 1 da migrare, 0 errori.

[DRY-RUN] Run with --apply to execute.

[DRY-RUN] Suggested commit after apply:
[DRY-RUN]   git -C C:\Users\davmelis\Documents\MyGitHub\deloitte-profiles add -A
[DRY-RUN]   git -C C:\Users\davmelis\Documents\MyGitHub\deloitte-profiles commit -m "refactor: split profile.json into CONST.json + PROFILE.json"
```

**Se l'output non corrisponde**, debugga prima di applicare.

---

## Task 14: Applicare lo script di migrazione

- [ ] **Step 1: Eseguire `--apply`**

Run:
```bash
python "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/migrate-profile-split.py" --apply
```

Expected output (parziale):
```
[APPLY] Scansiono ...
[APPLY] banca-agente/constitution/
  read  profile.json (14316 bytes)
  extract conventions.inviolable_principles → CONST.inviolable_principles (3 principi: ...)
  ...
[APPLY] Summary: 1 profili scansionati, 1 da migrare, 0 errori.

[APPLY] Done.
[APPLY] IMPORTANT: Rivedi a mano CONST.json appena generato ...
[APPLY] Commit suggerito:
[APPLY]   git -C ... add -A
[APPLY]   git -C ... commit -m "refactor: split profile.json into CONST.json + PROFILE.json"
```

- [ ] **Step 2: Verifica manuale che i file siano stati generati correttamente**

Run:
```bash
ls "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/constitution/"
```

Expected:
```
CONST.json
PROFILE.json
```

(Nessun `profile.json`.)

- [ ] **Step 3: Validare il CONST.json generato (struttura + contenuto)**

Run:
```bash
python -c "
import json
const = json.load(open('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/constitution/CONST.json'))
assert 'inviolable_principles' in const
assert 'security' in const['inviolable_principles']
assert 'accessibility' in const['inviolable_principles']
assert 'responsiveness' in const['inviolable_principles']
assert 'data_privacy' in const['inviolable_principles']  # aggiunto dal template
assert const['inviolable_principles']['security']['rule'].startswith('Tutto il codice deve rispettare')
assert 'quality_standards' in const
assert 'code_style' in const
assert 'git_workflow' in const
assert 'architectural_patterns' in const
print('OK: CONST.json struttura e contenuto validi')
"
```

Expected: `OK: CONST.json struttura e contenuto validi`

- [ ] **Step 4: Validare il PROFILE.json generato (no inviolable_principles, resto invariato)**

Run:
```bash
python -c "
import json
prof = json.load(open('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/constitution/PROFILE.json'))
assert 'project' in prof
assert prof['project']['name'] == 'Banca Agente'
assert 'tech_stack' in prof
assert 'conventions' in prof
assert 'inviolable_principles' not in prof['conventions'], 'inviolable_principles non rimosso!'
assert 'design_system' in prof
assert 'domain' in prof
print('OK: PROFILE.json struttura valida, inviolable_principles correttamente rimosso')
"
```

Expected: `OK: PROFILE.json struttura valida, inviolable_principles correttamente rimosso`

- [ ] **Step 5: Verifica che git tracci correttamente la rename**

Run:
```bash
git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" status --short
```

Expected (approssimativo):
```
?? banca-agente/constitution/CONST.json
R  banca-agente/constitution/profile.json -> banca-agente/constitution/PROFILE.json
```

(Il file viene RIDENOMINATO da git mv, non aggiunto come nuovo. Le modifiche di contenuto in PROFILE.json appaiono come edit.)

- [ ] **Step 6: NON committare automaticamente — passa la mano all'utente**

Stampa a video:

```
Migrazione applicata. I file sono pronti per il commit.

Comando suggerito:
  git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" add -A
  git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" commit -m "refactor: split profile.json into CONST.json + PROFILE.json"
  git -C "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles" push origin main

L'utente decide quando committare e pushare.
```

---

## Task 15: Sync delle skill installate localmente

**Pre-requisito:** L'utente ha committato anche le modifiche al repo `claude-flow` (Fasi 1-4).

- [ ] **Step 1: Eseguire dry-run dello sync**

Run:
```bash
bash "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/sync-installed.sh"
```

Expected: lista delle operazioni di sync (skill + agents).

- [ ] **Step 2: Eseguire apply dello sync**

Run:
```bash
bash "C:/Users/davmelis/Documents/MyGitHub/claude-flow/scripts/sync-installed.sh" --apply
```

Expected: tutte le `~/.claude/skills/sdlc-*` aggiornate alla nuova versione (con il loader CONST + PROFILE).

- [ ] **Step 3: Verifica che le skill installate abbiano la nuova sezione**

Run:
```bash
for f in sdlc-reviewer sdlc-clarify sdlc-executor sdlc-debug sdlc-updater sdlc-estimator sdlc-progress-report sdlc-analyzer; do
  if grep -q "Caricamento contesto progetto" "C:/Users/davmelis/.claude/skills/$f/SKILL.md"; then
    echo "OK: $f"
  else
    echo "FAIL: $f mancante"
  fi
done
```

Expected: 8 righe "OK".

(`sdlc-profile-setup` non ha la sezione standard, è l'eccezione — vedi Task 10 step 1.)

---

## Task 16: Smoke test post-rollout

Verifica che almeno una skill SDLC riesca a caricare CONST + PROFILE senza errori. Scelgo `sdlc-progress-report` perché è non-distruttiva (legge soltanto) ed è una delle skill "solo loader".

- [ ] **Step 1: Verifica che esista almeno un BR in `plans/in-progress/` o `plans/done/` di banca-agente**

Run:
```bash
ls -d "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/plans/in-progress"/*/ "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/plans/done"/*/ 2>/dev/null | head -5
```

Se vuoto, lo smoke test richiede un BR di test. In tal caso, skip Step 2-3 e fai solo lo Step 4 (verifica del loader in isolamento).

- [ ] **Step 2: Invoca `/sdlc-progress-report` (manualmente, da Claude Code)**

L'utente esegue manualmente in una sessione Claude Code:
```
/sdlc-progress-report
```

Expected behavior:
- La skill carica CONST.json + PROFILE.json senza errori
- Mostra lo stato avanzamento del BR scelto
- Nessun errore di tipo "profile.json not found" o "JSON parse error"

- [ ] **Step 3: Verifica errori loader (smoke negativo)**

Per verificare che gli errori del loader funzionino, temporaneamente sposta CONST.json:

```bash
mv "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/constitution/CONST.json" /tmp/CONST.json.bak
```

Invoca di nuovo `/sdlc-progress-report` manualmente. Expected: messaggio di errore esplicito tipo "Il profilo `banca-agente` non ha CONST.json. Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply`...".

Ripristina:
```bash
mv /tmp/CONST.json.bak "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/banca-agente/constitution/CONST.json"
```

- [ ] **Step 4: Verifica del loader in isolamento (se non hai BR per smoke test reale)**

Esegui questo Python script di simulazione:

```bash
python -c "
import json
import sys
from pathlib import Path

profiles_repo = Path('C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles')
profilo = 'banca-agente'

const_path = profiles_repo / profilo / 'constitution' / 'CONST.json'
profile_path = profiles_repo / profilo / 'constitution' / 'PROFILE.json'
legacy_path = profiles_repo / profilo / 'constitution' / 'profile.json'

if legacy_path.exists():
    print('FAIL: profile.json legacy ancora presente')
    sys.exit(1)
if not const_path.exists():
    print('FAIL: CONST.json mancante')
    sys.exit(1)
if not profile_path.exists():
    print('FAIL: PROFILE.json mancante')
    sys.exit(1)

const = json.loads(const_path.read_text())
prof = json.loads(profile_path.read_text())

print(f'OK: CONST.json caricato — {len(const.get(\"inviolable_principles\", {}))} principi inviolabili')
print(f'OK: PROFILE.json caricato — progetto: {prof[\"project\"][\"name\"]}')
print(f'OK: PROFILE.json non contiene inviolable_principles: {\"inviolable_principles\" not in prof.get(\"conventions\", {})}')
"
```

Expected:
```
OK: CONST.json caricato — 4 principi inviolabili
OK: PROFILE.json caricato — progetto: Banca Agente
OK: PROFILE.json non contiene inviolable_principles: True
```

---

**Fine FASE 5.** Stato: refactor completo, migrazione applicata, sync delle skill locali, smoke test passato.

**I commit dei due repo (deloitte-profiles + claude-flow) sono lasciati all'utente.**

---

## Rollback (in caso di problemi)

Se uno qualsiasi degli step della Fase 5 fallisce in modo non recuperabile:

1. **Repristino deloitte-profiles:**
   ```bash
   cd "C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles"
   git restore --source=HEAD --staged --worktree banca-agente/constitution/
   git clean -fd banca-agente/constitution/
   ```

2. **Ripristino claude-flow:**
   ```bash
   cd "C:/Users/davmelis/Documents/MyGitHub/claude-flow"
   git revert <hash-del-commit-refactor-skill>  # se già committato
   # oppure
   git restore skills/sdlc-*/SKILL.md  # se non committato
   ```

3. **Re-sync delle skill locali alla versione pre-refactor:**
   ```bash
   bash scripts/sync-installed.sh --apply
   ```

Stato post-rollback: identico al pre-refactor.

---

## Riferimenti

- Design spec: `docs/superpowers/specs/2026-05-19-sdlc-profile-const-split-design.md`
- Profilo attuale (pre-migrazione): `deloitte-profiles/banca-agente/constitution/profile.json`
- Schema attuale: `deloitte-profiles/profile-schema.json`
- Pattern script: `claude-flow/scripts/migrate-sdlc-naming.sh`, `claude-flow/scripts/sync-installed.sh`, `claude-flow/scripts/aggregate-progress.py`
- Documentazione skill SDLC: `claude-flow/SDLC_SKILLS_DOCUMENTATION.md`
