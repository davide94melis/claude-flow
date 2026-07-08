# Fase 1: Pre-Coding

### Fase 1a: Setup tecnico base
- **Tool:** GitHub (creazione manuale)
- **Descrizione:** Sotto-fase tecnica del setup, una tantum all'avvio del progetto. Il team tecnico crea manualmente su GitHub il repository, predispone la struttura `plans/` (`draft/`, `todo/`, `in-progress/`, `done/`), definisce e committa tramite la skill `sdlc-profile-setup` i due file tecnici di profilo progetto:
  - **`CONST.json`** — principi generici non negoziabili trasversali a qualunque progetto (es. OWASP Top 10, responsiveness, accessibility, performance budget, standard di logging/observability, convenzioni di sicurezza)
  - **`PROFILE.json`** — dettagli tecnici specifici del progetto: stack tecnologico, architettura, framework e linguaggi, linee guida architetturali, pattern di integrazione, scelte di deployment


- **Input:** stack tecnologico di alto livello del progetto + scelte architetturali iniziali
- **Output:** repository Git inizializzato + struttura `plans/` + file `CONST.json` e `PROFILE.json` committati + team tecnico abilitato su Claude Code
- **Attori coinvolti:** team tecnico

### Fase 1b: Creazione dataset di progetto e caricamento materiali funzionali
- **Tool:** Solaria (con persistenza/sincronizzazione su GitHub)
- **Descrizione:** Sotto-fase di creazione del **dataset Solaria del progetto** e caricamento dei materiali funzionali generici, eseguita con il supporto di Solaria. Il team funzionale fornisce a Solaria il branding kit, gli asset corporate, i materiali di marketing, il glossario di dominio e le info generiche sul perimetro funzionale e sugli attori coinvolti. Solaria **crea il dataset di lavoro del progetto** su cui opererà nelle sotto-fasi successive, guida l'upload, classifica e indicizza gli asset al suo interno secondo categorie standard (branding, corporate, glossario, attori, perimetro). Il dataset risiede su Solaria ma viene **ribaltato/sincronizzato in continuo su Git** in modo strutturato, così da essere sempre tracciabile e versionato nel repository. Si abilita il team funzionale sul progetto.
- **Input:** branding kit, asset corporate, documenti generici di dominio, info funzionale di alto livello
- **Output:** **dataset Solaria del progetto** creato e popolato con asset funzionali/branding indicizzati per categoria, ribaltato/sincronizzato su Git nel repo in modo strutturato + team funzionale abilitato su Solaria
- **Attori coinvolti:** team funzionale (con supporto Solaria)

