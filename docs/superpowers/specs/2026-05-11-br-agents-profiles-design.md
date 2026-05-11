# Agenti Generici + Profili Progetto — Design Spec

Estensione dell'ecosistema BR con agenti di ruolo riusabili, profili progetto centralizzati, e routing automatico agli specialist per stack tecnologico. Obiettivo: scalare le BR skill a tutti i progetti Deloitte senza creare agenti per progetto.

## Contesto

Le skill BR attuali (br-analyzer, br-executor, br-debug, ecc.) lanciano sottoagenti general-purpose con prompt custom. Ogni volta il prompt ri-spiega convenzioni, dominio, pattern del progetto. Con decine di progetti eterogenei, questo approccio non scala: ogni team deve ri-spiegare tutto, la qualita' del codice prodotto dipende dalla completezza del prompt, e non c'e' riuso.

## Decisioni di design

1. **No agenti per progetto** — non scalano (centinaia di file da mantenere)
2. **Profili progetto centralizzati** — un repo `deloitte-profiles/` con un `profile.json` per progetto
3. **Agenti generici di ruolo** — `br-codebase-explorer` e `br-verifier`, riusabili su tutti i progetti
4. **No br-implementer** — routing diretto ai subagent_type esistenti (spring-boot-engineer, react-specialist, ecc.) in base allo stack nel profilo
5. **No agenti BR-aware intermedi** (br-backend, br-frontend) — layer inutile, la skill orchestra direttamente
6. **Agenti di progetto opzionali** — solo per pattern non standard, nella cartella del profilo
7. **Manutenzione automatica** — br-analyzer aggiorna il profilo ad ogni gap analysis
8. **Skill br-profile-setup** — creazione guidata con auto-detect del codebase

---

## 1. Architettura a 3 strati

```
Strato 1 — Profili Progetto (conoscenza)
  repo: deloitte-profiles/
  File: pnrr/profile.json, ecomotive/profile.json, ...
  Contiene: stack, dominio, design system, convenzioni
  Chi lo mantiene: il team del progetto + auto-update da br-analyzer

Strato 2 — Agenti di Ruolo (comportamento)
  ~/.claude/agents/ (br-codebase-explorer, br-verifier)
  + subagent_type esistenti (spring-boot-engineer, react-specialist, ...)
  Generici, riusabili, non legati a nessun progetto

Strato 3 — Skill BR (orchestrazione)
  ~/.claude/skills/br-*/
  Leggono il profilo, scelgono l'agente/specialist, iniettano
  il contesto progetto nel prompt
```

---

## 2. Repo deloitte-profiles

### Struttura

```
deloitte-profiles/
├── pnrr/
│   ├── profile.json
│   ├── agents/                           (opzionale)
│   │   └── pnrr-validator.md
│   └── references/                       (opzionale)
│       ├── design-system/
│       │   ├── palette.png
│       │   └── components.png
│       └── examples/
│           ├── entity-example.java
│           └── component-example.ts
├── ecomotive/
│   ├── profile.json
│   └── references/
│       └── design-system/
│           └── theme-tokens.json
├── isp/
│   └── profile.json
├── profile-schema.json
└── README.md
```

### Struttura profile.json

Tutte le sezioni sono opzionali tranne `project` e `tech_stack`:

```json
{
  "project": {
    "name": "PNRR",
    "client": "...",
    "description": "Piattaforma per la gestione delle pratiche PNRR"
  },
  "tech_stack": {
    "backend": {
      "language": "Java 17",
      "framework": "Spring Boot 3.2",
      "database": "PostgreSQL 15",
      "orm": "JPA/Hibernate",
      "build": "Maven"
    },
    "frontend": {
      "language": "TypeScript",
      "framework": "Angular 17",
      "ui_library": "Angular Material (custom theme)",
      "state": "NgRx",
      "build": "Angular CLI"
    }
  },
  "conventions": {
    "package_structure": "com.pnrr.{modulo}.{layer}",
    "layers": ["domain", "repository", "service", "controller", "dto", "mapper"],
    "base_entity": "BaseEntity (id, createdAt, updatedAt)",
    "api_prefix": "/api/v1",
    "test_framework": "JUnit 5 + Mockito",
    "test_naming": "should{Action}When{Condition}",
    "branch_convention": "feature/{br-name}-{slug}",
    "commit_convention": "feat|fix|refactor: description"
  },
  "design_system": {
    "palette": {
      "primary": "#1E3A5F",
      "secondary": "#4A90D9",
      "accent": "#FF6B35",
      "success": "#28A745",
      "error": "#DC3545",
      "background": "#F8F9FA",
      "surface": "#FFFFFF",
      "text": "#212529"
    },
    "typography": {
      "font_family": "Roboto, sans-serif",
      "weights": [400, 500, 700],
      "base_size": "14px"
    },
    "spacing": {
      "unit": "8px",
      "scale": [4, 8, 12, 16, 24, 32, 48, 64]
    },
    "components": {
      "border_radius": "8px",
      "shadow": "0 2px 4px rgba(0,0,0,0.1)",
      "button_style": "filled primary, outlined secondary"
    },
    "reference_files": [
      "references/design-system/palette.png",
      "references/design-system/components.png"
    ]
  },
  "domain": {
    "glossary": {
      "Pratica": "Unita' di lavoro, rappresenta una richiesta di finanziamento",
      "Cono di visibilita'": "Regola di accesso: chi vede quali pratiche"
    },
    "business_rules": [
      "Una pratica bloccata non puo' essere modificata",
      "Gli utenti Banca vedono solo le pratiche del proprio cono"
    ],
    "entity_states": {
      "Pratica": ["bozza", "inviata", "in_validazione", "validata", "rifiutata"]
    }
  },
  "custom_agents": ["agents/pnrr-validator.md"]
}
```

