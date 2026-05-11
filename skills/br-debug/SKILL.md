---
name: br-debug
description: Gestisce i bug segnalati dai funzionali durante e dopo il testing di un Business Requirement. Importa bug da Excel o Jira, li collega alle task del piano, li assegna agli sviluppatori, esegue i fix con sottoagenti Claude e verifica in 3 fasi, gestisce la chiusura con validazione funzionale e il re-import iterativo. Supporta qualsiasi composizione di repository. Usa questa skill quando l'utente dice "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti", "lavora il bug", "fix il bug", "debug br", "il funzionale ha testato", "bug confermati", "aggiorna i bug", o qualsiasi variazione che implichi la gestione di bug su un BR. Attivala anche quando l'utente menziona un file di segnalazioni o chiede di lavorare i defect.
---

# BR Debug — Gestione Bug da Testing Funzionale

Questa skill gestisce i bug segnalati dai funzionali durante e dopo il testing di un Business Requirement. Copre l'intero ciclo: importazione, analisi, fix con sottoagenti, verifica, chiusura con validazione funzionale, e re-import iterativo.

Il debug e' uno **stage parallelo**: coesiste con l'esecuzione delle task, non e' sequenziale.

```
stato_pipeline:  approved ──→ execute ──→ done
debug:           ─────────── debug_attivo ─────── debug chiuso
```

Il BR passa a `done` solo quando tutte le task sono completate E tutti i bug sono chiusi.

---

## Rilevamento Contesto

La skill rileva automaticamente il contesto operativo:

- **Se trova `brs/<nome>/manifest.json`** → modalita' **portal-flow**: il manifest e' la source of truth, `BUG_REPORT_BR.md` e' una vista retrocompatibile generata dal manifest
- **Se trova `plans/*/PIANO_IMPLEMENTAZIONE_BR.md` senza manifest** → modalita' **claude-flow**: `BUG_REPORT_BR.md` e' la source of truth diretta

| Contesto | Source of truth | Artefatti |
|---|---|---|
| claude-flow | `BUG_REPORT_BR.md` in `plans/` | File MD diretto |
| portal-flow | `manifest.bugs[]` in `brs/<nome>/manifest.json` | Manifest + vista MD |

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

---

## Rilevamento Modalita'

La skill rileva automaticamente la modalita' di funzionamento in base al contesto e al trigger dell'utente:

- **Import mode**: non esiste `BUG_REPORT_BR.md` / `manifest.bugs`, oppure l'utente dice "ci sono dei bug", "segnalazioni test", "defect ricevuti", "importa i bug"
- **Execution mode**: esistono bug assegnati allo sviluppatore con stato diverso da `chiuso`, oppure l'utente dice "lavora il bug", "fix il bug", "debug br"
- **Chiusura mode**: l'utente dice "il funzionale ha testato", "bug confermati", "aggiorna i bug"

---

## Ciclo di Vita del Bug

```
aperto → assegnato → in_corso → verificato → chiuso
                        ↓
                     bloccato
```

| Stato | Significato |
|---|---|
| `aperto` | Bug importato, non ancora assegnato |
| `assegnato` | Owner definito, non ancora in lavorazione |
| `in_corso` | Lo sviluppatore sta lavorando il fix |
| `verificato` | Fix implementato e verificato tecnicamente, in attesa di validazione funzionale |
| `chiuso` | Il funzionale conferma che il bug e' risolto |
| `bloccato` | Il fix e' bloccato da un impedimento |

### Severita'

| Livello | Significato |
|---|---|
| `critico` | Blocca l'uso della funzionalita' |
| `maggiore` | Funzionalita' degradata ma utilizzabile |
| `minore` | Difetto estetico o marginale |

Tutti i livelli seguono il ciclo di verifica completo (3 fasi).

---

## Fase 1 — Import dei Bug

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — BR di riferimento

Cerca i BR attivi in base al contesto:

**Portal-flow:**
```bash
ls brs/*/manifest.json 2>/dev/null
```
Filtra quelli con `stato_pipeline` in `approved`, `execute`, o `done`.

**Claude-flow:**
```bash
ls -d plans/todo/*/ plans/in-progress/*/ plans/done/*/ 2>/dev/null
```

