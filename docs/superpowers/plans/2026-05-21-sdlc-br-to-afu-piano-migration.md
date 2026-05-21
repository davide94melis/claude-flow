# SDLC `BR` → `AFU` / `Piano` Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sostituire la terminologia "BR" (Business Requirement) con "AFU" (Analisi Funzionale Utente) per il documento di input e "Piano" per l'unità di lavoro nelle 9 skill SDLC, mantenendo zero break per i profili esistenti e i trigger naturali in italiano corporate.

**Architecture:** Migrazione wave-based in 4 commit atomici. Wave 1 aggiunge lettura compatibile del file config (`.sdlc-local.json` con fallback `.br-local.json`). Wave 2 applica il mapping testuale BR→AFU/Piano nelle 9 SKILL.md. Wave 3 fa scrivere il nuovo nome a `sdlc-profile-setup` con migrazione automatica del file legacy. Wave 4 allinea la documentazione esterna (SDLC_SKILLS_DOCUMENTATION.md, ~/.claude/CLAUDE.md, docs/ROADMAP_NEW_SKILLS.md). Ogni wave è retro-compatibile e revertabile in isolamento.

**Tech Stack:** Markdown skill files (~/.claude/skills/sdlc-*/SKILL.md), JSON config (`.br-local.json`/`.sdlc-local.json`), git (commit atomici per wave), grep (verifica zero-occorrenze residue).

**Spec di riferimento:** [docs/superpowers/specs/2026-05-21-sdlc-br-to-afu-piano-migration-design.md](../specs/2026-05-21-sdlc-br-to-afu-piano-migration-design.md)

---

## Glossary & Mapping Rules (riferimento per tutte le wave)

Queste regole sono **condivise da Wave 2 e Wave 4**. Ogni task le invocherà esplicitamente.

### MAPPING-AFU (documento di input)

Pattern di testo BR → AFU. Si applicano quando "BR" si riferisce al **documento di specifica funzionale** o ai suoi contenuti.

| Pattern old | Pattern new |
|---|---|
| `documentazione BR` | `documentazione AFU` |
| `documenti BR` | `documenti AFU` |
| `il BR descrive` | `l'AFU descrive` |
| `il BR presuppone` | `l'AFU presuppone` |
| `il BR è ambiguo` | `l'AFU è ambigua` |
| `il BR dice` | `l'AFU dice` |
| `il BR non menziona` | `l'AFU non menziona` |
| `del BR` (riferito al documento input) | `dell'AFU` |
| `dal BR` | `dall'AFU` |
| `Cosa richiede il BR` | `Cosa richiede l'AFU` |
| `richieste dal BR` | `richieste dall'AFU` |
| `Concetto BR` (header tabella) | `Concetto AFU` |
| `BR vs mockup` | `AFU vs mockup` |
| `BR vs specifiche tecniche` | `AFU vs specifiche tecniche` |
| `BR (Business Requirement)` | `AFU (Analisi Funzionale Utente)` |
| `BR (il documento principale dei requisiti)` | `AFU (il documento principale dei requisiti)` |
| `Analista BR` (agente che analizza il documento) | `Analista AFU` |
| `Verifica BR` (header file output review) | `Verifica AFU` |
| `Review Documentazione BR` | `Review Documentazione AFU` |

### MAPPING-PIANO (workflow / unità di lavoro)

Pattern di testo BR → Piano. Si applicano quando "BR" si riferisce alla **cartella di lavoro, allo stato, all'identificatore o agli artefatti generati**.

| Pattern old | Pattern new |
|---|---|
| `cartella BR` | `cartella del Piano` |
| `cartelle BR` | `cartelle dei Piani` |
| `cartella del BR` | `cartella del Piano` |
| `Nome BR` | `Nome Piano` |
| `nome BR` | `nome Piano` |
| `<nome BR>` | `<nome Piano>` |
| `BR di riferimento` | `Piano di riferimento` |
| `Domanda 1 — BR di riferimento` | `Domanda 1 — Piano di riferimento` |
| `il BR passa a` | `il Piano passa a` |
| `BR in stato` | `Piano in stato` |
| `il BR è in stato` | `il Piano è in stato` |
| `Cerca i BR attivi` | `Cerca i Piani attivi` |
| `BR attivi` | `Piani attivi` |
| `cartelle BR nelle tre aree` | `cartelle dei Piani nelle tre aree` |
| `cartelle BR nella struttura` | `cartelle dei Piani nella struttura` |
| `artefatti BR` | `artefatti del Piano` |
| `file BR` | `file del Piano` |
| `operazioni su file BR` | `operazioni sui file del Piano` |
| `BR passati` | `Piani passati` |
| `K BR precedenti` | `K Piani precedenti` |
| `N BR precedenti` | `N Piani precedenti` |
| `da K BR precedenti` | `da K Piani precedenti` |
| `da N BR precedenti` | `da N Piani precedenti` |
| `BR passati dallo storico` | `Piani passati dallo storico` |
| `Stima BR` (header file output) | `Stima Piano` |
| `Bug Report — <nome BR>` | `Bug Report — <nome Piano>` |
| `Progresso Implementazione [Nome BR]` | `Progresso Implementazione [Nome Piano]` |
| `Come vuoi chiamare questo BR?` | `Come vuoi chiamare questo Piano?` |
| `Quali sono le repository/codebase coinvolte in questo BR?` | `Quali sono le repository/codebase coinvolte in questo Piano?` |
| `Quali sono le repository coinvolte in questo BR` | `Quali sono le repository coinvolte in questo Piano` |
| `Se una repo non è coinvolta nel BR` | `Se una repo non è coinvolta nel Piano` |
| `Se una repo non e' coinvolta nel BR` | `Se una repo non e' coinvolta nel Piano` |
| `repo non è coinvolta nel BR, non includerla` | `repo non è coinvolta nel Piano, non includerla` |
| `lavorazione di un BR` | `lavorazione di un Piano` |

### MAPPING-SDLC (processo generale)

Pattern di testo BR → SDLC. Si applicano quando "BR" si riferisce al **processo o ciclo di vita complessivo**.

| Pattern old | Pattern new |
|---|---|
| `flusso BR completo` | `flusso SDLC completo` |
| `flusso BR` | `flusso SDLC` |
| `nel flusso BR` | `nel flusso SDLC` |
| `terzo tassello del flusso BR` | `terzo tassello del flusso SDLC` |
| `BR lifecycle suite` | `SDLC lifecycle suite` |
| `pipeline BR` | `pipeline SDLC` |
| `ciclo di vita dei Business Requirement` | `ciclo di vita dei Piani` |
| `Aggiornamento piano da nuova documentazione BR` | `Aggiornamento piano da nuova documentazione AFU` |

### MAPPING-PATH (file e placeholder tecnici)

| Pattern old | Pattern new |
|---|---|
| `<br-name>` | `<piano-name>` |
| `feature/<br-name>-<slug>` | `feature/<piano-name>-<slug>` |
| `feature/<br-name>` | `feature/<piano-name>` |

**NOTA**: `.br-local.json` NON è incluso qui — la gestione è speciale e separata (Wave 1 aggiunge fallback, Wave 3 fa la migrazione).

### MAPPING-TRIGGER (frontmatter description di ogni skill)

Multi-trigger: i trigger BR esistenti restano, si aggiungono nuovi trigger AFU/Piano per ogni skill.

Vedere Task 2.1-2.9 per la lista esatta di trigger da aggiungere per ciascuna skill.

### LETTURA COMPATIBILE (blocco da inserire in Wave 1)

Blocco markdown standard da inserire in ogni skill che legge il file config. Variazioni minime saranno chiamate fuori esplicitamente nel task.

```markdown
**Lettura compatibile del profilo**: cerca prima `.sdlc-local.json` nella repo corrente. Se non esiste, fa fallback a `.br-local.json` (profilo legacy). Se entrambi sono assenti, errore "Profilo non configurato — esegui `/sdlc-profile-setup`". Se trovi solo `.br-local.json`, emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.
```

---

## File Structure

### File da modificare

| File | Wave | Cambio principale |
|---|---|---|
| `~/.claude/skills/sdlc-analyzer/SKILL.md` | 1, 2 | Lettura compatibile + 31 BR + 14 br-name + multi-trigger |
| `~/.claude/skills/sdlc-clarify/SKILL.md` | 1, 2 | Lettura compatibile + 4 BR + multi-trigger |
| `~/.claude/skills/sdlc-debug/SKILL.md` | 1, 2 | Lettura compatibile + 18 BR + 14 br-name + multi-trigger |
| `~/.claude/skills/sdlc-estimator/SKILL.md` | 1, 2 | Lettura compatibile + 18 BR + multi-trigger |
| `~/.claude/skills/sdlc-executor/SKILL.md` | 1, 2 | Lettura compatibile + 14 BR + multi-trigger |
| `~/.claude/skills/sdlc-profile-setup/SKILL.md` | 1, 2, 3 | Lettura compatibile + 1 BR + 10 br-name + scrittura nuovo + multi-trigger |
| `~/.claude/skills/sdlc-progress-report/SKILL.md` | 1, 2 | Lettura compatibile + 7 BR + multi-trigger |
| `~/.claude/skills/sdlc-reviewer/SKILL.md` | 1, 2 | Lettura compatibile + 24 BR + 12 br-name + multi-trigger |
| `~/.claude/skills/sdlc-updater/SKILL.md` | 1, 2 | Lettura compatibile + 8 BR + multi-trigger |
| `~/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md` | 4 | 36 BR + 15 br-local + multi-trigger menzione |
| `~/.claude/CLAUDE.md` | 4 | 10 BR + 9 entry skill (trigger multi-versione) |
| `docs/ROADMAP_NEW_SKILLS.md` | 4 | 18 BR + nomi skill `br-*` → `sdlc-*` |
| `~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/sdlc-refactor-complete.md` | post-E2E | Aggiornamento testimonianza |

---

# Wave 1 — Lettura compatibile

**Obiettivo wave**: tutte le 9 skill che leggono `.br-local.json` devono leggere PRIMA `.sdlc-local.json` (con fallback). Zero impatto user-facing, zero modifiche testuali.

**File CWD per le operazioni git**: `C:/Users/davmelis/Documents/MyGitHub/claude-flow`

**File da modificare** (tutti fuori dal CWD, in `C:/Users/davmelis/.claude/skills/`):
- sdlc-analyzer/SKILL.md
- sdlc-clarify/SKILL.md
- sdlc-debug/SKILL.md
- sdlc-estimator/SKILL.md
- sdlc-executor/SKILL.md
- sdlc-profile-setup/SKILL.md (eccezione: questa SCRIVE il file, modifiche solo per la lettura iniziale)
- sdlc-progress-report/SKILL.md
- sdlc-reviewer/SKILL.md
- sdlc-updater/SKILL.md

**Importante**: i file delle skill SDLC vivono fuori dalla repo claude-flow. Il commit conterrà solo i file della repo claude-flow (in questo caso nessuno — quindi NESSUN commit git per Wave 1). Il "commit" semantico di Wave 1 è solo memoriale, salvato come riga nel memory file finale.

> **Eccezione operativa**: dato che le skill non sono tracked da git, il "rollback" della Wave 1 si fa manualmente con `git diff` impossibile. Strategia: PRIMA di modificare ogni file, fare una copia `.bak` (es. `sdlc-analyzer/SKILL.md.bak-wave1`). Dopo lo smoke test, eliminare i `.bak`.

---

### Task 1.1: Setup di sicurezza — copia di backup di tutte le skill

**Files:**
- Create: 9 file `.bak-wave1` (uno per skill) in `~/.claude/skills/sdlc-*/`

- [ ] **Step 1: Copia di backup di tutte le 9 skill**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  cp "/c/Users/davmelis/.claude/skills/$skill/SKILL.md" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md.bak-wave1"
done
ls /c/Users/davmelis/.claude/skills/sdlc-*/SKILL.md.bak-wave1 | wc -l
```

Expected: `9` (uno per skill)

- [ ] **Step 2: Backup anche di SDLC_SKILLS_DOCUMENTATION.md (servirà in Wave 4)**

Run:
```bash
cp /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md.bak-pre-migration
ls -la /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md.bak-pre-migration
```

Expected: file presente

---

### Task 1.2: Sdlc-analyzer — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md`

- [ ] **Step 1: Localizza la sezione che legge `.br-local.json`**

Run:
```bash
grep -n "br-local" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Expected: 14 righe con riferimenti a `br-local`. Identificare quelle che descrivono il **lookup iniziale del profilo** (tipicamente in "Fase 1 — Setup profilo" o sezione equivalente). Distinguere dalle righe che descrivono il valore di un campo o l'esempio di path.

- [ ] **Step 2: Leggi la sezione di lookup completa**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md | head -60
```

Identificare il blocco che istruisce la skill a leggere il file. Tipicamente sarà qualcosa come:
> Leggi `.br-local.json` nella repo corrente per ottenere `profiles_repo` e `profilo`.

- [ ] **Step 3: Modifica la sezione di lookup con Edit per inserire il fallback**

Usa il tool Edit. Pattern generico (adatta al testo esatto trovato nello Step 2):

`old_string`:
```
Leggi `.br-local.json` nella repo corrente
```

`new_string`:
```
Leggi il profilo locale: cerca prima `.sdlc-local.json` nella repo corrente; se non esiste, fa fallback a `.br-local.json` (profilo legacy). Se entrambi sono assenti, errore "Profilo non configurato — esegui `/sdlc-profile-setup`". Se trovi solo `.br-local.json`, emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

Dal file letto (`.sdlc-local.json` o `.br-local.json`)
```

