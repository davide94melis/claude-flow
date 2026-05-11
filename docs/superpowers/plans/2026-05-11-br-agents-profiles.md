# BR Agents + Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the BR skill ecosystem with centralized project profiles, two generic agents (br-codebase-explorer, br-verifier), profile-aware routing to specialist subagent_types, and a skill for guided profile creation — scaling BR skills to all Deloitte projects without per-project agents.

**Architecture:** Three layers — (1) `deloitte-profiles/` repo with one `profile.json` per project containing stack, conventions, domain, and design system; (2) two generic agents (`br-codebase-explorer` for gap analysis, `br-verifier` for 3-phase verification) that receive the profile as context; (3) modified BR skills that load the profile from `.br-local.json`, route to specialist subagent_types by stack, and inject profile context into all subagent prompts. Full retrocompatibility: skills work as today when no profile is configured.

**Tech Stack:** Claude Code skills (SKILL.md), Claude Code agents (.md), JSON Schema, git CLI for profile sync.

**Design spec:** `docs/superpowers/specs/2026-05-11-br-agents-profiles-design.md`

**Repos coinvolti:**
- `claude-flow/` — skill source, agents source, documentation
- `portal-flow/` — portal skills (br-debug, br-pipeline only)
- `deloitte-profiles/` — new repo for project profiles

**No co-author attribution in commits.**

---

## Execution Waves

```
Wave 1 (parallel, no deps):
  Task 1: profile-schema.json + README (deloitte-profiles)
  Task 2: br-codebase-explorer agent
  Task 3: br-verifier agent

Wave 2 (parallel, depends on Wave 1):
  Task 4: br-profile-setup skill (depends on 1, 2)
  Task 5: br-analyzer modification (depends on 1, 2)
  Task 6: br-executor modification (depends on 1, 3)
  Task 7: br-debug modification (depends on 1, 3)
  Task 8: br-updater modification (depends on 1, 2)
  Task 9: br-reviewer modification (depends on 1)
  Task 10: br-pipeline claude-flow (depends on 1)
  Task 11: br-pipeline portal-flow (depends on 1)

Wave 3 (sequential, depends on Wave 2):
  Task 12: BR_SKILLS_DOCUMENTATION.md
  Task 13: README.md claude-flow
  Task 14: CLAUDE.md global triggers
```

---

## Shared Reference: Profile Loading Block

Every modified skill adds this section. It is repeated in full in each task for self-contained execution.

```markdown
## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Se il campo `custom_agents` e' presente nel profilo, leggi anche i file .md degli agenti referenziati (path relativi alla cartella del profilo)
   d. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Il profilo, quando disponibile, viene iniettato nei prompt dei sottoagenti per fornire contesto su stack, convenzioni, dominio e design system del progetto.
```

## Shared Reference: Routing Table

```markdown
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
| (non riconosciuto/no profilo) | `general-purpose` (fallback) |
```

---

### Task 1: Create deloitte-profiles repo structure

**Files:**
- Create: `deloitte-profiles/profile-schema.json`
- Create: `deloitte-profiles/README.md`

- [ ] **Step 1: Create the repo directory**

```bash
mkdir -p C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
git init
```

- [ ] **Step 2: Create profile-schema.json**

Create `profile-schema.json` with the JSON Schema that validates all profile.json files:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Deloitte Project Profile",
  "description": "Schema per profile.json — profilo tecnico e di dominio di un progetto Deloitte.",
  "type": "object",
  "required": ["project", "tech_stack"],
  "properties": {
    "project": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "description": "Nome del progetto" },
        "client": { "type": "string", "description": "Nome del cliente" },
        "description": { "type": "string", "description": "Descrizione breve del progetto" }
      },
      "additionalProperties": false
    },
    "tech_stack": {
      "type": "object",
      "properties": {
        "backend": {
          "type": "object",
          "properties": {
            "language": { "type": "string" },
            "framework": { "type": "string" },
            "database": { "type": "string" },
            "orm": { "type": "string" },
            "build": { "type": "string" }
          },
          "additionalProperties": true
        },
        "frontend": {
          "type": "object",
          "properties": {
            "language": { "type": "string" },
            "framework": { "type": "string" },
            "ui_library": { "type": "string" },
            "state": { "type": "string" },
            "build": { "type": "string" }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "conventions": {
      "type": "object",
      "properties": {
        "package_structure": { "type": "string", "description": "Pattern struttura package (es. com.progetto.{modulo}.{layer})" },
        "layers": { "type": "array", "items": { "type": "string" }, "description": "Layer architetturali ordinati" },
        "base_entity": { "type": "string", "description": "Classe base per le entita'" },
        "api_prefix": { "type": "string", "description": "Prefisso API (es. /api/v1)" },
        "test_framework": { "type": "string" },
        "test_naming": { "type": "string", "description": "Convenzione naming test (es. should{Action}When{Condition})" },
        "branch_convention": { "type": "string" },
        "commit_convention": { "type": "string" }
      },
      "additionalProperties": true
    },
    "design_system": {
      "type": "object",
      "properties": {
        "palette": {
          "type": "object",
          "properties": {
            "primary": { "type": "string" },
            "secondary": { "type": "string" },
            "accent": { "type": "string" },
            "success": { "type": "string" },
            "error": { "type": "string" },
            "background": { "type": "string" },
            "surface": { "type": "string" },
            "text": { "type": "string" }
          },
          "additionalProperties": true
        },
        "typography": {
          "type": "object",
          "properties": {
            "font_family": { "type": "string" },
            "weights": { "type": "array", "items": { "type": "integer" } },
            "base_size": { "type": "string" }
          },
          "additionalProperties": true
        },
        "spacing": {
          "type": "object",
          "properties": {
            "unit": { "type": "string" },
            "scale": { "type": "array", "items": { "type": "integer" } }
          },
          "additionalProperties": true
        },
        "components": {
          "type": "object",
          "additionalProperties": true
        },
        "reference_files": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Path relativi a screenshot/file del design system"
        }
      },
      "additionalProperties": true
    },
    "domain": {
      "type": "object",
      "properties": {
        "glossary": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Termini chiave del business con definizione"
        },
        "business_rules": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Regole di business principali"
        },
        "entity_states": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": { "type": "string" }
          },
          "description": "Stati delle entita' principali"
        }
      },
      "additionalProperties": true
    },
    "custom_agents": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Path relativi a file .md di agenti custom del progetto"
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 3: Create README.md**

Create `README.md`:

```markdown
# Deloitte Profiles

Profili progetto centralizzati per l'ecosistema BR Skills di Claude Code. Ogni progetto ha una cartella con un `profile.json` che descrive stack tecnico, convenzioni, dominio e design system.

## Struttura

```
deloitte-profiles/
├── <progetto>/
│   ├── profile.json              (obbligatorio)
│   ├── agents/                   (opzionale — agenti custom)
│   │   └── <nome>-validator.md
│   └── references/               (opzionale — materiale di riferimento)
│       ├── design-system/
│       │   ├── palette.png
│       │   └── components.png
│       └── examples/
│           ├── entity-example.java
│           └── component-example.ts
├── profile-schema.json
└── README.md
```

## profile.json

Ogni profilo contiene (solo `project` e `tech_stack` sono obbligatori):

| Sezione | Contenuto | Obbligatoria |
|---|---|---|
| `project` | Nome, cliente, descrizione | Si |
| `tech_stack` | Backend e frontend: linguaggio, framework, DB, ORM, build | Si |
| `conventions` | Package structure, layers, base entity, API prefix, test naming | No |
| `design_system` | Palette, tipografia, spaziatura, componenti, reference files | No |
| `domain` | Glossario, regole di business, stati entita' | No |
| `custom_agents` | Path a file .md di agenti specifici del progetto | No |

Schema di validazione: `profile-schema.json` (JSON Schema Draft 2020-12).

## Come usare

### 1. Setup iniziale

Usa la skill `br-profile-setup` per creare un nuovo profilo con auto-detect del codebase:

```
> crea profilo progetto
```

### 2. Configurazione locale

Ogni sviluppatore aggiunge al `.br-local.json` nella root del repo di progetto:

```json
{
  "developer": "Marco",
  "profilo": "<nome-cartella>",
  "profiles_repo": "<path-locale-clone>",
  "paths": { ... }
}
```

### 3. Sincronizzazione

Le skill BR eseguono `git pull` automatico a ogni invocazione. Aggiornamenti al profilo sono visibili a tutti i developer al prossimo uso.

### 4. Manutenzione

`br-analyzer` aggiorna automaticamente il profilo dopo ogni gap analysis, confrontando il codebase con il profilo e proponendo delta significativi.

## Agenti custom (opzionali)

Presenti solo per pattern non standard che gli agenti generici e il profilo non coprono. Esempio: framework di validazione custom, ORM proprietario.

Il campo `custom_agents` nel profilo elenca i path relativi ai file .md. Le skill li caricano e li usano quando il contesto lo richiede.

## Reference files (opzionali)

Screenshot del design system, esempi di codice "gold standard", template specifici. Referenziati dal campo `reference_files` nelle sezioni del profilo.
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
git add profile-schema.json README.md
git commit -m "feat: initialize deloitte-profiles repo with schema and README"
```

