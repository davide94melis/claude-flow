# Migrazione terminologica `BR` → `AFU` / `Piano` nelle skill SDLC

**Data:** 2026-05-21
**Stato:** Design approvato, in attesa di plan di implementazione
**Repo coinvolti:** `claude-flow` (docs/ROADMAP_NEW_SKILLS.md), `~/.claude/skills/sdlc-*` (9 skill + documentazione), `~/.claude/CLAUDE.md` (registrazioni globali). Repo `deloitte-profiles` non toccata: i profili esistenti continuano a funzionare grazie alla lettura compatibile.
**Relazione con design precedenti:** completa la D5 del [2026-05-18-sdlc-rename-design.md](./2026-05-18-sdlc-rename-design.md), che aveva esplicitamente lasciato "terminologia di dominio BR nei testi → invariata" in attesa di una scelta semantica più chiara su come sostituirla.

---

## 1. Contesto e problema

Il refactor del 2026-05-18 ha rinominato i nomi tecnici delle skill da `br-*` a `sdlc-*`, ma ha **deliberatamente lasciato** la parola "BR" (Business Requirement) nei testi user-facing, nelle domande all'utente, negli header dei file output e nei placeholder tecnici (`<br-name>`, `.br-local.json`). Conseguenza: oggi le skill `sdlc-*` parlano ancora di "BR" in 125+ punti, generando incoerenza tra il nome tecnico ("sdlc-analyzer") e il vocabolario user-facing ("abbiamo un nuovo BR").

L'utente vuole completare la transizione semantica con un mapping **contestuale**: la parola "BR" oggi è sovraccarica perché indica almeno due cose distinte (il documento di input e l'unità di lavoro), e questa ambiguità viene risolta con due termini specifici:

- **AFU** (Analisi Funzionale Utente) per il **documento di input** ricevuto dal team funzionale
- **Piano** per l'**unità di lavoro** (cartella, workflow, identificatore, stato)

