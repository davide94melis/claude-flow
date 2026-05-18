# BR Skills Centralization — Design Spec

**Data**: 2026-05-18
**Obiettivo**: Centralizzare tutti gli artefatti BR nella repo `deloitte-profiles`, eliminando la dualità di storage e la portal-flow.

---

## 1. Motivazione

Oggi gli artefatti BR (piani, report, progressi) vivono nella repo del codice sorgente, separati dai profili progetto che stanno in `deloitte-profiles`. Questo causa:

- File sparsi su più repository
- Logica complessa di cross-branch aggregation per leggere progressi da altri branch
- Dualità claude-flow / portal-flow che complica ogni skill

La centralizzazione riunisce tutto in un unico posto.

---

## 2. Nuova struttura directory in `deloitte-profiles`

```
deloitte-profiles/
├── README.md
├── profile-schema.json
└── <nome-progetto>/
    ├── constitution/
    │   └── profile.json
    ├── agents/
    ├── references/
    └── plans/
        ├── todo/
        │   └── <data>_<nome-br>/
        │       ├── requirements/
        │       ├── REVIEW_BR.md
        │       ├── REVIEW_BR.docx
        │       ├── GAP_REPORT_BR.md
        │       ├── PIANO_IMPLEMENTAZIONE_BR.md
        │       ├── STIMA_BR.md
        │       └── STIMA_BR.xlsx
        ├── in-progress/
        │   └── <data>_<nome-br>/
        │       ├── (tutti i file da todo +)
        │       ├── PROGRESSO_BR.md
        │       ├── BUG_REPORT_BR.md
        │       ├── AVANZAMENTO_BR.xlsx
        │       └── screenshots/
        └── done/
            └── <data>_<nome-br>/
                └── (artefatti completi archiviati)
```

### Nella repo del codice

Resta solo `.br-local.json`:

```json
{
  "profilo": "banca-agente",
  "profiles_repo": "C:/Users/dev/Documents/deloitte-profiles",
  "developer": "nome"
}
```

---

## 3. Risoluzione dei path nelle skill

Ogni skill:

1. Legge `.br-local.json` dalla root della repo corrente
2. Estrae `profiles_repo` e `profilo`
3. Compone il base path: `<profiles_repo>/<profilo>/plans/...`
4. Esegue `git -C <profiles_repo> pull origin main --quiet` prima di leggere
5. Esegue `git -C <profiles_repo> add . && git commit -m "..." && git push` dopo ogni scrittura

### Se `.br-local.json` non esiste

- **Skill da TL/PM** (br-profile-setup, br-reviewer, br-analyzer, br-estimator): chiede di eseguire `br-profile-setup`
- **Skill da developer** (br-executor, br-debug): chiede i 3 campi (`profilo`, `profiles_repo`, `developer`) e crea `.br-local.json` senza toccare `deloitte-profiles`

Il file `.br-local.json` ha lo stesso schema per entrambi i ruoli. La differenziazione avviene a livello di quale skill viene invocata.

---

## 4. Modifiche per ciascuna skill

### br-profile-setup

- Crea `<profilo>/constitution/profile.json` (non piu in root del profilo)
- Crea le cartelle `agents/`, `references/`, `plans/todo/`, `plans/in-progress/`, `plans/done/`
- Aggiorna `profile-schema.json` e `README.md` di deloitte-profiles

### br-reviewer

- Scrive in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/`
- La cartella dei documenti convertiti si chiama `requirements/`
- Pull prima di leggere, commit+push dopo la scrittura

### br-clarify

- Cerca `REVIEW_BR.md` in `<profiles_repo>/<profilo>/plans/todo|in-progress/`
- Pull-before-write

### br-analyzer

- Scrive GAP_REPORT e PIANO_IMPLEMENTAZIONE in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/`
- Legge i documenti dalla cartella `requirements/`
- Continua a leggere il codice dalla repo corrente (la codebase non si sposta)

### br-executor

- Legge il piano da `<profiles_repo>/<profilo>/plans/todo/`
- Sposta la cartella in `plans/in-progress/` via `git mv` + commit + push
- Scrive PROGRESSO_BR.md nella stessa cartella
- Cross-branch aggregation eliminata: legge direttamente dopo pull
- Il codice viene scritto nella repo del progetto come oggi

### br-updater

- Legge e aggiorna i file in `<profiles_repo>/<profilo>/plans/todo|in-progress/`
- Salva nuove conversioni in `requirements/`

### br-debug

- Rimuove tutta la logica portal-flow
- Legge/scrive in `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/`
- Screenshots in `screenshots/` dentro la cartella del BR

### br-progress-report

- Legge piano e progresso da `<profiles_repo>/<profilo>/plans/`
- Scrive AVANZAMENTO_BR.xlsx nella cartella del BR
- Cross-branch aggregation eliminata

### br-estimator

- Scrive STIMA_BR.md e .xlsx in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/`
- Legge i dati storici da `plans/done/`
- Rimuove la logica portal-flow

---

## 5. Rimozioni

### Rimosso completamente

- **Skill `br-pipeline`**: intero file SKILL.md
- **Logica portal-flow** da ogni skill: detection di `brs/*/manifest.json`, rami condizionali
- **Cross-branch aggregation** da br-executor, br-progress-report
- **Concetto `brs/` e `manifest.json`** come struttura dati

### Aggiornamenti collaterali

- `~/.claude/CLAUDE.md`: rimuovere la sezione br-pipeline
- `BR_SKILLS_DOCUMENTATION.md`: aggiornare con la nuova struttura
- `profile-schema.json`: aggiornare per riflettere `constitution/profile.json`
- `README.md` di deloitte-profiles: aggiornare la struttura documentata
- Agenti in `~/.claude/agents/`: verificare che i path referenziati siano aggiornati (es. `br-estimation-historian.md` legge da `plans/done/`)

---

## 6. Concorrenza

Strategia **pull-before-write**: ogni skill fa `git pull` prima di scrivere e `git push` subito dopo, minimizzando la finestra di conflitto. Non servono lock o file separati per developer.

---

## 7. Approccio implementativo

**Big bang**: tutte le skill vengono modificate in un'unica sessione coordinata. Nessuna fase intermedia con skill disallineate.

---

## 8. Rinominazioni

| Prima | Dopo |
|-------|------|
| `<profilo>/profile.json` | `<profilo>/constitution/profile.json` |
| `br-docs-converted/` | `requirements/` |
| `brs/` (portal-flow) | rimosso |
| `manifest.json` (portal-flow) | rimosso |
| `plans/` (nella repo codice) | `plans/` (in deloitte-profiles) |
