---
name: sdlc-progress-report
description: Genera o aggiorna un file Excel con il riepilogo completo delle task, progressi e avanzamenti per sviluppatore a partire dal piano e dal file di progresso di sdlc-analyzer/sdlc-executor. Supporta qualsiasi composizione di repository — i nomi e le sigle vengono letti dinamicamente dal piano. Usa questa skill quando l'utente dice "genera il report excel", "aggiorna l'excel", "stato avanzamento excel", "esporta il progresso", "report avanzamento", "excel dei progressi", "aggiorna il foglio", "com'è la situazione delle task", o qualsiasi variazione che implichi la necessità di un report Excel sullo stato di avanzamento delle task di un piano (BR / AFU / Piano).
---

# SDLC Progress Report — Export Excel Avanzamento Task

Questa skill genera o aggiorna un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo, a partire dal piano e dal file di progresso generati da `sdlc-analyzer` / `sdlc-executor`.

---

## Risoluzione Path (modalita' duale: standalone | legacy)

Tutte le operazioni su file plan avvengono nella **project_repo** (modalita' standalone, una repo per progetto) o nella repo `deloitte-profiles` (modalita' legacy), **non** nella repo del codice applicativo. Il codice del progetto continua a essere scritto nelle repo del progetto.

### Lettura del file di configurazione locale (`.sdlc-local.json` con fallback `.br-local.json`)

**Lettura compatibile**: il file di configurazione locale può chiamarsi `.sdlc-local.json` (nuovo nome, raccomandato) oppure `.br-local.json` (nome legacy, ancora supportato). Cerca PRIMA `.sdlc-local.json`; se non esiste, fa fallback a `.br-local.json`. Se nessuno dei due esiste, ferma e chiedi all'utente di eseguire `/sdlc-profile-setup`.

Se trovi solo `.br-local.json` (profilo legacy), emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

I comandi `bash` seguenti sono scritti referenziando `.br-local.json` per chiarezza storica — applica equivalentemente la stessa logica al file effettivamente trovato (sia `.sdlc-local.json` che `.br-local.json`).

All'avvio, leggi il file (priorità `.sdlc-local.json`, fallback `.br-local.json`) dalla root della repo corrente:

```bash
# Esempio con .br-local.json — equivalente per .sdlc-local.json
cat .br-local.json 2>/dev/null
```

La presenza del campo `project_repo` o `profiles_repo` discrimina la modalita':

