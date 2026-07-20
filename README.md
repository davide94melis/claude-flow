# Claude Flow — BR Skills per Claude Code

Suite di 10 skill e 5 agenti generici per Claude Code che automatizzano il ciclo di vita dei Business Requirements: dalla review della documentazione funzionale alla gestione delle risposte del funzionale, dall'analisi gap all'esecuzione task, dalla gestione dei bug segnalati dai funzionali all'aggiornamento incrementale e al reporting Excel, con un orchestratore pipeline che coordina il tutto. Include profili progetto centralizzati per scalare a tutti i progetti.

## Skills

### sdlc-reviewer

Verifica la qualità, coerenza e completezza della documentazione funzionale di un BR *prima* dell'analisi tecnica. Produce un report duale:
- **Parte 1 — Per il team funzionale**: problemi da chiarire (bloccanti e non), con domande precise
- **Parte 2 — Per il team tecnico**: assunzioni di default e disallineamenti col codice

Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali.

Genera anche un DOCX con placeholder per le risposte, pronto per essere inviato al team funzionale.

**Trigger**: `rivedi il br`, `review del br`, `controlla la documentazione`, `verifica il br`

### sdlc-clarify

Gestisce le risposte del team funzionale alle domande sollevate nel review. Supporta due modalita di input:
- **DOCX compilato**: il funzionale compila il CLARIFY.docx e lo restituisce
- **Conversazione**: l'utente riporta le risposte a voce

Aggiorna il CLARIFY.md con le risposte, ri-valuta bloccanti e assunzioni, e rigenera il DOCX. Può essere eseguita più volte per risposte parziali.

**Trigger**: `chiarimenti ricevuti`, `risposte ricevute`, `il funzionale ha risposto`, `ho le risposte`

### sdlc-analyzer

Analizza un nuovo Business Requirement confrontandolo con i codebase esistenti (BE, FE, Document Manager, Email Manager). Genera:
- **Gap Report** dettagliato per funzionalità
- **Piano di Implementazione** con task indipendenti assegnate a sviluppatori

**Trigger**: `abbiamo un nuovo br`, `analizza il br`, `gap analysis br`

### sdlc-executor

Esegue i task dal piano generato da `sdlc-analyzer`. Ogni sviluppatore usa questa skill per:
- Lavorare le proprie task assegnate in ordine di priorita e dipendenze
- Delegare l'implementazione a sottoagenti Claude Code
- **Verifica in 3 fasi** dopo ogni sotto-step:
  - **Fase A -- Tecnica**: test tutti verdi (happy path + edge case + error case), build compila
  - **Fase B -- Coerenza**: ogni requisito verificato contro il codice prodotto
  - **Fase C -- Riesame**: second look critico sul codice, asserzioni dei test, naming
- **Ciclo di verifica finale**: tabella di tracciabilita requisiti -> implementazione -> test prima di dichiarare completa
- Creare branch in tutte le repo coinvolte (non solo quella del piano)
- Verificare le dipendenze con aggregazione cross-branch (vede il progresso di tutti i developer)
- Tracciare il progresso in un file condiviso

La task NON e completa finche tutti i requisiti non sono implementati, testati (con edge case) e il ciclo di verifica non e superato.

**Trigger**: `lavora il task`, `inizia a lavorare`, `esegui il piano`

### sdlc-updater

Aggiorna gap report e piano quando il BR o la documentazione cambia. Confronta la nuova documentazione con quella precedente, identifica i delta e aggiorna i file preservando il progresso delle task già completate o in corso.

**Trigger**: `il br e stato aggiornato`, `aggiorna il piano`, `nuova versione del br`

### sdlc-progress-report

Genera o aggiorna un file Excel (`.xlsx`) con il riepilogo completo delle task, progressi per sviluppatore e stato di avanzamento complessivo. L'Excel contiene 3 fogli: Task, Per Sviluppatore, Riepilogo. **Aggrega il progresso da tutti i feature branch remoti** per mostrare dati aggiornati anche prima delle merge.

