---
name: sdlc-debug
description: Gestisce i bug segnalati dai funzionali durante e dopo il testing di un Piano (ex Business Requirement, derivato da un'AFU). Importa bug da Excel o Jira, li collega alle task del piano, li assegna agli sviluppatori, esegue i fix con sottoagenti Claude e verifica in 3 fasi, gestisce la chiusura con validazione funzionale e il re-import iterativo. Supporta qualsiasi composizione di repository. Usa questa skill quando l'utente dice "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti", "lavora il bug", "fix il bug", "debug br", "debug Piano", "bug su Piano", "il funzionale ha testato", "bug confermati", "aggiorna i bug", o qualsiasi variazione che implichi la gestione di bug su un BR / AFU / Piano. Attivala anche quando l'utente menziona un file di segnalazioni o chiede di lavorare i defect.
---

# SDLC Debug — Gestione Bug da Testing Funzionale

Questa skill gestisce i bug segnalati dai funzionali durante e dopo il testing di un Piano (ex Business Requirement, derivato da un'AFU). Copre l'intero ciclo: importazione, analisi, fix con sottoagenti, verifica, chiusura con validazione funzionale, e re-import iterativo.

Il debug e' uno **stage parallelo**: coesiste con l'esecuzione delle task, non e' sequenziale.

```
stato_pipeline:  approved ──→ execute ──→ done
debug:           ─────────── debug_attivo ─────── debug chiuso
```

Il Piano passa a `done` solo quando tutte le task sono completate E tutti i bug sono chiusi.

---

## Risoluzione Path — deloitte-profiles

Tutte le operazioni sui file del Piano avvengono nella repo `deloitte-profiles`, non nella repo del codice.

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

**Lettura compatibile**: il file di configurazione locale può chiamarsi `.sdlc-local.json` (nuovo nome, raccomandato) oppure `.br-local.json` (nome legacy, ancora supportato). Cerca PRIMA `.sdlc-local.json`; se non esiste, fa fallback a `.br-local.json`. Se nessuno dei due esiste, chiedi all'utente come collegarsi al profilo (vedi sotto).

Se trovi solo `.br-local.json` (profilo legacy), emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

All'avvio, leggi il file (priorità `.sdlc-local.json`, fallback `.br-local.json`):

```bash
# Esempio con .br-local.json — equivalente per .sdlc-local.json
cat "$SDLC_CFG" 2>/dev/null
```

Estrai `profiles_repo`, `profilo`, `developer`.

Il **base path** per gli artefatti del Piano e': `<profiles_repo>/<profilo>/plans/`

### Se né `.sdlc-local.json` né `.br-local.json` esistono

Sei uno sviluppatore — per collegarti al profilo esistente:

> Nessun file di configurazione locale trovato (`.sdlc-local.json` né `.br-local.json` legacy). Per collegarti al profilo, ho bisogno di:
> 1. **Path del clone di deloitte-profiles**
> 2. **Nome del profilo**
> 3. **Il tuo nome**

Crea `.sdlc-local.json` (nuovo nome raccomandato) con:
```json
{
  "profilo": "<profilo>",
  "profiles_repo": "<path>",
  "developer": "<nome>"
}
```

### Sincronizzazione prima della lettura

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

### Read-first — changelog globale (#3)

Dopo il pull e **prima** di aprire i file per-piano, consulta `CHANGELOG.md` (root della repo specifiche/profilo, sibling di `plans/`) per il **contesto sulle modifiche recenti** al piano su cui stai lavorando i bug (contratto: [`../sdlc-executor/references/CHANGELOG-contract.md`](../sdlc-executor/references/CHANGELOG-contract.md)). Alla chiusura di un bug, appendi la voce `[BUG] <id> fixed` secondo il write-contract:

```bash
CHANGELOG_PATH="<profiles_repo>/<profilo>/CHANGELOG.md"
[ -f "$CHANGELOG_PATH" ] && grep -A5 '^## Attività' "$CHANGELOG_PATH"   # modifiche recenti
# alla chiusura bug (stessa disciplina single-writer: pull → helper → add → commit [sdlc-changelog] → push):
# python "${SCRIPTS}/changelog.py" add-activity --file "$CHANGELOG_PATH" --date "<YYYY-MM-DD>" \
#   --line "[BUG] <id> fixed — *plan: <plan>* — commit: \`<SIGLA@sha>\` — → PROGRESS"
```

### Commit e push dopo la scrittura

```bash
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "<messaggio>"
git -C "<profiles_repo>" push origin main --quiet
```

---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path (`profiles_repo`, `profilo`) e prima di eseguire qualsiasi altra fase, carica i due file di costituzione del progetto:

```bash
git -C "<profiles_repo>" pull origin main --quiet
cat "<profiles_repo>/<profilo>/constitution/CONST.json"
cat "<profiles_repo>/<profilo>/constitution/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| Né `.sdlc-local.json` né `.br-local.json` (legacy) presenti | "Esegui prima `/sdlc-profile-setup`" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il profilo `<nome>` non ha CONST.json. Eseguire `python ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il profilo `<nome>` non ha PROFILE.json. Stato inconsistente — il profilo è incompleto. Ripristinare da git history o rifare il setup." | Stop |
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
| `adversarial-verify` / `judge-panel` | singola verifica `sdlc-work-verifier` inline |
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

## Caricamento Profilo Progetto

Dopo aver risolto i path (vedi sezione "Risoluzione Path"), se il profilo è disponibile:

1. Carica CONST.json + PROFILE.json secondo la sezione "Caricamento contesto progetto"
2. Se il campo `custom_agents` è presente, leggi i file .md degli agenti referenziati (path relativi a `<profiles_repo>/<profilo>/agents/`)
3. Salva il profilo in memoria per uso nelle fasi successive

Quando il profilo è disponibile:
- Nella Fase 2, instrada i sottoagenti al subagent_type corretto in base allo stack del codebase coinvolto
- Nella Fase 2, usa sdlc-work-verifier per la verifica al posto della verifica inline
- Inietta convenzioni e dominio dal profilo nei prompt dei sottoagenti

---

## Rilevamento Modalita'

La skill rileva automaticamente la modalita' di funzionamento:

- **Import mode**: non esiste `BUG_REPORT.md` nella cartella del Piano, oppure l'utente dice "ci sono dei bug", "segnalazioni test", "defect ricevuti"
- **Execution mode**: esistono bug assegnati allo sviluppatore con stato diverso da `chiuso`, oppure l'utente dice "lavora il bug", "fix il bug"
- **Chiusura mode**: l'utente dice "il funzionale ha testato", "bug confermati", "aggiorna i bug"

---

## Ciclo di Vita del Bug

```
aperto → assegnato → in_corso → verificato → chiuso
                        ↓
                     bloccato
```

| Stato | Significato |
|---|---|
| `aperto` | Bug importato, non ancora assegnato |
| `assegnato` | Owner definito, non ancora in lavorazione |
| `in_corso` | Lo sviluppatore sta lavorando il fix |
| `verificato` | Fix implementato e verificato tecnicamente, in attesa di validazione funzionale |
| `chiuso` | Il funzionale conferma che il bug e' risolto |
| `bloccato` | Il fix e' bloccato da un impedimento |

### Severita'

| Livello | Significato |
|---|---|
| `critico` | Blocca l'uso della funzionalita' |
| `maggiore` | Funzionalita' degradata ma utilizzabile |
| `minore` | Difetto estetico o marginale |

Tutti i livelli seguono il ciclo di verifica completo (3 fasi).

---

## Fase 1 — Import dei Bug

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — Piano di riferimento

Cerca i Piani attivi:

```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/done"/*/ 2>/dev/null
```

Se ne trovi uno, proponilo. Se piu' di uno, chiedi quale. Se nessuno, avvisa che serve prima un TASKS.

### Domanda 2 — Sorgente dei bug

> Da dove arrivano i bug?
> 1. **File Excel** — dammi il path del file
> 2. **Jira** — mi collego al progetto e importo i ticket
> 3. **Entrambi** — prima importo da file, poi integro da Jira

### Import da Excel — Mapping intelligente

Leggi il file Excel con Python + openpyxl. Leggi la prima riga (header) e tenta un mapping automatico basato su pattern riconoscibili (case-insensitive, match parziale):

| Campo interno | Pattern riconosciuti |
|---|---|
| `id` | id, #, numero |
| `fase` | fase, fase processo, area, modulo |
| `sezione` | sezione, sotto-sezione, pagina |
| `utente` | utente, user, profilo, ruolo utente |
| `titolo` | titolo, problema riscontrato, summary, title |
| `descrizione` | descrizione, descrizione del problema, description |
| `screenshot` | screen, screenshot, allegati, immagini |
| `riferimento` | rif, rif. pratica, reference, ticket |
| `tipo` | tipo, tipo segnalazione, type, category |
| `origine` | origine, origin, source bug, fonte | **NUOVA (v2 Bug Excel template)** |
| `stato_originale` | stato, status |
| `data` | data, date, data segnalazione |
| `note_dev` | note team sviluppo, note dev, dev notes |
| `note_funzionale` | note team funzionale, note funzionali |

Se una colonna non viene mappata automaticamente, presentala all'utente e chiedi se e' rilevante. Le colonne non mappate vengono ignorate.

**Colonna `origine` (v2 template, da Fase 2c due ondate)**:

| Valore Excel | Significato | Default se assente |
|---|---|---|
| `tecnico` | Bug rilevato dai test tecnici automatici (unit/integration/perf/security) lanciati dal team tech in Fase 2c ondata (a). | (vedi default sotto) |
| `funzionale` | Bug rilevato dal team funzionale in autonomia eseguendo il playbook test (md/xlsx) in Fase 2c ondata (b). | (vedi default sotto) |

**Default retrocompat**: se la colonna `origine` e' **assente** nell'Excel (template v1 pre-Solaria), assumi `origine=tecnico` per tutti i bug. Comunica all'utente:

> Il file Excel non ha la colonna `origine` (formato v1). Tratto tutti i bug come `tecnico`. Per il nuovo template v2 (con colonna origine = tecnico|funzionale) vedi `${CLAUDE_PLUGIN_ROOT}/templates/BUG_EXCEL_TEMPLATE.xlsx`.

**Validazione**: se una riga ha `origine` con valore non in `{tecnico, funzionale}`, mostra errore e chiedi correzione (non default silenzioso — i valori invalidi sono probabilmente typo, meglio segnalarli).

Script per la lettura:

```python
import openpyxl

wb = openpyxl.load_workbook('<path_file>')
ws = wb[wb.sheetnames[0]]  # primo foglio = dati
headers = [cell.value for cell in ws[1]]
bugs = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] is None:
        continue
    bug = dict(zip(headers, row))
    bugs.append(bug)
```

**Mapping dei tipi segnalazione:**

| Tipo segnalazione (Excel) | Tipo (interno) | Severita' (default) |
|---|---|---|
| `DEFECT/BUG` | `bug` | `maggiore` |
| `MINOR` | `bug` | `minore` |
| `CAMBIO LABEL` | `label` | `minore` |
| `CR` | `change_request` | `minore` (fisso, non modificabile) |

Il mapping dei tipi e' flessibile — se il file usa termini diversi, la skill presenta i valori trovati e chiede la mappatura. Per i tipi riconosciuti, il TL/PM puo' cambiare la severita' in fase di conferma (tranne le CR che restano sempre `minore`).

**Filtro per stato:** importa solo i bug con stato diverso da "Chiuso":

> Il file contiene N segnalazioni.
> - X gia' chiuse (non importate)
> - Y aperte o in test → da importare
>
> Vuoi importare tutte le Y, oppure filtrare per tipo?

**Screenshot:** se il file ha un foglio "Screen" con immagini referenziate dalla colonna Screen, estrai le immagini e salvale nella cartella del Piano:

`<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/screenshots/` (o `plans/todo/` se non ancora in-progress)

### Import da Jira

Usa la skill `jira` (se disponibile) o l'MCP Jira se configurato. Chiedi:

1. **Progetto Jira** — o deducilo dall'AFU
2. **Filtro** — tipo = Bug, stato = Open/To Do, opzionalmente sprint o label

Per ogni ticket importato, mappa i campi Jira standard:

| Campo Jira | Campo interno |
|---|---|
| `key` | `id_originale` |
| `summary` | `titolo` |
| `description` | `descrizione` |
| `priority` | `severita` (Critical→critico, Major→maggiore, Minor/Trivial→minore) |
| `assignee` | `owner` (se corrisponde a un dev nel piano) |
| `labels` / `components` | `fase`, `sezione` (best effort) |
| `created` | `data_segnalazione` |

### Domanda 3 — Collegamento alle funzionalita'

Per ogni bug importato, tenta un collegamento automatico alle task/stream del piano:

1. Confronta il campo `fase` + `sezione` del bug con i nomi degli stream e le descrizioni delle task nel piano
2. Se il bug menziona un'area funzionale (es. "booking", "monitoraggio", "accesso"), collegalo allo stream corrispondente
3. Se trova un match con una task specifica, collegalo direttamente

Bug senza collegamento a task/stream vengono categorizzati sotto lo pseudo-stream `debug-generico`.

Presenta la lista all'utente per conferma e correzione:

> Bug importati: N
>
> | ID | Titolo | Tipo | Sev. | Collegato a | Owner suggerito |
> |---|---|---|---|---|---|
> | BUG-001 | Login fallisce con email maiuscola | bug | critico | T-012 (Auth login) | Marco (owner T-012) |
> | BUG-002 | Tabella non ordinabile | bug | maggiore | stream-monitoraggio | ? (nessun match) |
> | BUG-003 | Typo checkbox privacy | label | minore | T-008 (Pop-up info) | Luca (owner T-008) |
>
> Confermi i collegamenti? Per i bug senza match, a chi li assegno?

### Domanda 4 — Assegnazione

Per i bug con match: proponi l'owner della task collegata (default). Il TL/PM puo' riassegnare.
Per i bug senza match: chiedi esplicitamente a chi assegnare.

### Riepilogo e conferma

> Riepilogo import:
> - Sorgente: [Excel / Jira / entrambi]
> - Piano: [nome]
> - Bug importati: N (di cui X bug, Y label, Z CR)
> - Severita': A critici, B maggiori, C minori
> - Assegnati a: [lista sviluppatori con conteggio]
>
> Confermo?

Dopo la conferma, scrivi i bug nella source of truth.

### Scrittura BUG_REPORT.md

Crea `BUG_REPORT.md` nella cartella del Piano (es. `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/BUG_REPORT.md`). Usa il formato definito nella sezione "Struttura BUG_REPORT.md".

Dopo la scrittura, esegui commit + push su deloitte-profiles:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[sdlc-debug] <nome>: importati N bug da <sorgente>"
git -C "<profiles_repo>" push origin main --quiet
```

---

## Fase 2 — Esecuzione Fix

### Identificazione sviluppatore

Leggi `.br-local.json` per il nome dello sviluppatore (campo `developer`). Se non presente, chiedi chi e' lo sviluppatore, mostrando la lista dal piano.

### Selezione bug da lavorare

Filtra i bug assegnati allo sviluppatore con stato diverso da `chiuso` e `verificato`. Ordina per severita' (critico > maggiore > minore) e poi per tipo (bug > label > change_request). Le CR finiscono sempre in coda.

> I tuoi bug assegnati:
>
> | # | ID | Tipo | Sev. | Titolo | Fase > Sezione | Stato |
> |---|---|---|---|---|---|---|
> | 1 | BUG-003 | bug | critico | Login fallisce con email maiuscola | Accesso > Login | assegnato |
> | 2 | BUG-007 | bug | maggiore | Tabella non ordinabile | Dashboard > Pratiche | assegnato |
> | 3 | BUG-015 | label | minore | Typo checkbox privacy | Accesso > Pop-Up | assegnato |
>
> Vuoi procedere con **BUG-003**?

Aspetta la conferma prima di procedere.

### Raggruppamento bug minori

Per bug di tipo `label` o con severita' `minore` nella stessa sezione, proponi di raggrupparli:

> I bug BUG-015, BUG-016, BUG-017 sono tutti cambi label nella sezione "Pop-Up Informazioni Importanti".
> Vuoi lavorarli insieme su un unico branch `fix/<piano-name>-label-popup`?

Se confermato, lancia un sottoagente unico con tutti i bug del gruppo.

### Analisi del bug prima del fix

Prima di lanciare il sottoagente:

1. **Leggi la descrizione completa** del bug, inclusi tutti gli Update inline
2. **Leggi la task collegata** dal TASKS e dal PLAN per il contesto funzionale originale
3. **Localizza il codice coinvolto** — usa fase/sezione del bug e i file della task collegata. Se necessario, usa un agente `Explore` per trovare il codice rilevante nei codebase
4. **Leggi gli screenshot** se presenti
5. **Formula un'ipotesi di root cause** basata su descrizione + codice trovato

Presenta l'analisi allo sviluppatore:

> ## Analisi BUG-003 — Login fallisce con email maiuscola
>
> **Problema:** [riepilogo dalla descrizione]
> **Contesto funzionale:** [dalla task collegata T-012]
> **File probabilmente coinvolti:**
> - `src/auth/LoginService.java:42` — validazione email
> - `src/auth/UserRepository.java:78` — query lookup utente
>
> **Ipotesi root cause:** La query di lookup confronta l'email case-sensitive. Serve un confronto case-insensitive o una normalizzazione a lowercase.
>
> Procedo con il fix?

Aspetta la conferma.

### Creazione branch

Dopo la conferma, crea il branch in tutte le repo coinvolte:

1. **Determina il nome del branch:** `fix/<piano-name>-BUG-<NNN>-<slug>` (es. `fix/monitoring-BUG-003-table-sort`). Per bug raggruppati: `fix/<piano-name>-label-<sezione>`.

2. **Repo del piano** (la repo corrente):
   ```bash
   git checkout -b fix/<piano-name>-BUG-<NNN>-<slug>
   ```

3. **Per ogni altra repo coinvolta** (da `.br-local.json` o dai path forniti nella Fase 1 di sdlc-executor):
   ```bash
   git -C <path-repo-esterna> checkout -b fix/<piano-name>-BUG-<NNN>-<slug>
   ```

4. Aggiorna lo stato del bug a `in_corso` e il campo `branch`.

### Esecuzione con sottoagenti

**In `deep`** (vedi "## Modalità di orchestrazione"): per un batch di bug assegnati invoca il **Workflow tool** con `scriptPath: ${CLAUDE_PLUGIN_ROOT}/workflows/sdlc-debug-fixwave.js` con `{bugs (con `stack` per il routing), repos, profile, const, depth, verifier_panel}`. Il workflow fa root-cause read-only in parallelo, poi i fix in **worktree isolati** con routing per-stack, verifica ognuno con `sdlc-work-verifier` (panel adversariale in `ultracode`) e il loop fix→riverifica (`loop-until-dry`). Poi **tu** (single-writer): applica il `patch` dei bug `VERIFIED` uno alla volta (`git apply`), aggiorna `BUG_REPORT.md` (append, ID/counter), suggerisci i commit (mai automatici). Se `partial: true` / bug `NEEDS_ATTENTION` (§8.2): non applicare nulla, presenta lo stato e fai decidere l'utente; banner **COPERTURA RIDOTTA** se degradi a `classic`. La **validazione funzionale (Fase 3) resta umana**.

**In `classic`** (default): lavora i bug come descritto qui sotto (routing per-stack, verifica 3 fasi inline, una alla volta).

#### Routing a Specialist per Stack

**Se il profilo progetto e' disponibile**, determina il subagent_type in base al codebase coinvolto nel bug:

1. Identifica l'area del bug dalla colonna `fase`/`sezione` e dalla task collegata
2. Leggi `tech_stack.backend.framework` o `tech_stack.frontend.framework` dal profilo
3. Mappa al subagent_type:

| Stack (dal profilo) | subagent_type |
|---|---|
| Spring Boot | `spring-boot-engineer` |
| .NET Core | `csharp-developer` |
| Django | `django-developer` |
| FastAPI | `fastapi-developer` |
| Node.js / Express | `node-specialist` |
| Laravel | `laravel-specialist` |
| Angular | `angular-architect` |
| React | `react-specialist` |
| Vue | `vue-expert` |
| Next.js | `nextjs-developer` |
| Flutter | `flutter-expert` |
| Java (generico) | `java-architect` |
| Python (generico) | `python-pro` |
| Go | `golang-pro` |
| Rust | `rust-engineer` |
| Kotlin | `kotlin-specialist` |
| Swift | `swift-expert` |
| PHP | `php-pro` |
| (non riconosciuto/no profilo) | `general-purpose` (fallback) |

4. Lancia il sottoagente con `Agent(subagent_type: "<tipo>", prompt: "<prompt>")`
5. Se il profilo non e' disponibile, usa `general-purpose` (comportamento attuale)

Aggiungi al prompt del sottoagente il contesto dal profilo (convenzioni, test naming, package structure).

Lancia un sottoagente con prompt autosufficiente che include:

1. **Il bug** — descrizione completa, screenshot, utente impattato, ipotesi di root cause
2. **Il contesto** — task originale che ha implementato la funzionalita', file coinvolti, pattern del progetto
3. **L'ipotesi di root cause** — dove guardare, cosa potrebbe essere il problema
4. **Cosa deve fare:**
   - Implementare il fix
   - Scrivere un test che riproduce il bug (deve fallire PRIMA del fix se eseguito sul codice originale)
   - Scrivere un test che verifica il fix (deve passare DOPO)
   - Scrivere test di regressione (il comportamento corretto preesistente non e' rotto)
5. **Vincoli** — non rompere funzionalita' esistenti, seguire le convenzioni del progetto

Esempio di dispatch a un sottoagente:

```
Correggi il seguente bug nel codebase backend.

Codebase: <path locale>
Bug: BUG-003 — Login fallisce con email maiuscola

Descrizione del problema:
<descrizione completa dal bug>

Contesto:
- Questa funzionalita' e' stata implementata nella task T-012
- Il progetto usa Spring Boot con JPA/Hibernate
- I service seguono il pattern in <path>/service/
- [altri pattern osservati]

Ipotesi root cause:
La query di lookup in UserRepository confronta l'email case-sensitive.

File probabilmente coinvolti:
- <path>/service/LoginService.java
- <path>/repository/UserRepository.java

Cosa fare:
1. Scrivi un test che riproduce il bug: login con email "Mario@Example.com"
   deve funzionare come "mario@example.com"
2. Implementa il fix (normalizzazione email a lowercase)
3. Scrivi test di regressione: login con email corretta continua a funzionare

File di riferimento per le convenzioni:
- <path>/test/service/ExistingServiceTest.java
```

### Verifica in 3 fasi

Dopo che il sottoagente completa il fix, esegui la verifica in 3 fasi:

**Se il profilo progetto e' disponibile:**

Delega la verifica all'agente `sdlc-work-verifier` (leggendo le sue istruzioni da `${CLAUDE_PLUGIN_ROOT}/agents/sdlc-work-verifier.md`). Passa:
- Requisiti: descrizione del bug + ipotesi di root cause
- File modificati: lista dei file toccati dal sottoagente
- Risultati test: output dell'esecuzione test
- Convenzioni dal profilo: test_naming, base_entity, package_structure

Se il verifier restituisce FAIL, leggi i dettagli e lancia un sottoagente di correzione. Ripeti la verifica.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esegui la verifica inline in 3 fasi come segue:

**Fase A — Verifica tecnica**

1. **Esegui i test** — la suite completa deve passare con zero failure
2. **Verifica la build** — il progetto deve compilare senza errori
3. **Controlla i test scritti** — verifica che il sottoagente abbia scritto:
   - Test che riproduce il bug originale
   - Test che verifica il fix
   - Test di regressione
   - Se mancano, lancia un nuovo sottoagente per aggiungerli

**Fase B — Verifica di coerenza col bug**

Rileggi la descrizione del bug (inclusi tutti gli Update). Per OGNI aspetto del problema:

1. **E' stato risolto?** — il fix copre effettivamente il problema descritto
2. **Tutti gli scenari?** — se il bug ha piu' Update o casi d'uso, sono tutti coperti
3. **Effetti collaterali?** — il fix non introduce nuovi problemi

Se trovi discrepanze, lancia un sottoagente di correzione e ripeti la Fase B.

**Fase C — Riesame finale**

1. **Rileggere il codice del fix** — non fidarti del riepilogo del sottoagente
2. **Cercare regressioni** — il fix non rompe il comportamento corretto preesistente
3. **Verificare che i test testino realmente** — asserzioni specifiche e significative
4. **Controllare naming e convenzioni**

Se trovi problemi, correggi e ripeti la Fase C.

Solo quando TUTTE e 3 le fasi sono superate il fix e' verificato.

### Suggerimento commit

Mai committare autonomamente. Suggerisci per ogni repo coinvolta:

**Se il fix coinvolge solo la repo del piano:**

> Il fix per **BUG-003** e' completo e verificato:
> - [lista file creati/modificati]
> - Test: [N test, tutti verdi]
> - Build: compila
>
> Suggerisco:
> ```
> git add [file specifici]
> git commit -m "fix(<area>): <descrizione fix> (BUG-003)"
> ```
>
> Dopo il commit, pusha:
> ```
> git push origin fix/<piano-name>-BUG-003-<slug>
> ```

**Se il fix coinvolge piu' repo:**

Fornisci suggerimenti separati per ogni repo, come fa sdlc-executor.

Aspetta la conferma prima di proseguire.

### Completamento bug → stato `verificato`

Quando il fix e' implementato e verificato tecnicamente, presenta la tabella di verifica:

> ## Verifica completamento BUG-003
>
> | # | Aspetto | Verificato | Dettaglio |
> |---|---|---|---|
> | 1 | Bug riprodotto nel test | Si | `LoginServiceTest#shouldHandleCaseInsensitiveEmail` |
> | 2 | Fix implementato | Si | `LoginService.java:45` — normalizzazione toLowerCase |
> | 3 | Test di regressione | Si | `LoginServiceTest#shouldLoginWithValidEmail` — passa |
> | 4 | Build | Si | Compila senza errori |
>
> **Fix summary:** Normalizzazione email a lowercase prima del lookup nel DB.
>
> Il bug passa a stato **verificato**. Il funzionale dovra' confermare che il problema e' risolto.

Aggiorna lo stato del bug a `verificato`, il progresso a 100%, e compila il campo `fix_summary`.

Proponi il prossimo bug disponibile.

---

## Fase 3 — Chiusura e Re-import

### Chiusura da parte del funzionale

Tre flussi supportati:

**Flusso 1 — Excel aggiornato:**

Il funzionale aggiorna lo stesso file Excel cambiando lo stato a "Chiuso" o riapre il bug. La skill rileva i delta:

1. Leggi il file aggiornato con openpyxl
2. Per ogni riga, confronta lo stato con quello attuale dei bug (match per `id_originale`)
3. Presenta i delta:

> Ho confrontato il file aggiornato con lo stato attuale dei bug.
>
> | ID | Stato precedente | Stato nuovo | Note funzionale |
> |---|---|---|---|
> | BUG-003 | verificato | Chiuso | OK, funziona |
> | BUG-007 | verificato | Aperto | Il problema persiste con dati paginati |
> | BUG-015 | verificato | Chiuso | — |
>
> - 2 bug confermati chiusi
> - 1 bug riaperto con nuova nota
>
> Confermo gli aggiornamenti?

**Flusso 2 — Jira:**

Se l'import originale era da Jira, rileggi lo stato dei ticket per sincronizzare. Ticket chiusi → bug chiuso. Ticket riaperti → bug riaperto con commento Jira come nota.

**Flusso 3 — Conversazione:**

L'utente riporta a voce. Chiedi conferma bug per bug prima di aggiornare.

### Bug riaperti

Quando un bug torna da `verificato` a `aperto`:

1. Lo stato torna a `aperto`
2. La nota del funzionale viene aggiunta al campo `note_funzionale`
3. La descrizione viene preservata con append: `[Riapertura <data>]: <nota del funzionale>`
4. Il branch precedente viene riutilizzato se esiste ancora, oppure ne viene creato uno nuovo
5. Il `fix_summary` precedente viene preservato con prefisso `[Fix precedente]: `
6. Il progresso torna a 0%

### Re-import iterativo

La skill puo' essere invocata piu' volte sullo stesso Piano. A ogni invocazione:

- Bug gia' importati (match per `id_originale`) non vengono duplicati
- Nuovi bug nel file/Jira vengono aggiunti con ID sequenziale dal prossimo disponibile (es. se l'ultimo e' BUG-033, il prossimo e' BUG-034)
- Bug con stato cambiato vengono sincronizzati (se la direzione e' chiusura o riapertura)
- Presenta sempre il delta prima di applicare:

> Re-import dal file aggiornato:
> - 5 nuovi bug da importare (BUG-034 → BUG-038)
> - 3 bug con stato aggiornato (chiusi dal funzionale)
> - 25 invariati
>
> Confermo?

### Condizione di completamento debug

Quando tutti i bug hanno stato `chiuso`, aggiungi la sezione "Debug Completato" al `BUG_REPORT.md`:

```markdown
## Debug Completato

Data chiusura: <data>
Bug totali: N
Bug risolti: N
```

Dopo la scrittura, esegui commit + push:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[sdlc-debug] <nome>: debug completato (N bug risolti)"
git -C "<profiles_repo>" push origin main --quiet
```

Se il Piano e' in stato `execute` e tutte le task E tutti i bug sono completati, il Piano puo' passare a `done`.

---

## Struttura BUG_REPORT.md

Questo e' il formato canonico del file BUG_REPORT.md:

```markdown
# Bug Report — <nome Piano>

Data import: <data>
Sorgente: <file/jira/entrambi>
Ultimo aggiornamento: <data e ora>

## Riepilogo

| Metrica | Valore |
|---|---|
| Bug totali | N |
| Aperti | X |
| In corso | Y |
| Verificati | Z |
| Chiusi | W |
| Bloccati | K |

## Lista Bug

**In modalita' standalone (v2 template con colonna `origine`)**: emetti **due sezioni separate** per facilitare conteggio e gating chiusura. In modalita' legacy (no colonna origine): sezione unica come oggi.

### Bug tecnici (origine=tecnico)

| ID | Tipo | Sev. | Fase | Sezione | Titolo | Owner | Stato | Task | Branch |
|---|---|---|---|---|---|---|---|---|---|
| BUG-001 | bug | maggiore | Dashboard | Tabella Pratiche | ... | Marco | assegnato | T-012 | — |

### Bug funzionali (origine=funzionale)

| ID | Tipo | Sev. | Fase | Sezione | Titolo | Owner | Stato | Task | Branch |
|---|---|---|---|---|---|---|---|---|---|
| BUG-042 | bug | minore | Booking | Conferma | ... | Anna | assegnato | T-018 | — |

**Counter per chiusura plan** (consumati da `sdlc-executor` check automatico):
- `bug_tecnici_aperti`: <N>
- `bug_funzionali_aperti`: <M>
- Condizione chiusura standalone: entrambi = 0
- Condizione chiusura legacy: somma totale `bug_aperti` = 0 (counter unico, retrocompat)

## Dettaglio Bug

### BUG-001 — <titolo>

- **Tipo**: <tipo> | **Severita'**: <severita> | **Origine**: <origine>
- **Fase**: <fase> > <sezione>
- **Utente**: <utente>
- **Task collegata**: <task_collegata>
- **Owner**: <owner>
- **Stato**: <stato>

**Descrizione:**
<descrizione completa>

**Screenshot:** <link o "—">
**Note dev:** <note_dev o "—">
**Note funzionale:** <note_funzionale o "—">
**Fix summary:** <fix_summary o "—">

---

[ripetere per ogni bug]

## Log Attivita'

### <data>
- <evento>
```

---

## Regole Fondamentali

1. **Mai committare autonomamente** nel codebase del progetto — suggerisci e aspetta conferma. Committare autonomamente solo nella repo `deloitte-profiles` (BUG_REPORT, progresso).
2. **Mai procedere senza conferma** — tra un bug e l'altro, prima di ogni modifica alla source of truth.
3. **Verificare prima di dichiarare verificato** — tutte e 3 le fasi complete per ogni bug.
4. **Mai duplicare bug al re-import** — confronta sempre per `id_originale`.
5. **Mai sovrascrivere note precedenti** — append, non replace.
6. **Il sottoagente implementa, l'agente principale coordina** — non implementare codice direttamente.
7. **Le CR hanno sempre severita' minore** — non modificabile.

---

## Dipendenze

| Dipendenza | Usata per | Installazione |
|---|---|---|
| `openpyxl` (Python) | Lettura/scrittura Excel | `pip install openpyxl` |
| skill `jira` | Import da Jira (opzionale) | gia' nell'ecosistema |

## Context

This is one of the skills in the SDLC lifecycle suite (BR / AFU / Piano workflow). The other skills are:
- sdlc-reviewer: reviews functional documentation quality
- sdlc-clarify: manages functional team responses to review questions
- sdlc-analyzer: gap analysis between AFU docs and codebase
- sdlc-executor: executes implementation tasks from the plan
- sdlc-updater: updates plan when AFU documentation changes
- sdlc-progress-report: generates Excel progress reports

sdlc-debug fits as a PARALLEL stage alongside sdlc-executor. It uses the same patterns: subagent delegation, 3-phase verification, progress tracking.

All Plan artifacts (TASKS.md, PLAN.md, PROGRESS.md, BUG_REPORT.md, screenshots) live centrally in `<profiles_repo>/<profilo>/plans/`, not in the code repository. `BUG_REPORT.md` is the source of truth for bugs.
