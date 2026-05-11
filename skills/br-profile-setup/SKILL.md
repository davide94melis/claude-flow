---
name: br-profile-setup
description: Crea un nuovo profilo progetto in deloitte-profiles con auto-detect del codebase, domande guidate su dominio e design system, e configurazione automatica di .br-local.json. Usa questa skill quando l'utente dice "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo", o qualsiasi variazione che implichi la creazione o configurazione di un profilo progetto per le skill BR.
---

# BR Profile Setup — Creazione Guidata Profilo Progetto

Questa skill guida la creazione di un nuovo profilo progetto nel repository `deloitte-profiles/`. Il profilo contiene tech stack, convenzioni, dominio e design system utilizzati da tutte le skill BR. Il flusso e' composto da 10 step sequenziali: una domanda alla volta, con auto-detect del codebase prima delle domande manuali.

---

## Step 1 — Nome progetto

Chiedi il nome del progetto. Diventa il nome della cartella nel repo dei profili.

> Come vuoi chiamare questo progetto? Il nome verra' usato come cartella nel repo dei profili.
>
> Esempio: "pnrr", "ecomotive", "isp-banking"

Salva il nome fornito. Usa kebab-case se l'utente fornisce un nome con spazi.

---

## Step 2 — Profiles repo

Chiedi il path locale del clone di `deloitte-profiles`.

> Qual e' il path locale del tuo clone di `deloitte-profiles`?
>
> Esempio: `C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles`

Dopo la risposta, verifica che sia un repo git valido e che contenga lo schema:

```bash
git -C "<path>" rev-parse --is-inside-work-tree 2>/dev/null && echo "OK: git repo" || echo "ERRORE: non e' un repo git"
ls "<path>/profile-schema.json" 2>/dev/null && echo "OK: schema trovato" || echo "WARNING: profile-schema.json non trovato"
```

Se il repo non e' valido, segnala e chiedi di riprovare. Se lo schema non c'e', avvisa ma procedi (verra' creato se necessario).

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

## Step 8 — Genera profile.json

Assembla tutti i dati raccolti in un JSON strutturato. Includi solo le sezioni con dati reali — ometti campi vuoti o sezioni saltate.

Struttura del JSON:

```json
{
  "nome": "<nome-progetto>",
  "creato": "<YYYY-MM-DD>",
  "aggiornato": "<YYYY-MM-DD>",
  "codebase": [
    {
      "nome": "<nome>",
      "sigla": "<SIGLA>",
      "tipo": "backend|frontend|fullstack",
      "framework": "<framework e versione>",
      "linguaggio": "<linguaggio e versione>",
      "database": "<db se rilevato>",
      "orm": "<orm se rilevato>",
      "struttura": "<package structure pattern>",
      "baseEntity": "<path classe base se rilevata>",
      "apiPrefix": "<prefix API se rilevato>",
      "testFramework": "<framework test>",
      "testNaming": "<pattern naming test>",
      "designSystem": {
        "uiLibrary": "<libreria UI>",
        "css": "<preprocessore CSS>",
        "colori": { "<nome>": "<valore>" },
        "font": "<font-family>",
        "spacing": "<scale se rilevata>"
      }
    }
  ],
  "dominio": {
    "glossario": [
      { "termine": "<termine>", "definizione": "<definizione>" }
    ],
    "regoleBusiness": [
      "<regola 1>",
      "<regola 2>"
    ],
    "statiEntita": {
      "<entita>": ["<stato1>", "<stato2>", "<stato3>"]
    }
  },
  "references": [
    "<nome-file-copiato>"
  ]
}
```

Presenta il JSON all'utente per conferma finale:

> Ecco il profilo generato per **<nome>**:
>
> ```json
> [JSON completo]
> ```
>
> Confermo e scrivo il file?

Procedi solo dopo conferma. Scrivi il file:

```bash
mkdir -p "<profiles_repo>/<nome>"
# Scrivi profile.json con il contenuto confermato
```

---

## Step 9 — Commit e push

Committa e pusha il nuovo profilo.

```bash
cd "<profiles_repo>"
git add "<nome>/"
git commit -m "feat: add profile for <nome>"
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

## Step 10 — Aggiorna .br-local.json

Per ogni codebase fornito nello Step 3, proponi di aggiungere i campi `profilo` e `profiles_repo` a `.br-local.json`.

> Per ogni codebase, aggiorno `.br-local.json` con il riferimento al profilo.
>
> ### BE — Back-end (`C:/progetti/myapp-backend`)
> File: `C:/progetti/myapp-backend/.br-local.json`
>
> ```json
> {
>   "profilo": "<nome>",
>   "profiles_repo": "<path-profiles-repo>"
> }
> ```
>
> Procedo?

**Se `.br-local.json` esiste gia'**: leggi il contenuto, preserva tutti i campi esistenti (developer, paths, customPaths, ecc.) e aggiungi solo `profilo` e `profiles_repo`.

**Se `.br-local.json` non esiste**: crea il file con i campi base:

```json
{
  "profilo": "<nome>",
  "profiles_repo": "<path-profiles-repo>"
}
```

Procedi solo dopo conferma dell'utente. Aggiorna/crea il file per ogni codebase.

Dopo aver completato tutti i codebase, conferma:

> Profilo **<nome>** creato e configurato con successo.
>
> - Profilo: `<profiles_repo>/<nome>/profile.json`
> - References: `<profiles_repo>/<nome>/references/` (N file)
> - `.br-local.json` aggiornato in N codebase
>
> Il profilo e' un documento vivente: `br-analyzer` lo aggiornera' automaticamente quando rileva nuove convenzioni durante l'analisi.

---

## Regole

1. **Una domanda alla volta** — Non anticipare domande. Aspetta la risposta prima di procedere.
2. **Auto-detect prima delle domande** — Rileva tutto il possibile dal codice prima di chiedere all'utente.
3. **Mai scrivere senza conferma** — Mostra sempre il contenuto proposto e aspetta l'OK prima di scrivere file.
4. **I campi opzionali sono opzionali** — Se l'utente salta una sezione, non insistere. Ometti la sezione dal JSON.
5. **Profilo vivente** — Il profilo e' un documento vivente. `br-analyzer` lo aggiorna automaticamente quando rileva nuove convenzioni durante l'analisi dei codebase. Non serve che sia perfetto al primo setup.