**Trigger**: `genera il report excel`, `aggiorna l'excel`, `stato avanzamento`

### sdlc-debug

Gestisce i bug segnalati dai funzionali durante e dopo il testing. Copre l'intero ciclo:
- **Import** da Excel (mapping intelligente delle colonne) o Jira (API/MCP)
- **Collegamento automatico** dei bug alle task/stream del piano
- **Assegnazione** con default all'owner della task collegata, override dal TL/PM
- **Esecuzione fix** con sottoagenti Claude Code e **verifica in 3 fasi** (tecnica + coerenza + riesame)
- **Chiusura** con validazione funzionale (Excel aggiornato, Jira, o conversazione)
- **Re-import iterativo** senza duplicazioni

Opera come **stage parallelo**: coesiste con l'esecuzione delle task senza interromperla. Supporta dual-mode (claude-flow standalone con MD come source of truth, portal-flow con manifest).

**Trigger**: `ci sono dei bug`, `bug dal funzionale`, `segnalazioni test`, `lavora il bug`, `debug br`, `aggiorna i bug`

### sdlc-profile-setup

Crea un nuovo profilo progetto nel repo centralizzato `deloitte-profiles/`. Auto-detect del codebase (framework, convenzioni, design system), domande guidate su dominio e glossario, generazione profile.json con commit+push, e configurazione automatica di `.br-local.json` nei codebase coinvolti.

**Trigger**: `crea profilo progetto`, `setup profilo`, `nuovo profilo`

### sdlc-estimator

Stima il team necessario per completare un BR entro una deadline. Due modalita': rough (dalla documentazione, ±30-40%) e dettagliata (dal piano, ±10-15%). Produce scenari ottimistico/realistico/pessimistico con timeline, bottleneck e allocazione team. Simulazioni what-if interattive per variare team, deadline e scope. Genera report MD + Excel.

**Trigger**: `stima il br`, `quanti sviluppatori servono`, `simulazione team`, `stima effort`

### sdlc-pipeline

Orchestratore unico per il ciclo di vita dei BR. Legge lo stato dal `manifest.json` di ogni BR, rileva il ruolo dell'utente (TL/PM o Dev) e mostra una dashboard con lo stato di ogni BR, proponendo il prossimo step e delegando alle skill appropriate. **Aggrega il progresso da tutti i feature branch remoti** per la dashboard.

**Trigger**: `sdlc-pipeline`, `pipeline br`, `le mie task`, `stato dei br`

### sdlc-brandkit

Genera il `brand.md` ad alta fedeltà (design contract agnostico) per i mockup del Mockup Designer: ispeziona un frontend qualsiasi (token, componenti, pagine), cattura screenshot golden da una POC se disponibile, ed emette `brand.md` + `tokens.css` + `assets/{screenshots,snippets}`. Standalone o via hook da `sdlc-profile-setup`. Output nel **contesto** (SPEC/project repo), mai nel `dataset/` di Solaria. Include il componente riutilizzabile [`scripts/fidelity-diff`](scripts/fidelity-diff/) (render + PNG-diff, zero dipendenze immagine: decode/diff in-browser via canvas) invocato in `deep` e on-demand in `classic`.

**Trigger**: `genera il brand kit`, `genera il design spec`, `brand.md per i mockup`, `specifiche di stile per i mockup`, `design contract`

## Agenti Generici

### sdlc-codebase-explorer

Esploratore di codebase profilo-aware. Usato da `sdlc-analyzer` e `sdlc-updater` per la gap analysis. Riceve il profilo progetto e naviga il codice in modo mirato, producendo output strutturato.

### sdlc-verifier

Verificatore in 3 fasi profilo-aware. Usato da `sdlc-executor` e `sdlc-debug` per verificare il lavoro dei sottoagenti. Produce verdict PASS/FAIL strutturato usando le convenzioni dal profilo.