Se ne trovi uno, proponilo. Se piu' di uno, chiedi quale. Se nessuno, avvisa che serve prima un piano di implementazione.

### Domanda 2 — Sorgente dei bug

> Da dove arrivano i bug?
> 1. **File Excel** — dammi il path del file
> 2. **Jira** — mi collego al progetto e importo i ticket
> 3. **Entrambi** — prima importo da file, poi integro da Jira

### Import da Excel — Mapping intelligente

Leggi il file Excel con Python + openpyxl. Leggi la prima riga (header) e tenta un mapping automatico basato su pattern riconoscibili (case-insensitive, match parziale):

| Campo interno | Pattern riconosciuti |
|---|---|
| `id` | id, #, numero |
| `fase` | fase, fase processo, area, modulo |
| `sezione` | sezione, sotto-sezione, pagina |
| `utente` | utente, user, profilo, ruolo utente |
| `titolo` | titolo, problema riscontrato, summary, title |
| `descrizione` | descrizione, descrizione del problema, description |
| `screenshot` | screen, screenshot, allegati, immagini |
| `riferimento` | rif, rif. pratica, reference, ticket |
| `tipo` | tipo, tipo segnalazione, type, category |
| `stato_originale` | stato, status |
| `data` | data, date, data segnalazione |
| `note_dev` | note team sviluppo, note dev, dev notes |
| `note_funzionale` | note team funzionale, note funzionali |

Se una colonna non viene mappata automaticamente, presentala all'utente e chiedi se e' rilevante. Le colonne non mappate vengono ignorate.

Script per la lettura:

```python
import openpyxl

wb = openpyxl.load_workbook('<path_file>')
ws = wb[wb.sheetnames[0]]  # primo foglio = dati
headers = [cell.value for cell in ws[1]]
bugs = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] is None:
        continue
    bug = dict(zip(headers, row))
    bugs.append(bug)
```

**Mapping dei tipi segnalazione:**

| Tipo segnalazione (Excel) | Tipo (interno) | Severita' (default) |
|---|---|---|
| `DEFECT/BUG` | `bug` | `maggiore` |
| `MINOR` | `bug` | `minore` |
| `CAMBIO LABEL` | `label` | `minore` |
| `CR` | `change_request` | `minore` (fisso, non modificabile) |

Il mapping dei tipi e' flessibile — se il file usa termini diversi, la skill presenta i valori trovati e chiede la mappatura. Per i tipi riconosciuti, il TL/PM puo' cambiare la severita' in fase di conferma (tranne le CR che restano sempre `minore`).

**Filtro per stato:** importa solo i bug con stato diverso da "Chiuso":

> Il file contiene N segnalazioni.
> - X gia' chiuse (non importate)
> - Y aperte o in test → da importare
>
> Vuoi importare tutte le Y, oppure filtrare per tipo?

**Screenshot:** se il file ha un foglio "Screen" con immagini referenziate dalla colonna Screen, estrai le immagini e salvale nella cartella del BR:

- Portal-flow: `brs/<nome>/screenshots/`
- Claude-flow: `plans/in-progress/<data>_<nome>/screenshots/` (o `plans/todo/` se non ancora in-progress)

### Import da Jira

Usa la skill `jira` (se disponibile) o l'MCP Jira se configurato. Chiedi:

1. **Progetto Jira** — o deducilo dal BR
2. **Filtro** — tipo = Bug, stato = Open/To Do, opzionalmente sprint o label

Per ogni ticket importato, mappa i campi Jira standard:

| Campo Jira | Campo interno |
|---|---|
| `key` | `id_originale` |
| `summary` | `titolo` |
| `description` | `descrizione` |
| `priority` | `severita` (Critical→critico, Major→maggiore, Minor/Trivial→minore) |
| `assignee` | `owner` (se corrisponde a un dev nel piano) |
| `labels` / `components` | `fase`, `sezione` (best effort) |
| `created` | `data_segnalazione` |

### Domanda 3 — Collegamento alle funzionalita'

Per ogni bug importato, tenta un collegamento automatico alle task/stream del piano:

