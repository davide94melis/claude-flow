# BR Pipeline POM — Design Spec

Data: 2026-05-04

## Problema

La suite attuale di 6 skill BR (br-reviewer, br-clarify, br-analyzer, br-executor, br-updater, br-progress-report) e' developer-centric: lo sviluppatore avvia tutto, il funzionale interviene solo passivamente compilando un DOCX. Il ciclo DOCX e' lento (conversioni pandoc, corruzione file, round multipli = giorni/settimane). Non esiste dashboard, QA e' assente, non c'e' separazione tra chi pianifica e chi sviluppa.

## Soluzione

Un sistema a 2 componenti che implementa un flusso POM (Project Operating Model) completo:

1. **br-pipeline** — nuova skill CLI per Claude Code (le 6 skill esistenti restano intatte)
2. **BR Portal** — web app Next.js su Vercel, always-on, con viste per ruolo

Il funzionale diventa l'iniziatore del flusso, non piu' il destinatario passivo. Ogni ruolo ha la sua vista e le sue responsabilita'. Il DOCX viene eliminato: l'interazione avviene inline sul portale.

---

## Architettura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPONENTE 1: br-pipeline (Skill CLI)               │
│                                                                         │
│  Vive in Claude Code. Il TL/PM e i Dev lo invocano.                    │
│  Analizza, pianifica, esegue task. Legge/scrive sul repo git.          │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   │  git push/pull
                                   │
                          ┌────────▼────────┐
                          │   REPO GIT      │
                          │   (GitHub)      │
                          │                 │
                          │  brs/           │
                          │   <nome-br>/    │
                          │    manifest.json│
                          │    docs/        │
                          │    mockups/     │
                          │  design-system/ │
                          └────────┬────────┘
                                   │
                                   │  GitHub API + Webhooks
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                    COMPONENTE 2: BR Portal (Vercel)                     │
│                                                                         │
│  Next.js su Vercel. Always-on. 4 viste per ruolo.                      │
│  Auth: Vercel KV (Redis) per utenti/sessioni.                          │
│  Storage contenuti: repo git via GitHub API.                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Storage

| Cosa | Dove |
|---|---|
| Manifest, documenti, mockup, design system, report | Repo Git (GitHub) |
| Utenti, password (hash), sessioni | Vercel KV (Redis) |
| Path locali per-sviluppatore | `.br-local.json` (gitignored, per-macchina) |

### Struttura repo git

```
brs/
  booking-v2/
    manifest.json
    docs/
      BR_v24.docx
      BR_v24.md           (convertito)
      Specifiche.pdf
      Specifiche.md        (convertito)
    mockups/
      dashboard.png
      wizard.png
  monitoraggio/
    manifest.json
    ...
design-system/
  theme.json               (colori, tipografia, componenti, spaziature)
.br-portal-config.json     (config globale portale)
```

### `.br-local.json` (gitignored, per-macchina)

```json
{
  "developer": "Marco",
  "paths": {
    "BE": "C:/Users/marco/repos/backend",
    "FE": "C:/Users/marco/repos/frontend"
  }
}
```

Creato una volta alla prima invocazione di br-pipeline. Il manifest non contiene path locali — solo nome e sigla dei codebase.

---

## Ruoli e Viste

4 ruoli con responsabilita' separate. Account con email+password, admin approva e assegna ruolo.

| Ruolo | Responsabilita' | Dove lavora |
|---|---|---|
| **Funzionale** | Crea BR, carica docs/mockup, risponde alle domande del review | Portale |
| **Tech Lead / PM** | Lancia review e analisi, valida e approva piano (gate), assegna task, coordina, monitora | Portale + Claude Code |
| **Dev** | Esegue le task assegnate, scrive codice, aggiorna progresso | Claude Code (br-pipeline) |
| **QA** | Valida criteri di accettazione, esegue test, segnala difetti | Portale |

### Viste portale

**Vista Funzionale:**
- Lista dei propri BR (creati e in corso)
- Creazione nuovo BR (carica docs, mockup, assegna team tecnico)
- Integrazione Claude Design per mockup con design system
- Rispondi alle domande del review inline
- Vedi stato delle proprie risposte e dello avanzamento