---

### Task 2: Create br-codebase-explorer agent

**Files:**
- Create: `claude-flow/agents/br-codebase-explorer.md`

- [ ] **Step 1: Create the agents directory**

```bash
mkdir -p C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents
```

- [ ] **Step 2: Create br-codebase-explorer.md**

Create `agents/br-codebase-explorer.md`:

````markdown
---
name: br-codebase-explorer
description: Agente generico per l'esplorazione sistematica di un codebase durante la gap analysis. Riceve un profilo progetto, documentazione BR, e path del codebase. Produce output strutturato per confronto documentazione vs codice. Usato da br-analyzer e br-updater.
subagent_type: Explore
---

# BR Codebase Explorer

Sei un esploratore di codebase specializzato nella gap analysis per Business Requirements. Ricevi un profilo progetto, documentazione BR, e un path di codebase. Il tuo compito e' esplorare sistematicamente il codice e produrre un output strutturato che descrive cosa esiste, cosa manca, e cosa e' diverso rispetto ai requisiti.

## Input che ricevi

1. **Profilo progetto** (JSON) — se disponibile, contiene:
   - `tech_stack`: linguaggi, framework, database, ORM
   - `conventions`: package structure, layers, api_prefix, base_entity
   - `domain`: glossario dei termini di business, regole, stati entita'
   - `design_system`: palette, tipografia, componenti
2. **Documentazione BR** — i requisiti funzionali e tecnici da cercare nel codice
3. **Path del codebase** — dove esplorare

## Come esplorare

### Con profilo disponibile

Usa il profilo per navigare in modo mirato:

- **`conventions.package_structure`** → sai dove cercare entita', servizi, controller
- **`conventions.layers`** → sai l'ordine dei layer architetturali
- **`conventions.api_prefix`** → sai il prefisso delle API
- **`conventions.base_entity`** → sai la classe base delle entita'
- **`domain.glossary`** → sai i termini di business da cercare nel codice
- **`domain.entity_states`** → sai gli stati che le entita' dovrebbero avere

### Senza profilo

Esplora la struttura del progetto per dedurre le convenzioni:

1. Leggi i file di build (`pom.xml`, `package.json`, `go.mod`, `Cargo.toml`) per capire framework e dipendenze
2. Esplora la struttura delle directory per capire l'organizzazione
3. Leggi alcuni file di esempio per capire i pattern in uso

### Aree da esplorare (in ordine)

1. **Entita'/Modelli** — classi di dominio, DTO, enumerazioni
2. **API/Controller** — endpoint esposti, payload, validazioni
3. **Servizi/Logica** — business logic, workflow, macchine a stati
4. **Repository/Query** — accesso dati, query custom, viste
5. **Componenti FE** — componenti UI, routing, servizi frontend, i18n
6. **Configurazioni** — properties, feature flag, sicurezza, environment

### Confronto terminologico

Confronta i termini usati nella documentazione BR con quelli nel codice:

- Nomi di entita' (il BR dice "Pratica", il codice ha "Practice"?)
- Nomi di stati (il BR dice "bozza/inviata/validata", il codice ha "DRAFT/SUBMITTED/VALIDATED"?)
- Nomi di campi e proprieta'
- Nomi di endpoint API

## Output

Produci una tabella markdown strutturata per funzionalita':

```markdown
## Esplorazione Codebase — [Nome Repo] ([Sigla])

### Riepilogo Struttura

| Aspetto | Rilevato |
|---|---|
| Framework | Spring Boot 3.2 |
| Package root | com.example.progetto |
| Layer | domain, repository, service, controller, dto, mapper |
| Base entity | BaseAuditEntity (id, createdAt, updatedAt, createdBy) |
| API prefix | /api/v1 |
| Test framework | JUnit 5 + Mockito |

### Gap per Funzionalita'

| Funzionalita' | Stato | File coinvolti | Gap |
|---|---|---|---|
| Lista pratiche | Parziale | PraticaRepository.java, PraticaService.java | Manca filtro per cono visibilita' |
| Export PDF | Mancante | — | Nessuna implementazione trovata |
| Dashboard monitoraggio | Coperto | MonitoringController.java, monitoring.component.ts | — |
| Stato pratica | Discrepanza | PraticaStatus.java | BR dice 5 stati, codice ne ha 3 |

### Discrepanze Terminologiche

| Termine BR | Termine Codice | File | Note |
|---|---|---|---|
| Pratica | Practice | Practice.java | Traduzione EN |
| Cono di visibilita' | — | — | Concetto non presente nel codice |
```

## Regole

1. **Mai modificare codice** — sei solo un esploratore
2. **Segnala tutto** — anche i match parziali e le discrepanze minori
3. **Path esatti** — ogni file menzionato deve avere il path completo
4. **Dettaglio sufficiente** — chi legge il tuo output deve poter capire la situazione senza rileggere il codice
5. **Confronto terminologico** — sempre, anche se il profilo non ha un glossario
````

- [ ] **Step 3: Install agent globally**

```bash
mkdir -p ~/.claude/agents
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-codebase-explorer.md ~/.claude/agents/
```

