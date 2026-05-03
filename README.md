# Claude Flow — BR Skills per Claude Code

Suite di 6 skill per Claude Code che automatizzano il ciclo di vita dei Business Requirements: dalla review della documentazione funzionale alla gestione delle risposte del funzionale, dall'analisi gap all'esecuzione task, dall'aggiornamento incrementale al reporting Excel.

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

**Trigger**: `lavora il task`, `inizia a lavorare`, `esegui il piano`

### br-updater

Aggiorna gap report e piano quando il BR o la documentazione cambia. Confronta la nuova documentazione con quella precedente, identifica i delta e aggiorna i file preservando il progresso delle task già completate o in corso.

**Trigger**: `il br e stato aggiornato`, `aggiorna il piano`, `nuova versione del br`

### br-progress-report

Genera o aggiorna un file Excel (`.xlsx`) con il riepilogo completo delle task, progressi per sviluppatore e stato di avanzamento complessivo. L'Excel contiene 3 fogli: Task, Per Sviluppatore, Riepilogo.

**Trigger**: `genera il report excel`, `aggiorna l'excel`, `stato avanzamento`

## Installazione

Copia le cartelle delle skill nella directory `~/.claude/skills/`:

```bash
cp -r skills/br-* ~/.claude/skills/
```

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
            br-executor ──→ Implementazione task
                  │
                  ▼
        br-progress-report ──→ Excel avanzamento
                  │
    BR aggiornato ──→ br-updater ──→ Aggiorna report/piano
                  │
                  ▼
            br-executor ──→ Lavora task aggiornate
```

## Licenza

MIT
