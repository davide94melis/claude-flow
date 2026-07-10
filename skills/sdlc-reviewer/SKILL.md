---
name: sdlc-reviewer
description: Verifica la qualita', coerenza e completezza della documentazione funzionale (AFU, ex BR) prima dell'analisi tecnica. Produce un report duale — una parte per il team funzionale (problemi da chiarire) e una parte per il team tecnico (assunzioni di default). Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali. Usa questa skill quando l'utente dice "rivedi il br", "rivedi l'AFU", "review del br", "review dell'AFU", "controlla la documentazione", "verifica il br", "verifica l'AFU", "nuovo br da verificare", "nuova AFU da verificare", "c'e' un br da rivedere", o qualsiasi variazione che implichi la necessita' di verificare la qualita' della documentazione funzionale (BR / AFU) prima di procedere con l'analisi tecnica.
---

# SDLC Reviewer — Review Qualita' Documentazione Funzionale

Questa skill si posiziona *prima* di `sdlc-analyzer` nel flusso SDLC. Analizza la documentazione funzionale per qualita', coerenza e completezza, produce un report duale (per il funzionale e per il tecnico) e, se si decide di procedere, passa le assunzioni a sdlc-analyzer tramite handoff automatico.

Il flusso SDLC completo:
```
sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-executor → sdlc-updater
                                                      ↘ sdlc-progress-report
```

