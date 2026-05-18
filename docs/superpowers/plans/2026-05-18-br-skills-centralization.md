# BR Skills Centralization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralizzare tutti gli artefatti BR nella repo `deloitte-profiles`, eliminare la portal-flow e la cross-branch aggregation da tutte le skill BR.

**Architecture:** Ogni skill passa da path relativi alla repo del codice (`plans/todo/...`) a path risolti via `.br-local.json` → `<profiles_repo>/<profilo>/plans/...`. Tutte le operazioni su `deloitte-profiles` sono precedute da `git pull` e seguite da `git add + commit + push`. La logica portal-flow (`brs/`, `manifest.json`) viene rimossa da tutte le skill. La cross-branch aggregation viene rimossa e sostituita dalla lettura diretta dopo pull.

**Tech Stack:** Markdown (SKILL.md files), JSON (profile-schema.json, .br-local.json)

**File da modificare:**
- `~/.claude/skills/br-profile-setup/SKILL.md`
- `~/.claude/skills/br-reviewer/SKILL.md`
- `~/.claude/skills/br-clarify/SKILL.md`
- `~/.claude/skills/br-analyzer/SKILL.md`
- `~/.claude/skills/br-executor/SKILL.md`
- `~/.claude/skills/br-updater/SKILL.md`
- `~/.claude/skills/br-debug/SKILL.md`
- `~/.claude/skills/br-progress-report/SKILL.md`
- `~/.claude/skills/br-estimator/SKILL.md`
- `~/.claude/skills/br-pipeline/SKILL.md` (da eliminare)
- `~/.claude/CLAUDE.md`
- `~/.claude/skills/BR_SKILLS_DOCUMENTATION.md`
- `~/.claude/agents/br-estimation-historian.md`
- `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/README.md`
- `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json`

**Convenzione path:** in tutto il piano, `~/.claude/` = `C:/Users/davmelis/.claude/`

---

### Task 1: Blocco comune — Pattern di risoluzione path

Questo blocco di testo deve essere inserito in ogni skill (Task 2-10) come sezione comune. Definirlo qui una volta e riferirsi a "Blocco Path Resolution" nelle task successive.

**Blocco Path Resolution:**

```markdown
## Risoluzione Path — deloitte-profiles

Tutte le operazioni su file BR (piani, report, progressi) avvengono nella repo `deloitte-profiles`, non nella repo del codice.

### Lettura `.br-local.json`

All'avvio, leggi `.br-local.json` dalla root della repo corrente:

```bash
cat .br-local.json 2>/dev/null
```

Estrai i campi:
- `profiles_repo` — path assoluto al clone locale di `deloitte-profiles`
- `profilo` — nome della cartella progetto in `deloitte-profiles`
- `developer` — nome dello sviluppatore (usato da br-executor e br-debug)

Il **base path** per tutti gli artefatti BR e': `<profiles_repo>/<profilo>/plans/`

### Se `.br-local.json` non esiste

**Skill da TL/PM** (br-profile-setup, br-reviewer, br-analyzer, br-estimator):

> `.br-local.json` non trovato. Devi prima eseguire `br-profile-setup` per creare il profilo del progetto e configurare il collegamento.

Ferma l'esecuzione.

**Skill da developer** (br-executor, br-debug):

> `.br-local.json` non trovato. Per collegarti al profilo esistente, ho bisogno di:
> 1. **Path del clone di deloitte-profiles** (es. `C:/Users/dev/Documents/deloitte-profiles`)
> 2. **Nome del profilo** (es. `banca-agente`)
> 3. **Il tuo nome** (come appare nel piano di implementazione)

Dopo aver ricevuto i 3 campi, crea `.br-local.json`:

```json
{
  "profilo": "<profilo>",
  "profiles_repo": "<path>",
  "developer": "<nome>"
}
```

### Sincronizzazione prima della lettura

Prima di leggere qualsiasi file dalla repo profili:

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

### Commit e push dopo la scrittura

Dopo ogni scrittura di artefatti nella repo profili:

```bash
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "<messaggio>"
git -C "<profiles_repo>" push origin main --quiet
```

Se il push fallisce, avvisa l'utente e proponi: (1) riprovare, (2) creare un branch, (3) lasciare il commit locale.
```

- [ ] **Step 1: Salvare il blocco come riferimento**

Non c'e' un file da creare. Questo testo e' il riferimento da inserire in ogni skill nelle task successive. Procedi alla Task 2.

---

### Task 2: br-profile-setup — Nuova struttura directory

**Files:**
- Modify: `~/.claude/skills/br-profile-setup/SKILL.md`

- [ ] **Step 1: Aggiornare Step 8 — path profile.json**

Trovare in Step 8 il comando `mkdir`:
```
mkdir -p "<profiles_repo>/<nome>"
```

