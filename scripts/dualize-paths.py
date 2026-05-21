"""
Wave 1 — Sostituisce le sezioni 'Risoluzione Path' + 'Caricamento contesto'
nelle SKILL.md SDLC con la versione duale standalone|legacy (auto-detect da
.br-local.json). Sostituisce anche inline i riferimenti placeholder a
<profiles_repo>/<profilo>/{plans,constitution} con $BASE_PATH/$CONST_PATH
e git -C "<profiles_repo>" con git -C "$GIT_REPO_PATH".

Skill target (Wave 1, path-only):
  - sdlc-executor
  - sdlc-progress-report
  - sdlc-estimator

Wave 2 e Wave 3 useranno lo stesso replacement + cambi addizionali specifici
per skill (gestiti separatamente).
"""
import re
from pathlib import Path

NEW_BLOCK = """## Risoluzione Path (modalita' duale: standalone | legacy)

Tutte le operazioni su file plan avvengono nella **project_repo** (modalita' standalone, una repo per progetto) o nella repo `deloitte-profiles` (modalita' legacy), **non** nella repo del codice applicativo. Il codice del progetto continua a essere scritto nelle repo del progetto.

### Lettura `.br-local.json` e detection modalita'

All'avvio, leggi `.br-local.json` dalla root della repo corrente:

```bash
cat .br-local.json 2>/dev/null
```

La presenza del campo `project_repo` o `profiles_repo` discrimina la modalita':

```bash
if grep -q '"project_repo"' .br-local.json 2>/dev/null; then
  MODE="standalone"
  PROJECT_REPO=$(grep -oP '"project_repo"\\s*:\\s*"\\K[^"]+' .br-local.json)
  PROJECT_NAME=$(grep -oP '"project_name"\\s*:\\s*"\\K[^"]+' .br-local.json)
  BASE_PATH="$PROJECT_REPO/plans"
  CONST_PATH="$PROJECT_REPO/constitution"
  DATASET_PATH="$PROJECT_REPO/dataset"        # solo standalone (popolato da Solaria-side)
  GIT_REPO_PATH="$PROJECT_REPO"
elif grep -q '"profiles_repo"' .br-local.json 2>/dev/null; then
  MODE="legacy"
  PROFILES_REPO=$(grep -oP '"profiles_repo"\\s*:\\s*"\\K[^"]+' .br-local.json)
  PROFILO=$(grep -oP '"profilo"\\s*:\\s*"\\K[^"]+' .br-local.json)
  PROJECT_NAME="$PROFILO"
  BASE_PATH="$PROFILES_REPO/$PROFILO/plans"
  CONST_PATH="$PROFILES_REPO/$PROFILO/constitution"
  DATASET_PATH=""                              # non esiste in legacy
  GIT_REPO_PATH="$PROFILES_REPO"
fi
```

| Modalita' | `BASE_PATH` | `CONST_PATH` | Stati supportati |
|---|---|---|---|
| Standalone | `$PROJECT_REPO/plans` | `$PROJECT_REPO/constitution` | `draft`, `todo`, `in-progress`, `done` |
| Legacy | `$PROFILES_REPO/$PROFILO/plans` | `$PROFILES_REPO/$PROFILO/constitution` | `todo`, `in-progress`, `done` |

> **Nota**: `plans/draft/` esiste solo in modalita' standalone — area dove Solaria authora l'AFU prima dell'handoff (Fase 1c). Le skill SDLC ignorano `draft/` (e' Solaria-side) tranne `sdlc-reviewer` e `sdlc-clarify` quando esplicitamente invocate su un draft.

### Se `.br-local.json` non esiste

Ferma l'esecuzione e avvisa:

> `.br-local.json` non trovato. Devi prima eseguire `/sdlc-profile-setup`, che ti chiedera' se vuoi configurare in **modalita' standalone** (raccomandato per nuovi progetti, una repo per progetto con cartella `dataset/` Solaria-side) o **modalita' legacy** (progetti gia' esistenti in `deloitte-profiles`).

### Sincronizzazione prima della lettura

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
```

### Commit e push dopo la scrittura

```bash
git -C "$GIT_REPO_PATH" add .
git -C "$GIT_REPO_PATH" commit -m "<messaggio>"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path con l'helper di detection sopra, prima di eseguire qualsiasi altra fase carica i due file di costituzione del progetto:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
cat "$CONST_PATH/CONST.json"
cat "$CONST_PATH/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| `.br-local.json` manca | "Esegui prima `/sdlc-profile-setup` scegliendo modalita' standalone o legacy" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il progetto `<PROJECT_NAME>` non ha CONST.json. Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il progetto `<PROJECT_NAME>` non ha PROFILE.json. Stato inconsistente — il profilo e' incompleto. Ripristinare da git history o rifare il setup." | Stop |
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
"""

