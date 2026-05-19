# Design Spec — Split `profile.json` in `CONST.json` + `PROFILE.json`

**Data:** 2026-05-19
**Stato:** Design approvato dall'utente, pronto per implementazione plan
**Autore:** Claude Code + davide94melis (brainstorming session)
**Repo coinvolte:** `claude-flow` (skill SDLC + script), `deloitte-profiles` (schemi + profili progetto)

---

## 1. Goal

Splittare l'attuale file di "costituzione" del progetto (`deloitte-profiles/<progetto>/constitution/profile.json`) in due file separati:

- **`CONST.json`** — principi, standard e convenzioni di archetipo, ripetibili tra progetti simili (OWASP, WCAG, responsiveness, test coverage minimo, error handling, code style, git workflow, pattern architetturali generici).
- **`PROFILE.json`** — dettagli specifici del progetto (tech stack con versioni, repositories con sigle, infrastructure, integrations, package structure, dominio, design system, glossario).

Il motivo: oggi i "principi inviolabili" vivono dentro `profile.json` (`conventions.inviolable_principles`), ma **nessuna skill SDLC li legge attivamente**. Lo split formalizza la separazione tra **policy stabile** (CONST, gestita manualmente) e **dati progetto** (PROFILE, auto-aggiornati da `sdlc-analyzer`), e fa sì che CONST sia attivamente caricato e enforce da tutte le 9 skill SDLC.

## 2. Motivazione