Sostituire con:
```
mkdir -p "<profiles_repo>/<nome>/constitution"
mkdir -p "<profiles_repo>/<nome>/agents"
mkdir -p "<profiles_repo>/<nome>/references"
mkdir -p "<profiles_repo>/<nome>/plans/todo"
mkdir -p "<profiles_repo>/<nome>/plans/in-progress"
mkdir -p "<profiles_repo>/<nome>/plans/done"
```

E il commento `# Scrivi profile.json con il contenuto confermato` diventa:
```
# Scrivi constitution/profile.json con il contenuto confermato
```

- [ ] **Step 2: Aggiornare Step 7 — path references**

Trovare:
```
mkdir -p "<profiles_repo>/<nome>/references"
cp "<file>" "<profiles_repo>/<nome>/references/"
```

Gia' corretto — `references/` era gia' sotto il nome del progetto. Nessuna modifica necessaria, ma verificare che il path sia coerente.

- [ ] **Step 3: Aggiornare Step 9 — messaggio commit**

Il messaggio di commit resta invariato: `feat: add profile for <nome>`. Nessuna modifica.

- [ ] **Step 4: Aggiornare Step 5 — output di conferma**

Trovare il blocco di presentazione Step 5 e aggiornare il path del profilo:
```
> - Profilo: `<profiles_repo>/<nome>/profile.json`
```
Sostituire con:
```
> - Profilo: `<profiles_repo>/<nome>/constitution/profile.json`
```

- [ ] **Step 5: Aggiornare Step 10 — conferma finale**

Trovare:
```
> - Profilo: `<profiles_repo>/<nome>/profile.json`
```
Sostituire con:
```
> - Profilo: `<profiles_repo>/<nome>/constitution/profile.json`
> - Struttura: `constitution/`, `agents/`, `references/`, `plans/todo|in-progress|done/`
```

- [ ] **Step 6: Verifica**

Rileggere il file e verificare:
- Nessuna occorrenza di `<profiles_repo>/<nome>/profile.json` (deve essere tutto `constitution/profile.json`)
- Presenza di `mkdir` per `constitution`, `agents`, `plans/todo`, `plans/in-progress`, `plans/done`
- `references` gia' presente

- [ ] **Step 7: Commit**

```bash
cd ~/.claude && git add skills/br-profile-setup/SKILL.md && git commit -m "refactor(br-profile-setup): new directory structure with constitution/, agents/, plans/"
```

---

### Task 3: br-reviewer — Path centralizzati + rename requirements

**Files:**
- Modify: `~/.claude/skills/br-reviewer/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo la sezione "Il processo si compone di 4 fasi:" e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1, adattato con la nota: skill da TL/PM (ferma se `.br-local.json` non esiste).

- [ ] **Step 2: Aggiornare Fase 1 — Domanda 1 (Nome del BR)**

Trovare:
```
Salva il nome. Verra' usato per creare la cartella `plans/todo/<YYYY-MM-DD>_<nome>/`.
```

Sostituire con:
```
Salva il nome. Verra' usato per creare la cartella `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`.
```

- [ ] **Step 3: Aggiornare Fase 1 — Riepilogo**

Trovare:
```
> - Nome BR: [nome] → cartella `plans/todo/<YYYY-MM-DD>_<nome>/`
```

Sostituire con:
```
> - Nome BR: [nome] → cartella `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`
```

- [ ] **Step 4: Aggiornare Fase 2 — mkdir**

Trovare:
```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted"
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
mkdir -p "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements"
```

- [ ] **Step 5: Rinominare br-docs-converted → requirements in tutto il file**

Eseguire find-and-replace globale nel file:
- `br-docs-converted/` → `requirements/`
- `br-docs-converted` → `requirements` (senza slash dove serve)

Ogni occorrenza di path con `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/` diventa `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements/`.

- [ ] **Step 6: Aggiornare tutti i path plans/todo/ → path centralizzato**

Eseguire find-and-replace in tutto il file:
- `plans/todo/<YYYY-MM-DD>_<nome>/` → `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`

Attenzione: non duplicare se gia' sostituito nello step precedente.

- [ ] **Step 7: Aggiornare Fase 4 — dopo la generazione, commit e push**

Dopo la generazione di REVIEW_BR.md e REVIEW_BR.docx, aggiungere:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/"
git -C "<profiles_repo>" commit -m "[br-reviewer] <nome>: review documentazione completata"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 8: Aggiornare i messaggi utente con i path corretti**

Aggiornare tutti i messaggi che mostrano path all'utente (es. "I report sono salvati in `plans/todo/...`") per usare il path centralizzato.

- [ ] **Step 9: Verifica**

Rileggere il file e verificare:
- Zero occorrenze di `br-docs-converted`
- Zero occorrenze di `plans/todo/` senza il prefisso `<profiles_repo>/<profilo>/` (tranne nei path degli output pandoc che usano path assoluti gia' risolti)
- Presenza di `git pull` prima della lettura e `git commit + push` dopo la scrittura

- [ ] **Step 10: Commit**

```bash
cd ~/.claude && git add skills/br-reviewer/SKILL.md && git commit -m "refactor(br-reviewer): centralize paths to deloitte-profiles, rename br-docs-converted to requirements"
```

---

### Task 4: br-clarify — Path centralizzati

**Files:**
- Modify: `~/.claude/skills/br-clarify/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo "Il processo si compone di 6 fasi:" e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1. Skill da TL/PM.