**Vista Tech Lead / PM:**
- Dashboard completa di tutti i BR
- Lancia review e analisi dal portale (trigger CLI)
- Valida e approva il piano (gate esplicito prima che i dev inizino)
- Assegna/riassegna task
- Monitora avanzamento, blocchi, chi aspetta chi
- Timeline unificata

**Vista Dev:**
- Solo le proprie task assegnate
- Il proprio progresso
- I propri blocchi
- Nient'altro — nessuna distrazione

**Vista QA:**
- Criteri di accettazione da validare (per BR)
- Risultati test da registrare
- Difetti da segnalare
- Stato di copertura QA

---

## Pipeline — Stage e Flusso

```
Funzionale         TL/PM              Dev              QA
    │                │                  │                │
    │ 1. Crea BR     │                  │                │
    │ sul portale    │                  │                │
    │────────────────►                  │                │
    │                │ 2. Notifica      │                │
    │                │ "Nuovo BR"       │                │
    │                │                  │                │
    │                │ 3. Lancia review │                │
    │                │ (Claude Code)    │                │
    │                │                  │                │
    │ 4. Riceve      │                  │                │
    │ domande sul    │                  │                │
    │ portale        │                  │                │
    │                │                  │                │
    │ 5. Risponde    │                  │                │
    │ inline         │                  │                │
    │────────────────►                  │                │
    │                │ 6. Lancia analisi│                │
    │                │ gap + piano      │                │
    │                │                  │                │
    │                │ 7. GATE:         │                │
    │                │ approva piano    │                │
    │                │────────────────►│                │
    │                │                  │ 8. Vede task   │
    │                │                  │ assegnate      │
    │                │                  │                │
    │                │                  │ 9. Esegue con  │
    │                │                  │ br-pipeline    │
    │                │                  │                │
    │                │                  │                │ 10. QA valida
    │                │                  │                │ criteri
    │                │                  │                │
    │                │ 11. Monitora     │                │
    │                │ dashboard        │                │
```

### Stage del pipeline

| Stage | ID | Chi lo avvia | Cosa fa |
|---|---|---|---|
| **Onboard** | S0 | Funzionale (portale) | Crea BR, carica docs/mockup, assegna team |
| **Review** | S1 | TL/PM (Claude Code) | Analisi docs + codice, genera domande, criteri QA iniziali |
| **Clarify** | S2 | Funzionale (portale) | Risponde alle domande inline. Il pipeline rileva e rivaluta |
| **Analyze** | S3 | TL/PM (Claude Code) | Gap analysis, genera piano, test plan QA |
| **Approve** | S4 | TL/PM (portale) | GATE: valida e approva il piano. Solo dopo i dev vedono le task |
| **Execute** | S5 | Dev (Claude Code) | Esegue task con sottoagenti, aggiorna progresso |
| **Verify** | S6 | QA (portale) | Verifica criteri accettazione per task completate |
| **Update** | S7 | TL/PM (Claude Code) | Se il BR cambia, aggiorna piano preservando progresso |
| **Report** | S8 | Chiunque (portale) | Dashboard live, Excel esportabile |

---

## BR Manifest (JSON)

Single source of truth per ogni BR. Vive nel repo git come `brs/<nome-br>/manifest.json`.