Inoltre la migrazione deve:
- Non rompere i profili esistenti che hanno già `.br-local.json` distribuito nelle repo dei progetti
- Mantenere i trigger naturali in italiano corporate (l'utente continua a dire "abbiamo un nuovo BR" in chat)
- Allineare anche la documentazione esterna alle skill

---

## 2. Decisioni di design

Frutto del brainstorming, fissate prima del plan:

| # | Decisione | Scelta |
|---|---|---|
| D1 | Significato di AFU | Documento di input (la specifica funzionale ricevuta dal team funzionale) |
| D2 | Sostituto per workflow/cartella/identificatore | `Piano` (italiano) |
| D3 | Rename file/path tecnici | Sì, tutto (`.br-local.json` → `.sdlc-local.json`, `<br-name>` → `<piano-name>`) |
| D4 | Nome file config nuovo | `.sdlc-local.json` (neutro, allineato al prefisso skill) |
| D5 | Backward compatibility profili esistenti | Lettura compatibile: priorità `.sdlc-local.json`, fallback `.br-local.json` |
| D6 | Trigger phrases | Multi-trigger: mantieni BR + aggiungi AFU/Piano (l'utente continua a dire "BR") |
| D7 | Scope esterno alle skill | Sì: SDLC_SKILLS_DOCUMENTATION.md + ~/.claude/CLAUDE.md + docs/ROADMAP_NEW_SKILLS.md. Presentazioni .pptx escluse (refactor manuale separato) |
| D8 | Regola di mapping compound terms | Contestuale: Review/Verifica/Documentazione/Concetto → AFU. Stima/Piano/Progresso/Bug/Cartella → Piano. Analista BR → Analista AFU |
| D9 | Strategia di rollout | Wave-based (4 wave) coerente con lo stile del refactor SDLC precedente |
| D10 | Migrazione automatica file config | Sì: quando `sdlc-profile-setup` trova `.br-local.json` legacy, lo migra a `.sdlc-local.json` lasciando `.br-local.json.bak` |

---

## 3. Mapping terminologico (la "verità unica")

### 3.1 — Regola contestuale BR → ?

| Pattern d'uso | Sostituzione | Esempio prima | Esempio dopo |
|---|---|---|---|
| Documento input | **AFU** | "il BR descrive" | "l'AFU descrive" |
| Documentazione input | **AFU** | "documentazione BR" | "documentazione AFU" |
| Verifica/review documento | **AFU** | "# Report Verifica BR" | "# Report Verifica AFU" |
| Concetti nel documento | **AFU** | "Concetto BR" (header tabella) | "Concetto AFU" |
| Disambiguazione esplicita | **AFU** | "BR (Business Requirement)" | "AFU (Analisi Funzionale Utente)" |
| Cartella di lavoro | **Piano** | "cartella BR", "cartella del BR" | "cartella del Piano" |
| Identificatore | **Piano** | "Nome BR", "BR di riferimento" | "Nome Piano", "Piano di riferimento" |
| Stato workflow | **Piano** | "BR passa a `done`", "BR attivi" | "Piano passa a `done`", "Piani attivi" |
| Stima | **Piano** | "# Stima BR" | "# Stima Piano" |
| Progresso | **Piano** | "# Progresso Implementazione [Nome BR]" | "# Progresso Implementazione [Nome Piano]" |
| Bug report | **Piano** | "# Bug Report — <nome BR>" | "# Bug Report — <nome Piano>" |
| Artefatti generati | **Piano** | "artefatti BR", "file BR" | "artefatti del Piano", "file del Piano" |
| Calibrazione storica | **Piano** | "K BR precedenti" | "K Piani precedenti" |
| Flusso/processo generale | **SDLC** | "flusso BR completo", "BR lifecycle suite" | "flusso SDLC completo", "SDLC lifecycle suite" |
| Agente analista | **AFU** | "Analista BR" (analizza il documento) | "Analista AFU" |

### 3.2 — Rename file/path tecnici

| Prima | Dopo |
|---|---|
| `.br-local.json` | `.sdlc-local.json` (con fallback compatibile) |
| `<br-name>` | `<piano-name>` |
| `feature/<br-name>-<slug>` (branch git) | `feature/<piano-name>-<slug>` |

### 3.3 — Trigger phrases (multi-trigger)

I trigger esistenti `BR` restano attivi come alias. Si aggiungono i nuovi trigger AFU/Piano. Esempi:

| Skill | Trigger originali (restano) | Trigger aggiunti |
|---|---|---|
| sdlc-analyzer | "abbiamo un nuovo br", "analizza il br" | "abbiamo una nuova afu", "nuovo Piano", "analizza l'AFU" |
| sdlc-reviewer | "rivedi il br", "controlla la documentazione" | "rivedi l'AFU", "verifica l'AFU" |
| sdlc-clarify | "chiarimenti ricevuti", "il funzionale ha risposto" | (invariati: già non parlano di BR direttamente) |
| sdlc-debug | "ci sono dei bug", "debug br" | "debug Piano", "bug su Piano" |
| sdlc-executor | "lavora il task", "esegui il piano" | "lavora il Piano" |
| sdlc-updater | "il br è stato aggiornato", "nuova versione del br" | "l'AFU è stata aggiornata", "nuova versione AFU" |
| sdlc-progress-report | "genera il report excel", "aggiorna l'excel" | (invariati: già non parlano di BR direttamente) |
| sdlc-estimator | "stima il br", "quanti sviluppatori servono" | "stima il Piano", "stima l'AFU" |
| sdlc-profile-setup | "crea profilo progetto", "setup profilo" | (invariati: già non parlano di BR direttamente) |

### 3.4 — Invarianti (cosa NON cambia)

- **Nomi delle skill**: restano `sdlc-*` (refactor del 2026-05-18 già completo)
- **Nomi dei file output**: `PLAN.md`, `TASKS.md`, `PROGRESS.md`, `BUG_REPORT.md`, `REVIEW.md`, `CLARIFY.md`, `ESTIMATE.md` (già semantici)
- **Path structure**: `$BASE_PATH/{todo,in-progress,done}/<data>_<nome>/`
- **Schema JSON** del file config: invariato, cambia solo il nome del file
- **`_const-template.json`** in sdlc-profile-setup: zero occorrenze BR
- **Presentazioni `.pptx`** nel progetto claude-flow: out of scope (refactor manuale separato)
- **Memorie storiche** in `~/.claude/projects/.../memory/`: invariate (testimonianza di stato precedente)
- **Spec docs in `docs/superpowers/specs/`**: invariati come fossili (consistente con D3 del refactor 2026-05-18)

---

## 4. Scope concreto (inventario file)

### 4.1 — File da modificare

| Categoria | File | Occorrenze `BR` | Occorrenze `br-local` | Note |
|---|---|---|---|---|
| Skill | `~/.claude/skills/sdlc-analyzer/SKILL.md` | 31 | 14 | Più impattata |
| Skill | `~/.claude/skills/sdlc-reviewer/SKILL.md` | 24 | 12 | |
| Skill | `~/.claude/skills/sdlc-debug/SKILL.md` | 18 | 9 | |
| Skill | `~/.claude/skills/sdlc-estimator/SKILL.md` | 18 | 14 | |
| Skill | `~/.claude/skills/sdlc-executor/SKILL.md` | 14 | 12 | |
| Skill | `~/.claude/skills/sdlc-updater/SKILL.md` | 8 | 12 | |
| Skill | `~/.claude/skills/sdlc-progress-report/SKILL.md` | 7 | 12 | |
| Skill | `~/.claude/skills/sdlc-clarify/SKILL.md` | 4 | 12 | |
| Skill | `~/.claude/skills/sdlc-profile-setup/SKILL.md` | 1 | 10 | È quella che SCRIVE il config |
| Doc skill | `~/.claude/skills/SDLC_SKILLS_DOCUMENTATION.md` | 36 | 15 | Documentazione consolidata |
| Rules | `~/.claude/CLAUDE.md` | 10 | n/a | 9 entry skill + trigger |
| Doc progetto | `docs/ROADMAP_NEW_SKILLS.md` | 18 | n/a | Vedi 4.2 |
| **TOTALE** | | **~189** | **~122** | |

### 4.2 — Nota su `docs/ROADMAP_NEW_SKILLS.md`

Il roadmap ha **due lavori sovrapposti**:
1. Aggiornare i nomi vecchi delle skill da `br-*` a `sdlc-*` (residuo non completato del refactor 2026-05-18). Es. riga 10: `BR arriva → br-reviewer → br-clarify → ...`
2. Applicare la migrazione terminologica BR → AFU/Piano di questo design

Entrambi vanno fatti nella Wave 4.

### 4.3 — File esclusi

- `_const-template.json` in sdlc-profile-setup (zero BR)
- Presentazioni `.pptx` (BR_Skills_Presentation.pptx, BR_Skills_Pipeline.pptx)
- Profili `examples/standalone-project/banca-agente/` (verificare in Wave 4; se contengono solo dati di esempio Solaria invariati al refactor, non si toccano)
- Memorie auto in `~/.claude/projects/.../memory/`
- Spec docs storici in `docs/superpowers/specs/` (incluso questo file, una volta committed: gli aggiornamenti futuri si fanno con nuovi spec)

---

## 5. Strategia di rollout (Wave-based, 4 commit)

### 5.1 — Wave 1: Lettura compatibile del file config (low-risk safety net)

**Obiettivo**: aggiungere il pattern di lookup compatibile in tutte le 9 skill che leggono `.br-local.json`. Preferisce `.sdlc-local.json`, fa fallback a `.br-local.json`. Zero impatto user-facing.

**Logica**:
1. Cerca `.sdlc-local.json` nella repo corrente (priorità)
2. Se non trovato, cerca `.br-local.json` (fallback)
3. Se trovato `.br-local.json`, emetti warning soft user-facing che indica la possibilità di rinominare al prossimo `/sdlc-profile-setup`
4. Se nessuno dei due → errore "Profilo non configurato"

**Cosa NON tocca Wave 1**:
- Zero modifiche al testo user-facing (BR resta dappertutto)
- Zero rename placeholder
- `sdlc-profile-setup` continua a scrivere `.br-local.json`

**Verifica**:
- [ ] Profilo solo `.br-local.json` → skill leggono correttamente
- [ ] Profilo solo `.sdlc-local.json` → skill leggono correttamente
- [ ] Profilo entrambi → skill leggono `.sdlc-local.json`
- [ ] Nessuno dei due → errore corretto

**Commit**:
```
feat(sdlc): wave 1 — lettura compatibile .sdlc-local.json con fallback .br-local.json
```

### 5.2 — Wave 2: Sostituzione testuale nelle 9 skill

**Obiettivo**: applicare il mapping contestuale BR→AFU/Piano + multi-trigger + rename `<br-name>` → `<piano-name>` in tutte le SKILL.md.

**Ordine di lavorazione** (dalle più piccole alle più grandi):
1. sdlc-profile-setup (1 BR)
2. sdlc-clarify (4 BR)
3. sdlc-progress-report (7 BR)
4. sdlc-updater (8 BR)
5. sdlc-executor (14 BR)
6. sdlc-debug (18 BR)
7. sdlc-estimator (18 BR)
8. sdlc-reviewer (24 BR)
9. sdlc-analyzer (31 BR)

**Ordine di sostituzione interno a ogni file** (per evitare collisioni):
1. Compound espliciti (`BR (Business Requirement)`, `BR lifecycle suite`, `flusso BR`)
2. Header dei file output (`# Report Verifica BR`, `# Stima BR`, ecc.)
3. Frasi contestuali documento input → AFU
4. Frasi contestuali workflow → Piano
5. Domande all'utente
6. Placeholder tecnici (`<br-name>` → `<piano-name>`)
7. Multi-trigger nel frontmatter `description:`

**Casi grammaticali italiani da verificare manualmente dopo le sostituzioni**:
- Articoli: `il BR` → `l'AFU` (non `il AFU`), `del BR` → `dell'AFU` (non `del AFU`)
- Plurali: `BR attivi` → `Piani attivi` (non `Piano attivi`)
- Concordanze genere: `il BR è ambiguo` → `l'AFU è ambigua`

**Verifica per ogni skill**:
- [ ] `grep -c "\bBR\b" <skill>/SKILL.md` = 0 occorrenze residue (eccetto trigger phrases multi-trigger nel frontmatter)
- [ ] `grep -c "\bbr-name\b" <skill>/SKILL.md` = 0
- [ ] Lettura review della skill per frasi sgrammaticate

**Commit**:
```
refactor(sdlc): wave 2 — sostituzione terminologica BR → AFU/Piano nelle 9 skill
```

### 5.3 — Wave 3: Scrittura del nuovo file config + migrazione legacy

**Obiettivo**: far sì che `sdlc-profile-setup` scriva `.sdlc-local.json` e migri automaticamente i profili `.br-local.json` legacy.

**Modifiche a `sdlc-profile-setup`**:
- Step 10 rinominato in "Aggiorna .sdlc-local.json"
- Tutti i template di scrittura puntano al nuovo nome
- Logica di gestione esistente:
  - `.sdlc-local.json` esiste → leggi, preserva, aggiungi/aggiorna i campi
  - solo `.br-local.json` esiste (legacy) → migrazione automatica: legge il contenuto, scrive in `.sdlc-local.json`, rinomina il vecchio in `.br-local.json.bak` (NON cancellato)
  - nessuno dei due → crea ex novo `.sdlc-local.json`
- Comunicazione user-facing chiara durante la migrazione

**Schema JSON invariato**: cambia solo il nome del file. Le altre skill (con lettura compatibile dal Wave 1) continuano a funzionare senza modifiche.

**Verifica**:
- [ ] Nuovo setup su repo vergine → genera `.sdlc-local.json`
- [ ] Setup su repo con solo `.br-local.json` → migra a `.sdlc-local.json` + crea `.br-local.json.bak`
- [ ] Setup su repo con solo `.sdlc-local.json` → aggiorna in place
- [ ] Setup su repo con entrambi → usa `.sdlc-local.json`, warning sul vecchio file

**Commit**:
```
feat(sdlc): wave 3 — sdlc-profile-setup scrive .sdlc-local.json + migra legacy
```

### 5.4 — Wave 4: Documentazione esterna

**Obiettivo**: allineare la documentazione esterna alle skill.

**File 1 — `SDLC_SKILLS_DOCUMENTATION.md`** (36 BR + 15 br-local):
- Sostituzioni testuali con lo stesso mapping della Wave 2
- Riferimenti a `.br-local.json` → `.sdlc-local.json` (con nota sul fallback)
- Esempi di trigger → versione multi-trigger
- Header del tipo "Il flusso BR" → "Il flusso SDLC"
- Aggiungere glossario o nota: AFU, Piano, profilo legacy

**File 2 — `~/.claude/CLAUDE.md`** (10 BR, 9 entry skill):
- Trigger phrases → multi-trigger per ognuna delle 9 entry
- Descrizioni testuali → mapping contestuale AFU/Piano
- Riferimenti `.br-local.json` → `.sdlc-local.json` con menzione fallback

**File 3 — `docs/ROADMAP_NEW_SKILLS.md`** (18 BR):
- **Doppio lavoro**: aggiornare nomi skill `br-*` → `sdlc-*` (residuo refactor 2026-05-18) + applicare mapping BR → AFU/Piano
- Esempio: `BR arriva → br-reviewer → br-clarify → ...` diventa `AFU arriva → sdlc-reviewer → sdlc-clarify → ...`

**Verifica**:
- [ ] `grep -c "\bBR\b" SDLC_SKILLS_DOCUMENTATION.md` = 0 (tranne trigger phrase examples)
- [ ] `grep -c "\bBR\b" ~/.claude/CLAUDE.md` = N (solo dove fa parte di multi-trigger)
- [ ] `grep -c "\bBR\b" docs/ROADMAP_NEW_SKILLS.md` = 0
- [ ] `grep -c "\bbr-" docs/ROADMAP_NEW_SKILLS.md` = 0 (i nomi skill devono essere `sdlc-*`)
- [ ] Rilettura visuale dei 3 file per controlli grammaticali italiani

**Commit**:
```
docs(sdlc): wave 4 — allineamento documentazione esterna a AFU/Piano
```

---

## 6. Backward compatibility e rollback

### 6.1 — Matrice di compatibilità sui profili esistenti

| Profilo esistente | Skill leggono | Wave 3 (setup) fa |
|---|---|---|
| Solo `.br-local.json` (legacy) | Fallback → letto | Migra a `.sdlc-local.json` + crea `.br-local.json.bak` |
| Solo `.sdlc-local.json` (nuovo) | Priorità → letto | Aggiorna in place |
| Entrambi presenti | Priorità → `.sdlc-local.json` | Usa `.sdlc-local.json`, warning |
| Nessuno | Errore "Profilo non configurato" | Crea ex novo `.sdlc-local.json` |

### 6.2 — Trigger phrases utente

| Frase utente | Comportamento dopo migrazione |
|---|---|
| "abbiamo un nuovo BR" | Funziona (multi-trigger) |
| "abbiamo una nuova AFU" | Funziona (nuovo trigger) |
| "rivedi il BR" | Funziona (multi-trigger) |
| "rivedi l'AFU" | Funziona (nuovo trigger) |
| "lavora il Piano" | Funziona (nuovo trigger) |
| "debug BR" | Funziona (multi-trigger) |

### 6.3 — Strategia di rollback

Ogni wave è un commit atomico:

| Scenario | Comando | Effetto |
|---|---|---|
| Rollback Wave 4 (docs sbagliate) | `git revert <wave4-sha>` | Docs tornano a stato precedente; skill restano migrate |
| Rollback Wave 3 (problema migrazione setup) | `git revert <wave3-sha>` | sdlc-profile-setup torna a scrivere `.br-local.json`; lettura compatibile resta attiva |
| Rollback Wave 2 (regressione testuale) | `git revert <wave2-sha>` | Testo torna a "BR"; lettura compatibile resta attiva |
| Rollback completo | `git revert <wave4..wave1-sha>` in ordine inverso | Ritorno allo stato pre-migrazione |

Per gli utenti finali: **nessuna azione richiesta** in nessuno scenario di rollback. La lettura compatibile (Wave 1) garantisce che entrambi i nomi di file restino accettati.

---

## 7. Checklist E2E (al termine delle 4 wave)

### 7.1 — Per ogni skill

- [ ] `grep -c "\bBR\b" <skill>/SKILL.md` ∈ {0, N} dove N è solo nei trigger phrases multi-trigger del frontmatter
- [ ] `grep -c "\bbr-name\b" <skill>/SKILL.md` = 0
- [ ] `grep -c "\.br-local\.json\b" <skill>/SKILL.md` ∈ {0, 1} (al massimo 1 nella sezione fallback Wave 1)
- [ ] La skill ha sezione "Lettura compatibile" / "Profilo legacy" documentata

### 7.2 — Documentazione esterna

- [ ] `SDLC_SKILLS_DOCUMENTATION.md`: zero BR fuori dai trigger esempi; menzione fallback compatibile
- [ ] `~/.claude/CLAUDE.md`: trigger multi-versione per tutte e 9 le skill
- [ ] `docs/ROADMAP_NEW_SKILLS.md`: zero BR e zero `br-*` (nomi skill aggiornati)

### 7.3 — Test funzionali

- [ ] Su un profilo Solaria/banca-agente con `.br-local.json` esistente, simulare `/sdlc-analyzer` e verificare lettura corretta
- [ ] Su una repo vergine, simulare `/sdlc-profile-setup` e verificare creazione `.sdlc-local.json`
- [ ] Verificare che `"abbiamo un nuovo br"` attivi ancora `/sdlc-analyzer`
- [ ] Verificare che `"abbiamo una nuova afu"` attivi anch'esso `/sdlc-analyzer`

### 7.4 — Aggiornamento memory

Al termine, aggiungere o aggiornare la memory file `sdlc-refactor-complete.md` con:
- Vocabolario finale: AFU (documento) + Piano (workflow) + SDLC (processo)
- Multi-trigger attivo (BR continua a funzionare come alias)
- File config `.sdlc-local.json` con fallback `.br-local.json`

---

## 8. Order of execution

```
Wave 1 (lettura compatibile) → commit → smoke test profili esistenti
   ↓
Wave 2 (sostituzione testuale, 9 skill) → commit unico per wave
   ↓
Wave 3 (sdlc-profile-setup + migrazione legacy) → commit → test setup vergine + setup legacy
   ↓
Wave 4 (docs esterne, incluso doppio lavoro su ROADMAP) → commit
   ↓
Checklist E2E finale + aggiornamento memory file
```

In totale: **4 commit** in branch corrente (`main`), nessun branch separato richiesto perché ogni wave è retro-compatibile.