- [ ] **Step 2: Aggiornare Fase 1 — Auto-detect**

Trovare:
```bash
ls plans/todo/*/REVIEW_BR.md 2>/dev/null
ls plans/in-progress/*/REVIEW_BR.md 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls "<profiles_repo>/<profilo>/plans/todo"/*/REVIEW_BR.md 2>/dev/null
ls "<profiles_repo>/<profilo>/plans/in-progress"/*/REVIEW_BR.md 2>/dev/null
```

- [ ] **Step 3: Aggiornare il messaggio "non trovato"**

Trovare:
```
> Non ho trovato nessun REVIEW_BR.md nella struttura `plans/`.
```

Sostituire con:
```
> Non ho trovato nessun REVIEW_BR.md nella struttura `<profiles_repo>/<profilo>/plans/`.
```

- [ ] **Step 4: Aggiornare tutti i path `plans/todo/` e `plans/in-progress/`**

Sostituire in tutto il file ogni occorrenza di:
- `plans/todo/<YYYY-MM-DD>_<nome>/` → `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`
- `plans/in-progress/<YYYY-MM-DD>_<nome>/` → `<profiles_repo>/<profilo>/plans/in-progress/<YYYY-MM-DD>_<nome>/`

- [ ] **Step 5: Aggiornare il file temporaneo**

Trovare:
```
`<cartella-br>/REVIEW_BR_risposte_temp.md`
```

Il `<cartella-br>` e' gia' un placeholder — deve risolvere al path centralizzato. Nessuna modifica se il placeholder e' generico, ma verificare che nel contesto sia chiaro che `<cartella-br>` = `<profiles_repo>/<profilo>/plans/<stato>/<data>_<nome>/`.

- [ ] **Step 6: Aggiungere commit+push dopo la scrittura**

Dopo la sezione 5.4 (rigenerazione DOCX), aggiungere:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-clarify] <nome>: aggiornato review con risposte funzionale"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 7: Verifica**

Rileggere il file e verificare:
- Zero occorrenze di `plans/todo/` o `plans/in-progress/` senza prefisso `<profiles_repo>/<profilo>/`
- Presenza di git pull prima della lettura e git commit+push dopo la scrittura

- [ ] **Step 8: Commit**

```bash
cd ~/.claude && git add skills/br-clarify/SKILL.md && git commit -m "refactor(br-clarify): centralize paths to deloitte-profiles"
```

---

### Task 5: br-analyzer — Path centralizzati + rename requirements