1. Confronta il campo `fase` + `sezione` del bug con i nomi degli stream e le descrizioni delle task nel piano
2. Se il bug menziona un'area funzionale (es. "booking", "monitoraggio", "accesso"), collegalo allo stream corrispondente
3. Se trova un match con una task specifica, collegalo direttamente

Bug senza collegamento a task/stream vengono categorizzati sotto lo pseudo-stream `debug-generico`.

Presenta la lista all'utente per conferma e correzione:

> Bug importati: N
>
> | ID | Titolo | Tipo | Sev. | Collegato a | Owner suggerito |
> |---|---|---|---|---|---|
> | BUG-001 | Login fallisce con email maiuscola | bug | critico | T-012 (Auth login) | Marco (owner T-012) |
> | BUG-002 | Tabella non ordinabile | bug | maggiore | stream-monitoraggio | ? (nessun match) |
> | BUG-003 | Typo checkbox privacy | label | minore | T-008 (Pop-up info) | Luca (owner T-008) |
>
> Confermi i collegamenti? Per i bug senza match, a chi li assegno?

### Domanda 4 — Assegnazione

Per i bug con match: proponi l'owner della task collegata (default). Il TL/PM puo' riassegnare.
Per i bug senza match: chiedi esplicitamente a chi assegnare.

### Riepilogo e conferma

> Riepilogo import:
> - Sorgente: [Excel / Jira / entrambi]
> - BR: [nome]
> - Bug importati: N (di cui X bug, Y label, Z CR)
> - Severita': A critici, B maggiori, C minori
> - Assegnati a: [lista sviluppatori con conteggio]
>
> Confermo?

Dopo la conferma, scrivi i bug nella source of truth.

### Scrittura — Portal-flow

Leggi il manifest corrente, aggiungi la sezione `bugs`:

```json
{
  "bugs": {
    "debug_attivo": true,
    "data_ultimo_import": "<YYYY-MM-DD>",
    "sorgente": "<excel|jira|entrambi>",
    "sorgente_file": "<nome file se excel>",
    "riepilogo": {
      "totali": 0,
      "aperti": 0,
      "in_corso": 0,
      "verificati": 0,
      "chiusi": 0,
      "bloccati": 0
    },
    "lista": []
  }
}
```

Per ogni bug, aggiungi un oggetto a `bugs.lista[]`:

```json
{
  "id": "BUG-001",
  "id_originale": 1,
  "tipo": "bug",
  "severita": "maggiore",
  "fase": "Dashboard",
  "sezione": "Tabella Pratiche Attive",
  "utente": "Banca",
  "titolo": "Visualizza Pratiche",
  "descrizione": "Gli utenti Banca devono poter vedere...",
  "screenshot": [],
  "riferimento": null,
  "task_collegata": "T-012",
  "stream_collegato": "stream-monitoraggio",
  "owner": "Marco",
  "stato": "assegnato",
  "progresso": 0,
  "branch": null,
  "data_segnalazione": "2026-05-06",
  "data_assegnazione": "<data odierna>",
  "data_chiusura": null,
  "note_dev": "",
  "note_funzionale": "",
  "fix_summary": ""
}
```

Aggiorna `bugs.riepilogo` con i conteggi. Aggiungi entry alla `timeline[]`:

```json
{
  "data": "<ISO-timestamp>",
  "attore": "<utente>",
  "ruolo": "TL/PM",
  "azione": "Importati N bug da <sorgente>",
  "stage": "debug"
}
```

Scrivi il manifest con il tool `Write` (mai `Edit` per JSON). Commit: `[br-debug] <nome>: importati N bug da <sorgente>`

Dopo il commit, genera la vista MD `brs/<nome>/BUG_REPORT_BR.md` (vedi sezione "Struttura BUG_REPORT_BR.md").

### Scrittura — Claude-flow

Crea `BUG_REPORT_BR.md` nella cartella del BR (es. `plans/in-progress/<data>_<nome>/BUG_REPORT_BR.md`). Usa il formato definito nella sezione "Struttura BUG_REPORT_BR.md".

---

## Fase 2 — Esecuzione Fix

### Identificazione sviluppatore

