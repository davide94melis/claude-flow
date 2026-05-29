---
name: sdlc-updater
description: Aggiorna gap report e piano di implementazione quando il BR o la documentazione viene modificata. Confronta la nuova documentazione con quella precedente, identifica i delta, e aggiorna report e piano preservando il progresso delle task già completate o in corso. Supporta qualsiasi composizione di repository — le sigle e i nomi vengono letti dinamicamente dai file esistenti. Usa questa skill quando l'utente dice "il br è stato aggiornato", "nuova versione del br", "aggiorna il piano", "documentazione aggiornata", "c'è un aggiornamento al br", "mockup aggiornati", "nuova versione documentazione", o qualsiasi variazione che implichi una modifica alla documentazione di un BR / AFU / Piano già analizzato.
---

# SDLC Updater — Aggiornamento PLAN e TASKS su Documentazione Modificata

Questa skill è il terzo tassello del flusso SDLC, dopo `sdlc-analyzer` (analisi iniziale) e `sdlc-executor` (esecuzione task). Si attiva quando la documentazione dell'AFU viene aggiornata e bisogna propagare le modifiche al PLAN e al TASKS, senza perdere il lavoro già fatto.

Il principio guida: **mai sovrascrivere il progresso**. Le task completate restano completate, quelle in corso restano in corso. Solo i gap nuovi o modificati generano aggiornamenti al piano.

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

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 0 — Detection delta AFU via manifest (SOLO in standalone)