- [ ] **Step 4: Commit in claude-flow**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add agents/br-codebase-explorer.md
git commit -m "feat: add br-codebase-explorer agent for profile-aware gap analysis"
```

---

### Task 3: Create br-verifier agent

**Files:**
- Create: `claude-flow/agents/br-verifier.md`

- [ ] **Step 1: Create br-verifier.md**

Create `agents/br-verifier.md`:

````markdown
---
name: br-verifier
description: Agente generico per la verifica in 3 fasi del lavoro prodotto da sottoagenti. Riceve requisiti, file modificati, risultati test, e convenzioni dal profilo. Produce un verdict strutturato PASS/FAIL. Usato da br-executor e br-debug.
---

# BR Verifier

Sei un verificatore di lavoro completato. Dopo che un sottoagente ha implementato codice per una task o un bug fix, il tuo compito e' eseguire una verifica rigorosa in 3 fasi e produrre un verdict strutturato.

## Input che ricevi

1. **Requisiti** — descrizione della task o del bug dal piano/report
2. **File modificati** — lista dei file creati o modificati dal sottoagente
3. **Risultati test** — output dell'esecuzione dei test
4. **Convenzioni dal profilo** (se disponibile) — test_naming, base_entity, package_structure, commit_convention

## Fasi di verifica

### Fase A — Tecnica

1. **Test tutti verdi** — verifica che la suite completa passi con zero failure. Se i test non sono stati eseguiti, eseguili.
2. **Build OK** — verifica che il progetto compili senza errori ne' warning significativi.
3. **Copertura test** — verifica che il sottoagente abbia scritto:
   - Test happy path per ogni funzionalita' implementata
   - Test edge case: input vuoti, null, boundary values, liste vuote, stringhe troppo lunghe
   - Test error case: fallimenti di dipendenze, input malformati, stati invalidi
   - Se mancano categorie di test, segnalalo come FAIL con dettaglio.

### Fase B — Coerenza col requisito

Per OGNI requisito elencato nell'input:

1. **E' stato implementato?** — il codice prodotto copre effettivamente quel requisito
2. **E' stato implementato correttamente?** — il comportamento corrisponde a quello descritto, non a un'interpretazione semplificata
3. **Ha un test corrispondente?** — esiste un test che verifica questo specifico requisito

Produci una tabella di tracciabilita':

```markdown
| # | Requisito | Implementato | File | Test |
|---|---|---|---|---|
| 1 | Filtro per cono | Si | PraticaService.java:42 | shouldFilterByCono |
| 2 | Paginazione | Si | PraticaController.java:28 | shouldPaginate |
| 3 | Export CSV | No | — | — |
```

Se un requisito non e' implementato o non ha test → FAIL.

### Fase C — Riesame finale

1. **Naming** — variabili, metodi, classi seguono le convenzioni del progetto (usa `conventions` dal profilo se disponibile)
2. **Regressioni** — il fix/implementazione non rompe il comportamento corretto preesistente
3. **Assunzioni nascoste** — il sottoagente ha hardcodato valori che dovrebbero essere configurabili?
4. **Test significativi** — ogni test ha asserzioni specifiche e significative, non solo "non lancia eccezione"

## Output — Verdict

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
- Convenzioni: OK (test_naming: should{Action}When{Condition})
- Regressioni: nessuna
- Assunzioni: nessuna

### Problemi trovati (solo se FAIL)
1. [Descrizione problema + suggerimento fix]
2. [Descrizione problema + suggerimento fix]
```

## Regole

1. **Mai correggere codice** — segnala i problemi, non li risolvere
2. **Verdict binario** — PASS o FAIL, nessuna via di mezzo
3. **Ogni requisito deve avere implementazione E test** — un requisito senza test e' FAIL anche se implementato
4. **Leggi il codice, non fidarti dei riepiloghi** — verifica leggendo i file effettivi
5. **Usa le convenzioni dal profilo** — se il profilo dice `test_naming: "should{Action}When{Condition}"` e un test si chiama `testLogin`, segnalalo
````

- [ ] **Step 2: Install agent globally**

```bash
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-verifier.md ~/.claude/agents/
```

- [ ] **Step 3: Commit in claude-flow**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add agents/br-verifier.md
git commit -m "feat: add br-verifier agent for profile-aware 3-phase verification"
```

---

### Task 4: Create br-profile-setup skill

**Files:**
- Create: `claude-flow/skills/br-profile-setup/SKILL.md`
- Create: `portal-flow/skill/br-profile-setup/SKILL.md`
- Create: `portal-flow/skill/br-profile-setup/install.sh`

- [ ] **Step 1: Create skill directories**

```bash
mkdir -p C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-profile-setup
mkdir -p C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-profile-setup
```

- [ ] **Step 2: Create SKILL.md in claude-flow**

Create `skills/br-profile-setup/SKILL.md`:

````markdown
---
name: br-profile-setup
description: Crea un nuovo profilo progetto in deloitte-profiles con auto-detect del codebase, domande guidate su dominio e design system, e configurazione automatica di .br-local.json. Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill BR.
---

# BR Profile Setup — Creazione Guidata Profilo Progetto

Questa skill guida la creazione di un nuovo profilo progetto nel repo `deloitte-profiles/`. Il profilo contiene stack tecnico, convenzioni, dominio e design system — usato da tutte le skill BR per fornire contesto ai sottoagenti.

Il flusso e' composto da 10 step sequenziali. Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

---

## Step 1 — Nome progetto

> Come vuoi chiamare questo progetto? Il nome diventa la cartella nel repo profili.
>
> Esempio: "pnrr", "ecomotive", "isp-banking", "booking-platform"

Salva il nome. Verra' usato come `<nome>` in tutti i path successivi.

---

## Step 2 — Profiles repo

> Dove si trova il clone locale del repo `deloitte-profiles`?
>
> Dammi il path completo (es. `C:/Users/marco/repos/deloitte-profiles`)

Verifica che il path sia un repo git valido:

```bash
git -C <path> rev-parse --is-inside-work-tree 2>/dev/null
```

Se non e' un repo git, avvisa:

> Il path indicato non e' un repository git. Vuoi:
> 1. Indicare un path diverso
> 2. Inizializzare un nuovo repo in quel path (`git init`)

Verifica anche che `profile-schema.json` esista nel repo per confermare che sia il repo corretto:

```bash
ls <path>/profile-schema.json 2>/dev/null
```

---

## Step 3 — Codebase

> Quali sono i codebase/repository coinvolti in questo progetto?
> Per ognuno, dammi:
> - **Nome** (es. "back-end", "front-end", "document-manager")
> - **Sigla** (es. "BE", "FE", "DM")
> - **Path locale** (il path al codebase)
>
> Elenca tutti quelli del progetto, anche se non sono coinvolti in un BR specifico.

Salva la lista dei codebase con nome, sigla e path.

---

## Step 4 — Auto-detect

Per ogni codebase fornito, lancia un agente di esplorazione per rilevare automaticamente:

**Backend detection** — cerca in ordine:

| File | Framework rilevato |
|---|---|
| `pom.xml` con `spring-boot` | Spring Boot (leggi versione) |
| `build.gradle` con `spring` | Spring Boot |
| `pom.xml` con `jakarta` | Java EE |
| `*.csproj` con `Microsoft.NET` | .NET Core (leggi versione) |
| `requirements.txt` o `pyproject.toml` con `django` | Django |
| `requirements.txt` o `pyproject.toml` con `fastapi` | FastAPI |
| `package.json` con `express` | Node.js / Express |
| `composer.json` con `laravel` | Laravel |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

**Frontend detection** — cerca in ordine:

| File | Framework rilevato |
|---|---|
| `angular.json` | Angular (leggi versione) |
| `package.json` con `react` | React |
| `package.json` con `vue` | Vue |
| `package.json` con `next` | Next.js |
| `package.json` con `nuxt` | Nuxt.js |
| `pubspec.yaml` con `flutter` | Flutter |

**Convenzioni detection** — per ogni codebase:

1. **Package/directory structure** — leggi la struttura dei package/directory principali
2. **Base entity** — cerca classi base per le entita' (nomi come `BaseEntity`, `AbstractEntity`, `BaseAuditEntity`)
3. **API prefix** — cerca nei controller/route l'URL prefix comune
4. **Test framework** — rileva dal file di build (JUnit, Mockito, Jest, Jasmine, pytest, ecc.)
5. **Test naming** — leggi 2-3 file di test per dedurre il pattern di naming

**Design system detection** (solo per codebase FE):

1. **Colori** — cerca in file CSS/SCSS/theme le variabili colore (primary, secondary, accent, ecc.)
2. **Font** — cerca font-family dichiarati
3. **Spacing** — cerca scale di spaziatura o variabili spacing
4. **UI library** — rileva da package.json (Material, Ant Design, PrimeNG, Chakra, ecc.)

---

## Step 5 — Presenta e conferma

Mostra tutto cio' che e' stato rilevato:

> ## Auto-detect completato
>
> ### Back-end (BE) — `<path>`
> - **Framework**: Spring Boot 3.2
> - **Linguaggio**: Java 17
> - **Database**: PostgreSQL 15 (da `application.properties`)
> - **ORM**: JPA/Hibernate
> - **Build**: Maven
> - **Package root**: `com.progetto.modulo`
> - **Layers**: domain, repository, service, controller, dto, mapper
> - **Base entity**: `BaseAuditEntity (id, createdAt, updatedAt, createdBy)`
> - **API prefix**: `/api/v1`
> - **Test framework**: JUnit 5 + Mockito
> - **Test naming**: `should{Action}When{Condition}`
>
> ### Front-end (FE) — `<path>`
> - **Framework**: Angular 17
> - **Linguaggio**: TypeScript
> - **UI Library**: Angular Material (custom theme)
> - **State management**: NgRx
> - **Build**: Angular CLI
> - **Palette**: primary=#1E3A5F, secondary=#4A90D9, accent=#FF6B35
> - **Font**: Roboto, sans-serif
>
> Tutto corretto? Vuoi modificare o aggiungere qualcosa?

Applica le correzioni dell'utente.

---

## Step 6 — Dominio

Queste informazioni non sono deducibili dal codice. Chiedi all'utente:

> ### Dominio del progetto
>
> 1. **Glossario**: quali sono i termini chiave del business? Per ognuno, dammi il termine e una definizione breve.
>    Esempio: "Pratica = unita' di lavoro che rappresenta una richiesta di finanziamento"
>
> 2. **Regole di business principali**: quali sono le regole che il sistema deve sempre rispettare?
>    Esempio: "Una pratica bloccata non puo' essere modificata"
>
> 3. **Stati delle entita' principali**: quali entita' hanno un ciclo di vita con stati?
>    Esempio: "Pratica: bozza → inviata → in_validazione → validata → rifiutata"
>
> Se non hai queste informazioni adesso, posso lasciarle vuote e aggiungerle dopo.

---

## Step 7 — Reference files

> Hai materiale di riferimento da includere nel profilo?
>
> - **Screenshot del design system** (palette, componenti tipici)
> - **Esempi di codice "gold standard"** (un'entita' ben fatta, un componente esemplare)
> - **Template specifici** (template email, PDF, report)
>
> Se si', dammi i path dei file. Li copio nella cartella del profilo sotto `references/`.
> Se no, salto questo step.

Se l'utente fornisce file:

```bash
mkdir -p <profiles_repo>/<nome>/references/design-system
mkdir -p <profiles_repo>/<nome>/references/examples
cp <path-file> <profiles_repo>/<nome>/references/<sottocartella>/
```

---

## Step 8 — Genera profile.json

Assembla tutti i dati raccolti in un `profile.json` e scrivilo:

Path: `<profiles_repo>/<nome>/profile.json`

Usa il formato definito nella design spec (sezione 2). Includi solo le sezioni per cui ci sono dati. Non includere campi con valori vuoti o null — omettili completamente.

Presenta il JSON generato all'utente per conferma finale prima di scrivere.

---

## Step 9 — Commit e push

Dopo la conferma:

```bash
cd <profiles_repo>
git add <nome>/
git commit -m "feat: add profile for <nome>"
git push origin main
```

Se il push fallisce (no remote, conflitti), avvisa l'utente e suggerisci la soluzione.

---

## Step 10 — Aggiorna .br-local.json

Per ogni codebase coinvolto, proponi di aggiornare il `.br-local.json` nella root del repo:

> Vuoi che aggiorni il `.br-local.json` nei codebase del progetto?
>
> Aggiungero' i campi `profilo` e `profiles_repo`:
>
> **BE** — `<path-be>/.br-local.json`:
> ```json
> {
>   "profilo": "<nome>",
>   "profiles_repo": "<profiles_repo>"
> }
> ```
>
> **FE** — `<path-fe>/.br-local.json`:
> ```json
> {
>   "profilo": "<nome>",
>   "profiles_repo": "<profiles_repo>"
> }
> ```

Se il file esiste gia', aggiungi i nuovi campi preservando quelli esistenti (`developer`, `paths`). Se non esiste, crealo con i campi base.

---

## Regole

1. **Una domanda alla volta** — non anticipare domande
2. **Auto-detect prima, domande poi** — dedurre il massimo dal codice
3. **Mai scrivere senza conferma** — mostra sempre l'output prima di scrivere il profile.json
4. **Campi opzionali sono opzionali** — non forzare l'utente a compilare tutto
5. **Il profilo e' un documento vivo** — br-analyzer lo aggiorna automaticamente
````

- [ ] **Step 3: Copy SKILL.md to portal-flow**

Copy `claude-flow/skills/br-profile-setup/SKILL.md` to `portal-flow/skill/br-profile-setup/SKILL.md`. The content is identical.

- [ ] **Step 4: Create install.sh in portal-flow**

Create `portal-flow/skill/br-profile-setup/install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/br-profile-setup"

