# BR Pipeline POM — Piano di Implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementare il sistema BR Pipeline POM a 2 componenti: (1) br-pipeline — skill CLI per Claude Code con logica propria basata su manifest JSON, (2) BR Portal — web app Next.js su Vercel con viste per ruolo. Le 6 skill esistenti in `claude-flow` restano intatte per uso standalone.

**Architecture:** Logica propria + manifest JSON. br-pipeline lavora nativamente col manifest (single source of truth). I file MD (REVIEW, GAP_REPORT, PIANO, PROGRESSO) vengono generati dal manifest come viste retrocompatibili. Il portale legge/scrive lo stesso manifest via GitHub API. Auth con NextAuth + Vercel KV.

**Tech Stack:** Markdown skill file (br-pipeline), Next.js App Router, Vercel, NextAuth, Vercel KV (Redis), GitHub API, TypeScript

**Repo:** `https://github.com/davide94melis/portal-flow` (gia' esistente, vuoto)

**Spec:** `docs/superpowers/specs/2026-05-04-br-pipeline-pom-design.md` (in claude-flow)

**Decisioni chiave:**
- Le 6 skill esistenti in `claude-flow` restano intatte — zero modifiche
- br-pipeline ha logica propria ispirata alle skill ma basata sul manifest JSON
- CLI prima, portale dopo — il CLI funziona subito anche senza portale
- Il manifest e' la single source of truth; i file MD sono viste generate

---

## Struttura repo portal-flow

```
portal-flow/
  skill/
    br-pipeline/
      SKILL.md                # Skill CLI principale
      install.sh              # Symlink a ~/.claude/skills/br-pipeline/
  portal/
    src/
      app/                    # Next.js App Router
        (auth)/
          login/page.tsx
        dashboard/page.tsx
        br/
          nuovo/page.tsx
          [id]/
            page.tsx
            review/page.tsx
            piano/page.tsx
            task/page.tsx
            qa/page.tsx
        admin/page.tsx
        api/
          auth/[...nextauth]/route.ts
          webhooks/github/route.ts
          br/                 # API routes per CRUD manifest
      lib/
        github.ts             # GitHub API client
        manifest.ts           # Manifest read/write
        auth.ts               # NextAuth config
      components/             # UI components per ruolo
      types/
        manifest.ts           # TypeScript types dal manifest schema
    package.json
    next.config.ts
  shared/
    manifest.schema.json      # JSON Schema per validazione
    manifest.example.json     # Esempio compilato
    design-system.example.json
  docs/
    spec.md                   # Copia della spec
  README.md
  .br-portal-config.json      # Config globale portale
```

---

## Fasi di implementazione

Il piano e' diviso in 6 fasi. Le fasi 1-4 coprono il CLI (br-pipeline). Le fasi 5-6 coprono il portale. Ogni fase e' autosufficiente e produce un deliverable utilizzabile.

---

## Fase 1 — Fondazioni (repo + schema + struttura)

### Task 1.1: Setup repo portal-flow

**Files:**
- Create: `README.md`, `.gitignore`, struttura directory

- [ ] **Step 1:** Clonare il repo `portal-flow` e creare la struttura directory

```bash
git clone https://github.com/davide94melis/portal-flow.git
cd portal-flow
mkdir -p skill/br-pipeline portal shared docs
```

- [ ] **Step 2:** Creare `.gitignore` con:
  - `node_modules/`, `.next/`, `.env.local`, `.br-local.json`, `*.xlsx`

- [ ] **Step 3:** Creare `README.md` con descrizione del progetto, struttura, e link alla spec

- [ ] **Step 4:** Commit iniziale

---

### Task 1.2: Definire il manifest JSON schema

**Files:**
- Create: `shared/manifest.schema.json`
- Create: `shared/manifest.example.json`

- [ ] **Step 1:** Creare `shared/manifest.schema.json` — JSON Schema completo per il manifest BR. Deve validare tutti i campi definiti nella spec (sezione "BR Manifest"):
  - `version`, `nome`, `data_creazione`, `creato_da`, `stato_pipeline`
  - `codebase[]` con `nome` e `sigla`
  - `documenti[]` con `originale`, `convertito`, `tipo`
  - `team[]` con `nome`, `email`, `ruolo`, `seniority`, `reviewer`
  - `review` con `data`, `esito`, `problemi[]`, `assunzioni[]`, `disallineamenti_codice[]`
  - `qa` con `criteri_accettazione[]`
  - `gap_analysis` con `data`, `matrice[]`, `gap_aperti[]`
  - `piano` con `approvato`, `stream[]`, `task[]` (inclusi campi `qa_criteri[]`, `stato`, `progresso`)
  - `timeline[]` con `data`, `attore`, `ruolo`, `azione`, `stage`
  - Enumerazioni: `stato_pipeline` (onboard|review|clarify|analyze|approve|execute|verify|update|report), `stato_task` (da_iniziare|in_corso|completata|bloccata|annullata|sospesa), `priorita` (P0|P1|P2)

- [ ] **Step 2:** Creare `shared/manifest.example.json` — esempio compilato completo (quello nella spec, pulito e validato contro lo schema)

- [ ] **Step 3:** Commit

---

### Task 1.3: Definire template e config condivisi

**Files:**
- Create: `shared/design-system.example.json`
- Create: `shared/br-local.example.json`
- Create: `.br-portal-config.json`

- [ ] **Step 1:** Creare `shared/design-system.example.json` — template del design system per mockup (dalla spec, sezione "Design System per Mockup")

- [ ] **Step 2:** Creare `shared/br-local.example.json` — template `.br-local.json` con struttura `developer` + `paths`

- [ ] **Step 3:** Creare `.br-portal-config.json` — config globale portale (URL repo, branch default, ruoli disponibili, config notifiche)

- [ ] **Step 4:** Commit

---

### Task 1.4: Copiare la spec nel repo

**Files:**
- Create: `docs/spec.md`

- [ ] **Step 1:** Copiare `docs/superpowers/specs/2026-05-04-br-pipeline-pom-design.md` da claude-flow a `docs/spec.md` in portal-flow

- [ ] **Step 2:** Commit

---

## Fase 2 — br-pipeline Skill: Framework e Orchestrazione

### Task 2.1: Creare il framework della skill

**Files:**
- Create: `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Scrivere `SKILL.md` con:
  - **Frontmatter**: name, description (con trigger: "br-pipeline", "pipeline br", "le mie task")
  - **Introduzione**: posizionamento nel flusso, diagramma degli stage (S0-S8)
  - **Entry point unico**: logica di avvio che:
    1. Esegue `git pull` per sincronizzare
    2. Cerca manifest in `brs/*/manifest.json`
    3. Identifica il ruolo (TL/PM vs Dev da `.br-local.json`)
    4. Mostra BR attivi con stato pipeline
    5. Propone il next step basato su `stato_pipeline`

- [ ] **Step 2:** Sezione "Utilities condivise" nella skill:
  - **Lettura manifest**: `cat brs/<nome>/manifest.json | jq .`
  - **Scrittura manifest**: scrivi JSON → `git add` → `git commit -m "[br-pipeline] <nome>: <azione>"` → `git push`
  - **Timeline**: ogni azione significativa aggiunge un entry a `timeline[]`
  - **Generazione viste MD**: funzioni per generare REVIEW_BR.md, GAP_REPORT_BR.md, PIANO_IMPLEMENTAZIONE_BR.md, PROGRESSO_BR.md dal manifest

- [ ] **Step 3:** Sezione "Setup iniziale (.br-local.json)":
  - Alla prima invocazione come Dev, se `.br-local.json` non esiste, chiedi nome e path dei codebase
  - Crea il file gitignored

- [ ] **Step 4:** Commit

---

### Task 2.2: Creare install.sh

**Files:**
- Create: `skill/br-pipeline/install.sh`

- [ ] **Step 1:** Script che:
  1. Crea symlink `~/.claude/skills/br-pipeline/` → `<repo>/skill/br-pipeline/`
  2. Verifica che il link funzioni
  3. Suggerisce l'aggiunta del trigger in `~/.claude/CLAUDE.md`

- [ ] **Step 2:** Rendere eseguibile (`chmod +x`)

- [ ] **Step 3:** Commit

---

## Fase 3 — br-pipeline Skill: Stage CLI (S1, S3, S5, S7)

### Task 3.1: Stage S1 — Review (TL/PM)

**Aggiungere a:** `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Sezione `## Stage S1 — Review` con:
  - **Precondizioni**: `stato_pipeline == "onboard"`, documenti caricati in `brs/<nome>/docs/`
  - **Conversione documenti**: se i file in `docs/` non sono MD, convertili con doc-to-markdown/markitdown e salva il `.md` convertito; aggiorna `documenti[].convertito` nel manifest
  - **Analisi documentazione**: stessa logica di br-reviewer (analisi intra-doc, inter-doc, check leggero vs codice) ma scrivendo i risultati in `manifest.review.problemi[]` e `manifest.review.assunzioni[]`
  - **Generazione criteri QA iniziali**: popola `manifest.qa.criteri_accettazione[]` dalla documentazione
  - **Aggiornamento manifest**: `stato_pipeline = "review"`, `review.data`, `review.esito`, timeline entry
  - **Generazione vista MD**: genera `brs/<nome>/REVIEW_BR.md` dal manifest (retrocompatibilita')
  - **Output**: riepilogo problemi (bloccanti vs non bloccanti) e prossimo step proposto

- [ ] **Step 2:** Commit

---

### Task 3.2: Stage S3 — Analyze (TL/PM)

**Aggiungere a:** `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Sezione `## Stage S3 — Analyze` con:
  - **Precondizioni**: `stato_pipeline == "clarify"` (o `"review"` se si procede senza risposte)
  - **Incorpora risposte**: legge `review.problemi[].risposta` e `review.assunzioni[].risposta_funzionale` (compilati dal portale in S2)
  - **Esplorazione codebase**: per ogni `codebase[]` nel manifest, usa path da `.br-local.json` per esplorare struttura, modello dati, API, servizi (stessa logica di br-analyzer Fase 3)
  - **Gap analysis**: popola `manifest.gap_analysis.matrice[]` e `manifest.gap_analysis.gap_aperti[]`
  - **Generazione piano**: popola `manifest.piano.stream[]` e `manifest.piano.task[]` con tutti i campi (id, stream, owner, area, priorita, wave, attivita, descrizione, dipendenze, effort_gg, qa_criteri)
  - **QA test plan**: arricchisce `manifest.qa.criteri_accettazione[]` con dettagli tecnici
  - **Aggiornamento manifest**: `stato_pipeline = "analyze"`, timeline entry
  - **Generazione viste MD**: genera GAP_REPORT_BR.md e PIANO_IMPLEMENTAZIONE_BR.md dal manifest
  - **Output**: riepilogo gap, piano proposto, prossimo step (gate approvazione TL/PM)

- [ ] **Step 2:** Commit

---

### Task 3.3: Stage S5 — Execute (Dev)

**Aggiungere a:** `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Sezione `## Stage S5 — Execute` con:
  - **Precondizioni**: `piano.approvato == true` (gate esplicito)
  - **Identifica dev**: legge `.br-local.json` per nome, filtra task assegnate
  - **Mostra task**: solo le task con `owner == dev` e stato != completata, ordinate per wave e priorita'
  - **Selezione task**: propone la prossima task disponibile (non bloccata da dipendenze)
  - **Verifica dipendenze**: per ogni task, controlla che tutte le task in `dipendenze[]` siano in stato "completata" nel manifest
  - **Esecuzione con sottoagenti**: stessa logica di br-executor — scompone la task, lancia sottoagenti con contesto autosufficiente, verifica risultati
  - **Gestione merge task (T-MERGE-*)**: guida il merge senza sottoagenti
  - **Aggiornamento manifest**: aggiorna `task[].progresso`, `task[].stato`, `task[].branch`; timeline entry per ogni cambio di stato
  - **Suggerimento commit**: stessa logica di br-executor (mai committare autonomamente)
  - **Generazione vista MD**: aggiorna PROGRESSO_BR.md dal manifest

- [ ] **Step 2:** Commit

---

### Task 3.4: Stage S7 — Update (TL/PM)

**Aggiungere a:** `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Sezione `## Stage S7 — Update` con:
  - **Trigger**: TL/PM dice "il BR e' stato aggiornato" o il pipeline rileva nuovi documenti in `brs/<nome>/docs/`
  - **Delta analysis**: stessa logica di br-updater — confronta nuova documentazione con precedente, classifica delta (nuovo/modificato/rimosso)
  - **Aggiornamento manifest preservando progresso**: task completate restano, task nuove aggiunte con ID sequenziale, task rimosse segnate come annullate/sospese
  - **Ricalcolo piano**: wave, dipendenze, distribuzione team
  - **Aggiornamento manifest**: timeline entry, generazione viste MD aggiornate
  - **Output**: riepilogo delta con impatto su task esistenti

- [ ] **Step 2:** Commit

---

### Task 3.5: Orchestrazione stage e navigazione

**Aggiungere a:** `skill/br-pipeline/SKILL.md`

- [ ] **Step 1:** Completare la sezione entry point con la logica di navigazione tra stage:
  - Tabella di transizione stato_pipeline → azioni disponibili
  - Per TL/PM: mostra dashboard BR attivi, propone next step in base allo stato
  - Per Dev: mostra solo le proprie task, propone la prossima disponibile
  - Gestione multi-BR: se ci sono piu' BR, elenca e chiedi quale lavorare
  - Rilevamento automatico: "Il BR booking-v2 ha 3 risposte nuove dal funzionale — vuoi rivalutare?"

- [ ] **Step 2:** Commit

---

## Fase 4 — Registrazione e documentazione CLI

### Task 4.1: Registrare br-pipeline in CLAUDE.md

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1:** Aggiungere il blocco br-pipeline:

```markdown
# br-pipeline
- **br-pipeline** (`~/.claude/skills/br-pipeline/SKILL.md`) - pipeline POM completo per gestione BR con manifest JSON e viste per ruolo. Trigger: "br-pipeline", "pipeline br", "le mie task"
When the user says "br-pipeline", "pipeline br", "le mie task", or similar phrases about the BR pipeline or viewing assigned tasks, invoke the Skill tool with `skill: "br-pipeline"` before doing anything else.
```

- [ ] **Step 2:** Commit

---

### Task 4.2: Documentazione BR pipeline

**Files:**
- Update: `portal-flow/README.md`

- [ ] **Step 1:** Aggiornare README con:
  - Guida installazione skill (run install.sh)
  - Flusso POM completo con diagramma
  - Guida rapida per TL/PM e per Dev
  - Link alla spec

- [ ] **Step 2:** Commit

---

## Fase 5 — BR Portal: Foundation

### Task 5.1: Setup progetto Next.js

**Files:**
- Create: `portal/` — intero progetto Next.js

- [ ] **Step 1:** Inizializzare il progetto Next.js con App Router:
```bash
cd portal-flow
npx create-next-app@latest portal --typescript --tailwind --app --src-dir --eslint
```

- [ ] **Step 2:** Installare dipendenze:
```bash
cd portal
npm install next-auth @auth/core @vercel/kv @octokit/rest
npm install -D @types/node
```

- [ ] **Step 3:** Configurare Tailwind con il design system del progetto (colori, tipografia, componenti da `design-system/theme.json`)

- [ ] **Step 4:** Commit

---

### Task 5.2: Auth — NextAuth + Vercel KV

**Files:**
- Create: `portal/src/app/api/auth/[...nextauth]/route.ts`
- Create: `portal/src/lib/auth.ts`
- Create: `portal/src/app/(auth)/login/page.tsx`
- Create: `portal/src/middleware.ts`

- [ ] **Step 1:** Configurare NextAuth con CredentialsProvider (email+password):
  - Vercel KV per storage utenti (hash password con bcrypt)
  - Vercel KV per sessioni
  - Ruoli nel JWT: `funzionale`, `tech_lead`, `dev`, `qa`, `admin`

- [ ] **Step 2:** Creare pagina login (`/login`) con form email+password

- [ ] **Step 3:** Creare middleware per protezione route per ruolo:
  - `/dashboard` → solo `tech_lead`
  - `/br/nuovo` → solo `funzionale`
  - `/br/[id]/task` → solo `dev`
  - `/br/[id]/qa` → solo `qa`
  - `/admin` → solo `admin`
  - `/br/[id]` → tutti (vista cambia per ruolo)

- [ ] **Step 4:** Commit

---

### Task 5.3: GitHub API integration layer

**Files:**
- Create: `portal/src/lib/github.ts`
- Create: `portal/src/lib/manifest.ts`

- [ ] **Step 1:** Creare `github.ts` — client per GitHub API con Octokit:
  - `readFile(path)` — legge un file dal repo
  - `writeFile(path, content, message)` — scrive un file con commit
  - `listFiles(dir)` — lista file in una directory
  - `uploadFile(path, buffer)` — upload binario (docs, mockup)
  - Config: repo owner/name da env vars

- [ ] **Step 2:** Creare `manifest.ts` — layer sopra github.ts specifico per manifest:
  - `getManifest(brName)` → parsed manifest
  - `updateManifest(brName, updater)` → read-modify-write atomico con commit
  - `listBRs()` → lista BR con stato pipeline
  - `createBR(data)` → crea directory + manifest iniziale
  - Validazione contro JSON schema

- [ ] **Step 3:** Commit

---

### Task 5.4: Layout e navigazione per ruolo

**Files:**
- Create: `portal/src/app/layout.tsx`
- Create: `portal/src/components/nav/Sidebar.tsx`
- Create: `portal/src/components/nav/RoleGuard.tsx`

- [ ] **Step 1:** Layout principale con sidebar che cambia in base al ruolo:
  - Funzionale: "I miei BR", "Nuovo BR"
  - TL/PM: "Dashboard", "Tutti i BR"
  - Dev: "Le mie task"
  - QA: "Validazione"
  - Admin: "Utenti", "Design System"

- [ ] **Step 2:** Badge notifiche nella sidebar (conteggio eventi non letti)

- [ ] **Step 3:** Commit

---

### Task 5.5: Pagina admin

**Files:**
- Create: `portal/src/app/admin/page.tsx`
- Create: `portal/src/app/api/admin/users/route.ts`

- [ ] **Step 1:** Pagina `/admin` con:
  - Lista utenti registrati con ruolo
  - Form creazione utente (nome, email, password, ruolo)
  - Modifica/rimozione utente
  - Upload/modifica design system (theme.json)

- [ ] **Step 2:** API routes per CRUD utenti su Vercel KV

- [ ] **Step 3:** Commit

---

## Fase 6 — BR Portal: Viste per Ruolo

### Task 6.1: Vista Funzionale — Creazione BR (S0)

**Files:**
- Create: `portal/src/app/br/nuovo/page.tsx`
- Create: `portal/src/app/api/br/route.ts`
- Create: `portal/src/components/br/BRCreateForm.tsx`
- Create: `portal/src/components/br/DocUpload.tsx`

- [ ] **Step 1:** Pagina `/br/nuovo` con form multi-step:
  1. Nome e descrizione del BR
  2. Upload documenti (DOCX, PDF, XLSX, PPTX) con tag tipo (br, spec, mapping, mockup, altro)
  3. Upload mockup (PNG, JPG) o placeholder per "Crea con Claude Design"
  4. Selezione team tecnico (da lista utenti con ruolo Dev)
  5. Selezione TL/PM
  6. Anteprima e invio

- [ ] **Step 2:** API route `POST /api/br` che:
  - Crea directory `brs/<nome>/` nel repo via GitHub API
  - Upload documenti in `brs/<nome>/docs/`
  - Upload mockup in `brs/<nome>/mockups/`
  - Crea `manifest.json` iniziale con `stato_pipeline: "onboard"`
  - Aggiunge entry nella timeline

- [ ] **Step 3:** Lista BR del funzionale nella home (`/br`) — i propri BR con stato

- [ ] **Step 4:** Commit

---

### Task 6.2: Vista Funzionale — Risposte al Review (S2)

**Files:**
- Create: `portal/src/app/br/[id]/review/page.tsx`
- Create: `portal/src/components/br/ReviewQuestions.tsx`

- [ ] **Step 1:** Pagina `/br/[id]/review` con:
  - Domande dal manifest (`review.problemi[]`), raggruppate per priorita' (bloccanti prima, con banner visivo)
  - Ogni domanda non bloccante mostra l'assunzione proposta
  - Campo risposta inline per ogni domanda
  - Salvataggio parziale (puo' tornare dopo)
  - Ogni salvataggio aggiorna `review.problemi[].risposta` e `review.problemi[].data_risposta` nel manifest via GitHub API
  - Aggiorna `stato_pipeline` a "clarify" al primo salvataggio

- [ ] **Step 2:** Indicatore di completamento: "X/Y domande con risposta"

- [ ] **Step 3:** Commit

---

### Task 6.3: Vista TL/PM — Dashboard e Approvazione Piano (S4)

**Files:**
- Create: `portal/src/app/dashboard/page.tsx`
- Create: `portal/src/app/br/[id]/piano/page.tsx`
- Create: `portal/src/components/dashboard/BRCard.tsx`
- Create: `portal/src/components/dashboard/Timeline.tsx`

- [ ] **Step 1:** Dashboard `/dashboard` con:
  - Card per ogni BR con: nome, stato pipeline, progresso %, bloccanti, ultimo evento
  - Filtri per stato pipeline
  - Timeline unificata (ultimi eventi da tutti i BR)

- [ ] **Step 2:** Pagina `/br/[id]/piano` con:
  - Visualizzazione piano completo (stream, task, wave, dipendenze)
  - GATE esplicito: bottone "Approva piano" che setta `piano.approvato = true` e `piano.data_approvazione`
  - Assegnazione/riassegnazione task (drag-and-drop o dropdown)
  - Dopo approvazione: i Dev vedono le task

- [ ] **Step 3:** Vista dettaglio BR `/br/[id]` (per TL/PM): stato completo, risposte funzionale, gap report, piano, progresso, timeline

- [ ] **Step 4:** Commit

---

### Task 6.4: Vista Dev — Le proprie task

**Files:**
- Create: `portal/src/app/br/[id]/task/page.tsx`
- Create: `portal/src/components/task/TaskList.tsx`
- Create: `portal/src/components/task/TaskCard.tsx`

- [ ] **Step 1:** Pagina `/br/[id]/task` con:
  - Solo le task assegnate al Dev loggato
  - Progresso per task (barra visuale)
  - Stato: da_iniziare, in_corso, completata, bloccata
  - Blocchi visibili (task da cui dipendo e il loro stato)
  - Nota: il Dev lavora via Claude Code (br-pipeline), il portale e' read-only per lui

- [ ] **Step 2:** Commit

---

### Task 6.5: Vista QA — Validazione (S6)

**Files:**
- Create: `portal/src/app/br/[id]/qa/page.tsx`
- Create: `portal/src/components/qa/CriteriaList.tsx`
- Create: `portal/src/components/qa/DefectForm.tsx`

- [ ] **Step 1:** Pagina `/br/[id]/qa` con:
  - Criteri di accettazione per BR (`qa.criteri_accettazione[]`)
  - Per ogni task completata: criteri linkati via `task[].qa_criteri[]`
  - Form per registrare risultato test: pass/fail per criterio
  - Form per segnalare difetti con descrizione
  - Aggiornamento manifest: `qa.criteri_accettazione[].validato_qa`, `qa.criteri_accettazione[].risultato_test`

- [ ] **Step 2:** Commit

---

### Task 6.6: Notifiche

**Files:**
- Create: `portal/src/app/api/webhooks/github/route.ts`
- Create: `portal/src/lib/notifications.ts`
- Create: `portal/src/components/nav/NotificationBadge.tsx`

- [ ] **Step 1:** Webhook GitHub → Vercel endpoint:
  - Ascolta push events sul repo
  - Parsare il commit message per capire cosa e' cambiato
  - Creare notifica in Vercel KV per il/i destinatari

- [ ] **Step 2:** Sistema notifiche in-app:
  - Badge nell'header con conteggio non letti
  - Dropdown con lista notifiche
  - Mark as read

- [ ] **Step 3:** Mapping eventi → destinatari (dalla tabella nella spec):
  - Nuovo BR creato → TL/PM assegnato
  - Review completato → Funzionale
  - Risposte ricevute → TL/PM
  - Piano approvato → Dev assegnati
  - Task completata → QA, TL/PM
  - QA valida/rifiuta → Dev, TL/PM
  - BR aggiornato → TL/PM

- [ ] **Step 4:** Email opzionale (configurabile per utente) — seconda iterazione, non bloccante

- [ ] **Step 5:** Commit

---

### Task 6.7: Deploy su Vercel

**Files:**
- Create: `portal/vercel.json` (se necessario)

- [ ] **Step 1:** Configurare il progetto su Vercel:
  - Collegare il repo GitHub
  - Settare env vars: `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `NEXTAUTH_SECRET`, `KV_REST_API_URL`, `KV_REST_API_TOKEN`

- [ ] **Step 2:** Creare Vercel KV store e collegarlo al progetto

- [ ] **Step 3:** Primo deploy e verifica

- [ ] **Step 4:** Configurare GitHub webhook puntando all'endpoint Vercel

- [ ] **Step 5:** Commit config

---

## Ordine di esecuzione e dipendenze

```
Fase 1 (Foundation)
  Task 1.1 → 1.2 → 1.3 → 1.4

Fase 2 (Skill Framework)
  Task 2.1 → 2.2
  [dipende da: Fase 1]

Fase 3 (Skill Stages)
  Task 3.1, 3.2, 3.3, 3.4 → 3.5
  [3.1-3.4 parallelizzabili]
  [dipende da: Task 2.1]

Fase 4 (Registrazione CLI)
  Task 4.1, 4.2
  [dipende da: Fase 3]

Fase 5 (Portal Foundation)
  Task 5.1 → 5.2 → 5.3 → 5.4 → 5.5
  [dipende da: Fase 1 (schema manifest)]
  [parallelizzabile con Fasi 2-4]

Fase 6 (Portal Viste)
  Task 6.1 → 6.2
  Task 6.3
  Task 6.4
  Task 6.5
  Task 6.6 → 6.7
  [dipende da: Fase 5]
  [6.1-6.5 parallelizzabili]
  [6.7 dopo tutto]
```

---

## Verifica end-to-end

### CLI (dopo Fase 4)

1. **Setup**: `cd portal-flow && bash skill/br-pipeline/install.sh`
2. **TL/PM flow**: invocare `br-pipeline`, verificare che mostri BR attivi, lanciare review su un BR di test con documenti in `brs/test-br/docs/`
3. **Dev flow**: creare `.br-local.json`, invocare `le mie task`, verificare che mostri solo le task assegnate da un BR con piano approvato
4. **Manifest round-trip**: verificare che ogni azione CLI aggiorni correttamente il manifest.json e generi le viste MD retrocompatibili
5. **Git sync**: verificare commit automatici con messaggi strutturati

### Portal (dopo Fase 6)

1. **Auth**: login con utenti diversi, verificare che ogni ruolo veda solo le sue pagine
2. **Funzionale flow**: creare BR, caricare docs, rispondere alle domande del review
3. **TL/PM flow**: dashboard, approvazione piano, assegnazione task
4. **QA flow**: visualizzare criteri, registrare risultati test
5. **Notifiche**: verificare che gli eventi generino notifiche al destinatario corretto
6. **Real-time**: push da CLI → webhook → aggiornamento portale

---

## Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Manifest JSON complesso, errori di validazione | JSON Schema rigoroso (Task 1.2), validazione sia in CLI che nel portale |
| GitHub API rate limiting | Cache locale del manifest, batch writes dove possibile |
| Conflitti git (CLI e portale scrivono sullo stesso file) | Manifest update usa read-modify-write atomico con retry su conflict |
| Auth Vercel KV free tier limiti | Monitorare usage, upgrade se necessario |
| Skill SKILL.md troppo grande | Struttura modulare con sezioni chiare per stage, evitare ripetizioni |
