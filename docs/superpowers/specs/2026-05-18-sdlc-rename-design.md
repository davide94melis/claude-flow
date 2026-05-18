# Rename `br-*` → `sdlc-*` e file di output `CLARIFY` / `PLAN` / `TASKS`

**Data:** 2026-05-18
**Stato:** Design approvato, in attesa di plan di implementazione
**Repo coinvolti:** `claude-flow` (skill + agent + script + README), `deloitte-profiles` (migrazione file BR in-progress)

---

## 1. Contesto e problema

Le skill della pipeline BR hanno due naming convention ereditati dall'evoluzione organica del progetto:

1. **Nomi tecnici delle skill e degli agent**: prefisso `br-` (es. `br-reviewer`, `br-analyzer`). Il prefisso e' legato al concetto di Business Requirement ma non riflette piu' bene lo scope, che e' diventato l'intero ciclo SDLC (review → analysis → execution → testing → debug → progress reporting).

2. **Nomi dei file di output** delle skill: `REVIEW_BR.md`, `GAP_REPORT_BR.md`, `PIANO_IMPLEMENTAZIONE_BR.md`. Naming verboso, con suffisso `_BR` ridondante (vivono dentro una cartella che gia' identifica il BR), e mix italiano/inglese (`PIANO_IMPLEMENTAZIONE` vs `GAP_REPORT`).

L'obiettivo del refactor e' duplice e va eseguito atomicamente:
- Rinominare le skill da `br-*` a `sdlc-*` (solo nomi tecnici, vedi sezione 7 "Cosa NON cambia")
- Rinominare i 3 file di output in: `CLARIFY.md`, `PLAN.md`, `TASKS.md` (+ `CLARIFY.docx` companion)

---

## 2. Decisioni di design

Frutto del brainstorming, fissate prima di passare al plan:

| # | Decisione | Scelta |
|---|---|---|
| D1 | Convenzione naming file output | Senza suffisso (`CLARIFY.md`, `PLAN.md`, `TASKS.md`) |
| D2 | Backward compatibility con BR esistenti | Breaking change + script di migrazione one-shot per i BR in-progress |
| D3 | Documenti storici (`docs/superpowers/specs/` e `plans/`) | Lasciati invariati come fossili + glossario di migrazione in questo spec |
| D4 | Terminologia colloquiale nei testi delle skill | Riscrittura completa per coerenza (non solo path) |
| D5 | Scope del rename `br-*` → `sdlc-*` | Solo nomi tecnici: skill folders, agent files, frontmatter, cross-reference, copie installate. Trigger italiani, terminologia di dominio "BR" nei testi, cartelle dei profili → invariati |
| D6 | Strategia di rollout | PR atomico unico (no skill-by-skill, no check script permanente) |

---

## 3. Mapping nomi (la "verita' unica")

### 3.1 File di output

| Vecchio | Nuovo | Generato da | Letto da |
|---|---|---|---|
| `REVIEW_BR.md` | `CLARIFY.md` | sdlc-reviewer | sdlc-clarify, sdlc-analyzer, sdlc-updater |
| `REVIEW_BR.docx` | `CLARIFY.docx` | sdlc-reviewer (via pandoc) | umano (team funzionale) |
| `GAP_REPORT_BR.md` | `PLAN.md` | sdlc-analyzer | sdlc-executor, sdlc-updater, sdlc-debug |
| `PIANO_IMPLEMENTAZIONE_BR.md` | `TASKS.md` | sdlc-analyzer | sdlc-executor, sdlc-updater, sdlc-progress-report, sdlc-debug, sdlc-estimator |

### 3.2 Skill folders (`skills/`)

| Vecchio | Nuovo |
|---|---|
| `br-reviewer/` | `sdlc-reviewer/` |
| `br-clarify/` | `sdlc-clarify/` |
| `br-analyzer/` | `sdlc-analyzer/` |
| `br-executor/` | `sdlc-executor/` |
| `br-updater/` | `sdlc-updater/` |
| `br-debug/` | `sdlc-debug/` |
| `br-progress-report/` | `sdlc-progress-report/` |
| `br-estimator/` | `sdlc-estimator/` |
| `br-profile-setup/` | `sdlc-profile-setup/` |

### 3.3 Agent files (`agents/`)

| Vecchio | Nuovo |
|---|---|
| `br-codebase-explorer.md` | `sdlc-codebase-explorer.md` |
| `br-estimation-analyst.md` | `sdlc-estimation-analyst.md` |
| `br-estimation-historian.md` | `sdlc-estimation-historian.md` |
| `br-estimation-scenario.md` | `sdlc-estimation-scenario.md` |
| `br-verifier.md` | `sdlc-verifier.md` |

### 3.4 Terminologia colloquiale nei testi delle skill

| Vecchio termine | Nuovo termine |
|---|---|
| "gap report" / "gap analysis" (riferito al file) | "PLAN" / "file PLAN" |
| "piano di implementazione" / "piano sviluppo" (riferito al file) | "TASKS" / "file TASKS" |
| "review" / "review del br" (sostantivo riferito al file) | "CLARIFY" / "file CLARIFY" |
| "review" (verbo, l'azione di revieware) | resta invariato |

---

## 4. Impatto file-per-file

### 4.1 Mole complessiva

- **9 SKILL.md** nel repo: 68 occorrenze path file vecchi + 104 cross-reference = **~172 sostituzioni**
- **5 agent .md**: 1 path file + 10 cross-reference = **11 sostituzioni**
- **README.md**: 68+ sostituzioni (sezione installazione + snippet trigger)
- **14 cartelle/file** da rinominare nel repo (9 skill dirs + 5 agent files)
- **9 cartelle** da rimuovere/sostituire in `~/.claude/skills/`
- **5 file** da rimuovere/sostituire in `~/.claude/agents/`
- **`~/.claude/CLAUDE.md`** (private user file, non in git): 9 sezioni trigger da aggiornare

### 4.2 Per ogni SKILL.md

1. **Rinomina cartella**: `skills/br-X/` → `skills/sdlc-X/` (operazione `git mv` per preservare history)
2. **Frontmatter**: `name: br-X` → `name: sdlc-X`
3. **Cross-references inline**: ogni `br-Y` menzionato nel corpo (es. *"questa skill viene invocata dopo `br-analyzer`"*)
4. **Path file di output**: applicare il mapping 3.1
5. **Terminologia colloquiale**: applicare il mapping 3.4

### 4.3 Per ogni agent .md

1. **Rinomina file**: `agents/br-X.md` → `agents/sdlc-X.md`
2. **Frontmatter `name:`** aggiornato a `sdlc-X`
3. **Cross-references** ad altre skill/agent aggiornate
4. **Eventuali path file di output** aggiornati

### 4.4 README.md

- Sezione installazione: `cp -r skills/br-*` → `cp -r skills/sdlc-*` (idem per `agents/`)
- Snippet trigger da copiare in `~/.claude/CLAUDE.md`: nomi skill aggiornati a `sdlc-*`
- Eventuale aggiunta sezione "Migrazione naming legacy → SDLC" con istruzioni per chi aveva gia' installato la versione vecchia

---

## 5. Script di migrazione one-shot

**Path:** `scripts/migrate-sdlc-naming.sh` (Bash, coerente con altri script in `scripts/`)

### 5.1 Cosa fa

1. Scandaglia `<deloitte-profiles>/*/plans/{in-progress,todo}/**/` per i 4 file legacy:
   - `REVIEW_BR.md` → `CLARIFY.md`
   - `REVIEW_BR.docx` → `CLARIFY.docx`
   - `GAP_REPORT_BR.md` → `PLAN.md`
   - `PIANO_IMPLEMENTAZIONE_BR.md` → `TASKS.md`
2. Esegue `git mv` (preserva history) per ogni file trovato
3. Non tocca `plans/done/**` (fossili — i BR chiusi restano col loro nome storico)

### 5.2 Caratteristiche

- **Dry-run di default**: stampa cosa farebbe senza eseguire
- **`--apply`**: esegue davvero (richiesto esplicitamente)
- **`--root <path>`**: override del path repo profili (default: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles` o quello configurato in `.br-local.json`)
- **Idempotente**: se trova solo i nomi nuovi (gia' migrato), output "nothing to do"
- **Safe contro conflitti**: se trova *entrambi* il vecchio e il nuovo nella stessa cartella, aborta con errore chiaro
- **Warning finale**: nota che riferimenti *interni* a `PROGRESSO.md` o ad altri md potrebbero contenere ancora i vecchi nomi e sono lasciati intatti per scelta

### 5.3 Output esempio (dry-run)

```
[DRY-RUN] Scanning C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/*/plans/{in-progress,todo}/
[DRY-RUN] Found 1 BR with legacy files:
  banca-agente/plans/in-progress/2026-05-04_monitoring/
    REVIEW_BR.md → CLARIFY.md
    REVIEW_BR.docx → CLARIFY.docx
    GAP_REPORT_BR.md → PLAN.md
    PIANO_IMPLEMENTAZIONE_BR.md → TASKS.md

4 rename operations on 1 BR. Run with --apply to execute.
```

### 5.4 Esecuzione

```bash
./scripts/migrate-sdlc-naming.sh                  # dry-run
./scripts/migrate-sdlc-naming.sh --apply          # esegue git mv nel repo profili
```

---

## 6. Sync con copie installate e verifica finale

### 6.1 Script di sync: `scripts/sync-installed.sh`

Wrapper riutilizzabile per propagare le skill dal repo a `~/.claude/`. Necessario perche' il rename `br-*` → `sdlc-*` lascerebbe le vecchie cartelle come "skill zombie" disponibili in parallelo alle nuove.

```bash
# Cleanup vecchie installazioni br-*
rm -rf ~/.claude/skills/br-*
rm -f  ~/.claude/agents/br-*.md

# Installa le nuove sdlc-*
cp -r skills/sdlc-* ~/.claude/skills/
cp -r agents/sdlc-*.md ~/.claude/agents/
```

Lo script accetta `--dry-run` per verificare cosa farebbe.

### 6.2 Aggiornamento `~/.claude/CLAUDE.md`

File private dell'utente (non in git). Va aggiornato a mano (o con `sed`) cambiando:
- Header sezione `# br-X` → `# sdlc-X`
- Argomento `skill: "br-X"` → `skill: "sdlc-X"`
- Le frasi trigger italiane restano invariate (*"abbiamo un nuovo br"*, *"rivedi il br"*, ecc.)

Il README.md include uno snippet `sed` pronto da eseguire, oppure blocchi markdown aggiornati copia-incolla.

### 6.3 Verifica finale (consistency check)

Eseguito manualmente al termine del rollout, prima del commit finale:

```bash
# Nel repo claude-flow — deve restituire 0 match (escludendo docs/superpowers/)
grep -rE "br-(reviewer|clarify|analyzer|executor|updater|debug|progress-report|estimator|profile-setup)" \
  skills/ agents/ README.md scripts/

grep -rE "br-(codebase-explorer|estimation-(analyst|historian|scenario)|verifier)" \
  skills/ agents/ README.md scripts/

grep -rE "REVIEW_BR\.md|GAP_REPORT_BR\.md|PIANO_IMPLEMENTAZIONE_BR\.md|REVIEW_BR\.docx" \
  skills/ agents/ README.md scripts/

# Verifica copie installate
ls ~/.claude/skills/ | grep -E "^br-" && echo "FAIL: vecchie skill ancora installate" || echo "OK"
ls ~/.claude/agents/ | grep -E "^br-" && echo "FAIL: vecchi agent ancora installati" || echo "OK"
```

---

## 7. Cosa NON cambia (boundaries)

Per evitare scope creep, queste cose **non** vengono modificate dal refactor:

- **Trigger naturali italiani** nel `~/.claude/CLAUDE.md` (*"abbiamo un nuovo br"*, *"rivedi il br"*, *"lavora il task"*, ecc.) — restano cosi' come sono perche' riflettono il vocabolario reale dell'utente.
- **Terminologia di dominio "BR" / "Business Requirement"** nei testi descrittivi delle skill — il concetto rimane.
- **Cartelle dei profili** (`deloitte-profiles/<profilo>/plans/in-progress/<data>_<nome>/`) — rimangono cosi'.
- **PROGRESSO.md** — non era nello scope del rename (e' un file generato durante l'esecuzione delle task, non un output delle skill di analisi).
- **`plans/done/**`** — i BR chiusi restano fossili coi loro nomi storici (alcuni hanno anche convenzioni piu' vecchie tipo `GAP_ANALYSIS_BR_v27.md`).
- **`docs/superpowers/specs/` e `docs/superpowers/plans/`** — spec/plan storici lasciati intatti, accuratezza storica preservata. Vedi glossario nella sezione 8.
- **Riferimenti interni a `PROGRESSO.md` o ad altri md nei BR migrati** — lo script non fa `sed` sui contenuti, solo `git mv` dei file.

---

## 8. Glossario di migrazione (per i fossili in `docs/superpowers/`)

Chi legge gli spec e i plan storici trovera' i nomi vecchi. Equivalenze:

| Nome storico | Nome attuale (post 2026-05-18) |
|---|---|
| `br-reviewer` | `sdlc-reviewer` |
| `br-clarify` | `sdlc-clarify` |
| `br-analyzer` | `sdlc-analyzer` |
| `br-executor` | `sdlc-executor` |
| `br-updater` | `sdlc-updater` |
| `br-debug` | `sdlc-debug` |
| `br-progress-report` | `sdlc-progress-report` |
| `br-estimator` | `sdlc-estimator` |
| `br-profile-setup` | `sdlc-profile-setup` |
| `br-codebase-explorer` | `sdlc-codebase-explorer` |
| `br-estimation-{analyst,historian,scenario}` | `sdlc-estimation-{analyst,historian,scenario}` |
| `br-verifier` | `sdlc-verifier` |
| `REVIEW_BR.md` / `REVIEW_BR.docx` | `CLARIFY.md` / `CLARIFY.docx` |
| `GAP_REPORT_BR.md` | `PLAN.md` |
| `PIANO_IMPLEMENTAZIONE_BR.md` | `TASKS.md` |
| termine "gap report" (sostantivo) | "PLAN" (sostantivo) |
| termine "piano di implementazione" (sostantivo) | "TASKS" (sostantivo) |
| termine "review" (sostantivo riferito al file) | "CLARIFY" (sostantivo) |

Convenzioni ancora piu' vecchie (`GAP_ANALYSIS_BR_v27.md`, `PIANO_SVILUPPO_GAP_BR_v27.md`) appartengono a una generazione precedente e non sono mai state coperte dalle skill attuali — si trovano solo in `plans/done/` come fossili archeologici.

---

## 9. Ordine operativo del rollout

1. **Repo `claude-flow` — modifiche**
   - `git mv` cartelle skill (`br-*` → `sdlc-*`) e agent files
   - Edit di ogni SKILL.md (frontmatter + cross-ref + path file output + terminologia)
   - Edit di ogni agent .md (frontmatter + cross-ref)
   - Update `README.md`
   - Crea `scripts/migrate-sdlc-naming.sh` e `scripts/sync-installed.sh`
2. **Repo `claude-flow` — verifica**
   - Esegui i grep di consistency (sezione 6.3) → deve essere clean
3. **Repo `claude-flow` — commit + push**
   - Un commit unico con tutto il rename + script. Messaggio: `refactor: rename br-* skills to sdlc-* and standardize output filenames (CLARIFY/PLAN/TASKS)`
   - Push su `main`
   - **Niente attribution Co-Authored-By Claude** (esplicitamente richiesto dall'utente + gia' di default per global settings)
4. **Sync copie installate**
   - Esegui `./scripts/sync-installed.sh` (cleanup `br-*` + copia `sdlc-*`)
   - Aggiorna `~/.claude/CLAUDE.md` (a mano o con `sed` snippet dal README)
5. **Repo `deloitte-profiles` — migrazione BR in-progress**
   - Esegui `./scripts/migrate-sdlc-naming.sh` (dry-run, ispeziona output)
   - Esegui `./scripts/migrate-sdlc-naming.sh --apply` (esegue `git mv`)
   - Verifica con `git status` nel repo profili
6. **Repo `deloitte-profiles` — commit + push**
   - Commit dei rename. Messaggio: `chore: rename BR output files to CLARIFY/PLAN/TASKS convention`
   - Push su `main`
   - **Niente attribution Co-Authored-By Claude**
7. **Smoke test**
   - Invoca `/sdlc-reviewer` con un BR di test per verificare che la skill parta e produca `CLARIFY.md`
   - Verifica che `~/.claude/skills/` contenga solo cartelle `sdlc-*`

---

## 10. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Utente dimentica di eseguire `sync-installed.sh` dopo il pull | Sezione dedicata nel README, output di commit con istruzioni |
| Utente dimentica di aggiornare `~/.claude/CLAUDE.md` | Snippet `sed` pronto nel README + sezione "Post-update steps" |
| BR in-progress non scoperti dallo script (profili in path non-standard) | Flag `--root` per override + log esplicito di quali profili sono stati scanditi |
| Conflict tra file vecchi e nuovi nella stessa cartella | Script aborta con errore chiaro, l'utente decide manualmente |
| Riferimenti ai vecchi nomi dentro `PROGRESSO.md` di BR migrati | Warning finale dello script — l'utente gestisce caso per caso (probabilmente non rompe nulla operativamente) |
| Cross-reference sfuggita in qualche SKILL.md | Grep di verifica nella sezione 6.3 cattura tutto prima del commit |

---

## 11. Out of scope (esplicito)

Per evitare ambiguita' sulle prossime sessioni:

- **Rename del concetto "BR" a "SDLC unit"** nei testi descrittivi delle skill. Non si fa. Il dominio resta BR.
- **Modifica dei trigger italiani** ("nuovo br" → "nuovo sdlc"). Non si fa.
- **Rename delle cartelle dei profili** (`plans/in-progress/<data>_<nome>/`). Non si fa.
- **Modifica del file `PROGRESSO.md`** (nome o contenuto). Non si fa.
- **Migrazione dei BR in `plans/done/`**. Non si fa, restano fossili.
- **Hook precommit / check script permanente di consistency naming**. Non si fa, e' over-engineering per un rename one-shot.
- **Toccare `docs/superpowers/`** (spec e plan storici). Non si fa, glossario in questo spec basta.

---

## 12. Definition of done

- [ ] Tutte le 9 skill rinominate `sdlc-*` con frontmatter aggiornato
- [ ] Tutti i 5 agent rinominati `sdlc-*` con frontmatter aggiornato
- [ ] Tutte le 172+ cross-reference aggiornate
- [ ] Tutti i path file di output aggiornati (`CLARIFY/PLAN/TASKS`)
- [ ] Terminologia colloquiale aggiornata coerentemente
- [ ] `README.md` aggiornato (installazione + trigger templates + sezione migrazione)
- [ ] `scripts/migrate-sdlc-naming.sh` creato e funzionante (dry-run + apply)
- [ ] `scripts/sync-installed.sh` creato e funzionante (dry-run + apply)
- [ ] Grep di consistency in `skills/ agents/ README.md scripts/` ritorna 0 match sui pattern vecchi
- [ ] Commit + push su `claude-flow` (senza attribution)
- [ ] Sync `~/.claude/skills/` e `~/.claude/agents/` eseguito (zero residui `br-*`)
- [ ] `~/.claude/CLAUDE.md` aggiornato (9 sezioni trigger)
- [ ] Script di migrazione eseguito su `deloitte-profiles` con `--apply`
- [ ] Commit + push su `deloitte-profiles` (senza attribution)
- [ ] Smoke test su una skill `sdlc-*` confermato funzionante