```json
{
  "version": "1.0",
  "nome": "booking-v2",
  "data_creazione": "2026-05-04",
  "creato_da": "mario.rossi@azienda.it",
  "stato_pipeline": "review",

  "codebase": [
    { "nome": "back-end", "sigla": "BE" },
    { "nome": "front-end", "sigla": "FE" }
  ],

  "documenti": [
    { "originale": "docs/BR_v24.docx", "convertito": "docs/BR_v24.md", "tipo": "br" },
    { "originale": "docs/Specifiche.pdf", "convertito": "docs/Specifiche.md", "tipo": "spec" },
    { "originale": "mockups/dashboard.png", "tipo": "mockup" }
  ],

  "team": [
    { "nome": "Marco", "email": "marco@azienda.it", "ruolo": "BE", "seniority": "Senior" },
    { "nome": "Luca", "email": "luca@azienda.it", "ruolo": "FE", "seniority": "Mid" },
    { "nome": "Anna", "email": "anna@azienda.it", "ruolo": "BE", "seniority": "Junior", "reviewer": "Marco" }
  ],

  "review": {
    "data": "2026-05-04",
    "esito": "Con bloccanti",
    "problemi": [
      {
        "id": "B-001",
        "titolo": "Flusso annullamento non definito",
        "categoria": "Gap funzionale",
        "bloccante": true,
        "dove": "BR_v24.md, sezione 3.2",
        "problema": "Il BR descrive la creazione ma non l'annullamento",
        "impatto": "Impossibile pianificare il flusso completo",
        "domanda": "Cosa succede quando un booking confermato viene annullato?",
        "assunzione_proposta": null,
        "risposta": null,
        "data_risposta": null,
        "stato": "aperto"
      }
    ],
    "assunzioni": [
      {
        "id": "A-001",
        "problema_rif": "NB-3",
        "assunzione": "Si usa lo stesso enum esistente",
        "rischio": "Medio",
        "costo_correzione": "Basso",
        "stato": "in_attesa",
        "risposta_funzionale": null
      }
    ],
    "disallineamenti_codice": []
  },

  "qa": {
    "criteri_accettazione": [
      {
        "id": "QA-001",
        "funzionalita": "Booking - creazione",
        "criterio": "L'utente puo' creare un booking con tutti i campi obbligatori",
        "fonte": "review",
        "validato_qa": false,
        "risultato_test": null
      }
    ]
  },

  "gap_analysis": {
    "data": null,
    "matrice": [],
    "gap_aperti": []
  },

  "piano": {
    "approvato": false,
    "data_approvazione": null,
    "approvato_da": null,
    "stream": [],
    "task": [
      {
        "id": "T-001",
        "stream": "stream-fondazioni",
        "owner": "Marco",
        "area": "BE",
        "priorita": "P0",
        "wave": 0,
        "attivita": "Creare entita Booking",
        "descrizione": "...",
        "dipendenze": [],
        "effort_gg": 3,
        "branch": null,
        "progresso": 0,
        "stato": "da_iniziare",
        "qa_criteri": ["QA-001"],
        "note": ""
      }
    ]
  },

  "timeline": [
    {
      "data": "2026-05-04T10:30:00",
      "attore": "mario.rossi@azienda.it",
      "ruolo": "funzionale",
      "azione": "BR creato",
      "stage": "onboard"
    }
  ]
}
```

### Principi del manifest

- **Scrivi una volta, leggi ovunque**: codebase, team, documenti raccolti in S0, mai piu' chiesti
- **Stato pipeline esplicito**: il campo `stato_pipeline` dice dove siamo, l'orchestratore sa cosa proporre
- **Timeline auditabile**: ogni azione significativa finisce nella timeline con attore, ruolo, data
- **QA first-class citizen**: criteri nel manifest, linkati alle task via `qa_criteri[]`
- **Gate esplicito**: `piano.approvato` deve essere `true` prima che i dev vedano le task
- **Retrocompatibilita'**: i file MD (GAP_REPORT, PIANO, PROGRESSO, REVIEW) vengono generati dal manifest come viste di lettura per chi li preferisce

---

## Interazione col Funzionale (morte del DOCX)

### Creazione BR (portale)

Il funzionale accede al portale e crea un nuovo BR:

1. **Nome e descrizione** del BR
2. **Carica documenti** — DOCX, PDF, XLSX, PPTX, multipli, ognuno taggato per tipo (BR, spec, mapping, altro)
3. **Mockup** — upload diretto (PNG, JPG) oppure creazione tramite Claude Design con design system precaricato
4. **Assegna team tecnico** — seleziona da lista utenti registrati con ruolo Dev
5. **Assegna TL/PM** — seleziona il tech lead / project manager
6. **Invia** — il TL/PM riceve notifica