**Files:**
- Modify: `~/.claude/skills/br-analyzer/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo "Il processo si compone di 4 fasi:" e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1. Skill da TL/PM.

- [ ] **Step 2: Aggiornare Domanda 0 — ricerca REVIEW_BR.md**

Trovare:
```bash
ls plans/todo/*/REVIEW_BR.md 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls "<profiles_repo>/<profilo>/plans/todo"/*/REVIEW_BR.md 2>/dev/null
```

- [ ] **Step 3: Rinominare br-docs-converted → requirements in tutto il file**

Eseguire find-and-replace globale:
- `br-docs-converted/` → `requirements/`
- `br-docs-converted` → `requirements`

- [ ] **Step 4: Aggiornare tutti i path plans/ → path centralizzato**

Sostituire in tutto il file ogni occorrenza di:
- `plans/todo/<YYYY-MM-DD>_<nome>/` → `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`
- `plans/in-progress` → `<profiles_repo>/<profilo>/plans/in-progress`
- `plans/done` → `<profiles_repo>/<profilo>/plans/done`

- [ ] **Step 5: Aggiornare Fase 4 — mkdir**

Trovare:
```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>" plans/in-progress plans/done
```

Sostituire con:
```bash
mkdir -p "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements"
```

(Le cartelle `in-progress` e `done` sono gia' create da `br-profile-setup`.)

- [ ] **Step 6: Aggiungere nota — il codice resta nella repo del progetto**

Nella sezione Fase 3 (Analisi Gap), dopo la descrizione dell'esplorazione codebase, aggiungere:

```markdown
**Nota**: il codebase viene letto dalla repo del progetto (dove la skill e' invocata). Solo gli artefatti BR (report, piano) vengono scritti in `deloitte-profiles`.
```

- [ ] **Step 7: Aggiungere commit+push dopo la generazione output**

Dopo la generazione di GAP_REPORT_BR.md e PIANO_IMPLEMENTAZIONE_BR.md, aggiungere:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/"
git -C "<profiles_repo>" commit -m "[br-analyzer] <nome>: gap report e piano di implementazione"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 8: Verifica**

Rileggere e verificare:
- Zero `br-docs-converted`
- Zero `plans/todo/` senza prefisso centralizzato
- git pull prima, git push dopo
- Il codice sorgente viene letto dalla repo locale, non da deloitte-profiles

- [ ] **Step 9: Commit**

```bash
cd ~/.claude && git add skills/br-analyzer/SKILL.md && git commit -m "refactor(br-analyzer): centralize paths to deloitte-profiles, rename br-docs-converted to requirements"
```

---

### Task 6: br-executor — Path centralizzati + rimozione cross-branch aggregation

**Files:**
- Modify: `~/.claude/skills/br-executor/SKILL.md`

Questa e' la skill con le modifiche piu' ampie: rimuovere la cross-branch aggregation, aggiornare i path, aggiungere git pull/push, rimuovere la retrocompatibilita' flat.

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo il paragrafo introduttivo e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1. Skill da developer (crea `.br-local.json` se non esiste).

- [ ] **Step 2: Aggiornare Fase 1 — Domanda 1 (ricerca file piano)**

Trovare il blocco con:
```bash
ls -d plans/todo/*/ plans/in-progress/*/ plans/done/*/ 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/done"/*/ 2>/dev/null
```

- [ ] **Step 3: Rimuovere la retrocompatibilita' flat**

Rimuovere completamente i blocchi "Se trovi file flat (retrocompatibilita')" nella Fase 1 e nel completamento task. Questi blocchi gestiscono file senza sottocartella (es. `plans/todo/GAP_REPORT_BR_2026-04-24.md`). Con la centralizzazione non servono piu'.

Blocchi da rimuovere:
- Fase 1, Domanda 1: il blocco `**Se trovi file flat**` con l'esempio path flat
- Spostamento in `plans/in-progress/`: il blocco `Se stai lavorando con file flat (retrocompatibilita')`
- Completamento di tutte le task: il blocco `Se stai lavorando con file flat (retrocompatibilita')`

- [ ] **Step 4: Aggiornare lo spostamento in plans/in-progress/**

Trovare:
```bash
mkdir -p plans/in-progress
mv "plans/todo/<YYYY-MM-DD>_<nome>/" "plans/in-progress/" 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" mv "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/" "<profilo>/plans/in-progress/"
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "[br-executor] <nome>: avvio lavorazione, spostato in in-progress"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 5: Rimuovere TUTTA la sezione "Lettura progresso aggregata (cross-branch)"**

Rimuovere l'intera sezione che inizia con `### Lettura progresso aggregata (cross-branch)` e tutti i suoi sotto-punti (1-7 + fallback). Questa sezione e' lunga e contiene tutta la logica `git fetch`, `git show origin/<branch>:plans/...`, aggregazione "highest progress wins".

Sostituire con:

```markdown
### Lettura progresso

Prima di leggere il file di progresso, sincronizza la repo profili:

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

Leggi il PROGRESSO_BR.md dalla cartella del BR in `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/PROGRESSO_BR.md`.

Tutti gli sviluppatori scrivono nello stesso file nella repo centralizzata, quindi il progresso e' sempre aggiornato dopo il pull.
```

- [ ] **Step 6: Semplificare il controllo dipendenze**

Trovare il paragrafo sul controllo dipendenze che menziona "vista aggregata". Sostituire ogni riferimento a "vista aggregata" con "file di progresso" (dopo il pull e' gia' aggiornato).

- [ ] **Step 7: Aggiornare tutti i path plans/ → path centralizzato**

Sostituire in tutto il file:
- `plans/todo/` → `<profiles_repo>/<profilo>/plans/todo/`
- `plans/in-progress/` → `<profiles_repo>/<profilo>/plans/in-progress/`
- `plans/done/` → `<profiles_repo>/<profilo>/plans/done/`

Attenzione: i path del codice sorgente (repo del progetto) restano invariati.

- [ ] **Step 8: Aggiornare lo spostamento in plans/done/**

Trovare:
```bash
mkdir -p plans/done
mv "plans/in-progress/<YYYY-MM-DD>_<nome>/" "plans/done/" 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" mv "<profilo>/plans/in-progress/<YYYY-MM-DD>_<nome>/" "<profilo>/plans/done/"
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "[br-executor] <nome>: tutte le task completate, spostato in done"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 9: Aggiungere commit+push dopo ogni aggiornamento del progresso**

Dopo ogni aggiornamento del PROGRESSO_BR.md (cambio stato task, aggiornamento percentuale), aggiungere:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/in-progress/<data>_<nome>/PROGRESSO_BR.md"
git -C "<profiles_repo>" commit -m "[br-progress] <task-id> -> <progresso>%"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 10: Rimuovere la Domanda 2 (Path dei codebase locali)**

La Domanda 2 chiede i path delle repo perche' lo sviluppatore puo' lavorare su un PC diverso. Con la centralizzazione, i path delle repo vanno ancora chiesti (il codice resta nelle repo del progetto). Tuttavia, rimuovere il riferimento ai "path originali dal report" e semplificare — il piano in deloitte-profiles ha gia' i path.

Aggiornare il messaggio per non menzionare "PC diverso" ma semplicemente chiedere conferma dei path.

- [ ] **Step 11: Aggiornare i suggerimenti di commit**

I suggerimenti di commit per il codice sorgente restano invariati (il codice va committato nella repo del progetto). Aggiungere pero' un suggerimento separato per il commit del progresso in deloitte-profiles.

Dopo ogni suggerimento di commit nella repo del progetto, aggiungere:

```
> **Repo profili** — il progresso e' gia' stato aggiornato e pushato automaticamente.
```

- [ ] **Step 12: Verifica**

Rileggere e verificare:
- Zero occorrenze di `git show origin/<branch>:plans/`
- Zero occorrenze di `git fetch origin`
- Zero occorrenze di "aggregata" o "cross-branch"
- Zero occorrenze di "file flat" o "retrocompatibilita'"
- Zero `plans/` senza prefisso centralizzato (tranne i path del codice sorgente)
- git pull prima di ogni lettura, git push dopo ogni scrittura

- [ ] **Step 13: Commit**

```bash
cd ~/.claude && git add skills/br-executor/SKILL.md && git commit -m "refactor(br-executor): centralize to deloitte-profiles, remove cross-branch aggregation and flat compat"
```

---

### Task 7: br-updater — Path centralizzati + rename requirements

**Files:**
- Modify: `~/.claude/skills/br-updater/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo il paragrafo introduttivo e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1. Skill da TL/PM.

- [ ] **Step 2: Aggiornare Fase 1 — ricerca automatica**

Trovare:
```bash
ls -d plans/in-progress/*/ plans/todo/*/ 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/todo"/*/ 2>/dev/null
```

- [ ] **Step 3: Rimuovere retrocompatibilita' flat**

Rimuovere il blocco `**Se trovi file flat**` nella Fase 1.

- [ ] **Step 4: Rinominare br-docs-converted → requirements**

Find-and-replace globale: `br-docs-converted` → `requirements`

- [ ] **Step 5: Aggiornare tutti i path plans/ → centralizzato**

Sostituire in tutto il file:
- `plans/in-progress/` → `<profiles_repo>/<profilo>/plans/in-progress/`
- `plans/todo/` → `<profiles_repo>/<profilo>/plans/todo/`

- [ ] **Step 6: Aggiungere commit+push dopo l'aggiornamento**

Dopo la Fase 3 (aggiornamento report, piano, progresso), aggiungere:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-updater] <nome>: aggiornato piano da nuova documentazione"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 7: Verifica**

Zero `br-docs-converted`, zero `plans/` senza prefisso, zero "flat", git pull/push presenti.

- [ ] **Step 8: Commit**

```bash
cd ~/.claude && git add skills/br-updater/SKILL.md && git commit -m "refactor(br-updater): centralize to deloitte-profiles, rename br-docs-converted to requirements"
```

---

### Task 8: br-debug — Rimozione portal-flow + path centralizzati

**Files:**
- Modify: `~/.claude/skills/br-debug/SKILL.md`

Questa skill ha la maggiore quantita' di logica portal-flow da rimuovere.

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo il paragrafo introduttivo e prima di "## Rilevamento Contesto", inserire il **Blocco Path Resolution** dalla Task 1. Skill da developer.

- [ ] **Step 2: Rimuovere la sezione "Rilevamento Contesto"**

Rimuovere l'intera sezione "## Rilevamento Contesto" che distingue portal-flow e claude-flow. Non serve piu'.

- [ ] **Step 3: Aggiornare "Caricamento Profilo Progetto"**

Questa sezione legge `.br-local.json` — e' gia' coperta dal Blocco Path Resolution. Semplificare per leggere solo il profilo:

Trovare il blocco che inizia con "1. Leggi `.br-local.json`" e contiene la logica `profilo` + `profiles_repo`.

Sostituire con una versione che dice semplicemente: "Dopo aver risolto i path (vedi sezione precedente), se il profilo e' disponibile, leggi `<profiles_repo>/<profilo>/constitution/profile.json`."

Nota: il path del profile.json cambia da `<profilo>/profile.json` a `<profilo>/constitution/profile.json`.

- [ ] **Step 4: Rimuovere la sezione "Rilevamento Modalita'"**

Rimuovere l'intera sezione che distingue import/execution/chiusura in base a portal-flow o claude-flow. Riscriverla senza menzione di portal-flow:

```markdown
## Rilevamento Modalita'

La skill rileva automaticamente la modalita' di funzionamento:

- **Import mode**: non esiste `BUG_REPORT_BR.md` nella cartella del BR, oppure l'utente dice "ci sono dei bug", "segnalazioni test", "defect ricevuti"
- **Execution mode**: esistono bug assegnati allo sviluppatore con stato diverso da `chiuso`, oppure l'utente dice "lavora il bug", "fix il bug"
- **Chiusura mode**: l'utente dice "il funzionale ha testato", "bug confermati", "aggiorna i bug"
```

- [ ] **Step 5: Aggiornare Fase 1 — Domanda 1 (BR di riferimento)**

Rimuovere il blocco `**Portal-flow:**` con `ls brs/*/manifest.json`.

Aggiornare il blocco `**Claude-flow:**`:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/done"/*/ 2>/dev/null
```

- [ ] **Step 6: Aggiornare path screenshot**

Trovare:
```
- Portal-flow: `brs/<nome>/screenshots/`
- Claude-flow: `plans/in-progress/<data>_<nome>/screenshots/` (o `plans/todo/` se non ancora in-progress)
```

Sostituire con:
```
`<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/screenshots/` (o `plans/todo/` se non ancora in-progress)
```

- [ ] **Step 7: Rimuovere la sezione "Scrittura — Portal-flow"**

Rimuovere l'intera sezione che scrive il manifest JSON (`manifest.bugs`, `bugs.lista[]`, `timeline[]`). Lasciare solo la sezione "Scrittura — Claude-flow" rinominata come "Scrittura BUG_REPORT_BR.md".

Aggiornare il path: `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/BUG_REPORT_BR.md`.

- [ ] **Step 8: Aggiornare la condizione di completamento debug**

Rimuovere il blocco `**Portal-flow:**` con `manifest.bugs.debug_attivo` e `timeline`.

Lasciare solo la logica claude-flow (aggiungere sezione "Debug completato" al BUG_REPORT_BR.md).

- [ ] **Step 9: Rimuovere i riferimenti a portal-flow nelle Regole Fondamentali e Context**

Trovare la regola:
```
7. **Supportare entrambe le modalita'** (claude-flow e portal-flow) senza compromessi.
```
Rimuoverla.

Aggiornare la sezione Context in fondo al file rimuovendo i riferimenti a portal-flow e manifest.json.

- [ ] **Step 10: Aggiornare tutti i path plans/ → centralizzato**

Sostituire in tutto il file `plans/in-progress/<data>_<nome>/` → `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/`.

- [ ] **Step 11: Aggiungere commit+push dopo ogni scrittura**

Dopo ogni scrittura di BUG_REPORT_BR.md e dopo ogni cambio stato bug:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-debug] <nome>: <azione>"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 12: Verifica**

Rileggere e verificare:
- Zero occorrenze di `portal-flow`, `manifest.json`, `manifest.bugs`, `brs/`
- Zero occorrenze di `plans/` senza prefisso centralizzato
- `profile.json` → `constitution/profile.json`
- git pull/push presenti

- [ ] **Step 13: Commit**

```bash
cd ~/.claude && git add skills/br-debug/SKILL.md && git commit -m "refactor(br-debug): remove portal-flow, centralize to deloitte-profiles"
```

---

### Task 9: br-progress-report — Path centralizzati + rimozione cross-branch aggregation

**Files:**
- Modify: `~/.claude/skills/br-progress-report/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo il titolo e prima di "## Fase 1", inserire il **Blocco Path Resolution** dalla Task 1. Skill da TL/PM.

- [ ] **Step 2: Aggiornare Fase 1 — ricerca automatica**

Trovare:
```bash
ls -d plans/in-progress/*/ plans/todo/*/ plans/done/*/ 2>/dev/null
```

Sostituire con:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/done"/*/ 2>/dev/null
```

- [ ] **Step 3: Rimuovere retrocompatibilita' flat**

Rimuovere i blocchi "Se trovi file flat" e i path flat nelle fasi 1 e 4.

- [ ] **Step 4: Rimuovere TUTTA la sezione "Lettura progresso aggregata (cross-branch)"**

Rimuovere l'intera Fase 2 sezione "Lettura progresso aggregata (cross-branch)" con tutti i sotto-punti (1-7 + fallback). Sostituire con:

```markdown
### Lettura progresso

Sincronizza la repo profili prima di leggere:

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

Leggi il PROGRESSO_BR.md dalla cartella del BR in `<profiles_repo>/<profilo>/plans/<stato>/<data>_<nome>/PROGRESSO_BR.md`. Il file e' sempre aggiornato dopo il pull perche' tutti gli sviluppatori scrivono nella repo centralizzata.
```

- [ ] **Step 5: Aggiornare tutti i path plans/ → centralizzato**

Sostituire in tutto il file.

- [ ] **Step 6: Aggiungere commit+push dopo la generazione Excel**

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-progress-report] <nome>: aggiornato Excel avanzamento"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 7: Verifica**

Zero "aggregata", zero "cross-branch", zero "git fetch", zero "git show origin", zero "flat", zero `plans/` senza prefisso.

- [ ] **Step 8: Commit**

```bash
cd ~/.claude && git add skills/br-progress-report/SKILL.md && git commit -m "refactor(br-progress-report): centralize to deloitte-profiles, remove cross-branch aggregation"
```

---

### Task 10: br-estimator — Rimozione portal-flow + path centralizzati

**Files:**
- Modify: `~/.claude/skills/br-estimator/SKILL.md`

- [ ] **Step 1: Inserire la sezione Path Resolution**

Dopo il titolo e prima di "## Rilevamento Contesto", inserire il **Blocco Path Resolution** dalla Task 1. Skill da TL/PM.

- [ ] **Step 2: Rimuovere/semplificare "Rilevamento Contesto"**

Rimuovere:
```markdown
- **Se trova `brs/<nome>/manifest.json`** → modalita' **portal-flow**
- **Se trova `plans/*/PIANO_IMPLEMENTAZIONE_BR.md` senza manifest** → modalita' **claude-flow**
```

Sostituire con:
```markdown
La skill cerca il piano di implementazione in `<profiles_repo>/<profilo>/plans/`.
```

- [ ] **Step 3: Semplificare "Rilevamento Modalita'"**

Rimuovere il riferimento a `manifest.piano.task[]`. Lasciare solo:
- Se esiste `PIANO_IMPLEMENTAZIONE_BR.md` → dettagliata
- Se non esiste → rough

- [ ] **Step 4: Aggiornare Domanda 1 — ricerca BR**

Rimuovere il blocco `**Portal-flow:**` con `ls brs/*/manifest.json`.

Aggiornare il blocco `**Claude-flow:**`:
```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/in-progress"/*/ 2>/dev/null
```

- [ ] **Step 5: Aggiornare Fase 2 — path per lo storico**

Il lancio dello storico usa `plans/done/` o `brs/`. Aggiornare:

Trovare:
```
- Claude-flow: `plans/done/`
- Portal-flow: `brs/*/manifest.json` (filtra quelli con `stato_pipeline: "done"`)
```

Sostituire con:
```
`<profiles_repo>/<profilo>/plans/done/`
```

- [ ] **Step 6: Aggiornare i path di output STIMA_BR**

Trovare:
```markdown
- Claude-flow: `plans/todo/<data>_<nome>/STIMA_BR.md` o `plans/in-progress/<data>_<nome>/STIMA_BR.md`
- Portal-flow: `brs/<nome>/STIMA_BR.md`
```

Sostituire con:
```markdown
`<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/STIMA_BR.md` (o `in-progress/` se il BR e' gia' in lavorazione)
```

- [ ] **Step 7: Aggiornare il commit alla fine**

Trovare:
```bash
git add <cartella-br>/STIMA_BR.md <cartella-br>/STIMA_BR.xlsx
git commit -m "[br-estimator] <nome-br>: stima team (<modalita'>)"
```

Sostituire con:
```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-estimator] <nome-br>: stima team (<modalita'>)"
git -C "<profiles_repo>" push origin main --quiet
```

- [ ] **Step 8: Rimuovere la regola "Supportare entrambe le modalita'"**

Trovare e rimuovere:
```
6. **Supportare entrambe le modalita'** (claude-flow e portal-flow) senza compromessi
```

- [ ] **Step 9: Verifica**

Zero `portal-flow`, `manifest`, `brs/`, `plans/` senza prefisso.

- [ ] **Step 10: Commit**

```bash
cd ~/.claude && git add skills/br-estimator/SKILL.md && git commit -m "refactor(br-estimator): remove portal-flow, centralize to deloitte-profiles"
```

---

### Task 11: Eliminare br-pipeline

**Files:**
- Delete: `~/.claude/skills/br-pipeline/SKILL.md`

- [ ] **Step 1: Eliminare il file**

```bash
rm ~/.claude/skills/br-pipeline/SKILL.md
rmdir ~/.claude/skills/br-pipeline/
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude && git add -A skills/br-pipeline/ && git commit -m "refactor: remove br-pipeline skill (replaced by centralized plans)"
```

---

### Task 12: Aggiornare CLAUDE.md

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Rimuovere la sezione br-pipeline**

Trovare e rimuovere l'intero blocco:

```
# br-pipeline
- **br-pipeline** (`~/.claude/skills/br-pipeline/SKILL.md`) - pipeline POM completo per gestione BR con manifest JSON e viste per ruolo. Trigger: "br-pipeline", "pipeline br", "le mie task"
When the user says "br-pipeline", "pipeline br", "le mie task", or similar phrases about the BR pipeline or viewing assigned tasks, invoke the Skill tool with `skill: "br-pipeline"` before doing anything else.
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude && git add CLAUDE.md && git commit -m "docs: remove br-pipeline from CLAUDE.md"
```

---

### Task 13: Aggiornare gli agenti

**Files:**
- Modify: `~/.claude/agents/br-estimation-historian.md`

- [ ] **Step 1: Aggiornare i path nel historian**

Trovare:
```
- Claude-flow: `plans/done/`
- Portal-flow: `brs/*/manifest.json` (filtra quelli con `stato_pipeline: "done"`)
```

Sostituire con:
```
Il path ai BR completati e': `<profiles_repo>/<profilo>/plans/done/`

Il `profiles_repo` e il `profilo` vengono passati come parametri dall'orchestratore (br-estimator).
```

Rimuovere tutte le occorrenze di `brs/`, `manifest`, `portal-flow` nel file.

- [ ] **Step 2: Aggiornare il path di scansione**

Trovare:
```bash
ls -d plans/done/*/ 2>/dev/null
```

Sostituire con:
```bash
ls -d "<plans_done_path>"/*/ 2>/dev/null
```

(Dove `<plans_done_path>` e' il parametro passato dall'orchestratore.)

- [ ] **Step 3: Verifica**

Leggere l'intero file e verificare zero occorrenze di `portal-flow`, `manifest`, `brs/`.

- [ ] **Step 4: Commit**

```bash
cd ~/.claude && git add agents/br-estimation-historian.md && git commit -m "refactor(br-estimation-historian): remove portal-flow references, use centralized path"
```

---

### Task 14: Aggiornare deloitte-profiles (README + schema)

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/README.md`
- Modify: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json`

- [ ] **Step 1: Aggiornare il README con la nuova struttura**

Leggere il README corrente. Aggiornare la sezione che descrive la struttura per progetto:

```
<nome-progetto>/
├── constitution/
│   └── profile.json
├── agents/           # agenti custom .md per questo progetto
├── references/       # mockup, screenshot, style guide
└── plans/
    ├── todo/         # BR in attesa di lavorazione
    │   └── <data>_<nome-br>/
    │       ├── requirements/
    │       ├── REVIEW_BR.md
    │       ├── GAP_REPORT_BR.md
    │       ├── PIANO_IMPLEMENTAZIONE_BR.md
    │       └── STIMA_BR.md / .xlsx
    ├── in-progress/  # BR in lavorazione
    │   └── <data>_<nome-br>/
    │       ├── PROGRESSO_BR.md
    │       ├── BUG_REPORT_BR.md
    │       ├── AVANZAMENTO_BR.xlsx
    │       └── screenshots/
    └── done/         # BR completati (archivio storico)
        └── <data>_<nome-br>/
```

- [ ] **Step 2: Aggiornare profile-schema.json**

Leggere lo schema corrente. Se il path `profile.json` e' referenziato nello schema, non serve cambiarlo (lo schema valida il contenuto, non il path). Ma verificare che non ci siano assunzioni sul path.

- [ ] **Step 3: Migrare il profilo esistente banca-agente**

Spostare `banca-agente/profile.json` → `banca-agente/constitution/profile.json`:

```bash
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
mkdir -p banca-agente/constitution
git mv banca-agente/profile.json banca-agente/constitution/profile.json
mkdir -p banca-agente/agents
mkdir -p banca-agente/plans/todo banca-agente/plans/in-progress banca-agente/plans/done
```

- [ ] **Step 4: Commit e push**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
git add .
git commit -m "refactor: new directory structure — constitution/, agents/, plans/, rename br-docs-converted to requirements"
git push origin main
```

---

### Task 15: Aggiornare BR_SKILLS_DOCUMENTATION.md

**Files:**
- Modify: `~/.claude/skills/BR_SKILLS_DOCUMENTATION.md`

- [ ] **Step 1: Leggere il file corrente**

Leggere il file per capire la struttura attuale.

- [ ] **Step 2: Aggiornare con la nuova architettura**

Aggiornare tutte le sezioni che descrivono:
- I path dei file (da `plans/` locale a `<profiles_repo>/<profilo>/plans/`)
- La dualita' claude-flow / portal-flow (rimuovere portal-flow)
- La cross-branch aggregation (rimuovere, sostituire con "lettura diretta dopo pull")
- Il rename `br-docs-converted` → `requirements`
- Il nuovo path `constitution/profile.json`
- La rimozione di br-pipeline
- La nuova struttura directory in deloitte-profiles

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/BR_SKILLS_DOCUMENTATION.md && git commit -m "docs: update BR_SKILLS_DOCUMENTATION.md for centralized architecture"
```

---

### Task 16: Verifica finale

- [ ] **Step 1: Grep di controllo su tutte le skill**

Verificare che non rimangano riferimenti residui:

```bash
grep -rl "portal-flow\|portal_flow\|manifest\.json\|brs/" ~/.claude/skills/br-*/SKILL.md ~/.claude/agents/br-*.md
```

Output atteso: nessun risultato.

```bash
grep -rl "br-docs-converted" ~/.claude/skills/br-*/SKILL.md
```

Output atteso: nessun risultato.

```bash
grep -rl "cross-branch\|git show origin" ~/.claude/skills/br-*/SKILL.md
```

Output atteso: nessun risultato.

- [ ] **Step 2: Verificare che tutti i commit siano stati fatti**

```bash
cd ~/.claude && git log --oneline -20
```

Verificare la presenza di tutti i commit delle task 2-15.

- [ ] **Step 3: Segnalare completamento**

> Centralizzazione completata. Tutte le skill BR ora leggono e scrivono in `deloitte-profiles`. Portal-flow rimossa. Cross-branch aggregation rimossa. br-pipeline eliminata.
