# Claude Flow — BR Skills per Claude Code

Suite di 7 skill per Claude Code che automatizzano il ciclo di vita dei Business Requirements: dalla review della documentazione funzionale alla gestione delle risposte del funzionale, dall'analisi gap all'esecuzione task, dall'aggiornamento incrementale al reporting Excel, con un orchestratore pipeline che coordina il tutto.

## Skills

### br-reviewer

Verifica la qualità, coerenza e completezza della documentazione funzionale di un BR *prima* dell'analisi tecnica. Produce un report duale:
- **Parte 1 — Per il team funzionale**: problemi da chiarire (bloccanti e non), con domande precise
- **Parte 2 — Per il team tecnico**: assunzioni di default e disallineamenti col codice

Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali.

Genera anche un DOCX con placeholder per le risposte, pronto per essere inviato al team funzionale.

**Trigger**: `rivedi il br`, `review del br`, `controlla la documentazione`, `verifica il br`

### br-clarify

Gestisce le risposte del team funzionale alle domande sollevate nel review. Supporta due modalita di input:
- **DOCX compilato**: il funzionale compila il REVIEW_BR.docx e lo restituisce
- **Conversazione**: l'utente riporta le risposte a voce

Aggiorna il REVIEW_BR.md con le risposte, ri-valuta bloccanti e assunzioni, e rigenera il DOCX. Può essere eseguita più volte per risposte parziali.

**Trigger**: `chiarimenti ricevuti`, `risposte ricevute`, `il funzionale ha risposto`, `ho le risposte`

### br-analyzer

Analizza un nuovo Business Requirement confrontandolo con i codebase esistenti (BE, FE, Document Manager, Email Manager). Genera:
- **Gap Report** dettagliato per funzionalità
- **Piano di Implementazione** con task indipendenti assegnate a sviluppatori

**Trigger**: `abbiamo un nuovo br`, `analizza il br`, `gap analysis br`

### br-executor

Esegue i task dal piano generato da `br-analyzer`. Ogni sviluppatore usa questa skill per:
- Lavorare le proprie task assegnate in ordine di priorità e dipendenze
- Delegare l'implementazione a sottoagenti Claude Code
- Tracciare il progresso in un file condiviso
- **Creare branch in tutte le repo coinvolte** (non solo quella del piano)
- **Verificare le dipendenze con aggregazione cross-branch** (vede il progresso di tutti i developer anche se lavorano su branch diversi)

**Trigger**: `lavora il task`, `inizia a lavorare`, `esegui il piano`

### br-updater

Aggiorna gap report e piano quando il BR o la documentazione cambia. Confronta la nuova documentazione con quella precedente, identifica i delta e aggiorna i file preservando il progresso delle task già completate o in corso.

**Trigger**: `il br e stato aggiornato`, `aggiorna il piano`, `nuova versione del br`

### br-progress-report

Genera o aggiorna un file Excel (`.xlsx`) con il riepilogo completo delle task, progressi per sviluppatore e stato di avanzamento complessivo. L'Excel contiene 3 fogli: Task, Per Sviluppatore, Riepilogo. **Aggrega il progresso da tutti i feature branch remoti** per mostrare dati aggiornati anche prima delle merge.

**Trigger**: `genera il report excel`, `aggiorna l'excel`, `stato avanzamento`

### br-pipeline

Orchestratore unico per il ciclo di vita dei BR. Legge lo stato dal `manifest.json` di ogni BR, rileva il ruolo dell'utente (TL/PM o Dev) e mostra una dashboard con lo stato di ogni BR, proponendo il prossimo step e delegando alle skill appropriate. **Aggrega il progresso da tutti i feature branch remoti** per la dashboard.

**Trigger**: `br-pipeline`, `pipeline br`, `le mie task`, `stato dei br`

## Installazione

Copia le cartelle delle skill nella directory `~/.claude/skills/`:

```bash
cp -r skills/br-* ~/.claude/skills/
```

Questo copia tutte le 7 skill (br-reviewer, br-clarify, br-analyzer, br-executor, br-updater, br-progress-report, br-pipeline).

Aggiungi i trigger nel tuo `~/.claude/CLAUDE.md`:

```markdown
# br-reviewer
- **br-reviewer** (`~/.claude/skills/br-reviewer/SKILL.md`) - review qualita della documentazione funzionale prima dell'analisi tecnica. Trigger: "rivedi il br", "review del br", "controlla la documentazione"
When the user says "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", or similar phrases about reviewing BR documentation quality, invoke the Skill tool with `skill: "br-reviewer"` before doing anything else.

# br-clarify
- **br-clarify** (`~/.claude/skills/br-clarify/SKILL.md`) - gestisce le risposte del funzionale alle domande del review BR. Trigger: "chiarimenti ricevuti", "risposte ricevute", "il funzionale ha risposto", "ho le risposte"
When the user says "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", or similar phrases about receiving functional team responses, invoke the Skill tool with `skill: "br-clarify"` before doing anything else.

# br-analyzer
- **br-analyzer** (`~/.claude/skills/br-analyzer/SKILL.md`) - analisi gap tra BR e codice + piano di implementazione. Trigger: "abbiamo un nuovo br"
When the user says "abbiamo un nuovo br" (or similar phrases about a new business requirement), invoke the Skill tool with `skill: "br-analyzer"` before doing anything else.

# br-executor
- **br-executor** (`~/.claude/skills/br-executor/SKILL.md`) - esecuzione task dal piano di br-analyzer. Trigger: "lavora il task", "inizia a lavorare", "esegui il piano"
When the user says "lavora il task", "inizia a lavorare", "esegui il piano", or similar phrases about executing tasks from an implementation plan, invoke the Skill tool with `skill: "br-executor"` before doing anything else.

# br-updater
- **br-updater** (`~/.claude/skills/br-updater/SKILL.md`) - aggiorna report e piano quando il BR o la documentazione cambia. Trigger: "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br"
When the user says "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br", "documentazione aggiornata", or similar phrases about updated BR documentation, invoke the Skill tool with `skill: "br-updater"` before doing anything else.

# br-progress-report
- **br-progress-report** (`~/.claude/skills/br-progress-report/SKILL.md`) - genera/aggiorna Excel con avanzamento task e progressi per sviluppatore. Trigger: "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso"
When the user says "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso", or similar phrases about generating an Excel progress report, invoke the Skill tool with `skill: "br-progress-report"` before doing anything else.

# br-pipeline
- **br-pipeline** (`~/.claude/skills/br-pipeline/SKILL.md`) - pipeline POM completo per gestione BR con manifest JSON e viste per ruolo. Trigger: "br-pipeline", "pipeline br", "le mie task"
When the user says "br-pipeline", "pipeline br", "le mie task", or similar phrases about the BR pipeline or viewing assigned tasks, invoke the Skill tool with `skill: "br-pipeline"` before doing anything else.
```