# Inline replacements (applicati DOPO la sostituzione del blocco principale)
INLINE = [
    # Longest match first to evitare match parziali
    (r"<profiles_repo>/<profilo>/plans", r"$BASE_PATH"),
    (r"<profiles_repo>/<profilo>/constitution", r"$CONST_PATH"),
    (r'git -C "<profiles_repo>"', r'git -C "$GIT_REPO_PATH"'),
    # Ultime sicurezze: <profiles_repo> orfano residuo
    (r'"<profiles_repo>"', r'"$GIT_REPO_PATH"'),
]


def replace_path_block(content: str) -> str:
    """Sostituisce dalla riga '## Risoluzione Path' al penultimo '---' che precede
    la sezione successiva (che NON sia 'Risoluzione Path' ne' 'Caricamento contesto').
    """
    lines = content.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## Risoluzione Path"):
            start = i
            break
    if start is None:
        raise RuntimeError("Sezione '## Risoluzione Path' non trovata")

    # Trova la prima header ## che NON appartiene ai blocchi da sostituire
    end_header_idx = None
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("## "):
            if "Risoluzione Path" in line or "Caricamento contesto" in line:
                continue
            end_header_idx = i
            break
    if end_header_idx is None:
        raise RuntimeError("Header successiva non trovata dopo le sezioni da sostituire")

    # Cerca all'indietro un '---' eventualmente seguito da righe vuote
    sep_idx = end_header_idx - 1
    while sep_idx > start and lines[sep_idx].strip() == "":
        sep_idx -= 1
    if lines[sep_idx].strip() == "---":
        # Sostituisci [start..sep_idx] (inclusivo) con NEW_BLOCK + '\n---' (mantieni separator)
        replacement = NEW_BLOCK.rstrip("\n") + "\n\n---"
        new_lines = lines[:start] + replacement.split("\n") + lines[sep_idx + 1:]
    else:
        # Non c'e' --- esplicito; sostituisci fino a (escluso) end_header_idx
        replacement = NEW_BLOCK.rstrip("\n") + "\n\n---\n"
        new_lines = lines[:start] + replacement.split("\n") + lines[end_header_idx:]
    return "\n".join(new_lines)


def apply_inline(content: str) -> str:
    for old, new in INLINE:
        content = content.replace(old, new)
    return content


def process(skill_path: Path) -> tuple[int, int]:
    """Ritorna (occorrenze_prima, occorrenze_dopo) di profiles_repo per audit."""
    src = skill_path.read_text(encoding="utf-8")
    before = src.count("profiles_repo")
    new = replace_path_block(src)
    new = apply_inline(new)
    after = new.count("profiles_repo")
    skill_path.write_text(new, encoding="utf-8")
    return before, after


SKILLS = [
    # Wave 1 (gia' fatto in commit 59bcf1b — script idempotente: skip se gia' applicato)
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-executor\SKILL.md"),
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-progress-report\SKILL.md"),
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-estimator\SKILL.md"),
    # Wave 2 (manifest-aware — cambi addizionali specifici post path dualization)
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-reviewer\SKILL.md"),
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-clarify\SKILL.md"),
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-analyzer\SKILL.md"),
    Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-updater\SKILL.md"),
    # Wave 3 (profile-setup + debug) — cambi strutturali piu' pesanti, applicare a parte
    # Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-profile-setup\SKILL.md"),
    # Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\skills\sdlc-debug\SKILL.md"),
]

for s in SKILLS:
    try:
        before, after = process(s)
        print(f"{s.name} ({s.parent.name}): profiles_repo {before} -> {after} occurrences")
    except RuntimeError as e:
        # Idempotenza: il file e' gia' stato dualizzato in una run precedente
        if "non trovata" in str(e):
            print(f"{s.name} ({s.parent.name}): SKIP (gia' dualizzato)")
        else:
            raise