echo "=== br-profile-setup installer ==="
echo ""

if [ -L "$SKILL_DIR" ]; then
    EXISTING_TARGET="$(readlink "$SKILL_DIR")"
    if [ "$EXISTING_TARGET" = "$SCRIPT_DIR" ]; then
        echo "Symlink already exists and points to the correct location."
    else
        echo "Symlink exists but points to: $EXISTING_TARGET"
        echo "Updating to: $SCRIPT_DIR"
        rm "$SKILL_DIR"
        ln -s "$SCRIPT_DIR" "$SKILL_DIR"
        echo "Symlink updated."
    fi
elif [ -d "$SKILL_DIR" ]; then
    echo "ERROR: $SKILL_DIR exists as a directory (not a symlink)."
    echo "Remove it manually and re-run this script."
    exit 1
else
    mkdir -p "$(dirname "$SKILL_DIR")"
    ln -s "$SCRIPT_DIR" "$SKILL_DIR"
    echo "Symlink created: $SKILL_DIR -> $SCRIPT_DIR"
fi

if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo "Verification: SKILL.md found at $SKILL_DIR/SKILL.md"
else
    echo "ERROR: SKILL.md not found after symlink. Something went wrong."
    exit 1
fi

echo ""
echo "=== Add this to ~/.claude/CLAUDE.md ==="
echo ""
cat <<'BLOCK'
# br-profile-setup
- **br-profile-setup** (`~/.claude/skills/br-profile-setup/SKILL.md`) - creazione guidata profilo progetto con auto-detect codebase. Trigger: "crea profilo progetto", "setup profilo", "nuovo profilo"
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating a project profile, invoke the Skill tool with `skill: "br-profile-setup"` before doing anything else.
BLOCK

echo ""
echo "Done."
```

- [ ] **Step 5: Commit in both repos**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-profile-setup/SKILL.md
git commit -m "feat: add br-profile-setup skill for guided profile creation"
```

```bash
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow
git add skill/br-profile-setup/SKILL.md skill/br-profile-setup/install.sh
git commit -m "feat: add br-profile-setup skill for guided profile creation"
```

---

### Task 5: Modify br-analyzer — add profile loading, explorer, auto-update

**Files:**
- Modify: `claude-flow/skills/br-analyzer/SKILL.md`

The analyzer gets three additions: (A) profile loading before Fase 1, (B) br-codebase-explorer dispatch in Fase 3, (C) profile auto-update after Fase 4.

- [ ] **Step 1: Add profile loading section**

In `skills/br-analyzer/SKILL.md`, after the flow diagram (line ~14, after the `br-progress-report` line) and before `## Fase 1 — Raccolta Input`, insert:

```markdown
---

## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Se il campo `custom_agents` e' presente nel profilo, leggi anche i file .md degli agenti referenziati (path relativi alla cartella del profilo)
   d. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Quando il profilo e' disponibile:
- Nella Fase 1, salta la Domanda 1 (Codebase) se i path sono gia' in `.br-local.json`
- Nella Fase 3, usa br-codebase-explorer con il profilo iniettato per l'esplorazione
- Nella Fase 4, dopo la generazione degli output, confronta il codebase con il profilo per proporre aggiornamenti
```

- [ ] **Step 2: Modify exploration section (Fase 3.2)**

In `skills/br-analyzer/SKILL.md`, find section `### 3.2 — Esplorazione dei codebase` (around line 184). Replace the content of that subsection with:

```markdown
### 3.2 — Esplorazione dei codebase

**Se il profilo progetto e' disponibile:**

Per ogni codebase, lancia un agente `br-codebase-explorer` (leggendo le sue istruzioni da `~/.claude/agents/br-codebase-explorer.md`) con:
- Il profilo progetto completo (JSON)
- I requisiti estratti dalla documentazione (dalla Fase 3.1)
- Il path del codebase da esplorare

L'explorer usa il profilo per navigare in modo mirato: sa dove cercare entita', servizi, controller, e conosce la terminologia di dominio.

Per codebase indipendenti (es. BE e FE), lancia gli explorer in parallelo.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Per ogni codebase fornito, analizza:
- **Struttura del progetto**: package, moduli, layer architetturali
- **Modello dati**: entita', DTO, migration, relazioni
- **API/Controller**: endpoint esposti, payload, validazioni
- **Servizi**: logica di business, workflow, macchine a stati
- **Repository**: query, viste, materializzazioni
- **Frontend** (se applicabile): componenti, routing, modelli, i18n, servizi
- **Configurazione**: properties, feature flag, sicurezza

Usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase quando possibile.
```

- [ ] **Step 3: Add profile auto-update section**

In `skills/br-analyzer/SKILL.md`, after the entire `## Fase 4 — Generazione Output` section (at the end of the file, before any closing section), add:

```markdown
---

## Fase 5 — Aggiornamento Automatico Profilo

Questa fase si esegue SOLO se il profilo progetto e' disponibile (caricato nella fase iniziale).

Dopo aver completato la gap analysis, il codebase e' stato esplorato in dettaglio. Confronta quello che hai trovato col profilo esistente e rileva delta significativi.

**Delta da rilevare:**

- Nuovi package/moduli non presenti nel profilo
- Rinominazione di classi base (es. `BaseEntity` → `BaseAuditEntity`)
- Cambio di API prefix (es. `/api/v1` → `/api/v2`)
- Nuovo framework o libreria (es. aggiunta di un message broker)
- Cambiamenti nel design system (font, colori, componenti)
- Nuovi stati di entita' rispetto al glossario

**Delta da ignorare (rumore):**

- File temporanei o di configurazione locale
- Differenze di branch (file presenti solo su feature branch)
- Dipendenze transitorie (non nel build file principale)

**Se trovi delta significativi**, presentali all'utente:

> Ho rilevato differenze tra il codebase e il profilo progetto:
>
> | Aspetto | Profilo | Codebase | Delta |
> |---|---|---|---|
> | Base entity | BaseEntity | BaseAuditEntity | Rinominata |
> | Nuovo package | — | com.progetto.notification | Aggiunto |
> | API prefix | /api/v1 | /api/v2 (parziale) | Migrazione in corso |
> | Font | Roboto | Inter | Cambiato |
>
> Aggiorno il profilo?

Se confermato:

1. Aggiorna il `profile.json` nel repo profili
2. Commit e push:
   ```bash
   cd <profiles_repo>
   git add <profilo>/profile.json
   git commit -m "chore: auto-update profile <profilo> from br-analyzer"
   git push origin main
   ```
3. Tutti i developer avranno il profilo aggiornato al prossimo pull (automatico a ogni invocazione skill)

**Se non trovi delta**, non mostrare nulla — passa silenziosamente alla fine.
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-analyzer/SKILL.md
git commit -m "feat: add profile loading, explorer agent, and auto-update to br-analyzer"
```

---

### Task 6: Modify br-executor — add profile loading, routing, verifier

**Files:**
- Modify: `claude-flow/skills/br-executor/SKILL.md`

The executor gets three additions: (A) profile loading before Fase 1, (B) routing to specialist subagent_types in Fase 3, (C) br-verifier dispatch replacing inline verification in Fase 3.

- [ ] **Step 1: Add profile loading section**

In `skills/br-executor/SKILL.md`, after the intro paragraph (line ~9, after "tiene aggiornato il file di progresso.") and before `## Fase 1 — Raccolta Input`, insert:

```markdown
---

## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Se il campo `custom_agents` e' presente nel profilo, leggi anche i file .md degli agenti referenziati (path relativi alla cartella del profilo)
   d. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Quando il profilo e' disponibile:
- Nella Fase 1, usa i campi `profilo` e `paths` da `.br-local.json` per pre-compilare le risposte
- Nella Fase 3, instrada i sottoagenti al subagent_type corretto in base allo stack
- Nella Fase 3, usa br-verifier per la verifica al posto della verifica inline
- Inietta convenzioni e dominio dal profilo in tutti i prompt dei sottoagenti
```

- [ ] **Step 2: Add routing section to Fase 3**

In `skills/br-executor/SKILL.md`, find section `#### Come istruire un sottoagente` (around line 312). Before this subsection, insert a new subsection:

```markdown
#### Routing a Specialist per Stack

**Se il profilo progetto e' disponibile**, usa il campo `tech_stack` per instradare il lavoro al subagent_type piu' adatto.

Logica di routing:
1. Determina l'area della task dalla colonna **Area** del piano (es. BE, FE, BE+FE)
2. Per area BE: leggi `tech_stack.backend.framework` dal profilo e mappa:

| Stack (dal profilo) | subagent_type |
|---|---|
| Spring Boot | `spring-boot-engineer` |
| .NET Core | `csharp-developer` |
| Django | `django-developer` |
| FastAPI | `fastapi-developer` |
| Node.js / Express | `node-specialist` |
| Laravel | `laravel-specialist` |
| Java (generico) | `java-architect` |
| Python (generico) | `python-pro` |
| Go | `golang-pro` |
| Rust | `rust-engineer` |
| Kotlin | `kotlin-specialist` |
| Swift | `swift-expert` |
| PHP | `php-pro` |

3. Per area FE: leggi `tech_stack.frontend.framework` dal profilo e mappa:

| Stack (dal profilo) | subagent_type |
|---|---|
| Angular | `angular-architect` |
| React | `react-specialist` |
| Vue | `vue-expert` |
| Next.js | `nextjs-developer` |
| Flutter | `flutter-expert` |

4. Lancia il sottoagente con `Agent(subagent_type: "<tipo>", prompt: "<prompt>")` invece di `Agent(prompt: "<prompt>")`
5. Se il framework non e' nella tabella o il profilo non e' disponibile, usa `general-purpose` (fallback, comportamento attuale)

Per task multi-area (BE + FE), lancia specialist diversi per ogni sotto-step in sequenza: prima lo specialist BE per l'API, poi lo specialist FE per il componente che la consuma.

**Iniezione profilo nel prompt del sottoagente:**

Quando il profilo e' disponibile, aggiungi al prompt del sottoagente (dopo i vincoli):

```
Contesto progetto (dal profilo):
- Framework: <tech_stack.backend.framework o frontend.framework>
- Package structure: <conventions.package_structure>
- Layers: <conventions.layers>
- Base entity: <conventions.base_entity>
- API prefix: <conventions.api_prefix>
- Test framework: <conventions.test_framework>
- Test naming: <conventions.test_naming>
- Design system: <palette, typography, spacing se area FE>
```
```

- [ ] **Step 3: Replace inline verification with br-verifier dispatch**

In `skills/br-executor/SKILL.md`, find section `#### Verifica del lavoro dei sottoagenti` (around line 359). Replace the entire content of this subsection (Fase A, Fase B, Fase C) with:

