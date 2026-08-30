# Solaria ↔ SDLC Skills — Flusso End-to-End e Contratti di Interscambio

**Rev. corrente:** 2026-07-06
**Stato:** Contratto attivo per integrazione Solaria-side. Allinearsi a `Fasi-New-way-of-working.md` (2 fasi composite) prima di proporre cambi.
> Rev. 2026-07-06: aggiunta la sezione **"Layout dataset in fallback (per-progetto)"** — namespacing per-progetto degli output Solaria nel dataset condiviso quando il team funzionale non ha GitHub.
**Scopo:** Definire come l'agente esterno **Solaria** si integra a monte del nostro processo SDLC, dalla creazione del dataset di progetto fino alla chiusura post-testing, e formalizzare i contratti d'interscambio (schema manifest, formati output, convenzioni commit).

---

## Premessa

L'agente **Solaria** (in fase di progettazione presso un altro team, opera via API Anthropic — non Claude Code) assiste il **team funzionale** nella produzione e manutenzione dell'AFU (Analisi Funzionale Utente). L'**AFU e' sempre prodotta**; i **mockup** e il **playbook test** sono invece artefatti **opzionali**, generati solo se l'analista lo richiede esplicitamente a due gate distinti post-GO (GATE-1 "genero i mockup?" e GATE-2 "genero il playbook di test?", ognuno indipendente Si/No). Un package puo' quindi essere consegnato in modalita' **solo-AFU** (senza `requirements/mockups/` e senza `tests{}` nel manifest); in un secondo momento l'Orchestrator, re-invocato su un'AFU gia' GO, puo' rilevare gli artefatti mancanti e generare solo quelli (bump minor del manifest). Le skill `sdlc-*` di Claude Code prendono in carico il flusso dal momento in cui Solaria fa l'**handoff** del package alla repo del progetto, tollerano l'assenza di mockup/playbook, e producono codice, test e reportistica fino alla chiusura del plan.

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
    │   ├── requirements/{AFU-<slug>.md, mockups/}
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

> Nota: `requirements/mockups/` e `tests/playbook.{md,xlsx}` sono **opzionali** — presenti solo se l'analista ha attivato GATE-1 (mockup) e/o GATE-2 (playbook) post-GO. Un package solo-AFU non li contiene.

### Layout dataset in fallback (nessun GitHub — modalità normale del team funzionale)

L'albero qui sopra è quello della **spec-repo GitHub**. Il team funzionale **non ha accesso a GitHub**, quindi gli agenti Solaria girano in **fallback**: gli artefatti prodotti dai tool di generazione (AI Ghost Writer, Generative UI, Python) **non** finiscono in una repo ma si materializzano nel **dataset Solaria**, che è **unico e condiviso tra tutti i team/progetti**. Per evitare collisioni cross-progetto, gli agenti replicano nel dataset la **stessa alberatura**, con **una cartella per progetto** al posto della repo:

```
<progetto>/                                   ← = slug della spec-repo (kebab); se non c'è repo → kebab del nome progetto
  plans/<stato>/<YYYY-MM-DD>_<slug>/          ← <stato> ∈ {draft, todo, in-progress, done}
    requirements/
      AFU-<slug>.md
      mockups/<schermata>.{html,png,svg}      (opzionale, GATE-1)
    tests/
      playbook.md                             (opzionale, GATE-2)
      playbook.xlsx                           (opzionale, GATE-2)
    afu-manifest.json                         (plan root)
    CLARIFY.md                                (inbound: drag&drop analista, in todo/)
```