### Risposte alle domande (portale)

Dopo il review (S1), il funzionale vede le domande sul portale:

- Domande raggruppate per priorita' (bloccanti prima, con banner visivo)
- Ogni domanda non bloccante mostra l'assunzione proposta ("se non rispondi, assumiamo X")
- Il funzionale risponde inline, campo per campo
- Puo' salvare risposte parziali e tornare dopo
- Ogni salvataggio aggiorna il manifest nel repo git via GitHub API
- Il TL/PM vede le risposte arrivare sulla sua dashboard

### Claude Design per i mockup

- Il portale definisce un **design system** condiviso (colori, tipografia, componenti, spaziature) in `design-system/theme.json`
- Quando il funzionale clicca "Crea con Claude Design", il design system viene precaricato come contesto
- Claude Design genera mockup coerenti con il tema del progetto
- I mockup vengono allegati al BR nel portale
- Opzionale: il funzionale puo' anche caricare mockup fatti a mano

---

## Integrazione QA

Il QA e' presente in 3 stage:

### S1 — Review

Il pipeline genera criteri di accettazione iniziali dalla documentazione del BR. Il QA li vede sul portale e puo':
- Validare i criteri proposti
- Modificarli o aggiungerne di nuovi
- Definire scenari di test

### S3 — Analyze

Il pipeline arricchisce i criteri QA con dettagli tecnici dal gap report. Il QA rivede il test plan e lo valida prima dell'approvazione del piano.

### S6 — Verify

Quando un dev completa una task, il QA la vede sul portale con i criteri linkati (`qa_criteri[]`). Il QA:
- Esegue i test (manuali o automatici)
- Registra il risultato (pass/fail) per ogni criterio
- Segnala difetti con descrizione
- Una task e' veramente "completata" solo quando il QA la valida

---

## br-pipeline (Skill CLI)

### Invocazione

La skill ha un unico entry point. Il comportamento cambia in base al ruolo:

**TL/PM dice:** `"br-pipeline"` o `"pipeline br"`
- Il pipeline legge il repo git, mostra i BR attivi con il loro stato
- Propone il next step: "Il BR booking-v2 ha 3 risposte nuove dal funzionale — vuoi rivalutare?"
- Il TL/PM puo' lanciare review, analisi, approvare il piano

**Dev dice:** `"le mie task"` o `"br-pipeline"`
- Il pipeline legge `.br-local.json` per identificare il dev
- Mostra solo le task assegnate a quel dev, dai BR con piano approvato
- Propone la prossima task disponibile (stessa logica di br-executor)

### Stage interni

La skill contiene la logica di tutti gli stage, ma li espone in modo diverso in base al ruolo:

| Stage | Logica | Basata su |
|---|---|---|
| Review (S1) | Analisi docs + codice, genera domande | br-reviewer attuale |
| Clarify (S2) | Legge risposte dal manifest, rivaluta | br-clarify attuale |
| Analyze (S3) | Gap analysis + piano + QA test plan | br-analyzer attuale |
| Execute (S5) | Esecuzione task con sottoagenti | br-executor attuale |
| Update (S7) | Delta BR, aggiornamento piano | br-updater attuale |

Le skill esistenti restano intatte e utilizzabili standalone.

### Interazione col repo git

- All'avvio: `git pull` per sincronizzare
- Dopo ogni modifica al manifest: `git commit` + `git push`
- Messaggi di commit strutturati: `[br-pipeline] booking-v2: review completato (3 bloccanti, 5 non bloccanti)`

---

## BR Portal (Web App)

### Stack

| Componente | Tecnologia |
|---|---|
| Frontend | Next.js (App Router) |
| Hosting | Vercel |
| Auth | NextAuth + Vercel KV (Redis) |
| Storage contenuti | GitHub API (repo git) |
| Real-time | GitHub Webhooks → Vercel endpoint |
| Design system mockup | Integrazione Claude Design |

### Pagine principali