```markdown
#### Verifica del lavoro dei sottoagenti

Dopo che ogni sottoagente completa il suo lavoro, delega la verifica all'agente `br-verifier`.

**Se il profilo progetto e' disponibile:**

Leggi le istruzioni dell'agente da `~/.claude/agents/br-verifier.md`. Costruisci un prompt che includa:

1. **Requisiti** — descrizione della task dal piano e dal gap report
2. **File modificati** — lista completa dei file creati/modificati dal sottoagente
3. **Risultati test** — esegui prima la suite di test e passa l'output
4. **Convenzioni dal profilo** — `test_naming`, `base_entity`, `package_structure`, `commit_convention`

Lancia il verifier e attendi il verdict.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esegui la verifica inline in 3 fasi come segue:

**Fase A — Verifica tecnica (automatica)**

1. **Esegui i test** — lancia la suite di test e verifica che TUTTI i test passino (zero failure)
2. **Verifica la build** — assicurati che il progetto compili senza errori ne' warning significativi
3. **Controlla i test scritti** — verifica che il sottoagente abbia scritto test che coprano:
   - Il caso felice (happy path)
   - I casi limite (edge case): input vuoti, null, valori al boundary, liste vuote, stringhe troppo lunghe, concorrenza
   - I casi di errore: cosa succede quando la dipendenza fallisce, il DB non risponde, l'input e' malformato
   - Se i test edge case mancano, **non procedere** — istruisci un nuovo sottoagente per aggiungerli

**Fase B — Verifica di coerenza col requisito (manuale)**

Rileggi la descrizione della task dal piano e dal gap report. Per OGNI requisito elencato nella task, verifica:

1. **E' stato implementato?** — il codice prodotto copre effettivamente quel requisito, non solo qualcosa di simile
2. **E' stato implementato correttamente?** — il comportamento corrisponde a quello descritto, non a un'interpretazione semplificata
3. **Manca qualcosa?** — ci sono aspetti del requisito che il sottoagente ha ignorato o saltato

Se trovi discrepanze, istruisci un nuovo sottoagente per correggere. Ripeti la Fase B dopo la correzione.

**Fase C — Riesame finale (second look)**

1. **Rileggere il codice prodotto dall'inizio alla fine** — non fidarti del riepilogo del sottoagente
2. **Cercare assunzioni nascoste** — il sottoagente ha fatto assunzioni non esplicite nei requisiti?
3. **Verificare che i test testino realmente** — asserzioni specifiche e significative
4. **Controllare i nomi** — variabili, metodi, classi seguono le convenzioni del progetto

Se trovi problemi, correggi con un sottoagente dedicato e ripeti la Fase C.

**In entrambi i casi (con o senza verifier):**

Se il verdict e' FAIL (o la verifica inline trova problemi), leggi i dettagli e lancia un sottoagente di correzione. Ripeti la verifica dopo la correzione.

Solo quando la verifica e' superata il sotto-step e' considerato verificato.
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-executor/SKILL.md
git commit -m "feat: add profile loading, specialist routing, and verifier to br-executor"
```

---

### Task 7: Modify br-debug — add profile loading, routing, verifier

**Files:**
- Modify: `claude-flow/skills/br-debug/SKILL.md`
- Modify: `portal-flow/skill/br-debug/SKILL.md`

Same pattern as Task 6: profile loading, routing, and verifier. The br-debug SKILL.md is identical in both repos.

- [ ] **Step 1: Add profile loading section**

In `claude-flow/skills/br-debug/SKILL.md`, after the context detection table (around line 33, after the `| portal-flow | manifest...` row) and before `## Rilevamento Modalita'`, insert:

```markdown
---

## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Se il campo `custom_agents` e' presente nel profilo, leggi anche i file .md degli agenti referenziati (path relativi alla cartella del profilo)
   d. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Quando il profilo e' disponibile:
- Nella Fase 2, instrada i sottoagenti al subagent_type corretto in base allo stack del codebase coinvolto
- Nella Fase 2, usa br-verifier per la verifica al posto della verifica inline
- Inietta convenzioni e dominio dal profilo nei prompt dei sottoagenti
```

- [ ] **Step 2: Add routing section to Fase 2**

In `claude-flow/skills/br-debug/SKILL.md`, find section `### Esecuzione con sottoagenti` in Fase 2 (the section that describes dispatching subagents for bug fixes). Before the existing dispatch example, insert:

```markdown
#### Routing a Specialist per Stack

**Se il profilo progetto e' disponibile**, determina il subagent_type in base al codebase coinvolto nel bug:

1. Identifica l'area del bug dalla colonna `fase`/`sezione` e dalla task collegata
2. Leggi `tech_stack.backend.framework` o `tech_stack.frontend.framework` dal profilo
3. Mappa al subagent_type usando la stessa tabella di br-executor:

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
| (non riconosciuto/no profilo) | `general-purpose` (fallback) |

4. Lancia il sottoagente con `Agent(subagent_type: "<tipo>", prompt: "<prompt>")` invece di `Agent(prompt: "<prompt>")`
5. Se il profilo non e' disponibile, usa `general-purpose` (comportamento attuale)

Aggiungi al prompt del sottoagente il contesto dal profilo (convenzioni, test naming, package structure).
```

- [ ] **Step 3: Add br-verifier dispatch to Fase 2 verification**

In `claude-flow/skills/br-debug/SKILL.md`, find section `### Verifica in 3 fasi` in Fase 2. Before the existing Fase A, insert:

```markdown
**Se il profilo progetto e' disponibile:**

Delega la verifica all'agente `br-verifier` (leggendo le sue istruzioni da `~/.claude/agents/br-verifier.md`). Passa:
- Requisiti: descrizione del bug + ipotesi di root cause
- File modificati: lista dei file toccati dal sottoagente
- Risultati test: output dell'esecuzione test
- Convenzioni dal profilo: test_naming, base_entity, package_structure

Se il verifier restituisce FAIL, leggi i dettagli e lancia un sottoagente di correzione. Ripeti la verifica.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esegui la verifica inline in 3 fasi come segue:
```