### Agenti di progetto (opzionali)

Presenti solo quando il progetto ha pattern non standard che gli agenti generici e il profilo non possono coprire. Esempio: un framework di validazione custom, un ORM proprietario, un sistema di componenti interno.

Il campo `custom_agents` nel profilo elenca i path relativi ai file .md degli agenti. Le skill li rilevano e li usano al posto degli agenti generici quando il contesto lo richiede.

### Reference files (opzionali)

Screenshot del design system, esempi di codice "gold standard", template specifici. Referenziati dal campo `reference_files` nelle sezioni del profilo. Gli agenti li leggono quando devono implementare codice FE o seguire pattern complessi.

---

## 3. Configurazione locale (.br-local.json esteso)

Il file `.br-local.json` nella root di ogni repo di progetto viene esteso con due nuovi campi:

```json
{
  "developer": "Marco",
  "profilo": "pnrr",
  "profiles_repo": "C:/Users/marco/repos/deloitte-profiles",
  "paths": {
    "BE": "C:/Users/marco/repos/pnrr-backend",
    "FE": "C:/Users/marco/repos/pnrr-frontend",
    "DM": "C:/Users/marco/repos/pnrr-doc-manager"
  }
}
```

| Campo | Nuovo? | Descrizione |
|---|---|---|
| `developer` | No | Nome dello sviluppatore (gia' esistente) |
| `profilo` | **Si** | Nome della cartella nel repo profili |
| `profiles_repo` | **Si** | Path locale del clone di deloitte-profiles |
| `paths` | No | Path locali dei codebase (gia' esistente) |

### Logica di caricamento profilo

Quando una skill ha bisogno del profilo:

1. Legge `.br-local.json` dalla root del repo corrente
2. Estrae `profiles_repo` e `profilo`
3. `git -C <profiles_repo> pull origin main` per sincronizzare
4. Legge `<profiles_repo>/<profilo>/profile.json`
5. Se `custom_agents` e' presente, carica anche gli agent .md referenziati

Fallback: se `.br-local.json` non ha `profilo` o `profiles_repo`, la skill funziona come oggi (senza profilo). Retrocompatibilita' totale.

---

## 4. Agenti generici

### br-codebase-explorer

**File:** `~/.claude/agents/br-codebase-explorer.md`

**Usato da:** br-analyzer, br-updater

**Riceve:**
- Profilo progetto (iniettato dalla skill)
- Documentazione BR (cosa cercare)
- Path del codebase da esplorare

**Sa fare:**
- Esplorare sistematicamente un codebase: entita'/modelli, API/controller, servizi/logica, repository/query, componenti FE, configurazioni
- Usare il profilo per sapere dove guardare (package_structure, layers, api_prefix)
- Produrre output strutturato per la gap analysis:

```markdown
| Funzionalita' | Stato | File coinvolti | Gap |
|---|---|---|---|
| Lista pratiche | Parziale | PraticaRepository.java, PraticaService.java | Manca filtro per cono visibilita' |
| Export PDF | Mancante | — | Nessuna implementazione trovata |
```

- Confrontare terminologia BR vs codice (nomi entita', stati, enum)

**Non sa:** niente di nessun progetto specifico. Riceve tutto dal profilo iniettato.

### br-verifier

**File:** `~/.claude/agents/br-verifier.md`

**Usato da:** br-executor, br-debug

**Riceve:**
- Requisiti della task/bug (dal piano o dal bug report)
- File modificati (lista)
- Risultati test
- Convenzioni dal profilo (test_naming, base_entity, ecc.)

**Esegue le 3 fasi:**

- **Fase A — Tecnica**: test tutti verdi, build ok, copertura happy path + edge case + error case
- **Fase B — Coerenza**: ogni requisito ha implementazione e test corrispondente. Tabella di tracciabilita'
- **Fase C — Riesame**: naming segue convenzioni, nessuna regressione, nessuna assunzione nascosta, test con asserzioni significative

**Produce verdict strutturato:**

```markdown
## Verdict: PASS | FAIL

### Fase A — Tecnica
- Test: 12/12 verdi
- Build: compila
- Copertura: 8 happy path, 3 edge case, 1 error case

### Fase B — Coerenza
| # | Requisito | Implementato | File | Test |
|---|---|---|---|---|
| 1 | Filtro per cono | Si | PraticaService.java:42 | shouldFilterByCono |
| 2 | Paginazione | Si | PraticaController.java:28 | shouldPaginate |

### Fase C — Riesame
- Naming: OK
- Convenzioni: OK
- Regressioni: nessuna
```

---

## 5. Routing a subagent_type esistenti

Le skill br-executor e br-debug usano il campo `tech_stack` dal profilo per instradare al subagent_type giusto:

| Stack (dal profilo) | subagent_type |
|---|---|
| Spring Boot | `spring-boot-engineer` |
| .NET Core | `csharp-developer` |
| Django | `django-developer` |
| FastAPI | `fastapi-developer` |
| Node.js / Express | `node-specialist` |
| Laravel | `laravel-specialist` |
| Angular | `angular-architect` |
| React | `react-specialist` |
| Vue | `vue-expert` |
| Next.js | `nextjs-developer` |
| Flutter | `flutter-expert` |
| Java (generico) | `java-architect` |
| Python (generico) | `python-pro` |
| Go | `golang-pro` |
| Rust | `rust-engineer` |
| Kotlin | `kotlin-specialist` |
| Swift | `swift-expert` |
| PHP | `php-pro` |
| (non riconosciuto) | `general-purpose` (fallback) |

Il routing avviene nella skill: legge `tech_stack.backend.framework` o `tech_stack.frontend.framework`, mappa al subagent_type, e lancia `Agent(subagent_type: "<tipo>")` con il contesto iniettato.

Per task multi-area (BE + FE), la skill lancia specialist diversi per ogni sotto-step in sequenza (es. prima spring-boot-engineer per l'API, poi react-specialist per il componente che la consuma). Il sotto-step FE tipicamente dipende dall'API BE.

### Uso aggiuntivo di subagent_type esistenti

| Dove | subagent_type | Quando |
|---|---|---|
| br-executor/br-debug (Fase C) | `code-reviewer` | Dopo br-verifier, come second opinion opzionale |
| br-executor/br-debug (task security) | `security-reviewer` | Task che toccano auth, autorizzazione, pagamenti |
| br-executor/br-debug (build fail) | `build-error-resolver` | Quando la build fallisce dopo implementazione |
| br-analyzer (schema DB) | `database-reviewer` | Per analisi schema, migration, indici |

---

## 6. Skill br-profile-setup

**Trigger:** "crea profilo progetto", "setup profilo", "nuovo profilo"

### Flusso

1. **Nome progetto:** chiede il nome (diventa la cartella nel repo profili)
2. **Profiles repo:** chiede il path locale del clone di deloitte-profiles. Verifica che sia un repo git valido
3. **Codebase:** chiede i path dei codebase coinvolti (nome, sigla, path locale)
4. **Auto-detect:** per ogni codebase, lancia `br-codebase-explorer` per rilevare:
   - Framework e linguaggio (da build files: pom.xml, package.json, go.mod, ecc.)
   - Struttura package/directory
   - Base entity e pattern
   - API prefix
   - Test framework
   - Design system (colori, font, spacing da CSS/SCSS/theme files)
5. **Presenta e conferma:** mostra tutto cio' che ha rilevato, chiede correzioni
6. **Dominio:** chiede le informazioni non deducibili dal codice:
   - Glossario (termini chiave del business)
   - Regole di business principali
   - Stati delle entita' principali
7. **Reference files:** chiede se ci sono screenshot del design system, esempi di codice gold standard, o template specifici. Se si', li copia nella cartella del profilo
8. **Genera:** crea `<profiles_repo>/<nome>/profile.json` con tutti i dati
9. **Commit + push:** committa e pusha su deloitte-profiles
10. **Aggiorna .br-local.json:** propone di aggiornare il `.br-local.json` di ogni codebase coinvolto con `profilo` e `profiles_repo`

---

## 7. Manutenzione automatica del profilo

Integrata in br-analyzer. Dopo ogni gap analysis:

1. La skill ha gia' esplorato il codebase per il BR
2. Confronta quello che ha trovato col profilo esistente
3. Se rileva delta significativi (non rumore), li presenta:

> Ho rilevato differenze tra il codebase e il profilo progetto:
>
> | Aspetto | Profilo | Codebase | Delta |
> |---|---|---|---|
> | Base entity | BaseEntity | BaseAuditEntity | Rinominata |
> | Nuovo package | — | com.pnrr.notification | Aggiunto |
> | API prefix | /api/v1 | /api/v2 (parziale) | Migrazione in corso |
> | Font | Roboto | Inter | Cambiato |
>
> Aggiorno il profilo?

4. Se confermato, aggiorna profile.json, commit + push su deloitte-profiles
5. Tutti i developer avranno il profilo aggiornato al prossimo pull (che avviene automaticamente a ogni invocazione skill)

Delta ignorati (rumore): file temporanei, branch-specific, configurazioni locali.

---

## 8. Flusso operativo end-to-end

```
[TL/PM] br-profile-setup
  → auto-detect codebase
  → domande dominio
  → genera profile.json in deloitte-profiles/
  → commit + push

[TL/PM] br-analyzer per nuovo BR
  → legge .br-local.json → profilo: "pnrr"
  → git pull deloitte-profiles
  → legge pnrr/profile.json
  → lancia br-codebase-explorer (con profilo iniettato)
  → gap analysis + piano
  → confronta codebase vs profilo → propone aggiornamenti
  → commit + push aggiornamenti profilo

[Dev] br-executor per task T-005 (BE, Spring Boot)
  → legge .br-local.json → profilo: "pnrr"
  → git pull deloitte-profiles
  → legge pnrr/profile.json
  → routing: Spring Boot → spring-boot-engineer
  → lancia spring-boot-engineer con contesto BR + profilo
  → specialist implementa
  → lancia br-verifier con requisiti + codice prodotto
  → verdict PASS → suggerisce commit

[Dev] br-debug per BUG-003 (FE, Angular)
  → legge .br-local.json → profilo: "pnrr"
  → git pull deloitte-profiles
  → legge pnrr/profile.json
  → routing: Angular → angular-architect
  → lancia angular-architect con contesto bug + profilo
  → specialist implementa fix
  → lancia br-verifier
  → verdict PASS → suggerisce commit
```

---

## 9. Impatto sulle skill esistenti

| Skill | Modifica | Dettaglio |
|---|---|---|
| br-analyzer | Media | Legge profilo, usa br-codebase-explorer invece di Explore generico, aggiorna profilo automaticamente |
| br-executor | Media | Legge profilo, routing a specialist per stack, usa br-verifier invece di verifica inline |
| br-debug | Media | Stesso di br-executor (routing + br-verifier) |
| br-updater | Bassa | Legge profilo, usa br-codebase-explorer per ri-verificare |
| br-reviewer | Bassa | Legge profilo per check leggero codice (migliora il confronto terminologico) |
| br-pipeline | Bassa | Mostra info profilo nella dashboard (nome progetto, stack) |
| br-clarify | Nessuna | — |
| br-progress-report | Nessuna | — |

---

## 10. Deliverable

| # | Componente | Tipo | Dove |
|---|---|---|---|
| 1 | profile-schema.json | Nuovo file | deloitte-profiles/ |
| 2 | README.md del repo profili | Nuovo file | deloitte-profiles/ |
| 3 | br-codebase-explorer.md | Nuovo agente | ~/.claude/agents/ e claude-flow/agents/ |
| 4 | br-verifier.md | Nuovo agente | ~/.claude/agents/ e claude-flow/agents/ |
| 5 | br-profile-setup SKILL.md | Nuova skill | claude-flow/skills/br-profile-setup/ |
| 6 | br-analyzer SKILL.md | Modifica | Aggiunta lettura profilo + routing + auto-update |
| 7 | br-executor SKILL.md | Modifica | Aggiunta lettura profilo + routing + br-verifier |
| 8 | br-debug SKILL.md | Modifica | Aggiunta lettura profilo + routing + br-verifier |
| 9 | br-updater SKILL.md | Modifica | Aggiunta lettura profilo + br-codebase-explorer |
| 10 | br-reviewer SKILL.md | Modifica | Aggiunta lettura profilo per check codice |
| 11 | br-pipeline SKILL.md (x2) | Modifica | Mostra info profilo in dashboard |
| 12 | BR_SKILLS_DOCUMENTATION.md | Modifica | Nuove sezioni per agenti e profili |
| 13 | README.md claude-flow | Modifica | Aggiornamento con agenti e profili |
| 14 | CLAUDE.md globale | Modifica | Trigger per br-profile-setup |
