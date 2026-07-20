---
name: sdlc-profile-setup
description: Crea un nuovo profilo progetto in deloitte-profiles con auto-detect del codebase, domande guidate su dominio e design system, e configurazione automatica di .sdlc-local.json (con fallback compatibile a .br-local.json per profili legacy). Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill SDLC.
---

# SDLC Profile Setup — Creazione Guidata Profilo Progetto

> **Nota su CONST + PROFILE:** Questa skill è l'**eccezione** al loader standard delle skill SDLC: NON carica CONST + PROFILE all'avvio (li sta creando). Tutte le altre 8 skill (`sdlc-analyzer`, `sdlc-reviewer`, `sdlc-clarify`, `sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-estimator`, `sdlc-progress-report`) caricano CONST + PROFILE dopo la "Risoluzione Path".
>
> Output di questa skill: **due file** nella folder `constitution/` del progetto:
> - `CONST.json` — principi/standard di archetipo (template precompilato di default, adattato in base al codebase)
> - `PROFILE.json` — dettagli specifici del progetto (tech stack, dominio, design system)

Questa skill guida la creazione di un nuovo profilo progetto in **modalita' duale**: **standalone** (una repo Git per progetto, raccomandato per nuovi progetti, con cartella `dataset/` Solaria-side) oppure **legacy** (centralizzata in `deloitte-profiles/`). Il profilo contiene tech stack, convenzioni, dominio e design system utilizzati da tutte le skill SDLC. Il flusso e' composto da step sequenziali: una domanda alla volta, con auto-detect del codebase prima delle domande manuali.

---

## Step 1 — Nome progetto

Chiedi il nome del progetto. Diventa il nome della cartella nel profilo (in legacy) o del progetto (in standalone).

> Come vuoi chiamare questo progetto? Il nome verra' usato come slug del progetto (kebab-case).
>
> Esempio: "pnrr", "ecomotive", "isp-banking", "banca-agente"

Salva il nome fornito. Usa kebab-case se l'utente fornisce un nome con spazi.

---

## Step 1.5 — Scelta modalita' (standalone | legacy)

Chiedi la modalita' di setup:

> Vuoi configurare in **modalita' standalone** (raccomandato per nuovi progetti) o **modalita' legacy**?
>
> - **Standalone**: una repo Git dedicata al progetto (es. `banca-agente`), con cartella `dataset/` popolata da Solaria-side (branding, glossario, attori, perimetro), `constitution/`, `references/`, `plans/{draft,todo,in-progress,done}/`. La repo va creata su GitHub e clonata in locale prima di lanciare questa skill (NON la creo io: assume `git rev-parse` valido sul path).
> - **Legacy**: il profilo viene aggiunto come cartella in `deloitte-profiles/<nome>/`, con `constitution/`, `references/`, `agents/`, `plans/{todo,in-progress,done}/` (senza `dataset/` ne' `draft/`). Modalita' storica, per progetti gia' avviati o che convivono in `deloitte-profiles`.
>
> Scegli (default raccomandato per nuovi progetti: standalone):

Salva la scelta come `MODE` (`standalone` o `legacy`). Tutto il flusso a seguire si biforca su questa scelta.

---

## Modalità di orchestrazione

Ogni skill SDLC può girare in due modalità:

- **`classic`** (default) — esecuzione sequenziale, leggera, pochi token. È il comportamento storico.
- **`deep`** — orchestrazione parallela multi-agent (Workflow tool) + verifica adversariale: più lenta e costosa, ma più esaustiva.

> **Mai escalation silenziosa.** Non si passa a `deep` (con la relativa spesa) senza una scelta esplicita — flag persistente o conferma dell'utente. Default globale = `classic`.

### Risoluzione della modalità (cascata, in ordine di precedenza)

1. **Flag persistente** in `.sdlc-local.json` (fallback `.br-local.json`) — la sorgente automatica a precedenza più alta. Campi *flat* (grep-compatibili, niente `jq`):

   ```bash
   LOCAL_CFG=".sdlc-local.json"; [ -f "$LOCAL_CFG" ] || LOCAL_CFG=".br-local.json"
   ORCH_MODE=$(grep -oP '"orchestration_mode"\s*:\s*"\K[^"]+' "$LOCAL_CFG" 2>/dev/null);  ORCH_MODE=${ORCH_MODE:-classic}
   ORCH_DEPTH=$(grep -oP '"orchestration_depth"\s*:\s*"\K[^"]+' "$LOCAL_CFG" 2>/dev/null); ORCH_DEPTH=${ORCH_DEPTH:-standard}
   ORCH_MAXC=$(grep -oP '"orchestration_max_concurrency"\s*:\s*\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_MAXC=${ORCH_MAXC:-10}
   ORCH_PANEL=$(grep -oP '"orchestration_verifier_panel"\s*:\s*\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_PANEL=${ORCH_PANEL:-3}
   ```

2. **Keyword nel trigger** ("a fondo", "esaustivo", "in parallelo", "ultracode") — override per singola invocazione, ma **declassata sotto il flag**: una scelta `classic` deliberata nel flag NON viene scavalcata da una keyword ambigua. Ogni escalation verso `deep` innescata da keyword **passa da conferma esplicita** (AskUserQuestion) prima di spendere.

3. **AskUserQuestion** quando né flag né keyword hanno deciso. Con **auto-suggeritore**: se la dimensione del lavoro supera una soglia (≥3 repo, ≥25 task, ondata ≥8 bug, changelog AFU ampio) proponi `deep` mostrando il razionale, **ma la pre-selezione resta `classic`** (no spesa a sorpresa).

**`/effort ultracode` di sessione**: se attivo a livello sessione, la **prima** skill SDLC invocata chiede **una volta** se applicare `deep` a tutte le skill SDLC della sessione, poi ricorda la risposta.

### Banner di modalità (sempre a video prima del lavoro pesante)

- `deep`:  *"Eseguo in modalità Workflow+approfondita: ~N agent, più lento/costoso."*
- `classic`: *"Modalità classica (sequenziale)."*

### Esecuzione `deep` — invocazione del Workflow tool

In `deep`, la skill **istruisce Claude a invocare il Workflow tool**: con lo script dedicato in `workflows/` per le skill *heavy* (`sdlc-analyzer`, `sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-reviewer` — vero fan-out + `adversarial-verify` + `completeness-critic` + `isolation:'worktree'`), oppure con un singolo sub-step di `completeness/coherence-critic` per le skill *light* (`sdlc-estimator`, `sdlc-clarify`, `sdlc-progress-report`, `sdlc-profile-setup`). Gli schema JSON vivono **negli script `workflows/*.js`**, non qui.

### Capability check + degradazione (assume-disponibile + fallback esplicito)

**Nessun probe preventivo**: procedi assumendo il Workflow tool presente. Se l'invocazione **non è possibile** (tool assente) **oppure fallisce/non completa**:

1. banner a video: *"Workflow tool non disponibile: eseguo in modalità classica sequenziale."*;
2. prosegui nel ramo `classic` usando la mappa di fallback sotto;
3. inserisci in testa all'artefatto prodotto (PLAN/CLARIFY/gap report/...) il banner **"COPERTURA RIDOTTA — prodotto senza completeness-critic/adversarial-verify"**. La degradazione è **rumorosa**, mai silenziosa: gli artefatti `classic` e `deep` NON sono equivalenti.

> Due casi distinti: (a) **Workflow tool assente / non parte** → fallback completo a `classic` (sopra). (b) **Barriera parziale** (il workflow parte ma k/N agent falliscono) → lo script ritorna i k riusciti come *proposte non applicate*; i file source-of-truth NON vengono scritti parzialmente; l'agente principale presenta lo stato e l'utente decide.

### Mappa di fallback `deep` → `classic`

| Primitiva `deep` | Fallback `classic` |
|---|---|
| `parallel` / `pipeline` | loop sequenziale sugli stessi thunk (comportamento attuale) |
| `agent({agentType, schema})` | "leggi `${CLAUDE_PLUGIN_ROOT}/agents/<agentType>.md` e lancia un Task" + parsing MD |
| `adversarial-verify` / `judge-panel` | singola verifica `sdlc-verifier` inline |
| `completeness-critic` | checklist manuale già presente nella skill |
| `loop-until-dry` | ciclo fix/riverifica già descritto |

### Invarianti inviolabili (in ENTRAMBE le modalità)

1. Tutti i gate di conferma utente ("mai procedere senza conferma").
2. Mai auto-commit sulle repo di **codice**.
3. Il sottoagente implementa, l'agente principale coordina.
4. Scritture sui file source-of-truth (PROGRESS, BUG_REPORT, CLARIFY, PLAN/TASKS) sempre **single-writer serializzato** (pull→edit→commit→push).
5. Gli agent di verifica/esplorazione restano **read-only**.
6. Barriere obbligatorie dove la fase a valle richiede lo stato completo (prima della gap-synthesis, tra wave, prima della presentazione unica dell'auto-detect).

> **Nota per `sdlc-profile-setup` (eccezione §7.6):** questa skill **crea** `.sdlc-local.json`, non lo legge a monte come le altre. La modalità si risolve qui, dopo lo Step MODE: se un `.sdlc-local.json` (o `.br-local.json` legacy) esiste già nel codebase usa il suo `orchestration_mode`; altrimenti chiedi via AskUserQuestion (default `classic`). In `deep` il valore aggiunto è confinato a: auto-detect multi-repo con explorer + `completeness-critic` sul PROFILE prima della conferma (un PROFILE errato viene ereditato da tutte le altre 8 skill).

---

## Step 2 — Path repo

In base a `MODE`:

**Se `MODE=standalone`**:

> Qual e' il path locale del tuo clone della repo del progetto `<nome>`?
>
> Esempio: `C:/Users/davmelis/Documents/MyGitHub/<nome>`
>
> NB: la repo deve esistere su GitHub e essere gia' clonata (e inizializzata) — io NON eseguo `git init`, popolo solo i contents.

Dopo la risposta:

```bash
git -C "<path>" rev-parse --is-inside-work-tree 2>/dev/null && echo "OK: git repo" || echo "ERRORE: non e' un repo git"
```

Salva il path come `PROJECT_REPO`. Se il repo non e' valido, segnala e chiedi di riprovare.

**Se `MODE=legacy`**:

> Qual e' il path locale del tuo clone di `deloitte-profiles`?
>
> Esempio: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles`

Dopo la risposta, verifica che sia un repo git valido e che contenga lo schema:

```bash
git -C "<path>" rev-parse --is-inside-work-tree 2>/dev/null && echo "OK: git repo" || echo "ERRORE: non e' un repo git"
ls "<path>/profile-schema.json" 2>/dev/null && echo "OK: schema trovato" || echo "WARNING: profile-schema.json non trovato"
```

Salva il path come `PROFILES_REPO`. Se il repo non e' valido, segnala e chiedi di riprovare. Se lo schema non c'e', avvisa ma procedi (verra' creato se necessario).

---

## Step 3 — Codebase

Chiedi tutte le repository del progetto.

> Quali sono le repository/codebase di questo progetto?
> Per ognuna, dammi:
> - **Nome** (es. "back-end", "front-end", "api-gateway")
> - **Sigla** (abbreviazione breve, es. "BE", "FE", "GW")
> - **Path locale** (il path al codebase sulla tua macchina)
>
> Esempio:
> - Back-end (BE) -> `C:/progetti/myapp-backend`
> - Front-end (FE) -> `C:/progetti/myapp-frontend`

Salva nome, sigla e path per ogni repository.

---

## Step 4 — Auto-detect

Per ogni codebase fornito nello Step 3, esplora automaticamente per rilevare tech stack, convenzioni e design system. Non chiedere nulla all'utente in questo step — lavora in silenzio e mostra i risultati nello Step 5.

### 4.1 — Backend detection

Rileva il framework backend dai file di build:

| File trovato | Stack rilevato |
|---|---|
| `pom.xml` con `spring-boot` | Spring Boot (Java/Kotlin) |
| `build.gradle` con `spring-boot` | Spring Boot (Gradle) |
| `*.csproj` o `*.sln` | .NET (C#) |
| `requirements.txt` o `pyproject.toml` | Python (Django/FastAPI/Flask — leggi il file per distinguere) |
| `package.json` con `express` o `nestjs` o `fastify` | Node.js (leggi dipendenze per framework) |
| `composer.json` | PHP (Laravel/Symfony — leggi il file per distinguere) |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

Per ogni detection, approfondisci:
- Versione del framework (dal file di build)
- Database usato (da connection string in properties/config, o da dipendenze ORM)
- ORM/Data layer (Hibernate, Entity Framework, SQLAlchemy, Prisma, GORM, ecc.)

### 4.2 — Frontend detection

Rileva il framework frontend:

| File trovato | Stack rilevato |
|---|---|
| `angular.json` | Angular (leggi versione) |
| `package.json` con `react` | React (controlla anche Next.js, Vite, CRA) |
| `package.json` con `vue` | Vue (controlla anche Nuxt) |
| `package.json` con `svelte` | Svelte/SvelteKit |
| `pubspec.yaml` con `flutter` | Flutter/Dart |

### 4.3 — Convenzioni

Rileva le convenzioni analizzando la struttura del codice:

**Package/directory structure**: lista i package/directory principali del progetto per capire l'organizzazione (layered, feature-based, ecc.)

**Base entity classes**: cerca classi base come `BaseEntity`, `AuditableEntity`, `AbstractEntity` per capire il pattern di ereditarieta' delle entita'.

```bash
# Esempio per Java/Kotlin
grep -rl "class Base\|abstract class.*Entity\|@MappedSuperclass" "<path>/src" --include="*.java" --include="*.kt" | head -5
```

**API prefix**: leggi 2-3 controller per trovare il pattern dei path (es. `/api/v1/`, `/api/`, nessun prefix).

```bash
# Esempio per Spring Boot
grep -rh "@RequestMapping\|@GetMapping\|@PostMapping" "<path>/src" --include="*.java" --include="*.kt" | head -10
```

**Test framework**: rileva dai file di build (JUnit, pytest, Jest, Vitest, xUnit, ecc.)

**Test naming convention**: leggi 2-3 file di test per capire il pattern di naming (should_xxx_when_yyy, givenXxx_whenYyy_thenZzz, test_xxx, ecc.)

```bash
# Trova file di test
find "<path>" -name "*Test*" -o -name "*test*" -o -name "*.spec.*" | head -5
```

### 4.4 — Design system (solo frontend)

Per codebase frontend, rileva:

**Colori**: cerca variabili CSS/SCSS con colori.

```bash
grep -rh "\-\-color\|--primary\|\$color\|\$primary" "<path>/src" --include="*.css" --include="*.scss" --include="*.less" | head -20
```

**Font**: cerca font-family declarations.

```bash
grep -rh "font-family" "<path>/src" --include="*.css" --include="*.scss" | head -5
```

**Spacing scale**: cerca variabili di spacing.

```bash
grep -rh "\-\-spacing\|\-\-space\|\$spacing" "<path>/src" --include="*.css" --include="*.scss" | head -10
```

**UI library**: cerca nel package.json librerie UI note (PrimeNG, Angular Material, MUI, Ant Design, Tailwind, Bootstrap, Chakra, shadcn/ui, ecc.)

```bash
cat "<path>/package.json" | grep -i "primeng\|angular.*material\|@mui\|antd\|tailwind\|bootstrap\|chakra\|radix\|shadcn"
```

---

## Step 5 — Presenta e conferma

Presenta tutto quello che hai rilevato in formato strutturato. Per ogni codebase:

> ## Auto-detect completato
>
> ### BE — Back-end (`C:/progetti/myapp-backend`)
> - **Framework**: Spring Boot 3.2.1 (Java 17)
> - **Database**: PostgreSQL (rilevato da `application.yml`)
> - **ORM**: Hibernate/JPA
> - **Package structure**: layered (`controller/`, `service/`, `repository/`, `model/`, `dto/`)
> - **Base entity**: `BaseEntity` con `id`, `createdAt`, `updatedAt` (`com.myapp.model.BaseEntity`)
> - **API prefix**: `/api/v1/`
> - **Test framework**: JUnit 5 + Mockito
> - **Test naming**: `should_xxx_when_yyy` (es. `should_returnBooking_when_validId`)
>
> ### FE — Front-end (`C:/progetti/myapp-frontend`)
> - **Framework**: Angular 17
> - **UI library**: PrimeNG 17.3
> - **CSS**: SCSS con variabili custom
> - **Colori primari**: `--primary: #2196F3`, `--accent: #FF4081`
> - **Font**: `'Inter', sans-serif`
> - **Package structure**: feature-based (`features/booking/`, `features/dashboard/`)
> - **Test framework**: Jest + Testing Library
>
> E' tutto corretto? Ci sono correzioni o integrazioni?

Aspetta la risposta. Se l'utente corregge qualcosa, aggiorna i dati.

---

## Step 6 — Dominio

Chiedi informazioni non deducibili dal codice. Ognuna e' opzionale — l'utente puo' saltare.

> Ora alcune domande sul dominio di business. Puoi saltare quelle che non ritieni necessarie.
>
> **1. Glossario** — Ci sono termini di business specifici che il team usa? Elenca termine e definizione.
> Esempio: "Pratica = istanza di una richiesta di finanziamento", "Lotto = raggruppamento di pratiche per la validazione"
>
> **2. Regole di business principali** — Ci sono regole di business fondamentali che ogni sviluppatore deve conoscere?
> Esempio: "Una pratica non puo' passare a stato APPROVATA senza validazione del responsabile", "L'importo massimo per singola pratica e' 500k EUR"
>
> **3. Stati delle entita' principali** — Quali sono le entita' centrali e i loro stati? (se rilevante)
> Esempio: "Pratica: BOZZA -> INVIATA -> IN_VALUTAZIONE -> APPROVATA/RESPINTA -> CHIUSA"

Per ogni risposta, salva i dati forniti. Se l'utente dice "salta" o "non serve", procedi senza.

---

## Step 7 — Reference files

Chiedi per file di riferimento opzionali.

> Hai file di riferimento da includere nel profilo? Sono tutti opzionali:
>
> - **Screenshot design system** — screenshot della UI esistente che mostrino look & feel
> - **Codice gold-standard** — file di esempio che rappresentino le convenzioni "perfette" del progetto
> - **Template specifici** — template per controller, servizi, componenti, ecc.
>
> Per ognuno, dammi il path del file. Verranno copiati nella cartella `references/` del profilo.

Se l'utente fornisce file, copiali:

```bash
mkdir -p "<profiles_repo>/<nome>/references"
cp "<file>" "<profiles_repo>/<nome>/references/"
```

Se l'utente dice "nessuno" o "salta", procedi senza.

---

## Step 8 — Genera CONST.json + PROFILE.json

In questo step generi DUE file separati: un `CONST.json` (principi/standard di archetipo, template precompilato) e un `PROFILE.json` (dettagli specifici progetto).

### 8.1 — Genera CONST.json dal template precompilato

Leggi il template precompilato:

```bash
cat "<path-al-repo-claude-flow>/skills/sdlc-profile-setup/_const-template.json"
```

Adatta il template in base ai codebase rilevati negli Step 3-5:

| Condizione | Modifica al template |
|---|---|
| Nessun codebase frontend rilevato | Rimuovi `inviolable_principles.accessibility` e `inviolable_principles.responsiveness` |
| Nessuna API REST rilevata | Rimuovi `architectural_patterns.api_response_envelope` |
| Nessun database con dati personali | Mantieni `data_privacy` come default conservativo (l'utente può rimuoverlo dopo) |

Presenta il CONST.json risultante:

> Ecco il **CONST.json** generato (template di default adattato al tuo codebase):
>
> ```json
> [JSON completo]
> ```
>
> Va bene così o vuoi modificare qualche principio prima di scrivere il file? (es. cambiare la soglia di test coverage, aggiungere un principio personalizzato, rimuovere uno dei default)

Aspetta la risposta. Se l'utente vuole modifiche, applicale e ripresenta il JSON. Solo dopo OK procedi.

### 8.2 — Genera PROFILE.json dai dati raccolti negli Step 1-7

Assembla i dati raccolti negli Step 1-7 in `PROFILE.json` (struttura come da `profile-schema.json`). Include solo le sezioni con dati reali — ometti campi vuoti o sezioni saltate.

**In `deep`** (cerchio *light*, vedi "## Modalità di orchestrazione" e l'eccezione §7.6): nessun workflow pesante. Due sub-step leggeri: (1) auto-detect multi-repo più approfondito con explorer `sdlc-codebase-explorer` in "modalità senza profilo" sui codebase dello Step 3; (2) un **completeness-critic** sul PROFILE **prima della conferma** — un PROFILE errato viene ereditato da TUTTE le altre 8 skill, quindi vale una verifica scettica (campi stack/convenzioni/dominio coerenti col codice rilevato?). Banner **COPERTURA RIDOTTA** se degradi a `classic`.

Struttura del JSON:

```json
{
  "$schema": "../../profile-schema.json",
  "project": {
    "name": "<nome>",
    "client": "<client>",
    "description": "<description>"
  },
  "tech_stack": { },
  "conventions": { },
  "design_system": { },
  "domain": { },
  "custom_agents": [],
  "progress_report_template": { "mode": "official", "path": null, "confirmed_at": null, "confirmed_by": null }
}
```

**`progress_report_template` (report Excel — #6):** governa quale layout usa `sdlc-progress-report`.

| Campo | Default | Significato |
|---|---|---|
| `mode` | `"official"` | `official` (layout canonico) \| `custom` (manifest fornito dal TL). Con `custom` l'ufficiale **non** è mai consultato. |
| `path` | `null` | Path **repo-relative** del manifest JSON custom nella repo di progetto (es. `constitution/progress-report-manifest.json`); `null` per `official`. |
| `confirmed_at` | `null` | Data ISO di conferma del template custom. |
| `confirmed_by` | `null` | Chi (TL) ha confermato il template custom. |

Per un profilo nuovo scrivi sempre `mode:"official"`. L'ingest di un template custom avviene **on-demand** dentro `sdlc-progress-report` (non qui): quella skill analizza l'`.xlsx` del TL in un manifest e aggiorna questo campo. **Preserva** su re-run del setup un `progress_report_template` già presente con `mode:"custom"` (come per `orchestration_*` e `interaction_language`).

**NOTA IMPORTANTE:** in `conventions` NON inserire più `inviolable_principles` — quei dati ora vivono in `CONST.json`.

Presenta `PROFILE.json` all'utente:

> Ecco il **PROFILE.json** generato per **<nome>**:
>
> ```json
> [JSON completo]
> ```
>
> Confermo e scrivo i due file?

Aspetta la risposta finale.

### 8.3 — Scrivi entrambi i file e crea la struttura

Dopo conferma, scrivi i file e crea la struttura cartelle. La struttura cambia in base a `MODE`:

**Se `MODE=standalone`** (project_repo dedicata):

```bash
PROJECT_REPO_ROOT="<path-da-Step-2>"

mkdir -p "$PROJECT_REPO_ROOT/constitution"
mkdir -p "$PROJECT_REPO_ROOT/references"
mkdir -p "$PROJECT_REPO_ROOT/agents"
mkdir -p "$PROJECT_REPO_ROOT/dataset/branding"            # NUOVA — popolata da Solaria in F1b
mkdir -p "$PROJECT_REPO_ROOT/dataset/corporate"           # NUOVA — popolata da Solaria in F1b
mkdir -p "$PROJECT_REPO_ROOT/plans/draft"                 # NUOVA — area Solaria F1c
mkdir -p "$PROJECT_REPO_ROOT/plans/todo"
mkdir -p "$PROJECT_REPO_ROOT/plans/in-progress"
mkdir -p "$PROJECT_REPO_ROOT/plans/done"

# Scrivi CONST.json (8.1) e PROFILE.json (8.2) in $PROJECT_REPO_ROOT/constitution/
# Copia afu-manifest.schema.json v2 dal template canonico alla root del project_repo
cp "<path-claude-flow>/templates/afu-manifest.schema.json" "$PROJECT_REPO_ROOT/afu-manifest.schema.json"

# Scrivi template iniziali in dataset/ (vuoti con header, popolati da Solaria F1b)
cat > "$PROJECT_REPO_ROOT/dataset/README.md" <<'EOF'
# Dataset Solaria

Cartella popolata e mantenuta da Solaria-side (vedi Fase 1b di Fasi-New-way-of-working.md).
NON modificare da Claude Code — e' read-only per il team tech.
Solaria committa via GitHub API (commit message [solaria-dataset-*]).

## Struttura

- branding/      — logo, palette, font, brand book
- corporate/     — template documenti, presentazioni corporate
- glossario.md   — termini di dominio
- attori.md      — ruoli, personas, sistemi esterni
- perimetro.md   — scope progetto, esclusioni
EOF
cat > "$PROJECT_REPO_ROOT/dataset/glossario.md" <<'EOF'
# Glossario di dominio

<!-- Popolato da Solaria in F1b a partire dal materiale fornito dal funzionale. -->
EOF
cat > "$PROJECT_REPO_ROOT/dataset/attori.md" <<'EOF'
# Attori

<!-- Popolato da Solaria in F1b. Lista di ruoli, personas, sistemi esterni. -->
EOF
cat > "$PROJECT_REPO_ROOT/dataset/perimetro.md" <<'EOF'
# Perimetro funzionale

<!-- Popolato da Solaria in F1b. Scope del progetto + esclusioni esplicite. -->
EOF
```

**Se `MODE=legacy`** (centralizzata in deloitte-profiles):

```bash
mkdir -p "<profiles_repo>/<nome>/constitution"
mkdir -p "<profiles_repo>/<nome>/agents"
mkdir -p "<profiles_repo>/<nome>/references"
mkdir -p "<profiles_repo>/<nome>/plans/todo"
mkdir -p "<profiles_repo>/<nome>/plans/in-progress"
mkdir -p "<profiles_repo>/<nome>/plans/done"
# NO dataset/ ne' plans/draft/ in legacy
# NO afu-manifest.schema.json (legacy non usa Solaria handoff manifest-based)
# Scrivi CONST.json con il contenuto confermato in 8.1
# Scrivi PROFILE.json con il contenuto confermato in 8.2
```

Conferma finale (testo adattato a `MODE`):

> Profilo **<nome>** creato in modalita' **<MODE>**:
> - `<PROJECT_REPO o profiles_repo/nome>/constitution/CONST.json` (principi)
> - `<PROJECT_REPO o profiles_repo/nome>/constitution/PROFILE.json` (dettagli)
> - Struttura: `constitution/`, `references/`, `agents/`, `plans/{[draft (standalone)],todo,in-progress,done}/`
> - [Solo standalone] `dataset/{branding,corporate,glossario.md,attori.md,perimetro.md}` — popolato da Solaria in F1b
> - [Solo standalone] `afu-manifest.schema.json` v2 copiato dal template

---

## Step 9 — Commit e push

Committa e pusha il nuovo profilo. Il target dipende da `MODE`:

**Se `MODE=standalone`** (project_repo dedicata):

```bash
cd "$PROJECT_REPO_ROOT"
git add constitution/ references/ agents/ dataset/ plans/ afu-manifest.schema.json
git commit -m "feat: initialize project setup (standalone mode) — CONST + PROFILE + dataset scaffolding"
git push origin main
```

**Se `MODE=legacy`** (deloitte-profiles):

```bash
cd "<profiles_repo>"
git add "<nome>/"
git commit -m "feat: add profile for <nome> (CONST + PROFILE)"
git push origin main
```

Se il push fallisce (es. branch protetto, conflitti), segnala all'utente:

> Il push e' fallito. Errore:
> ```
> [errore git]
> ```
>
> Opzioni:
> 1. Creare un branch e aprire una PR
> 2. Risolvere manualmente e riprovare
> 3. Lasciare il commit locale (pusha tu quando pronto)

Se l'utente sceglie branch + PR:

```bash
git checkout -b "profile/<nome>"
git push -u origin "profile/<nome>"
```

---

## Step 10 — Aggiorna .sdlc-local.json (con migrazione automatica per profili legacy)

Per ogni codebase fornito nello Step 3, proponi di aggiungere i campi a `.sdlc-local.json`. Lo schema cambia in base a `MODE`. Se nel codebase esiste già un `.br-local.json` legacy, viene migrato automaticamente.

**Algoritmo di scrittura/migrazione (4 scenari)**:

1. **`.sdlc-local.json` esiste già** → leggi il contenuto, preserva tutti i campi esistenti (developer, paths, customPaths, ecc.), aggiungi/aggiorna solo i campi della modalità scelta. **Non mischiare i due set** (`project_repo` e `profiles_repo` sono mutualmente esclusivi): se l'utente sta migrando un codebase da legacy a standalone, rimuovi `profiles_repo`+`profilo` e aggiungi `project_repo`+`project_name`, comunicandolo esplicitamente.

2. **Solo `.br-local.json` esiste (legacy)** → migrazione automatica:
   - Leggi il contenuto di `.br-local.json`
   - Scrivi il contenuto (preservando i campi esistenti + aggiungendo/aggiornando i campi della modalità) in `.sdlc-local.json`
   - Rinomina il vecchio file in `.br-local.json.bak` (NON cancellare, lascia traccia di rollback)
   - Comunica all'utente:
     ```
     > Profilo legacy `.br-local.json` rilevato. Lo migro a `.sdlc-local.json`.
     > Il vecchio file viene conservato come `.br-local.json.bak` (puoi cancellarlo
     > quando sei sicuro che tutto funzioni).
     ```

3. **Entrambi `.sdlc-local.json` e `.br-local.json` esistono (caso patologico)** → usa `.sdlc-local.json`, lascia `.br-local.json` invariato, segnala warning:
   ```
   > Trovati entrambi `.sdlc-local.json` e `.br-local.json` nella repo. Uso il primo.
   > Ti consiglio di rimuovere manualmente `.br-local.json` per evitare ambiguità.
   ```

4. **Nessuno dei due esiste** → crea ex novo `.sdlc-local.json` con i campi base della modalità scelta.

**Campi di orchestrazione (sempre inclusi, default `classic`)**:

Oltre ai campi di modalità, `.sdlc-local.json` contiene 4 campi **flat** che controllano come le skill SDLC si orchestrano — modalità `classic` (sequenziale, leggera, il comportamento storico) vs `deep` (workflow multi-agent + verifica adversariale). Sono flat (non annidati) per restare leggibili col `grep -oP` usato dalle skill su Git-bash Windows, senza dipendere da `jq`. Dettagli: `docs/ORCHESTRATION_INTEGRATION_DESIGN.md`.

| Campo | Default | Significato |
|---|---|---|
| `interaction_language` | *(chiesto una volta)* | `it` \| `en` — lingua di interazione con l'utente. Gli artefatti seguono la regola per classe (dev-facing sempre EN). |
| `decomposition_bias` | *(opzionale)* | `testability` \| `parallelization` — default suggerito per la strategia di decomposizione dei task (l'analyzer chiede comunque per-Piano). |
| `orchestration_mode` | `"classic"` | `classic` (sequenziale) \| `deep` (workflow + adversarial verify) |
| `orchestration_depth` | `"standard"` | `standard` \| `ultracode` (approfondimento extra in `deep`) |
| `orchestration_max_concurrency` | `10` | tetto agent concorrenti nei fan-out `deep` |
| `orchestration_verifier_panel` | `3` | numero di verificatori nei panel adversariali `deep` |

**Default conservativo**: per ogni profilo nuovo scrivi sempre `orchestration_mode: "classic"` — nessuna escalation a `deep` senza scelta esplicita dell'utente (mai spesa a sorpresa). Nello **scenario 1** (`.sdlc-local.json` già esistente) **preserva** eventuali valori `orchestration_*` presenti: non resettare a `classic` una scelta `deep` deliberata su un re-run del setup. Analogamente, se in `PROFILE.json` esiste già un `progress_report_template` con `mode:"custom"`, **preservalo** (non riportarlo a `official`).

**Lingua di interazione**: chiedi una volta all'utente se preferisce interagire in **italiano (`it`)** o **inglese (`en`)** con `AskUserQuestion`, e includi `"interaction_language": "<scelta>"` nel `.sdlc-local.json` scritto per ogni codebase. Nello **scenario 1** (`.sdlc-local.json` gia' esistente) **preserva** un `interaction_language` gia' presente (come per gli `orchestration_*`). Opzionalmente chiedi anche una preferenza di decomposizione (testability|parallelization) e scrivila come "decomposition_bias" (campo opzionale; se omesso, l'analyzer usa testability come default e chiede comunque per-Piano).

**Se `MODE=standalone`**:

> Per ogni codebase, aggiorno `.sdlc-local.json` con il riferimento al project_repo.
>
> ### BE — Back-end (`C:/progetti/myapp-backend`)
> File: `C:/progetti/myapp-backend/.sdlc-local.json`
>
> ```json
> {
>   "project_repo": "<PROJECT_REPO_ROOT>",
>   "project_name": "<nome>",
>   "interaction_language": "<it|en>",
>   "orchestration_mode": "classic",
>   "orchestration_depth": "standard",
>   "orchestration_max_concurrency": 10,
>   "orchestration_verifier_panel": 3
> }
> ```
>
> Procedo?

**Se `MODE=legacy`**:

> Per ogni codebase, aggiorno `.sdlc-local.json` con il riferimento al profilo.
>
> ### BE — Back-end (`C:/progetti/myapp-backend`)
> File: `C:/progetti/myapp-backend/.sdlc-local.json`
>
> ```json
> {
>   "profilo": "<nome>",
>   "profiles_repo": "<path-profiles-repo>",
>   "interaction_language": "<it|en>",
>   "orchestration_mode": "classic",
>   "orchestration_depth": "standard",
>   "orchestration_max_concurrency": 10,
>   "orchestration_verifier_panel": 3
> }
> ```
>
> Procedo?

**Se nessuno dei due file esiste** (`.sdlc-local.json` né `.br-local.json` legacy): crea ex novo `.sdlc-local.json` con i campi base della modalita' scelta:

```json
// standalone
{ "project_repo": "<PROJECT_REPO_ROOT>", "project_name": "<nome>", "interaction_language": "<it|en>", "orchestration_mode": "classic", "orchestration_depth": "standard", "orchestration_max_concurrency": 10, "orchestration_verifier_panel": 3 }

// legacy
{ "profilo": "<nome>", "profiles_repo": "<path-profiles-repo>", "interaction_language": "<it|en>", "orchestration_mode": "classic", "orchestration_depth": "standard", "orchestration_max_concurrency": 10, "orchestration_verifier_panel": 3 }
```

Procedi solo dopo conferma dell'utente. Aggiorna/crea il file per ogni codebase.

Dopo aver completato tutti i codebase, conferma:

> Profilo **<nome>** creato e configurato con successo.
>
> - Profilo: `<profiles_repo>/<nome>/constitution/CONST.json` + `PROFILE.json`
> - Struttura: `constitution/`, `agents/`, `references/`, `plans/todo|in-progress|done/`
> - References: `<profiles_repo>/<nome>/references/` (N file)
> - `.sdlc-local.json` aggiornato/creato in N codebase (eventuali `.br-local.json` legacy migrati a `.sdlc-local.json` + `.br-local.json.bak`)
> - Orchestrazione: `classic` (default conservativo). Per attivare la modalità workflow+approfondita, rilancia `/sdlc-profile-setup` o imposta `orchestration_mode: "deep"` in `.sdlc-local.json`.
>
> Il profilo e' un documento vivente: `sdlc-analyzer` lo aggiornera' automaticamente quando rileva nuove convenzioni durante l'analisi.

> **Master-folder:** se piu' codebase di uno stesso progetto vivono come sottocartelle di una master-folder, ogni codebase riceve il proprio `.sdlc-local.json` che punta allo stesso `project_repo`/`profilo`. E' atteso e corretto: le skill fanno **dedup per progetto** in fase di discovery (molte config = un progetto → una sola scelta).

---

## Step 11 — (Opzionale) Genera il brand.md deep per i mockup

Se è stato rilevato un codebase **frontend** (Step 4.2), proponi:

> Ho rilevato un frontend (`<framework>`). Vuoi generare anche il **brand.md** ad alta fedeltà
> per i mockup (skill `sdlc-brandkit`)? Serve al Mockup Designer per produrre mockup
> quasi-pixel-perfect. (Sì / No)

- **Sì** → invoca `sdlc-brandkit` passando i path dei repo frontend già raccolti (Step 3) e,
  se disponibile, un URL/POC per gli screenshot. L'output va nel **contesto** (SPEC/project repo),
  mai nel `dataset/`.
- **No** → salta (default). Il brand.md potrà essere generato in seguito con `/sdlc-brandkit`.

---

## Regole

1. **Una domanda alla volta** — Non anticipare domande. Aspetta la risposta prima di procedere.
2. **Auto-detect prima delle domande** — Rileva tutto il possibile dal codice prima di chiedere all'utente.
3. **Mai scrivere senza conferma** — Mostra sempre il contenuto proposto e aspetta l'OK prima di scrivere file.
4. **I campi opzionali sono opzionali** — Se l'utente salta una sezione, non insistere. Ometti la sezione dal JSON.
5. **Profilo vivente** — Il profilo e' un documento vivente. `sdlc-analyzer` lo aggiorna automaticamente quando rileva nuove convenzioni durante l'analisi dei codebase. Non serve che sia perfetto al primo setup.
