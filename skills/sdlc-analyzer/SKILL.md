---
name: sdlc-analyzer
description: Analizza una nuova AFU (Analisi Funzionale Utente, ex Business Requirement / BR) confrontandola con i codebase esistenti del progetto, genera un gap report dettagliato per funzionalità e un Piano di implementazione con task indipendenti assegnate a sviluppatori muniti di Claude Code. Usa questa skill quando l'utente dice "abbiamo un nuovo br", "abbiamo una nuova afu", "nuovo Piano", "nuovo br", "c'è un br nuovo", "analizza il br", "analizza l'AFU", "gap analysis br", "gap analysis AFU", "nuovo business requirement", "nuova analisi funzionale utente", o qualsiasi variazione che implichi l'arrivo di un nuovo documento di requisiti da analizzare e pianificare. Attivala anche quando l'utente menziona la necessità di confrontare documentazione di requisiti con il codice per trovare cosa manca e pianificare lo sviluppo.
---

# SDLC Analyzer — PLAN & TASKS

Questa skill guida l'analisi di una nuova AFU (Analisi Funzionale Utente, ex Business Requirement): dal confronto con i codebase al Piano di sviluppo con task indipendenti per un team di sviluppatori, ognuno munito di Claude Code.

Il flusso SDLC completo:
```
sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-executor → sdlc-updater
                                                      ↘ sdlc-progress-report
```

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (solo se `sdlc-reviewer` non e' stato eseguito prima — se trova `requirements/` nella cartella del Piano, salta questa fase)
3. **Analisi gap** (confronto documentazione vs codice)
4. **Generazione output** (2 file MD: gap report + piano di implementazione, nella cartella del Piano)

---

## Risoluzione Path (modalita' duale: standalone | legacy)

Tutte le operazioni su file plan avvengono nella **project_repo** (modalita' standalone, una repo per progetto) o nella repo `deloitte-profiles` (modalita' legacy), **non** nella repo del codice applicativo. Il codice del progetto continua a essere scritto nelle repo del progetto.

### Discovery del profilo (master-folder aware)

Le skill possono partire dalla **root della repo di specifiche** (dove vive `.sdlc-local.json`) **oppure** da una **master-folder** di progetto che contiene le sottocartelle di tutte le repo (backend, frontend, `*-specs`, ...). In quest'ultimo caso il marker non e' in cwd ma in una sottocartella. Risolvi il profilo **prima** di leggere il config, impostando `SDLC_CFG` (path assoluto del file di config risolto):

```bash
SDLC_CFG=""
if   [ -f ".sdlc-local.json" ]; then SDLC_CFG="$PWD/.sdlc-local.json"
elif [ -f ".br-local.json"   ]; then SDLC_CFG="$PWD/.br-local.json"
else
  # sottocartelle immediate (maxdepth 2): marker .sdlc-local.json poi legacy .br-local.json
  CANDS=$(find . -maxdepth 2 \( -name .sdlc-local.json -o -name .br-local.json \) 2>/dev/null)
  # dedup per PROGETTO (chiave = project_repo | profiles_repo/profilo): molte config di un solo
  # progetto collassano in UNA scelta; restano righe distinte solo per progetti diversi.
  UNIQ=$(printf '%s\n' "$CANDS" | while IFS= read -r f; do
    [ -z "$f" ] && continue
    key=$(grep -oP '"project_repo"\s*:\s*"\K[^"]+' "$f" 2>/dev/null)
    [ -z "$key" ] && key="$(grep -oP '"profiles_repo"\s*:\s*"\K[^"]+' "$f" 2>/dev/null)/$(grep -oP '"profilo"\s*:\s*"\K[^"]+' "$f" 2>/dev/null)"
    printf '%s\t%s\n' "$key" "$f"
  done | sort -u -t"$(printf '\t')" -k1,1)
  N=$(printf '%s\n' "$UNIQ" | grep -c .)
  if   [ "$N" -eq 1 ]; then SDLC_CFG=$(printf '%s' "$UNIQ" | cut -f2)
  elif [ "$N" -gt 1 ]; then echo "MULTI"; printf '%s\n' "$UNIQ" | cut -f2
  fi
fi
echo "SDLC_CFG=${SDLC_CFG:-<none>}"
```

- **1 progetto** → usa `SDLC_CFG`. Prosegui col blocco di lettura sotto.
- **`MULTI`** (piu' progetti DISTINTI) → mostra i candidati e **chiedi all'utente** quale progetto lavorare (`AskUserQuestion`), imposta `SDLC_CFG` di conseguenza, e ancora ogni operazione git ai repo di quel progetto.
- **nessun candidato** → comportamento invariato: applica la sezione "Se ne' `.sdlc-local.json` ne' `.br-local.json` esistono" sotto.

Da qui in poi, i comandi che seguono referenziano `.br-local.json` per continuita' storica: **applicali a `"$SDLC_CFG"`** (il file risolto). Il suffisso `-specs` NON e' una chiave — il marker e' la presenza del file di config; il suffisso puo' servire solo come hint di ordinamento tra candidati.

### Lettura del file di configurazione locale (`.sdlc-local.json` con fallback `.br-local.json`)

**Lettura compatibile**: il file di configurazione locale può chiamarsi `.sdlc-local.json` (nuovo nome, raccomandato) oppure `.br-local.json` (nome legacy, ancora supportato). Cerca PRIMA `.sdlc-local.json`; se non esiste, fa fallback a `.br-local.json`. Se nessuno dei due esiste, ferma e chiedi all'utente di eseguire `/sdlc-profile-setup`.

Se trovi solo `.br-local.json` (profilo legacy), emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

I comandi `bash` seguenti sono scritti referenziando `.br-local.json` per chiarezza storica — applica equivalentemente la stessa logica al file effettivamente trovato (sia `.sdlc-local.json` che `.br-local.json`).

All'avvio, leggi il file (priorità `.sdlc-local.json`, fallback `.br-local.json`) dalla root della repo corrente:

```bash
# Esempio con .br-local.json — equivalente per .sdlc-local.json
cat "$SDLC_CFG" 2>/dev/null
```

La presenza del campo `project_repo` o `profiles_repo` discrimina la modalita':

```bash
if grep -q '"project_repo"' "$SDLC_CFG" 2>/dev/null; then
  MODE="standalone"
  PROJECT_REPO=$(grep -oP '"project_repo"\s*:\s*"\K[^"]+' "$SDLC_CFG")
  PROJECT_NAME=$(grep -oP '"project_name"\s*:\s*"\K[^"]+' "$SDLC_CFG")
  BASE_PATH="$PROJECT_REPO/plans"
  CONST_PATH="$PROJECT_REPO/constitution"
  DATASET_PATH="$PROJECT_REPO/dataset"        # solo standalone (popolato da Solaria-side)
  GIT_REPO_PATH="$PROJECT_REPO"
elif grep -q '"profiles_repo"' "$SDLC_CFG" 2>/dev/null; then
  MODE="legacy"
  PROFILES_REPO=$(grep -oP '"profiles_repo"\s*:\s*"\K[^"]+' "$SDLC_CFG")
  PROFILO=$(grep -oP '"profilo"\s*:\s*"\K[^"]+' "$SDLC_CFG")
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

## Lingua di interazione e degli artefatti

La lingua di **interazione** (conversazione con l'utente) e' persistita in `.sdlc-local.json` (fallback `.br-local.json`) nel campo flat `interaction_language` (`it` | `en`). Risoluzione (grep-compatibile, niente `jq`):

```bash
INTERACTION_LANG=$(grep -oP '"interaction_language"\s*:\s*"\K(it|en)' "$SDLC_CFG" 2>/dev/null)
```

- Se `INTERACTION_LANG` e' vuoto (campo assente, es. profilo pre-esistente): **chiedi una volta** all'utente `it`/`en` (`AskUserQuestion`), poi **persisti** aggiungendo `"interaction_language": "<scelta>"` a `"$SDLC_CFG"` (staging con messaggio `[sdlc-config] set interaction_language`). **Nessun default silenzioso.**
- Tutta la **comunicazione conversazionale** con l'utente segue `INTERACTION_LANG`.

**Lingua degli artefatti prodotti (regola per classe, indipendente da `INTERACTION_LANG`):**

| Classe | Artefatti | Lingua |
|---|---|---|
| Dev-facing | gap report/PLAN, TASKS, PROGRESS, bug report, codice, messaggi di commit, report estimator, report progress | **Solo inglese (EN)** |
| Funzionale/end-user | CLARIFY (lato skill); AFU, playbook, report a11y (lato Solaria) | Lingua di interazione/prodotto **+ copia EN** (`<nome>.en.<ext>`) |
| Mockup | copy UI (lato Solaria) | Solo lingua utente finale (nessuna copia EN) |

> Questa skill produce artefatti **dev-facing → sempre in EN**, indipendentemente da `INTERACTION_LANG` (che governa solo la conversazione). *(Eccezione: `sdlc-reviewer`/`sdlc-clarify` producono anche il CLARIFY, funzionale → vedi la loro sezione dedicata.)*

---

## Modalità di orchestrazione

Ogni skill SDLC può girare in due modalità:

- **`classic`** (default) — esecuzione sequenziale, leggera, pochi token. È il comportamento storico.
- **`deep`** — orchestrazione parallela multi-agent (Workflow tool) + verifica adversariale: più lenta e costosa, ma più esaustiva.

> **Mai escalation silenziosa.** Non si passa a `deep` (con la relativa spesa) senza una scelta esplicita — flag persistente o conferma dell'utente. Default globale = `classic`.

### Risoluzione della modalità (cascata, in ordine di precedenza)

1. **Flag persistente** in `.sdlc-local.json` (fallback `.br-local.json`) — la sorgente automatica a precedenza più alta. Campi *flat* (grep-compatibili, niente `jq`):

   ```bash
   LOCAL_CFG="$SDLC_CFG"
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

### Domanda 0 — Cartella Piano esistente

Prima di chiedere qualsiasi cosa, verifica cosa Solaria (standalone) o `sdlc-reviewer` (legacy) hanno gia' depositato in `plans/todo/`:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/todo"/*/ 2>/dev/null
```

In **modalita' standalone**, controlla anche eventuali plan ancora in `plans/draft/` (Solaria non ha ancora fatto handoff). Se trovi un `afu-manifest.json` in `draft/` ma non in `todo/`:

```bash
ls "$BASE_PATH/draft"/*/afu-manifest.json 2>/dev/null
```

> Ho trovato un plan ancora in `plans/draft/<dir>/`. Solaria non ha eseguito l'handoff (probabilmente gate=NO-GO o review/clarify Solaria-side ancora aperto). Attendi che Solaria completi la Fase 1c e promuova a `todo/`, oppure forza l'analisi sul draft (sconsigliato).

Per i plan in `$BASE_PATH/todo/<dir>/`, leggi `afu-manifest.json` (se presente, modalita' standalone) ed estrai `nome`, `versione`, `coverage.overall_percent`, `gate_outcome`, `tests.playbook_md`, e (se presenti, schema v2) `feature_index`, `rule_index`, `legal_baseline`. Cerca poi `CLARIFY.md`:

```bash
ls "$BASE_PATH/todo"/*/CLARIFY.md 2>/dev/null
```

> **Nota standalone**: `CLARIFY.md` puo' essere assente se il TL ha skippato la review tech post-handoff opzionale (F2a). In tal caso `sdlc-analyzer` lavora direttamente dal `afu-manifest.json` e da `requirements/`.

**Se trovi una cartella con CLARIFY.md** (legacy o standalone con review tech opzionale attivata), proponila:

> Ho trovato una cartella Piano con review gia' completata:
> - `$BASE_PATH/todo/2026-04-28_booking-v2/CLARIFY.md`
> - Documentazione convertita in `requirements/`
>
> Uso questa come base? Le assunzioni dalla review verranno incorporate nel piano.

Se l'utente conferma:
- Leggi il `CLARIFY.md`, in particolare la sezione "Riepilogo per sdlc-analyzer"
- Controlla se `sdlc-clarify` e' stato eseguito: cerca "Ultimo aggiornamento:" con "(sdlc-clarify)" nel riepilogo
- **Se sdlc-clarify e' stato eseguito**:
  - Estrai i bloccanti risolti → usali come fatti certi nell'analisi gap
  - Estrai le assunzioni confermate dal funzionale → usale come fatti
  - Estrai le assunzioni rigettate → usa la risposta del funzionale al posto dell'assunzione
  - Estrai le assunzioni adottate senza risposta → usale con rischio segnalato
  - Mostra all'utente: "Review con chiarimenti: N bloccanti risolti, M assunzioni confermate, K bloccanti ancora aperti"
  - I bloccanti ancora aperti vengono segnalati come "Da chiarire" nel gap report
- **Se sdlc-clarify NON e' stato eseguito**:
  - Usa la sezione "Riepilogo per sdlc-analyzer" nella sua forma originale (assunzioni confermate dall'utente e bloccanti aperti)
- Usa i file in `requirements/` per l'analisi (salta la Fase 2)
- Salta le domande su documentazione e codebase — leggile dal CLARIFY.md
- Procedi direttamente alla Domanda 3 (Team di sviluppo)

**Se non trovi nulla**, chiedi il nome del Piano:

> Come vuoi chiamare questo Piano? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Poi procedi con le domande successive.

### Domanda 1 — Codebase

> Quali sono le repository/codebase coinvolte in questo Piano?
> Per ognuna, dammi:
> - **Nome** (es. "back-end", "front-end", "api-gateway", "mobile-app", "notification-service" — qualsiasi nome che identifichi la repo)
> - **Sigla** (un'abbreviazione breve, es. "BE", "FE", "GW", "MOB", "NS" — verrà usata nelle tabelle e nei report)
> - **Path** (il path locale al codebase)
>
> Elenca tutte quelle coinvolte, senza limiti. Se una repo non è coinvolta nel Piano, non includerla.
>
> Esempio:
> - Back-end (BE) → `/path/to/backend`
> - Front-end (FE) → `/path/to/frontend`
> - Notification Service (NS) → `/path/to/notifications`

Salva i nomi, le sigle e i path forniti. Usa le sigle dell'utente in tutto il report e nel piano. Se l'utente fornisce una sola repo, è perfettamente valido — non forzare una lista lunga.

### Domanda 2 — Documentazione

> Dove trovo l'AFU? Dammi i path per:
> - **AFU** (il documento principale dei requisiti)
> - **Mockup** (se presenti)
> - **Qualsiasi altro file rilevante** (specifiche tecniche, template, mapping, matrici)
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Team di sviluppo

> Chi lavorerà all'implementazione? Per ogni sviluppatore dimmi:
> - **Nome** (o identificativo, es. "Marco", "Dev-Senior")
> - **Ruolo/Area**: su quali repository lavora (usa le sigle definite prima, es. "BE", "FE", "BE+FE", "GW+NS", o qualsiasi combinazione)
> - **Seniority**: Junior / Mid / Senior
>
> Esempio: "Marco - BE senior, Luca - FE mid, Anna - BE+GW junior"

### Domanda 4 — Strategia di decomposizione dei task

Leggi un eventuale default persistito (grep-compatibile, niente `jq`):

```bash
DECOMP_BIAS=$(grep -oP '"decomposition_bias"\s*:\s*"\K(testability|parallelization)' "$SDLC_CFG" 2>/dev/null)
```

Chiedi comunque la scelta per QUESTO Piano con `AskUserQuestion` (pre-seleziona `$DECOMP_BIAS` se presente, altrimenti `testability`):

> Come vuoi decomporre i task di questo Piano?
> - **testability-first** (default) — ogni task porta criteri di completamento auto-verificabili dallo sviluppatore (e, dove serve, il proprio test); task più grandi (fino a 3-5 gg), meno merge task, ma parallelismo massimizzato a parità di testabilità.
> - **parallelization-first** — split atomico aggressivo (anche <1 gg quando aumenta il fan-out), più merge task cross-stream, accettando task meno comprensibili/testabili in isolamento (con un floor minimo di verificabilità).

Registra la scelta come `DECOMP_MODE` e riportala nell'header/Assunzioni del TASKS. Nessuna escalation silenziosa: la scelta è sempre esplicita.

### Domanda 5 — Deadline e data di inizio (opzionale)

> Esiste una **data di inizio ufficiale** del Piano e una **deadline**? (formato `YYYY-MM-DD`, oppure "nessuna")

Se il manifest standalone (`requirements/afu-manifest.json`) ha già un campo `deadline`, proponilo come default. Registra `START_DATE` e `DEADLINE` (o "non fornita"). La sezione "Cadenza verso la deadline" nel TASKS richiede **entrambe** le date: se una o entrambe mancano, viene omessa. L'header del PLAN riporta comunque i due campi (con `non fornita` dove manca), così progress-report ha una fonte uniforme; con entrambe assenti non calcolerà anticipo/ritardo.

### Prima di procedere

Dopo aver raccolto tutti gli input, ricapitola quello che hai ricevuto e chiedi conferma:

> Riepilogo:
> - Repository coinvolte:
>   [per ognuna: Nome (SIGLA) → path]
> - Documentazione: [lista con path]
> - Team: [lista con ruolo e seniority]
> - Strategia decomposizione: [testability-first | parallelization-first]
> - Deadline / Data inizio: [vedi Domanda 5]
>
> Confermo e procedo con l'analisi?

Procedi solo dopo la conferma.

---

## Fase 2 — Conversione Documentazione in Markdown

**Se `sdlc-reviewer` e' stato eseguito** e la cartella `requirements/` esiste gia' nella cartella del Piano (`$BASE_PATH/todo/<data>_<nome>/requirements/`), **salta completamente questa fase** e vai alla Fase 3. La conversione e' gia' stata fatta da sdlc-reviewer.

**Se `sdlc-reviewer` non e' stato eseguito**, converti tutti i documenti non-MD in formato Markdown. Questo riduce significativamente il contesto necessario e rende i documenti piu' leggibili per l'analisi.

### Procedura di conversione

Crea la cartella del Piano e la sottocartella per i documenti convertiti:

```bash
mkdir -p "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements"
```

Per ogni file di documentazione fornito:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown è disponibile globalmente
markitdown "<path-file>" > "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"
```

**File `.md`** — Copia direttamente in `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/`.

**Immagini (mockup `.png`, `.jpg`, ecc.)** — Non convertire. Leggile con Read (supporto multimodale) durante la fase di analisi e descrivi nel dettaglio cosa vedi.

### Verifica conversione

Dopo la conversione, verifica che ogni file MD generato contenga contenuto valido. Se un file risulta vuoto o corrotto, segnalalo all'utente e usa il Read diretto sul file originale come fallback.

Comunica all'utente lo stato della conversione:

> Conversione completata:
> - `BR_v24.docx` → `requirements/BR_v24.md` (OK)
> - `Mockup_Booking.pptx` → `requirements/Mockup_Booking.md` (OK)
> - `mockup_dashboard.png` → letto direttamente come immagine
>
> Procedo con l'analisi gap.

Da questo punto in poi, l'analisi lavora sui file MD convertiti in `requirements/`, non sui file originali.

---

### Scansione mockups/ (modalita' standalone)

Se il plan e' in modalita' standalone **e** la cartella `requirements/mockups/` esiste (i mockup sono **opzionali** — vedi nota sotto), scansionala e usa i file come input visuale per la gap analysis UI/frontend:

```bash
ls "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements/mockups"/* 2>/dev/null
```

Per ogni mockup (PNG/JPG/SVG generato dal Mockup Designer Agent Solaria), usa `Read` (supporto multimodale) e descrivi cosa rappresenta. Mappa ogni componente UI rilevato a una task della matrice di verifica (colonna FE o equivalente). Se un mockup mostra elementi che il codice FE non implementa ancora, e' un gap "Mancante" automatico per le task frontend.

I mockup, **quando presenti**, vivono in `requirements/mockups/` perche' Solaria li include in `manifest.files[]` con prefisso `mockups/`, e sono asset di prima classe per il planning UI. Sono pero' **opzionali**: l'Orchestrator Solaria li genera solo se l'analista lo conferma al gate post-GO, quindi un package puo' legittimamente non averli. Se `requirements/mockups/` e' assente o `manifest.files[]` non elenca voci `mockups/`, il comando `ls ... 2>/dev/null` sopra ritorna vuoto: salta la scansione, senza segnalarlo come anomalia.

---

## Fase 3 — Analisi Gap

### 3.1 — Lettura della documentazione

Leggi integralmente ogni documento MD convertito nella cartella `requirements/` (dentro la cartella del Piano). Per le immagini (mockup), usa Read sul file originale e descrivi nel dettaglio cosa vedi, mappando le UI ai componenti da implementare.

Da ogni documento, estrai:
- Ogni requisito funzionale (cosa deve fare il sistema)
- Ogni requisito tecnico (come deve farlo, vincoli, integrazioni)
- Ogni elemento visuale dai mockup (layout, componenti, flussi utente)

Organizza i requisiti per **funzionalità** (es. "Dashboard", "Booking", "Monitoraggio"), non per documento o per modulo tecnico.

### 3.1bis — Parsing AFU feature-first (front-matter + §6 indice di copertura)

Le AFU generate da Solaria con la struttura **feature-first** espongono anchor macchina che rendono l'estrazione dei requisiti deterministica. Prima di leggere il corpo in prosa, estrai gli anchor:

1. **Front-matter YAML** (in testa a `requirements/AFU-<slug>.md`): leggi `nome`, `versione`, `parent_version` (se presente), `feature_index` (ID feature `F-01, F-02, ...`), `rule_index` (ID regola `RB-<AREA>-NN`).

   ```bash
   AFU_FILE=$(ls "$BASE_PATH/todo"/<dir>/requirements/AFU-*.md 2>/dev/null | head -1)
   # Estrai il blocco front-matter (tra i primi due '---')
   awk '/^---$/{c++; next} c==1' "$AFU_FILE"
   ```

2. **§6 Indice di copertura canoniche** (matrice auto-generata in fondo all'AFU): mappa ognuna delle 7 chiavi canoniche (`funzionalita, attori, casi_uso, flussi, regole_business, vincoli_tecnici, criteri_accettazione`) alle `F-.. / RB-.. / AC-..` che la coprono. Usa questa matrice come **fonte di verità della copertura**: sostituisce l'euristica di scansione per sezioni.

3. **Corpo §4 (feature-first)**: per ogni `## F-NN — <nome>`, estrai i sotto-blocchi: Sintesi, Attori coinvolti, Casi d'uso, Flussi (happy + alternativi + edge case), Regole di business (`RB-…`, enunciate una sola volta qui), Criteri di accettazione (`AC-FNN-NN`).

**Regola DRY nel consumo**: ogni `RB-…`/`AC-…` è enunciato **una sola volta** alla sua fonte. Altrove l'AFU **cita l'ID**. Quando costruisci la matrice di verifica (§3.3), tratta ogni ID come **un solo requisito** anche se citato in più punti — non generare righe duplicate per lo stesso ID.

**Baseline legale (§3 dell'AFU)**: se front-matter/manifest riportano `legal_baseline.applicable: true`, leggi gli item di §3 con il loro `status` (`included` / `already_present` / `scoped_out`). Gli item `included` sono requisiti a tutti gli effetti → una riga di matrice ciascuno. Gli item `already_present` e `scoped_out` NON generano task ma vanno elencati nell'Esito sintetico del PLAN come "coperti / fuori scope per decisione funzionale".

**Fallback AFU legacy (section-oriented)**: se l'AFU **non** ha front-matter YAML **oppure** manca la §6 indice di copertura (documento pre-redesign, organizzato per le 7 sezioni canoniche), degrada all'euristica storica: scansiona le sezioni canoniche e organizza i requisiti per funzionalità inferendole dal testo. Segnala in testa al PLAN: `NOTA: AFU in formato legacy section-oriented — nessun front-matter/§6, estrazione via euristica a sezioni.`

### 3.2 — Esplorazione dei codebase

Per ogni codebase fornito, analizza:
- **Struttura del progetto**: package, moduli, layer architetturali
- **Modello dati**: entità, DTO, migration, relazioni
- **API/Controller**: endpoint esposti, payload, validazioni
- **Servizi**: logica di business, workflow, macchine a stati
- **Repository**: query, viste, materializzazioni
- **Frontend** (se applicabile): componenti, routing, modelli, i18n, servizi
- **Configurazione**: properties, feature flag, sicurezza

**In `classic`** (default): usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase quando possibile (fan-out opportunistico, model-driven).

**In `deep`** (vedi "## Modalità di orchestrazione"): invoca il **Workflow tool** `name: sdlc-analyzer-gap`, passando `{repos, requirements (estratti in 3.1), profile, const, depth, max_concurrency, verifier_panel}`. Il workflow esegue il fan-out parallelo degli explorer `sdlc-codebase-explorer` — un explorer per repo, e in `depth: ultracode` un explorer per **repo × layer** (dati/API/servizi/repo/FE/config) per ridurre i falsi "Mancante" — con **barriera** prima della sintesi. Se il Workflow tool non è disponibile o fallisce, degrada a `classic` con banner **COPERTURA RIDOTTA**.

**Nota**: il codebase viene letto dalla repo del progetto (dove la skill e' invocata). Solo gli artefatti del Piano (report, piano implementazione) vengono scritti in `deloitte-profiles`.

### 3.3 — Confronto e classificazione gap

Per ogni funzionalità richiesta dall'AFU, confronta con il codice esistente e classifica:

| Stato | Significato |
|---|---|
| **Coperto** | Implementato correttamente, nessun gap |
| **Parziale** | Implementato in parte, manca qualcosa di specifico |
| **Mancante** | Non implementato, da sviluppare da zero |
| **Discrepanza** | Implementato ma diverso da quanto richiesto dall'AFU |
| **Da chiarire** | L'AFU è ambigua o il codice suggerisce un'interpretazione diversa |

Per ogni gap, documenta:
- **Cosa richiede l'AFU** (con riferimento a sezione/pagina del documento)
- **Cosa esiste nel codice** (con path esatti a file/classi/metodi)
- **Cosa manca o è diverso** (con dettaglio sufficiente per implementare)
- **Repository coinvolte** (usa le sigle fornite dall'utente)
- **Complessità stimata** (Bassa / Media / Alta)
- **ID AFU coperti**: elenca gli ID `F-NN` / `RB-…` / `AC-…` che la riga indirizza (solo AFU feature-first). Ogni riga della matrice cita l'ID stabile per tracciabilità con `sdlc-updater` (delta su ID). Se AFU legacy, lascia la colonna vuota.

Il livello di dettaglio deve essere sufficiente perché un agente Claude Code, leggendo solo il gap report, possa capire esattamente cosa va fatto senza dover rileggere l'AFU originale.

**In `deep`**: parti dal `matrix_draft` restituito dal Workflow tool `sdlc-analyzer-gap` e raffinalo prima di scrivere il report:
- **completeness-critic**: per ogni requisito in `completeness.orphan_requirements` aggiungi la riga mancante (nessun requisito AFU orfano); valuta `completeness.extra_rows`.
- **adversarial-verify**: per ogni voce in `adversarial`, se `status_riconciliato` ≠ `status_originale` adotta lo stato riconciliato (maggioranza semplice >1/2 dei voti; in pareggio → `Da chiarire`) e cita le `controprove` nelle colonne Evidenze/Gap.
- **barriera parziale (§8.2)**: se `meta_run.explore_ok < meta_run.explore_units` (o `partial: true`), alcuni explorer sono falliti — tratta l'output come *proposta non applicata*: presenta lo stato parziale, **non scrivere** finché l'utente non conferma, e aggiungi in testa al PLAN il banner **COPERTURA RIDOTTA**.

La **sintesi finale e la scrittura del report restano dell'agente principale** (single-writer): il workflow propone, tu decidi e scrivi.

---

## Fase 4 — Generazione Output

Se la cartella del Piano non esiste ancora (sdlc-reviewer non eseguito), creala:

```bash
mkdir -p "$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/requirements"
```

Se il Piano richiede una o più **API di comunicazione FE↔BE** (euristica: un requisito la cui Area coinvolge sia BE sia FE, o un endpoint esposto dal BE e consumato dal FE), genera **anche** `CONTRACTS.md` nella cartella del Piano (contratto a monte, vedi §4.1/§4.2 e i Principi). Se nessuna API FE↔BE è richiesta, non creare il file.

(in-progress e done sono già create da sdlc-profile-setup)

Genera entrambi i file nella cartella del Piano in `$BASE_PATH/todo/`. Questo e' lo stato iniziale: la cartella intera si sposta in `in-progress/` quando uno sviluppatore avvia la lavorazione con `sdlc-executor`, e in `done/` al completamento di tutte le task.

**In `deep`** — banner e judge-panel (vedi "## Modalità di orchestrazione"):
- Mostra il banner di modalità all'avvio del lavoro pesante. Se hai dovuto degradare a `classic` (Workflow tool assente o fallito), scrivi in testa al PLAN il banner **"COPERTURA RIDOTTA — prodotto senza completeness-critic/adversarial-verify"**: gli artefatti `classic` e `deep` non sono equivalenti, la degradazione è rumorosa.
- Dopo aver scritto il TASKS (4.2), esegui un **judge-panel** sulle task — auto-sufficienza di ogni task, granularità 1–5 gg, correttezza delle merge task `T-MERGE-NNN` e delle dipendenze: lancia `verifier_panel` verifiche scettiche (Task con prompt da `${CLAUDE_PLUGIN_ROOT}/agents/sdlc-verifier.md` adattato al planning) e correggi le task segnalate **prima** del commit. In `classic` questo passo non viene eseguito. In *testability-first* il panel verifica anche l'auto-testabilità di ogni task (non solo il range 1–5 gg); in *parallelization-first* verifica il floor minimo di verificabilità oltre alla correttezza delle merge task.

### 4.1 — PLAN

**Path file**: `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/PLAN.md`

Struttura:

```
# Report Verifica AFU [nome/versione]

Data verifica: `<data>`
Modalita': `standalone` | `legacy`
Data inizio ufficiale: `<START_DATE o "non fornita">`
Deadline: `<DEADLINE o "non fornita">`
Processed AFU version: `<manifest.versione>`            # SOLO standalone — letto da requirements/afu-manifest.json
AFU manifest: `requirements/afu-manifest.json`          # SOLO standalone
Test playbook: `tests/playbook.md` + `tests/playbook.xlsx`   # SOLO standalone se manifest.tests presente

Branch verificato:
[per ogni repo coinvolta:]
- <SIGLA>: `<branch>`

Perimetro documentale verificato:
- AFU: `<path>`
- Mockup: `<path>`
[altri documenti]

Codebase verificati:
[per ogni repo coinvolta:]
- <SIGLA> (<nome completo>): `<path>`

## Assunzioni da review

[Se sdlc-reviewer non e' stato eseguito:]
Nessuna review preventiva eseguita.

[Se sdlc-reviewer eseguito ma sdlc-clarify NON eseguito:]
Assunzioni confermate dall'utente: [lista A-XXX dal CLARIFY.md]
Bloccanti aperti: [lista dal CLARIFY.md, segnalati come "Da chiarire" nei gap]

[Se sdlc-clarify e' stato eseguito:]
Bloccanti risolti (risposte del funzionale, usate come fatti nell'analisi):
- [B1] [Titolo] → [sintesi risposta]
[...]

Bloccanti ancora aperti (segnalati come "Da chiarire" nei gap):
- [BN] [Titolo]
[...]

Assunzioni confermate dal funzionale (usate come fatti): A-001, A-003
Assunzioni rigettate dal funzionale (usata la risposta al posto dell'assunzione):
- A-005: "[risposta corretta del funzionale]"
[...]
Assunzioni adottate senza risposta (usate con rischio segnalato): A-002, A-004

## Esito sintetico

[2-3 frasi che riassumono lo stato complessivo: cosa e' coperto, dove sono i gap principali]

## Matrice di verifica

Genera dinamicamente una colonna per ogni repository coinvolta, usando le sigle fornite dall'utente.

| Requisito | ID AFU | <SIGLA_1> | <SIGLA_2> | ... <SIGLA_N> | Stato | Evidenze | Gap |
|---|---|---|---|---|---|---|---|
| [Requisito dall'AFU] | [F-NN / RB-… / AC-… o "—" se legacy] | [Implementato/Non implementato/N/A] | [Implementato/Non implementato/N/A] | ... | [Coperto/Parziale/Mancante/Discrepanza/Da chiarire] | [Path esatti a file e classi rilevanti, per ogni repo] | [Descrizione precisa del gap, o "Nessuno"] |

[Una riga per ogni requisito identificato, raggruppate per funzionalità. Se il progetto ha una sola repo, la matrice avrà una sola colonna repo.]

## Gap aperti reali

### 1. [Nome gap]

[Dettaglio completo del gap:]
- Cosa richiede l'AFU
- Cosa esiste nel codice (con path)
- Cosa manca
- Impatto su quali moduli

### 2. [Nome gap]
[...]

## Conclusione finale

[Riepilogo: cosa è coperto, cosa è mancante, cosa è da chiarire.
 Organizzato per funzionalità, con lo stato di ognuna.]

## Contratti API FE↔BE

[SOLO se il Piano richiede API FE↔BE; altrimenti OMETTI. Indice dei contratti definiti in `CONTRACTS.md`.]

| ID Contratto | Endpoint + Metodo | Repo coinvolte | Task-contratto |
|---|---|---|---|
| `C-01` | `POST /api/...` | BE, FE | `T-00X` (Wave 0) |

Dettaglio completo (request/response schema, codici errore, auth/headers) in `CONTRACTS.md`.

## Violazioni principi CONST rilevate

Elenco dei punti in cui il codebase corrente NON rispetta i principi dichiarati in `CONST.json`. Sono finding informativi (non blocking — il piano va avanti comunque), ma vanno mostrati al team funzionale e di sviluppo perché documentano gap di conformità da chiudere nel medio termine.

Formato di ogni finding:
- **Principio violato:** `<categoria.regola>` (es. `quality_standards.test_coverage.minimum_percent`)
- **Dove:** `<repo>/<path>:<linea>` o `<repo>/<modulo>` se diffuso
- **Evidenza:** snippet di codice o metrica osservata
- **Impatto sul Piano corrente:** `BLOCCA il task X` | `Da fixare in coda al Piano` | `Solo segnalazione (gap pregresso)`

Se nessuna violazione è stata rilevata, lascia la sezione vuota con il testo: "Nessuna violazione dei principi CONST rilevata durante l'analisi."
```

Ogni riga della matrice e ogni gap aperto deve contenere path esatti ai file rilevanti, in modo che gli agenti Claude Code possano navigare direttamente al codice interessato.

### 4.2 — TASKS

**Path file**: `$BASE_PATH/todo/<YYYY-MM-DD>_<nome>/TASKS.md`

Struttura:

```
# Piano Implementazione [Nome feature/AFU]

Data: `<data>`

Assunzioni:
- [contesto, cosa e' gia' completato, perimetro residuo]
- [se sdlc-reviewer e' stato eseguito, includi qui tutte le assunzioni confermate dalla review, con riferimento al CLARIFY.md]
- team disponibile:
  - [per ogni sviluppatore: ruolo e seniority]
- Strategia di decomposizione: `<DECOMP_MODE>` (testability-first | parallelization-first)

## Obiettivo

[1-2 frasi coerenti con `DECOMP_MODE`: in *testability-first* enfatizza task auto-verificabili e parallelismo a parità di testabilità; in *parallelization-first* enfatizza il massimo parallelismo/fan-out. Cita esplicitamente la modalità scelta.]

## Strategia di esecuzione

[Come è diviso il lavoro: fondazioni, stream paralleli, integrazione.
 Quali sono i punti di congelamento iniziali che bloccano tutto il resto.]

## Distribuzione team consigliata

[Per ogni sviluppatore, descrivere il tipo di lavoro assegnato,
 tenendo conto della seniority reale:
 - Senior: governance, design, review, pairing, sblocco
 - Mid: stream core a media-alta complessità
 - Junior: stream guidati, scope ben chiuso, con review frequente]

## Definizione degli Stream

Ogni stream rappresenta un flusso di lavoro funzionalmente coeso: un insieme di task che appartengono alla stessa area funzionale e lavorano sullo stesso branch o su branch sequenziali. Le task all'interno dello stesso stream condividono il contesto di codice — il completamento di una rende il codice disponibile localmente per la successiva senza bisogno di merge.

Definisci gli stream basandoti sulle funzionalità dell'AFU, non sulla struttura tecnica. Esempi:
- `stream-booking` — tutte le task relative alla funzionalità Booking
- `stream-monitoraggio` — tutte le task relative al Monitoraggio
- `stream-fondazioni` — task di base che creano entità/enum/migration condivise

Regole:
- Uno stream può avere più owner (es. task BE e FE della stessa funzionalità)
- Un owner può lavorare su più stream
- Le task di Wave 0 (fondazioni) vanno tipicamente in uno stream dedicato `stream-fondazioni`
- Lo stream è un campo organizzativo per raggruppare le task — NON ha ruolo nella logica di sblocco delle dipendenze dell'executor

**Dipendenze cross-stream e merge task automatici**: quando una task in uno stream dipende da una task in un altro stream, sdlc-analyzer inserisce automaticamente una **merge task** tra le due. La merge task rappresenta l'atto di mergiare il branch dello stream sorgente nel branch base condiviso. Questo rende esplicita la dipendenza: l'executor non deve conoscere la logica degli stream — tutte le dipendenze si sbloccano semplicemente quando lo stato è "Completata". All'interno dello stesso stream, le dipendenze dirette sono sufficienti e non serve alcuna merge task.

[Lista degli stream identificati con descrizione, es:]
- `stream-fondazioni` — entità, enum, migration condivise
- `stream-booking` — funzionalità di gestione booking
- `stream-monitoraggio` — dashboard e pratiche monitoraggio
[...]

## Backlog operativo

| ID | Stream | Owner | Area | Branch | Priorità | Attività | Descrizione | Dipendenze | Effort |
|---|---|---|---|---|---:|---|---|---|---:|
| `T-001` | `stream-fondazioni` | `[Dev]` | BE/FE | `feature/<piano-name>-<slug>` | P0/P1/P2 | [Nome task] | [Descrizione dettagliata, con riferimento ai gap del report, file da toccare, pattern da seguire] | [ID dipendenze o "Nessuna"] | `N gg` |

[Una riga per ogni task]

**Nota sulle merge task**: le task di tipo merge usano il formato ID `T-MERGE-NNN` (dove NNN è l'ID numerico della task sorgente che viene mergiata, es. `T-MERGE-005`). Hanno type "merge", effort ~0.5gg, e la descrizione specifica quale branch mergiare, in quale branch base, e di verificare la build dopo il merge.

## Ordine di esecuzione

### Wave 0 — Fondazioni (`stream-fondazioni`)
- [task fondazionali che sbloccano tutto il resto]

### Merge tasks (tra wave)
- [merge task generate automaticamente per dipendenze cross-stream, es. T-MERGE-005]

### Wave 1
- [Per ogni stream attivo in questa wave, lista task]

### Wave 2
[...]

### Wave N — Integrazione e UAT
[Con contratto API congelato a monte (vedi Contract-first), questa wave NON riconcilia FE/BE ex-post: diventa un **conformance-check** (verifica che FE e BE rispettino esattamente `CONTRACTS.md`: schema request/response, codici errore) **+ UAT**. Mantiene il checkpoint end-to-end ma con effort ridotto.]

## Dipendenze critiche

- [lista delle dipendenze che possono creare colli di bottiglia]

## Piano per persona

### [Nome/ID sviluppatore]
- [lista task assegnate in ordine]
- [note su pairing, review, supporto]

[Ripeti per ogni sviluppatore]

## Stima complessiva

### Effort
[per ogni repository/area coinvolta:]
- <SIGLA>: circa `N gg/uomo`
- Integrazione e UAT: circa `N gg/uomo` (ridotto se contract-first attivo: solo conformance-check + UAT)

### Durata calendario realistica
[Scenario realistico settimana per settimana]
[Scenario aggressivo con rischi]

### Cadenza verso la deadline

[SOLO se `START_DATE` e `DEADLINE` sono presenti; altrimenti OMETTI questa sezione.]

- Giorni lavorativi disponibili (weekend esclusi) tra `START_DATE` e `DEADLINE`: `N`
- Cadenza richiesta: `<effort_totale_gg>/N` = **`X gg-effort/giorno`** (primaria) · **`Y task/giorno`** (secondaria = `<num_task>/N`)
- Capacità del team: `<somma capacità dev>` gg-effort/giorno → confronto: `[sufficiente | insufficiente di Z gg-effort/giorno]`
- Baseline cumulativa attesa (curva di completamento pianificata): in `classic`, lineare — `effort_atteso(d) = effort_totale * giorni_lavorativi_trascorsi(d) / N`. In `deep` o quando esiste un ESTIMATE dell'`sdlc-estimator`, usa una baseline wave/dipendenza-aware riusando la logica di `sdlc-estimation-scenario` e **indica quale baseline** è stata usata.

> Questa baseline è la fonte che `sdlc-progress-report` legge per calcolare anticipo/ritardo (WS2).

## Rischi principali

- [rischi tecnici, organizzativi, di scope]

## Raccomandazioni operative

- [consigli pratici per l'esecuzione]

## Deliverable minimi

- [lista di cosa deve funzionare per considerare il perimetro chiuso]
```

### 4.3 — Commit e push degli artefatti del Piano

Dopo aver generato `PLAN.md` e `TASKS.md`, esegui commit e push verso `deloitte-profiles`:

```bash
git -C "$GIT_REPO_PATH" add "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-analyzer] <nome>: gap report e piano di implementazione"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

### Perimetro dell'auto-update

**L'auto-update riguarda esclusivamente `PROFILE.json`.**

I principi di `CONST.json` sono policy stabili, gestite manualmente dall'utente. Non vanno mai modificati in automatico dall'analisi del codebase.

Se durante l'analisi rilevi che un principio CONST non è rispettato dal codice esistente (es. test coverage < soglia minima dichiarata, log con PII, funzioni > max_function_lines, endpoint senza validazione), **segnalalo come finding nel `PLAN.md` sotto la sezione "Violazioni principi CONST rilevate"**, NON modificare `CONST.json`.

### Principi per la creazione delle task

Quando scomponi il lavoro in task, questi principi guidano le decisioni:

**Organizzazione in stream** — Raggruppa le task in stream funzionali coesi (es. `stream-booking`, `stream-monitoraggio`). Le task nello stesso stream condividono il contesto di codice e possono dipendere direttamente tra loro. Per le dipendenze cross-stream, inserisci sempre una merge task esplicita tra la task sorgente e quella dipendente.

**Merge task per dipendenze cross-stream** — Quando una task in stream-X dipende da una task in stream-Y, sdlc-analyzer DEVE inserire una merge task tra di esse (es. `T-005` in `stream-fondazioni` -> `T-MERGE-005` -> `T-010` in `stream-booking`). La merge task:
- Appartiene allo stream sorgente (stream-Y)
- Ha come owner suggerito lo sviluppatore che ha completato la task sorgente
- Ha effort ~0.5gg e type "merge"
- La descrizione specifica: quale branch mergiare (`feature/<task-name>`), in quale branch base, verificare la build dopo il merge
- All'interno dello stesso stream non serve alcuna merge task — la dipendenza diretta è sufficiente
- Le merge task si collocano tipicamente tra le wave, fungendo da punto di sincronizzazione

**Indipendenza massima** — Ogni task deve poter essere sviluppata in parallelo. Se due task condividono una dipendenza (es. una nuova entità DB), la task che crea la dipendenza va nella wave precedente e deve essere completata prima. Minimizza le dipendenze cross-stream: le fondazioni condivise vanno in `stream-fondazioni` completato e mergiato prima che gli altri stream inizino.

**Assegnazione per competenza e seniority** — Assegna le task agli sviluppatori in base alla loro area di competenza e alla repository coinvolta. Task complesse o architetturali ai senior/mid. Task ripetitive o con scope ben chiuso ai junior, sempre con review assegnata. I senior non vanno caricati di implementazione continua: il loro valore è nel design, review, e sblocco tecnico.

**Granularità giusta** — Ogni task deve essere completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala con task correlate.

**Bilanciamento per modalità di decomposizione** — Pesa i principi sopra secondo `DECOMP_MODE`:
- *testability-first* (default): la testabilità domina. Ogni task espone criteri di completamento auto-verificabili dallo sviluppatore che la lavora (e, dove ha senso, il proprio test). Preferisci task più grandi (cap verso 3-5 gg) e meno merge task quando questo le rende verificabili in isolamento; massimizza comunque il parallelismo a parità di testabilità.
- *parallelization-first*: la parallelizzazione domina. Split atomico aggressivo (anche <1 gg) quando aumenta il fan-out, con più merge task cross-stream; è accettabile che una task sia meno comprensibile/testabile in isolamento, ma mantieni sempre un **floor minimo di verificabilità** (criteri di completamento oggettivi) — mai task non verificabili del tutto.

**Branch convention** — Ogni task ha un branch specificato nella colonna **Branch** del backlog. Il naming segue il pattern `feature/<piano-name>-<slug-attivita>` (es. `feature/monitoring-enum-entities-core`). Per task multi-repo (Area = BE+FE), lo stesso nome branch viene usato in tutte le repo coinvolte. Per le merge task (T-MERGE-*), la colonna Branch e' `—` (non hanno un branch proprio). Specifica l'ordine di merge basato sulle dipendenze.

**Autosufficiente per Claude Code** — Ogni task deve contenere abbastanza contesto perché un agente Claude Code possa implementarla leggendo solo la task e il gap report. Includi: file esatti da modificare/creare, pattern del progetto da seguire, criteri di completamento verificabili, e note specifiche (convenzioni, attenzioni, edge case).

**Contract-first per API FE↔BE** — Quando un requisito richiede un'API tra FE e BE (Area = BE+FE sullo stesso requisito, o endpoint BE consumato dal FE), genera una **task-contratto P0** in Wave 0 / `stream-fondazioni` che scrive e **congela** il contratto in `CONTRACTS.md` (endpoint+metodo, schema request, schema response, codici errore, auth/headers, repo coinvolte, ID `C-NN`). Le task FE e BE della stessa API **dipendono** dalla task-contratto e ne **citano l'ID** (`C-NN`) nella Descrizione (nessuna nuova colonna nel backlog). Così FE e BE implementano contro la stessa reference e la wave finale è un conformance-check invece di una riconciliazione ex-post. Il contratto è single-writer (lo scrive l'analyzer in fase di plan). Se durante l'esecuzione emerge la necessità di cambiarlo, la modifica passa da `sdlc-updater` (vedi il suo tracking di `CONTRACTS.md`).

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (solo se sdlc-reviewer non e' stato eseguito)
- **`markitdown`** — per conversione PDF, PPTX, XLSX (solo se sdlc-reviewer non e' stato eseguito)
- **`sdlc-reviewer`** — (opzionale ma consigliato) se eseguito prima, sdlc-analyzer ne legge il CLARIFY.md e salta la conversione
