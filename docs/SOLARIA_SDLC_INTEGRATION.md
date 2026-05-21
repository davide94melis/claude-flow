# Solaria ↔ SDLC Skills — Flusso End-to-End e Contratti di Interscambio

**Rev. corrente:** 2026-05-21
**Stato:** Contratto attivo per integrazione Solaria-side. Allinearsi a `Fasi-New-way-of-working.md` (2 fasi composite) prima di proporre cambi.
**Scopo:** Definire come l'agente esterno **Solaria** si integra a monte del nostro processo SDLC, dalla creazione del dataset di progetto fino alla chiusura post-testing, e formalizzare i contratti d'interscambio (schema manifest, formati output, convenzioni commit).

---

## Premessa

L'agente **Solaria** (in fase di progettazione presso un altro team, opera via API Anthropic — non Claude Code) assiste il **team funzionale** nella produzione e manutenzione dell'AFU (Analisi Funzionale Utente) + mockup + playbook test. Le skill `sdlc-*` di Claude Code prendono in carico il flusso dal momento in cui Solaria fa l'**handoff** del package alla repo del progetto, e producono codice, test e reportistica fino alla chiusura del plan.

Il flusso end-to-end e' organizzato in **2 fasi composite** (vedi `Fasi-New-way-of-working.md`):

- **Fase 1: Pre-Coding** — 1a setup tecnico (team tech, `sdlc-profile-setup`), 1b setup dataset funzionale (Solaria), 1c authoring AFU + mockup + playbook (Solaria multi-agent)
- **Fase 2: Coding & Test** — 2a implementazione (team tech, Claude Code), 2b update mid-flight opzionale (Solaria → Claude Code), 2c test in due ondate sequenziali + chiusura

---

## Principi chiave (non-negoziabili)

### 1. Solaria non parla con lo stakeholder

Il rapporto con lo **stakeholder business** e' tenuto **sempre dal team funzionale**, **al di fuori di Solaria** (riunioni, mail, telefonate, sessioni dirette). Solaria interagisce solo con il **funzionale**, che porta input gia' raccolti offline e riporta gli output allo stakeholder per validazione, raccogliendone i feedback per il round successivo. Vale in tutte le sotto-fasi (1b, 1c, 2b).

### 2. Solaria opera server-side via GitHub API (no clone locale)

Solaria **non gira sulla macchina dell'analista funzionale** e **non clona la project_repo in locale**. E' un servizio server-side che accede alla repo del progetto **interamente via GitHub API**:

| API GitHub | Uso Solaria |
|---|---|
| Contents API (`GET/PUT /repos/{o}/{r}/contents/{path}`) | Read/write file singoli |
| Git Data API — Trees (`POST .../git/trees` con `base_tree`) | Commit atomici multi-file; rename atomici di cartelle (`sha: null` su path = delete) |
| Git Data API — Commits/Refs (`POST .../git/commits`, `PATCH .../git/refs/heads/main`) | Creazione commit + avanzamento ref `main` |
| Commits API (`GET .../commits?path=...&since=...`) | Polling on-demand commit del team tech (`[sdlc-*]`) |
| Webhook GitHub `push` event (opzionale) | Detection real-time alternativa al polling |

**Autenticazione**: GitHub App installata sulla `project_repo` (raccomandato in produzione, token per-installazione) oppure PAT con scope `repo` (sviluppo/staging).

L'analista funzionale accede a Solaria come servizio (web UI o chat). Tutto storage, versionamento ed esecuzione vivono nella `project_repo` su GitHub/GitHub Enterprise.

### 3. Solaria accede al contesto del progetto in continuo

Per produrre AFU coerenti col progetto reale (non descrizioni generiche scollegate dal codice), Solaria carica via API lo snapshot dello stato corrente di `main` ad ogni apertura di sessione. Risorse lette:

| Risorsa | Path nella project_repo | Scopo per Solaria |
|---|---|---|
| Profilo tecnico | `constitution/CONST.json` + `constitution/PROFILE.json` | Tech stack, dominio, glossario, regole business, design system. Usato da FunctionalWeaver per terminologia coerente. |
| References | `references/` | Asset team tech (style guide, link). Read-only per Solaria. |
| Dataset Solaria | `dataset/` | Branding, corporate, glossario, attori, perimetro. **Area Solaria-side** popolata in F1b e arricchita in F1c — Solaria SCRIVE qui. |
| Plan completati | `plans/done/**/*` | Funzionalita' gia' implementate (evitare di re-richiedere cose fatte). |
| Plan in coda | `plans/todo/**/*` | AFU consegnati ma non ancora in esecuzione. |
| Plan in lavorazione | `plans/in-progress/**/*` | Cosa il team tech sta gia' implementando (evitare conflitti scope + coordinamento timing). |
| Plan in draft | `plans/draft/**/*` | Altri AFU in authoring (evitare duplicazioni con altri analisti funzionali in parallelo). |

**Permessi di scrittura Solaria** (sintesi):
- `dataset/**` — WRITE (F1b + F1c arricchimento per-plan)
- `plans/draft/<plan>/**` — WRITE (F1c authoring)
- `plans/todo/<plan>/CLARIFY.md` — WRITE (F2a compilazione risposte se review tech opzionale attivata)
- `plans/in-progress/<plan>/requirements/**` + `afu-manifest.json` — WRITE (F2b update v2.0)
- Tutto il resto — READ-ONLY (PLAN.md, TASKS.md, PROGRESS.md, BUG_REPORT.md sono lato Claude Code)

---

## Architettura: una repo per progetto

```
<project_repo>/                                  (es. banca-agente)
├── constitution/                                 (team tech, sdlc-profile-setup F1a)
│   ├── CONST.json                                principi/standard
│   └── PROFILE.json                              tech stack + dominio
├── references/                                   (team tech)
│   └── style-guide-*.md                          link, snippet, doc tech
├── agents/                                       (team tech, agent SDLC custom)
├── dataset/                                      (SOLARIA-SIDE, F1b + F1c)
│   ├── branding/                                 logo, palette, font, brand book
│   ├── corporate/                                template doc, presentazioni
│   ├── glossario.md                              termini di dominio
│   ├── attori.md                                 ruoli, personas, sistemi esterni
│   └── perimetro.md                              scope progetto + esclusioni
├── afu-manifest.schema.json                      schema v2 (copiato in F1a)
└── plans/
    ├── draft/<YYYY-MM-DD>_<slug>/                 SOLARIA authoring F1c
    │   ├── requirements/{AFU.docx|md, mockups/}
    │   ├── afu-manifest.json                      (gate=GO|NO-GO, coverage, ecc.)
    │   ├── REVIEW.md                              (rilievi review/clarify post-GO)
    │   └── tests/{playbook.md, playbook.xlsx}     (output F1c)
    ├── todo/<plan>/                               post-handoff Solaria
    │   ├── (tutto da draft + )
    │   ├── CLARIFY.md                             (opzionale, F2a review tech)
    │   ├── PLAN.md (sdlc-analyzer)
    │   └── TASKS.md (sdlc-analyzer)
    ├── in-progress/<plan>/                        F2a/2b/2c
    │   ├── (tutto da todo + )
    │   ├── PROGRESS.md (sdlc-executor)
    │   ├── PROGRESS.xlsx (sdlc-progress-report)
    │   ├── BUG_REPORT.md (sdlc-debug — 2 sezioni: tecnico + funzionale)
    │   └── bug-import-YYYYMMDD.xlsx (v2, colonna origine)
    └── done/<plan>/                               F2c chiusura (sdlc-executor automatico)
```

`.br-local.json` in ogni repo applicativa del developer:
```json
{ "project_repo": "<path-locale-del-clone>", "project_name": "<nome>", "developer": "<nome-dev>" }
```

---

## Agenti Solaria-side (DA IMPLEMENTARE dal team Solaria)

Il team Solaria deve produrre i seguenti agenti, tutti via API Anthropic (no Claude Code), che operano contro la project_repo via GitHub API. Le skill SDLC originali in `~/.claude/skills/` restano intatte: il team Solaria mantiene fork adattati Solaria-side.