| Pagina | Ruoli | Contenuto |
|---|---|---|
| `/login` | Tutti | Login email+password |
| `/dashboard` | TL/PM | Tutti i BR, stato pipeline, blocchi, timeline |
| `/br/nuovo` | Funzionale | Form creazione BR |
| `/br/[id]` | Tutti (vista per ruolo) | Dettaglio BR: stato, domande, piano, progresso |
| `/br/[id]/review` | Funzionale | Domande del review, rispondi inline |
| `/br/[id]/piano` | TL/PM | Piano con approvazione, assegnazione task |
| `/br/[id]/task` | Dev | Le proprie task assegnate |
| `/br/[id]/qa` | QA | Criteri, test results, difetti |
| `/admin` | Admin | Gestione utenti, ruoli, design system |

### Notifiche

Il portale notifica via:
- Badge/indicatore nel portale stesso (sempre visibile)
- Email opzionale (configurabile per utente)

Eventi che generano notifica:

| Evento | Chi riceve |
|---|---|
| Nuovo BR creato | TL/PM assegnato |
| Review completato (domande pronte) | Funzionale del BR |
| Risposte ricevute | TL/PM |
| Piano pronto per approvazione | TL/PM |
| Piano approvato, task assegnate | Dev assegnati |
| Task completata | QA, TL/PM |
| QA valida/rifiuta task | Dev, TL/PM |
| BR aggiornato | TL/PM |

---

## Design System per Mockup

Il file `design-system/theme.json` definisce le regole visive del progetto:

```json
{
  "nome_progetto": "Booking Platform",
  "colori": {
    "primary": "#0d6efd",
    "secondary": "#6c757d",
    "success": "#198754",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "background": "#ffffff",
    "surface": "#f8f9fa",
    "text": "#1a1a1a"
  },
  "tipografia": {
    "font_family": "Inter, sans-serif",
    "heading_sizes": { "h1": "32px", "h2": "24px", "h3": "18px" }
  },
  "componenti": {
    "border_radius": "8px",
    "spacing_unit": "8px",
    "button_style": "rounded",
    "input_style": "outlined"
  },
  "note": "Stile moderno, pulito. Bottoni arrotondati, card con ombra leggera."
}
```

Quando il funzionale crea mockup con Claude Design, il tema viene precaricato come contesto per garantire coerenza visiva tra tutti i BR.

---

## Vincoli e decisioni

| Decisione | Scelta | Motivazione |
|---|---|---|
| Skill esistenti | Restano intatte | Zero rischio di regressione |
| Storage | Git repo | Version history gratis, dev lo conoscono gia' |
| Auth | Vercel KV | Minimo necessario, free tier, nativo Vercel |
| Path locali | `.br-local.json` gitignored | Creato una volta, mai piu' chiesto |
| DOCX | Eliminato | Sostituito da interazione inline sul portale |
| Claude Design | Opzionale | Acceleratore per mockup, non obbligatorio |
| Gate piano | Esplicito (TL/PM approva) | I dev non vedono task finche' il piano non e' approvato |
| QA | End-to-end | Criteri nel review, test plan nell'analisi, verifica nell'esecuzione |
| Real-time | Webhooks GitHub → Vercel | Nessun polling, notifiche push |
| Retrocompatibilita' MD | Si | I file MD vengono generati come viste del manifest per chi li preferisce |

---

## Scope di implementazione

### Componente 1: br-pipeline (Skill CLI)

- Nuova skill in `~/.claude/skills/br-pipeline/SKILL.md`
- Contiene la logica di tutti gli stage
- Legge/scrive sul repo git
- Usa `.br-local.json` per path locali
- Genera file MD come viste retrocompatibili del manifest
- Entry point unico con comportamento basato sul ruolo

### Componente 2: BR Portal (Web App)

- Progetto Next.js separato
- Deploy su Vercel
- GitHub API per lettura/scrittura repo
- Vercel KV per auth
- Viste per ruolo (Funzionale, TL/PM, Dev, QA)
- Integrazione Claude Design per mockup
- Sistema notifiche (in-app + email opzionale)
- Pagina admin per gestione utenti e design system