**NOTA**: l'`old_string` deve corrispondere ESATTAMENTE al testo nella skill (compresi accenti e apostrofi italiani — `e'` o `è` a seconda di come è scritto). Se la frase esatta è diversa, ricavare il match minimo univoco usando il contesto dei `-B 2 -A 10` sopra.

- [ ] **Step 4: Verifica che il file abbia ora 2 riferimenti a `.sdlc-local.json` (uno nel nuovo testo + uno nel warning)**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Expected: `2` (o più, se ci sono molteplici punti di lettura nella skill — in tal caso ripetere Step 3 per ognuno)

- [ ] **Step 5: Verifica che `.br-local.json` sia ancora menzionato (per il fallback)**

Run:
```bash
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Expected: `>= 1` (non deve scendere a 0, altrimenti il fallback non c'è)

---

### Task 1.3: Sdlc-clarify — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md`

- [ ] **Step 1: Localizza la sezione che legge `.br-local.json`**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md | head -60
```

- [ ] **Step 2: Applica la stessa modifica del Task 1.2 Step 3 con Edit**

Stesso pattern `old_string`/`new_string` del Task 1.2 Step 3. Se l'esatto wording della frase di lookup è diverso, usare il testo esistente come `old_string` e premettere il nuovo blocco (mantenendo la frase originale come riga finale del nuovo blocco — vedi pattern Task 1.2).

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.4: Sdlc-debug — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md`

- [ ] **Step 1: Localizza la sezione che legge `.br-local.json`**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (stesso pattern del Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.5: Sdlc-estimator — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (pattern Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.6: Sdlc-executor — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (pattern Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.7: Sdlc-profile-setup — aggiungi lettura compatibile (parziale)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md`

**Eccezione**: questa skill SCRIVE il file. In Wave 1 modifichiamo SOLO le sezioni che LEGGONO per detection (per capire se il profilo esiste già). La sezione di SCRITTURA viene modificata in Wave 3.

- [ ] **Step 1: Localizza le sezioni**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md | head -100
```

Identificare:
- Sezioni di LETTURA / DETECTION (es. "Se `.br-local.json` esiste già") → modificare in Wave 1
- Sezioni di SCRITTURA (es. "Crea il file `.br-local.json`") → NON toccare ora, vanno in Wave 3
- La riga `description:` nel frontmatter — NON toccare ora, va in Wave 2

- [ ] **Step 2: Aggiungi lettura compatibile solo per la sezione di detection iniziale**

Cerca la sezione tipica:
```
**Se `.br-local.json` esiste gia'**: leggi il contenuto, preserva...
```

Modificala con Edit:

`old_string`:
```
**Se `.br-local.json` esiste gia'**
```

`new_string`:
```
**Se `.sdlc-local.json` esiste già** (oppure, in fallback compatibile, **se esiste `.br-local.json`** legacy)
```

E lascia INVARIATO il resto del paragrafo (`leggi il contenuto, preserva tutti i campi esistenti...`) perché la logica è la stessa per entrambi i file.

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 1
- `.br-local.json` ≥ 9 (la maggior parte ancora invariata, sarà rinominata in Wave 3)

---

### Task 1.8: Sdlc-progress-report — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (pattern Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.9: Sdlc-reviewer — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (pattern Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.10: Sdlc-updater — aggiungi lettura compatibile

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n -B 2 -A 10 "br-local" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md | head -80
```

- [ ] **Step 2: Applica la modifica con Edit (pattern Task 1.2 Step 3)**

- [ ] **Step 3: Verifica**

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
grep -c "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
```

Expected:
- `.sdlc-local.json` ≥ 2
- `.br-local.json` ≥ 1

---

### Task 1.11: Smoke test Wave 1

**Files:**
- Read: tutti i 9 SKILL.md modificati

- [ ] **Step 1: Verifica globale del numero di skill che hanno il nuovo lookup**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\.sdlc-local\.json" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count occorrenze .sdlc-local.json"
done
```

Expected: tutte le 9 skill ≥ 1 occorrenza `.sdlc-local.json`

- [ ] **Step 2: Verifica che il fallback `.br-local.json` sia ancora presente in tutte**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\.br-local\.json" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count occorrenze .br-local.json"
done
```

Expected: tutte ≥ 1 (fallback compatibile presente)

- [ ] **Step 3: Verifica che il warning soft sia inserito in almeno 8 skill (sdlc-profile-setup escluso perché non lo ha)**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "profilo legacy" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count warning"
done
```

Expected: tutte le 8 skill ≥ 1 warning

- [ ] **Step 4: Test manuale via lettura della skill sdlc-analyzer**

Read del file modificato:
```
~/.claude/skills/sdlc-analyzer/SKILL.md
```

Verificare visivamente che la sezione di lookup sia:
- Coerente nel italiano (no doppi articoli, no accenti rotti)
- Inserita nel posto corretto (vicino alla detection iniziale del profilo)
- Il warning soft è ben formattato come blockquote

- [ ] **Step 5: Marca Wave 1 come completata nel memory log (file temporaneo)**

Create file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave1-done.tmp
```

con contenuto:
```
Wave 1 completata 2026-05-21:
- 9 skill con lettura compatibile .sdlc-local.json → fallback .br-local.json
- Warning soft inserito in 8 skill (escluso sdlc-profile-setup)
- Backup .bak-wave1 presenti per rollback
```

- [ ] **Step 6: (Nessun commit git per Wave 1)**

Le skill SDLC vivono fuori dalla repo claude-flow, quindi `git status` nella repo non mostra modifiche. Wave 1 è completata. Se serve rollback, ripristinare i file da `.bak-wave1`.

---

# Wave 2 — Sostituzione testuale BR → AFU/Piano nelle 9 skill

**Obiettivo wave**: applicare MAPPING-AFU, MAPPING-PIANO, MAPPING-SDLC, MAPPING-PATH e MAPPING-TRIGGER alle 9 SKILL.md. Una task per skill, dalla più piccola alla più grande.

**Strategia per ogni task**:
1. Leggere il file completo per identificare le occorrenze
2. Applicare le sostituzioni dei mapping (uno Edit alla volta)
3. Verificare grep `\bBR\b` = 0 (escluso trigger phrases nel frontmatter)
4. Verificare grep `\bbr-name\b` = 0

**Casi grammaticali**: dopo le sostituzioni meccaniche, controllare a vista che:
- `il BR` → `l'AFU` (elisione corretta, non `il AFU`)
- `del BR` → `dell'AFU` (non `del AFU`)
- `BR attivi` → `Piani attivi` (plurale concordato)
- `il BR è ambiguo` → `l'AFU è ambigua` (genere femminile per AFU)

---

### Task 2.1: Sdlc-profile-setup — sostituzione testuale (1 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md`

- [ ] **Step 1: Localizza l'unica occorrenza BR**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected: 1 riga, nella `description:` del frontmatter:
```
3:description: Crea un nuovo profilo progetto in deloitte-profiles con auto-detect del codebase, domande guidate su dominio e design system, e configurazione automatica di .br-local.json. Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill BR.
```

- [ ] **Step 2: Applica il multi-trigger nella description**

Usa Edit:

`old_string`:
```
configurazione automatica di .br-local.json. Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill BR.
```

`new_string`:
```
configurazione automatica di .sdlc-local.json (con fallback compatibile a .br-local.json per profili legacy). Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill SDLC.
```

- [ ] **Step 3: Verifica grep BR = 0**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected: `0`

- [ ] **Step 4: Verifica grep br-name = 0**

Run:
```bash
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected: `0` (questa skill non usa `<br-name>`)

---

### Task 2.2: Sdlc-clarify — sostituzione testuale (4 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md`

- [ ] **Step 1: Localizza tutte le occorrenze**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
```

Expected (sulla base dell'analisi pre-piano):
```
8:Questa skill si posiziona tra `sdlc-reviewer` e `sdlc-analyzer` nel flusso BR. Riceve le risposte del team funzionale...
10:Il flusso BR completo:
146:> Ho trovato il review del BR:
```

(potrebbe esserci anche una nel description del frontmatter — verificare)

- [ ] **Step 2: Applica sostituzioni Edit**

Sostituzione 1 — MAPPING-SDLC sulla riga 8:

`old_string`:
```
nel flusso BR. Riceve
```

`new_string`:
```
nel flusso SDLC. Riceve
```

Sostituzione 2 — MAPPING-SDLC sulla riga 10:

`old_string`:
```
Il flusso BR completo:
```

`new_string`:
```
Il flusso SDLC completo:
```

Sostituzione 3 — MAPPING-AFU sulla riga 146 (è il review del documento input):

`old_string`:
```
> Ho trovato il review del BR:
```

`new_string`:
```
> Ho trovato il review dell'AFU:
```

- [ ] **Step 3: Aggiorna il description del frontmatter con multi-trigger**

Read del frontmatter:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
```

Identificare la riga `description:`. La skill sdlc-clarify ha trigger naturali che non parlano direttamente di BR ("chiarimenti ricevuti", "risposte ricevute", "il funzionale ha risposto"). Il multi-trigger qui consiste nell'aggiungere riferimenti SDLC/AFU all'interno della descrizione, NON nei trigger di attivazione (che restano focalizzati su "chiarimenti"/"risposte").

Modifica con Edit la `description:` per:
- Sostituire `flusso BR` con `flusso SDLC` (se presente)
- Sostituire `del BR` con `dell'AFU` o `del Piano` a seconda del contesto specifico nella description

Esempio: se la description contiene `"risposte al review BR"`, sostituire con `"risposte al review AFU"`.

Verificare con:
```bash
grep -n "BR" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md | head -5
```

- [ ] **Step 4: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-clarify/SKILL.md
```

Expected:
- `BR` = 0 (oppure ≤ N solo se trigger phrases multi-trigger mantengono "BR" come alias esplicito)
- `br-name` = 0

---

### Task 2.3: Sdlc-progress-report — sostituzione testuale (7 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md
```

Expected (basato sull'analisi pre-piano, righe approssimative):
- Riga 114: `Cerca cartelle BR nella struttura plans/ centralizzata in deloitte-profiles, in ordine di priorita':`
- Riga 126: `**Se trovi cartelle BR**, proponile:`
- Riga 139: `Cerca nella stessa cartella del BR se esiste gia' un file Excel:`
- Riga 168: `Leggi il PROGRESS.md dalla cartella del BR in $BASE_PATH/<stato>/<data>_<nome>/PROGRESS.md...`
- Riga 262: `Progetto: [nome BR]`
- Riga 299: `Salva nella stessa cartella del BR all'interno della repo centralizzata:`

- [ ] **Step 2: Applica sostituzioni MAPPING-PIANO**

Edit 1:

`old_string`:
```
Cerca cartelle BR nella struttura
```

`new_string`:
```
Cerca cartelle dei Piani nella struttura
```

Edit 2:

`old_string`:
```
**Se trovi cartelle BR**, proponile:
```

`new_string`:
```
**Se trovi cartelle dei Piani**, proponile:
```

Edit 3:

`old_string`:
```
Cerca nella stessa cartella del BR se esiste gia' un file Excel:
```

`new_string`:
```
Cerca nella stessa cartella del Piano se esiste gia' un file Excel:
```

Edit 4:

`old_string`:
```
Leggi il PROGRESS.md dalla cartella del BR in
```

`new_string`:
```
Leggi il PROGRESS.md dalla cartella del Piano in
```

Edit 5:

`old_string`:
```
Progetto: [nome BR]
```

`new_string`:
```
Progetto: [nome Piano]
```

Edit 6:

`old_string`:
```
Salva nella stessa cartella del BR all'interno della repo centralizzata:
```

`new_string`:
```
Salva nella stessa cartella del Piano all'interno della repo centralizzata:
```

- [ ] **Step 3: Aggiorna description del frontmatter (multi-trigger se presente)**

Run:
```bash
sed -n '1,10p' /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md
```

Se la description contiene riferimenti a "BR" o "piano BR", aggiornarli (es. `piano BR` → `piano del lavoro`). I trigger phrases di sdlc-progress-report sono già neutri ("genera report excel", "stato avanzamento") — non serve aggiungere alias.

- [ ] **Step 4: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-progress-report/SKILL.md
```

Expected: `0`

---

### Task 2.4: Sdlc-updater — sostituzione testuale (8 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
```

Expected (sulla base dell'analisi pre-piano):
- Riga 8: `Questa skill è il terzo tassello del flusso BR, dopo sdlc-analyzer (analisi iniziale) e sdlc-executor (esecuzione task). Si attiva quando la documentazione del BR viene aggiornata...`
- Riga 146: `Cerca automaticamente cartelle BR nella struttura plans/:`
- Riga 153: `**Se trovi cartelle BR**, elencale con il loro contenuto:`
- Riga 155: `> Ho trovato questa cartella BR:`
- Riga 220: `Salva nella cartella requirements/ dentro la cartella del BR (es. $BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/requirements/), sovrascrivendo i file precedenti dove applicabile.`
- Riga 312: `...nome branch seguendo il pattern feature/<br-name>-<slug-attivita> (dove <br-name> e' il nome del BR e <slug>...`
- Riga 353: `[data] — Aggiornamento piano da nuova documentazione BR: N task aggiunte...`

- [ ] **Step 2: Applica sostituzioni**

Edit 1 (MAPPING-SDLC + MAPPING-AFU sulla riga 8):

`old_string`:
```
Questa skill è il terzo tassello del flusso BR, dopo `sdlc-analyzer` (analisi iniziale) e `sdlc-executor` (esecuzione task). Si attiva quando la documentazione del BR viene aggiornata
```

`new_string`:
```
Questa skill è il terzo tassello del flusso SDLC, dopo `sdlc-analyzer` (analisi iniziale) e `sdlc-executor` (esecuzione task). Si attiva quando la documentazione dell'AFU viene aggiornata
```

Edit 2 (MAPPING-PIANO):

`old_string`:
```
Cerca automaticamente cartelle BR nella struttura
```

`new_string`:
```
Cerca automaticamente cartelle dei Piani nella struttura
```

Edit 3 (MAPPING-PIANO):

`old_string`:
```
**Se trovi cartelle BR**, elencale con il loro contenuto:
```

`new_string`:
```
**Se trovi cartelle dei Piani**, elencale con il loro contenuto:
```

Edit 4 (MAPPING-PIANO):

`old_string`:
```
> Ho trovato questa cartella BR:
```

`new_string`:
```
> Ho trovato questa cartella del Piano:
```

Edit 5 (MAPPING-PIANO):

`old_string`:
```
dentro la cartella del BR (es.
```

`new_string`:
```
dentro la cartella del Piano (es.
```

Edit 6 (MAPPING-PATH + MAPPING-PIANO sulla riga 312):

`old_string`:
```
feature/<br-name>-<slug-attivita> (dove `<br-name>` e' il nome del BR
```

`new_string`:
```
feature/<piano-name>-<slug-attivita> (dove `<piano-name>` e' il nome del Piano
```

Edit 7 (MAPPING-AFU sulla riga 353):

`old_string`:
```
Aggiornamento piano da nuova documentazione BR:
```

`new_string`:
```
Aggiornamento piano da nuova documentazione AFU:
```

- [ ] **Step 3: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
```

Se la description contiene trigger come `"il br è stato aggiornato"`, `"nuova versione del br"`, aggiungere alias accanto:
- `"il br è stato aggiornato"` → `"il BR/AFU è stato aggiornato", "l'AFU è stata aggiornata"`
- `"nuova versione del br"` → `"nuova versione del BR/AFU"`

Esempio Edit della description:

`old_string`:
```
Trigger: "il br è stato aggiornato"
```

`new_string`:
```
Trigger: "il br è stato aggiornato", "l'AFU è stata aggiornata", "nuova versione AFU", "aggiorna il Piano"
```

(adatta al wording esatto presente nella description)

- [ ] **Step 4: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-updater/SKILL.md
```

Expected:
- `BR` ≤ N (solo se trigger phrases multi-trigger lo mantengono come alias)
- `br-name` = 0

---

### Task 2.5: Sdlc-executor — sostituzione testuale (14 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
```

Expected (sulla base dell'analisi pre-piano):
- Riga 8: `Questa skill è il complemento operativo di sdlc-analyzer. Mentre sdlc-analyzer analizza un BR e genera PLAN + TASKS, questa skill permette a ogni sviluppatore (assistito da un agente Claude Code) di eseguire le proprie task assegnate.`
- Riga 118: `Prima di chiedere, sincronizza la repo profili e verifica se esiste la struttura plans/ nel profilo. Cerca cartelle BR nelle tre aree:`
- Riga 125: `**Se trovi cartelle BR**, elencale e proponi:`
- Riga 127: `> Ho trovato queste cartelle BR:`
- Riga 147: `Quando lo sviluppatore conferma e la lavorazione sta per iniziare, sposta l'intera cartella del BR da $BASE_PATH/todo/ a $BASE_PATH/in-progress/ (se non e' gia' li'):`
- Riga 156: `Il file di progresso viene creato (o cercato) dentro la cartella del BR in $BASE_PATH/in-progress/.`
- Riga 174: `> - **BR**: \`<nome file originale>\``
- Riga 210: `Crea il file PROGRESS.md nella stessa cartella del BR (es. $BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.md), con questa struttura:`
- Riga 213: `# Progresso Implementazione [Nome BR]`
- Riga 296: `Leggi il PROGRESS.md dalla cartella del BR in $BASE_PATH/in-progress/<data>_<nome>/PROGRESS.md.`
- Riga 369: `3. **Riferimenti** — estratti rilevanti dal gap report (cosa richiede il BR, cosa esiste, cosa manca)`
- Riga 600: `> Tutte le task del piano sono completate **e** tutti i bug (tecnici + funzionali) sono chiusi. Cartella del BR spostata in $BASE_PATH/done/.`
- Riga 620: `Se durante la lavorazione emerge un blocco (dipendenza non prevista, ambiguità nel BR, problema tecnico):`

- [ ] **Step 2: Applica sostituzioni**

Edit 1 (MAPPING-AFU sulla riga 8 — "analizza un BR" è documento input):

`old_string`:
```
Mentre `sdlc-analyzer` analizza un BR e genera PLAN + TASKS
```

`new_string`:
```
Mentre `sdlc-analyzer` analizza un'AFU e genera PLAN + TASKS
```

Edit 2 (MAPPING-PIANO sulla riga 118):

`old_string`:
```
Cerca cartelle BR nelle tre aree:
```

`new_string`:
```
Cerca cartelle dei Piani nelle tre aree:
```

Edit 3 (MAPPING-PIANO sulla riga 125):

`old_string`:
```
**Se trovi cartelle BR**, elencale e proponi:
```

`new_string`:
```
**Se trovi cartelle dei Piani**, elencale e proponi:
```

Edit 4 (MAPPING-PIANO sulla riga 127):

`old_string`:
```
> Ho trovato queste cartelle BR:
```

`new_string`:
```
> Ho trovato queste cartelle dei Piani:
```

Edit 5 (MAPPING-PIANO sulla riga 147):

`old_string`:
```
sposta l'intera cartella del BR da `$BASE_PATH/todo/` a `$BASE_PATH/in-progress/`
```

`new_string`:
```
sposta l'intera cartella del Piano da `$BASE_PATH/todo/` a `$BASE_PATH/in-progress/`
```

Edit 6 (MAPPING-PIANO sulla riga 156):

`old_string`:
```
Il file di progresso viene creato (o cercato) dentro la cartella del BR in `$BASE_PATH/in-progress/`.
```

`new_string`:
```
Il file di progresso viene creato (o cercato) dentro la cartella del Piano in `$BASE_PATH/in-progress/`.
```

Edit 7 (MAPPING-AFU sulla riga 174 — "BR" come label del documento input):

`old_string`:
```
> - **BR**: `<nome file originale>`
```

`new_string`:
```
> - **AFU**: `<nome file originale>`
```

Edit 8 (MAPPING-PIANO sulla riga 210):

`old_string`:
```
Crea il file `PROGRESS.md` nella stessa cartella del BR (es. `$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.md`)
```

`new_string`:
```
Crea il file `PROGRESS.md` nella stessa cartella del Piano (es. `$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.md`)
```

Edit 9 (MAPPING-PIANO sulla riga 213 — header file output):

`old_string`:
```
# Progresso Implementazione [Nome BR]
```

`new_string`:
```
# Progresso Implementazione [Nome Piano]
```

Edit 10 (MAPPING-PIANO sulla riga 296):

`old_string`:
```
Leggi il PROGRESS.md dalla cartella del BR in `$BASE_PATH/in-progress/<data>_<nome>/PROGRESS.md`.
```

`new_string`:
```
Leggi il PROGRESS.md dalla cartella del Piano in `$BASE_PATH/in-progress/<data>_<nome>/PROGRESS.md`.
```

Edit 11 (MAPPING-AFU sulla riga 369 — "richiede il BR" è il documento input):

`old_string`:
```
estratti rilevanti dal gap report (cosa richiede il BR, cosa esiste, cosa manca)
```

`new_string`:
```
estratti rilevanti dal gap report (cosa richiede l'AFU, cosa esiste, cosa manca)
```

Edit 12 (MAPPING-PIANO sulla riga 600):

`old_string`:
```
Cartella del BR spostata in `$BASE_PATH/done/`.
```

`new_string`:
```
Cartella del Piano spostata in `$BASE_PATH/done/`.
```

Edit 13 (MAPPING-AFU sulla riga 620 — "ambiguità nel BR" è il documento input):

`old_string`:
```
ambiguità nel BR, problema tecnico
```

`new_string`:
```
ambiguità nell'AFU, problema tecnico
```

- [ ] **Step 3: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
```

Identificare i trigger esistenti e aggiungere `"lavora il Piano"` come alias. Es:

`old_string` (nella description):
```
Trigger: "lavora il task", "inizia a lavorare", "esegui il piano"
```

`new_string`:
```
Trigger: "lavora il task", "lavora il Piano", "inizia a lavorare", "esegui il piano"
```

- [ ] **Step 4: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-executor/SKILL.md
```

Expected:
- `BR` ≤ N (solo trigger multi-trigger)
- `br-name` = 0

---

### Task 2.6: Sdlc-debug — sostituzione testuale (18 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
```

Expected (basato sull'analisi):
- Riga 17: `Il BR passa a done solo quando tutte le task sono completate E tutti i bug sono chiusi.`
- Riga 23: `Tutte le operazioni su file BR avvengono nella repo deloitte-profiles, non nella repo del codice.`
- Riga 35: `Il **base path** per gli artefatti BR e': <profiles_repo>/<profilo>/plans/`
- Riga 124: `**Import mode**: non esiste BUG_REPORT.md nella cartella del BR, oppure l'utente dice "ci sono dei bug", "segnalazioni test", "defect ricevuti"`
- Riga 163: `### Domanda 1 — BR di riferimento`
- Riga 165: `Cerca i BR attivi:`
- Riga 252: `**Screenshot:** se il file ha un foglio "Screen" con immagini referenziate dalla colonna Screen, estrai le immagini e salvale nella cartella del BR:`
- Riga 260: `1. **Progetto Jira** — o deducilo dal BR`
- Riga 306: `> - BR: [nome]`
- Riga 317: `Crea BUG_REPORT.md nella cartella del BR (es. <profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/BUG_REPORT.md). Usa il formato definito nella sezione "Struttura BUG_REPORT.md".`
- Riga 635: `La skill puo' essere invocata piu' volte sullo stesso BR. A ogni invocazione:`
- Riga 669: `Se il BR e' in stato execute e tutte le task E tutti i bug sono completati, il BR puo' passare a done.`
- Riga 678: `# Bug Report — <nome BR>`
- Riga 769: `This is one of the skills in the BR (Business Requirement) lifecycle suite. The other skills are:`
- Riga 772: `- sdlc-analyzer: gap analysis between BR docs and codebase`
- Riga 774: `- sdlc-updater: updates plan when BR documentation changes`
- Riga 779: `All BR artifacts (TASKS.md, PLAN.md, PROGRESS.md, BUG_REPORT.md, screenshots) live centrally in <profiles_repo>/<profilo>/plans/, not in the code repository.`

- [ ] **Step 2: Applica sostituzioni**

Edit 1 (MAPPING-PIANO riga 17):

`old_string`:
```
Il BR passa a `done` solo quando
```

`new_string`:
```
Il Piano passa a `done` solo quando
```

Edit 2 (MAPPING-PIANO riga 23):

`old_string`:
```
Tutte le operazioni su file BR avvengono nella repo `deloitte-profiles`
```

`new_string`:
```
Tutte le operazioni sui file del Piano avvengono nella repo `deloitte-profiles`
```

Edit 3 (MAPPING-PIANO riga 35):

`old_string`:
```
Il **base path** per gli artefatti BR e':
```

`new_string`:
```
Il **base path** per gli artefatti del Piano e':
```

Edit 4 (MAPPING-PIANO riga 124):

`old_string`:
```
non esiste `BUG_REPORT.md` nella cartella del BR
```

`new_string`:
```
non esiste `BUG_REPORT.md` nella cartella del Piano
```

Edit 5 (MAPPING-PIANO riga 163):

`old_string`:
```
### Domanda 1 — BR di riferimento
```

`new_string`:
```
### Domanda 1 — Piano di riferimento
```

Edit 6 (MAPPING-PIANO riga 165):

`old_string`:
```
Cerca i BR attivi:
```

`new_string`:
```
Cerca i Piani attivi:
```

Edit 7 (MAPPING-PIANO riga 252):

`old_string`:
```
salvale nella cartella del BR:
```

`new_string`:
```
salvale nella cartella del Piano:
```

Edit 8 (MAPPING-AFU riga 260 — "deduci dal documento input"):

`old_string`:
```
**Progetto Jira** — o deducilo dal BR
```

`new_string`:
```
**Progetto Jira** — o deducilo dall'AFU
```

Edit 9 (MAPPING-PIANO riga 306):

`old_string`:
```
> - BR: [nome]
```

`new_string`:
```
> - Piano: [nome]
```

Edit 10 (MAPPING-PIANO riga 317):

`old_string`:
```
Crea `BUG_REPORT.md` nella cartella del BR (es.
```

`new_string`:
```
Crea `BUG_REPORT.md` nella cartella del Piano (es.
```

Edit 11 (MAPPING-PIANO riga 635):

`old_string`:
```
La skill puo' essere invocata piu' volte sullo stesso BR.
```

`new_string`:
```
La skill puo' essere invocata piu' volte sullo stesso Piano.
```

Edit 12 (MAPPING-PIANO riga 669):

`old_string`:
```
Se il BR e' in stato `execute` e tutte le task E tutti i bug sono completati, il BR puo' passare a `done`.
```

`new_string`:
```
Se il Piano e' in stato `execute` e tutte le task E tutti i bug sono completati, il Piano puo' passare a `done`.
```

Edit 13 (MAPPING-PIANO riga 678 — header file output):

`old_string`:
```
# Bug Report — <nome BR>
```

`new_string`:
```
# Bug Report — <nome Piano>
```

Edit 14 (MAPPING-SDLC + MAPPING-AFU riga 769 — sezione inglese):

`old_string`:
```
This is one of the skills in the BR (Business Requirement) lifecycle suite. The other skills are:
```

`new_string`:
```
This is one of the skills in the SDLC lifecycle suite (BR / AFU / Piano workflow). The other skills are:
```

Edit 15 (MAPPING-AFU riga 772):

`old_string`:
```
- sdlc-analyzer: gap analysis between BR docs and codebase
```

`new_string`:
```
- sdlc-analyzer: gap analysis between AFU docs and codebase
```

Edit 16 (MAPPING-AFU riga 774):

`old_string`:
```
- sdlc-updater: updates plan when BR documentation changes
```

`new_string`:
```
- sdlc-updater: updates plan when AFU documentation changes
```

Edit 17 (MAPPING-PIANO riga 779):

`old_string`:
```
All BR artifacts (TASKS.md, PLAN.md, PROGRESS.md, BUG_REPORT.md, screenshots) live centrally in
```

`new_string`:
```
All Plan artifacts (TASKS.md, PLAN.md, PROGRESS.md, BUG_REPORT.md, screenshots) live centrally in
```

- [ ] **Step 3: Rename `<br-name>` → `<piano-name>` se presenti**

Run:
```bash
grep -n "<br-name>" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
```

Per ogni occorrenza, applica Edit con `replace_all: true`:

Pattern Edit:
- `old_string`: `<br-name>`
- `new_string`: `<piano-name>`
- `replace_all`: true

- [ ] **Step 4: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
```

Aggiungere alias accanto ai trigger esistenti:
- `"debug br"` → `"debug br", "debug Piano", "bug su Piano"`

Esempio Edit della description:

`old_string`:
```
Trigger: "ci sono dei bug", "lavora il bug", "debug br"
```

`new_string`:
```
Trigger: "ci sono dei bug", "lavora il bug", "debug br", "debug Piano", "bug su Piano"
```

- [ ] **Step 5: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-debug/SKILL.md
```

Expected:
- `BR` ≤ N (solo trigger multi-trigger)
- `br-name` = 0

---

### Task 2.7: Sdlc-estimator — sostituzione testuale (18 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
```

Expected (basato sull'analisi):
- Riga 8: `Questa skill stima quanti sviluppatori servono per completare un BR entro una deadline...`
- Riga 11: `- **Rough** (pre-analisi) — dalla documentazione BR, stima approssimativa (±30-40%)`
- Riga 121: `- **Se non esiste un TASKS ma ci sono documenti BR** → modalita' **rough**`
- Riga 125: `> Ho rilevato che il BR **<nome>** ha un TASKS.`
- Riga 130: `> Il BR **<nome>** non ha ancora un TASKS. Uso la modalita' **rough** dalla documentazione (precisione ±30-40%).`
- Riga 138: `### Domanda 1 — BR di riferimento`
- Riga 140: `Cerca i BR attivi:`
- Riga 147: `Se ne trovi uno, proponilo. Se piu' di uno, chiedi quale. Se nessuno, avvisa che serve almeno la documentazione BR.`
- Riga 151: `> Entro quando deve essere completato il BR?`
- Riga 169: `> - **Disponibilita'**: percentuale di tempo dedicato a questo BR (default 100%)`
- Riga 191: `- **Analista BR** (sdlc-estimation-analyst): leggi le sue istruzioni da ~/.claude/agents/sdlc-estimation-analyst.md. Passagli la documentazione BR e il profilo progetto (se disponibile da .br-local.json → profiles_repo/profilo).`
- Riga 204: `> **Calibrazione storica:** Xx (da K BR precedenti)`
- Riga 292: `Scrivi il file nella cartella del BR:`
- Riga 293: `$BASE_PATH/todo/<data>_<nome>/ESTIMATE.md (o in-progress/ se il BR è già in lavorazione)`
- Riga 298: `# Stima BR — <nome>`
- Riga 350: `Fattore: Xx (da N BR precedenti)`
- Riga 356: `[tabella BR passati dallo storico]`

- [ ] **Step 2: Applica sostituzioni**

Edit 1 (MAPPING-PIANO riga 8):

`old_string`:
```
Questa skill stima quanti sviluppatori servono per completare un BR entro una deadline
```

`new_string`:
```
Questa skill stima quanti sviluppatori servono per completare un Piano entro una deadline
```

Edit 2 (MAPPING-AFU riga 11 — "documentazione BR" è il documento input):

`old_string`:
```
- **Rough** (pre-analisi) — dalla documentazione BR, stima approssimativa
```

`new_string`:
```
- **Rough** (pre-analisi) — dalla documentazione AFU, stima approssimativa
```

Edit 3 (MAPPING-AFU riga 121):

`old_string`:
```
**Se non esiste un TASKS ma ci sono documenti BR** → modalita' **rough**
```

`new_string`:
```
**Se non esiste un TASKS ma ci sono documenti AFU** → modalita' **rough**
```

Edit 4 (MAPPING-PIANO riga 125):

`old_string`:
```
> Ho rilevato che il BR **<nome>** ha un TASKS.
```

`new_string`:
```
> Ho rilevato che il Piano **<nome>** ha un TASKS.
```

Edit 5 (MAPPING-PIANO riga 130):

`old_string`:
```
> Il BR **<nome>** non ha ancora un TASKS. Uso la modalita' **rough** dalla documentazione (precisione ±30-40%).
```

`new_string`:
```
> Il Piano **<nome>** non ha ancora un TASKS. Uso la modalita' **rough** dalla documentazione (precisione ±30-40%).
```

Edit 6 (MAPPING-PIANO riga 138):

`old_string`:
```
### Domanda 1 — BR di riferimento
```

`new_string`:
```
### Domanda 1 — Piano di riferimento
```

Edit 7 (MAPPING-PIANO riga 140):

`old_string`:
```
Cerca i BR attivi:
```

`new_string`:
```
Cerca i Piani attivi:
```

Edit 8 (MAPPING-AFU riga 147):

`old_string`:
```
avvisa che serve almeno la documentazione BR.
```

`new_string`:
```
avvisa che serve almeno la documentazione AFU.
```

Edit 9 (MAPPING-PIANO riga 151):

`old_string`:
```
> Entro quando deve essere completato il BR?
```

`new_string`:
```
> Entro quando deve essere completato il Piano?
```

Edit 10 (MAPPING-PIANO riga 169):

`old_string`:
```
**Disponibilita'**: percentuale di tempo dedicato a questo BR (default 100%)
```

`new_string`:
```
**Disponibilita'**: percentuale di tempo dedicato a questo Piano (default 100%)
```

Edit 11 (MAPPING-AFU riga 191):

`old_string`:
```
**Analista BR** (`sdlc-estimation-analyst`): leggi le sue istruzioni da `~/.claude/agents/sdlc-estimation-analyst.md`. Passagli la documentazione BR e il profilo progetto
```

`new_string`:
```
**Analista AFU** (`sdlc-estimation-analyst`): leggi le sue istruzioni da `~/.claude/agents/sdlc-estimation-analyst.md`. Passagli la documentazione AFU e il profilo progetto
```

Edit 12 (MAPPING-PIANO riga 204):

`old_string`:
```
> **Calibrazione storica:** Xx (da K BR precedenti)
```

`new_string`:
```
> **Calibrazione storica:** Xx (da K Piani precedenti)
```

Edit 13 (MAPPING-PIANO riga 292):

`old_string`:
```
Scrivi il file nella cartella del BR:
```

`new_string`:
```
Scrivi il file nella cartella del Piano:
```

Edit 14 (MAPPING-PIANO riga 293):

`old_string`:
```
`$BASE_PATH/todo/<data>_<nome>/ESTIMATE.md` (o `in-progress/` se il BR è già in lavorazione)
```

`new_string`:
```
`$BASE_PATH/todo/<data>_<nome>/ESTIMATE.md` (o `in-progress/` se il Piano è già in lavorazione)
```

Edit 15 (MAPPING-PIANO riga 298 — header file output):

`old_string`:
```
# Stima BR — <nome>
```

`new_string`:
```
# Stima Piano — <nome>
```

Edit 16 (MAPPING-PIANO riga 350):

`old_string`:
```
Fattore: Xx (da N BR precedenti)
```

`new_string`:
```
Fattore: Xx (da N Piani precedenti)
```

Edit 17 (MAPPING-PIANO riga 356):

`old_string`:
```
[tabella BR passati dallo storico]
```

`new_string`:
```
[tabella Piani passati dallo storico]
```

- [ ] **Step 3: Rename `<br-name>` → `<piano-name>` se presenti**

Run:
```bash
grep -n "<br-name>" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
```

Se trovi occorrenze, usa Edit con `replace_all: true`.

- [ ] **Step 4: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
```

Aggiungere alias:
- `"stima il br"` → `"stima il br", "stima il Piano", "stima l'AFU"`

- [ ] **Step 5: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-estimator/SKILL.md
```

Expected:
- `BR` ≤ N (solo trigger multi-trigger)
- `br-name` = 0

---

### Task 2.8: Sdlc-reviewer — sostituzione testuale (24 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md`

- [ ] **Step 1: Localizza**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
```

Expected (basato sull'analisi, righe approssimative):
- Riga 8: `Questa skill si posiziona *prima* di sdlc-analyzer nel flusso BR. Analizza la documentazione funzionale...`
- Riga 10: `Il flusso BR completo:`
- Riga 179: `### Domanda 1 — Nome del BR`
- Riga 181: `> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.`
- Riga 191: `> Dove trovo la documentazione del BR? Dammi i path per:`
- Riga 192: `> - **BR** (il documento principale dei requisiti)`
- Riga 202: `> Quali sono le repository/codebase coinvolte in questo BR?`
- Riga 209: `> Se una repo non e' coinvolta nel BR, non includerla.`
- Riga 218: `> - Nome BR: [nome] → cartella $BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`
- Riga 285: `**Regole di business** — le regole di business sono esplicitate? Gli stati, le transizioni, le condizioni, i vincoli sono definiti? O il BR descrive la UI senza definire la logica dietro?`
- Riga 291: `**BR vs mockup** — ogni elemento visuale nel mockup ha un corrispettivo funzionale nel BR? Il BR descrive funzionalita' che il mockup non mostra?`
- Riga 292: `**BR vs specifiche tecniche** — se ci sono specifiche tecniche, sono coerenti con i requisiti funzionali?`
- Riga 293: `**Terminologia** — lo stesso concetto e' chiamato con lo stesso nome in tutti i documenti? Se il BR dice "pratica" e il mockup dice "richiesta", e' un problema.`
- Riga 299: `**Entita' e modelli dati** — il BR presuppone strutture dati che nel codice esistono ma sono diverse?`
- Riga 300: `**Enum e costanti** — il BR definisce stati o valori che nel codice esistono gia' come enum con valori/nomi diversi?`
- Riga 301: `**API/endpoint** — il BR descrive operazioni che nel codice corrispondono ad API con naming o struttura diversa?`
- Riga 302: `**Flussi e stati** — il BR descrive transizioni di stato che nel codice funzionano diversamente?`
- Riga 304: `Lo scopo NON e' fare la gap analysis (quello lo fa sdlc-analyzer) ma trovare problemi di *documentazione* visibili solo confrontando col codice: il BR presuppone strutture che nel codice esistono ma sono diverse. Questi disallineamenti vanno segnalati al team funzionale perche' possono essere errori nel BR o evoluzioni non documentate.`
- Riga 322: `**Disallineamento col codice** | Il BR presuppone strutture/terminologie diverse da quelle nel codice`
- Riga 338: `# Review Documentazione BR [nome/versione]`
- Riga 414: `| # | Concetto BR | Nel codice | File/Classe | Nota |`
- Riga 416: `| D-001 | "stato pratica: Aperta, Chiusa" | enum PracticeStatus: OPEN, CLOSED, SUSPENDED | src/.../PracticeStatus.java | Il BR non menziona SUSPENDED |`
- Riga 438: `Entrambi i file (MD e DOCX) vengono salvati nella cartella del BR. Il DOCX contiene i placeholder...`

- [ ] **Step 2: Applica sostituzioni**

Edit 1 (MAPPING-SDLC riga 8):

`old_string`:
```
Questa skill si posiziona *prima* di `sdlc-analyzer` nel flusso BR.
```

`new_string`:
```
Questa skill si posiziona *prima* di `sdlc-analyzer` nel flusso SDLC.
```

Edit 2 (MAPPING-SDLC riga 10):

`old_string`:
```
Il flusso BR completo:
```

`new_string`:
```
Il flusso SDLC completo:
```

Edit 3 (MAPPING-PIANO riga 179):

`old_string`:
```
### Domanda 1 — Nome del BR
```

`new_string`:
```
### Domanda 1 — Nome del Piano
```

Edit 4 (MAPPING-PIANO riga 181):

`old_string`:
```
> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
```

`new_string`:
```
> Come vuoi chiamare questo Piano? Il nome verra' usato per creare la cartella di lavoro.
```

Edit 5 (MAPPING-AFU riga 191):

`old_string`:
```
> Dove trovo la documentazione del BR? Dammi i path per:
```

`new_string`:
```
> Dove trovo l'AFU? Dammi i path per:
```

Edit 6 (MAPPING-AFU riga 192):

`old_string`:
```
> - **BR** (il documento principale dei requisiti)
```

`new_string`:
```
> - **AFU** (il documento principale dei requisiti)
```

Edit 7 (MAPPING-PIANO riga 202):

`old_string`:
```
> Quali sono le repository/codebase coinvolte in questo BR?
```

`new_string`:
```
> Quali sono le repository/codebase coinvolte in questo Piano?
```

Edit 8 (MAPPING-PIANO riga 209):

`old_string`:
```
> Se una repo non e' coinvolta nel BR, non includerla.
```

`new_string`:
```
> Se una repo non e' coinvolta nel Piano, non includerla.
```

Edit 9 (MAPPING-PIANO riga 218):

`old_string`:
```
> - Nome BR: [nome] → cartella `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`
```

`new_string`:
```
> - Nome Piano: [nome] → cartella `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`
```

Edit 10 (MAPPING-AFU riga 285):

`old_string`:
```
O il BR descrive la UI senza definire la logica dietro?
```

`new_string`:
```
O l'AFU descrive la UI senza definire la logica dietro?
```

Edit 11 (MAPPING-AFU riga 291):

`old_string`:
```
**BR vs mockup** — ogni elemento visuale nel mockup ha un corrispettivo funzionale nel BR? Il BR descrive funzionalita' che il mockup non mostra?
```

`new_string`:
```
**AFU vs mockup** — ogni elemento visuale nel mockup ha un corrispettivo funzionale nell'AFU? L'AFU descrive funzionalita' che il mockup non mostra?
```

Edit 12 (MAPPING-AFU riga 292):

`old_string`:
```
**BR vs specifiche tecniche**
```

`new_string`:
```
**AFU vs specifiche tecniche**
```

Edit 13 (MAPPING-AFU riga 293):

`old_string`:
```
Se il BR dice "pratica" e il mockup dice "richiesta", e' un problema.
```

`new_string`:
```
Se l'AFU dice "pratica" e il mockup dice "richiesta", e' un problema.
```

Edit 14 (MAPPING-AFU riga 299):

`old_string`:
```
**Entita' e modelli dati** — il BR presuppone strutture dati che nel codice esistono ma sono diverse?
```

`new_string`:
```
**Entita' e modelli dati** — l'AFU presuppone strutture dati che nel codice esistono ma sono diverse?
```

Edit 15 (MAPPING-AFU riga 300):

`old_string`:
```
**Enum e costanti** — il BR definisce stati o valori che nel codice esistono gia' come enum con valori/nomi diversi?
```

`new_string`:
```
**Enum e costanti** — l'AFU definisce stati o valori che nel codice esistono gia' come enum con valori/nomi diversi?
```

Edit 16 (MAPPING-AFU riga 301):

`old_string`:
```
**API/endpoint** — il BR descrive operazioni che nel codice corrispondono ad API con naming o struttura diversa?
```

`new_string`:
```
**API/endpoint** — l'AFU descrive operazioni che nel codice corrispondono ad API con naming o struttura diversa?
```

Edit 17 (MAPPING-AFU riga 302):

`old_string`:
```
**Flussi e stati** — il BR descrive transizioni di stato che nel codice funzionano diversamente?
```

`new_string`:
```
**Flussi e stati** — l'AFU descrive transizioni di stato che nel codice funzionano diversamente?
```

Edit 18 (MAPPING-AFU riga 304):

`old_string`:
```
il BR presuppone strutture che nel codice esistono ma sono diverse. Questi disallineamenti vanno segnalati al team funzionale perche' possono essere errori nel BR o evoluzioni non documentate.
```

`new_string`:
```
l'AFU presuppone strutture che nel codice esistono ma sono diverse. Questi disallineamenti vanno segnalati al team funzionale perche' possono essere errori nell'AFU o evoluzioni non documentate.
```

Edit 19 (MAPPING-AFU riga 322):

`old_string`:
```
**Disallineamento col codice** | Il BR presuppone strutture/terminologie diverse da quelle nel codice
```

`new_string`:
```
**Disallineamento col codice** | L'AFU presuppone strutture/terminologie diverse da quelle nel codice
```

Edit 20 (MAPPING-AFU riga 338 — header file output):

`old_string`:
```
# Review Documentazione BR [nome/versione]
```

`new_string`:
```
# Review Documentazione AFU [nome/versione]
```

Edit 21 (MAPPING-AFU riga 414 — header tabella):

`old_string`:
```
| # | Concetto BR | Nel codice | File/Classe | Nota |
```

`new_string`:
```
| # | Concetto AFU | Nel codice | File/Classe | Nota |
```

Edit 22 (MAPPING-AFU riga 416):

`old_string`:
```
Il BR non menziona SUSPENDED
```

`new_string`:
```
L'AFU non menziona SUSPENDED
```

Edit 23 (MAPPING-PIANO riga 438):

`old_string`:
```
Entrambi i file (MD e DOCX) vengono salvati nella cartella del BR.
```

`new_string`:
```
Entrambi i file (MD e DOCX) vengono salvati nella cartella del Piano.
```

- [ ] **Step 3: Rename `<br-name>` → `<piano-name>` se presenti**

Run:
```bash
grep -n "<br-name>" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
```

Per ogni occorrenza, applica Edit con `replace_all: true`.

- [ ] **Step 4: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
```

Aggiungere alias:
- `"rivedi il br"` → `"rivedi il br", "rivedi l'AFU", "verifica l'AFU"`

- [ ] **Step 5: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-reviewer/SKILL.md
```

Expected:
- `BR` ≤ N (solo trigger multi-trigger)
- `br-name` = 0

---

### Task 2.9: Sdlc-analyzer — sostituzione testuale (31 BR)

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md`

Skill più impattata. Procedere con cautela.

- [ ] **Step 1: Localizza tutte le occorrenze (con contesto)**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Expected: 31 righe. Riferimento all'analisi pre-piano per il contesto di ognuna (frasi del documento input → AFU, cartelle/workflow → Piano, ecc.).

- [ ] **Step 2: Applica sostituzioni in batch ordinati per tipologia**

**Batch A — MAPPING-SDLC** (flusso/processo, ~2 occorrenze):

Edit A1:

`old_string`:
```
Il flusso BR completo:
```

`new_string`:
```
Il flusso SDLC completo:
```

**Batch B — MAPPING-AFU** (documento input, ~12 occorrenze):

Edit B1 (riga ~18):

`old_string`:
```
2. **Conversione documentazione** (solo se `sdlc-reviewer` non e' stato eseguito prima — se trova `requirements/` nella cartella del BR, salta questa fase)
```

`new_string`:
```
2. **Conversione documentazione** (solo se `sdlc-reviewer` non e' stato eseguito prima — se trova `requirements/` nella cartella del Piano, salta questa fase)
```

(Nota: questa è MAPPING-PIANO perché parla della cartella di lavoro, non del documento)

Edit B2 (riga ~202-203):

`old_string`:
```
> Dove trovo la documentazione del BR? Dammi i path per:
> - **BR** (il documento principale dei requisiti)
```

`new_string`:
```
> Dove trovo l'AFU? Dammi i path per:
> - **AFU** (il documento principale dei requisiti)
```

Edit B3 (riga ~304):

`old_string`:
```
Leggi integralmente ogni documento MD convertito nella cartella `requirements/` (dentro la cartella del BR). Per le immagini (mockup), usa Read sul file originale e descrivi nel dettaglio cosa vedi, mappando le UI ai componenti da implementare.
```

`new_string`:
```
Leggi integralmente ogni documento MD convertito nella cartella `requirements/` (dentro la cartella del Piano). Per le immagini (mockup), usa Read sul file originale e descrivi nel dettaglio cosa vedi, mappando le UI ai componenti da implementare.
```

(MAPPING-PIANO per "cartella del BR")

Edit B4 (riga ~326):

`old_string`:
```
**Nota**: il codebase viene letto dalla repo del progetto (dove la skill e' invocata). Solo gli artefatti BR (report, piano) vengono scritti in `deloitte-profiles`.
```

`new_string`:
```
**Nota**: il codebase viene letto dalla repo del progetto (dove la skill e' invocata). Solo gli artefatti del Piano (report, piano implementazione) vengono scritti in `deloitte-profiles`.
```

Edit B5 (riga ~330):

`old_string`:
```
Per ogni funzionalità richiesta dal BR, confronta con il codice esistente e classifica:
```

`new_string`:
```
Per ogni funzionalità richiesta dall'AFU, confronta con il codice esistente e classifica:
```

Edit B6 (riga ~337):

`old_string`:
```
| **Discrepanza** | Implementato ma diverso da quanto richiesto dal BR |
```

`new_string`:
```
| **Discrepanza** | Implementato ma diverso da quanto richiesto dall'AFU |
```

Edit B7 (riga ~338):

`old_string`:
```
| **Da chiarire** | Il BR è ambiguo o il codice suggerisce un'interpretazione diversa |
```

`new_string`:
```
| **Da chiarire** | L'AFU è ambigua o il codice suggerisce un'interpretazione diversa |
```

Edit B8 (riga ~341):

`old_string`:
```
- **Cosa richiede il BR** (con riferimento a sezione/pagina del documento)
```

`new_string`:
```
- **Cosa richiede l'AFU** (con riferimento a sezione/pagina del documento)
```

Edit B9 (riga ~347):

`old_string`:
```
Il livello di dettaglio deve essere sufficiente perché un agente Claude Code, leggendo solo il gap report, possa capire esattamente cosa va fatto senza dover rileggere il BR originale.
```

`new_string`:
```
Il livello di dettaglio deve essere sufficiente perché un agente Claude Code, leggendo solo il gap report, possa capire esattamente cosa va fatto senza dover rileggere l'AFU originale.
```

Edit B10 (riga ~370 — header file output):

`old_string`:
```
# Report Verifica BR [nome/versione]
```

`new_string`:
```
# Report Verifica AFU [nome/versione]
```

Edit B11 (riga ~383):

`old_string`:
```
- BR: `<path>`
```

`new_string`:
```
- AFU: `<path>`
```

Edit B12 (riga ~425 — header tabella):

`old_string`:
```
| [Requisito dal BR] | [Implementato/Non implementato/N/A]
```

`new_string`:
```
| [Requisito dall'AFU] | [Implementato/Non implementato/N/A]
```

Edit B13 (riga ~434):

`old_string`:
```
- Cosa richiede il BR
```

`new_string`:
```
- Cosa richiede l'AFU
```

Edit B14 (riga ~455):

`old_string`:
```
- **Impatto sul BR corrente:** `BLOCCA il task X` | `Da fixare in coda al BR` | `Solo segnalazione (gap pregresso)`
```

`new_string`:
```
- **Impatto sul Piano corrente:** `BLOCCA il task X` | `Da fixare in coda al Piano` | `Solo segnalazione (gap pregresso)`
```

(Qui "BR corrente" → "Piano corrente" perché si parla dell'unità di lavoro)

Edit B15 (riga ~469 — header file output):

`old_string`:
```
# Piano Implementazione [Nome feature/BR]
```

`new_string`:
```
# Piano Implementazione [Nome feature/AFU]
```

Edit B16 (riga ~500):

`old_string`:
```
Definisci gli stream basandoti sulle funzionalità del BR, non sulla struttura tecnica. Esempi:
```

`new_string`:
```
Definisci gli stream basandoti sulle funzionalità dell'AFU, non sulla struttura tecnica. Esempi:
```

**Batch C — MAPPING-PIANO** (cartella/workflow, ~12 occorrenze):

Edit C1 (riga ~20):

`old_string`:
```
4. **Generazione output** (2 file MD: gap report + piano di implementazione, nella cartella del BR)
```

`new_string`:
```
4. **Generazione output** (2 file MD: gap report + piano di implementazione, nella cartella del Piano)
```

Edit C2 (riga ~126):

`old_string`:
```
### Domanda 0 — Cartella BR esistente
```

`new_string`:
```
### Domanda 0 — Cartella Piano esistente
```

Edit C3 (riga ~153):

`old_string`:
```
> Ho trovato una cartella BR con review gia' completata:
```

`new_string`:
```
> Ho trovato una cartella Piano con review gia' completata:
```

Edit C4 (riga ~175):

`old_string`:
```
**Se non trovi nulla**, chiedi il nome del BR:
```

`new_string`:
```
**Se non trovi nulla**, chiedi il nome del Piano:
```

Edit C5 (riga ~177):

`old_string`:
```
> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
```

`new_string`:
```
> Come vuoi chiamare questo Piano? Il nome verra' usato per creare la cartella di lavoro.
```

Edit C6 (riga ~185):

`old_string`:
```
> Quali sono le repository/codebase coinvolte in questo BR?
```

`new_string`:
```
> Quali sono le repository/codebase coinvolte in questo Piano?
```

Edit C7 (riga ~191):

`old_string`:
```
> Elenca tutte quelle coinvolte, senza limiti. Se una repo non è coinvolta nel BR, non includerla.
```

`new_string`:
```
> Elenca tutte quelle coinvolte, senza limiti. Se una repo non è coinvolta nel Piano, non includerla.
```

Edit C8 (riga ~236):

`old_string`:
```
**Se `sdlc-reviewer` e' stato eseguito** e la cartella `requirements/` esiste gia' nella cartella del BR (`$BASE_PATH/todo/<data>_<nome>/requirements/`), **salta completamente questa fase** e vai alla Fase 3. La conversione e' gia' stata fatta da sdlc-reviewer.
```

`new_string`:
```
**Se `sdlc-reviewer` e' stato eseguito** e la cartella `requirements/` esiste gia' nella cartella del Piano (`$BASE_PATH/todo/<data>_<nome>/requirements/`), **salta completamente questa fase** e vai alla Fase 3. La conversione e' gia' stata fatta da sdlc-reviewer.
```

Edit C9 (riga ~242):

`old_string`:
```
Crea la cartella del BR e la sottocartella per i documenti convertiti:
```

`new_string`:
```
Crea la cartella del Piano e la sottocartella per i documenti convertiti:
```

Edit C10 (riga ~353):

`old_string`:
```
Se la cartella del BR non esiste ancora (sdlc-reviewer non eseguito), creala:
```

`new_string`:
```
Se la cartella del Piano non esiste ancora (sdlc-reviewer non eseguito), creala:
```

Edit C11 (riga ~361):

`old_string`:
```
Genera entrambi i file nella cartella del BR in `$BASE_PATH/todo/`. Questo e' lo stato iniziale: la cartella intera si sposta in `in-progress/` quando uno sviluppatore avvia la lavorazione con `sdlc-executor`, e in `done/` al completamento di tutte le task.
```

`new_string`:
```
Genera entrambi i file nella cartella del Piano in `$BASE_PATH/todo/`. Questo e' lo stato iniziale: la cartella intera si sposta in `in-progress/` quando uno sviluppatore avvia la lavorazione con `sdlc-executor`, e in `done/` al completamento di tutte le task.
```

Edit C12 (riga ~582):

`old_string`:
```
### 4.3 — Commit e push degli artefatti BR
```

`new_string`:
```
### 4.3 — Commit e push degli artefatti del Piano
```

- [ ] **Step 3: Rename `<br-name>` → `<piano-name>`**

Run:
```bash
grep -n "<br-name>" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Per ogni occorrenza, applica Edit con `replace_all: true`:
- `old_string`: `<br-name>`
- `new_string`: `<piano-name>`
- `replace_all`: true

- [ ] **Step 4: Sostituisci `Business Requirement` con `Analisi Funzionale Utente` (2 occorrenze totali)**

Run:
```bash
grep -n "Business Requirement" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Per ogni occorrenza, usa Edit per sostituire con `Analisi Funzionale Utente` (mantenendo il contesto circostante).

- [ ] **Step 5: Aggiorna description del frontmatter (multi-trigger)**

Read:
```bash
sed -n '1,8p' /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Aggiungere alias accanto ai trigger esistenti. Esempio Edit:

`old_string`:
```
Usa questa skill quando l'utente dice "abbiamo un nuovo br", "nuovo br", "c'è un br nuovo", "analizza il br", "gap analysis br", "nuovo business requirement"
```

`new_string`:
```
Usa questa skill quando l'utente dice "abbiamo un nuovo br", "abbiamo una nuova afu", "nuovo Piano", "c'è un br nuovo", "analizza il br", "analizza l'AFU", "gap analysis br", "gap analysis AFU", "nuovo business requirement", "nuova analisi funzionale utente"
```

(adatta al wording esatto della description esistente)

- [ ] **Step 6: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
grep -c "Business Requirement" /c/Users/davmelis/.claude/skills/sdlc-analyzer/SKILL.md
```

Expected:
- `BR` ≤ N (solo trigger multi-trigger)
- `br-name` = 0
- `Business Requirement` = 0

---

### Task 2.10: Verifica E2E Wave 2

**Files:**
- Read: tutti i 9 SKILL.md modificati

- [ ] **Step 1: Conteggio totale BR residuo per skill**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\bBR\b" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count BR residue"
done
```

Expected: numero piccolo per ogni skill (≤ 5 — solo trigger phrases multi-trigger nel frontmatter)

- [ ] **Step 2: Conteggio totale br-name residuo**

Run:
```bash
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\bbr-name\b" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count br-name residue"
done
```

Expected: tutti = 0

- [ ] **Step 3: Lettura review manuale di sdlc-analyzer (la più grande)**

Read del file:
```
~/.claude/skills/sdlc-analyzer/SKILL.md
```

Verificare visivamente per ogni sezione:
- Articoli italiani corretti (no `il AFU`, no `del AFU`)
- Plurali corretti (no `Piano attivi`, no `Piano precedenti`)
- Genere femminile per AFU (`l'AFU è ambigua`, non `ambiguo`)
- Header file output puliti (no doppi `Piano Piano`)
- Trigger phrases nel frontmatter ben formattati

- [ ] **Step 4: (Nessun commit git per Wave 2)**

Le skill SDLC sono fuori dal git claude-flow. Wave 2 completata in memoria. Backup `.bak-wave1` ancora disponibili per rollback completo.

- [ ] **Step 5: Marca Wave 2 come completata nel memory log**

Create file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave2-done.tmp
```

con contenuto:
```
Wave 2 completata 2026-05-21:
- 9 skill con sostituzione testuale BR → AFU/Piano completata
- Multi-trigger phrases nel description del frontmatter
- <br-name> → <piano-name> ovunque
- Nessuna occorrenza Business Requirement residua
```

---

# Wave 3 — Sdlc-profile-setup scrive il nuovo file config + migrazione legacy

**Obiettivo wave**: `sdlc-profile-setup` deve scrivere `.sdlc-local.json` per i nuovi setup e migrare automaticamente i profili `.br-local.json` legacy.

---

### Task 3.1: Sdlc-profile-setup — sostituisci tutti i riferimenti di SCRITTURA

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md`

- [ ] **Step 1: Localizza tutte le occorrenze `.br-local.json` rimaste**

Run:
```bash
grep -n "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected: ~9 occorrenze (la sezione di detection iniziale è già stata aggiornata in Wave 1; restano le sezioni di scrittura).

Esempio (basato sull'analisi pre-piano):
- Riga 3: `description: ...configurazione automatica di .br-local.json.` (è in frontmatter, modificata in Wave 2)
- Riga 461: `## Step 10 — Aggiorna .br-local.json`
- Riga 463: `Per ogni codebase fornito nello Step 3, proponi di aggiungere i campi a .br-local.json.`
- Riga 467: `> Per ogni codebase, aggiorno .br-local.json con il riferimento al project_repo.`
- Riga 470: `> File: C:/progetti/myapp-backend/.br-local.json`
- Riga 483: `> Per ogni codebase, aggiorno .br-local.json con il riferimento al profilo.`
- Riga 486: `> File: C:/progetti/myapp-backend/.br-local.json`
- Riga 499: `**Se .br-local.json non esiste**: crea il file con i campi base della modalita' scelta:`
- Riga 518: `> - .br-local.json aggiornato in N codebase`

- [ ] **Step 2: Rinomina Step 10 (titolo)**

Edit:

`old_string`:
```
## Step 10 — Aggiorna .br-local.json
```

`new_string`:
```
## Step 10 — Aggiorna .sdlc-local.json (con migrazione automatica per profili legacy)
```

- [ ] **Step 3: Aggiorna il primo paragrafo dello Step 10 (riga ~463)**

Edit:

`old_string`:
```
Per ogni codebase fornito nello Step 3, proponi di aggiungere i campi a `.br-local.json`. Lo schema cambia in base a `MODE`:
```

`new_string`:
```
Per ogni codebase fornito nello Step 3, proponi di aggiungere i campi a `.sdlc-local.json`. Lo schema cambia in base a `MODE`. Se nel codebase esiste già un `.br-local.json` legacy, viene migrato automaticamente:

**Algoritmo di scrittura/migrazione**:
1. Se `.sdlc-local.json` esiste già → leggi il contenuto, preserva tutti i campi esistenti, aggiungi/aggiorna solo i campi della modalità scelta
2. Se solo `.br-local.json` esiste (legacy) → migrazione automatica:
   a. Leggi il contenuto di `.br-local.json`
   b. Scrivi il contenuto (preservando i campi esistenti + aggiungendo/aggiornando i campi della modalità) in `.sdlc-local.json`
   c. Rinomina il vecchio file in `.br-local.json.bak` (NON cancellare, lascia traccia di rollback)
   d. Comunica all'utente:
      ```
      > Profilo legacy `.br-local.json` rilevato. Lo migro a `.sdlc-local.json`.
      > Il vecchio file viene conservato come `.br-local.json.bak` (puoi cancellarlo
      > quando sei sicuro che tutto funzioni).
      ```
3. Se entrambi `.sdlc-local.json` e `.br-local.json` esistono (caso patologico) → usa `.sdlc-local.json`, lascia `.br-local.json` invariato, segnala warning:
   ```
   > Trovati entrambi `.sdlc-local.json` e `.br-local.json` nella repo. Uso il primo.
   > Ti consiglio di rimuovere manualmente `.br-local.json` per evitare ambiguità.
   ```
4. Se nessuno dei due esiste → crea ex novo `.sdlc-local.json` con i campi base della modalità scelta
```

- [ ] **Step 4: Aggiorna i sample/template del file (righe ~467, 470, 483, 486)**

Edit (riga ~467):

`old_string`:
```
> Per ogni codebase, aggiorno `.br-local.json` con il riferimento al project_repo.
```

`new_string`:
```
> Per ogni codebase, aggiorno `.sdlc-local.json` con il riferimento al project_repo.
```

Edit (riga ~470):

`old_string`:
```
> File: `C:/progetti/myapp-backend/.br-local.json`
```

`new_string`:
```
> File: `C:/progetti/myapp-backend/.sdlc-local.json`
```

Edit (riga ~483):

`old_string`:
```
> Per ogni codebase, aggiorno `.br-local.json` con il riferimento al profilo.
```

`new_string`:
```
> Per ogni codebase, aggiorno `.sdlc-local.json` con il riferimento al profilo.
```

Edit (riga ~486):

`old_string`:
```
> File: `C:/progetti/myapp-backend/.sdlc-local.json`
```

(Nota: questa potrebbe essere già stata aggiornata dall'Edit precedente se il pattern è uguale. Verificare con grep prima di applicare.)

- [ ] **Step 5: Aggiorna la sezione "Se .br-local.json non esiste" (riga ~499)**

Edit:

`old_string`:
```
**Se `.br-local.json` non esiste**: crea il file con i campi base della modalita' scelta:
```

`new_string`:
```
**Se nessuno dei due file esiste** (`.sdlc-local.json` né `.br-local.json` legacy): crea ex novo `.sdlc-local.json` con i campi base della modalita' scelta:
```

- [ ] **Step 6: Aggiorna il riepilogo finale (riga ~518)**

Edit:

`old_string`:
```
> - `.br-local.json` aggiornato in N codebase
```

`new_string`:
```
> - `.sdlc-local.json` aggiornato/creato in N codebase (eventuali `.br-local.json` legacy migrati a `.sdlc-local.json` + `.br-local.json.bak`)
```

- [ ] **Step 7: Verifica che la sezione di detection iniziale (Wave 1) e quella di SCRITTURA (Wave 3) siano coerenti**

Run:
```bash
grep -n "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
grep -n "\.br-local\.json" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected:
- `.sdlc-local.json`: ≥ 6 occorrenze (tutte le menzioni di scrittura + detection + frontmatter)
- `.br-local.json`: ≥ 3 occorrenze (le menzioni legacy nella migrazione + fallback)

- [ ] **Step 8: Verifica BR e br-name = 0 (deve essere già 0 dalla Wave 2)**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
grep -c "\bbr-name\b" /c/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md
```

Expected: entrambi = 0

---

### Task 3.2: Smoke test Wave 3 (manuale)

**Files:**
- Read: `C:/Users/davmelis/.claude/skills/sdlc-profile-setup/SKILL.md`

- [ ] **Step 1: Lettura review manuale dello Step 10**

Read del file modificato e leggi attentamente la sezione "Step 10" per verificare:
- L'algoritmo di scrittura/migrazione è chiaro e implementabile da un agente
- I 4 casi (sdlc esiste, solo br legacy, entrambi, nessuno) sono coperti
- Il warning soft e il warning patologico sono ben formattati come blockquote
- Schema JSON non è cambiato (deve essere lo stesso di prima)

- [ ] **Step 2: Test mentale dei 4 scenari di migrazione**

Per ognuno dei 4 scenari, verifica leggendo il file che la skill saprebbe cosa fare:
1. Profilo nuovo (no file) → crea `.sdlc-local.json` ex novo ✓
2. Profilo legacy (`.br-local.json` esiste) → migra + crea `.bak` ✓
3. Profilo nuovo già esistente (`.sdlc-local.json` esiste) → aggiorna in place ✓
4. Caso patologico (entrambi) → usa nuovo, warning ✓

- [ ] **Step 3: Marca Wave 3 come completata**

Create file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave3-done.tmp
```

con contenuto:
```
Wave 3 completata 2026-05-21:
- sdlc-profile-setup scrive .sdlc-local.json (Step 10 aggiornato)
- Migrazione automatica per profili legacy con .br-local.json.bak
- Schema JSON invariato
```

---

# Wave 4 — Documentazione esterna

**Obiettivo wave**: allineare `SDLC_SKILLS_DOCUMENTATION.md` + `~/.claude/CLAUDE.md` + `docs/ROADMAP_NEW_SKILLS.md` alla nuova terminologia.

**File git tracked**: `docs/ROADMAP_NEW_SKILLS.md` è dentro la repo claude-flow → questa è l'unica wave con commit git.

---

### Task 4.1: SDLC_SKILLS_DOCUMENTATION.md — sostituzione testuale

**Files:**
- Modify: `C:/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md`

- [ ] **Step 1: Localizza tutte le occorrenze BR**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md
```

Expected: 36 righe.

- [ ] **Step 2: Localizza tutte le occorrenze `.br-local.json`**

Run:
```bash
grep -n "\.br-local\.json" /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md
```

Expected: 15 righe.

- [ ] **Step 3: Lettura review del file completo**

Read del file `C:/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md` (47KB, leggerlo per sezioni se necessario).

Mappare ogni occorrenza BR con il contesto (documento input → AFU; workflow/cartella → Piano; processo → SDLC) seguendo le regole del Glossary & Mapping Rules.

- [ ] **Step 4: Applica sostituzioni Edit, una per ogni occorrenza**

Per ogni occorrenza BR identificata nello Step 1, applica un Edit con il mapping corretto. Le sostituzioni MOLTO frequenti si possono fare con `replace_all: true` SE il pattern è univoco:

Esempio sostituzioni candidate per `replace_all`:
- `"cartella BR"` → `"cartella del Piano"` (se mai compare in altri contesti, verificare prima)
- `"documentazione BR"` → `"documentazione AFU"`
- `"flusso BR"` → `"flusso SDLC"`

Esempio sostituzioni che richiedono Edit puntuale (per contesto specifico):
- Header di sezione, esempi di output, frasi di paragrafo

Per minimizzare gli errori, procedere prima con i pattern più univoci (`replace_all`) e poi con quelli puntuali.

- [ ] **Step 5: Aggiorna riferimenti `.br-local.json` → `.sdlc-local.json` aggiungendo nota fallback**

Per ogni occorrenza `.br-local.json`, decidere:
- Se è un riferimento generico al file di configurazione → sostituire con `.sdlc-local.json (con fallback compatibile a .br-local.json per profili legacy)`
- Se è in un esempio di codice/path → sostituire con `.sdlc-local.json`
- Se descrive specificamente il fallback legacy → mantenere `.br-local.json` come riferimento

Aggiungere una sezione "Nota sulla migrazione legacy" se non già presente nel documento, che spieghi la convivenza tra `.sdlc-local.json` e `.br-local.json` con priorità al primo.

- [ ] **Step 6: Aggiorna esempi di trigger phrase per riflettere il multi-trigger**

Se il documento contiene esempi di trigger come `"abbiamo un nuovo br"`, aggiornarli a:
```
"abbiamo un nuovo br" / "abbiamo una nuova afu" / "nuovo Piano"
```

- [ ] **Step 7: Aggiungi o aggiorna glossario terminologico**

Se il documento ha già una sezione "Glossario", aggiungere/aggiornare:
- **AFU**: Analisi Funzionale Utente, il documento di specifica funzionale ricevuto dal team funzionale (era "BR" prima della migrazione del 2026-05-21)
- **Piano**: l'unità di lavoro (cartella che contiene PLAN.md, TASKS.md, PROGRESS.md, BUG_REPORT.md) — era "BR" prima della migrazione
- **SDLC**: il processo/ciclo di vita complessivo che orchestra review → analysis → execution → testing → debug → progress reporting
- **`.sdlc-local.json`**: file di configurazione del profilo nella repo del progetto (era `.br-local.json` prima della migrazione, ancora supportato come fallback compatibile)

Se non esiste una sezione glossario, crearne una nuova alla fine del documento.

- [ ] **Step 8: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md
```

Expected: ≤ N (solo dove appare in esempi di trigger phrases multi-trigger; idealmente 0 fuori da quegli esempi)

Run:
```bash
grep -c "\.sdlc-local\.json" /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md
```

Expected: ≥ 12

---

### Task 4.2: ~/.claude/CLAUDE.md — sostituzione testuale + multi-trigger

**Files:**
- Modify: `C:/Users/davmelis/.claude/CLAUDE.md`

- [ ] **Step 1: Backup pre-modifica**

Run:
```bash
cp /c/Users/davmelis/.claude/CLAUDE.md /c/Users/davmelis/.claude/CLAUDE.md.bak-pre-migration
ls -la /c/Users/davmelis/.claude/CLAUDE.md.bak-pre-migration
```

Expected: file presente

- [ ] **Step 2: Localizza le 9 entry skill SDLC**

Run:
```bash
grep -n "^# sdlc-" /c/Users/davmelis/.claude/CLAUDE.md
```

Expected: 9 righe con headers `# sdlc-analyzer`, `# sdlc-clarify`, ecc.

- [ ] **Step 3: Localizza le occorrenze BR**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/.claude/CLAUDE.md
```

Expected: 10 righe.

- [ ] **Step 4: Aggiorna le trigger phrases di ogni entry**

Per ogni entry, leggere la sezione `When the user says ...` e aggiungere alias multi-trigger. Esempi:

**sdlc-analyzer** — Edit:

`old_string`:
```
When the user says "abbiamo un nuovo br" (or similar phrases about a new business requirement), invoke the Skill tool with `skill: "sdlc-analyzer"` before doing anything else.
```

`new_string`:
```
When the user says "abbiamo un nuovo br", "abbiamo una nuova afu", "nuovo Piano", or similar phrases about a new business requirement / nuova AFU / nuovo Piano, invoke the Skill tool with `skill: "sdlc-analyzer"` before doing anything else.
```

**sdlc-reviewer** — Edit:

`old_string`:
```
When the user says "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", "nuovo br da verificare", or similar phrases about reviewing BR documentation quality, invoke the Skill tool with `skill: "sdlc-reviewer"` before doing anything else.
```

`new_string`:
```
When the user says "rivedi il br", "rivedi l'AFU", "review del br", "review dell'AFU", "controlla la documentazione", "verifica il br", "verifica l'AFU", "nuovo br da verificare", "nuova AFU da verificare", or similar phrases about reviewing BR / AFU documentation quality, invoke the Skill tool with `skill: "sdlc-reviewer"` before doing anything else.
```

**sdlc-clarify** — Edit:

`old_string`:
```
When the user says "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", "risposte al review", or similar phrases about receiving functional team responses to BR review questions, invoke the Skill tool with `skill: "sdlc-clarify"` before doing anything else.
```

`new_string`:
```
When the user says "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", "risposte al review", or similar phrases about receiving functional team responses to BR / AFU review questions, invoke the Skill tool with `skill: "sdlc-clarify"` before doing anything else.
```

**sdlc-debug** — Edit:

`old_string`:
```
When the user says "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti", "lavora il bug", "fix il bug", "debug br", "il funzionale ha testato", "bug confermati", "aggiorna i bug", or similar phrases about managing bugs on a BR, invoke the Skill tool with `skill: "sdlc-debug"` before doing anything else.
```

`new_string`:
```
When the user says "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti", "lavora il bug", "fix il bug", "debug br", "debug Piano", "bug su Piano", "il funzionale ha testato", "bug confermati", "aggiorna i bug", or similar phrases about managing bugs on a BR / Piano, invoke the Skill tool with `skill: "sdlc-debug"` before doing anything else.
```

**sdlc-executor** — Edit:

`old_string`:
```
When the user says "lavora il task", "inizia a lavorare", "esegui il piano", or similar phrases about executing tasks from an implementation plan, invoke the Skill tool with `skill: "sdlc-executor"` before doing anything else.
```

`new_string`:
```
When the user says "lavora il task", "lavora il Piano", "inizia a lavorare", "esegui il piano", or similar phrases about executing tasks from an implementation plan, invoke the Skill tool with `skill: "sdlc-executor"` before doing anything else.
```

**sdlc-updater** — Edit:

`old_string`:
```
When the user says "il br è stato aggiornato", "aggiorna il piano", "nuova versione del br", "documentazione aggiornata", or similar phrases about updated BR documentation, invoke the Skill tool with `skill: "sdlc-updater"` before doing anything else.
```

`new_string`:
```
When the user says "il br è stato aggiornato", "l'AFU è stata aggiornata", "aggiorna il piano", "nuova versione del br", "nuova versione AFU", "documentazione aggiornata", or similar phrases about updated BR / AFU documentation, invoke the Skill tool with `skill: "sdlc-updater"` before doing anything else.
```

**sdlc-progress-report** — trigger già neutri ("genera il report excel", "stato avanzamento"), nessuna modifica significativa salvo eventuali riferimenti generici a BR nella description.

**sdlc-estimator** — Edit:

`old_string`:
```
When the user says "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR, invoke the Skill tool with `skill: "sdlc-estimator"` before doing anything else.
```

`new_string`:
```
When the user says "stima il br", "stima il Piano", "stima l'AFU", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR / AFU / Piano, invoke the Skill tool with `skill: "sdlc-estimator"` before doing anything else.
```

**sdlc-profile-setup** — Edit:

`old_string`:
```
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating or configuring a project profile for the BR skills, invoke the Skill tool with `skill: "sdlc-profile-setup"` before doing anything else.
```

`new_string`:
```
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating or configuring a project profile for the SDLC skills, invoke the Skill tool with `skill: "sdlc-profile-setup"` before doing anything else.
```

- [ ] **Step 5: Aggiorna le descrizioni (testo prima del "When the user says")**

Per ognuna delle 9 entry, leggere la descrizione e applicare il mapping AFU/Piano dove appropriato. Esempi:

Edit (sdlc-analyzer description):

`old_string`:
```
- **sdlc-analyzer** (`~/.claude/skills/sdlc-analyzer/SKILL.md`) - analisi gap tra BR e codice + piano di implementazione. Trigger: "abbiamo un nuovo br"
```

`new_string`:
```
- **sdlc-analyzer** (`~/.claude/skills/sdlc-analyzer/SKILL.md`) - analisi gap tra AFU (documento funzionale input) e codice + Piano di implementazione. Trigger: "abbiamo un nuovo br" / "abbiamo una nuova afu" / "nuovo Piano"
```

Ripetere per tutte le 9 entry, mantenendo coerenza con il mapping.

- [ ] **Step 6: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/.claude/CLAUDE.md
```

Expected: ≤ N (solo dove BR appare come parte di trigger phrases multi-trigger esplicito; idealmente compreso fra 5 e 9 — uno per ogni multi-trigger preservato)

---

### Task 4.3: docs/ROADMAP_NEW_SKILLS.md — doppio lavoro (rename skill + BR→AFU/Piano)

**Files:**
- Modify: `C:/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md`

- [ ] **Step 1: Backup pre-modifica (git tracked, ma per sicurezza)**

Run:
```bash
cp /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md.bak-pre-migration
```

(Il `.bak` non verrà commitato, lasciato come safety net.)

- [ ] **Step 2: Lettura review del file completo**

Read del file:
```
/c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md
```

- [ ] **Step 3: Identifica tutti i nomi vecchi delle skill `br-*`**

Run:
```bash
grep -n "br-" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md
```

Esempio (basato sull'analisi pre-piano, riga 10):
```
BR arriva → br-reviewer → br-clarify → br-analyzer → br-estimator → br-executor → br-progress-report → br-debug → br-updater
                                                                                                              ↑
                                                                                                    br-pipeline (orchestratore)
```

- [ ] **Step 4: Rename `br-*` → `sdlc-*` con `replace_all: true` (uno per skill)**

Per ogni skill, applica Edit con `replace_all: true`:

Edit 1:
- `old_string`: `br-reviewer`
- `new_string`: `sdlc-reviewer`
- `replace_all`: true

Edit 2:
- `old_string`: `br-clarify`
- `new_string`: `sdlc-clarify`
- `replace_all`: true

Edit 3:
- `old_string`: `br-analyzer`
- `new_string`: `sdlc-analyzer`
- `replace_all`: true

Edit 4:
- `old_string`: `br-estimator`
- `new_string`: `sdlc-estimator`
- `replace_all`: true

Edit 5:
- `old_string`: `br-executor`
- `new_string`: `sdlc-executor`
- `replace_all`: true

Edit 6:
- `old_string`: `br-progress-report`
- `new_string`: `sdlc-progress-report`
- `replace_all`: true

Edit 7:
- `old_string`: `br-debug`
- `new_string`: `sdlc-debug`
- `replace_all`: true

Edit 8:
- `old_string`: `br-updater`
- `new_string`: `sdlc-updater`
- `replace_all`: true

Edit 9 (se presente — `br-pipeline` potrebbe essere un nome storico, valutare se rinominare in `sdlc-pipeline` o lasciare):
- Decisione: se nel ROADMAP esiste ancora `br-pipeline`, rinominarlo in `sdlc-pipeline` per consistenza
- `old_string`: `br-pipeline`
- `new_string`: `sdlc-pipeline`
- `replace_all`: true

- [ ] **Step 5: Localizza occorrenze BR rimaste (dopo il rename `br-*`)**

Run:
```bash
grep -n "\bBR\b" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md
```

Expected: ~18 occorrenze BR (parola intera, non più legate ai nomi skill).

Esempio (riga 5):
```
Analisi del pipeline BR attuale e identificazione dei gap nel ciclo di vita dei Business Requirement.
```

- [ ] **Step 6: Applica mapping BR → AFU/Piano/SDLC con Edit puntuale**

Per ogni occorrenza, identificare il contesto e applicare:

Esempio Edit (riga 5):

`old_string`:
```
Analisi del pipeline BR attuale e identificazione dei gap nel ciclo di vita dei Business Requirement.
```

`new_string`:
```
Analisi del pipeline SDLC attuale e identificazione dei gap nel ciclo di vita dei Piani (ex Business Requirement / nuovo termine: AFU per il documento input, Piano per l'unità di lavoro).
```

Esempio Edit (riga 10 — diagramma del flusso):

`old_string`:
```
BR arriva → sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-estimator → sdlc-executor → sdlc-progress-report → sdlc-debug → sdlc-updater
```

`new_string`:
```
AFU arriva → sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-estimator → sdlc-executor → sdlc-progress-report → sdlc-debug → sdlc-updater
```

Continuare per tutte le 18 occorrenze, applicando il mapping contestuale.

- [ ] **Step 7: Verifica finale**

Run:
```bash
grep -c "\bBR\b" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md
grep -c "\bbr-" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md
```

Expected:
- `BR` = 0
- `br-` = 0 (tutti i nomi skill rinominati)

---

### Task 4.4: Commit Wave 4

**Files:**
- Commit: `docs/ROADMAP_NEW_SKILLS.md`

- [ ] **Step 1: Verifica stato git**

Run:
```bash
cd /c/Users/davmelis/Documents/MyGitHub/claude-flow
git status --short docs/ROADMAP_NEW_SKILLS.md
```

Expected: il file ROADMAP risulta tracked (era untracked nel git status iniziale, ora va aggiunto).

- [ ] **Step 2: Aggiungi il file e committa**

Run:
```bash
cd /c/Users/davmelis/Documents/MyGitHub/claude-flow
git add docs/ROADMAP_NEW_SKILLS.md
git commit -m "$(cat <<'EOF'
docs(sdlc): wave 4 — allinea ROADMAP_NEW_SKILLS al vocabolario AFU/Piano e ai nomi skill sdlc-*

Doppio refactor sul roadmap:
- Rename nomi skill `br-*` → `sdlc-*` (residuo del refactor 2026-05-18)
- Applica mapping terminologico BR → AFU (documento input) / Piano (workflow) / SDLC (processo)

Wave 4 fa parte della migrazione BR→AFU/Piano definita in
docs/superpowers/specs/2026-05-21-sdlc-br-to-afu-piano-migration-design.md.

Le altre modifiche della Wave 4 (SDLC_SKILLS_DOCUMENTATION.md e
~/.claude/CLAUDE.md) vivono fuori dal git claude-flow.
EOF
)"
```

- [ ] **Step 3: Verifica commit**

Run:
```bash
cd /c/Users/davmelis/Documents/MyGitHub/claude-flow
git log -1 --oneline
git log -1 --stat
```

Expected: commit appena creato con `docs/ROADMAP_NEW_SKILLS.md` come unico file modificato.

- [ ] **Step 4: NON push**

Il push viene fatto separatamente dall'utente quando vuole. Non eseguire `git push`.

- [ ] **Step 5: Marca Wave 4 come completata**

Create file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave4-done.tmp
```

con contenuto:
```
Wave 4 completata 2026-05-21:
- SDLC_SKILLS_DOCUMENTATION.md allineato
- ~/.claude/CLAUDE.md allineato con multi-trigger per 9 entry skill
- docs/ROADMAP_NEW_SKILLS.md allineato + nomi skill br-* → sdlc-*
- Commit git: docs/ROADMAP_NEW_SKILLS.md (le altre modifiche vivono fuori dal git claude-flow)
```

---

# Wave 5 — E2E checklist + cleanup + memory update

**Obiettivo wave**: verifica finale end-to-end, cleanup dei file `.bak`, aggiornamento memory file ufficiale.

---

### Task 5.1: E2E checklist finale

**Files:**
- Read: tutte le 9 SKILL.md + SDLC_SKILLS_DOCUMENTATION.md + ~/.claude/CLAUDE.md + docs/ROADMAP_NEW_SKILLS.md

- [ ] **Step 1: Conteggio BR finale per file**

Run:
```bash
echo "=== SKILL.md files ==="
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\bBR\b" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count BR residue"
done
echo ""
echo "=== Documentation files ==="
echo "SDLC_SKILLS_DOCUMENTATION.md: $(grep -c "\bBR\b" /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md) BR residue"
echo "~/.claude/CLAUDE.md: $(grep -c "\bBR\b" /c/Users/davmelis/.claude/CLAUDE.md) BR residue"
echo "docs/ROADMAP_NEW_SKILLS.md: $(grep -c "\bBR\b" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md) BR residue"
```

Expected: tutti ≤ N (solo dove appaiono come parte di trigger phrases multi-trigger esplicito)

- [ ] **Step 2: Conteggio br-name finale**

Run:
```bash
echo "=== br-name residue ==="
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\bbr-name\b" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count br-name residue"
done
echo "docs/ROADMAP_NEW_SKILLS.md: $(grep -c "\bbr-" /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md) br- residue (nomi skill)"
```

Expected: tutti = 0

- [ ] **Step 3: Verifica lettura compatibile in tutte le 9 skill**

Run:
```bash
echo "=== lettura compatibile (.sdlc-local.json menzionato) ==="
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\.sdlc-local\.json" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count occorrenze .sdlc-local.json"
done
echo ""
echo "=== fallback .br-local.json ancora presente ==="
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  count=$(grep -c "\.br-local\.json" "/c/Users/davmelis/.claude/skills/$skill/SKILL.md")
  echo "$skill: $count occorrenze .br-local.json"
done
```

Expected:
- `.sdlc-local.json` ≥ 1 in tutte le 9 skill
- `.br-local.json` ≥ 1 in tutte le 9 skill (fallback presente)

- [ ] **Step 4: Lettura review finale di sdlc-analyzer (la skill più impattata)**

Read del file:
```
~/.claude/skills/sdlc-analyzer/SKILL.md
```

Verifica visiva finale:
- Tutti gli header sono coerenti
- Tutti gli articoli italiani sono corretti
- Tutte le frasi sono leggibili e fluenti
- Nessuna frase è diventata sgrammaticata
- Il frontmatter `description:` è ben formato (no apostrofi singoli interni a stringa YAML)

- [ ] **Step 5: Test di attivazione di una skill (manuale)**

Test mentale (non eseguibile in questo ambiente):
- Se l'utente dice `"abbiamo un nuovo br"` → la skill `sdlc-analyzer` deve attivarsi (multi-trigger)
- Se l'utente dice `"abbiamo una nuova afu"` → la skill `sdlc-analyzer` deve attivarsi (nuovo trigger)
- Se l'utente dice `"rivedi l'AFU"` → la skill `sdlc-reviewer` deve attivarsi

Annotare in caso di dubbi sulla riga delle trigger phrases nel CLAUDE.md per le 9 entry.

---

### Task 5.2: Cleanup file .bak

**Files:**
- Delete: 9 file `.bak-wave1` in `~/.claude/skills/sdlc-*/`
- Delete: `~/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md.bak-pre-migration`
- Delete: `~/.claude/CLAUDE.md.bak-pre-migration`
- Delete: `docs/ROADMAP_NEW_SKILLS.md.bak-pre-migration`
- Delete: 4 file `.tmp` di marker wave nel memory folder

- [ ] **Step 1: Conferma con l'utente prima di cancellare i backup**

Chiedi all'utente:
> "Verifica completata con successo. Posso eliminare i file `.bak-wave1` e `.bak-pre-migration`? (O preferisci conservarli ancora qualche giorno come safety net?)"

- [ ] **Step 2: Se l'utente conferma, elimina i backup**

Run:
```bash
# Backup wave1 delle skill
for skill in sdlc-analyzer sdlc-clarify sdlc-debug sdlc-estimator sdlc-executor sdlc-profile-setup sdlc-progress-report sdlc-reviewer sdlc-updater; do
  rm -f "/c/Users/davmelis/.claude/skills/$skill/SKILL.md.bak-wave1"
done

# Backup pre-migration delle docs
rm -f /c/Users/davmelis/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md.bak-pre-migration
rm -f /c/Users/davmelis/.claude/CLAUDE.md.bak-pre-migration
rm -f /c/Users/davmelis/Documents/MyGitHub/claude-flow/docs/ROADMAP_NEW_SKILLS.md.bak-pre-migration

# Marker tmp wave
rm -f /c/Users/davmelis/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave*-done.tmp
```

- [ ] **Step 3: Verifica cleanup**

Run:
```bash
find /c/Users/davmelis/.claude -name "*.bak-wave1" -o -name "*.bak-pre-migration" 2>/dev/null
find /c/Users/davmelis/Documents/MyGitHub/claude-flow -name "*.bak-pre-migration" 2>/dev/null
ls /c/Users/davmelis/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/wave*-done.tmp 2>/dev/null || echo "no tmp files"
```

Expected: nessun output (tutti puliti)

---

### Task 5.3: Aggiorna memory file ufficiale

**Files:**
- Modify: `~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/sdlc-refactor-complete.md`
- Modify: `~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/MEMORY.md`

- [ ] **Step 1: Read memory file esistente**

Read del file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/sdlc-refactor-complete.md
```

- [ ] **Step 2: Aggiungi nota sulla migrazione BR→AFU/Piano**

Edit (append in fondo al file, prima di eventuale blocco di chiusura):

Aggiungere blocco markdown:

```markdown

## Aggiornamento 2026-05-21 — Migrazione BR → AFU / Piano

Completata la migrazione terminologica nelle 9 skill SDLC e nella documentazione esterna:

- **AFU** (Analisi Funzionale Utente) per il documento di input ricevuto dal team funzionale
- **Piano** per l'unità di lavoro (cartella, workflow, identificatore, stato)
- **SDLC** per il processo/ciclo di vita complessivo

**File config**: `.br-local.json` → `.sdlc-local.json` con lettura compatibile (fallback al vecchio nome). Profili legacy migrati automaticamente al prossimo `/sdlc-profile-setup` con `.br-local.json.bak` come safety net.

**Trigger phrases**: multi-trigger attivo nelle 9 skill — BR continua a funzionare come alias accanto ai nuovi AFU/Piano. Esempio: `"abbiamo un nuovo BR"` e `"abbiamo una nuova AFU"` attivano entrambi `sdlc-analyzer`.

**Scope**: 9 SKILL.md, SDLC_SKILLS_DOCUMENTATION.md, ~/.claude/CLAUDE.md, docs/ROADMAP_NEW_SKILLS.md. Presentazioni .pptx escluse (refactor manuale separato).

**Spec di riferimento**: [2026-05-21-sdlc-br-to-afu-piano-migration-design.md](../../../Documents/MyGitHub/claude-flow/docs/superpowers/specs/2026-05-21-sdlc-br-to-afu-piano-migration-design.md)
**Plan di riferimento**: [2026-05-21-sdlc-br-to-afu-piano-migration.md](../../../Documents/MyGitHub/claude-flow/docs/superpowers/plans/2026-05-21-sdlc-br-to-afu-piano-migration.md)
```

- [ ] **Step 3: Aggiorna anche il MEMORY.md index**

Read del file:
```
~/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/MEMORY.md
```

Edit per aggiungere o aggiornare la riga relativa a `sdlc-refactor-complete.md`. Se la riga esiste già, sostituirla con:

```markdown
- [SDLC refactor + BR→AFU/Piano migration (2026-05-21)](sdlc-refactor-complete.md) — refactor 5 waves + migrazione terminologica BR→AFU/Piano completati: 9 skill dual-mode, multi-trigger, .sdlc-local.json con fallback compatibile
```

- [ ] **Step 4: Verifica modifiche**

Run:
```bash
cat /c/Users/davmelis/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/MEMORY.md
echo "---"
tail -20 /c/Users/davmelis/.claude/projects/C--Users-davmelis-Documents-MyGitHub-claude-flow/memory/sdlc-refactor-complete.md
```

Expected: la nuova nota è presente in `sdlc-refactor-complete.md` e la riga in MEMORY.md è aggiornata.

---

## Self-Review

**1. Spec coverage** — confronto con la spec `2026-05-21-sdlc-br-to-afu-piano-migration-design.md`:

| Spec Section | Task implementing it |
|---|---|
| §1 Contesto e problema | Plan goal/architecture (header) |
| §2 D1-D10 Decisioni di design | Glossary & Mapping Rules + Task 1.x-5.x |
| §3.1 Mapping contestuale | MAPPING-AFU / MAPPING-PIANO / MAPPING-SDLC (glossary) |
| §3.2 Rename file/path tecnici | MAPPING-PATH + Task 1.1-1.10 (lettura), Task 3.1 (scrittura) |
| §3.3 Trigger phrases multi-trigger | MAPPING-TRIGGER + Task 2.1-2.9 Step "Aggiorna description" + Task 4.2 Step 4-5 |
| §3.4 Invarianti | Plan File Structure (non include i file invarianti) |
| §4.1 Scope concreto inventario | Plan File Structure tabella |
| §4.2 ROADMAP doppio lavoro | Task 4.3 Step 4 + Step 5-6 |
| §4.3 File esclusi | Plan File Structure (non include i file esclusi) |
| §5.1 Wave 1 | Task 1.1-1.11 |
| §5.2 Wave 2 | Task 2.1-2.10 |
| §5.3 Wave 3 | Task 3.1-3.2 |
| §5.4 Wave 4 | Task 4.1-4.4 |
| §6.1 Matrice compat | Implementata in Task 1.x (lettura) + Task 3.1 (scrittura, 4 scenari) |
| §6.2 Trigger utente | Multi-trigger in Task 2.x + Task 4.2 |
| §6.3 Rollback strategy | Backup .bak in Task 1.1 + cleanup Task 5.2 |
| §7 Checklist E2E | Task 5.1 |
| §7.4 Aggiornamento memory | Task 5.3 |
| §8 Order of execution | Wave ordering 1→2→3→4→5 |

Nessuna sezione della spec è scoperta.

**2. Placeholder scan** — riletto il piano:
- Nessun "TBD" / "TODO"
- Codice e pattern Edit presenti in tutte le task che modificano file
- Riferimenti a "pattern Task 1.2 Step 3" sono ammissibili perché il pattern è esplicitato in Task 1.2 (non un riferimento a codice non ancora scritto)

**3. Type consistency** — verificato:
- `.sdlc-local.json` (con punto iniziale) usato consistentemente in tutto il piano
- `<piano-name>` (con trattino, non underscore) usato consistentemente
- `MAPPING-AFU` / `MAPPING-PIANO` / `MAPPING-SDLC` / `MAPPING-PATH` / `MAPPING-TRIGGER` riferiti coerentemente
- Nomi skill: sempre `sdlc-*` (mai più `br-*` post-Wave 4)

---

## Note finali

- Le wave 1, 2, 3 NON producono commit git (file fuori dalla repo claude-flow). Le modifiche sono comunque tracciate nei file `.bak-wave1` e `.tmp` marker.
- L'unica wave con commit git è la Wave 4 (per `docs/ROADMAP_NEW_SKILLS.md`).
- Il plan è retro-compatibile: ogni wave può essere rollback indipendentemente ripristinando i `.bak`.
- Stima tempo totale: 60-90 minuti per un agente che esegue task-by-task con verifica intermedia.