In modalita' standalone, prima di chiedere documentazione nuova al funzionale, prova ad auto-rilevare se Solaria ha gia' committato un AFU v2 in `plans/in-progress/`:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls "$BASE_PATH/in-progress"/*/afu-manifest.json 2>/dev/null
```

Per ogni manifest trovato, leggi `versione` e confrontalo con l'header `Processed AFU version` del PLAN.md corrispondente:

```bash
# Pseudocodice
manifest_version = $(jq -r '.versione' "<plan>/afu-manifest.json")
plan_processed = $(grep -oP '^Processed AFU version:\s*`?\K[^`\n]+' "<plan>/PLAN.md")
```

**Casi**:

| Caso | Azione |
|---|---|
| `manifest.versione > plan.processed_afu_version` | Solaria ha consegnato v2 (Fase 2b mid-flight). Mostra `manifest.changelog` all'utente come **fonte primaria** del delta. Procedi con la pipeline (Fase 2-3) usando il changelog testuale per guidare l'analisi, anziche' chiedere quali documenti sono cambiati. |
| `manifest.versione == plan.processed_afu_version` | Niente da aggiornare via Solaria. Chiedi: "Manifest version invariata. Stai aggiornando manualmente?" e procedi con la pipeline standard (Domanda 2). |
| `manifest.gate_outcome != "GO"` | Warning: "Solaria sta ancora iterando AFU v<n> (gate=<x>). Procedi solo se intenzionale o stai facendo un dry-run sulle modifiche in corso." |
| `manifest.tests.playbook_md` (o `_xlsx`) cambiato vs versione precedente | Segnala "Il playbook test e' stato rigenerato per v2 — comunica al team funzionale di usare la nuova versione in Fase 2c ondata (b)." |

In **modalita' legacy**, salta questa domanda e procedi con la Domanda 1 standard.

### Domanda 1 — File esistenti

Cerca automaticamente cartelle dei Piani nella struttura `plans/`:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/in-progress"/*/ "$BASE_PATH/todo"/*/ 2>/dev/null
```

**Se trovi cartelle dei Piani**, elencale con il loro contenuto:

> Ho trovato questa cartella del Piano:
> - `$BASE_PATH/in-progress/2026-04-28_booking-v2/`
>   - `PLAN.md`
>   - `TASKS.md`
>   - `PROGRESS.md`
>   - `CLARIFY.md`
>
> Uso questa come base? Oppure dammi i path manualmente.

**Se non trovi nulla**, chiedi:

> Dammi i path dei file da aggiornare:
> 1. **PLAN** esistente
> 2. **TASKS** esistente
> 3. **File di Progresso** (se esiste)

Leggi tutti i file. Estrai lo stato attuale completo: task, progresso, codebase, documentazione originale.

### Domanda 2 — Documentazione aggiornata

> Quali documenti sono stati aggiornati? Dammi i path dei file nuovi/modificati.
> Per ognuno, dimmi se:
> - **Sostituisce** un documento esistente (nuova versione dello stesso file)
> - **È un documento nuovo** che si aggiunge ai precedenti
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Repository

> Le repository coinvolte o i loro path sono cambiati rispetto all'analisi precedente?
> - Se **no**, uso quelli già nel report.
> - Se **sì**, dimmi le modifiche (path cambiati, repo aggiunte, repo rimosse).
> - Se ci sono **nuove repository** non presenti nel report precedente, dammi: nome, sigla e path.

### Domanda 4 — Team

> Il team è cambiato rispetto al piano attuale?
> - Se **no**, mantengo la composizione attuale.
> - Se **sì**, dimmi le modifiche (sviluppatori aggiunti, rimossi, ruoli cambiati).

### Riepilogo e conferma

> Riepilogo aggiornamento:
> - Report base: [path]
> - Piano base: [path]
> - Progresso: [path o "non presente"]
> - Documenti aggiornati: [lista]
> - Repository: [invariate / aggiornate — dettaglio modifiche]
> - Team: [invariato / modifiche]
>
> Procedo con l'analisi dei delta?

---

## Fase 2 — Conversione e Analisi Delta Documentazione

### 2.1 — Conversione documenti aggiornati

Converti i nuovi documenti in MD (stessa procedura di `sdlc-analyzer`):

- DOCX/DOC → `~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py`
- PDF/PPTX/XLSX → `markitdown`
- MD → copia diretta
- Immagini → Read diretto

Salva nella cartella `requirements/` dentro la cartella del Piano (es. `$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/requirements/`), sovrascrivendo i file precedenti dove applicabile.

### 2.2 — Identificazione delta

Confronta la documentazione aggiornata con quella referenziata nel report esistente. Identifica:

**Requisiti nuovi** — presenti nella nuova documentazione ma assenti dal report attuale.

**Requisiti modificati** — presenti in entrambi ma con differenze (campo, logica, UI, vincoli).

**Requisiti rimossi** — presenti nel report attuale ma assenti dalla nuova documentazione.

**Requisiti invariati** — identici tra vecchia e nuova documentazione.

Per ogni delta, documenta:
- **Tipo**: NUOVO / MODIFICATO / RIMOSSO
- **Funzionalità** di riferimento
- **Cosa cambia** (descrizione precisa)
- **Riferimento** al documento aggiornato (sezione/pagina)
- **Impatto** sulle task esistenti nel piano

### 2.3 — Verifica delta contro il codice

Per ogni requisito nuovo o modificato, verifica lo stato nel codice attuale (come nella Fase 3 di `sdlc-analyzer`):
- Esiste già? Parzialmente? Per niente?
- Genera la classificazione gap: Coperto / Parziale / Mancante / Discrepanza / Da chiarire

Per i requisiti rimossi, verifica se il codice corrispondente era già stato implementato (task completate nel progresso).

---

## Fase 3 — Aggiornamento Report

### Comunicazione delta all'utente

Prima di modificare qualsiasi file, presenta il riepilogo dei delta:

> ## Delta identificati
>
> **Requisiti nuovi**: N
> - [lista con breve descrizione]
>
> **Requisiti modificati**: N
> - [lista con cosa cambia]
>
> **Requisiti rimossi**: N
> - [lista — ATTENZIONE: se task già completate sono legate a requisiti rimossi, segnalalo]
>
> **Impatto sul piano**:
> - Task da aggiungere: N
> - Task da modificare: N
> - Task da rimuovere/annullare: N
> - Task invariate: N
>
> Procedo con l'aggiornamento?

Aspetta conferma.

### 3.1 — Aggiornamento PLAN

Aggiorna il file PLAN esistente (non crearne uno nuovo):

1. **Aggiorna l'header** — data aggiornamento, lista documenti aggiornata. **In modalita' standalone**: aggiorna anche `Processed AFU version: <nuova manifest.versione>` (es. `1.0` → `2.0`). Se il manifest aggiorna anche `tests.playbook_md/xlsx`, riallinea le righe `Test playbook:` nell'header.
2. **Aggiungi una sezione "Storico aggiornamenti"** in fondo al report:

```
## Storico Aggiornamenti

### Aggiornamento <data> — AFU v<versione precedente> -> v<nuova versione>
- Documenti aggiornati: [lista]
- Requisiti nuovi: N
- Requisiti modificati: N
- Requisiti rimossi: N
- Motivazione: [breve descrizione]
- [SOLO standalone] Changelog manifest (Solaria, fonte primaria del delta):
  > <testo da manifest.changelog>
- [SOLO standalone] Playbook test rigenerato: [si/no]
```

In **modalita' standalone**, il `changelog` del manifest e' la fonte primaria del delta (Solaria l'ha redatto durante l'authoring v2 in Fase 2b). La detection automatica file-by-file resta utile come sanity check ma il narrativo del changelog ha priorita' nelle voci dello storico.

3. **Aggiorna la matrice di verifica**:
   - Aggiungi righe per i requisiti nuovi
   - Aggiorna lo stato per i requisiti modificati
   - Segna come `RIMOSSO` (non cancellare) i requisiti eliminati, con nota sulla data di rimozione
4. **Aggiorna "Gap aperti reali"** — aggiungi i nuovi gap, aggiorna quelli modificati, segna come risolti quelli rimossi
5. **Aggiorna "Esito sintetico"** e "Conclusione finale"

### 3.2 — Aggiornamento TASKS

Aggiorna il TASKS preservando il progresso.

**Pre-step: colonna Branch** — Se il backlog operativo del piano NON ha una colonna **Branch**, aggiungila PRIMA di qualsiasi altra modifica. Per ogni task esistente, genera il nome branch seguendo il pattern `feature/<piano-name>-<slug-attivita>` (dove `<piano-name>` e' il nome del Piano e `<slug>` e' derivato dal nome dell'attivita'). Per le merge task (T-MERGE-*), il valore e' `—`. Comunica all'utente:

> Il piano non aveva la colonna Branch. L'ho aggiunta con i nomi branch generati per ogni task.
> Verifica che i nomi siano corretti — se qualche task e' gia' stata lavorata su un branch diverso, aggiorna il nome.

**Task invariate** — non toccarle, mantieni ID, owner, descrizione, effort, branch.

**Task da modificare** (requisito cambiato):
- Aggiorna la descrizione con i nuovi requisiti
- Se la task è "Da iniziare": aggiorna liberamente
- Se la task è "In corso": aggiungi una nota `[AGGIORNATO <data>]: [cosa è cambiato]` in cima alla descrizione, senza cancellare il lavoro già fatto
- Se la task è "Completata": crea una nuova task di adeguamento (es. `T-001-fix`) collegata alla originale

**Task nuove** (requisito nuovo):
- Assegna un nuovo ID sequenziale che continua dalla numerazione esistente
- Assegna lo **stream** appropriato: usa uno stream esistente se la task appartiene alla stessa area funzionale, oppure crea un nuovo stream se rappresenta una funzionalità nuova
- Assegna un nome **Branch** seguendo lo stesso pattern del piano (`feature/<piano-name>-<slug-attivita>`)
- Assegnale al developer più adatto in base a ruolo, seniority e carico attuale (dal progresso)
- Inseriscile nella wave appropriata rispettando le dipendenze
- Se il team è cambiato, ridistribuisci considerando i nuovi membri

**Task da rimuovere** (requisito rimosso):
- Se "Da iniziare": segna come `ANNULLATA` nel piano con motivazione, non cancellarla
- Se "In corso": avvisa lo sviluppatore, segna come `SOSPESA` con motivazione
- Se "Completata": lasciala nello stato attuale, aggiungi nota `[REQUISITO RIMOSSO <data>]`

**Aggiorna le sezioni del piano**:
- Backlog operativo — aggiungi/modifica/annulla task
- Ordine di esecuzione — ricalcola le wave
- Piano per persona — ribilancia i carichi
- Stima complessiva — aggiorna effort e timeline
- Rischi — aggiungi rischi derivanti dai cambiamenti
- Aggiungi una sezione "Storico Aggiornamenti" analoga a quella del report

### 3.3 — Aggiornamento File di Progresso

Se il file di progresso esiste, aggiornalo:
- Aggiungi le task nuove con stato "Da iniziare" e progresso 0%
- Segna le task annullate con stato "Annullata"
- Segna le task sospese con stato "Sospesa"
- Aggiorna il riepilogo (totali, percentuali)
- Aggiungi voce al log attività: `[data] — Aggiornamento piano da nuova documentazione AFU: N task aggiunte, M modificate, K annullate`

### 3.4 — Commit e push aggiornamenti

Dopo aver aggiornato report, piano e progresso, committa e pusha le modifiche nella repo `deloitte-profiles`:

```bash
git -C "$GIT_REPO_PATH" add "<profilo>/plans/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-updater] <nome>: aggiornato piano da nuova documentazione"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Fase 4 — Riepilogo Finale

Al termine, presenta un riepilogo completo:

> ## Aggiornamento completato
>
> **File aggiornati**:
> - [path report] — aggiornato
> - [path piano] — aggiornato
> - [path progresso] — aggiornato (se presente)
>
> **Impatto**:
> - Task aggiunte: [lista con ID e owner]
> - Task modificate: [lista con ID e cosa è cambiato]
> - Task annullate/sospese: [lista con ID e motivazione]
> - Task invariate: N
>
> **Attenzione**:
> - [eventuali task in corso impattate — lo sviluppatore deve essere avvisato]
> - [eventuali task completate il cui requisito è stato rimosso]
> - [rischi nuovi]

---

## Regole Fondamentali

1. **Mai sovrascrivere il progresso** — le task completate restano nel loro stato, quelle in corso restano in corso
2. **Mai cancellare** — i requisiti rimossi vengono segnati come RIMOSSO/ANNULLATA, non eliminati, per preservare la tracciabilità
3. **Sempre chiedere conferma** — prima di applicare qualsiasi modifica, mostra il delta e aspetta conferma
4. **Nuove task con ID sequenziali** — continua la numerazione esistente, non riusare ID di task annullate
5. **Segnalare sempre i conflitti** — se una modifica impatta task in corso o completate, avvisa esplicitamente