Il testo delle Fasi A, B, C rimane invariato (e' il fallback senza profilo).

- [ ] **Step 4: Copy updated SKILL.md to portal-flow**

```bash
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-debug/SKILL.md C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-debug/SKILL.md
```

- [ ] **Step 5: Commit in both repos**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-debug/SKILL.md
git commit -m "feat: add profile loading, specialist routing, and verifier to br-debug"
```

```bash
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow
git add skill/br-debug/SKILL.md
git commit -m "feat: add profile loading, specialist routing, and verifier to br-debug"
```

---

### Task 8: Modify br-updater — add profile loading and explorer

**Files:**
- Modify: `claude-flow/skills/br-updater/SKILL.md`

- [ ] **Step 1: Add profile loading section**

In `skills/br-updater/SKILL.md`, after the intro paragraph (line ~9, after "senza perdere il lavoro gia' fatto.") and before `## Fase 1 — Raccolta Input`, insert:

```markdown
---

## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Se il campo `custom_agents` e' presente nel profilo, leggi anche i file .md degli agenti referenziati (path relativi alla cartella del profilo)
   d. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Quando il profilo e' disponibile:
- Usa br-codebase-explorer con il profilo iniettato per ri-verificare il codebase aggiornato
- Il profilo fornisce contesto su dove guardare e che terminologia aspettarsi
```

- [ ] **Step 2: Add explorer dispatch to re-verification**

In `skills/br-updater/SKILL.md`, find the section where the codebase is re-analyzed to detect deltas. Add after the re-analysis instructions:

```markdown
### Ri-esplorazione con br-codebase-explorer

**Se il profilo progetto e' disponibile:**

Per ogni codebase coinvolto nel delta, lancia un agente `br-codebase-explorer` (leggendo le sue istruzioni da `~/.claude/agents/br-codebase-explorer.md`) con:
- Il profilo progetto completo (JSON)
- I NUOVI requisiti dalla documentazione aggiornata
- Il path del codebase da esplorare

L'explorer usa il profilo per navigare in modo mirato e confrontare la terminologia. L'output strutturato viene usato per aggiornare il gap report.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esplora il codebase direttamente come oggi, analizzando struttura, modello dati, API, servizi, frontend e configurazione.
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-updater/SKILL.md
git commit -m "feat: add profile loading and explorer agent to br-updater"
```

---

### Task 9: Modify br-reviewer — add profile loading for code check

**Files:**
- Modify: `claude-flow/skills/br-reviewer/SKILL.md`

- [ ] **Step 1: Add profile loading section**

In `skills/br-reviewer/SKILL.md`, after the flow diagram (line ~14) and before `## Fase 1 — Raccolta Input`, insert:

```markdown
---

## Caricamento Profilo Progetto

Prima di iniziare qualsiasi operazione, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene i campi `profilo` e `profiles_repo`:
   a. Sincronizza il repo profili: `git -C <profiles_repo> pull origin main --quiet`
   b. Leggi `<profiles_repo>/<profilo>/profile.json`
   c. Salva il profilo in memoria per uso nelle fasi successive
3. Se `.br-local.json` non ha `profilo` o `profiles_repo`, procedi senza profilo (comportamento attuale, retrocompatibilita' completa)

Quando il profilo e' disponibile:
- Nella Fase 3 (Analisi), il check leggero contro il codice usa il glossario dal profilo (`domain.glossary`) per un confronto terminologico piu' preciso
- Gli stati delle entita' (`domain.entity_states`) vengono confrontati con quelli descritti nel BR
- Le regole di business (`domain.business_rules`) vengono verificate per coerenza con la documentazione
```

- [ ] **Step 2: Enhance code check with profile terminology**

In `skills/br-reviewer/SKILL.md`, find the section about the code check (the light check against existing code). Add this paragraph:

```markdown
#### Check terminologico con profilo

**Se il profilo e' disponibile con `domain.glossary`:**

Per ogni termine nel glossario del profilo, verifica se il BR lo usa con la stessa semantica:
- Se il BR usa un termine diverso per lo stesso concetto → segnala come discrepanza terminologica
- Se il BR introduce un nuovo termine non nel glossario → segnala come termine da aggiungere al glossario
- Se il profilo ha `domain.entity_states` e il BR descrive transizioni di stato → confronta e segnala differenze

Queste discrepanze finiscono nella **Parte 2 — Per il team tecnico** del report, nella sezione "Disallineamenti terminologici".

**Se il profilo non e' disponibile:**

Esegui il check terminologico standard (confronto diretto tra nomi nel BR e nel codice).
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-reviewer/SKILL.md
git commit -m "feat: add profile loading and enhanced terminology check to br-reviewer"
```

---

### Task 10: Modify br-pipeline (claude-flow) — show profile info

**Files:**
- Modify: `claude-flow/skills/br-pipeline/SKILL.md`

- [ ] **Step 1: Add profile loading to pipeline init**

In `skills/br-pipeline/SKILL.md`, in the section about Fase 1 — Rilevamento BR (after the manifest search logic), add:

```markdown
### Caricamento Profilo (se disponibile)

Dopo aver trovato i BR attivi, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene `profilo` e `profiles_repo`, carica il `profile.json`
3. Usa il profilo per arricchire la dashboard con informazioni progetto
```

- [ ] **Step 2: Add profile info to dashboard display**

In `skills/br-pipeline/SKILL.md`, find the section where the TL/PM dashboard is shown (Fase 3). In the header section of the dashboard display, add:

```markdown
**Se il profilo e' disponibile**, mostra le informazioni progetto nell'header della dashboard:

> **Progetto: <project.name>** (<project.client>)
> Stack: <tech_stack.backend.framework> + <tech_stack.frontend.framework>
> Profilo: `<profilo>` (ultimo sync: <data pull>)
```

- [ ] **Step 3: Add profile info to Dev dashboard**

In the Dev dashboard section, add:

```markdown
**Se il profilo e' disponibile**, mostra nell'header:

> **Progetto: <project.name>**
> Stack BE: <tech_stack.backend.framework> | Stack FE: <tech_stack.frontend.framework>
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-pipeline/SKILL.md
git commit -m "feat: show profile info in br-pipeline dashboard"
```

---

### Task 11: Modify br-pipeline (portal-flow) — show profile info

**Files:**
- Modify: `portal-flow/skill/br-pipeline/SKILL.md`

- [ ] **Step 1: Add profile loading to entry point**

In `portal-flow/skill/br-pipeline/SKILL.md`, in the Entry Point section after "### 3. Identificazione ruolo", add:

```markdown
### 4. Caricamento Profilo (se disponibile)

Dopo l'identificazione del ruolo, tenta di caricare il profilo progetto:

1. Leggi `.br-local.json` dalla root del repo corrente
2. Se contiene `profilo` e `profiles_repo`, sincronizza e carica il `profile.json`
3. Usa il profilo per arricchire la dashboard e la configurazione del setup Dev

**Aggiornamento Setup Dev:**

Se l'utente e' un Dev e `.br-local.json` non ha `profilo` o `profiles_repo`, ma il TL/PM ha gia' creato un profilo, chiedi:

> Il profilo progetto **<nome>** e' disponibile. Vuoi configurare il collegamento?
> Dammi il path locale del clone di `deloitte-profiles`.

Se confermato, aggiungi `profilo` e `profiles_repo` al `.br-local.json`.
```

- [ ] **Step 2: Add profile info to TL/PM dashboard**

In the TL/PM dashboard section, add:

```markdown
**Se il profilo e' disponibile**, mostra nell'header della dashboard:

> **Progetto: <project.name>** (<project.client>)
> Stack: <tech_stack.backend.framework> + <tech_stack.frontend.framework>
> Profilo: `<profilo>` (ultimo sync: <data pull>)
```

- [ ] **Step 3: Add profile info to Dev dashboard**

In the Dev dashboard section, add:

```markdown
**Se il profilo e' disponibile**, mostra nell'header:

> **Progetto: <project.name>**
> Stack BE: <tech_stack.backend.framework> | Stack FE: <tech_stack.frontend.framework>
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow
git add skill/br-pipeline/SKILL.md
git commit -m "feat: show profile info in br-pipeline dashboard"
```

---

### Task 12: Update BR_SKILLS_DOCUMENTATION.md

**Files:**
- Modify: `claude-flow/BR_SKILLS_DOCUMENTATION.md`

- [ ] **Step 1: Update the architecture diagram**

In `BR_SKILLS_DOCUMENTATION.md`, find the flow diagram at the top. After the `br-progress-report` line and before the closing "```", add:

```
        |
        |   (profili progetto)
        |         |
        |         v
        |   deloitte-profiles/       profili centralizzati
        |   <progetto>/profile.json  stack, convenzioni, dominio
        |
        |   (agenti generici)
        |         |
        |         v
        |   br-codebase-explorer     esplorazione profilo-aware
        |   br-verifier              verifica 3 fasi profilo-aware
```

- [ ] **Step 2: Add new section 9 — Profili Progetto**

After section 8 (BR Debug), add:

```markdown
---

## 9. Profili Progetto

### Repo deloitte-profiles

Repository centralizzato con un `profile.json` per progetto. Contiene stack tecnico, convenzioni, dominio e design system.

| Sezione | Contenuto | Obbligatoria |
|---|---|---|
| `project` | Nome, cliente, descrizione | Si |
| `tech_stack` | Backend + frontend: linguaggio, framework, DB, ORM | Si |
| `conventions` | Package structure, layers, API prefix, test naming | No |
| `design_system` | Palette, tipografia, spaziatura, componenti | No |
| `domain` | Glossario, regole di business, stati entita' | No |
| `custom_agents` | Path a agenti specifici del progetto | No |

### Configurazione locale (.br-local.json)

Due nuovi campi:

| Campo | Descrizione |
|---|---|
| `profilo` | Nome della cartella nel repo profili (es. "pnrr") |
| `profiles_repo` | Path locale del clone di deloitte-profiles |

### Caricamento automatico

Tutte le skill BR caricano il profilo allo startup:
1. Leggono `.br-local.json`
2. `git pull` sul repo profili
3. Leggono `profile.json`
4. Iniettano il contesto nei prompt dei sottoagenti

Fallback: senza `profilo`/`profiles_repo`, le skill funzionano come prima.

### Manutenzione automatica

`br-analyzer` aggiorna il profilo dopo ogni gap analysis confrontando codebase vs profilo. Delta significativi vengono proposti all'utente.

---

## 10. Agenti Generici

### br-codebase-explorer

**File**: `~/.claude/agents/br-codebase-explorer.md`
**Usato da**: br-analyzer, br-updater

Esploratore di codebase generico. Riceve profilo, documentazione BR, e path del codebase. Produce output strutturato per la gap analysis. Usa il profilo per navigare in modo mirato (package structure, layers, API prefix, terminologia).

### br-verifier

**File**: `~/.claude/agents/br-verifier.md`
**Usato da**: br-executor, br-debug

Verificatore in 3 fasi del lavoro dei sottoagenti. Riceve requisiti, file modificati, risultati test, e convenzioni dal profilo. Produce verdict PASS/FAIL strutturato.

### Routing a Specialist

Le skill br-executor e br-debug instradano al subagent_type giusto in base al `tech_stack` dal profilo:

| Stack | subagent_type |
|---|---|
| Spring Boot | `spring-boot-engineer` |
| .NET Core | `csharp-developer` |
| Angular | `angular-architect` |
| React | `react-specialist` |
| (altri) | vedi design spec completa |

---

## 11. BR Profile Setup

**Skill**: `br-profile-setup`
**Path**: `~/.claude/skills/br-profile-setup/SKILL.md`
**Trigger**: "crea profilo progetto", "setup profilo", "nuovo profilo"

Creazione guidata di un profilo progetto con auto-detect del codebase (10 step):
1. Nome progetto
2. Path repo profili
3. Codebase coinvolti
4. Auto-detect framework, convenzioni, design system
5. Conferma e correzione
6. Domande dominio (glossario, regole, stati)
7. Reference files (opzionali)
8. Genera profile.json
9. Commit + push su deloitte-profiles
10. Aggiorna .br-local.json nei codebase
```

- [ ] **Step 3: Update trigger table**

Find the "Trigger Registrati (CLAUDE.md)" table and add:

```markdown
| "crea profilo progetto" / "setup profilo" / "nuovo profilo" / "configura il profilo" | br-profile-setup |
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add BR_SKILLS_DOCUMENTATION.md
git commit -m "docs: add profiles, agents, and profile-setup to BR skills documentation"
```

---

### Task 13: Update README.md claude-flow

**Files:**
- Modify: `claude-flow/README.md`

- [ ] **Step 1: Update skill count in intro**

In `README.md`, find the first line "Suite di 8 skill" and update to:

```markdown
Suite di 9 skill e 2 agenti generici per Claude Code che automatizzano il ciclo di vita dei Business Requirements: dalla review della documentazione funzionale alla gestione delle risposte del funzionale, dall'analisi gap all'esecuzione task, dalla gestione dei bug segnalati dai funzionali all'aggiornamento incrementale e al reporting Excel, con un orchestratore pipeline che coordina il tutto. Include profili progetto centralizzati per scalare a tutti i progetti.
```

- [ ] **Step 2: Add br-profile-setup to skills section**

After the br-debug section and before the br-pipeline section, add:

```markdown
### br-profile-setup

Crea un nuovo profilo progetto nel repo centralizzato `deloitte-profiles/`. Auto-detect del codebase (framework, convenzioni, design system), domande guidate su dominio e glossario, generazione profile.json con commit+push, e configurazione automatica di `.br-local.json` nei codebase coinvolti.

**Trigger**: `crea profilo progetto`, `setup profilo`, `nuovo profilo`
```

- [ ] **Step 3: Add agents section**

After all the skill sections and before "## Installazione", add:

```markdown
## Agenti Generici

### br-codebase-explorer

Esploratore di codebase profilo-aware. Usato da `br-analyzer` e `br-updater` per la gap analysis. Riceve il profilo progetto e naviga il codice in modo mirato, producendo output strutturato.

### br-verifier

Verificatore in 3 fasi profilo-aware. Usato da `br-executor` e `br-debug` per verificare il lavoro dei sottoagenti. Produce verdict PASS/FAIL strutturato usando le convenzioni dal profilo.

### Routing a specialist

Con profilo configurato, `br-executor` e `br-debug` instradano i sottoagenti al subagent_type appropriato (es. `spring-boot-engineer` per Spring Boot, `angular-architect` per Angular). Senza profilo, usano `general-purpose` (retrocompatibilita').
```

- [ ] **Step 4: Update installation section**

In the installation section, update the copy command and add agent installation:

```markdown
cp -r skills/br-* ~/.claude/skills/
cp -r agents/br-* ~/.claude/agents/
```

Update the note: "Questo copia tutte le 9 skill e i 2 agenti generici."

- [ ] **Step 5: Add trigger block for br-profile-setup**

In the trigger blocks section, add after the br-debug block:

```markdown
# br-profile-setup
- **br-profile-setup** (`~/.claude/skills/br-profile-setup/SKILL.md`) - creazione guidata profilo progetto con auto-detect codebase. Trigger: "crea profilo progetto", "setup profilo", "nuovo profilo"
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating a project profile, invoke the Skill tool with `skill: "br-profile-setup"` before doing anything else.
```

- [ ] **Step 6: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add README.md
git commit -m "docs: add profile-setup skill, agents, and routing to README"
```

---

### Task 14: Register br-profile-setup trigger in global CLAUDE.md

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Add br-profile-setup trigger block**

In `~/.claude/CLAUDE.md`, after the br-debug block and before the jarvis-polling block, add:

```markdown
# br-profile-setup
- **br-profile-setup** (`~/.claude/skills/br-profile-setup/SKILL.md`) - creazione guidata profilo progetto con auto-detect codebase, domande dominio, e configurazione .br-local.json. Trigger: "crea profilo progetto", "setup profilo", "nuovo profilo"
When the user says "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", or similar phrases about creating or configuring a project profile for the BR skills, invoke the Skill tool with `skill: "br-profile-setup"` before doing anything else.
```

- [ ] **Step 2: Verify trigger block format**

Compare with existing blocks (br-executor, br-debug, br-pipeline) to confirm the format matches:
- Header: `# br-profile-setup`
- Bullet with path, description, and trigger phrases
- `When the user says...` instruction with Skill tool invocation

No commit needed — `~/.claude/CLAUDE.md` is not in a git repo.

---

### Task 15: Final verification

- [ ] **Step 1: Verify file structure**

```bash
# deloitte-profiles
ls C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/profile-schema.json
ls C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles/README.md

# agents
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-codebase-explorer.md
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-verifier.md
ls ~/.claude/agents/br-codebase-explorer.md
ls ~/.claude/agents/br-verifier.md

# new skill
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-profile-setup/SKILL.md
ls C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-profile-setup/SKILL.md
ls C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-profile-setup/install.sh
```

All files should exist.

- [ ] **Step 2: Verify profile loading in all modified skills**

Read each modified skill and confirm it has the "Caricamento Profilo Progetto" section:

```bash
grep -l "Caricamento Profilo Progetto" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-analyzer/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-executor/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-debug/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-updater/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-reviewer/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-pipeline/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-pipeline/SKILL.md
```

All 7 files should match.

- [ ] **Step 3: Verify routing in executor and debug**

Read both skills and confirm they have the routing table:

```bash
grep -l "Routing a Specialist per Stack" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-executor/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-debug/SKILL.md
```

Both should match.

- [ ] **Step 4: Verify br-verifier dispatch in executor and debug**

```bash
grep -l "br-verifier" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-executor/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-debug/SKILL.md
```

Both should match.

- [ ] **Step 5: Verify br-codebase-explorer dispatch in analyzer and updater**

```bash
grep -l "br-codebase-explorer" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-analyzer/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-updater/SKILL.md
```

Both should match.

- [ ] **Step 6: Verify portal-flow consistency**

```bash
diff C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-debug/SKILL.md \
     C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-debug/SKILL.md
```

Should show no differences (identical files).

- [ ] **Step 7: Verify documentation**

Read `BR_SKILLS_DOCUMENTATION.md` and confirm:
- Architecture diagram includes profiles and agents
- Section 9 (Profili Progetto) exists
- Section 10 (Agenti Generici) exists
- Section 11 (BR Profile Setup) exists
- Trigger table includes br-profile-setup

- [ ] **Step 8: Verify CLAUDE.md**

Read `~/.claude/CLAUDE.md` and confirm the br-profile-setup trigger block exists and matches the format of other skill triggers.