### sdlc-estimation-analyst

Analista per stima rough. Estrae funzionalita' dalla documentazione BR e stima task, complessita', rischio e area.

### sdlc-estimation-historian

Storico per calibrazione. Scansiona BR completati ed estrae metriche reali per correggere le stime default.

### sdlc-estimation-scenario

Scenarista per simulazioni. Calcola timeline giorno per giorno, identifica bottleneck, produce 3 scenari con allocazione team. Supporta scope cutting con effetto cascata.

### Routing a specialist

Con profilo configurato, `sdlc-executor` e `sdlc-debug` instradano i sottoagenti al subagent_type appropriato (es. `spring-boot-engineer` per Spring Boot, `angular-architect` per Angular). Senza profilo, usano `general-purpose` (retrocompatibilita').

## Modalità di orchestrazione (classic / deep)

Ogni skill SDLC può girare in due modalità, scelte dall'utente (default `classic`):

- **`classic`** — sequenziale, leggera, pochi token. Il comportamento storico.
- **`deep`** — orchestrazione multi-agent via **Workflow tool** + verifica adversariale: più lenta/costosa ma più esaustiva. Mai escalation silenziosa: si attiva solo via flag persistente o conferma esplicita.

**Flag** in `.sdlc-local.json` (fallback `.br-local.json`), campi flat scritti da `sdlc-profile-setup`: `orchestration_mode` (`classic`|`deep`), `orchestration_depth` (`standard`|`ultracode`), `orchestration_max_concurrency`, `orchestration_verifier_panel`.

**Due cerchi** (design completo: [`docs/ORCHESTRATION_INTEGRATION_DESIGN.md`](docs/ORCHESTRATION_INTEGRATION_DESIGN.md)):
- **Heavy** — 5 script in [`workflows/`](workflows/) (`sdlc-analyzer-gap`, `sdlc-executor-wave`, `sdlc-debug-fixwave`, `sdlc-updater-delta`, `sdlc-reviewer-quality`): fan-out parallelo + `adversarial-verify` + `completeness-critic` + worktree isolati.
- **Light** (`sdlc-estimator`, `sdlc-clarify`, `sdlc-progress-report`, `sdlc-profile-setup`) — solo un sub-step di coherence/completeness-critic.

In `deep` i workflow **propongono**; l'agente principale resta single-writer (gate utente, niente auto-commit sul codice, scritture serializzate sui file source-of-truth). Se il Workflow tool è assente o fallisce, degrada a `classic` con banner **"COPERTURA RIDOTTA"** nell'artefatto. Deploy dei workflow: `scripts/sync-installed.sh --apply`.

> Il pattern `deep` è validato con review adversariale statica ma **non ancora con un run empirico** (golden-test facoltativo: [`docs/GOLDEN_TEST_ANALYZER.md`](docs/GOLDEN_TEST_ANALYZER.md)).

## Installazione

Copia le cartelle delle skill nella directory `~/.claude/skills/`:

```bash
cp -r skills/sdlc-* ~/.claude/skills/
cp -r agents/sdlc-* ~/.claude/agents/
```

Questo copia tutte le 10 skill e i 5 agenti generici (sdlc-reviewer, sdlc-clarify, sdlc-analyzer, sdlc-executor, sdlc-updater, sdlc-progress-report, sdlc-debug, sdlc-profile-setup, sdlc-estimator, sdlc-pipeline).

Aggiungi i trigger nel tuo `~/.claude/CLAUDE.md`:

```markdown
# sdlc-reviewer
- **sdlc-reviewer** (`~/.claude/skills/sdlc-reviewer/SKILL.md`) - review qualita della documentazione funzionale prima dell'analisi tecnica. Trigger: "rivedi il br", "review del br", "controlla la documentazione"
When the user says "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", or similar phrases about reviewing BR documentation quality, invoke the Skill tool with `skill: "sdlc-reviewer"` before doing anything else.

# sdlc-clarify
- **sdlc-clarify** (`~/.claude/skills/sdlc-clarify/SKILL.md`) - gestisce le risposte del funzionale alle domande del review BR. Trigger: "chiarimenti ricevuti", "risposte ricevute", "il funzionale ha risposto", "ho le risposte"
When the user says "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", or similar phrases about receiving functional team responses, invoke the Skill tool with `skill: "sdlc-clarify"` before doing anything else.

# sdlc-analyzer
- **sdlc-analyzer** (`~/.claude/skills/sdlc-analyzer/SKILL.md`) - analisi gap tra BR e codice + piano di implementazione. Trigger: "abbiamo un nuovo br"
When the user says "abbiamo un nuovo br" (or similar phrases about a new business requirement), invoke the Skill tool with `skill: "sdlc-analyzer"` before doing anything else.

# sdlc-executor
- **sdlc-executor** (`~/.claude/skills/sdlc-executor/SKILL.md`) - esecuzione task dal piano di sdlc-analyzer. Trigger: "lavora il task", "inizia a lavorare", "esegui il piano"
When the user says "lavora il task", "inizia a lavorare", "esegui il piano", or similar phrases about executing tasks from an implementation plan, invoke the Skill tool with `skill: "sdlc-executor"` before doing anything else.

# sdlc-updater
- **sdlc-updater** (`~/.claude/skills/sdlc-updater/SKILL.md`) - aggiorna report e piano quando il BR o la documentazione cambia. Trigger: "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br"
When the user says "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br", "documentazione aggiornata", or similar phrases about updated BR documentation, invoke the Skill tool with `skill: "sdlc-updater"` before doing anything else.

# sdlc-progress-report
- **sdlc-progress-report** (`~/.claude/skills/sdlc-progress-report/SKILL.md`) - genera/aggiorna Excel con avanzamento task e progressi per sviluppatore. Trigger: "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso"
When the user says "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso", or similar phrases about generating an Excel progress report, invoke the Skill tool with `skill: "sdlc-progress-report"` before doing anything else.

# sdlc-debug
- **sdlc-debug** (`~/.claude/skills/sdlc-debug/SKILL.md`) - gestione bug da testing funzionale: import da Excel/Jira, fix con sottoagenti e verifica 3 fasi, chiusura con validazione funzionale. Trigger: "ci sono dei bug", "lavora il bug", "debug br"
When the user says "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti", "lavora il bug", "fix il bug", "debug br", "il funzionale ha testato", "bug confermati", "aggiorna i bug", or similar phrases about managing bugs on a BR, invoke the Skill tool with `skill: "sdlc-debug"` before doing anything else.

# sdlc-profile-setup
- **sdlc-profile-setup** (`~/.claude/skills/sdlc-profile-setup/SKILL.md`) - creazione guidata profilo progetto con auto-detect codebase. Trigger: "crea profilo progetto", "setup profilo", "nuovo profilo"
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating a project profile, invoke the Skill tool with `skill: "sdlc-profile-setup"` before doing anything else.

# sdlc-estimator
- **sdlc-estimator** (`~/.claude/skills/sdlc-estimator/SKILL.md`) - stima team e simulazioni what-if per BR. Trigger: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort"
When the user says "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR, invoke the Skill tool with `skill: "sdlc-estimator"` before doing anything else.

# sdlc-pipeline
- **sdlc-pipeline** (`~/.claude/skills/sdlc-pipeline/SKILL.md`) - pipeline POM completo per gestione BR con manifest JSON e viste per ruolo. Trigger: "sdlc-pipeline", "pipeline br", "le mie task"
When the user says "sdlc-pipeline", "pipeline br", "le mie task", or similar phrases about the BR pipeline or viewing assigned tasks, invoke the Skill tool with `skill: "sdlc-pipeline"` before doing anything else.
```

## Migrazione dal naming legacy (br-*)

Se hai installato una versione precedente con prefisso `br-*` (skill folders) e file di output con suffisso `_BR` (`REVIEW_BR.md`/`GAP_REPORT_BR.md`/`PIANO_IMPLEMENTAZIONE_BR.md`/`PROGRESSO_BR.md`/`AVANZAMENTO_BR.xlsx`/`STIMA_BR.{md,xlsx}`/`BUG_REPORT_BR.md`), segui questi passi per migrare:

```bash
# 1. Sincronizza skill installate (rimuove le vecchie br-*, installa le nuove sdlc-*)
./scripts/sync-installed.sh --apply

# 2. Aggiorna i trigger nel tuo ~/.claude/CLAUDE.md
# Per ogni sezione trigger nella forma:
#   # br-X
#   ... skill: "br-X" ...
# Cambia in:
#   # sdlc-X
#   ... skill: "sdlc-X" ...
# Le frasi trigger italiane restano invariate ("rivedi il br", "abbiamo un nuovo br", ecc.)

# 3. Migra i file dei BR in-progress nel tuo repo profili
./scripts/migrate-sdlc-naming.sh                  # dry-run, verifica
./scripts/migrate-sdlc-naming.sh --apply          # esegue git mv

# 4. Commit + push nel repo profili
cd /path/to/deloitte-profiles
git commit -m "chore: rename BR output files to CLARIFY/PLAN/TASKS convention"
git push origin main
```

**Mapping nomi:**

| Legacy | Nuovo |
|---|---|
| Skill folders `br-{reviewer,clarify,analyzer,executor,updater,debug,progress-report,estimator,profile-setup}` | `sdlc-*` |
| Agent files `br-{codebase-explorer,estimation-{analyst,historian,scenario},verifier}.md` | `sdlc-*.md` |
| `REVIEW_BR.md` / `REVIEW_BR.docx` | `CLARIFY.md` / `CLARIFY.docx` |
| `GAP_REPORT_BR.md` | `PLAN.md` |
| `PIANO_IMPLEMENTAZIONE_BR.md` | `TASKS.md` |
| `PROGRESSO_BR.md` | `PROGRESS.md` |
| `AVANZAMENTO_BR.xlsx` | `PROGRESS.xlsx` |
| `STIMA_BR.md` / `STIMA_BR.xlsx` | `ESTIMATE.md` / `ESTIMATE.xlsx` |
| `BUG_REPORT_BR.md` | `BUG_REPORT.md` |

**Cosa NON cambia:**
- Trigger naturali italiani (*"abbiamo un nuovo br"*, *"rivedi il br"*, *"lavora il task"*, ecc.)
- Concetto di dominio "BR" / "Business Requirement" nei testi descrittivi
- Cartelle dei profili (`deloitte-profiles/<profilo>/plans/in-progress/<data>_<nome>/`)
- `.br-local.json` (configurazione per-repo)

Lo script `migrate-sdlc-naming.sh` salta automaticamente la cartella `plans/done/` (i BR chiusi restano fossili con i loro nomi storici).

## Dipendenze

- **doc-to-markdown** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (usata da `sdlc-reviewer`, `sdlc-analyzer` e `sdlc-updater`)
- **markitdown** — per conversione PDF, PPTX, XLSX (`pip install 'markitdown[all]'`)
- **pandoc** — per generazione DOCX e conversione DOCX→MD (usata da `sdlc-reviewer` e `sdlc-clarify`)
- **openpyxl** — per generazione Excel e lettura bug report (`pip install openpyxl`, usata da `sdlc-progress-report` e `sdlc-debug`)

## Documentazione completa

Per la documentazione dettagliata di ogni skill (fasi operative, regole, formati di output, gestione situazioni speciali), consulta **[SDLC_SKILLS_DOCUMENTATION.md](SDLC_SKILLS_DOCUMENTATION.md)**.

## Struttura Cartelle

I file di ogni BR sono organizzati in una cartella dedicata con formato `<YYYY-MM-DD>_<nome-br>/`. La cartella si sposta come unità tra le tre aree:

```
plans/
├── todo/                              <-- sdlc-reviewer e sdlc-analyzer creano i report qui
│   └── 2026-04-28_booking-v2/
│       ├── requirements/              <-- documentazione convertita in MD
│       ├── CLARIFY.md               <-- output di sdlc-reviewer
│       ├── CLARIFY.docx             <-- output di sdlc-reviewer (per il funzionale)
│       ├── PLAN.md           <-- output di sdlc-analyzer
│       └── TASKS.md
├── in-progress/                       <-- sdlc-executor sposta qui la cartella all'avvio
│   └── 2026-04-28_booking-v2/
│       ├── ...tutto il contenuto...
│       ├── PROGRESS.md            <-- creato da sdlc-executor
│       └── BUG_REPORT.md          <-- creato da sdlc-debug (se ci sono bug)
└── done/                              <-- sdlc-executor sposta qui al completamento
    └── 2026-04-28_booking-v2/
        └── PROGRESS.xlsx        <-- creato da sdlc-progress-report
```

Tutte le skill mantengono retrocompatibilita con il vecchio formato flat (es. `GAP_REPORT_BR_2026-04-28.md`).

## Flusso di lavoro

```
BR nuovo ──→ sdlc-reviewer ──→ Review qualità documentazione + DOCX
                  │
                  ▼
             sdlc-clarify ──→ Risposte funzionale → aggiorna review
                  │
                  ▼
            sdlc-analyzer ──→ Gap Report + Piano
                  │
                  ▼
            sdlc-executor ──→ Implementazione task (branch multi-repo)
                  │                    ↕
                  │              sdlc-debug ──→ Fix bug dal funzionale (stage parallelo)
                  │
                  ▼
        sdlc-progress-report ──→ Excel avanzamento (aggregato cross-branch)
                  │
    BR aggiornato ──→ sdlc-updater ──→ Aggiorna report/piano
                  │
                  ▼
            sdlc-executor ──→ Lavora task aggiornate
```

`sdlc-pipeline` puo' essere usato come orchestratore unico: rileva lo stato di ogni BR e propone automaticamente il prossimo step, delegando alla skill appropriata.

## Aggregazione Cross-Branch del Progresso

Quando piu' sviluppatori lavorano in parallelo su feature branch diversi, ognuno aggiorna il file PROGRESS.md sul proprio branch. Per garantire visibilita' del progresso a tutti senza attendere le merge, le skill di lettura (sdlc-executor, sdlc-pipeline, sdlc-progress-report) eseguono un'**aggregazione cross-branch**:

1. `git fetch origin` per sincronizzare
2. Lettura del piano per estrarre i nomi branch di ogni task (colonna Branch nel backlog) oppure il nome del BR per la ricerca per pattern (retrocompatibilita')
3. Ricerca dei feature branch remoti corrispondenti
4. Lettura del PROGRESSO da ogni feature branch via `git show`, provando 3 path possibili (`plans/in-progress/`, `plans/todo/`, `plans/done/`)
5. Aggregazione per task: **"highest progress wins"** — per ogni task, la versione con il progresso piu' alto vince; se una versione mostra "Completata", vince sempre

Il piano (generato da sdlc-analyzer) include una colonna **Branch** nel backlog che specifica il nome esatto del branch per ogni task. Per piani creati prima di questa modifica, l'aggregazione cerca i branch per pattern sul nome del BR (retrocompatibilita').

Il developer non cambia nulla nel suo workflow — basta pushare il feature branch. Il progresso diventa visibile a tutti senza merge.

## Licenza

MIT
