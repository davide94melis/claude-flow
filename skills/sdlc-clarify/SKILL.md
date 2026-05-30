---
name: sdlc-clarify
description: Gestisce le risposte del team funzionale alle domande sollevate in CLARIFY.md da sdlc-reviewer. Aggiorna il report con le risposte ricevute, ri-valuta bloccanti e assunzioni, e rigenera il DOCX. Supporta risposte via DOCX compilato o conversazione diretta, e puo' essere eseguita piu' volte per risposte parziali. Usa questa skill quando l'utente dice "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", "risposte al review", o qualsiasi variazione che implichi la ricezione di risposte dal team funzionale alle domande del review BR / AFU.
---

# SDLC Clarify — Risposte del Funzionale e Aggiornamento Review

Questa skill si posiziona tra `sdlc-reviewer` e `sdlc-analyzer` nel flusso SDLC. Riceve le risposte del team funzionale alle domande sollevate nel CLARIFY.md, aggiorna il report, ri-valuta bloccanti e assunzioni.

Il flusso SDLC completo:
```
sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-executor → sdlc-updater
                                                      ↘ sdlc-progress-report
```

> **Posizionamento nel flusso (modalita' standalone)**
>
> Come `sdlc-reviewer`, anche `sdlc-clarify` e' **opzionale in Fase 2a standalone**: viene invocata solo se il TL ha lanciato `sdlc-reviewer` post-handoff e si e' generato un `CLARIFY.md`. Quando il package consegnato da Solaria e' chiaro (gate=GO, coverage alta, review/clarify Solaria-side chiuso), entrambe le skill possono essere skippate.
>
> In modalita' standalone le risposte non arrivano via DOCX compilato a mano dal funzionale ma via **MD modificato direttamente da Solaria** e committato con messaggio `[solaria-clarify] <plan>: round <N> risposte funzionale`. La skill rileva questa modalita' tramite `git log` sul `CLARIFY.md` (vedi nuova Modalita' C in Fase 2/3).
>
> In modalita' legacy il flusso DOCX-compilato resta valido.

Questa skill puo' essere eseguita **piu' volte** sullo stesso CLARIFY.md: ogni esecuzione aggiunge le nuove risposte senza sovrascrivere quelle gia' registrate. Questo supporta lo scenario tipico in cui il funzionale risponde a domande diverse in momenti diversi.

Il processo si compone di 6 fasi:
1. **Auto-detect** (trova il CLARIFY.md)
2. **Modalita' input** (DOCX compilato o conversazione)
3. **Acquisizione risposte** (raccolta e conferma)
4. **Rivalutazione** (aggiorna bloccanti e assunzioni)
5. **Aggiornamento CLARIFY.md** (integra risposte e rigenera DOCX)
6. **Riepilogo** (stato aggiornato per l'utente)

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

## Fase 1 — Auto-detect CLARIFY.md

Cerca automaticamente il report del review nella struttura `plans/` centralizzata:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls "$BASE_PATH/todo"/*/CLARIFY.md 2>/dev/null
ls "$BASE_PATH/in-progress"/*/CLARIFY.md 2>/dev/null
```

**Se trovi un solo CLARIFY.md**, proponilo:

> Ho trovato il review dell'AFU:
> - `$BASE_PATH/todo/2026-04-28_monitoraggio/CLARIFY.md`
>
> Uso questo?

**Se ne trovi piu' di uno**, elenca e chiedi:

> Ho trovato piu' review:
> - `$BASE_PATH/todo/2026-04-28_monitoraggio/CLARIFY.md`
> - `$BASE_PATH/todo/2026-04-25_booking-v2/CLARIFY.md`
>
> Quale vuoi aggiornare?

**Se non ne trovi nessuno**, informa:

> Non ho trovato nessun CLARIFY.md nella struttura `$BASE_PATH/`.
> Devi prima eseguire `sdlc-reviewer` per generare il report con le domande.

Dopo l'identificazione, leggi il CLARIFY.md e analizza la sua struttura:
- Conta i **problemi bloccanti** e quanti gia' hanno "Risposta del funzionale"
- Conta i **problemi non bloccanti** e quanti gia' hanno risposta
- Identifica le **assunzioni proposte** e il loro stato
- Calcola quante domande sono ancora **aperte** (senza risposta)

Presenta il riepilogo:

> Stato attuale del review:
> - Problemi bloccanti: N totali (X con risposta, Y ancora aperti)
> - Problemi non bloccanti: N totali (X con risposta, Y ancora aperti)
> - Domande totali ancora aperte: **Z**
>
> Procedo con l'acquisizione delle risposte?

Se tutte le domande hanno gia' risposta:

> Tutte le domande hanno gia' ricevuto risposta.
> Se vuoi aggiornare una risposta specifica, dimmelo. Altrimenti il review e' completo e puoi procedere con `sdlc-analyzer`.

---

## Fase 2 — Modalita' Input

### Auto-detection Modalita' C (SOLO in standalone)

Prima di chiedere all'utente, in modalita' standalone verifica se Solaria ha gia' compilato le risposte direttamente nel `CLARIFY.md`:

```bash
git -C "$GIT_REPO_PATH" log -1 --format="%h|%s|%an" -- "<path-a-CLARIFY.md>"
```

Se l'ultimo commit che ha toccato il file ha messaggio che **inizia con `[solaria-clarify]`** (e/o opzionalmente autore `solaria`), inferisci la Modalita' C automaticamente e procedi alla Fase 3 / Modalita' C senza chiedere all'utente.

Se non c'e' un commit `[solaria-clarify]` recente, prosegui con il prompt standard sotto.

### Prompt modalita' input

Chiedi come arrivano le risposte (il set di opzioni si adatta alla modalita'):

**In modalita' standalone** (no DOCX):

> Come arrivano le risposte del funzionale?
>
> 1. **MD compilato da Solaria** — Solaria ha gia' scritto le risposte direttamente nel CLARIFY.md committato (`[solaria-clarify]`). Le leggo dal MD.
> 2. **Te le dico io** — ho le risposte da email, riunione, chat, o altri canali.

**In modalita' legacy** (con DOCX):

> Come arrivano le risposte del funzionale?
>
> 1. **DOCX compilato** — il funzionale ha compilato il CLARIFY.docx inserendo le risposte sotto ogni domanda
> 2. **Te le dico io** — ho le risposte da email, riunione, chat, o altri canali

Aspetta la risposta prima di procedere.

---

## Fase 3 — Acquisizione Risposte

### Modalita' C — MD compilato da Solaria (SOLO standalone)

1. Identifica il commit `[solaria-clarify]` piu' recente sul `CLARIFY.md`:

```bash
git -C "$GIT_REPO_PATH" log --format="%h|%s|%ai" --all \
  --grep="^\[solaria-clarify\]" -- "<path-a-CLARIFY.md>" | head -5
```

2. Confronta lo stato corrente del file con la versione precedente al primo commit `[solaria-clarify]` (o con la versione di sdlc-reviewer marcata `[sdlc-reviewer]`):

```bash
LAST_REVIEWER_SHA=$(git -C "$GIT_REPO_PATH" log -1 --format="%H" \
  --grep="^\[sdlc-reviewer\]" -- "<path-a-CLARIFY.md>")
git -C "$GIT_REPO_PATH" diff "$LAST_REVIEWER_SHA" HEAD -- "<path-a-CLARIFY.md>"
```

3. Per ogni domanda, cerca differenze nei placeholder `*(inserire qui la risposta)*` sostituiti con testo non vuoto.

4. Presenta le risposte rilevate per conferma, una alla volta, indicando autore + commit:

> **Problema bloccante 1 — [Titolo]**
> Domanda: [domanda originale]
> Risposta rilevata (commit `<sha>` di Solaria, <data>): "[testo dal MD]"
>
> Confermo questa risposta? (si / no / correggi)

5. Per ogni risposta confermata, marca come acquisita e passa alla rivalutazione (Fase 4). NB: le risposte sono **gia' nel file** committato, quindi la Fase 5.1 (scrittura risposte) viene saltata in Modalita' C — la skill aggiorna solo i campi strutturati (Stato assunzione, Data risposta, sezioni di riepilogo bloccanti/aperti) in un secondo commit.

6. Se sono presenti anche risposte raccolte offline non ancora nel MD, l'utente puo' aggiungere la Modalita' B come complemento.

### Modalita' A — DOCX compilato (SOLO legacy)

1. Chiedi il path del DOCX compilato:

> Dammi il path del CLARIFY.docx compilato dal funzionale.

2. Converti il DOCX in markdown con pandoc:

```bash
pandoc -f docx -t markdown "<path-docx-compilato>" -o "<cartella-br>/CLARIFY_risposte_temp.md"
```

3. Confronta il file convertito con il CLARIFY.md originale. Per ogni domanda, cerca differenze nel testo dopo il campo "**Risposta:**":
   - Se il placeholder `*(inserire qui la risposta)*` e' stato sostituito con testo diverso → risposta rilevata
   - Se il placeholder e' invariato o il campo e' assente → nessuna risposta

4. Presenta le risposte rilevate per conferma, una alla volta:

> **Problema bloccante 1 — [Titolo]**
> Domanda: [domanda originale]
> Risposta rilevata: "[testo estratto dal DOCX]"
>
> Confermo questa risposta? (si / no / correggi)

Per ogni risposta, aspetta la conferma. Se l'utente dice "correggi", chiedi il testo corretto.

5. Dopo aver processato tutte le risposte rilevate, chiedi:

> Ho rilevato N risposte dal DOCX. Ci sono altre risposte che il funzionale ha dato a voce o via email e che non sono nel DOCX?

Se si', passa alla Modalita' B per le domande rimanenti.

6. Rimuovi il file temporaneo:

```bash
rm "<cartella-br>/CLARIFY_risposte_temp.md"
```

### Modalita' B — Conversazione

Identifica tutte le domande ancora aperte (senza "Risposta del funzionale"). Presentale una alla volta, raggruppate per priorita': prima i bloccanti, poi i non bloccanti.

Per ogni domanda aperta:

> **[Bloccante/Non bloccante] [N] — [Titolo problema]**
>
> Domanda per il funzionale: [domanda originale]
>
> Qual e' la risposta? (scrivi "salta" se non hai ancora la risposta)

Se l'utente scrive "salta", "non lo so", "ancora niente", o simili → segna come ancora aperta e passa alla successiva.

Dopo tutte le domande:

> Risposte raccolte: N su M domande aperte.
> Domande ancora senza risposta: K
>
> Procedo con l'aggiornamento del review?

---

## Fase 4 — Rivalutazione

**In `deep`** (cerchio *light*, vedi "## Modalità di orchestrazione"): nessun workflow pesante. Due sub-step leggeri: (1) un **finder** sull'estrazione delle risposte ambigue dal diff/DOCX che **classifica, non riscrive** (Regola verbatim); (2) un **adversarial-verify SOLO sulle assunzioni "Rigettata"** — un rigetto errato inietta un fatto sbagliato in `sdlc-analyzer`: un'istanza `sdlc-verifier` scettica conferma che la risposta del funzionale contraddice davvero l'assunzione prima di marcarla `Rigettata`. Banner **COPERTURA RIDOTTA** se degradi a `classic`.

Per ogni risposta ricevuta, valuta l'impatto:

### Problemi bloccanti

Per ogni bloccante con risposta, valuta se la risposta **risolve** il problema:

- **Risolto**: la risposta chiarisce il punto in modo univoco, il problema non blocca piu' la pianificazione
  → Stato: `Bloccante: Si` diventa `Bloccante: Si → **RISOLTO**`

- **Non risolto**: la risposta e' parziale, ambigua, o solleva nuove domande
  → Stato: resta `Bloccante: Si`, con nota esplicativa
  → Se la risposta genera una nuova domanda, aggiungila come "Domanda di follow-up"

### Problemi non bloccanti

Per ogni non bloccante con risposta, confronta la risposta con l'assunzione proposta nella Parte 2:

- **Assunzione confermata**: la risposta del funzionale conferma l'assunzione
  → Stato assunzione: `Confermata dal funzionale`

- **Assunzione rigettata**: la risposta del funzionale da' un'indicazione diversa
  → Stato assunzione: `Rigettata — risposta: [fatto corretto]`
  → **Segnala all'utente**: "L'assunzione A-XXX era '[assunzione proposta]' ma il funzionale ha risposto '[risposta]'. L'analisi tecnica usera' la risposta del funzionale."

### Presentazione della rivalutazione

Prima di modificare qualsiasi file, presenta il riepilogo:

> ## Rivalutazione
>
> **Bloccanti risolti**: N
> [per ognuno: titolo → sintesi risposta]
>
> **Bloccanti ancora aperti**: N
> [per ognuno: titolo — motivo]
>
> **Assunzioni confermate**: N
> [lista A-XXX]
>
> **Assunzioni rigettate**: N
> [per ognuna: A-XXX — assunzione proposta → fatto corretto]
>
> **Domande ancora aperte**: N
>
> Procedo con l'aggiornamento del CLARIFY.md?

Aspetta conferma.

---

## Fase 5 — Aggiornamento CLARIFY.md e DOCX

### 5.1 — Aggiornamento problemi (Parte 1)

Per ogni problema che ha ricevuto risposta, aggiorna il blocco nel CLARIFY.md aggiungendo i campi:

**Per i bloccanti risolti:**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: Si → **RISOLTO**
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Impatto**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta]
- **Data risposta**: <YYYY-MM-DD>
```

**Per i bloccanti non ancora risolti (risposta parziale):**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: Si
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Impatto**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta parziale]
- **Data risposta**: <YYYY-MM-DD>
- **Nota**: La risposta non risolve completamente il bloccante. [spiegazione]
- **Domanda di follow-up**: [nuova domanda se necessaria]
```

**Per i non bloccanti:**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: No
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta]
- **Data risposta**: <YYYY-MM-DD>
```

### 5.2 — Aggiornamento assunzioni (Parte 2)

Aggiorna la tabella delle assunzioni aggiungendo le colonne "Stato" e "Risposta funzionale":

```
| # | Problema rif. | Assunzione proposta | Rischio se errata | Costo | Stato | Risposta funzionale |
|---|---|---|---|---|---|---|
| A-001 | NB-1 | [assunzione] | [rischio] | Basso | **Confermata** | "Si', confermato" |
| A-002 | NB-2 | [assunzione] | [rischio] | Basso | *In attesa* | — |
| A-005 | NB-5 | [assunzione] | [rischio] | Basso | **Rigettata** | "[risposta diversa]" |
```

### 5.3 — Aggiornamento "Riepilogo per sdlc-analyzer"

Sostituisci l'intera sezione "Riepilogo per sdlc-analyzer" con il formato arricchito:

```
## Riepilogo per sdlc-analyzer

Ultimo aggiornamento: <YYYY-MM-DD> (sdlc-clarify)

### Bloccanti risolti

1. [B1] [Titolo] → [sintesi risposta in 1-2 frasi]
2. [B2] [Titolo] → [sintesi risposta]
[...]

### Bloccanti ancora aperti

N. [BN] [Titolo] — in attesa di risposta
[...]

[Se non ci sono bloccanti aperti:]
Nessun bloccante aperto. Tutti i bloccanti sono stati risolti.

### Stato assunzioni

Assunzioni confermate dal funzionale: A-001, A-003, A-007
Assunzioni adottate (nessuna risposta, si procede con l'assunzione proposta): A-002, A-004
Assunzioni rigettate (risposta diversa dall'assunzione):
- A-005: assunzione era "[testo]" → il funzionale ha risposto "[testo]"
[...]

### Repository coinvolte

- SIGLA (nome) → path
[...]
```

### 5.4 — Rigenerazione DOCX (SOLO legacy)

In **modalita' legacy**, dopo aver aggiornato il CLARIFY.md rigenera il DOCX:

```bash
pandoc -f markdown -t docx "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/CLARIFY.md" -o "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/CLARIFY.docx"
```

Se il file si trova in `$BASE_PATH/in-progress/`, usa quel path:

```bash
pandoc -f markdown -t docx "$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/CLARIFY.md" -o "$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/CLARIFY.docx"
```

In **modalita' standalone**: **SKIP** — non rigenerare il DOCX. Il `.md` aggiornato e' sufficiente (Solaria leggera' eventuali ri-richieste dal MD).

### 5.5 — Commit e push

Dopo la rigenerazione (legacy) o l'aggiornamento dei campi strutturati (standalone), effettua commit e push:

```bash
git -C "$GIT_REPO_PATH" add "$BASE_PATH/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-clarify] <nome>: aggiornato review con risposte funzionale"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Fase 6 — Riepilogo Finale

Presenta all'utente il riepilogo completo:

> **Nota**: la riga `CLARIFY.docx` nei messaggi sotto compare solo in **modalita' legacy**. In standalone il file non viene rigenerato.

**Se tutti i bloccanti sono risolti:**

> ## Aggiornamento review completato
>
> **File aggiornati**:
> - `[path]/CLARIFY.md` — aggiornato con N risposte
> - [Solo legacy] `[path]/CLARIFY.docx` — rigenerato
>
> **Stato**:
> - Bloccanti: tutti risolti (N su N)
> - Assunzioni confermate: X | Rigettate: Y | In attesa: Z
> - Domande ancora aperte: K
>
> **Il review e' pronto per `sdlc-analyzer`**. Puoi procedere con l'analisi tecnica — le risposte e le assunzioni verranno incorporate automaticamente nel gap report e nel piano di implementazione.

**Se ci sono ancora bloccanti aperti:**

> ## Aggiornamento review completato
>
> **File aggiornati**:
> - `[path]/CLARIFY.md` — aggiornato con N risposte
> - [Solo legacy] `[path]/CLARIFY.docx` — rigenerato
>
> **Stato**:
> - Bloccanti risolti: X su N
> - **Bloccanti ancora aperti: Y**
>   [lista dei bloccanti aperti]
> - Assunzioni confermate: X | Rigettate: Y | In attesa: Z
> - Domande ancora aperte: K
>
> **Ci sono ancora bloccanti aperti.** Puoi:
> 1. Attendere le risposte rimanenti e rieseguire `sdlc-clarify` (in standalone Solaria compilera' un nuovo round via commit `[solaria-clarify]`)
> 2. Procedere comunque con `sdlc-analyzer` (i bloccanti verranno segnalati come "Da chiarire" nel gap report)

**Se ci sono assunzioni rigettate:**

Aggiungi al riepilogo:

> **Attenzione — Assunzioni rigettate:**
> Le seguenti assunzioni del team tecnico sono state corrette dal funzionale:
> - A-XXX: "[assunzione]" → "[risposta corretta]"
>
> Queste correzioni verranno automaticamente incorporate da `sdlc-analyzer`.

---

## Regole Fondamentali

1. **Mai modificare le domande o le categorie originali** — i problemi restano invariati, solo le risposte vengono aggiunte
2. **Mai sovrascrivere risposte precedenti** — in caso di round multipli, ogni risposta viene aggiunta, non sostituita. Se una risposta deve essere corretta, l'utente lo dice esplicitamente
3. **Sempre chiedere conferma** — prima di scrivere sul CLARIFY.md, mostra la rivalutazione e aspetta conferma
4. **Sempre rigenerare il DOCX** — dopo ogni modifica al MD, il DOCX deve essere rigenerato
5. **Preservare la tracciabilita'** — ogni risposta ha la data, ogni assunzione ha lo stato. La storia completa e' sempre leggibile
6. **Non interpretare le risposte** — riporta la risposta del funzionale cosi' com'e'. La rivalutazione (risolto/non risolto, confermata/rigettata) e' una tua valutazione tecnica che presenti all'utente per conferma

---

## Dipendenze

- **`pandoc`** — **opzionale (solo modalita' legacy)** per conversione DOCX ↔ MD e rigenerazione DOCX. In modalita' standalone non serve (Solaria scrive direttamente nel MD via GitHub Contents API; la skill legge dal MD e fa diff via `git`).
- **`sdlc-reviewer`** — deve essere stato eseguito prima (CLARIFY.md deve esistere). In modalita' standalone, la presenza del file in `$BASE_PATH/todo/<plan>/` o `$BASE_PATH/in-progress/<plan>/` e' il prerequisito; il file puo' essere stato creato anche da una invocazione di sdlc-reviewer in F2a opzionale.