**Portal-flow:** leggi `.br-local.json` per il nome.
**Claude-flow:** chiedi chi e' lo sviluppatore, mostrando la lista dal piano.

### Selezione bug da lavorare

Filtra i bug assegnati allo sviluppatore con stato diverso da `chiuso` e `verificato`. Ordina per severita' (critico > maggiore > minore) e poi per tipo (bug > label > change_request). Le CR finiscono sempre in coda.

> I tuoi bug assegnati:
>
> | # | ID | Tipo | Sev. | Titolo | Fase > Sezione | Stato |
> |---|---|---|---|---|---|---|
> | 1 | BUG-003 | bug | critico | Login fallisce con email maiuscola | Accesso > Login | assegnato |
> | 2 | BUG-007 | bug | maggiore | Tabella non ordinabile | Dashboard > Pratiche | assegnato |
> | 3 | BUG-015 | label | minore | Typo checkbox privacy | Accesso > Pop-Up | assegnato |
>
> Vuoi procedere con **BUG-003**?

Aspetta la conferma prima di procedere.

### Raggruppamento bug minori

Per bug di tipo `label` o con severita' `minore` nella stessa sezione, proponi di raggrupparli:

> I bug BUG-015, BUG-016, BUG-017 sono tutti cambi label nella sezione "Pop-Up Informazioni Importanti".
> Vuoi lavorarli insieme su un unico branch `fix/<br-name>-label-popup`?

Se confermato, lancia un sottoagente unico con tutti i bug del gruppo.

### Analisi del bug prima del fix

Prima di lanciare il sottoagente:

1. **Leggi la descrizione completa** del bug, inclusi tutti gli Update inline
2. **Leggi la task collegata** dal piano e dal gap report per il contesto funzionale originale
3. **Localizza il codice coinvolto** — usa fase/sezione del bug e i file della task collegata. Se necessario, usa un agente `Explore` per trovare il codice rilevante nei codebase
4. **Leggi gli screenshot** se presenti
5. **Formula un'ipotesi di root cause** basata su descrizione + codice trovato

Presenta l'analisi allo sviluppatore:

> ## Analisi BUG-003 — Login fallisce con email maiuscola
>
> **Problema:** [riepilogo dalla descrizione]
> **Contesto funzionale:** [dalla task collegata T-012]
> **File probabilmente coinvolti:**
> - `src/auth/LoginService.java:42` — validazione email
> - `src/auth/UserRepository.java:78` — query lookup utente
>
> **Ipotesi root cause:** La query di lookup confronta l'email case-sensitive. Serve un confronto case-insensitive o una normalizzazione a lowercase.
>
> Procedo con il fix?

Aspetta la conferma.

### Creazione branch

Dopo la conferma, crea il branch in tutte le repo coinvolte:

1. **Determina il nome del branch:** `fix/<br-name>-BUG-<NNN>-<slug>` (es. `fix/monitoring-BUG-003-table-sort`). Per bug raggruppati: `fix/<br-name>-label-<sezione>`.

2. **Repo del piano** (la repo corrente):
   ```bash
   git checkout -b fix/<br-name>-BUG-<NNN>-<slug>
   ```

3. **Per ogni altra repo coinvolta** (da `.br-local.json` o dai path forniti nella Fase 1 di br-executor):
   ```bash
   git -C <path-repo-esterna> checkout -b fix/<br-name>-BUG-<NNN>-<slug>
   ```

4. Aggiorna lo stato del bug a `in_corso` e il campo `branch`.

### Esecuzione con sottoagenti

#### Routing a Specialist per Stack

**Se il profilo progetto e' disponibile**, determina il subagent_type in base al codebase coinvolto nel bug:

1. Identifica l'area del bug dalla colonna `fase`/`sezione` e dalla task collegata
2. Leggi `tech_stack.backend.framework` o `tech_stack.frontend.framework` dal profilo
3. Mappa al subagent_type:

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

4. Lancia il sottoagente con `Agent(subagent_type: "<tipo>", prompt: "<prompt>")`
5. Se il profilo non e' disponibile, usa `general-purpose` (comportamento attuale)