## Dipendenze

- **doc-to-markdown** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (usata da `br-reviewer`, `br-analyzer` e `br-updater`)
- **markitdown** — per conversione PDF, PPTX, XLSX (`pip install 'markitdown[all]'`)
- **pandoc** — per generazione DOCX e conversione DOCX→MD (usata da `br-reviewer` e `br-clarify`)
- **openpyxl** — per generazione Excel (`pip install openpyxl`, usata da `br-progress-report`)

## Documentazione completa

Per la documentazione dettagliata di ogni skill (fasi operative, regole, formati di output, gestione situazioni speciali), consulta **[BR_SKILLS_DOCUMENTATION.md](BR_SKILLS_DOCUMENTATION.md)**.

## Struttura Cartelle

I file di ogni BR sono organizzati in una cartella dedicata con formato `<YYYY-MM-DD>_<nome-br>/`. La cartella si sposta come unità tra le tre aree:

```
plans/
├── todo/                              <-- br-reviewer e br-analyzer creano i report qui
│   └── 2026-04-28_booking-v2/
│       ├── br-docs-converted/         <-- documentazione convertita in MD
│       ├── REVIEW_BR.md               <-- output di br-reviewer
│       ├── REVIEW_BR.docx             <-- output di br-reviewer (per il funzionale)
│       ├── GAP_REPORT_BR.md           <-- output di br-analyzer
│       └── PIANO_IMPLEMENTAZIONE_BR.md
├── in-progress/                       <-- br-executor sposta qui la cartella all'avvio
│   └── 2026-04-28_booking-v2/
│       ├── ...tutto il contenuto...
│       └── PROGRESSO_BR.md            <-- creato da br-executor
└── done/                              <-- br-executor sposta qui al completamento
    └── 2026-04-28_booking-v2/
        └── AVANZAMENTO_BR.xlsx        <-- creato da br-progress-report
```

Tutte le skill mantengono retrocompatibilita con il vecchio formato flat (es. `GAP_REPORT_BR_2026-04-28.md`).

## Flusso di lavoro

```
BR nuovo ──→ br-reviewer ──→ Review qualità documentazione + DOCX
                  │
                  ▼
             br-clarify ──→ Risposte funzionale → aggiorna review
                  │
                  ▼
            br-analyzer ──→ Gap Report + Piano
                  │
                  ▼
            br-executor ──→ Implementazione task (branch multi-repo)
                  │
                  ▼
        br-progress-report ──→ Excel avanzamento (aggregato cross-branch)
                  │
    BR aggiornato ──→ br-updater ──→ Aggiorna report/piano
                  │
                  ▼
            br-executor ──→ Lavora task aggiornate
```

`br-pipeline` puo' essere usato come orchestratore unico: rileva lo stato di ogni BR e propone automaticamente il prossimo step, delegando alla skill appropriata.

## Aggregazione Cross-Branch del Progresso

Quando piu' sviluppatori lavorano in parallelo su feature branch diversi, ognuno aggiorna il file PROGRESSO_BR.md sul proprio branch. Per garantire visibilita' del progresso a tutti senza attendere le merge, le skill di lettura (br-executor, br-pipeline, br-progress-report) eseguono un'**aggregazione cross-branch**:

1. `git fetch origin` per sincronizzare
2. Lettura del piano per estrarre i nomi branch di ogni task (colonna Branch nel backlog) oppure il nome del BR per la ricerca per pattern (retrocompatibilita')
3. Ricerca dei feature branch remoti corrispondenti
4. Lettura del PROGRESSO da ogni feature branch via `git show`, provando 3 path possibili (`plans/in-progress/`, `plans/todo/`, `plans/done/`)
5. Aggregazione per task: **"highest progress wins"** — per ogni task, la versione con il progresso piu' alto vince; se una versione mostra "Completata", vince sempre

Il piano (generato da br-analyzer) include una colonna **Branch** nel backlog che specifica il nome esatto del branch per ogni task. Per piani creati prima di questa modifica, l'aggregazione cerca i branch per pattern sul nome del BR (retrocompatibilita').

Il developer non cambia nulla nel suo workflow — basta pushare il feature branch. Il progresso diventa visibile a tutti senza merge.

## Licenza

MIT