Regole (definite nel System Prompt dell'Orchestrator, sezione `DATASET LAYOUT`, e applicate dai worker 01/03/04):
- **`<progetto>`** è derivato **una sola volta** dall'Orchestrator (slug spec-repo; se non c'è repo, kebab del nome progetto) e passato ai worker come `{project_folder, dataset_base_path}`; i worker non lo ri-derivano quando orchestrati.
- **Doppio meccanismo (belt-and-suspenders):** se il tool di generazione espone un campo cartella/destinazione → impostarlo alla sottocartella (sovrascrive l'auto-bucket `assistant`/root di Solaria); **in ogni caso** il titolo del documento usa la forma piatta collision-safe con `__` al posto di `/` — es. `<progetto>__plans__<stato>__<YYYY-MM-DD>_<slug>__requirements__AFU-<slug>.md`. Mai un nome nudo (`AFU.md`, `playbook.md`, `playbook.xlsx`) nella root condivisa.
- **draft→todo** in fallback: nessun rename atomico → un solo stato-target per emissione (authoring su `draft/`; all'handoff si emette su `todo/` e si cancella la copia draft).
- **Invariante manifest:** il prefisso `<progetto>/plans/...` è **solo** collocazione nel dataset e **non entra mai** nei valori del manifest — `files[]` resta relativo a `requirements/`, `tests{}` resta relativo alla plan-root.

> ⚠️ **Cleanup una-tantum:** i file già scaricati "piatti" nella root del dataset condiviso vanno riordinati **a mano** nella rispettiva cartella `<progetto>/...` (gli agenti non spostano file preesistenti).

`.br-local.json` in ogni repo applicativa del developer:
```json
{ "project_repo": "<path-locale-del-clone>", "project_name": "<nome>", "developer": "<nome-dev>" }
```

---

## Agenti Solaria-side (DA IMPLEMENTARE dal team Solaria)

Il team Solaria deve produrre i seguenti agenti, tutti via API Anthropic (no Claude Code), che operano contro la project_repo via GitHub API. Le skill SDLC originali in `~/.claude/skills/` restano intatte: il team Solaria mantiene fork adattati Solaria-side.

Il roster e' composto da **7 agenti**: **00** AFU Orchestrator, **01** FunctionalWeaver, **02** FunctionalReviewer, **03** Mockup Designer, **04** Playbook Generator, **05** Accessibility Assistant (sub-agente di 03, non di 00), **06** Coherence Assessor (sub-agente di 03: coerenza mockup↔AFU). Mockup Designer (03) e Playbook Generator (04) sono invocati solo su opt-in dell'analista ai gate post-GO (GATE-1 / GATE-2); Accessibility Assistant (05) e Coherence Assessor (06) sono attivati da 03 e quindi solo se GATE-1 e' attivo.

### A. FunctionalWeaver (Fase 1c — generazione AFU dal dataset)

**Quando**: F1c authoring iniziale + ogni round stakeholder F2 + update mid-flight F2b
**Input**: dataset Solaria del progetto (caricato in F1b) + `CONST.json` + `PROFILE.json` + scansione `plans/*` (read-only) + materiale offline funzionale (note, mail, mockup grezzi)
**Output**: `plans/draft/<plan>/requirements/AFU-<slug>.md` + `afu-manifest.json` v1.0/v1.N/v2.N
**Caratteristica chiave**: **NON conduce Q&A col funzionale**. Genera l'AFU **direttamente dal dataset**. La qualita' dell'AFU dipende dalla ricchezza del dataset. Itera con FunctionalReviewer fino a GO.
**Implementazione**: prompt engineering con API Anthropic. System message con profilo + dataset come context.

### B. FunctionalReviewer (Fase 1c — quality gate GO/NO-GO)

**Quando**: F1c dopo ogni generazione FunctionalWeaver + ogni round stakeholder F2 + ogni update F2b
**Input**: `requirements/AFU-<slug>.md` + dataset corrispondente
**Output**:
- Aggiornamento `afu-manifest.json` con `coverage.{overall_percent, by_section{...}}` e `gate_outcome: "GO" | "NO-GO"`
- Se NO-GO: log delle sezioni a bassa copertura (segnale implicito al funzionale su cosa manca nel dataset)
**Caratteristica chiave**: quality gate **automatico**. Se NO-GO, blocca il passaggio a review/clarify Solaria-side. Il funzionale arricchisce il dataset, FunctionalWeaver rigenera, FunctionalReviewer rivaluta. Loop fino a GO.
**Implementazione**: prompt engineering scorer (rubric per sezione AFU) con API Anthropic. Output strutturato JSON convertito in campi manifest.

### C. Mockup Designer Agent (03) (Fase 1c — generazione mockup, **opzionale GATE-1**)

**Quando**: solo se l'analista attiva **GATE-1** post-GO ("genero i mockup?") + F2b se cambio requisiti impatta UI. Se GATE-1 = No, l'agente non viene invocato e il package resta solo-AFU.
**Modello**: Claude 4.7 Opus, temperature 0.
**Input**: mockup grezzi forniti dal funzionale + asset branding (`dataset/branding/`) + AFU corrente
**Output**: mockup HTML **interattivi/cliccabili e modulari** in `plans/draft/<plan>/requirements/mockups/`, **accessibili by construction** (WCAG 2.1 AA)
**Caratteristica chiave**: produce mockup HTML interattivi (navigabili, cliccabili) coerenti col branding e accessibili per costruzione. Non sostituisce il design vero, ma da' al team tech un baseline visuale e di interazione. Per garantire l'accessibilita' invoca il sub-agente **Accessibility Assistant (05)** e applica le remediation che questo restituisce.
**Implementazione**: generazione HTML/CSS/JS modulare via API Anthropic + ciclo di assessment WCAG con l'Accessibility Assistant (05).

### C-bis. Accessibility Assistant (05) (sub-agente di 03 — assessor WCAG 2.1 AA)

**Quando**: invocato **dal Mockup Designer (03)** durante la generazione dei mockup (quindi solo se GATE-1 e' attivo). E' un sub-agente di 03, **non** dell'Orchestrator.
**Modello**: Claude 4.6 Sonnet.
**Input**: i mockup HTML prodotti da 03
**Output**: report di remediation WCAG 2.1 AA (read-only sull'assessment: non scrive i file, restituisce a 03 le correzioni da applicare)
**Caratteristica chiave**: assessor **read-only** di conformita' WCAG 2.1 AA. Non modifica direttamente i mockup: 03 applica le remediation restituite.
**Implementazione**: prompt engineering scorer WCAG 2.1 AA con API Anthropic, output strutturato consumato da 03.

### C-ter. Coherence Assessor (06) (sub-agente di 03 — coerenza mockup↔AFU)

**Quando**: invocato **dal Mockup Designer (03)** durante il *coherence pass*, dopo la generazione dei mockup HTML dal Contratto UI (quindi solo se GATE-1 e' attivo). E' un sub-agente di 03, **non** dell'Orchestrator.

**Input**: i mockup HTML prodotti da 03 + il **Contratto UI** dell'AFU (schermate `SC-F<NN>-NN`, componenti tipizzati con campi/colonne/widget, trigger & navigazione) + i requisiti trasversali applicabili (MFA/OTP, legali/consenso, NFR con impatto UI, a11y)
**Output**:
- report di remediation ritornato a 03 (issue per schermata: elemento del contratto → `COVERED / ASSUMED / OPEN-QUESTION / FIXED`, divergenza mancante/inventato/difforme/trasversale-violato, fix passo-passo) — 03 applica e richiede il re-check fino a `COERENTE`
- il report persistibile `requirements/mockup-coherence-report.md` (+ copia EN `mockup-coherence-report.en.md`), committato dall'Orchestrator (single writer) e referenziato in `afu-manifest.json.coherence`
**Caratteristica chiave**: assessor **read-only** — verifica il "cosa" (contenuto mockup vs AFU), complementare all'Accessibility Assistant (05) che verifica il "come" (WCAG). Non modifica i mockup: 03 applica le remediation. Alimenta la verifica dinamica di `sdlc-verifier` a valle, che ricontrolla lo stesso Contratto UI sull'app reale.
**Implementazione**: prompt engineering (rubric di coerenza per Contratto UI) con API Anthropic, output strutturato consumato da 03.

### D. Skill review + clarify forkate Solaria-side (Fase 1c post-GO + F2/F2b)

**Quando**: solo **dopo** che FunctionalReviewer ha emesso GO
**Input**: AFU + dataset
**Output**:
- `plans/draft/<plan>/REVIEW.md` con rilievi dettaglio (corner case, bad flow, unhappy path, ambiguita' residue, incongruenze interne)
- Aggiornamento `afu-manifest.json` con `review_clarify_status: "open" | "closed"`
**Caratteristica chiave**: fork delle skill `sdlc-reviewer` + `sdlc-clarify` Claude Code, adattate per analisi dettaglio post-GO (le originali sono per review tech post-handoff). Iterazione col funzionale tramite Solaria fino a `closed`.
**Implementazione**: prompt engineering riusando la logica di categorizzazione problemi delle skill originali.

### E. Playbook Generator (04) (Fase 1c — generazione test funzionali, **opzionale GATE-2**)

**Quando**: solo se l'analista attiva **GATE-2** post-GO ("genero il playbook di test?"), al consenso finale stakeholder (gate=GO + review_clarify=closed) + F2b se delta v2 impatta criteri accettazione. Se GATE-2 = No, il playbook non viene generato e il manifest non contiene `tests{}`.
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
| `tests` | `{playbook_md, playbook_xlsx}` | Playbook Generator (F1c) | sdlc-analyzer (header PLAN.md), sdlc-executor (log informativo F2c) — **OPZIONALE**: presente solo se l'analista ha attivato GATE-2 e il playbook e' stato generato; altrimenti il campo e' omesso. |
| `coherence` | `{report_md, report_en_md}` | Coherence Assessor (06) via Mockup Designer (F1c) | sdlc-analyzer / sdlc-verifier (Contratto UI) — presente **ogni volta che i mockup sono generati** (GATE-1), non opt-in |

> Le voci `mockups/...` in `files[]` sono **opzionali** allo stesso modo: presenti solo se l'analista ha attivato GATE-1. Un package solo-AFU elenca in `files[]` la sola AFU.

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
  "files": ["AFU-login-sso.md", "mockups/login.png", "mockups/forgot-password.png"],
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
  },
  "coherence": {
    "report_md": "mockup-coherence-report.md",
    "report_en_md": "mockup-coherence-report.en.md"
  },
  "screen_index": ["SC-F01-01", "SC-F01-02", "SC-F02-01"]
}
```

**Campi opzionali aggiunti (back-compat — i manifest legacy restano validi):**
- `legal_baseline`: `{ "applicable": bool, "jurisdiction": "EU-IT", "items": [ { "id": "cookie-consent", "status": "included" | "already_present" | "scoped_out" } ] }`
- `feature_index`: `["F-01", "F-02", ...]` — navigazione feature-first.
- `rule_index`: `["RB-<AREA>-NN", ...]` — indice regole di business.
- `screen_index`: `["SC-F<NN>-NN", ...]` — indice schermate del Contratto UI (prodotto dal FunctionalWeaver in `### Schermate & Interazioni`, consumato da Mockup Designer, Coherence Assessor 06 e `sdlc-verifier`).

`coverage.by_section` resta INVARIATO (le 7 chiavi canoniche: funzionalita, attori, casi_uso, flussi, regole_business, vincoli_tecnici, criteri_accettazione) per back-compat 1:1 col Reviewer.

### Struttura AFU feature-first (v2)

File AFU: `requirements/AFU-<slug>.md`. Front-matter YAML: `nome, versione, parent_version?, feature_index[], rule_index[]`.

Ordine sezioni (obbligatorio):
0. Executive summary (1 paragrafo, linguaggio piano)
1. Glossario & Attori (tabella globale)
2. Perimetro & Dipendenze (incl. esclusioni)
3. Requisiti obbligatori/legali (greenfield: baseline; brownfield: esito Q&A)
4. Funzionalità (CORPO feature-first): per feature `## F-NN — <nome>` con sotto-blocchi Sintesi / Attori coinvolti (rif. §1) / Casi d'uso / Flussi (happy + alternativi + EDGE CASE, un Mermaid per feature) / Regole di business (RB-<AREA>-NN enunciate QUI una sola volta) / Criteri di accettazione (AC-F<NN>-NN)
5. Vincoli tecnici (funzionali, globali)
6. Indice di copertura canoniche (AUTO-GENERATO): le 7 chiavi canoniche → quali F-.. / RB-.. / AC-.. le coprono

ID: feature `F-01`... (2 cifre); regola `RB-<AREA>-NN` (AREA maiuscolo breve, NN 2 cifre); criterio `AC-F<NN>-NN`.
Regola DRY: ogni RB/AC enunciato UNA VOLTA alla fonte; altrove si cita l'ID, mai si riscrive il testo.

### `CLARIFY.md` con placeholder per Solaria (F2a opzionale)

Quando il TL invoca `sdlc-reviewer` post-handoff in F2a (opzionale standalone), viene generato un `CLARIFY.md` con placeholder `*(inserire qui la risposta)*` sotto ogni domanda. Solaria detecta il nuovo commit `[sdlc-reviewer]` via polling Commits API o webhook, compila le risposte direttamente nel MD via Contents API e committa con prefisso `[solaria-clarify]`. `sdlc-clarify` lato Claude Code rileva il commit Solaria via `git log --grep="^\[solaria-clarify\]"` e attiva la **Modalita' C** (auto-detection). No DOCX in standalone.

### Loop review/clarify bidirezionale (INCOMING CLARIFY)

> ⚠️ **Vincolo tool GitHub (2026-06-15):** il tool GitHub di Solaria, allo stato attuale, crea un **branch + una PR per OGNI file** anziche' un commit atomico multi-file. Finche' e' cosi', lo scambio del `CLARIFY.md` (e dell'AFU rivista) **non** passa da GitHub Contents/polling come descritto nel paragrafo precedente, ma da **drag&drop nel dataset Solaria**. Il modello a polling/webhook resta il target quando il tool supportera' i commit atomici (coerente v3).

Flusso effettivo del ciclo (step manuali, demo-friendly):
1. Claude `sdlc-reviewer` produce `CLARIFY.md` in `plans/todo/<plan>/` (Parte 1 domande funzionale + Parte 2 assunzioni `A-XXX` / disallineamenti `D-XXX`).
2. L'analista **carica `CLARIFY.md` nel dataset Solaria** (drag&drop).
3. L'**Orchestrator** (branch *INCOMING CLARIFY*) legge il file via **Browse Dataset / Semantic Search**, estrae le domande (Parte 1 + i `D-XXX` che richiedono una decisione funzionale) e le passa al **FunctionalWeaver**.
4. Il Weaver le ritorna come `OPEN_QUESTIONS`; l'Orchestrator alza il proprio **Interactive Questions Form**; le risposte dell'analista rigenerano l'**AFU v2** (`AFU-<slug>.md`, bump `versione` + `parent_version` + changelog).
5. Re-gate FunctionalReviewer (deve restare GO). `review_clarify_status`: `open` durante il round, `closed` a convergenza.
6. L'Orchestrator emette AFU v2 + manifest + `[solaria-update] <plan>: round chiarimenti da CLARIFY`; l'analista li ricolloca in `plans/todo/<plan>/` e Claude rilancia `sdlc-reviewer`/`sdlc-clarify`. Loop fino a CLARIFY risolto → `sdlc-analyzer`.

Le **due review** restano distinte: il **gate Solaria** (FunctionalReviewer, copertura GO/NO-GO, pre-handoff) ≠ la **review Claude** (`sdlc-reviewer`, qualita' + chiarimenti vs codice, post-handoff).

**Clarify-both (nuovo, #1).** Dopo aver raccolto le risposte, l'Orchestrator (single writer) esegue ENTRAMBE le scritture:
1. Ricompila `CLARIFY.md`: campi "Risposta del funzionale" + "Data risposta" in Parte 1; stato assunzioni `A-XXX` + risoluzione disallineamenti `D-XXX` in Parte 2; aggiorna "Riepilogo per sdlc-analyzer". NON modifica domande/categorie originali.
2. Rigenera l'AFU v2 con bump `versione` + `parent_version` + `changelog`.
Emissione: `CLARIFY.md` con commit `[solaria-clarify]`, AFU con `[solaria-update]`. Trasporto: via contesto se presente, altrimenti dataset drag&drop.
Lato Claude: `sdlc-clarify` Modalità C (auto-detect `[solaria-clarify]`) ora acquisisce un `CLARIFY.md` DAVVERO compilato (non più solo AFU rigenerato).

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

### Output FunctionalReviewer (02) esteso

{ "coverage": { "overall_percent": int, "by_section": { 7 chiavi int } },
  "quality": { "no_repetition": int, "edge_case_coverage": int, "readability": int },
  "legal_baseline": { "applicable": bool, "missing": [ids] },
  "gate_outcome": "GO" | "NO-GO", "low_coverage_sections": [], "notes": "..." }

Gate GO se e solo se: overall_percent ≥ 85 AND ogni by_section ≥ 70 AND quality.no_repetition ≥ 85 AND (legal_baseline.applicable ? legal_baseline.missing == [] : true).

### Schema domanda dual-register (Weaver ↔ sdlc-reviewer)
{ id, feature, source, context_funzionale, domanda_funzionale, opzioni: [{ label, conseguenza }], dettaglio_tecnico?, allow_note }
Testo primario in italiano business; il dettaglio tecnico SOLO dentro `dettaglio_tecnico` (per il TL).

### Baseline legale
File: `solaria-agents/contract/legal-baseline-web-eu.md`. Campi voce: `id, titolo, quando_si_applica, riferimento_normativo, nota_funzionale`. Voci default (EU-IT, 9): cookie-consent, privacy-policy, cookie-policy, tos, sitemap, accessibility-statement, gdpr-rights, minors-consent (condizionale: minori nel perimetro), ai-act-transparency (condizionale: la piattaforma usa AI — Reg. UE 2024/1689 art. 50, uso AI esplicitato + consenso utente, pena indisponibilità funzionalità AI).
Greenfield + web ⇒ il Weaver propone gli item in §3 flaggandoli, e il Reviewer va in NO-GO se mancano. Brownfield ⇒ il Weaver CHIEDE al funzionale (una OPEN_QUESTION per cluster) se inserirli o se già presenti; nessun gate automatico.

### Contesto: concorrenza / resume (`_state.json`)
Path: `<progetto>/plans/<stato>/<plan>/_state.json`. Chiavi: `plan, versione, phase("authoring"|"gate"|"post-go"|"clarify"|"handoff"), gate_outcome, review_clarify_status("open"|"closed"), open_questions[], features{ "F-NN": { owner, status("todo"|"in-progress"|"done"), heartbeat(ISO8601) } }, plan_lock{ owner, heartbeat }`.
La feature è l'unità di ownership; gli artefatti plan-level (manifest, indice §6, sezioni globali §1/§2/§3/§5) sono protetti da `plan_lock` (single-writer). Soglia heartbeat stantio = 15 min. Senza contesto: niente `_state.json`, comportamento attuale + avviso esplicito "nessun contesto".

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
| 1c (Authoring AFU) | FunctionalWeaver + FunctionalReviewer (loop) → review/clarify forkate (post-GO loop) → *[opt-in]* Mockup Designer (03) + Accessibility Assistant (05) se **GATE-1** → *[opt-in]* Playbook Generator (04) se **GATE-2** | sempre: `plans/draft/<plan>/{requirements/AFU.*, afu-manifest.json, REVIEW.md}`. Opzionali (solo su opt-in post-GO): `requirements/mockups/` (GATE-1), `tests/playbook.{md,xlsx}` + `tests{}` nel manifest (GATE-2). Handoff finale `plans/todo/<plan>/...` via Git Trees API anche in modalita' **solo-AFU** |
| 2a (Implementazione) | nessuno (team tech: `sdlc-reviewer`/`sdlc-clarify` opzionali, poi `sdlc-analyzer`, `sdlc-executor`, `sdlc-progress-report`) | `plans/todo/<plan>/{CLARIFY.md opzionale, PLAN.md, TASKS.md}` → `plans/in-progress/<plan>/{PROGRESS.md, PROGRESS.xlsx}` |
| 2a Q&A loop (INCOMING CLARIFY) | Orchestratore Solaria: l'analista carica `CLARIFY.md` nel dataset (drag&drop), l'Orchestrator lo legge (Browse Dataset) → Weaver ripropone le domande via IQF → AFU v2 *(futuro: detection `[sdlc-reviewer]` via polling/webhook quando GitHub supportera' commit atomici)* | `plans/todo/<plan>/CLARIFY.md` compilato + AFU v2 + manifest (bump) con `[solaria-update]` |
| 2b (Update mid-flight) | FunctionalWeaver + FunctionalReviewer + review/clarify forkate + (Mockup Designer / Accessibility Assistant + Playbook Generator **solo se gia' presenti dai gate F1c o via RESUME**) → team tech `sdlc-updater` | `plans/in-progress/<plan>/{requirements/, afu-manifest.json v2.0}` + `tests/playbook.* rigenerato` e `requirements/mockups/` aggiornati **solo se presenti** (plan **AFU-only**: solo AFU + manifest) |
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
| Mockup Designer (03) — HTML interattivo/cliccabile + accessibile WCAG 2.1 AA (Claude 4.7 Opus) | DA IMPLEMENTARE | Team Solaria |
| Accessibility Assistant (05) — assessor read-only WCAG 2.1 AA, sub-agente di 03 (Claude 4.6 Sonnet) | DA IMPLEMENTARE | Team Solaria |
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