### A. FunctionalWeaver (Fase 1c — generazione AFU dal dataset)

**Quando**: F1c authoring iniziale + ogni round stakeholder F2 + update mid-flight F2b
**Input**: dataset Solaria del progetto (caricato in F1b) + `CONST.json` + `PROFILE.json` + scansione `plans/*` (read-only) + materiale offline funzionale (note, mail, mockup grezzi)
**Output**: `plans/draft/<plan>/requirements/AFU.docx` (e/o `.md`) + `afu-manifest.json` v1.0/v1.N/v2.N
**Caratteristica chiave**: **NON conduce Q&A col funzionale**. Genera l'AFU **direttamente dal dataset**. La qualita' dell'AFU dipende dalla ricchezza del dataset. Itera con FunctionalReviewer fino a GO.
**Implementazione**: prompt engineering con API Anthropic. System message con profilo + dataset come context.

### B. FunctionalReviewer (Fase 1c — quality gate GO/NO-GO)

**Quando**: F1c dopo ogni generazione FunctionalWeaver + ogni round stakeholder F2 + ogni update F2b
**Input**: `requirements/AFU.docx` + dataset corrispondente
**Output**:
- Aggiornamento `afu-manifest.json` con `coverage.{overall_percent, by_section{...}}` e `gate_outcome: "GO" | "NO-GO"`
- Se NO-GO: log delle sezioni a bassa copertura (segnale implicito al funzionale su cosa manca nel dataset)
**Caratteristica chiave**: quality gate **automatico**. Se NO-GO, blocca il passaggio a review/clarify Solaria-side. Il funzionale arricchisce il dataset, FunctionalWeaver rigenera, FunctionalReviewer rivaluta. Loop fino a GO.
**Implementazione**: prompt engineering scorer (rubric per sezione AFU) con API Anthropic. Output strutturato JSON convertito in campi manifest.

### C. Mockup Designer Agent (Fase 1c — generazione mockup)

**Quando**: F1c in parallelo all'authoring AFU + F2b se cambio requisiti impatta UI
**Input**: mockup grezzi forniti dal funzionale + asset branding (`dataset/branding/`) + AFU corrente
**Output**: file in `plans/draft/<plan>/requirements/mockups/` (PNG/JPG/SVG/Figma export)
**Caratteristica chiave**: produce mockup "di esempio" coerenti col branding. Non sostituisce il design vero, ma da' al team tech un baseline visuale.
**Implementazione**: image generation API + asset compositing.

### D. Skill review + clarify forkate Solaria-side (Fase 1c post-GO + F2/F2b)