```bash
if grep -q '"project_repo"' .br-local.json 2>/dev/null; then
  MODE="standalone"
  PROJECT_REPO=$(grep -oP '"project_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROJECT_NAME=$(grep -oP '"project_name"\s*:\s*"\K[^"]+' .br-local.json)
  BASE_PATH="$PROJECT_REPO/plans"
  CONST_PATH="$PROJECT_REPO/constitution"
  DATASET_PATH="$PROJECT_REPO/dataset"        # solo standalone (popolato da Solaria-side)
  GIT_REPO_PATH="$PROJECT_REPO"
elif grep -q '"profiles_repo"' .br-local.json 2>/dev/null; then
  MODE="legacy"
  PROFILES_REPO=$(grep -oP '"profiles_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROFILO=$(grep -oP '"profilo"\s*:\s*"\K[^"]+' .br-local.json)
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

### Se né `.sdlc-local.json` né `.br-local.json` esistono

Ferma l'esecuzione e avvisa:

> Nessun file di configurazione locale trovato (`.sdlc-local.json` né `.br-local.json` legacy). Devi prima eseguire `/sdlc-profile-setup`, che ti chiedera' se vuoi configurare in **modalita' standalone** (raccomandato per nuovi progetti, una repo per progetto con cartella `dataset/` Solaria-side) o **modalita' legacy** (progetti gia' esistenti in `deloitte-profiles`).

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
| Né `.sdlc-local.json` né `.br-local.json` (legacy) presenti | "Esegui prima `/sdlc-profile-setup` scegliendo modalita' standalone o legacy" | Stop |
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

---

## Modalità di orchestrazione

Ogni skill SDLC può girare in due modalità:

- **`classic`** (default) — esecuzione sequenziale, leggera, pochi token. È il comportamento storico.
- **`deep`** — orchestrazione parallela multi-agent (Workflow tool) + verifica adversariale: più lenta e costosa, ma più esaustiva.

> **Mai escalation silenziosa.** Non si passa a `deep` (con la relativa spesa) senza una scelta esplicita — flag persistente o conferma dell'utente. Default globale = `classic`.

### Risoluzione della modalità (cascata, in ordine di precedenza)

1. **Flag persistente** in `.sdlc-local.json` (fallback `.br-local.json`) — la sorgente automatica a precedenza più alta. Campi *flat* (grep-compatibili, niente `jq`):

   ```bash
   LOCAL_CFG=".sdlc-local.json"; [ -f "$LOCAL_CFG" ] || LOCAL_CFG=".br-local.json"
   ORCH_MODE=$(grep -oP '"orchestration_mode"\s*:\s*"\K[^"]+' "$LOCAL_CFG" 2>/dev/null);  ORCH_MODE=${ORCH_MODE:-classic}
   ORCH_DEPTH=$(grep -oP '"orchestration_depth"\s*:\s*"\K[^"]+' "$LOCAL_CFG" 2>/dev/null); ORCH_DEPTH=${ORCH_DEPTH:-standard}
   ORCH_MAXC=$(grep -oP '"orchestration_max_concurrency"\s*:\s*\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_MAXC=${ORCH_MAXC:-10}
   ORCH_PANEL=$(grep -oP '"orchestration_verifier_panel"\s*:\s*\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_PANEL=${ORCH_PANEL:-3}
   ```

2. **Keyword nel trigger** ("a fondo", "esaustivo", "in parallelo", "ultracode") — override per singola invocazione, ma **declassata sotto il flag**: una scelta `classic` deliberata nel flag NON viene scavalcata da una keyword ambigua. Ogni escalation verso `deep` innescata da keyword **passa da conferma esplicita** (AskUserQuestion) prima di spendere.

3. **AskUserQuestion** quando né flag né keyword hanno deciso. Con **auto-suggeritore**: se la dimensione del lavoro supera una soglia (≥3 repo, ≥25 task, ondata ≥8 bug, changelog AFU ampio) proponi `deep` mostrando il razionale, **ma la pre-selezione resta `classic`** (no spesa a sorpresa).

**`/effort ultracode` di sessione**: se attivo a livello sessione, la **prima** skill SDLC invocata chiede **una volta** se applicare `deep` a tutte le skill SDLC della sessione, poi ricorda la risposta.

### Banner di modalità (sempre a video prima del lavoro pesante)

- `deep`:  *"Eseguo in modalità Workflow+approfondita: ~N agent, più lento/costoso."*
- `classic`: *"Modalità classica (sequenziale)."*

### Esecuzione `deep` — invocazione del Workflow tool

In `deep`, la skill **istruisce Claude a invocare il Workflow tool**: con lo script dedicato in `workflows/` per le skill *heavy* (`sdlc-analyzer`, `sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-reviewer` — vero fan-out + `adversarial-verify` + `completeness-critic` + `isolation:'worktree'`), oppure con un singolo sub-step di `completeness/coherence-critic` per le skill *light* (`sdlc-estimator`, `sdlc-clarify`, `sdlc-progress-report`, `sdlc-profile-setup`). Gli schema JSON vivono **negli script `workflows/*.js`**, non qui.

### Capability check + degradazione (assume-disponibile + fallback esplicito)

**Nessun probe preventivo**: procedi assumendo il Workflow tool presente. Se l'invocazione **non è possibile** (tool assente) **oppure fallisce/non completa**:

1. banner a video: *"Workflow tool non disponibile: eseguo in modalità classica sequenziale."*;
2. prosegui nel ramo `classic` usando la mappa di fallback sotto;
3. inserisci in testa all'artefatto prodotto (PLAN/CLARIFY/gap report/...) il banner **"COPERTURA RIDOTTA — prodotto senza completeness-critic/adversarial-verify"**. La degradazione è **rumorosa**, mai silenziosa: gli artefatti `classic` e `deep` NON sono equivalenti.

> Due casi distinti: (a) **Workflow tool assente / non parte** → fallback completo a `classic` (sopra). (b) **Barriera parziale** (il workflow parte ma k/N agent falliscono) → lo script ritorna i k riusciti come *proposte non applicate*; i file source-of-truth NON vengono scritti parzialmente; l'agente principale presenta lo stato e l'utente decide.

### Mappa di fallback `deep` → `classic`

| Primitiva `deep` | Fallback `classic` |
|---|---|
| `parallel` / `pipeline` | loop sequenziale sugli stessi thunk (comportamento attuale) |
| `agent({agentType, schema})` | "leggi `~/.claude/agents/<agentType>.md` e lancia un Task" + parsing MD |
| `adversarial-verify` / `judge-panel` | singola verifica `sdlc-verifier` inline |
| `completeness-critic` | checklist manuale già presente nella skill |
| `loop-until-dry` | ciclo fix/riverifica già descritto |

### Invarianti inviolabili (in ENTRAMBE le modalità)

1. Tutti i gate di conferma utente ("mai procedere senza conferma").
2. Mai auto-commit sulle repo di **codice**.
3. Il sottoagente implementa, l'agente principale coordina.
4. Scritture sui file source-of-truth (PROGRESS, BUG_REPORT, CLARIFY, PLAN/TASKS) sempre **single-writer serializzato** (pull→edit→commit→push).
5. Gli agent di verifica/esplorazione restano **read-only**.
6. Barriere obbligatorie dove la fase a valle richiede lo stato completo (prima della gap-synthesis, tra wave, prima della presentazione unica dell'auto-detect).

---

## Fase 1 — Individuazione File Sorgente

### Ricerca automatica

Cerca cartelle dei Piani nella struttura `plans/` centralizzata in `deloitte-profiles`, in ordine di priorita':

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/in-progress"/*/ "$BASE_PATH/todo"/*/ "$BASE_PATH/done"/*/ 2>/dev/null
```

Serve trovare:
- **TASKS** (`TASKS.md`) — obbligatorio
- **File di Progresso** (`PROGRESS.md`) — opzionale, se non esiste le task partono tutte da 0%
- **PLAN** (`PLAN.md`) — opzionale, usato per arricchire le descrizioni

**Se trovi cartelle dei Piani**, proponile:

> Ho trovato:
> - `$BASE_PATH/in-progress/2026-04-28_booking-v2/`
>   - `TASKS.md`
>   - `PROGRESS.md`
>
> Uso questa cartella per generare l'Excel?

Se non trovi nulla, chiedi i path manualmente.

### Verifica Excel esistente

Cerca nella stessa cartella del Piano se esiste gia' un file Excel:

```bash
ls "$BASE_PATH/in-progress"/*/PROGRESS.xlsx "$BASE_PATH/todo"/*/PROGRESS.xlsx "$BASE_PATH/done"/*/PROGRESS.xlsx 2>/dev/null
```

- **Se esiste** → modalità aggiornamento (solo i dati cambiano, struttura preservata)
- **Se non esiste** → modalità creazione da zero

Comunica la modalità all'utente:

> [Excel trovato — aggiorno `PROGRESS.xlsx` con i progressi attuali.]

oppure

> [Nessun Excel trovato — ne creo uno nuovo.]

---

## Fase 2 — Estrazione Dati

### Lettura progresso

Sincronizza la repo profili prima di leggere:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
```

Leggi il PROGRESS.md dalla cartella del Piano in `$BASE_PATH/<stato>/<data>_<nome>/PROGRESS.md`. Il file e' sempre aggiornato dopo il pull perche' tutti gli sviluppatori scrivono nella repo centralizzata.

### Estrazione campi

Dal PROGRESS.md e dal piano, estrai per ogni task:

| Campo | Fonte |
|---|---|
| ID | Piano — colonna ID |
| Attivita' | Piano — colonna Attivita' |
| Descrizione | Piano — colonna Descrizione (testo completo) |
| Owner | Piano — colonna Owner |
| Area | Piano — colonna Area (BE/FE) |
| Priorita' | Piano — colonna Priorita' (P0/P1/P2) |
| Wave | Piano — sezione Ordine di esecuzione |
| Dipendenze | Piano — colonna Dipendenze |
| Effort stimato | Piano — colonna Effort |
| Branch | PROGRESS.md — colonna Branch |
| Progresso % | PROGRESS.md — colonna Progresso |
| Stato | PROGRESS.md — colonna Stato (Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa) |
| Note | PROGRESS.md — colonna Note |

Se il file di progresso non esiste, imposta progresso a 0% e stato a "Da iniziare" per tutte le task.

---

## Fase 3 — Generazione / Aggiornamento Excel

Usa Python con `openpyxl` per generare il file. L'Excel deve contenere 3 fogli:

### Foglio 1 — "Task"

Tabella principale con tutte le task:

| Colonna | Larghezza | Contenuto |
|---|---|---|
| A — ID | 10 | ID task (es. T-001) |
| B — Stream | 18 | Stream funzionale (es. stream-booking) |
| C — Attività | 30 | Nome della task |
| D — Descrizione | 60 | Descrizione completa dal piano |
| E — Owner | 18 | Sviluppatore assegnato |
| F — Area | 8 | Sigla/e delle repo coinvolte (es. BE, FE, BE+FE, GW, ecc.) |
| G — Priorità | 10 | P0 / P1 / P2 |
| H — Wave | 10 | Wave 0 / 1 / 2 / ... |
| I — Dipendenze | 15 | ID task dipendenze |
| J — Effort | 10 | Giorni stimati |
| K — Branch | 25 | Nome branch |
| L — Progresso | 12 | Percentuale (0-100%) |
| M — Stato | 15 | Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa |
| N — Note | 40 | Note dal progresso |

Formattazione:
- Header in grassetto con sfondo grigio scuro e testo bianco
- Colonna K (Progresso) con formattazione condizionale:
  - 0% → sfondo rosso chiaro
  - 1-49% → sfondo arancione chiaro
  - 50-99% → sfondo giallo chiaro
  - 100% → sfondo verde chiaro
- Colonna L (Stato) con formattazione condizionale:
  - "Completata" → testo verde scuro, sfondo verde chiaro
  - "In corso" → testo blu scuro, sfondo blu chiaro
  - "Bloccata" → testo rosso scuro, sfondo rosso chiaro
  - "Annullata" / "Sospesa" → testo grigio, sfondo grigio chiaro
  - "Da iniziare" → nessuna formattazione speciale
- Filtri attivi su tutte le colonne
- Righe alternate con sfondo leggermente diverso per leggibilità
- Testo della colonna Descrizione con "wrap text" attivo

### Foglio 2 — "Per Sviluppatore"

Riepilogo per ogni sviluppatore:

| Colonna | Contenuto |
|---|---|
| A — Sviluppatore | Nome/ID |
| B — Ruolo | Area/sigle repo (come definite nel piano) |
| C — Seniority | Junior / Mid / Senior |
| D — Task totali | Conteggio |
| E — Completate | Conteggio |
| F — In corso | Conteggio |
| G — Da iniziare | Conteggio |
| H — Bloccate | Conteggio |
| I — Progresso medio | Media % delle sue task |
| J — Effort totale | Somma giorni stimati |
| K — Effort completato | Somma giorni delle task completate |

Stessa formattazione header del Foglio 1.
In fondo alla tabella, una riga "TOTALE" con le somme.

### Foglio 3 — "Riepilogo"

Dashboard complessiva con le metriche chiave:

```
Progetto: [nome Piano]
Data generazione: [data]
Ultimo aggiornamento progresso: [data dal file progresso]

STATO COMPLESSIVO
─────────────────
Task totali:        N
Completate:         N  (xx%)
In corso:           N  (xx%)
Da iniziare:        N  (xx%)
Bloccate:           N  (xx%)
Annullate/Sospese:  N  (xx%)

Progresso complessivo: xx%

EFFORT
──────
Effort totale stimato:    N gg/uomo
Effort completato:        N gg/uomo  (xx%)
Effort rimanente:         N gg/uomo

PER WAVE
────────
Wave 0: xx% completata (N/M task)
Wave 1: xx% completata (N/M task)
Wave 2: xx% completata (N/M task)
...
```

Formatta questa sezione come testo leggibile, non come tabella. Usa merge di celle per i titoli.

---

## Fase 4 — Salvataggio e Comunicazione

### Nome e posizione file

Salva nella stessa cartella del Piano all'interno della repo centralizzata:
- **Path**: `$BASE_PATH/<stato>/<YYYY-MM-DD>_<nome>/PROGRESS.xlsx`
- **Aggiornamento**: sovrascrivi il file esistente

### Modalità aggiornamento

Se il file esiste già, non ricrearlo da zero. Aggiorna solo:
- I valori di progresso e stato (dal file di progresso aggiornato)
- Eventuali task nuove (aggiunte da `sdlc-updater`)
- Eventuali task annullate/sospese
- Il foglio "Per Sviluppatore" e "Riepilogo" ricalcolati
- Preserva eventuali note manuali aggiunte dall'utente nelle celle Note

### Script Python

Genera ed esegui uno script Python con `openpyxl`. Se `openpyxl` non è installato:

```bash
pip install openpyxl
```

Lo script deve:
1. Parsare il piano MD per estrarre le task
2. Parsare il progresso MD per estrarre stati e percentuali
3. Se l'Excel esiste, leggerlo e preservare le note manuali
4. Generare/aggiornare i 3 fogli
5. Applicare formattazione e formattazione condizionale
6. Salvare il file

### Commit e push su deloitte-profiles

Dopo aver salvato l'Excel, fai commit e push nella repo centralizzata:

```bash
git -C "$GIT_REPO_PATH" add "<profilo>/plans/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-progress-report] <nome>: aggiornato Excel avanzamento"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

### Comunicazione finale

> Excel [creato / aggiornato]: `$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.xlsx`
>
> Riepilogo:
> - Task totali: N (X completate, Y in corso, Z da iniziare)
> - Progresso complessivo: xx%
> - [eventuali task bloccate da segnalare]

---

## Dipendenze

- **`openpyxl`** — libreria Python per generazione Excel (`pip install openpyxl`)
