# SDLC Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rinominare le skill della pipeline da `br-*` a `sdlc-*` e i file di output da `REVIEW_BR.md`/`GAP_REPORT_BR.md`/`PIANO_IMPLEMENTAZIONE_BR.md` a `CLARIFY.md`/`PLAN.md`/`TASKS.md`, mantenendo invariati trigger italiani e terminologia di dominio "BR".

**Architecture:** Refactor atomico in due fasi. Fase 1 crea due script bash riusabili (`migrate-sdlc-naming.sh` per i profili, `sync-installed.sh` per `~/.claude/`). Fase 2 esegue il rename completo del repo `claude-flow` (`git mv` cartelle + edit testuali con verifica grep dopo ogni skill). Poi sync delle copie installate, migrazione dei BR in-progress in `deloitte-profiles`, smoke test finale.

**Tech Stack:** Bash, Git (`git mv` per preservare history), grep, find. Niente nuove dipendenze runtime.

**Spec di riferimento:** `docs/superpowers/specs/2026-05-18-sdlc-rename-design.md`

**Repo coinvolti:**
- `C:/Users/davmelis/Documents/MyGitHub/claude-flow` (skill, agent, script, README, doc plan)
- `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles` (rename dei file BR in-progress)

**Vincoli operativi:**
- Niente attribution `Co-Authored-By: Claude` nei commit (esplicitamente richiesto dall'utente)
- Push su entrambi i repo dopo i commit
- Mantenere invariati: trigger italiani in `~/.claude/CLAUDE.md`, terminologia di dominio "BR" nei testi, cartelle dei profili (`plans/in-progress/<data>_<nome>/`), `PROGRESSO.md`, contenuto di `docs/superpowers/specs/` e `plans/` storici

---

## Mappa file/cartelle

### Da creare nel repo `claude-flow`

- `scripts/migrate-sdlc-naming.sh` — script bash per rinominare i file BR nei profili
- `scripts/sync-installed.sh` — script bash per sincronizzare `skills/` e `agents/` verso `~/.claude/`

### Da rinominare (`git mv`) nel repo `claude-flow`

**Skill folders** (9):
- `skills/br-reviewer/` → `skills/sdlc-reviewer/`
- `skills/br-clarify/` → `skills/sdlc-clarify/`
- `skills/br-analyzer/` → `skills/sdlc-analyzer/`
- `skills/br-executor/` → `skills/sdlc-executor/`
- `skills/br-updater/` → `skills/sdlc-updater/`
- `skills/br-debug/` → `skills/sdlc-debug/`
- `skills/br-progress-report/` → `skills/sdlc-progress-report/`
- `skills/br-estimator/` → `skills/sdlc-estimator/`
- `skills/br-profile-setup/` → `skills/sdlc-profile-setup/`

**Agent files** (5):
- `agents/br-codebase-explorer.md` → `agents/sdlc-codebase-explorer.md`
- `agents/br-estimation-analyst.md` → `agents/sdlc-estimation-analyst.md`
- `agents/br-estimation-historian.md` → `agents/sdlc-estimation-historian.md`
- `agents/br-estimation-scenario.md` → `agents/sdlc-estimation-scenario.md`
- `agents/br-verifier.md` → `agents/sdlc-verifier.md`

### Da modificare (contenuto) nel repo `claude-flow`

- 9 `SKILL.md` (uno per ogni skill rinominato): frontmatter + cross-reference + path file output + terminologia colloquiale
- 5 agent `.md`: frontmatter + cross-reference + eventuali path file output
- `README.md`: sezione installazione, snippet trigger, eventuale sezione "Migrazione naming legacy"

### Da NON modificare nel repo `claude-flow`

- `docs/superpowers/specs/2026-05-18-sdlc-rename-design.md` (spec corrente, gia' usa nomi nuovi)
- `docs/superpowers/specs/*-design.md` e `docs/superpowers/plans/*.md` (fossili storici, accuratezza preservata)

### File rename nel repo `deloitte-profiles`

Eseguiti dallo script `migrate-sdlc-naming.sh`:
- `banca-agente/plans/in-progress/2026-05-04_monitoring/REVIEW_BR.md` → `CLARIFY.md`
- `banca-agente/plans/in-progress/2026-05-04_monitoring/REVIEW_BR.docx` → `CLARIFY.docx`
- `banca-agente/plans/in-progress/2026-05-04_monitoring/GAP_REPORT_BR.md` → `PLAN.md`
- `banca-agente/plans/in-progress/2026-05-04_monitoring/PIANO_IMPLEMENTAZIONE_BR.md` → `TASKS.md`
- + qualsiasi altro BR in-progress trovato dallo script (scope: `*/plans/{in-progress,todo}/**/`)

---

## Mapping sostituzioni testuali (cheat sheet)

Da applicare in ogni file che lo richiede.

### Cross-reference skill/agent (case-sensitive)

| sed pattern | da | a |
|---|---|---|
| `br-reviewer` | `br-reviewer` | `sdlc-reviewer` |
| `br-clarify` | `br-clarify` | `sdlc-clarify` |
| `br-analyzer` | `br-analyzer` | `sdlc-analyzer` |
| `br-executor` | `br-executor` | `sdlc-executor` |
| `br-updater` | `br-updater` | `sdlc-updater` |
| `br-debug` | `br-debug` | `sdlc-debug` |
| `br-progress-report` | `br-progress-report` | `sdlc-progress-report` |
| `br-estimator` | `br-estimator` | `sdlc-estimator` |
| `br-profile-setup` | `br-profile-setup` | `sdlc-profile-setup` |
| `br-codebase-explorer` | `br-codebase-explorer` | `sdlc-codebase-explorer` |
| `br-estimation-analyst` | `br-estimation-analyst` | `sdlc-estimation-analyst` |
| `br-estimation-historian` | `br-estimation-historian` | `sdlc-estimation-historian` |
| `br-estimation-scenario` | `br-estimation-scenario` | `sdlc-estimation-scenario` |
| `br-verifier` | `br-verifier` | `sdlc-verifier` |

### Path file di output

| da | a |
|---|---|
| `REVIEW_BR.md` | `CLARIFY.md` |
| `REVIEW_BR.docx` | `CLARIFY.docx` |
| `GAP_REPORT_BR.md` | `PLAN.md` |
| `PIANO_IMPLEMENTAZIONE_BR.md` | `TASKS.md` |

### Terminologia colloquiale (riscrittura manuale, attenzione al contesto)

Queste richiedono giudizio (non sostituibili in cieco):
- "gap report" / "gap analysis" (riferito al file) → "PLAN" / "file PLAN"
- "piano di implementazione" / "piano sviluppo" (riferito al file) → "TASKS" / "file TASKS"
- "review" (sostantivo riferito al file) → "CLARIFY" / "file CLARIFY"
- "review" (verbo "revieware") → resta invariato
- "il gap report" → "il PLAN"
- "Sezione Generazione REVIEW_BR.docx" (heading) → "Sezione Generazione CLARIFY.docx"

---

## Fase 1 — Script tools

### Task 1: Crea `scripts/migrate-sdlc-naming.sh`

**Files:**
- Create: `scripts/migrate-sdlc-naming.sh`

- [ ] **Step 1: Crea lo script**

```bash
cat > scripts/migrate-sdlc-naming.sh <<'EOF'
#!/usr/bin/env bash
# migrate-sdlc-naming.sh
# Rinomina i file BR legacy (REVIEW_BR/GAP_REPORT_BR/PIANO_IMPLEMENTAZIONE_BR) ai nomi nuovi
# (CLARIFY/PLAN/TASKS) nelle cartelle plans/{in-progress,todo}/ del repo profili.
#
# Default: dry-run. Usa --apply per eseguire i git mv.
# Default root: C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
# Override con --root <path>.

set -euo pipefail

DEFAULT_ROOT="C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles"
ROOT="$DEFAULT_ROOT"
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --root) ROOT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--apply] [--root <path>]"
      echo "  Default root: $DEFAULT_ROOT"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "ERROR: root directory not found: $ROOT" >&2
  exit 1
fi

declare -A MAP=(
  ["REVIEW_BR.md"]="CLARIFY.md"
  ["REVIEW_BR.docx"]="CLARIFY.docx"
  ["GAP_REPORT_BR.md"]="PLAN.md"
  ["PIANO_IMPLEMENTAZIONE_BR.md"]="TASKS.md"
)

PREFIX="[DRY-RUN]"
[[ $APPLY -eq 1 ]] && PREFIX="[APPLY]"

echo "$PREFIX Scanning $ROOT/*/plans/{in-progress,todo}/"
echo ""

total_renames=0
total_brs=0
conflict_found=0

# Cerca tutte le directory BR (cartelle figlie dirette di plans/in-progress/ o plans/todo/)
while IFS= read -r br_dir; do
  br_renames=()

  for old in "${!MAP[@]}"; do
    new="${MAP[$old]}"
    old_path="$br_dir/$old"
    new_path="$br_dir/$new"

    if [[ -f "$old_path" && -f "$new_path" ]]; then
      echo "  CONFLICT in $br_dir:" >&2
      echo "    both $old and $new exist. Resolve manually." >&2
      conflict_found=1
      continue
    fi

    if [[ -f "$old_path" ]]; then
      br_renames+=("$old → $new")
    fi
  done

  if [[ ${#br_renames[@]} -gt 0 ]]; then
    total_brs=$((total_brs + 1))
    rel="${br_dir#$ROOT/}"
    echo "  $rel/"
    for r in "${br_renames[@]}"; do
      echo "    $r"
      total_renames=$((total_renames + 1))
      if [[ $APPLY -eq 1 ]]; then
        old="${r% → *}"
        new="${r#* → }"
        (cd "$ROOT" && git mv "${rel}/${old}" "${rel}/${new}")
      fi
    done
  fi
done < <(find "$ROOT" -type d \( -path "*/plans/in-progress/*" -o -path "*/plans/todo/*" \) -mindepth 4 -maxdepth 4)

echo ""

if [[ $conflict_found -eq 1 ]]; then
  echo "ERROR: conflicts found. Resolve manually before running with --apply." >&2
  exit 2
fi

if [[ $total_renames -eq 0 ]]; then
  echo "Nothing to do. All files already use the new naming."
  exit 0
fi

echo "$total_renames rename operation(s) on $total_brs BR(s)."
if [[ $APPLY -eq 0 ]]; then
  echo "Run with --apply to execute. Then commit and push the deloitte-profiles repo."
else
  echo "Done. Now commit and push the deloitte-profiles repo."
  echo ""
  echo "WARNING: references to old file names inside PROGRESSO.md or other markdown files"
  echo "are NOT modified. Inspect manually if needed."
fi
EOF
chmod +x scripts/migrate-sdlc-naming.sh
```

- [ ] **Step 2: Verifica che lo script sia eseguibile**

Run: `ls -l scripts/migrate-sdlc-naming.sh`
Expected: il file esiste, permessi `-rwxr-xr-x` (o equivalente Windows)

---

### Task 2: Test smoke di `migrate-sdlc-naming.sh` su filesystem mockup

**Files:**
- Use: `scripts/migrate-sdlc-naming.sh` (gia' creato in Task 1)

- [ ] **Step 1: Crea un repo mockup temporaneo**

```bash
MOCK_ROOT=$(mktemp -d)
mkdir -p "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo"
cd "$MOCK_ROOT" && git init -q test-profile
touch "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/REVIEW_BR.md"
touch "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/REVIEW_BR.docx"
touch "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/GAP_REPORT_BR.md"
touch "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/PIANO_IMPLEMENTAZIONE_BR.md"
(cd "$MOCK_ROOT/test-profile" && git add -A && git -c user.email=t@t -c user.name=t commit -q -m "init")
echo "Mock root: $MOCK_ROOT"
```

- [ ] **Step 2: Esegui dry-run**

Run: `./scripts/migrate-sdlc-naming.sh --root "$MOCK_ROOT"`
Expected output (esempio):
```
[DRY-RUN] Scanning <MOCK_ROOT>/*/plans/{in-progress,todo}/

  test-profile/plans/in-progress/2026-01-01_demo/
    REVIEW_BR.md → CLARIFY.md
    REVIEW_BR.docx → CLARIFY.docx
    GAP_REPORT_BR.md → PLAN.md
    PIANO_IMPLEMENTAZIONE_BR.md → TASKS.md

4 rename operation(s) on 1 BR(s).
Run with --apply to execute. ...
```

- [ ] **Step 3: Esegui --apply e verifica**

Run: `./scripts/migrate-sdlc-naming.sh --root "$MOCK_ROOT" --apply`
Run: `ls "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/"`
Expected: solo `CLARIFY.md`, `CLARIFY.docx`, `PLAN.md`, `TASKS.md` (nessun `*_BR.*`)

- [ ] **Step 4: Verifica idempotenza**

Run: `./scripts/migrate-sdlc-naming.sh --root "$MOCK_ROOT"`
Expected output finale: `Nothing to do. All files already use the new naming.`

- [ ] **Step 5: Verifica conflict detection**

```bash
touch "$MOCK_ROOT/test-profile/plans/in-progress/2026-01-01_demo/REVIEW_BR.md"
./scripts/migrate-sdlc-naming.sh --root "$MOCK_ROOT"
```
Expected: errore `CONFLICT ... both REVIEW_BR.md and CLARIFY.md exist`, exit code 2

- [ ] **Step 6: Cleanup mockup**

Run: `rm -rf "$MOCK_ROOT"`

---

### Task 3: Crea `scripts/sync-installed.sh`

**Files:**
- Create: `scripts/sync-installed.sh`

- [ ] **Step 1: Crea lo script**

```bash
cat > scripts/sync-installed.sh <<'EOF'
#!/usr/bin/env bash
# sync-installed.sh
# Sincronizza le skill sdlc-* dal repo claude-flow verso ~/.claude/skills/ e ~/.claude/agents/.
# Rimuove le vecchie installazioni br-* per evitare skill zombie.
#
# Default: dry-run. Usa --apply per eseguire.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--apply]"
      echo "  Source: $REPO_ROOT/{skills,agents}/sdlc-*"
      echo "  Target: $CLAUDE_HOME/{skills,agents}/"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PREFIX="[DRY-RUN]"
RUN=":"
[[ $APPLY -eq 1 ]] && { PREFIX="[APPLY]"; RUN=""; }

echo "$PREFIX Sync from $REPO_ROOT → $CLAUDE_HOME"
echo ""

# 1. Cleanup vecchie installazioni br-*
echo "Cleanup old br-* installations:"
for d in "$CLAUDE_HOME"/skills/br-*; do
  [[ -d "$d" ]] || continue
  echo "  rm -rf $d"
  $RUN rm -rf "$d"
done
for f in "$CLAUDE_HOME"/agents/br-*.md; do
  [[ -f "$f" ]] || continue
  echo "  rm -f $f"
  $RUN rm -f "$f"
done

echo ""
echo "Install new sdlc-* skills:"
for d in "$REPO_ROOT"/skills/sdlc-*; do
  [[ -d "$d" ]] || continue
  name=$(basename "$d")
  echo "  cp -r $d → $CLAUDE_HOME/skills/$name"
  $RUN cp -r "$d" "$CLAUDE_HOME/skills/"
done

echo ""
echo "Install new sdlc-* agents:"
for f in "$REPO_ROOT"/agents/sdlc-*.md; do
  [[ -f "$f" ]] || continue
  name=$(basename "$f")
  echo "  cp $f → $CLAUDE_HOME/agents/$name"
  $RUN cp "$f" "$CLAUDE_HOME/agents/"
done

echo ""
if [[ $APPLY -eq 0 ]]; then
  echo "Run with --apply to execute."
else
  echo "Done. Verify with: ls $CLAUDE_HOME/skills/ | grep -E '^(br|sdlc)-'"
  echo ""
  echo "REMINDER: update ~/.claude/CLAUDE.md trigger sections manually"
  echo "  (change '# br-X' → '# sdlc-X' and 'skill: \"br-X\"' → 'skill: \"sdlc-X\"')"
fi
EOF
chmod +x scripts/sync-installed.sh
```

- [ ] **Step 2: Verifica che lo script sia eseguibile**

Run: `ls -l scripts/sync-installed.sh`
Expected: il file esiste, eseguibile

---

### Task 4: Test smoke di `sync-installed.sh` (solo dry-run, non --apply)

**Files:**
- Use: `scripts/sync-installed.sh`

- [ ] **Step 1: Esegui dry-run (NON --apply, le skill sdlc-* non esistono ancora)**

Run: `./scripts/sync-installed.sh`
Expected: lo script stampa il cleanup di `~/.claude/skills/br-*` (9 cartelle) e `~/.claude/agents/br-*.md` (5 file), ma la sezione "Install new sdlc-*" e' vuota perche' le cartelle `sdlc-*` non esistono ancora nel repo. Nessuna modifica al filesystem.

**Nota:** lo script verra' eseguito davvero (con `--apply`) solo in Task 21, dopo che le skill saranno rinominate.

---

### Task 5: Commit script

**Files:**
- Stage: `scripts/migrate-sdlc-naming.sh`, `scripts/sync-installed.sh`

- [ ] **Step 1: Stage e commit (senza attribution)**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add scripts/migrate-sdlc-naming.sh scripts/sync-installed.sh
git commit -m "feat(scripts): add sdlc rename migration and sync helpers

- migrate-sdlc-naming.sh: rename BR legacy files (REVIEW_BR/GAP_REPORT_BR/PIANO_IMPLEMENTAZIONE_BR) to CLARIFY/PLAN/TASKS in deloitte-profiles in-progress BRs (dry-run default, --apply to execute)
- sync-installed.sh: sync sdlc-* skills/agents from repo to ~/.claude/, removing legacy br-* installations (dry-run default, --apply to execute)"
```

**Importante:** NON aggiungere `Co-Authored-By: Claude` al messaggio.

- [ ] **Step 2: Verifica il commit**

Run: `git log -1 --format='%s%n---%n%b'`
Expected: il messaggio sopra, senza linee `Co-Authored-By:`.

---

## Fase 2 — Rename file system nel repo `claude-flow`

### Task 6: `git mv` agent files

**Files:**
- Rename: `agents/br-codebase-explorer.md` → `agents/sdlc-codebase-explorer.md`
- Rename: `agents/br-estimation-analyst.md` → `agents/sdlc-estimation-analyst.md`
- Rename: `agents/br-estimation-historian.md` → `agents/sdlc-estimation-historian.md`
- Rename: `agents/br-estimation-scenario.md` → `agents/sdlc-estimation-scenario.md`
- Rename: `agents/br-verifier.md` → `agents/sdlc-verifier.md`

- [ ] **Step 1: Esegui git mv su tutti gli agent**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git mv agents/br-codebase-explorer.md agents/sdlc-codebase-explorer.md
git mv agents/br-estimation-analyst.md agents/sdlc-estimation-analyst.md
git mv agents/br-estimation-historian.md agents/sdlc-estimation-historian.md
git mv agents/br-estimation-scenario.md agents/sdlc-estimation-scenario.md
git mv agents/br-verifier.md agents/sdlc-verifier.md
```

- [ ] **Step 2: Verifica le rinomine**

Run: `ls agents/`
Expected: 5 file con prefisso `sdlc-`, nessuno con prefisso `br-`.

Run: `git status --short agents/`
Expected: 5 righe `R  agents/br-X.md -> agents/sdlc-X.md` (R = rename tracked).

---

### Task 7: `git mv` skill folders

**Files:**
- Rename: `skills/br-{reviewer,clarify,analyzer,executor,updater,debug,progress-report,estimator,profile-setup}/` → `skills/sdlc-*/`

- [ ] **Step 1: Esegui git mv su tutte le 9 cartelle skill**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git mv skills/br-reviewer skills/sdlc-reviewer
git mv skills/br-clarify skills/sdlc-clarify
git mv skills/br-analyzer skills/sdlc-analyzer
git mv skills/br-executor skills/sdlc-executor
git mv skills/br-updater skills/sdlc-updater
git mv skills/br-debug skills/sdlc-debug
git mv skills/br-progress-report skills/sdlc-progress-report
git mv skills/br-estimator skills/sdlc-estimator
git mv skills/br-profile-setup skills/sdlc-profile-setup
```

- [ ] **Step 2: Verifica le rinomine**

Run: `ls skills/`
Expected: 9 cartelle con prefisso `sdlc-`, nessuna con prefisso `br-`.

Run: `git status --short skills/`
Expected: 9 righe `R  skills/br-X/SKILL.md -> skills/sdlc-X/SKILL.md` (R = rename tracked).

---

## Fase 3 — Edit contenuto delle skill e degli agent

**Pattern di edit comune (applicabile a tutti i SKILL.md e agent):**

Per ogni file, usare il `Edit` tool con `replace_all: true` per i pattern univoci. Ordine consigliato:

1. **Frontmatter `name:`** → `Edit` con `old_string: "name: br-X"`, `new_string: "name: sdlc-X"`
2. **Cross-reference** (le 14 stringhe della cheat sheet sopra) → `Edit` con `replace_all: true` per ognuna
3. **Path file output** (`REVIEW_BR.md`/`REVIEW_BR.docx`/`GAP_REPORT_BR.md`/`PIANO_IMPLEMENTAZIONE_BR.md`) → `Edit` con `replace_all: true`
4. **Terminologia colloquiale** → `Read` la skill, identifica le occorrenze, applica `Edit` mirate (manuale, una alla volta)

Dopo ogni file editato: `grep` di verifica deve restituire 0 match dei pattern vecchi nella skill specifica.

---

### Task 8: Edit dei 5 agent files

**Files:**
- Modify: `agents/sdlc-codebase-explorer.md`
- Modify: `agents/sdlc-estimation-analyst.md`
- Modify: `agents/sdlc-estimation-historian.md`
- Modify: `agents/sdlc-estimation-scenario.md`
- Modify: `agents/sdlc-verifier.md`

- [ ] **Step 1: Leggi ogni agent e mappa le sostituzioni**

Per ogni agent, esegui `Read` per identificare tutte le occorrenze di pattern vecchi (frontmatter `name:`, riferimenti a `br-*` skill, path file output, terminologia).

Esempio per `agents/sdlc-estimation-historian.md`:
- Frontmatter: `name: br-estimation-historian` → `name: sdlc-estimation-historian`
- Eventuale path file: `PIANO_IMPLEMENTAZIONE_BR.md` → `TASKS.md`
- Eventuali cross-ref `br-estimator` → `sdlc-estimator`

- [ ] **Step 2: Applica le edit con il tool Edit**

Per ogni pattern usa `Edit` con `replace_all: true`. Esempio:

```
Edit agents/sdlc-estimation-historian.md:
  old_string: "name: br-estimation-historian"
  new_string: "name: sdlc-estimation-historian"
```

```
Edit agents/sdlc-estimation-historian.md:
  old_string: "br-estimator"
  new_string: "sdlc-estimator"
  replace_all: true
```

```
Edit agents/sdlc-estimation-historian.md:
  old_string: "PIANO_IMPLEMENTAZIONE_BR.md"
  new_string: "TASKS.md"
  replace_all: true
```

Ripeti per tutti i 5 agent.

- [ ] **Step 3: Verifica con grep**

Run:
```bash
grep -E "br-(reviewer|clarify|analyzer|executor|updater|debug|progress-report|estimator|profile-setup|codebase-explorer|estimation|verifier)|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." agents/sdlc-*.md
```
Expected: 0 match.

---

### Task 9: Edit `skills/sdlc-reviewer/SKILL.md`

**Files:**
- Modify: `skills/sdlc-reviewer/SKILL.md`

Conteggio pre-modifica: 12 occorrenze path file (REVIEW_BR/REVIEW_BR.docx) + 14 cross-reference.

- [ ] **Step 1: Read del file per mappare le edit**

Read `skills/sdlc-reviewer/SKILL.md` interamente. Identifica:
- Frontmatter `name: br-reviewer` → `sdlc-reviewer`
- Tutte le cross-reference `br-*` da sostituire
- Tutti i path `REVIEW_BR.md`, `REVIEW_BR.docx`
- Riferimenti testuali alla "review" del br (sostantivo) → da valutare in contesto

- [ ] **Step 2: Frontmatter**

```
Edit skills/sdlc-reviewer/SKILL.md:
  old_string: "name: br-reviewer"
  new_string: "name: sdlc-reviewer"
```

- [ ] **Step 3: Cross-reference (replace_all per ogni nome skill citato)**

Applica `Edit` con `replace_all: true` per ogni pattern della cheat sheet che appare nel file. Tipicamente:

```
Edit: "br-clarify" → "sdlc-clarify"  (replace_all: true)
Edit: "br-analyzer" → "sdlc-analyzer"  (replace_all: true)
Edit: "br-updater" → "sdlc-updater"  (replace_all: true)
```
(verifica via Read quali skill sono effettivamente citate)

- [ ] **Step 4: Path file output**

```
Edit: "REVIEW_BR.md" → "CLARIFY.md"  (replace_all: true)
Edit: "REVIEW_BR.docx" → "CLARIFY.docx"  (replace_all: true)
```

- [ ] **Step 5: Terminologia colloquiale**

Cerca nel file riferimenti colloquiali tipo "la review", "il file review", "Generazione REVIEW_BR.docx" (heading) e aggiornali manualmente con `Edit` mirate. Tipico:
- Heading "Generazione REVIEW_BR.docx" diventa "Generazione CLARIFY.docx" (gia' coperto da step 4)
- Frasi tipo "produce la review" → "produce il CLARIFY" — usa giudizio caso per caso

- [ ] **Step 6: Verifica con grep**

Run:
```bash
grep -nE "br-(reviewer|clarify|analyzer|executor|updater|debug|progress-report|estimator|profile-setup)|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-reviewer/SKILL.md
```
Expected: 0 match.

---

### Task 10: Edit `skills/sdlc-clarify/SKILL.md`

**Files:**
- Modify: `skills/sdlc-clarify/SKILL.md`

Conteggio pre-modifica: 31 occorrenze path file (REVIEW_BR e simili) + 18 cross-reference. **File piu' modificato del refactor**.

- [ ] **Step 1: Read del file**

Read `skills/sdlc-clarify/SKILL.md`. Identifica tutte le occorrenze.

- [ ] **Step 2: Frontmatter**

```
Edit: "name: br-clarify" → "name: sdlc-clarify"
```

- [ ] **Step 3: Cross-reference (replace_all per ogni pattern)**

Tipicamente sdlc-clarify cita: `br-reviewer`, `br-analyzer`. Applica `Edit` con `replace_all: true` per ognuno.

- [ ] **Step 4: Path file output**

```
Edit: "REVIEW_BR.md" → "CLARIFY.md"  (replace_all: true)
Edit: "REVIEW_BR.docx" → "CLARIFY.docx"  (replace_all: true)
```

(Probabilmente non ci sono GAP_REPORT_BR o PIANO_IMPLEMENTAZIONE_BR in questa skill, verifica con grep.)

- [ ] **Step 5: Terminologia colloquiale**

Cerca riferimenti a "la review", "review del br" e aggiornali.

- [ ] **Step 6: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-clarify/SKILL.md`
Expected: 0 match.

---

### Task 11: Edit `skills/sdlc-analyzer/SKILL.md`

**Files:**
- Modify: `skills/sdlc-analyzer/SKILL.md`

Conteggio pre-modifica: 13 occorrenze path file + 26 cross-reference (skill centrale, cita molte altre).

- [ ] **Step 1: Read del file**

- [ ] **Step 2: Frontmatter**

```
Edit: "name: br-analyzer" → "name: sdlc-analyzer"
```

- [ ] **Step 3: Cross-reference**

sdlc-analyzer e' il centro della pipeline e cita molte skill. Applica `Edit` con `replace_all: true` per: `br-reviewer`, `br-clarify`, `br-executor`, `br-updater`, `br-progress-report`, `br-estimator`, `br-debug`, `br-profile-setup`, `br-codebase-explorer`, `br-estimation-*`, `br-verifier` (quelli che effettivamente compaiono — verifica via grep).

- [ ] **Step 4: Path file output**

```
Edit: "REVIEW_BR.md" → "CLARIFY.md"  (replace_all: true)
Edit: "GAP_REPORT_BR.md" → "PLAN.md"  (replace_all: true)
Edit: "PIANO_IMPLEMENTAZIONE_BR.md" → "TASKS.md"  (replace_all: true)
```

- [ ] **Step 5: Terminologia colloquiale**

Particolare attenzione qui — sdlc-analyzer produce sia PLAN che TASKS e ne parla in molti punti:
- "gap report" → "PLAN"
- "piano di implementazione" → "TASKS"
- "il piano" (riferito al file TASKS) → "il TASKS"

Usa giudizio: se "piano" si riferisce al concetto astratto (es. "il piano di sviluppo") puo' restare, se si riferisce al file specifico → cambia a TASKS.

- [ ] **Step 6: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-analyzer/SKILL.md`
Expected: 0 match.

---

### Task 12: Edit `skills/sdlc-executor/SKILL.md`

**Files:**
- Modify: `skills/sdlc-executor/SKILL.md`

Conteggio: 3 occorrenze path file + 7 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref, path, terminologia, grep** (stesso pattern di Task 9)

```
Edit: "name: br-executor" → "name: sdlc-executor"
Edit "br-analyzer", "br-updater", "br-debug", ecc. (replace_all per quelli citati)
Edit "REVIEW_BR.md", "GAP_REPORT_BR.md", "PIANO_IMPLEMENTAZIONE_BR.md" → nuovi nomi
```

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-executor/SKILL.md`
Expected: 0 match.

---

### Task 13: Edit `skills/sdlc-updater/SKILL.md`

**Files:**
- Modify: `skills/sdlc-updater/SKILL.md`

Conteggio: 3 occorrenze path file + 6 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref, path, terminologia, grep** (stesso pattern)

```
Edit: "name: br-updater" → "name: sdlc-updater"
Edit cross-ref (br-analyzer, br-reviewer, br-clarify, ecc.)
Edit path file: REVIEW_BR/GAP_REPORT_BR/PIANO_IMPLEMENTAZIONE_BR → CLARIFY/PLAN/TASKS
```

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-updater/SKILL.md`
Expected: 0 match.

---

### Task 14: Edit `skills/sdlc-debug/SKILL.md`

**Files:**
- Modify: `skills/sdlc-debug/SKILL.md`

Conteggio: 1 occorrenza path file + 14 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref, path, terminologia, grep** (stesso pattern)

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-debug/SKILL.md`
Expected: 0 match.

---

### Task 15: Edit `skills/sdlc-progress-report/SKILL.md`

**Files:**
- Modify: `skills/sdlc-progress-report/SKILL.md`

Conteggio: 3 occorrenze path file + 6 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref, path, terminologia, grep**

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-progress-report/SKILL.md`
Expected: 0 match.

---

### Task 16: Edit `skills/sdlc-estimator/SKILL.md`

**Files:**
- Modify: `skills/sdlc-estimator/SKILL.md`

Conteggio: 2 occorrenze path file + 10 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref (inclusi `br-estimation-*` agents), path, terminologia, grep**

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-estimator/SKILL.md`
Expected: 0 match.

---

### Task 17: Edit `skills/sdlc-profile-setup/SKILL.md`

**Files:**
- Modify: `skills/sdlc-profile-setup/SKILL.md`

Conteggio: 0 occorrenze path file + 3 cross-reference.

- [ ] **Step 1: Read, frontmatter, cross-ref, terminologia, grep**

- [ ] **Step 2: Verifica con grep**

Run: `grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." skills/sdlc-profile-setup/SKILL.md`
Expected: 0 match.

---

## Fase 4 — README, verifica finale e commit `claude-flow`

### Task 18: Edit `README.md`

**Files:**
- Modify: `README.md`

Conteggio: 68+ occorrenze tra nomi skill, nomi agent, snippet di installazione, snippet trigger.

- [ ] **Step 1: Read del README per identificare le sezioni**

Sezioni tipiche da aggiornare:
- "Installazione" — comando `cp -r skills/br-*` → `cp -r skills/sdlc-*`, idem per `agents/`
- "Skill disponibili" — lista nomi skill
- "Trigger" — snippet markdown da copiare in `~/.claude/CLAUDE.md`
- Eventuali path nei comandi esemplificativi

- [ ] **Step 2: Sostituzioni con Edit replace_all per ogni nome skill/agent**

Applica `Edit` con `replace_all: true` per ogni pattern della cheat sheet che compare nel README.

- [ ] **Step 3: Path file output (replace_all)**

```
Edit: "REVIEW_BR.md" → "CLARIFY.md"
Edit: "GAP_REPORT_BR.md" → "PLAN.md"
Edit: "PIANO_IMPLEMENTAZIONE_BR.md" → "TASKS.md"
Edit: "REVIEW_BR.docx" → "CLARIFY.docx"
```

- [ ] **Step 4: Aggiungi sezione "Migrazione naming legacy"**

Aggiungi vicino alla sezione installazione una nuova sezione:

````markdown
## Migrazione dal naming legacy (br-*)

Se hai installato una versione precedente con prefisso `br-*` e file di output `REVIEW_BR.md`/`GAP_REPORT_BR.md`/`PIANO_IMPLEMENTAZIONE_BR.md`, esegui:

```bash
# 1. Sincronizza skill installate (rimuove vecchie br-*, installa sdlc-*)
./scripts/sync-installed.sh --apply

# 2. Aggiorna i trigger nel tuo ~/.claude/CLAUDE.md
# Cambia tutte le occorrenze:
#   '# br-X'              →  '# sdlc-X'
#   'skill: "br-X"'       →  'skill: "sdlc-X"'
# Le frasi trigger italiane restano invariate ("rivedi il br", "nuovo br", ecc.)

# 3. Migra i file dei BR in-progress nel tuo repo profili
./scripts/migrate-sdlc-naming.sh --root /path/to/deloitte-profiles --apply

# 4. Commit + push nel repo profili
cd /path/to/deloitte-profiles && git commit -m "chore: rename BR output files to CLARIFY/PLAN/TASKS" && git push
```

Mapping nomi:

| Legacy | Nuovo |
|---|---|
| `br-{reviewer,clarify,analyzer,executor,updater,debug,progress-report,estimator,profile-setup}` | `sdlc-*` |
| `REVIEW_BR.md` / `REVIEW_BR.docx` | `CLARIFY.md` / `CLARIFY.docx` |
| `GAP_REPORT_BR.md` | `PLAN.md` |
| `PIANO_IMPLEMENTAZIONE_BR.md` | `TASKS.md` |
````

- [ ] **Step 5: Verifica con grep**

Run: `grep -nE "br-(reviewer|clarify|analyzer|executor|updater|debug|progress-report|estimator|profile-setup|codebase-explorer|estimation|verifier)|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\." README.md`
Expected: 0 match **eccetto** la nuova sezione "Migrazione dal naming legacy" che cita esplicitamente i nomi vecchi nella tabella di mapping. Quei match sono intenzionali — vanno ignorati.

Per verifica pulita: `grep -vE "Migrazione|Legacy|legacy" README.md | grep -nE "br-|REVIEW_BR\.|GAP_REPORT_BR\.|PIANO_IMPLEMENTAZIONE_BR\."` → 0 match.

---

### Task 19: Verifica consistency su tutto il repo `claude-flow`

**Files:**
- Verify: `skills/`, `agents/`, `scripts/`, `README.md`

- [ ] **Step 1: Grep su nomi skill vecchi**

Run:
```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
grep -rnE "br-(reviewer|clarify|analyzer|executor|updater|debug|progress-report|estimator|profile-setup)" \
  skills/ agents/ scripts/ README.md
```
Expected: solo i match nella sezione "Migrazione dal naming legacy" di README.md (intenzionali). Tutti gli altri match sono bug — risolvere prima di committare.

- [ ] **Step 2: Grep su nomi agent vecchi**

Run:
```bash
grep -rnE "br-(codebase-explorer|estimation-(analyst|historian|scenario)|verifier)" \
  skills/ agents/ scripts/ README.md
```
Expected: solo nella sezione "Migrazione" (intenzionali). Altri match = bug.

- [ ] **Step 3: Grep su nomi file output vecchi**

Run:
```bash
grep -rnE "REVIEW_BR\.md|REVIEW_BR\.docx|GAP_REPORT_BR\.md|PIANO_IMPLEMENTAZIONE_BR\.md" \
  skills/ agents/ scripts/ README.md
```
Expected: solo nella sezione "Migrazione" e nello script `scripts/migrate-sdlc-naming.sh` (intenzionali: lo script DEVE menzionare i nomi vecchi per cercarli). Altri match = bug.

- [ ] **Step 4: Verifica struttura cartelle**

Run: `ls skills/ agents/`
Expected:
- `skills/`: 9 cartelle `sdlc-*`, nessuna `br-*`
- `agents/`: 5 file `sdlc-*.md`, nessuno `br-*.md`

---

### Task 20: Commit + push del refactor su `claude-flow`

**Files:**
- Stage: tutte le modifiche del refactor (skill, agent, README)

- [ ] **Step 1: Verifica `git status`**

Run: `git status --short`
Expected output (riassuntivo):
- ~14 rinomine `R  skills/br-X/SKILL.md -> skills/sdlc-X/SKILL.md` e `R  agents/br-X.md -> agents/sdlc-X.md`
- 1 modifica `M  README.md`
- Modifiche apparenti su tutti i SKILL.md (perche' sono stati editati dopo il rename)

- [ ] **Step 2: Stage tutto e committa (senza attribution)**

```bash
git add skills/ agents/ README.md
git commit -m "refactor: rename br-* skills to sdlc-* and standardize output file names

Skill folders br-{reviewer,clarify,analyzer,executor,updater,debug,
progress-report,estimator,profile-setup} renamed to sdlc-*.
Agent files br-{codebase-explorer,estimation-*,verifier}.md renamed to sdlc-*.md.

Output file names standardized:
  REVIEW_BR.md   -> CLARIFY.md
  REVIEW_BR.docx -> CLARIFY.docx
  GAP_REPORT_BR.md -> PLAN.md
  PIANO_IMPLEMENTAZIONE_BR.md -> TASKS.md

Updated: all skill frontmatters, cross-references between skills/agents,
file output paths, colloquial terminology in descriptions, README install
section, trigger snippets, plus a new 'Migrazione dal naming legacy' section.

Unchanged: italian trigger phrases in ~/.claude/CLAUDE.md (e.g. 'rivedi il br'),
domain terminology 'BR' in descriptive text, profile folder layout
(plans/in-progress/<date>_<name>/), PROGRESSO.md, historical docs in
docs/superpowers/specs/ and plans/.

See docs/superpowers/specs/2026-05-18-sdlc-rename-design.md for full rationale."
```

**Importante:** NON aggiungere `Co-Authored-By: Claude`.

- [ ] **Step 3: Verifica il commit**

Run: `git log -1 --format='%s%n---%n%b'`
Expected: il messaggio sopra, senza linee `Co-Authored-By:`.

- [ ] **Step 4: Push**

Run: `git push origin main`
Expected: push avvenuto, output `<old_hash>..<new_hash>  main -> main`.

---

## Fase 5 — Sync copie installate in `~/.claude/`

### Task 21: Esegui `sync-installed.sh --apply`

**Files:**
- Use: `scripts/sync-installed.sh`

- [ ] **Step 1: Dry-run finale per ispezione**

Run: `./scripts/sync-installed.sh`
Expected output: lista delle 9 cartelle `br-*` da rimuovere + 5 agent `br-*.md` + 9 cartelle `sdlc-*` da installare + 5 agent `sdlc-*.md`.

- [ ] **Step 2: Esegui con --apply**

Run: `./scripts/sync-installed.sh --apply`
Expected: output stesso del dry-run ma con i comandi eseguiti davvero.

- [ ] **Step 3: Verifica installazione**

Run: `ls ~/.claude/skills/ | grep -E "^(br|sdlc)-"`
Expected: solo cartelle `sdlc-*`, nessuna `br-*`.

Run: `ls ~/.claude/agents/ | grep -E "^(br|sdlc)-"`
Expected: solo file `sdlc-*.md`, nessuno `br-*.md`.

---

### Task 22: Aggiorna `~/.claude/CLAUDE.md`

**Files:**
- Modify: `~/.claude/CLAUDE.md`

Il file `~/.claude/CLAUDE.md` non e' nel repo (e' privato dell'utente). Va aggiornato manualmente.

- [ ] **Step 1: Backup del file corrente**

Run: `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak-$(date +%Y%m%d-%H%M%S)`

- [ ] **Step 2: Esegui sed in-place per le 14 sostituzioni**

```bash
sed -i \
  -e 's/# br-reviewer/# sdlc-reviewer/g' \
  -e 's/# br-clarify/# sdlc-clarify/g' \
  -e 's/# br-analyzer/# sdlc-analyzer/g' \
  -e 's/# br-executor/# sdlc-executor/g' \
  -e 's/# br-updater/# sdlc-updater/g' \
  -e 's/# br-debug/# sdlc-debug/g' \
  -e 's/# br-progress-report/# sdlc-progress-report/g' \
  -e 's/# br-estimator/# sdlc-estimator/g' \
  -e 's/# br-profile-setup/# sdlc-profile-setup/g' \
  -e 's/skill: "br-reviewer"/skill: "sdlc-reviewer"/g' \
  -e 's/skill: "br-clarify"/skill: "sdlc-clarify"/g' \
  -e 's/skill: "br-analyzer"/skill: "sdlc-analyzer"/g' \
  -e 's/skill: "br-executor"/skill: "sdlc-executor"/g' \
  -e 's/skill: "br-updater"/skill: "sdlc-updater"/g' \
  -e 's/skill: "br-debug"/skill: "sdlc-debug"/g' \
  -e 's/skill: "br-progress-report"/skill: "sdlc-progress-report"/g' \
  -e 's/skill: "br-estimator"/skill: "sdlc-estimator"/g' \
  -e 's/skill: "br-profile-setup"/skill: "sdlc-profile-setup"/g' \
  -e 's|`~/.claude/skills/br-|`~/.claude/skills/sdlc-|g' \
  ~/.claude/CLAUDE.md
```

- [ ] **Step 3: Verifica con grep**

Run: `grep -nE "^# br-|skill: \"br-|skills/br-" ~/.claude/CLAUDE.md`
Expected: 0 match.

Run: `grep -nE "^# sdlc-|skill: \"sdlc-|skills/sdlc-" ~/.claude/CLAUDE.md`
Expected: ~9 match (i nuovi nomi nei trigger).

- [ ] **Step 4: Test trigger naturali**

Le frasi trigger italiane restano invariate. Verifica con grep:
```bash
grep -E "rivedi il br|abbiamo un nuovo br|lavora il task" ~/.claude/CLAUDE.md
```
Expected: i match originali, identici a prima (trigger non toccati).

---

## Fase 6 — Migrazione BR in-progress nel repo `deloitte-profiles`

### Task 23: Dry-run `migrate-sdlc-naming.sh` su deloitte-profiles

**Files:**
- Use: `scripts/migrate-sdlc-naming.sh`

- [ ] **Step 1: Esegui dry-run**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
./scripts/migrate-sdlc-naming.sh
```

Expected output (basato sullo scan attuale):
```
[DRY-RUN] Scanning C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/*/plans/{in-progress,todo}/

  banca-agente/plans/in-progress/2026-05-04_monitoring/
    REVIEW_BR.md → CLARIFY.md
    REVIEW_BR.docx → CLARIFY.docx
    GAP_REPORT_BR.md → PLAN.md
    PIANO_IMPLEMENTAZIONE_BR.md → TASKS.md

4 rename operation(s) on 1 BR(s).
Run with --apply to execute. ...
```

- [ ] **Step 2: Se l'output mostra BR non previsti o conflict, fermarsi e investigare**

Verifica che la lista corrisponda alle aspettative. Se ci sono altri profili/BR oltre a `banca-agente/monitoring`, prendi nota.

---

### Task 24: Esegui `migrate-sdlc-naming.sh --apply`

**Files:**
- Modify: file in `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/` (via git mv)

- [ ] **Step 1: Esegui --apply**

```bash
./scripts/migrate-sdlc-naming.sh --apply
```

Expected: stesso output del dry-run ma con `git mv` eseguiti davvero.

- [ ] **Step 2: Verifica con git status nel repo profili**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
git status --short
```

Expected: 4 righe `R  banca-agente/plans/in-progress/2026-05-04_monitoring/<old> -> <new>` (1 R per ogni file rinominato).

- [ ] **Step 3: Verifica filesystem**

```bash
ls banca-agente/plans/in-progress/2026-05-04_monitoring/
```

Expected: nuovi nomi (`CLARIFY.md`, `CLARIFY.docx`, `PLAN.md`, `TASKS.md`). Eventuale `PROGRESSO.md` resta intatto.

---

### Task 25: Commit + push `deloitte-profiles`

**Files:**
- Commit: rinomine nel repo profili

- [ ] **Step 1: Commit (senza attribution)**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
git commit -m "chore: rename BR output files to CLARIFY/PLAN/TASKS convention

Migrates in-progress BR file names from legacy convention:
  REVIEW_BR.md   -> CLARIFY.md
  REVIEW_BR.docx -> CLARIFY.docx
  GAP_REPORT_BR.md -> PLAN.md
  PIANO_IMPLEMENTAZIONE_BR.md -> TASKS.md

Applied via claude-flow/scripts/migrate-sdlc-naming.sh. Closed BRs in
plans/done/ are left untouched (historical artifacts).

Note: references to old file names inside PROGRESSO.md or other markdown
files are NOT modified by the migration script and may need manual fixes
if encountered."
```

**Importante:** NON aggiungere `Co-Authored-By: Claude`.

- [ ] **Step 2: Verifica il commit**

Run: `git log -1 --format='%s%n---%n%b'`
Expected: messaggio sopra, senza `Co-Authored-By:`.

- [ ] **Step 3: Push**

Run: `git push origin main`
Expected: push avvenuto. Verifica che il branch tracking sia attivo (`git branch -vv`).

Se il branch non e' `main` o non ha upstream, usa `git push -u origin <branch>`.

---

## Fase 7 — Smoke test finale

### Task 26: Smoke test invocando una skill `sdlc-*`

- [ ] **Step 1: In una nuova sessione Claude Code, dichiara un trigger**

Apri una nuova sessione e digita una frase trigger, es.: `"rivedi il br"`.

Expected:
- Claude invoca la skill `sdlc-reviewer` (verifica nel log della tool-call: `skill: "sdlc-reviewer"`)
- La skill carica il proprio SKILL.md aggiornato
- Se eseguita su un BR di test, produce `CLARIFY.md` (non `REVIEW_BR.md`)

- [ ] **Step 2: Verifica che le vecchie skill non siano piu' visibili**

In una sessione Claude Code, verifica che `br-reviewer` non compaia piu' nella lista skill disponibili (`/skills` o equivalente).

Expected: solo `sdlc-*` listed.

- [ ] **Step 3: Verifica idempotenza della migrazione**

Run: `./scripts/migrate-sdlc-naming.sh`
Expected: `Nothing to do. All files already use the new naming.`

- [ ] **Step 4: Verifica che il BR in-progress migrato sia leggibile dalle skill**

In una sessione Claude Code, prova a invocare `"aggiorna l'excel"` (trigger di `sdlc-progress-report`) sul BR `banca-agente/plans/in-progress/2026-05-04_monitoring/`. La skill deve trovare `TASKS.md` (non `PIANO_IMPLEMENTAZIONE_BR.md`) senza errori.

---

## Definition of done

- [ ] `scripts/migrate-sdlc-naming.sh` e `scripts/sync-installed.sh` creati, testati, committati e pushati
- [ ] Tutte le 9 skill rinominate `sdlc-*` con frontmatter, cross-ref, path e terminologia aggiornati
- [ ] Tutti i 5 agent rinominati `sdlc-*` con frontmatter + cross-ref aggiornati
- [ ] `README.md` aggiornato con installazione + trigger templates + sezione "Migrazione dal naming legacy"
- [ ] Grep di consistency in `skills/ agents/ scripts/ README.md` → 0 match sui pattern vecchi (eccetto la sezione Migrazione di README e i pattern legittimi in `migrate-sdlc-naming.sh`)
- [ ] Repo `claude-flow`: commit + push fatti, **senza** attribution Claude
- [ ] `~/.claude/skills/` contiene solo cartelle `sdlc-*` (nessuna `br-*`)
- [ ] `~/.claude/agents/` contiene solo file `sdlc-*.md` (nessuno `br-*.md`)
- [ ] `~/.claude/CLAUDE.md` aggiornato (9 sezioni trigger con `skill: "sdlc-X"`, trigger italiani invariati)
- [ ] BR in-progress in `deloitte-profiles` migrati ai nuovi nomi (CLARIFY/PLAN/TASKS)
- [ ] Repo `deloitte-profiles`: commit + push fatti, **senza** attribution Claude
- [ ] Smoke test: invocazione di una skill `sdlc-*` parte e produce output coi nomi nuovi