**Quando**: solo **dopo** che FunctionalReviewer ha emesso GO
**Input**: AFU + dataset
**Output**:
- `plans/draft/<plan>/REVIEW.md` con rilievi dettaglio (corner case, bad flow, unhappy path, ambiguita' residue, incongruenze interne)
- Aggiornamento `afu-manifest.json` con `review_clarify_status: "open" | "closed"`
**Caratteristica chiave**: fork delle skill `sdlc-reviewer` + `sdlc-clarify` Claude Code, adattate per analisi dettaglio post-GO (le originali sono per review tech post-handoff). Iterazione col funzionale tramite Solaria fino a `closed`.
**Implementazione**: prompt engineering riusando la logica di categorizzazione problemi delle skill originali.

### E. Playbook Generator (Fase 1c — generazione test funzionali)

**Quando**: F1c al consenso finale stakeholder (gate=GO + review_clarify=closed) + F2b se delta v2 impatta criteri accettazione
**Input**: criteri di accettazione dell'AFU + flussi (happy path + eccezioni)
**Output**:
- `plans/<state>/<plan>/tests/playbook.md` (checklist eseguibile manualmente, formato MD per lettura)
- `plans/<state>/<plan>/tests/playbook.xlsx` (stessa checklist importabile in Jira/TestRail/foglio)
- Aggiornamento `afu-manifest.json` con `tests: {playbook_md, playbook_xlsx}`
**Caratteristica chiave**: NON e' esecutore test. Produce la checklist che il **team funzionale eseguira' manualmente in autonomia** in Fase 2c ondata (b), senza Solaria.
**Implementazione**: parsing AFU + template MD/XLSX (openpyxl o equivalente JS).

> Schema colonne consigliato per `playbook.xlsx` (TBC con team funzionale): `id`, `area`, `pre-condizioni`, `step`, `risultato_atteso`, `risultato_effettivo`, `esito (pass|fail|n/a)`, `evidenza_path`, `note`.

### F. Orchestratore Solaria

Componente che orchestra A-E secondo il flow F1b → F1c → handoff → F2b → F2c notification. Gestisce:
- Persistenza dataset (sincronizzazione continua su `dataset/` via Contents API)
- Handoff atomico F1c → F2a (rename `plans/draft/<plan>` → `plans/todo/<plan>` via Git Trees API, commit `[solaria-handoff]`)
- Polling Commits API (default) o webhook (opzionale) per intercettare commit `[sdlc-reviewer]`, `[sdlc-clarify]`, chiusura plan da `sdlc-executor`
- Validazione `afu-manifest.json` v2 contro lo schema (`ajv` o `jsonschema`) prima di ogni commit

---

## Contratti d'interscambio

### Schema `afu-manifest.json` v2

Canonical in `claude-flow/templates/afu-manifest.schema.json` (JSON Schema draft-07). Copiato in `<project_repo>/afu-manifest.schema.json` dal `sdlc-profile-setup` in F1a.

Campi obbligatori (invariati da v1): `nome`, `versione`, `autore`, `data`, `files`, `stakeholder`, `deadline`, `priorita`.
Campi opzionali invariati: `parent_version`, `changelog`.

**Nuovi campi opzionali v2** (obbligatori nei plan handoff'able):

| Campo | Tipo | Prodotto da | Consumato da |
|---|---|---|---|
| `coverage` | `{overall_percent, by_section{...}}` | FunctionalReviewer (F1c) | sdlc-reviewer / sdlc-analyzer (validazione handoff-ability) |
| `gate_outcome` | enum `GO | NO-GO` | FunctionalReviewer (F1c) | sdlc-reviewer / sdlc-analyzer (gate handoff: solo GO procede) |
| `review_clarify_status` | enum `open | closed` | skill review/clarify forkate (F1c post-GO) | sdlc-reviewer / sdlc-analyzer (gate handoff: solo closed procede) |
| `tests` | `{playbook_md, playbook_xlsx}` | Playbook Generator (F1c) | sdlc-analyzer (header PLAN.md), sdlc-executor (log informativo F2c) |

Esempio completo:

```json
{
  "$schema": "../../afu-manifest.schema.json",
  "nome": "login-sso",
  "versione": "1.3",
  "parent_version": "1.2",
  "changelog": "Round 3 stakeholder: cambiata regola scadenza password 90->60gg.",
  "autore": "Mario Rossi <mario.rossi@example.com>",
  "data": "2026-05-21",
  "files": ["AFU.docx", "mockups/login.png", "mockups/forgot-password.png"],
  "stakeholder": "Banca XYZ — Direzione Digital",
  "deadline": "2026-06-30",
  "priorita": "alta",
  "coverage": {
    "overall_percent": 100,
    "by_section": {
      "funzionalita": 100, "attori": 100, "casi_uso": 100, "flussi": 95,
      "regole_business": 100, "vincoli_tecnici": 100, "criteri_accettazione": 100
    }
  },
  "gate_outcome": "GO",
  "review_clarify_status": "closed",
  "tests": {
    "playbook_md": "tests/playbook.md",
    "playbook_xlsx": "tests/playbook.xlsx"
  }
}
```

### `CLARIFY.md` con placeholder per Solaria (F2a opzionale)

Quando il TL invoca `sdlc-reviewer` post-handoff in F2a (opzionale standalone), viene generato un `CLARIFY.md` con placeholder `*(inserire qui la risposta)*` sotto ogni domanda. Solaria detecta il nuovo commit `[sdlc-reviewer]` via polling Commits API o webhook, compila le risposte direttamente nel MD via Contents API e committa con prefisso `[solaria-clarify]`. `sdlc-clarify` lato Claude Code rileva il commit Solaria via `git log --grep="^\[solaria-clarify\]"` e attiva la **Modalita' C** (auto-detection). No DOCX in standalone.

### Excel bug v2 con colonna `origine`

Template canonical in `claude-flow/templates/BUG_EXCEL_TEMPLATE.xlsx` v2.

| Colonna | Tipo | Note |
|---|---|---|
| `id`, `fase`, `sezione`, `utente`, `titolo`, `descrizione`, `screenshot`, `riferimento`, `tipo`, `stato_originale`, `data`, `note_dev`, `note_funzionale` | Esistenti v1 | Invariati |
| **`origine`** (NUOVA v2) | enum `tecnico | funzionale` | Data validation Excel. `tecnico` = bug da test team tech in F2c ondata (a). `funzionale` = bug da playbook funzionale in F2c ondata (b). |

`sdlc-debug` mappa la colonna, popola `BUG_REPORT.md` con due sezioni separate, espone counter `bug_tecnici_aperti` / `bug_funzionali_aperti` consumati da `sdlc-executor` per il check di chiusura plan. Retrocompat: file senza colonna `origine` → tutti tecnico (default).

In alternativa all'Excel: scrittura diretta su Jira (se progetto configurato), stesso schema campi.

### Playbook test (`tests/playbook.md` + `.xlsx`)

Generato da Playbook Generator Solaria-side in F1c, committato come parte del package handoff. Eseguito **manualmente in autonomia dal team funzionale** in F2c ondata (b) — Solaria non e' coinvolta nell'esecuzione. Fail confluiscono in `bug-import-YYYYMMDD.xlsx` con `origine=funzionale`.

---

## Convenzioni commit message Solaria

Pattern unico per facilitare polling/filtering da `sdlc-*` skill:

```
[solaria-<azione>] <plan>: <descrizione concisa>
```

| Azione | Quando | Esempio |
|---|---|---|
| `solaria-dataset-bootstrap` | F1b creazione dataset progetto | `[solaria-dataset-bootstrap] init: dataset/branding,corporate,glossario,attori,perimetro` |
| `solaria-dataset-update` | F1b/F1c arricchimento dataset | `[solaria-dataset-update] login-sso: added brand assets v2` |
| `solaria-draft` | F1c authoring/iterazione FunctionalWeaver+Reviewer | `[solaria-draft] 2026-05-21_login-sso: AFU v1.0 ready for stakeholder` |
| `solaria-stakeholder` | F1c round stakeholder con bump versione | `[solaria-stakeholder] 2026-05-21_login-sso: round 2, v1.2` |
| `solaria-handoff` | F1c → F2a rename atomico draft→todo via Git Trees API | `[solaria-handoff] 2026-05-21_login-sso: stakeholder approved v1.3, ready for dev` |
| `solaria-clarify` | F2a (opzionale) compilazione risposte CLARIFY.md | `[solaria-clarify] 2026-05-21_login-sso: round 1 risposte funzionale` |
| `solaria-update` | F2b update mid-flight v2.0 | `[solaria-update] 2026-04-28_booking-v2: AFU v2.0 (cambi requisiti)` |

---

## Mapping agenti Solaria ↔ sub-fasi

| Sub-fase | Agenti Solaria attivi | Output Git |
|---|---|---|
| 1a (Setup tecnico) | nessuno (team tech `sdlc-profile-setup`) | `constitution/`, `references/`, `agents/`, `plans/{draft,todo,in-progress,done}/`, `dataset/` scheletro, `afu-manifest.schema.json` |
| 1b (Setup dataset) | Orchestratore Solaria | `dataset/{branding,corporate,glossario.md,attori.md,perimetro.md}` popolati |
| 1c (Authoring AFU) | FunctionalWeaver + FunctionalReviewer (loop) → Mockup Designer Agent → review/clarify forkate (post-GO loop) → Playbook Generator | `plans/draft/<plan>/{requirements/{AFU.*,mockups/}, afu-manifest.json, REVIEW.md, tests/playbook.{md,xlsx}}` + handoff finale `plans/todo/<plan>/...` via Git Trees API |
| 2a (Implementazione) | nessuno (team tech: `sdlc-reviewer`/`sdlc-clarify` opzionali, poi `sdlc-analyzer`, `sdlc-executor`, `sdlc-progress-report`) | `plans/todo/<plan>/{CLARIFY.md opzionale, PLAN.md, TASKS.md}` → `plans/in-progress/<plan>/{PROGRESS.md, PROGRESS.xlsx}` |
| 2a Q&A loop opzionale | Orchestratore Solaria (detection `[sdlc-reviewer]`/`[sdlc-clarify]` via polling/webhook) + skill clarify forkata (compila risposte) | `plans/todo/<plan>/CLARIFY.md` con commit `[solaria-clarify]` |
| 2b (Update mid-flight) | FunctionalWeaver + FunctionalReviewer + Mockup Designer + review/clarify forkate + Playbook Generator (riuso F1c) → team tech `sdlc-updater` | `plans/in-progress/<plan>/{requirements/, afu-manifest.json v2.0, tests/playbook.* rigenerato}` |
| 2c ondata (a) test tecnici | nessuno (team tech: test automatici unit/integration/perf/security → `sdlc-debug`) | `plans/in-progress/<plan>/{bug-import-*.xlsx (origine=tecnico), BUG_REPORT.md sez. tecnici}` |
| 2c ondata (b) test funzionali | nessuno (team funzionale autonomo su playbook md/xlsx → `sdlc-debug`) | `plans/in-progress/<plan>/{bug-import-*.xlsx (origine=funzionale), BUG_REPORT.md sez. funzionali}` |
| 2c chiusura | nessuno (team tech `sdlc-executor` automatico) | `plans/done/<plan>/` (move automatico se task=Completata + bug_tecnici_aperti=0 + bug_funzionali_aperti=0) |

---

## Sintesi "Da implementare" vs "Esistente"

| Componente | Stato | Owner |
|---|---|---|
| Orchestratore Solaria + autenticazione GitHub App/PAT | DA IMPLEMENTARE | Team Solaria |
| FunctionalWeaver | DA IMPLEMENTARE | Team Solaria |
| FunctionalReviewer | DA IMPLEMENTARE | Team Solaria |
| Mockup Designer Agent | DA IMPLEMENTARE | Team Solaria |
| Skill review + clarify forkate Solaria-side | DA IMPLEMENTARE | Team Solaria (fork da claude-flow/skills/sdlc-reviewer, sdlc-clarify) |
| Playbook Generator | DA IMPLEMENTARE | Team Solaria |
| Detection commit `[sdlc-*]` (polling on-demand default, webhook opzionale) | DA IMPLEMENTARE | Team Solaria |
| `sdlc-profile-setup` (modalita' standalone + cartella `dataset/`) | ESISTENTE (Wave 3.1 del refactor) | Claude Code |
| 8 skill SDLC duali (legacy + standalone) | ESISTENTE (Wave 1-3 del refactor) | Claude Code |
| Schema `afu-manifest.json` v2 | ESISTENTE (Wave 0) | Claude Code (`templates/`) |
| Excel bug template v2 (colonna `origine`) | ESISTENTE (Wave 0) | Claude Code (`templates/`) |
| `Fasi-New-way-of-working.md` (2 fasi composite) | ESISTENTE (Wave 0) | Claude Code (`docs/`) |
| Documentazione di integrazione (questo file) | ESISTENTE (Wave 4) | Claude Code (`docs/`) |

---

## Riferimenti

- `Fasi-New-way-of-working.md` — descrizione 2 fasi composite (1a/b/c, 2a/b/c)
- `SOLARIA_SDLC_DIAGRAM.svg` — diagramma swimlane
- `claude-flow/templates/afu-manifest.schema.json` — schema v2 canonical
- `claude-flow/templates/BUG_EXCEL_TEMPLATE.xlsx` — template v2 canonical
- `claude-flow/SDLC_SKILLS_DOCUMENTATION.md` — documentazione skill SDLC + modalita' operative
- `~/.claude/plans/luminous-skipping-lamport.md` — piano refactor SDLC (5 waves)