> **Posizionamento nel flusso (modalita' standalone)**
>
> In modalita' standalone (vedi `Fasi-New-way-of-working.md` — 2 fasi composite con Solaria a monte), `sdlc-reviewer` e' una **review tecnica post-handoff OPZIONALE in Fase 2a**: il TL la lancia solo se il package consegnato da Solaria in `plans/todo/<plan>/` e' particolarmente articolato, il dominio e' complesso o emergono dubbi architetturali. Solaria ha gia' eseguito self-review macro in Fase 1c (FunctionalReviewer + skill review/clarify post-GO), quindi se il package e' chiaro e completo lo step e' skippabile e si passa direttamente a `sdlc-analyzer`.
>
> In modalita' legacy, `sdlc-reviewer` rimane parte del flusso standard pre-analisi.

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (tutti i documenti vengono convertiti in MD)
3. **Analisi della documentazione** (intra-documento, inter-documento, vs codice)
4. **Generazione output** (CLARIFY.md con report duale)

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
| `CONST.json` manca, `PROFILE.json` esiste | "Il progetto `<PROJECT_NAME>` non ha CONST.json. Eseguire `python ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il progetto `<PROJECT_NAME>` non ha PROFILE.json. Stato inconsistente — il profilo e' incompleto. Ripristinare da git history o rifare il setup." | Stop |
| Entrambi mancano, esiste `profile.json` (legacy) | "Profilo in formato vecchio (pre-split CONST/PROFILE). Eseguire `python ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-profile-split.py --apply` per fare lo split automaticamente." | Stop |
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
| `agent({agentType, schema})` | "leggi `${CLAUDE_PLUGIN_ROOT}/agents/<agentType>.md` e lancia un Task" + parsing MD |
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

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finche' l'utente non ha risposto.

### Domanda 0 — Auto-detect plan Solaria (SOLO in modalita' standalone)

In modalita' standalone, prima di chiedere nome e documentazione, prova ad auto-rilevare il plan che Solaria ha gia' consegnato in `plans/todo/`:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/todo"/*/ 2>/dev/null
```

Per ogni cartella trovata, verifica la presenza del manifest:

```bash
ls "$BASE_PATH/todo"/*/afu-manifest.json 2>/dev/null
```

Per ogni `afu-manifest.json`, validalo contro lo schema e leggi i campi chiave:

```bash
# Validazione schema (richiede ajv-cli OPPURE python jsonschema; vedi sezione Dipendenze)
ajv validate \
  -s "$GIT_REPO_PATH/afu-manifest.schema.json" \
  -d "<manifest_path>" \
  -c ajv-formats 2>/dev/null
```

Estrai dal manifest: `nome`, `versione`, `gate_outcome`, `coverage.overall_percent`, `review_clarify_status`, `files[]`, `tests.playbook_md`.

**Validazione handoff-ability**:
- Se `gate_outcome != "GO"` → mostra warning e chiedi conferma:
  > Il plan `<nome>` v<versione> e' in stato `<gate>` (coverage=<percent>%). Solaria non ha ancora completato il quality gate di Fase 1c. Procedi comunque o aspetti?
- Se `review_clarify_status == "open"` → mostra warning analogo (bloccanti review/clarify ancora aperti Solaria-side).
- Se manifest manca o malformato → mostra errore "AFU package non conforme allo schema v2, manca/invalido afu-manifest.json. Solaria deve regenerare prima dell'handoff."

Se trovi UN plan valido (gate=GO, review_clarify_status=closed), proponilo automaticamente all'utente con i metadati:

> Ho trovato il plan `<nome>` v<versione> consegnato da Solaria in `$BASE_PATH/todo/<dir>/`:
> - Coverage: <percent>%, gate: GO, review/clarify: closed
> - Files: [lista da manifest.files]
> - Test playbook: [playbook_md] + [playbook_xlsx] (per F2c ondata b) — *mostra questa riga solo se `manifest.tests` è presente; per un package AFU-only (nessun playbook) ometti la riga*
> - Stakeholder: <stakeholder>, deadline: <deadline>, priorita: <priorita>
>
> Confermi che vuoi rivedere questo plan?

Se l'utente conferma: usa `manifest.nome` per la Domanda 1 (skip) e `manifest.files[]` per la Domanda 2 (skip). Salta direttamente alla Domanda 3 (codebase). Se l'utente vuole rivedere un plan diverso o sei in modalita' legacy, prosegui con la Domanda 1 standard.

Se trovi piu' di un plan in `todo/`, listali tutti e chiedi quale rivedere.

### Domanda 1 — Nome del Piano

> Come vuoi chiamare questo Piano? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Salva il nome. Verra' usato per creare la cartella `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`.

> **Nota standalone**: se la Domanda 0 ha trovato e validato un manifest Solaria, questa domanda viene **skippata** — si usa `manifest.nome` come slug e la cartella esiste gia' (Solaria l'ha creata e popolata).

### Domanda 2 — Documentazione

> Dove trovo l'AFU? Dammi i path per:
> - **AFU** (il documento principale dei requisiti)
> - **Mockup** (se presenti)
> - **Qualsiasi altro file rilevante** (specifiche tecniche, template, mapping, matrici)
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

> **Nota standalone**: se la Domanda 0 ha trovato e validato un manifest Solaria, questa domanda viene **skippata** — i file sono auto-popolati da `manifest.files[]` e si trovano gia' in `$BASE_PATH/todo/<plan>/requirements/` (inclusi i `requirements/mockups/` se presenti — i mockup sono opzionali). Il playbook test in `$BASE_PATH/todo/<plan>/tests/` non e' input della review (verra' usato in F2c).

### Domanda 3 — Codebase

> Quali sono le repository/codebase coinvolte in questo Piano?
> Per ognuna, dammi:
> - **Nome** (es. "back-end", "front-end", "api-gateway")
> - **Sigla** (un'abbreviazione breve, es. "BE", "FE", "GW")
> - **Path** (il path locale al codebase)
>
> Queste servono per verificare la coerenza della documentazione con il codice esistente.
> Se una repo non e' coinvolta nel Piano, non includerla.

Salva i nomi, le sigle e i path. Questi stessi dati verranno riutilizzati da sdlc-analyzer.

### Prima di procedere

Dopo aver raccolto tutti gli input, ricapitola e chiedi conferma:

> Riepilogo:
> - Nome Piano: [nome] → cartella `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`
> - Documentazione: [lista con path]
> - Repository coinvolte:
>   [per ognuna: Nome (SIGLA) → path]
>
> Confermo e procedo con la review?

Procedi solo dopo la conferma.

---

## Fase 2 — Conversione Documentazione in Markdown

> **Nota standalone**: se la Domanda 0 ha auto-rilevato un plan Solaria, la cartella `$BASE_PATH/todo/<plan>/requirements/` esiste gia' con i file consegnati da Solaria. La conversione di AFU.docx in MD per l'analisi resta necessaria (la skill analizza testo, non binari), ma **non spostare/duplicare i file binari originali** — restano in `requirements/` come ricevuti. Lavora producendo solo gli `.md` derivati nella stessa cartella.

Crea la struttura cartelle (in standalone esiste gia'):

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
mkdir -p "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements"
```

Per ogni file di documentazione fornito, converti in MD e salva nella cartella `requirements/`:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown e' disponibile globalmente
markitdown "<path-file>" > "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"
```

**File `.md`** — Copia direttamente in `requirements/`.

**Immagini (mockup `.png`, `.jpg`, ecc.)** — Non convertire. Leggile con Read (supporto multimodale) durante la fase di analisi e descrivi nel dettaglio cosa vedi.

### Verifica conversione

Dopo la conversione, verifica che ogni file MD generato contenga contenuto valido. Se un file risulta vuoto o corrotto, segnalalo all'utente e usa il Read diretto sul file originale come fallback.

Comunica all'utente lo stato della conversione:

> Conversione completata:
> - `BR_v24.docx` → `requirements/BR_v24.md` (OK)
> - `Mockup_Booking.pptx` → `requirements/Mockup_Booking.md` (OK)
> - `mockup_dashboard.png` → letto direttamente come immagine
>
> Procedo con l'analisi della documentazione.

---

## Fase 3 — Analisi della Documentazione

### 3.0 — Riconoscimento struttura AFU (feature-first vs legacy)

Prima dell'analisi, rileva la struttura dell'AFU in `requirements/AFU-*.md`:

- **Feature-first**: ha front-matter YAML (`feature_index`, `rule_index`) e la §6 "Indice di copertura canoniche". In questo caso:
  - **Ancora ogni rilievo a un ID**: il campo "Dove" di ogni problema usa `F-NN` (feature), `RB-<AREA>-NN` (regola) o `AC-FNN-NN` (criterio), non "sezione/pagina".
  - **Niente falsi "sezione mancante"**: una canonica coperta via §6 (anche senza una sezione dedicata) NON è un gap. Verifica la §6 prima di segnalare una copertura mancante.
  - **Check DRY**: se una regola `RB-…` risulta riscritta per esteso in più punti invece che citata per ID, segnalalo come problema di categoria "Incoerenza" (l'AFU feature-first impone fonte unica).
- **Legacy (section-oriented)**: nessun front-matter/§6 → analisi per le 7 sezioni canoniche come da comportamento storico. Segnala in testa al CLARIFY: `NOTA: AFU legacy section-oriented — rilievi ancorati a sezione/pagina.`

### 3.1 — Analisi intra-documento

Per ogni documento singolo convertito, verifica:

- **Coerenza interna** — le stesse informazioni sono descritte in modo coerente in tutte le sezioni? Un campo e' obbligatorio in una sezione e opzionale in un'altra? Uno stato e' definito diversamente in punti diversi?
- **Completezza dei flussi** — ogni flusso descrive il caso felice E le eccezioni, gli errori, i flussi alternativi? Ci sono scenari utente che iniziano ma non finiscono, o che hanno un esito senza un ingresso?
- **Chiarezza dei requisiti** — ci sono requisiti vaghi ("il sistema deve gestire adeguatamente...", "se opportuno", "quando necessario", "le informazioni necessarie")? Ogni requisito e' interpretabile in un solo modo?
- **Regole di business** — le regole di business sono esplicitate? Gli stati, le transizioni, le condizioni, i vincoli sono definiti? O l'AFU descrive la UI senza definire la logica dietro?

### 3.2 — Analisi inter-documento

Confronto tra documenti diversi:

- **AFU vs mockup** — ogni elemento visuale nel mockup ha un corrispettivo funzionale nell'AFU? L'AFU descrive funzionalita' che il mockup non mostra? I campi, i bottoni, le label sono coerenti?
- **AFU vs specifiche tecniche** — se ci sono specifiche tecniche, sono coerenti con i requisiti funzionali? I vincoli tecnici sono compatibili con il flusso descritto?
- **Terminologia** — lo stesso concetto e' chiamato con lo stesso nome in tutti i documenti? Se l'AFU dice "pratica" e il mockup dice "richiesta", e' un problema.

### 3.3 — Check leggero contro il codice

Per ogni codebase fornito, verifica superficialmente:

- **Entita' e modelli dati** — l'AFU presuppone strutture dati che nel codice esistono ma sono diverse? (nomi diversi, campi diversi, relazioni diverse)
- **Enum e costanti** — l'AFU definisce stati o valori che nel codice esistono gia' come enum con valori/nomi diversi?
- **API/endpoint** — l'AFU descrive operazioni che nel codice corrispondono ad API con naming o struttura diversa?
- **Flussi e stati** — l'AFU descrive transizioni di stato che nel codice funzionano diversamente?

Lo scopo NON e' fare la gap analysis (quello lo fa `sdlc-analyzer`) ma trovare problemi di *documentazione* visibili solo confrontando col codice: l'AFU presuppone strutture che nel codice esistono ma sono diverse. Questi disallineamenti vanno segnalati al team funzionale perche' possono essere errori nell'AFU o evoluzioni non documentate.

**In `classic`** (default): usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase quando possibile.

**In `deep`** (vedi "## Modalità di orchestrazione"): invoca il **Workflow tool** `name: sdlc-reviewer-quality` con `{documents (i MD in requirements/), repos, profile, const, depth, verifier_panel}`. Il workflow analizza i documenti in parallelo (intra-doc) + check read-only vs codice per repo, sintetizza problemi/assunzioni/disallineamenti (inter-doc), poi `completeness-critic` + `adversarial` (scettici cercano bloccanti/ambiguità MANCATI con lenti diverse) + `judge-panel` sulle assunzioni di Parte 2. In Fase 4 consuma `problemi` + `assunzioni_judged` (assunzioni con `davvero_non_bloccante=false` → promuovi a bloccante; con `rischio_corretto=false` → ri-valuta rischio/costo in Parte 2) + `missed` (problemi aggiunti dagli scettici) + `disallineamenti`. La **scrittura del CLARIFY.md single-file + DOCX e il commit restano dell'agente principale** (single-writer); se il workflow non parte, degrada a `classic` con banner **COPERTURA RIDOTTA**.

---

### 3.4 — Baseline legale (awareness brownfield)

Se il progetto è **web/public-facing** e **brownfield** (codebase esistente fornito in Domanda 3), verifica che l'AFU §3 "Requisiti obbligatori/legali" indirizzi la baseline legale. Consulta la checklist di contratto `solaria-agents/contract/legal-baseline-web-eu.md` (giurisdizione EU-IT di default) per i cluster: cookie-consent, privacy-policy, cookie-policy, tos, sitemap, accessibility-statement, gdpr-rights, minors-consent (condizionale), ai-act-transparency (condizionale — se la piattaforma usa AI: trasparenza + consenso ex Reg. UE 2024/1689).

- Su brownfield Solaria (Weaver) **chiede** al funzionale (OPEN_QUESTION per cluster) se inserire o se già presenti; l'esito finisce in §3 dell'AFU.
- Il tuo compito qui è **solo di awareness**: se §3 **non** menziona affatto la baseline e la Q&A legale risulta **non risolta**, solleva un problema **non bloccante** di categoria "Riferimento mancante": "La baseline legale (cookie/privacy/ToS/sitemap/accessibilità/GDPR/AI-Act) non risulta indirizzata né come già presente né come da inserire. Confermare lo stato per ciascun cluster."
- **Non** fare gate NO-GO qui (il gate legale greenfield è responsabilità del Reviewer Solaria). Su brownfield nessun gate automatico.

## Fase 4 — Generazione Output

### Categorie di problemi

Ogni problema trovato viene classificato per tipo con flag bloccante si/no:

| Categoria | Descrizione |
|---|---|
| **Incoerenza** | Contraddizioni tra parti della documentazione (intra o inter-documento) |
| **Gap funzionale** | Pezzi mancanti nella descrizione del comportamento (flussi, eccezioni, regole) |
| **Ambiguita'** | Punti interpretabili in piu' modi (requisiti vaghi, condizioni non definite) |
| **Riferimento mancante** | Dipendenze esterne non specificate (integrazioni, processi, fonti dati) |
| **Disallineamento col codice** | L'AFU presuppone strutture/terminologie diverse da quelle nel codice |

Per ogni problema documenta:
- **Categoria**: una delle 5 sopra
- **Bloccante**: si/no — un problema e' bloccante quando senza risposta non e' possibile fare una pianificazione affidabile (es. un flusso fondamentale descritto in modo contraddittorio, una regola di business centrale non definita)
- **Dove**: riferimento preciso al documento e sezione/pagina
- **Problema**: descrizione chiara del problema
- **Impatto**: cosa succede se non viene risolto
- **Domanda per il funzionale**: domanda precisa a cui serve risposta
- **Assunzione proposta** (solo per i non-bloccanti): cosa il team tecnico assumera' se non arriva chiarimento, con indicazione del rischio e del costo di correzione se l'assunzione si rivela errata

### Registro funzionale (dual-register) — regola dura + esempi

**Regola dura**: il testo primario di ogni domanda (Parte 1) è in **linguaggio business**, leggibile da un funzionale senza contesto tecnico. Il dettaglio tecnico va **solo** nel campo "Dettaglio tecnico (per il TL)" e nella Parte 2. Stesso schema condiviso con le OPEN_QUESTIONS del Weaver Solaria: `{feature, context_funzionale, domanda_funzionale, opzioni[], dettaglio_tecnico?}`.

**Esempio CATTIVO (troppo tecnico in Parte 1):**
> Domanda: Il campo `statoPratica` del DTO `PracticeDTO` deve accettare l'enum `SUSPENDED` oltre a `OPEN/CLOSED`, e l'endpoint `PATCH /practices/{id}` deve validarlo a boundary?

**Esempio BUONO (business in Parte 1, tecnico separato):**
> - **Contesto funzionale**: Oggi una pratica può essere Aperta o Chiusa. L'AFU introduce la possibilità di "sospendere" temporaneamente una pratica.
> - **Domanda per il funzionale**: Una pratica sospesa può tornare Aperta, o la sospensione è definitiva?
>   - Opzione A — la sospensione è reversibile (l'operatore può riattivarla)
>   - Opzione B — la sospensione è definitiva (equivale a una chiusura speciale)
> - **Dettaglio tecnico (per il TL)**: aggiungere `SUSPENDED` a `enum PracticeStatus`; validare la transizione in `PracticeService.changeStatus()`.

### Generazione del CLARIFY.md

Genera il file `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/CLARIFY.md` con questa struttura:

```
# Review Documentazione AFU [nome/versione]

Data review: `<data>`

Documentazione analizzata:
- [lista file con path]

Codebase verificati:
- [per ogni repo: SIGLA (nome) → path]

## Esito sintetico

[2-3 frasi: qualita' complessiva della documentazione, numero di problemi
per categoria, presenza o meno di bloccanti]

Problemi trovati: N totali (X bloccanti, Y non bloccanti)

---

## Parte 1 — Per il team funzionale

Questa sezione elenca i punti che richiedono chiarimento o correzione
nella documentazione.

### Problemi bloccanti

[Se presenti. Questi impediscono una pianificazione affidabile.]

#### 1. [Titolo problema]

- **Categoria**: [Incoerenza / Gap funzionale / Ambiguita' / Riferimento mancante / Disallineamento col codice]
- **Bloccante**: Si
- **Dove**: [ID `F-NN` / `RB-<AREA>-NN` / `AC-FNN-NN` se AFU feature-first; altrimenti documento, sezione/pagina]
- **Contesto funzionale**: [1-2 frasi in linguaggio business che spiegano la situazione a chi non conosce il codice — zero termini tecnici/DTO/endpoint]
- **Domanda per il funzionale**: [decisione da prendere, con conseguenze concrete; se ci sono più strade, elencale come opzioni con la loro conseguenza]
  - Opzione A — [conseguenza in linguaggio business]
  - Opzione B — [conseguenza]
- **Dettaglio tecnico (per il TL)**: *(opzionale)* [qui, e SOLO qui, il dettaglio tecnico: nomi campi, endpoint, enum, vincoli implementativi]
- **Impatto**: [perche' senza risposta non si puo' procedere]
- **Risposta del funzionale**: *(inserire qui la risposta)*
- **Data risposta**: *(YYYY-MM-DD)*

#### 2. [...]

### Problemi non bloccanti

#### 1. [Titolo problema]

- **Categoria**: [...]
- **Bloccante**: No
- **Dove**: [ID `F-NN` / `RB-…` / `AC-…` se feature-first; altrimenti documento, sezione/pagina]
- **Contesto funzionale**: [1-2 frasi in linguaggio business]
- **Domanda per il funzionale**: [domanda precisa, con opzioni/conseguenze se applicabile]
- **Dettaglio tecnico (per il TL)**: *(opzionale)* [dettaglio implementativo, se serve]
- **Risposta del funzionale**: *(inserire qui la risposta)*
- **Data risposta**: *(YYYY-MM-DD)*
- **Nota**: se non arriva chiarimento, il team tecnico procedera'
  con l'assunzione indicata nella Parte 2.

#### 2. [...]

---

## Parte 2 — Per il team tecnico

Questa sezione contiene le assunzioni che il team tecnico adottera'
in assenza di chiarimenti dal funzionale. Ogni assunzione e' legata
a un problema della Parte 1.

### Assunzioni proposte

| # | Problema rif. | Assunzione proposta | Rischio se errata | Costo di correzione |
|---|---|---|---|---|
| A-001 | Problema 3 | [descrizione assunzione] | [cosa succede se sbagliata] | Basso / Medio / Alto |
| A-002 | Problema 5 | [...] | [...] | [...] |

### Disallineamenti col codice

[Sezione specifica per i problemi di categoria "Disallineamento col codice".
Questa info e' solo per il team tecnico — il funzionale non ha contesto
per capirla.]

| # | Concetto AFU | Nel codice | File/Classe | Nota |
|---|---|---|---|---|
| D-001 | "stato pratica: Aperta, Chiusa" | enum PracticeStatus: OPEN, CLOSED, SUSPENDED | src/.../PracticeStatus.java | L'AFU non menziona SUSPENDED |

---

## Riepilogo per sdlc-analyzer

[Sezione tecnica consumata automaticamente da sdlc-analyzer.
Contiene le assunzioni in formato strutturato che l'analyzer
puo' incorporare direttamente nel gap report e nel piano.]

Assunzioni confermate: [lista A-XXX delle assunzioni validate dall'utente]
Bloccanti aperti: [lista dei bloccanti non ancora risolti, se si procede comunque]
```

### Generazione CLARIFY.docx (SOLO in modalita' legacy)

In **modalita' legacy** (deloitte-profiles), dopo aver generato CLARIFY.md converti in DOCX per facilitare la compilazione da parte del team funzionale:

```bash
pandoc -f markdown -t docx "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/CLARIFY.md" -o "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/CLARIFY.docx"
```

Entrambi i file (MD e DOCX) vengono salvati nella cartella del Piano. Il DOCX contiene i placeholder "*(inserire qui la risposta)*" sotto ogni domanda, pronti per la compilazione.

In **modalita' standalone** (project_repo): **NON generare il DOCX**. Solaria scrive le risposte direttamente nel `CLARIFY.md` committato via GitHub Contents API (commit message `[solaria-clarify]`). Il file `.md` con placeholder e' sufficiente.

### Commit e push degli artefatti

Dopo la generazione di CLARIFY.md (+ CLARIFY.docx in legacy), fai commit e push nella repo:

```bash
git -C "$GIT_REPO_PATH" add "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-reviewer] <nome>: review documentazione completata"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

Se il push fallisce, avvisa l'utente e proponi: (1) riprovare, (2) creare un branch, (3) lasciare il commit locale.

### Presentazione all'utente

Dopo aver generato report e DOCX, presentali all'utente per revisione. L'utente puo' chiedere modifiche al report. Quando l'utente conferma:

> **Nota standalone**: i messaggi seguenti si adattano alla modalita' rilevata. In **legacy** la skill ha generato sia `CLARIFY.md` che `CLARIFY.docx` (invia il DOCX al funzionale per la compilazione). In **standalone** la skill ha generato solo `CLARIFY.md` — Solaria scrivera' le risposte direttamente nel MD via GitHub Contents API (no DOCX, no compilazione manuale).

**Se non ci sono bloccanti:**

> Review completata. Nessun bloccante trovato.
>
> I report sono salvati in `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`:
> - `CLARIFY.md` — versione markdown
> - [Solo legacy] `CLARIFY.docx` — versione Word, pronta per la compilazione
>
> [Legacy] Puoi inviare il **DOCX** al team funzionale: contiene i placeholder per le risposte sotto ogni domanda.
> [Standalone] Notifica Solaria che `CLARIFY.md` e' pronto — compilera' le risposte direttamente nel MD committato.
>
> Quando ricevi le risposte, usa `sdlc-clarify` per integrarle nel review.
> Quando vuoi, puoi procedere con `sdlc-analyzer` per l'analisi tecnica — le assunzioni verranno incorporate automaticamente.

**Se ci sono bloccanti:**

> Review completata. Ci sono **N problemi bloccanti** ancora aperti.
>
> I report sono salvati in `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/`:
> - `CLARIFY.md` — versione markdown
> - [Solo legacy] `CLARIFY.docx` — versione Word, pronta per la compilazione
>
> [Legacy] Puoi inviare il **DOCX** al team funzionale.
> [Standalone] Notifica Solaria che `CLARIFY.md` e' pronto — compilera' le risposte direttamente nel MD committato.
>
> **Ti consiglio di attendere chiarimenti dal funzionale prima di procedere con l'analisi tecnica** — il rischio e' di pianificare lavoro su basi fragili che dovra' essere rifatto.
>
> Quando ricevi le risposte, usa `sdlc-clarify` per integrarle nel review.
>
> Pero' la decisione e' tua: se vuoi procedere comunque con `sdlc-analyzer`, le assunzioni proposte verranno incorporate nel piano e i bloccanti aperti saranno segnalati.

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC in input
- **`markitdown`** — per conversione PDF, PPTX, XLSX (installato come dipendenza di doc-to-markdown, oppure via `pip install 'markitdown[all]'` o `uvx`)
- **`pandoc`** — **opzionale (solo modalita' legacy)** per generazione CLARIFY.docx. In modalita' standalone non serve (Solaria scrive direttamente nel MD).
- **`ajv-cli` + `ajv-formats`** (oppure `python jsonschema`) — **opzionale (solo modalita' standalone)** per validare `afu-manifest.json` v2 nella Domanda 0. Installazione: `npm i -g ajv-cli ajv-formats`.