- I principi inviolabili attualmente sono "dormienti": presenti nel JSON ma ignorati dalle skill. Ogni output (PLAN, TASKS, REVIEW, fix bug) è generato senza che il modello abbia coscienza esplicita dei vincoli.
- La sezione `inviolable_principles` cresce solo manualmente; manca un template di default che ogni nuovo progetto eredita.
- Mescolare policy stabile (raramente cambia) e dati dinamici (cambiano ad ogni feature) nello stesso file crea attrito sui commit (ogni auto-update dell'analyzer tocca il file anche dove non dovrebbe).
- Splittare permette: (a) caricamento esplicito di CONST come "system prompt" implicito; (b) auto-update sicuro di PROFILE senza rischiare di alterare i principi; (c) template di default riusabile per nuovi progetti.

## 3. Decisioni chiave (output del brainstorming)

| Decisione | Scelta | Alternative scartate |
|---|---|---|
| Sharing tra progetti | **Per progetto, no condivisione** | CONST globale unico / CONST per archetipo condiviso |
| Formato file | **Entrambi JSON** | Entrambi MD / PROFILE.json + CONST.md |
| Perimetro CONST | **Tutto ciò che è ripetibile tra progetti simili** (principi + qualità + git + test + architettura) | Solo i 3 principi attuali / Principi + qualità tecnica |
| Consumo CONST | **Tutte le 9 skill caricano CONST + PROFILE all'avvio** | Solo skill rilevanti / Espansione inline in PLAN/TASKS |
| Template CONST iniziale | **Precompilato** con set completo, adattabile | Minimale (solo i 3 attuali) / Vuoto |
| Auto-update | **Solo PROFILE.json** | Entrambi (PROFILE + CONST con suggerimenti) |
| Strategia rollout | **Big bang** con migrazione automatica | Incrementale con compat layer |

## 4. Architettura — struttura file

```
deloitte-profiles/
├── README.md
├── const-schema.json          # NUOVO  — JSON Schema per CONST.json
├── profile-schema.json        # MODIFICATO — rimuove `conventions.inviolable_principles`
├── <progetto>/
│   ├── constitution/
│   │   ├── CONST.json         # NUOVO  — principi/standard di archetipo
│   │   └── PROFILE.json       # NUOVO  — dettagli specifici progetto (rinominato da profile.json)
│   ├── agents/
│   ├── references/
│   └── plans/
└── ...
```

**Vincoli:**
- La folder `constitution/` rimane (semanticamente: "la costituzione del progetto" = i due file insieme).
- Estensioni `.json` esplicite, no file senza estensione.
- Schemi nella root del repo (`const-schema.json` + `profile-schema.json`).
- `profile.json` (singolare) viene eliminato. Niente compat layer (un solo profilo esistente, sotto controllo locale).
- `.br-local.json` invariato: continua a puntare a `profilo` + `profiles_repo`. Le skill risolvono `<profiles_repo>/<profilo>/constitution/CONST.json` e `.../PROFILE.json`.

## 5. Contenuto di `CONST.json`

### 5.1 Macro-sezioni

1. **`inviolable_principles`** — non-negoziabili (security/OWASP, accessibility/WCAG, responsiveness, data_privacy/GDPR)
2. **`quality_standards`** — test coverage, error handling, logging, performance budget
3. **`code_style`** — limiti dimensionali (funzioni/file/nesting), no magic numbers, no debug statements in prod
4. **`git_workflow`** — branch pattern + commit convention generici
5. **`architectural_patterns`** — layered separation, API response envelope, AAA test pattern, input validation ai boundary

### 5.2 Template precompilato di default

Generato da `sdlc-profile-setup` per ogni nuovo progetto. L'utente lo adatta dopo la creazione.

```json
{
  "$schema": "../../const-schema.json",
  "inviolable_principles": {
    "security": {
      "rule": "Tutto il codice deve rispettare OWASP Top 10",
      "scope": "ogni endpoint, input utente, query, gestione dati sensibili",
      "verification": "verifica obbligatoria prima del merge"
    },
    "accessibility": {
      "rule": "Tutto il codice frontend deve rispettare WCAG 2.1 AA",
      "requirements": [
        "navigabile da tastiera",
        "compatibile screen reader",
        "contrasto AA",
        "attributi ARIA corretti"
      ]
    },
    "responsiveness": {
      "rule": "Tutto il codice frontend deve essere responsive",
      "breakpoints": ["mobile", "tablet", "desktop"]
    },
    "data_privacy": {
      "rule": "Mai loggare PII; rispettare GDPR per ogni dato personale",
      "scope": "log applicativi, error tracking, analytics"
    }
  },
  "quality_standards": {
    "test_coverage": {
      "minimum_percent": 80,
      "applies_to": ["unit", "integration"]
    },
    "error_handling": "Gestire ogni errore esplicitamente, mai swallow; user-facing friendly, server-side con context",
    "logging": {
      "format": "structured",
      "never_log": ["PII", "credenziali", "token"]
    },
    "performance": {
      "api_latency_p95_ms": 200,
      "frontend_lcp_ms": 2500
    }
  },
  "code_style": {
    "max_function_lines": 50,
    "max_file_lines": 800,
    "max_nesting_depth": 4,
    "no_magic_numbers": true,
    "no_debug_statements_in_prod": true
  },
  "git_workflow": {
    "branch_pattern": "feature/<desc> | fix/<desc> | release/sprint-wave-X.Y",
    "commit_convention": "conventional commits (feat:, fix:, refactor:, docs:, test:, chore:)"
  },
  "architectural_patterns": {
    "layered_separation": "controller/service/repository (o equivalenti) con dipendenze unidirezionali",
    "api_response_envelope": "shape consistente: { status, data|null, error|null, meta? }",
    "test_pattern": "Arrange-Act-Assert; nomi test descrittivi del comportamento atteso",
    "input_validation": "validare sempre ai boundary del sistema"
  }
}
```

### 5.3 Regole di adattamento del template

`sdlc-profile-setup` adatta il template di default in base al codebase rilevato:

| Condizione | Modifica al template |
|---|---|
| Nessun codebase frontend rilevato | Rimuovi `inviolable_principles.accessibility` e `inviolable_principles.responsiveness` |
| Nessuna API REST rilevata | Rimuovi `architectural_patterns.api_response_envelope` |
| Nessun database con dati personali (rilevato dal dominio) | Mantieni `data_privacy` come default conservativo, ma l'utente può rimuoverlo |

## 6. Contenuto di `PROFILE.json`

### 6.1 Macro-sezioni (invariate vs profile.json attuale, **eccetto rimozione di `conventions.inviolable_principles`**)

1. `project` — name, client, description
2. `tech_stack` — backend, frontend, repositories (multi-repo con sigle), infrastructure, integrations
3. `conventions` — package_structure, layers, base_entity, api_prefix, test_framework, test_naming, branch_convention, commit_convention, frontend (con valori SPECIFICI del progetto)
4. `design_system` — palette, typography, components, reference_files
5. `domain` — glossary, business_rules, entity_states
6. `custom_agents`

### 6.2 Regola di smistamento per campi grigi

| Campo | CONST (regola astratta) | PROFILE (valore concreto) |
|---|---|---|
| commit_convention | "conventional commits" | "conventional commits con descrizione mista IT/EN" |
| branch_convention | "feature/<desc>" pattern | "feature/<desc>, release/sprint-wave-X.Y, main=develop" |
| test_naming | "Arrange-Act-Assert" pattern | "shouldXxxWhenYyy" |
| layers | "layered con dipendenze unidirezionali" | `["controller","service","repository","domain","dto","mapper",...]` |
| test_framework | (non in CONST) | "JUnit 5 + Mockito + AssertJ" |
| api_prefix | (non in CONST) | "nessun prefix globale — path per controller (...)" |

**Principio guida:** *valore concreto → PROFILE*; *regola astratta → CONST*; *entrambi sensati → entrambi i file* (PROFILE specializza CONST per il progetto).

### 6.3 Esempio post-split di `banca-agente/constitution/PROFILE.json` (frammento `conventions`)

```json
"conventions": {
  "package_structure": "it.deloitte.ba.backend.<layer> oppure it.deloitte.ba.backend.<layer>.<feature>",
  "layers": [
    "controller", "service", "repository", "domain", "dto",
    "mapper", "config", "enumeration", "error", "utils",
    "audit", "scheduled", "shared", "connector", "interceptor", "annotation"
  ],
  "base_entity": "it.deloitte.ba.backend.audit.Auditable<U> (createdBy, createdDate, lastModifiedBy, lastModifiedDate)",
  "api_prefix": "nessun prefix globale — path per controller (/admin-util, /assessment, /public/*, /assurance, /back-office/*, /agency-desk/*, /dashboard, /chatbot, /iocr, /csv, /financing-agreements, /post-closing/*, /import-users, /consultant/reports, /owner/reports)",
  "test_framework": "JUnit 5 + Mockito + AssertJ",
  "test_naming": "shouldXxxWhenYyy (es. shouldCreateCsvDataRecord)",
  "branch_convention": "feature/<description>, release/sprint-wave-X.Y, main branch = develop",
  "commit_convention": "conventional commits (fix:, feat:) con descrizione mista IT/EN",
  "frontend": {
    "module_structure": "modulare per feature (module/agency-desk, module/autogreen, module/common, module/esgo, module/marketplace) + shared (class, const, directive, enum, helper, model, pipe, type, ui, validator) + service",
    "component_prefix": "app",
    "test_framework": "Karma + Jasmine",
    "test_naming": "describe + it('should ...')",
    "i18n": "@ngx-translate (assets/i18n/)"
  }
}
```

> **Nota:** `inviolable_principles` viene RIMOSSO da questa sezione e migrato in `CONST.json`.

## 7. Loader nelle skill SDLC

### 7.1 Pattern

Ogni skill SDLC (9 totali) avrà una sezione iniziale identica chiamata **"Caricamento contesto progetto (CONST + PROFILE)"**, posta subito dopo la sezione "Risoluzione Path" già esistente. Il pattern è la duplicazione strutturata (come fai oggi per la "Risoluzione Path") — non c'è meccanismo di import tra SKILL.md in Claude Code, quindi la coerenza si garantisce via review/codemod, non via dipendenza tecnica.

### 7.2 Sequenza di loading

1. Estrai `profiles_repo` e `profilo` da `.br-local.json` (passo già esistente).
2. `git -C "<profiles_repo>" pull origin main --quiet` (passo già esistente).
3. Leggi `<profiles_repo>/<profilo>/constitution/CONST.json`.
4. Leggi `<profiles_repo>/<profilo>/constitution/PROFILE.json`.
5. Se manca uno dei due → errore esplicito (vedi tabella 7.4) e stop.
6. Tieni entrambi i contesti attivi per tutta la durata della skill.

### 7.3 Semantica d'uso (parte istruzionale)

> **CONST** = vincoli inviolabili per ogni output generato.
> Ogni piano, task, fix, review, bug analysis che produci DEVE rispettare:
> - `inviolable_principles` (security/a11y/responsiveness/privacy)
> - `quality_standards` (coverage, error handling, logging, performance)
> - `code_style` (limiti dimensionali, no magic numbers)
> - `git_workflow` (branch/commit pattern)
> - `architectural_patterns` (layering, response envelope, AAA, validazione boundary)
>
> **PROFILE** = "lingua" del progetto. Usa i dettagli (tech stack, repositories con sigle, dominio, glossario, design system) per:
> - Nominare le task con le sigle giuste (es. BE/FE/EM/DM/GA per banca-agente)
> - Proporre snippet con il framework/versione corretti
> - Usare il vocabolario di dominio nel testo (es. Pratica, PSM, NDG)
> - Riferire componenti UI del design system (es. PrimeNG, palette, theme)

### 7.4 Gestione errori del loader (uniforme)

| Caso | Messaggio | Azione |
|---|---|---|
| `.br-local.json` manca | "Esegui prima `/sdlc-profile-setup`" | Stop |
| CONST.json manca, PROFILE.json esiste | "Il profilo `<nome>` non ha CONST.json. Eseguire `bash claude-flow/scripts/migrate-profile-split.sh --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`" | Stop |
| PROFILE.json manca, CONST.json esiste | "Il profilo `<nome>` non ha PROFILE.json. Stato inconsistente — il profilo è incompleto. Ripristinare da git history o rifare il setup." | Stop |
| Entrambi mancano, esiste profile.json (legacy) | "Profilo in formato vecchio (pre-split CONST/PROFILE). Eseguire `bash claude-flow/scripts/migrate-profile-split.sh --apply` per fare lo split automaticamente" | Stop |
| JSON malformed | Mostra errore di parse + path | Stop |

### 7.5 Volume del refactor sulle skill

| Skill | Cambio | Note |
|---|---|---|
| sdlc-profile-setup | **Strutturale** | Step 8 raddoppiato (genera CONST + PROFILE), template precompilato, conferma a due step |
| sdlc-analyzer | **Strutturale** | Loader nuovo, auto-update SOLO su PROFILE, nuova sezione "Violazioni principi" in PLAN.md |
| sdlc-reviewer | Solo loader | Aggiunge sezione "Caricamento contesto" |
| sdlc-clarify | Solo loader | Idem |
| sdlc-executor | Solo loader | Idem |
| sdlc-debug | Solo loader | Idem (rimuove l'unico riferimento esistente a `constitution/profile.json` linea 75) |
| sdlc-updater | Solo loader | Idem |
| sdlc-estimator | Solo loader | Idem |
| sdlc-progress-report | Solo loader | Idem |

## 8. Schema JSON proposti

### 8.1 `const-schema.json` (nuovo)

Schema completo (Draft 2020-12) per `CONST.json`. Tutte le 5 macro-sezioni sono `additionalProperties: false` ma OPZIONALI a livello root (un progetto può avere CONST minimale).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/deloitte/deloitte-profiles/const-schema.json",
  "title": "Deloitte Project Constitution — Archetypal Principles",
  "description": "Schema for CONST.json. Contains principles, quality standards, code style, git workflow, and architectural patterns. Read by all SDLC skills as inviolable constraints on every generated output.",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "$schema": { "type": "string" },
    "inviolable_principles": {
      "type": "object",
      "description": "Non-negotiable rules every output must respect",
      "additionalProperties": true,
      "properties": {
        "security": { "$ref": "#/$defs/principle" },
        "accessibility": { "$ref": "#/$defs/principle" },
        "responsiveness": { "$ref": "#/$defs/principle" },
        "data_privacy": { "$ref": "#/$defs/principle" }
      }
    },
    "quality_standards": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "test_coverage": {
          "type": "object",
          "properties": {
            "minimum_percent": { "type": "integer", "minimum": 0, "maximum": 100 },
            "applies_to": { "type": "array", "items": { "type": "string" } }
          }
        },
        "error_handling": { "type": "string" },
        "logging": {
          "type": "object",
          "properties": {
            "format": { "type": "string" },
            "never_log": { "type": "array", "items": { "type": "string" } }
          }
        },
        "performance": { "type": "object", "additionalProperties": true }
      }
    },
    "code_style": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "max_function_lines": { "type": "integer", "minimum": 1 },
        "max_file_lines": { "type": "integer", "minimum": 1 },
        "max_nesting_depth": { "type": "integer", "minimum": 1 },
        "no_magic_numbers": { "type": "boolean" },
        "no_debug_statements_in_prod": { "type": "boolean" }
      }
    },
    "git_workflow": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "branch_pattern": { "type": "string" },
        "commit_convention": { "type": "string" }
      }
    },
    "architectural_patterns": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "layered_separation": { "type": "string" },
        "api_response_envelope": { "type": "string" },
        "test_pattern": { "type": "string" },
        "input_validation": { "type": "string" }
      }
    }
  },
  "$defs": {
    "principle": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "rule": { "type": "string" },
        "scope": { "type": "string" },
        "verification": { "type": "string" },
        "requirements": { "type": "array", "items": { "type": "string" } },
        "breakpoints": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["rule"]
    }
  }
}
```

### 8.2 `profile-schema.json` (modificato)

**Unica modifica:** rimuovere la sezione `inviolable_principles` da `conventions.properties` (oggi è descritta implicitamente come `additionalProperties: true`, quindi tecnicamente non c'è da rimuovere nulla — basta documentare nel README che `inviolable_principles` non va più in `conventions`).

Aggiornamento al `description` di `conventions`:
> Project coding conventions and structural patterns. **Note:** `inviolable_principles` is no longer accepted here — moved to `CONST.json`.

## 9. Script di migrazione — `migrate-profile-split.sh`

**Path:** `claude-flow/scripts/migrate-profile-split.sh`
**Stile:** segue il pattern di `migrate-sdlc-naming.sh` (bash, dry-run default, `--apply` per eseguire, `--root` per override).

### 9.1 Cosa fa

Per ogni `<progetto>/constitution/profile.json` trovato sotto `--root` (default `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles`):

1. Legge `profile.json`.
2. Estrae `conventions.inviolable_principles` se presente, trasformandolo nello shape nuovo di CONST. Lo script preserva la stringa originale nel campo `rule` e popola gli altri campi del nuovo schema (`scope`, `verification`, `requirements`, `breakpoints`) coi valori di default del template. Nessuna estrazione "semantica" dalla stringa originale — la riconciliazione fine è lasciata all'utente in revisione manuale post-migrazione:
   - `security` (string) → `{ "rule": "<string originale>", "scope": "<default>", "verification": "<default>" }`
   - `accessibility` (string) → `{ "rule": "<string originale>", "requirements": ["navigabile da tastiera", "compatibile screen reader", "contrasto AA", "attributi ARIA corretti"] }`
   - `responsiveness` (string) → `{ "rule": "<string originale>", "breakpoints": ["mobile", "tablet", "desktop"] }`
3. Aggiunge le sezioni mancanti del template di default (`quality_standards`, `code_style`, `git_workflow`, `architectural_patterns`, e `data_privacy` se non presente in `inviolable_principles`) con valori di default.
4. Scrive `<progetto>/constitution/CONST.json`.
5. Rimuove `conventions.inviolable_principles` da profile.json.
6. `git mv profile.json PROFILE.json`.
7. NON committa né pusha automaticamente. Mostra il comando di commit suggerito.
8. Al termine, stampa un reminder: "Rivedi a mano il CONST.json appena generato — le stringhe originali sono state preservate nei campi `rule`, ma campi come `scope`/`requirements`/`breakpoints` sono valori di default e potrebbero non riflettere esattamente la policy originale."

### 9.2 Output esempio (dry-run)

```
[DRY-RUN] Scansiono C:/.../deloitte-profiles/*/constitution/profile.json
[DRY-RUN]
[DRY-RUN] banca-agente/constitution/
[DRY-RUN]   read  profile.json (14316 bytes)
[DRY-RUN]   extract conventions.inviolable_principles → CONST.inviolable_principles (3 principi: security, accessibility, responsiveness)
[DRY-RUN]   add default sections: quality_standards, code_style, git_workflow, architectural_patterns, data_privacy
[DRY-RUN]   write CONST.json (~2.5 KB)
[DRY-RUN]   remove conventions.inviolable_principles from profile.json
[DRY-RUN]   git mv profile.json PROFILE.json
[DRY-RUN]
[DRY-RUN] Summary: 1 profilo, 1 da migrare, 0 errori.
[DRY-RUN]
[DRY-RUN] Run with --apply to execute.
[DRY-RUN]
[DRY-RUN] Suggested commit after apply:
[DRY-RUN]   git -C deloitte-profiles add -A
[DRY-RUN]   git -C deloitte-profiles commit -m "refactor: split profile.json into CONST.json + PROFILE.json"
[DRY-RUN]   git -C deloitte-profiles push origin main
```

### 9.3 Considerazioni implementative

- Lo script userà `jq` per parsare/manipolare JSON (assumibile presente su Windows con git-bash o WSL). Se `jq` non è disponibile, fallback su uno script Python `migrate-profile-split.py`.
- **Idempotenza:** se `CONST.json` e `PROFILE.json` già esistono e `profile.json` non c'è, lo script skippa quel progetto con messaggio "già migrato".
- **Safety:** lo script verifica che il `<profiles_repo>` sia un working tree git pulito prima di applicare. Se ci sono modifiche unstaged, errore e stop.

## 10. Sync delle skill installate localmente

Lo script `sync-installed.sh` esiste già e gestisce sia skill (`~/.claude/skills/sdlc-*`) sia agenti (`~/.claude/agents/sdlc-*.md`).

Dopo aver aggiornato le 9 SKILL.md nel repo `claude-flow`, basterà:

```bash
bash scripts/sync-installed.sh --apply
```

Non serve modificare lo script di sync.

## 11. Strategia di rollout (big bang)

| # | Azione | Repo |
|---|---|---|
| 1 | Crea `const-schema.json`, aggiorna `profile-schema.json` description | deloitte-profiles |
| 2 | Aggiorna `README.md` di deloitte-profiles (struttura CONST + PROFILE, sezione "Profile Sections" → "Constitution Files") | deloitte-profiles |
| 3 | Scrivi `scripts/migrate-profile-split.sh` (con dry-run) | claude-flow |
| 4 | Refactora 9 SKILL.md (aggiungi sezione "Caricamento contesto progetto") | claude-flow |
| 5 | Refactora `sdlc-profile-setup` (Step 8 raddoppiato, template precompilato, conferma a due step) | claude-flow |
| 6 | Refactora `sdlc-analyzer` (auto-update solo PROFILE, nuova sezione "Violazioni principi" in PLAN.md template) | claude-flow |
| 7 | Aggiorna `SDLC_SKILLS_DOCUMENTATION.md` (sezione "Profilo" → "CONST + PROFILE", glossario aggiornato) | claude-flow |
| 8 | **Dry-run** della migrazione: `bash scripts/migrate-profile-split.sh` | locale |
| 9 | **Apply** della migrazione: `bash scripts/migrate-profile-split.sh --apply` | locale → deloitte-profiles working tree |
| 10 | Verifica manuale `banca-agente/constitution/` ha CONST.json + PROFILE.json, profile.json sparito | locale |
| 11 | Commit + push deloitte-profiles | deloitte-profiles |
| 12 | Commit + push claude-flow | claude-flow |
| 13 | **Sync** skill locali: `bash scripts/sync-installed.sh --apply` | locale ~/.claude/ |
| 14 | Smoke test: invoca `/sdlc-progress-report` o `/sdlc-reviewer` per verificare che CONST+PROFILE vengano caricati senza errori | locale |

## 12. Rollback strategy

Entrambi i commit (claude-flow + deloitte-profiles) sono atomici e indipendenti dallo stato dei BR esistenti (le folder `plans/todo|in-progress|done/` non vengono toccate).

In caso di fallimento dello step 14 (smoke test):

1. `git -C deloitte-profiles revert HEAD` → ripristina profile.json
2. `git -C claude-flow revert HEAD` → ripristina le SKILL.md vecchie
3. `bash claude-flow/scripts/sync-installed.sh --apply` → re-sync skill locali alla versione precedente
4. Stato locale: come pre-refactor, niente perdite.

## 13. Data flow (end-to-end)

```
User invoca /sdlc-<skill>
        ↓
Skill esegue "Risoluzione Path"  →  estrae profiles_repo, profilo da .br-local.json
        ↓
Skill esegue "Caricamento contesto progetto"
        ↓
  git pull deloitte-profiles
        ↓
  Read CONST.json  →  contesto "vincoli"
  Read PROFILE.json  →  contesto "dati progetto"
        ↓
Skill esegue il suo body
        ↓
Output generato (PLAN/TASKS/CLARIFY/REVIEW/fix/...)
        ↓
Output rispetta CONST + usa PROFILE come "lingua"
        ↓
Commit nell'eventuale repo target (codice progetto / deloitte-profiles)
```

## 14. Error handling

Tutti i casi di errore del loader (Sezione 7.4) producono un messaggio esplicito + stop della skill. Mai procedere con contesto parziale. Una skill SDLC senza CONST è privata dei vincoli di policy → output potenzialmente non compliant → meglio fermare.

## 15. Testing strategy

- **Dry-run migrazione** (step 8 del rollout) — verifica che lo script identifichi correttamente i campi da splittare e non perda dati.
- **Smoke test post-rollout** (step 14) — invocazione manuale di 2-3 skill su un BR esistente (banca-agente ha BR in `plans/done/`) per verificare che il loader funzioni e l'output rispetti i principi.
- **Validazione schema** — al primo loading post-migrazione, ogni skill valida CONST.json e PROFILE.json contro i rispettivi schemi (`ajv` o validator equivalente). Se la validazione fallisce, errore esplicito col path del campo invalido.
- **Test di idempotenza dello script di migrazione** — eseguirlo due volte deve essere no-op (skippato con messaggio "già migrato").

## 16. Out of scope (non-goals)

- **Migrazione di profili che non esistono ancora.** Solo `banca-agente` è in scope (è l'unico profilo presente).
- **Refactor del file `.br-local.json`.** Rimane invariato.
- **Refactor degli agenti `<profilo>/agents/*.md`.** Non toccati.
- **Modifica del lifecycle dei BR (`todo/in-progress/done`).** Invariato.
- **Aggiunta di CONST condivisi tra progetti.** Esclusa esplicitamente dalla scelta utente (vedi Decisione "Sharing tra progetti" in Sezione 3). Se in futuro servisse un CONST condiviso (es. "tutti i progetti web Deloitte"), sarà un design separato.
- **Validazione runtime dei principi CONST sul codice esistente.** Lo script di migrazione non esegue verifiche di compliance del codice. La nuova sezione "Violazioni principi" in `sdlc-analyzer` farà finding-mode, non blocking-mode.

## 17. Riferimenti

- Profilo attuale: `deloitte-profiles/banca-agente/constitution/profile.json`
- Schema attuale: `deloitte-profiles/profile-schema.json`
- Pattern script: `claude-flow/scripts/migrate-sdlc-naming.sh`, `claude-flow/scripts/sync-installed.sh`
- Documentazione skill SDLC: `claude-flow/SDLC_SKILLS_DOCUMENTATION.md`
- Spec correlato: `docs/superpowers/specs/2026-05-11-br-agents-profiles-design.md` (introdusse il concetto di profilo)
- Spec correlato: `docs/superpowers/specs/2026-05-18-br-skills-centralization-design.md` (centralizzò gli artefatti in deloitte-profiles)
