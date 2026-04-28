# Claude Flow — BR Skills per Claude Code

Suite di skill per Claude Code che automatizzano il ciclo di vita dei Business Requirements: dall'analisi gap all'esecuzione task, con aggiornamento incrementale e reporting Excel.

## Skills

### br-analyzer

Analizza un nuovo Business Requirement confrontandolo con i codebase esistenti (BE, FE, Document Manager, Email Manager). Genera:
- **Gap Report** dettagliato per funzionalita
- **Piano di Implementazione** con task indipendenti assegnate a sviluppatori

**Trigger**: `abbiamo un nuovo br`, `analizza il br`, `gap analysis br`

### br-executor

Esegue i task dal piano generato da `br-analyzer`. Ogni sviluppatore usa questa skill per:
- Lavorare le proprie task assegnate in ordine di priorita e dipendenze
- Delegare l'implementazione a sottoagenti Claude Code
- Tracciare il progresso in un file condiviso

**Trigger**: `lavora il task`, `inizia a lavorare`, `esegui il piano`

### br-updater

Aggiorna gap report e piano quando il BR o la documentazione cambia. Confronta la nuova documentazione con quella precedente, identifica i delta e aggiorna i file preservando il progresso delle task gia completate o in corso.

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

- **doc-to-markdown** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (usata da `br-analyzer` e `br-updater`)
- **markitdown** — per conversione PDF, PPTX, XLSX (`pip install 'markitdown[all]'`)
- **openpyxl** — per generazione Excel (`pip install openpyxl`, usata da `br-progress-report`)

## Flusso di lavoro

```
BR nuovo ──→ br-analyzer ──→ Gap Report + Piano
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