Aggiungi al prompt del sottoagente il contesto dal profilo (convenzioni, test naming, package structure).

Lancia un sottoagente con prompt autosufficiente che include:

1. **Il bug** — descrizione completa, screenshot, utente impattato, ipotesi di root cause
2. **Il contesto** — task originale che ha implementato la funzionalita', file coinvolti, pattern del progetto
3. **L'ipotesi di root cause** — dove guardare, cosa potrebbe essere il problema
4. **Cosa deve fare:**
   - Implementare il fix
   - Scrivere un test che riproduce il bug (deve fallire PRIMA del fix se eseguito sul codice originale)
   - Scrivere un test che verifica il fix (deve passare DOPO)
   - Scrivere test di regressione (il comportamento corretto preesistente non e' rotto)
5. **Vincoli** — non rompere funzionalita' esistenti, seguire le convenzioni del progetto

Esempio di dispatch a un sottoagente:

```
Correggi il seguente bug nel codebase backend.

Codebase: <path locale>
Bug: BUG-003 — Login fallisce con email maiuscola

Descrizione del problema:
<descrizione completa dal bug>

Contesto:
- Questa funzionalita' e' stata implementata nella task T-012
- Il progetto usa Spring Boot con JPA/Hibernate
- I service seguono il pattern in <path>/service/
- [altri pattern osservati]

Ipotesi root cause:
La query di lookup in UserRepository confronta l'email case-sensitive.

File probabilmente coinvolti:
- <path>/service/LoginService.java
- <path>/repository/UserRepository.java

Cosa fare:
1. Scrivi un test che riproduce il bug: login con email "Mario@Example.com"
   deve funzionare come "mario@example.com"
2. Implementa il fix (normalizzazione email a lowercase)
3. Scrivi test di regressione: login con email corretta continua a funzionare

File di riferimento per le convenzioni:
- <path>/test/service/ExistingServiceTest.java
```

### Verifica in 3 fasi

Dopo che il sottoagente completa il fix, esegui la verifica in 3 fasi:

**Se il profilo progetto e' disponibile:**

Delega la verifica all'agente `br-verifier` (leggendo le sue istruzioni da `~/.claude/agents/br-verifier.md`). Passa:
- Requisiti: descrizione del bug + ipotesi di root cause
- File modificati: lista dei file toccati dal sottoagente
- Risultati test: output dell'esecuzione test
- Convenzioni dal profilo: test_naming, base_entity, package_structure

Se il verifier restituisce FAIL, leggi i dettagli e lancia un sottoagente di correzione. Ripeti la verifica.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esegui la verifica inline in 3 fasi come segue:

**Fase A — Verifica tecnica**

1. **Esegui i test** — la suite completa deve passare con zero failure
2. **Verifica la build** — il progetto deve compilare senza errori
3. **Controlla i test scritti** — verifica che il sottoagente abbia scritto:
   - Test che riproduce il bug originale
   - Test che verifica il fix
   - Test di regressione
   - Se mancano, lancia un nuovo sottoagente per aggiungerli

**Fase B — Verifica di coerenza col bug**

Rileggi la descrizione del bug (inclusi tutti gli Update). Per OGNI aspetto del problema:

1. **E' stato risolto?** — il fix copre effettivamente il problema descritto
2. **Tutti gli scenari?** — se il bug ha piu' Update o casi d'uso, sono tutti coperti
3. **Effetti collaterali?** — il fix non introduce nuovi problemi

Se trovi discrepanze, lancia un sottoagente di correzione e ripeti la Fase B.

**Fase C — Riesame finale**

1. **Rileggere il codice del fix** — non fidarti del riepilogo del sottoagente
2. **Cercare regressioni** — il fix non rompe il comportamento corretto preesistente
3. **Verificare che i test testino realmente** — asserzioni specifiche e significative
4. **Controllare naming e convenzioni**

Se trovi problemi, correggi e ripeti la Fase C.

Solo quando TUTTE e 3 le fasi sono superate il fix e' verificato.

### Suggerimento commit

Mai committare autonomamente. Suggerisci per ogni repo coinvolta:

**Se il fix coinvolge solo la repo del piano:**

> Il fix per **BUG-003** e' completo e verificato:
> - [lista file creati/modificati]
> - Test: [N test, tutti verdi]
> - Build: compila
>
> Suggerisco:
> ```
> git add [file specifici]
> git commit -m "fix(<area>): <descrizione fix> (BUG-003)"
> ```
>
> Dopo il commit, pusha:
> ```
> git push origin fix/<br-name>-BUG-003-<slug>
> ```

**Se il fix coinvolge piu' repo:**

Fornisci suggerimenti separati per ogni repo, come fa br-executor.

Aspetta la conferma prima di proseguire.

### Completamento bug → stato `verificato`

Quando il fix e' implementato e verificato tecnicamente, presenta la tabella di verifica:

> ## Verifica completamento BUG-003
>
> | # | Aspetto | Verificato | Dettaglio |
> |---|---|---|---|
> | 1 | Bug riprodotto nel test | Si | `LoginServiceTest#shouldHandleCaseInsensitiveEmail` |
> | 2 | Fix implementato | Si | `LoginService.java:45` — normalizzazione toLowerCase |
> | 3 | Test di regressione | Si | `LoginServiceTest#shouldLoginWithValidEmail` — passa |
> | 4 | Build | Si | Compila senza errori |
>
> **Fix summary:** Normalizzazione email a lowercase prima del lookup nel DB.
>
> Il bug passa a stato **verificato**. Il funzionale dovra' confermare che il problema e' risolto.

Aggiorna lo stato del bug a `verificato`, il progresso a 100%, e compila il campo `fix_summary`.

Proponi il prossimo bug disponibile.

---

## Fase 3 — Chiusura e Re-import

### Chiusura da parte del funzionale

Tre flussi supportati:

**Flusso 1 — Excel aggiornato:**

Il funzionale aggiorna lo stesso file Excel cambiando lo stato a "Chiuso" o riapre il bug. La skill rileva i delta:

1. Leggi il file aggiornato con openpyxl
2. Per ogni riga, confronta lo stato con quello attuale dei bug (match per `id_originale`)
3. Presenta i delta:

> Ho confrontato il file aggiornato con lo stato attuale dei bug.
>
> | ID | Stato precedente | Stato nuovo | Note funzionale |
> |---|---|---|---|
> | BUG-003 | verificato | Chiuso | OK, funziona |
> | BUG-007 | verificato | Aperto | Il problema persiste con dati paginati |
> | BUG-015 | verificato | Chiuso | — |
>
> - 2 bug confermati chiusi
> - 1 bug riaperto con nuova nota
>
> Confermo gli aggiornamenti?

**Flusso 2 — Jira:**

Se l'import originale era da Jira, rileggi lo stato dei ticket per sincronizzare. Ticket chiusi → bug chiuso. Ticket riaperti → bug riaperto con commento Jira come nota.

**Flusso 3 — Conversazione:**

L'utente riporta a voce. Chiedi conferma bug per bug prima di aggiornare.

### Bug riaperti

Quando un bug torna da `verificato` a `aperto`:

1. Lo stato torna a `aperto`
2. La nota del funzionale viene aggiunta al campo `note_funzionale`
3. La descrizione viene preservata con append: `[Riapertura <data>]: <nota del funzionale>`
4. Il branch precedente viene riutilizzato se esiste ancora, oppure ne viene creato uno nuovo
5. Il `fix_summary` precedente viene preservato con prefisso `[Fix precedente]: `
6. Il progresso torna a 0%

### Re-import iterativo

La skill puo' essere invocata piu' volte sullo stesso BR. A ogni invocazione:

- Bug gia' importati (match per `id_originale`) non vengono duplicati
- Nuovi bug nel file/Jira vengono aggiunti con ID sequenziale dal prossimo disponibile (es. se l'ultimo e' BUG-033, il prossimo e' BUG-034)
- Bug con stato cambiato vengono sincronizzati (se la direzione e' chiusura o riapertura)
- Presenta sempre il delta prima di applicare:

> Re-import dal file aggiornato:
> - 5 nuovi bug da importare (BUG-034 → BUG-038)
> - 3 bug con stato aggiornato (chiusi dal funzionale)
> - 25 invariati
>
> Confermo?

### Condizione di completamento debug

Quando tutti i bug hanno stato `chiuso`:

**Portal-flow:**
- `manifest.bugs.debug_attivo` → `false`
- Aggiungi entry alla timeline: "Debug completato: N bug risolti"
- Rigenera `BUG_REPORT_BR.md`

**Claude-flow:**
- Aggiungi sezione "Debug completato" al `BUG_REPORT_BR.md`:

```markdown
## Debug Completato

Data chiusura: <data>
Bug totali: N
Bug risolti: N
```

Se il BR e' in stato `execute` e tutte le task E tutti i bug sono completati, il BR puo' passare a `done`.

---

## Struttura BUG_REPORT_BR.md

Questo formato e' usato sia come source of truth (claude-flow) sia come vista generata (portal-flow):

```markdown
# Bug Report — <nome BR>

Data import: <data>
Sorgente: <file/jira/entrambi>
Ultimo aggiornamento: <data e ora>

## Riepilogo

| Metrica | Valore |
|---|---|
| Bug totali | N |
| Aperti | X |
| In corso | Y |
| Verificati | Z |
| Chiusi | W |
| Bloccati | K |

## Lista Bug

| ID | Tipo | Sev. | Fase | Sezione | Titolo | Owner | Stato | Task | Branch |
|---|---|---|---|---|---|---|---|---|---|
| BUG-001 | bug | maggiore | Dashboard | Tabella Pratiche | ... | Marco | assegnato | T-012 | — |

## Dettaglio Bug

### BUG-001 — <titolo>

- **Tipo**: <tipo> | **Severita'**: <severita>
- **Fase**: <fase> > <sezione>
- **Utente**: <utente>
- **Task collegata**: <task_collegata>
- **Owner**: <owner>
- **Stato**: <stato>

**Descrizione:**
<descrizione completa>

**Screenshot:** <link o "—">
**Note dev:** <note_dev o "—">
**Note funzionale:** <note_funzionale o "—">
**Fix summary:** <fix_summary o "—">

---

[ripetere per ogni bug]

## Log Attivita'

### <data>
- <evento>
```

---

## Regole Fondamentali

1. **Mai committare autonomamente** nel codebase del progetto — suggerisci e aspetta conferma. Committare autonomamente solo nella repo del piano/pipeline (manifest, progresso, BUG_REPORT).
2. **Mai procedere senza conferma** — tra un bug e l'altro, prima di ogni modifica alla source of truth.
3. **Verificare prima di dichiarare verificato** — tutte e 3 le fasi complete per ogni bug.
4. **Mai duplicare bug al re-import** — confronta sempre per `id_originale`.
5. **Mai sovrascrivere note precedenti** — append, non replace.
6. **Il sottoagente implementa, l'agente principale coordina** — non implementare codice direttamente.
7. **Supportare entrambe le modalita'** (claude-flow e portal-flow) senza compromessi.
8. **Le CR hanno sempre severita' minore** — non modificabile.

---

## Dipendenze

| Dipendenza | Usata per | Installazione |
|---|---|---|
| `openpyxl` (Python) | Lettura/scrittura Excel | `pip install openpyxl` |
| skill `jira` | Import da Jira (opzionale) | gia' nell'ecosistema |

## Context

This is one of 8 skills in the BR (Business Requirement) lifecycle suite. The other skills are:
- br-reviewer: reviews functional documentation quality
- br-clarify: manages functional team responses to review questions
- br-analyzer: gap analysis between BR docs and codebase
- br-executor: executes implementation tasks from the plan
- br-updater: updates plan when BR documentation changes
- br-progress-report: generates Excel progress reports
- br-pipeline: orchestrates the entire BR lifecycle

br-debug fits as a PARALLEL stage alongside br-executor. It uses the same patterns: subagent delegation, 3-phase verification, progress tracking, cross-branch aggregation.

The skill must work in TWO contexts:
1. claude-flow: standalone, BUG_REPORT_BR.md is the source of truth, files in plans/ directory
2. portal-flow: with manifest.json as source of truth, BUG_REPORT_BR.md as generated view