### Fase 1c: Creazione, affinamento e validazione AFU (mockup e playbook di test OPZIONALI, dietro gate post-GO)
- **Tool:** Solaria
- **Agenti Solaria:** **FunctionalWeaver** (generazione AFU a partire dal dataset) + **FunctionalReviewer** (verifica copertura sezioni AFU con percentuale e gate GO/NO-GO) + **Mockup Designer Agent** (mockup di esempio **interattivi/cliccabili e accessibili WCAG 2.1 AA**, **opzionali** dietro gate post-GO) + **Accessibility Assistant** (assessor read-only WCAG 2.1 AA, sub-agent del Mockup Designer). A valle del GO intervengono inoltre le skill **review** e **clarify** per l'analisi di dettaglio con eventuale generazione di domande di chiarimento e relative risposte.
- **Descrizione:** Sotto-fase end-to-end di authoring funzionale gestita su Solaria. All'avvio del plan, il **FunctionalWeaver** apre il **dataset Solaria del progetto creato in Fase 1b** (con gli asset di branding/funzionali già indicizzati per categoria) e lo arricchisce con i contenuti specifici di questo plan: aggiunge automaticamente i file tecnici `CONST.json` e `PROFILE.json` letti dal repository, scansiona `plans/*` (read-only) per recuperare il contesto storico ed evitare conflitti/duplicazioni con plan esistenti, e ingerisce il materiale offline portato dal funzionale (note di riunione, mail, mockup grezzi, survey utente). Il dataset rimane **ribaltato/sincronizzato in continuo su Git** durante l'intero ciclo di authoring, così che lo stato del lavoro sia sempre tracciabile e versionato nel repository.

  Il **FunctionalWeaver** **genera l'AFU** elaborando direttamente i contenuti del dataset (materiale offline, asset funzionali/branding, `CONST.json`/`PROFILE.json`, contesto storico): produce in autonomia tutte le sezioni canoniche (funzionalità, attori, casi d'uso, flussi happy path + eccezioni, regole di business, vincoli tecnici, criteri di accettazione) senza condurre alcuna sessione di Q&A con il funzionale. La qualità e la completezza dell'AFU prodotta dipendono dalla ricchezza del dataset.

  Il **FunctionalReviewer** verifica la copertura di tutte le sezioni canoniche dell'AFU generata e produce **(a)** una **percentuale di copertura** complessiva e per-sezione (es. "stato corrente AFU = 20%": se consegnato così, i funzionali avrebbero solo il 20% delle informazioni necessarie per eseguire i test) e **(b)** un verdetto **GO / NO-GO** che funge da quality gate per passare allo step successivo. Se l'esito è **NO-GO**, il funzionale arricchisce il dataset con il materiale mancante (indicato implicitamente dalle sezioni a bassa copertura) e il FunctionalWeaver rigenera. Il ciclo arricchimento dataset → generazione → review prosegue finché il FunctionalReviewer non emette **GO**.

  Solo **a valle del GO**, intervengono le skill **review** e **clarify** che agiscono sull'AFU già coperto a livello macro per condurre un'**analisi di maggior dettaglio**: identificano corner case non considerati, punti non chiari, bad flow / unhappy path non coperti, ambiguità residue, incongruenze interne. Il funzionale risponde ai rilievi, l'AFU viene raffinato e le skill ri-passano fino a quando il livello di dettaglio è considerato accettabile.

  **Solo a valle del GO, e se l'analista lo conferma al gate (GATE-1),** il **Mockup Designer Agent** genera **mockup di esempio interattivi/cliccabili e modulari** delle interfacce e dei flussi descritti nell'AFU, partendo dai mockup grezzi forniti dal funzionale e dagli asset di branding caricati in Fase 1b; sono **accessibili per costruzione** (il Mockup Designer invoca l'**Accessibility Assistant**, assessor read-only WCAG 2.1 AA, e applica le remediation). I mockup vengono inclusi nel dataset e ribaltati su Git come asset di corredo all'AFU.

  L'AFU (e i mockup, se generati al GATE-1) viene poi portata allo stakeholder per validazione. Lo stakeholder fornisce feedback e, in caso di modifiche, Solaria **riaffina ciclicamente l'AFU** (e, se i mockup esistono, li rigenera) ripetendo il flusso completo (FunctionalWeaver → FunctionalReviewer per il GO macro → review/clarify per il dettaglio; rigenerazione mockup solo se il GATE-1 è attivo). Ogni round produce un commit incrementale con bump semver nel `afu-manifest.json` (`1.0` → `1.1` → ... → `1.N`) e changelog narrativo dei delta. Il ciclo termina solo quando **(a)** lo stakeholder ha validato esplicitamente il requisito, **(b)** il FunctionalReviewer ha emesso GO sull'ultima versione **e (c)** le skill review/clarify non rilevano più corner case aperti.

  Al consenso finale, **se l'analista lo conferma al gate (GATE-2)**, Solaria genera il **playbook di test funzionali** derivato dai criteri di accettazione e dai flussi dell'AFU: checklist destinate al team funzionale, prodotte sia in formato `.md` sia in `.xlsx` (per import in tracker/Jira o esecuzione su foglio), che verranno eseguite manualmente e in autonomia nella Fase 2c.

  Chiusa la sotto-fase, Solaria esegue l'handoff atomico al team tecnico spostando il package da `plans/draft/` a `plans/todo/` via GitHub Git Data API (tree-commit add+delete in singolo commit, server-side, no clone locale).
- **Input:** materiale raccolto offline dal funzionale (riunioni, mail, mockup grezzi, survey utente) + `CONST.json` e `PROFILE.json` caricati automaticamente nel dataset Solaria + asset di branding (da Fase 1b) + scansione `plans/*` (read-only) + feedback stakeholder
- **Output:** dataset Solaria del plan ribaltato su Git in `plans/todo/<YYYY-MM-DD>_<slug>/`:
  - `requirements/AFU.docx` (e/o `.md`) — versione finale stakeholder-approved (**sempre presente**)
  - `requirements/mockups/` — mockup di esempio generati dal Mockup Designer Agent (**OPZIONALE**: generato solo se l'analista dà GATE-1 "genero i mockup?" = Si)
  - `afu-manifest.json` v1.N (con percentuale di copertura finale, esito GO del FunctionalReviewer ed esito review/clarify registrati)
  - `tests/playbook.md` + `tests/playbook.xlsx` (checklist funzionali per esecuzione manuale autonoma, in entrambi i formati) (**OPZIONALE**: generato solo se l'analista dà GATE-2 "genero il playbook di test?" = Si)
  - commit di handoff `[solaria-handoff] <plan>: stakeholder approved, ready for dev`
  - _Nota RESUME:_ se mockup e/o playbook non sono stati generati al primo passaggio, l'Orchestrator può essere ri-invocato su un AFU già in GO per generare **solo** gli artefatti mancanti, con bump della minor version del manifest.
- **Attori coinvolti:** team funzionale (analista) + stakeholder
- **Skill / Agenti:** **FunctionalWeaver** (generazione AFU dal dataset) + **FunctionalReviewer** (copertura % + gate GO/NO-GO) + **Mockup Designer Agent** (interattivo/accessibile, opzionale GATE-1) + **Accessibility Assistant** (assessor WCAG 2.1 AA, sub-agent di 03) + skill **review** + skill **clarify** (analisi di dettaglio post-GO: corner case, bad flow, ambiguità) + skill di generazione playbook di test (md + xlsx, opzionale GATE-2)

> **Redesign authoring AFU (2026-07).** L'AFU è ora **feature-first**: corpo organizzato per feature `F-NN` con, per ciascuna, Sintesi / Attori / Casi d'uso / Flussi (happy + alternativi + edge case, un Mermaid) / Regole di business `RB-<AREA>-NN` / Criteri `AC-F<NN>-NN`. Regola DRY: ogni regola/criterio enunciato una sola volta, altrove si cita l'ID. In coda l'§6 "Indice di copertura canoniche" (auto-generato) mappa le 7 chiavi canoniche sulle feature/ID, così le skill Claude estraggono i requisiti senza parsing fragile.
>
> **Baseline legale.** Su progetti **greenfield web/public-facing** il Weaver propone in §3 i requisiti obbligatori per legge (cookie-consent, privacy/cookie policy, ToS, sitemap, dichiarazione di accessibilità, diritti GDPR, consenso minori se applicabile, e — se la piattaforma usa AI — trasparenza + consenso AI Act ex Reg. UE 2024/1689: l'uso dell'AI dev'essere esplicitato e l'utente deve poter accettarlo, pena l'indisponibilità delle funzionalità AI), flaggati e da confermare; il Reviewer va in **NO-GO** se mancano. Su **brownfield** il Weaver **chiede** al funzionale se inserirli o se già presenti (nessun gate automatico). Fonte: `contract/legal-baseline-web-eu.md`.
>
> **Clarify lossless (both).** Nel round INCOMING CLARIFY l'Orchestrator ricompila `CLARIFY.md` con le risposte del funzionale **e** rigenera l'AFU v2 (bump versione + parent_version + changelog), in sync.
>
> **Domande in linguaggio funzionale (dual-register).** Le OPEN_QUESTIONS e la Parte 1 di `CLARIFY.md` sono scritte in italiano business (decisione + conseguenze); l'eventuale dettaglio tecnico va in una nota separata "dettaglio tecnico (per il TL)".
>
> **Contesto-aware.** Con un contesto Solaria agganciato, l'Orchestrator abilita concorrenza (ownership per **feature**), resume da stato intermedio e multi-analista via `_state.json` (soglia heartbeat stantio 15 min). Senza contesto: comportamento attuale, con avviso esplicito.

# Fase 2: Coding & Test

### Fase 2a: Implementazione
- **Tool:** Claude Code
- **Descrizione:** Il team tecnico prende in carico il package consegnato da Solaria in `plans/todo/<plan>/`. La sotto-fase si articola in tre step:
  - **Review tecnica post-handoff (opzionale):** se il TL lo ritiene necessario (es. dominio complesso, package particolarmente articolato, dubbi architetturali), si lancia `sdlc-reviewer` per un'analisi di gap tecnici, ambiguità o disallineamenti architetturali non emersi nel self-review di Solaria, con generazione di `CLARIFY.md`. Le domande tornano a Solaria, che compila le risposte direttamente nel file e committa con prefisso `[solaria-clarify]`. `sdlc-clarify` ingerisce le risposte, ri-valuta e aggiorna il file. Loop fino a 0 bloccanti aperti. Se il package è chiaro e completo, lo step è skippabile e si passa direttamente al planning.
  - **Gap analysis e planning:** `sdlc-analyzer` confronta AFU vs codebase esistente, classifica i gap (Coperto/Parziale/Mancante/Discrepanza) e produce `PLAN.md` + `TASKS.md` con task assegnate ai developer, stream funzionali, wave di esecuzione e dipendenze. L'header `Processed AFU version` del `PLAN.md` viene allineato a `manifest.versione` per consentire detection dei delta futuri.
  - **Esecuzione e reporting:** `sdlc-executor` esegue le task con sottoagenti (implementazione codice + test + verifica in 3 fasi tecnica/coerenza/riesame), sposta automaticamente la cartella in `plans/in-progress/` all'avvio e produce commit + `PROGRESS.md` aggiornato cross-branch. `sdlc-progress-report` aggrega lo stato in un `PROGRESS.xlsx` consultabile da TL/PM (e in sola lettura dal funzionale via Solaria).
- **Input:** package AFU (+ mockup + playbook test se generati) in `plans/todo/<plan>/` + codebase esistente + team
- **Output:** (`CLARIFY.md` clean se review opzionale attivata) + `PLAN.md` + `TASKS.md` + codice committato + `PROGRESS.md` aggiornato + `PROGRESS.xlsx`; cartella plan spostata in `plans/in-progress/<plan>/`
- **Attori coinvolti:** team sviluppo (TL + developer); team funzionale e Solaria coinvolti solo per il Q&A in caso di review opzionale attivata
- **Skill:** `sdlc-reviewer` e `sdlc-clarify` (opzionali) + `sdlc-analyzer` + `sdlc-executor` + `sdlc-progress-report`

### Fase 2b (opzionale): Aggiornamento mid-flight in caso di cambio requisiti
- **Tool:** Solaria → Claude Code
- **Descrizione:** Se il business cambia esigenza dopo l'avvio dell'esecuzione, il funzionale arricchisce il dataset del plan con il nuovo materiale fornito dallo stakeholder e ripete su Solaria il flusso della Fase 1c producendo **AFU v2.0**: il FunctionalWeaver rigenera AFU + manifest a partire dal dataset aggiornato, il FunctionalReviewer riemette percentuale di copertura e gate GO/NO-GO sulla nuova versione, le skill review/clarify riapplicano l'analisi di dettaglio sui corner case e (**se mockup/playbook erano stati generati ai gate in F1c o via RESUME**) il Mockup Designer aggiorna i mockup impattati. Segue validazione stakeholder e, se presente, rigenerazione/aggiornamento del playbook di test (md + xlsx) impattato. Per un plan **AFU-only**, la 2b aggiorna solo AFU + manifest. Il dataset Solaria del plan resta ribaltato in continuo su Git. Il manifest finale viene aggiornato con `versione: "2.0"`, `parent_version: "1.N"` (ultima versione stakeholder-approved) e `changelog` narrativo dei delta. Lato Claude Code, `sdlc-updater` detecta l'incremento di versione confrontando l'header `Processed AFU version` di `PLAN.md` con `manifest.versione`, ingerisce il delta e aggiorna `PLAN.md`/`TASKS.md` preservando il progresso delle task gia' completate o in corso non impattate dal cambio.
- **Input:** nuove richieste stakeholder + AFU v1.N (da git history) + `PLAN.md`/`TASKS.md`/`PROGRESS.md` esistenti
- **Output:** AFU v2.0 package (+ mockup/playbook aggiornati **se presenti**) + `PLAN.md` e `TASKS.md` riallineati; `PROGRESS.md` preservato sui task non impattati
- **Attori coinvolti:** team funzionale + stakeholder + team sviluppo
- **Skill / Agenti:** **FunctionalWeaver** + **FunctionalReviewer** + **Mockup Designer Agent** + skill **review** + **clarify** (analisi di dettaglio post-GO) + skill di generazione playbook (riuso Fase 1c) + `sdlc-updater`

### Fase 2c: Test tecnici, funzionali e chiusura
- **Tool:** Claude Code (test tecnici) → esecuzione manuale del team funzionale → Claude Code (bug fix + chiusura)
- **Descrizione:** Dopo il rilascio in ambiente di test, la sotto-fase si svolge in due ondate sequenziali con due attori distinti, gestite con un quality gate intermedio:

  **(a) Test tecnici automatici — Team tecnico (Claude Code):** il team tecnico lancia per primo i test tecnici (unit, integration, performance, security). I fallimenti confluiscono in un Excel bug compatibile con `sdlc-debug`, salvato in `plans/in-progress/<plan>/bug-import-YYYYMMDD.xlsx`; `sdlc-debug` mappa i bug alle task, assegna agli sviluppatori, esegue i fix con sottoagenti e aggiorna `BUG_REPORT.md`. Il team tecnico itera fix → rerun fino a **validare l'esito tecnico** (test tecnici verdi), che funge da quality gate per l'ondata successiva.

  **(b) Test funzionali manuali — Team funzionale (esecuzione autonoma):** solo a valle della validazione tecnica, il team funzionale esegue **manualmente e in autonomia** il playbook di test funzionali generato da Solaria in Fase 1c (in formato `.md` o `.xlsx`, a scelta): percorre la checklist passo per passo, annota gli esiti e raccoglie le evidenze. Eventuali fallimenti vengono trascritti nello stesso Excel bug compatibile con `sdlc-debug` e lavorati dal team sviluppo con il medesimo flusso di fix.

  **Chiusura:** quando **tutte le task** sono in stato "Completata" e **tutti i bug** (tecnici + funzionali) in stato "Chiuso", `sdlc-executor` sposta automaticamente la cartella in `plans/done/<plan>/` e aggiorna il manifest. Lo step di chiusura è skippabile via flag esplicito se TL/PM vuole mantenere il plan aperto (soak in produzione, audit, ulteriori cicli). Solaria recepisce il completamento via polling on-demand della GitHub Commits API o webhook.
- **Input:** codice deployato in test environment + playbook test (md/xlsx) prodotto in Fase 1c (o aggiornato in 2b) + `TASKS.md` + criteri di accettazione AFU
- **Output:** test report tecnici + esiti playbook funzionale → Excel bug list → `BUG_REPORT.md` aggiornato + fix nel codice + cartella plan in `plans/done/<plan>/`
- **Attori coinvolti:** team tecnico (test tecnici + fix) → team funzionale (esecuzione manuale del playbook, in autonomia, senza Solaria) → team sviluppo (fix dei bug funzionali)
- **Skill:** `sdlc-debug` (per entrambe le ondate) + `sdlc-executor` (con check automatico delle condizioni di chiusura). Per l'ondata (b) non si invocano skill: il team funzionale esegue il playbook in autonomia.
