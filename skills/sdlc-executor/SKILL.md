---
name: sdlc-executor
description: Esegue i task del piano di implementazione generato da sdlc-analyzer. Ogni sviluppatore/agente usa questa skill per lavorare le proprie task assegnate, con sottoagenti Claude che implementano codice e test mentre l'agente principale coordina, verifica e traccia il progresso. Supporta qualsiasi composizione di repository — il progetto può avere una o più repo con nomi arbitrari. Usa questa skill quando l'utente dice "lavora il task", "inizia a lavorare", "esegui il piano", "sono lo sviluppatore X", "devo lavorare le mie task", "task executor", "esegui task", o qualsiasi variazione che implichi l'inizio della lavorazione di task da un piano di implementazione (BR / AFU / Piano). Attivala anche quando l'utente menziona un file di progresso o chiede di riprendere il lavoro su task assegnate.
---

# SDLC Executor — Esecuzione Task da TASKS

Questa skill è il complemento operativo di `sdlc-analyzer`. Mentre `sdlc-analyzer` analizza un'AFU e genera PLAN + TASKS, questa skill permette a ogni sviluppatore (assistito da un agente Claude Code) di eseguire le proprie task assegnate.

L'agente principale coordina il lavoro, delega l'implementazione a sottoagenti, verifica i risultati e tiene aggiornato il file di progresso.

---

## Risoluzione Path (modalita' duale: standalone | legacy)

Tutte le operazioni su file plan avvengono nella **project_repo** (modalita' standalone, una repo per progetto) o nella repo `deloitte-profiles` (modalita' legacy), **non** nella repo del codice applicativo. Il codice del progetto continua a essere scritto nelle repo del progetto.

### Lettura del file di configurazione locale (`.sdlc-local.json` con fallback `.br-local.json`)

**Lettura compatibile**: il file di configurazione locale può chiamarsi `.sdlc-local.json` (nuovo nome, raccomandato) oppure `.br-local.json` (nome legacy, ancora supportato). Cerca PRIMA `.sdlc-local.json`; se non esiste, fa fallback a `.br-local.json`. Se nessuno dei due esiste, ferma e chiedi all'utente di eseguire `/sdlc-profile-setup`.

Se trovi solo `.br-local.json` (profilo legacy), emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

I comandi `bash` seguenti sono scritti referenziando `.br-local.json` per chiarezza storica — applica equivalentemente la stessa logica al file effettivamente trovato (sia `.sdlc-local.json` che `.br-local.json`).

All'avvio, leggi il file (priorità `.sdlc-local.json`, fallback `.br-local.json`) dalla root della repo corrente:

```bash
# Esempio con .br-local.json — equivalente per .sdlc-local.json
cat .br-local.json 2>/dev/null
```

La presenza del campo `project_repo` o `profiles_repo` discrimina la modalita':

```bash
if grep -q '"project_repo"' .br-local.json 2>/dev/null; then
  MODE="standalone"
  PROJECT_REPO=$(grep -oP '"project_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROJECT_NAME=$(grep -oP '"project_name"\s*:\s*"\K[^"]+' .br-local.json)
  BASE_PATH="$PROJECT_REPO/plans"
  CONST_PATH="$PROJECT_REPO/constitution"
  DATASET_PATH="$PROJECT_REPO/dataset"        # solo standalone (popolato da Solaria-side)
  GIT_REPO_PATH="$PROJECT_REPO"
elif grep -q '"profiles_repo"' .br-local.json 2>/dev/null; then
  MODE="legacy"
  PROFILES_REPO=$(grep -oP '"profiles_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROFILO=$(grep -oP '"profilo"\s*:\s*"\K[^"]+' .br-local.json)
  PROJECT_NAME="$PROFILO"
  BASE_PATH="$PROFILES_REPO/$PROFILO/plans"
  CONST_PATH="$PROFILES_REPO/$PROFILO/constitution"
  DATASET_PATH=""                              # non esiste in legacy
  GIT_REPO_PATH="$PROFILES_REPO"
fi
```

| Modalita' | `BASE_PATH` | `CONST_PATH` | Stati supportati |
|---|---|---|---|
| Standalone | `$PROJECT_REPO/plans` | `$PROJECT_REPO/constitution` | `draft`, `todo`, `in-progress`, `done` |
| Legacy | `$PROFILES_REPO/$PROFILO/plans` | `$PROFILES_REPO/$PROFILO/constitution` | `todo`, `in-progress`, `done` |

> **Nota**: `plans/draft/` esiste solo in modalita' standalone — area dove Solaria authora l'AFU prima dell'handoff (Fase 1c). Le skill SDLC ignorano `draft/` (e' Solaria-side) tranne `sdlc-reviewer` e `sdlc-clarify` quando esplicitamente invocate su un draft.

### Se né `.sdlc-local.json` né `.br-local.json` esistono

Ferma l'esecuzione e avvisa:

> Nessun file di configurazione locale trovato (`.sdlc-local.json` né `.br-local.json` legacy). Devi prima eseguire `/sdlc-profile-setup`, che ti chiedera' se vuoi configurare in **modalita' standalone** (raccomandato per nuovi progetti, una repo per progetto con cartella `dataset/` Solaria-side) o **modalita' legacy** (progetti gia' esistenti in `deloitte-profiles`).

### Sincronizzazione prima della lettura

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
```

### Commit e push dopo la scrittura

```bash
git -C "$GIT_REPO_PATH" add .
git -C "$GIT_REPO_PATH" commit -m "<messaggio>"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path con l'helper di detection sopra, prima di eseguire qualsiasi altra fase carica i due file di costituzione del progetto:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
cat "$CONST_PATH/CONST.json"
cat "$CONST_PATH/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| Né `.sdlc-local.json` né `.br-local.json` (legacy) presenti | "Esegui prima `/sdlc-profile-setup` scegliendo modalita' standalone o legacy" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il progetto `<PROJECT_NAME>` non ha CONST.json. Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il progetto `<PROJECT_NAME>` non ha PROFILE.json. Stato inconsistente — il profilo e' incompleto. Ripristinare da git history o rifare il setup." | Stop |
| Entrambi mancano, esiste `profile.json` (legacy) | "Profilo in formato vecchio (pre-split CONST/PROFILE). Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per fare lo split automaticamente." | Stop |
| JSON malformed | Mostra errore di parse + path | Stop |

**Semantica d'uso:**

- **CONST** = vincoli inviolabili per ogni output generato. Ogni piano, task, fix, review, bug analysis che produci DEVE rispettare:
  - `inviolable_principles` (security/a11y/responsiveness/privacy)
  - `quality_standards` (coverage, error handling, logging, performance)
  - `code_style` (limiti dimensionali, no magic numbers)
  - `git_workflow` (branch/commit pattern)
  - `architectural_patterns` (layering, response envelope, AAA, validazione boundary)
- **PROFILE** = "lingua" del progetto. Usa i dettagli (tech stack, repositories con sigle, dominio, glossario, design system) per nominare le task con le sigle corrette, proporre snippet con il framework/versione giusti, usare il vocabolario di dominio, e riferire componenti del design system.

Entrambi i file restano disponibili come contesto per tutta la durata della skill.

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — File del piano

Prima di chiedere, sincronizza la repo profili e verifica se esiste la struttura `plans/` nel profilo. Cerca cartelle dei Piani nelle tre aree:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/todo"/*/ "$BASE_PATH/in-progress"/*/ "$BASE_PATH/done"/*/ 2>/dev/null
```

**Se trovi cartelle dei Piani**, elencale e proponi:

> Ho trovato queste cartelle dei Piani:
> - `$BASE_PATH/todo/2026-04-28_booking-v2/` (contiene PLAN.md, TASKS.md)
> - `$BASE_PATH/in-progress/2026-04-15_monitoraggio/` (contiene PROGRESS.md)
>
> Quale vuoi lavorare? Oppure dammi i path manualmente.

**Se non trovi nulla**, chiedi:

> Per iniziare mi servono i file generati da sdlc-analyzer:
> 1. **PLAN** — il file `PLAN.md`
> 2. **TASKS** — il file `TASKS.md`
> 3. **File di Progresso** — se esiste gia' un file `PROGRESS.md`, dammi il path. Se non esiste ancora, lo creo io.

Leggi tutti i file forniti. Estrai dal gap report e dal piano:
- La lista di tutti i codebase menzionati (con i path originali)
- La lista di tutti i file di documentazione menzionati (con i path originali)
- La lista completa delle task con owner, dipendenze e stato

### Spostamento in `plans/in-progress/`

Quando lo sviluppatore conferma e la lavorazione sta per iniziare, sposta l'intera cartella del Piano da `$BASE_PATH/todo/` a `$BASE_PATH/in-progress/` (se non e' gia' li'):

```bash
git -C "$GIT_REPO_PATH" mv "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/" "<profilo>/plans/in-progress/"
git -C "$GIT_REPO_PATH" add .
git -C "$GIT_REPO_PATH" commit -m "[sdlc-executor] <nome>: avvio lavorazione, spostato in in-progress"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

Il file di progresso viene creato (o cercato) dentro la cartella del Piano in `$BASE_PATH/in-progress/`.

### Domanda 2 — Path dei codebase locali

Dal report e dal piano, estrai tutti i nomi e le sigle dei codebase/repository referenziati. Per ognuno, chiedi il path locale:

> Il piano fa riferimento a queste repository:
> [per ogni repo trovata nei file:]
> - **<Nome> (<SIGLA>)** — path nel piano: `<path dal report>`
>
> Conferma i path locali di ogni repository che hai disponibile.
> Se una repo non ti serve per le tue task, dimmelo.

### Domanda 3 — Path della documentazione locale

Dal report, estrai i nomi dei file di documentazione referenziati. Per ognuno, chiedi il path locale:

> Il report fa riferimento a questi documenti:
> - **AFU**: `<nome file originale>`
> - **Mockup**: `<nome file originale>`
> - [altri file]
>
> Dammi i path locali di quelli che hai disponibile. Se non li hai tutti, non è un problema — lavoreremo dal gap report che contiene già i dettagli estratti.

### Domanda 4 — Identità sviluppatore

> Chi sei? Il piano elenca questi sviluppatori:
> [lista degli sviluppatori dal piano con ruolo e seniority]
>
> Dimmi quale sei.

Dopo l'identificazione, mostra le task assegnate a quello sviluppatore con il loro stato attuale (dal file di progresso se esiste, altrimenti tutte a 0%).

### Riepilogo e conferma

> Riepilogo:
> - Sviluppatore: [nome] ([ruolo/area] [seniority])
> - Repository disponibili:
>   [per ognuna: Nome (SIGLA) → path locale]
> - Documentazione disponibile: [lista con path locali]
> - Task assegnate: [N task]
>
> [Tabella task con ID, nome, dipendenze, stato attuale]
>
> Confermo e procedo?

Procedi solo dopo la conferma.

---

## Fase 2 — Gestione del File di Progresso

### Se il file non esiste — Crealo

Crea il file `PROGRESS.md` nella stessa cartella del Piano (es. `$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.md`), con questa struttura:

```
# Progresso Implementazione [Nome Piano]

Data creazione: `<data>`
Ultimo aggiornamento: `<data e ora>`

## Riepilogo

| Metrica | Valore |
|---|---|
| Task totali | N |
| Completate | 0 |
| In corso | 0 |
| Da iniziare | N |
| Bloccate | 0 |
| Progresso complessivo | 0% |

## Stato Task

| ID | Attività | Owner | Progresso | Stato | Branch | Note |
|---|---|---|---:|---|---|---|
| T-001 | [Nome] | [Dev] | 0% | Da iniziare | — | — |
| T-002 | [Nome] | [Dev] | 0% | Da iniziare | — | — |
[tutte le task dal piano]

## Log Attività

[Cronologia delle attività svolte, aggiornata automaticamente]

### <data>
- [Nessuna attività registrata]
```

### Se il file esiste — Leggilo e sincronizza

Leggi il file di progresso e verifica che sia allineato con il piano. Se ci sono task nel piano che mancano dal progresso (es. il piano è stato aggiornato), aggiungile. Mostra allo sviluppatore lo stato attuale delle sue task.

### Aggiornamento del progresso

Aggiorna il file di progresso a ogni cambio di stato significativo:
- Quando una task passa a "In corso"
- Quando un sottoagente completa una parte del lavoro (aggiorna la %)
- Quando una task viene completata
- Quando una task risulta bloccata

Aggiorna sempre il campo "Ultimo aggiornamento" e aggiungi una riga al Log Attività.

**Dopo ogni aggiornamento del PROGRESS.md, esegui commit + push sulla repo profili**, in modo che il progresso sia immediatamente visibile a tutti gli altri sviluppatori:

```bash
git -C "$GIT_REPO_PATH" add "<profilo>/plans/in-progress/<data>_<nome>/PROGRESS.md"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-progress] <task-id> -> <progresso>%"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Fase 3 — Lavorazione Task

### Selezione della prossima task

Presenta le task assegnate allo sviluppatore in ordine di priorità (P0 > P1 > P2), rispettando le wave del piano:

> Le tue task assegnate:
>
> | # | ID | Attività | Priorità | Wave | Dipendenze | Stato |
> |---|---|---|---|---|---|---|
> | 1 | T-001 | ... | P0 | Wave 1 | Nessuna | Da iniziare |
> | 2 | T-005 | ... | P0 | Wave 2 | T-001 | Da iniziare |
>
> Vuoi procedere con **T-001 — [nome]**?

Aspetta la conferma dello sviluppatore prima di iniziare qualsiasi lavoro.

**Nota sulle merge task (T-MERGE-*)**: le merge task sono task speciali che non richiedono implementazione di codice. Quando l'executor incontra una merge task, guida lo sviluppatore attraverso il processo di merge: (1) merge del branch sorgente nel branch base, (2) verifica che la build compili correttamente, (3) mark come completata. Non vengono lanciati sottoagenti per le merge task.

### Lettura progresso

Prima di leggere il file di progresso, sincronizza la repo profili:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
```

Leggi il PROGRESS.md dalla cartella del Piano in `$BASE_PATH/in-progress/<data>_<nome>/PROGRESS.md`.

Tutti gli sviluppatori scrivono nello stesso file nella repo centralizzata, quindi il progresso e' sempre aggiornato dopo il pull.

### Controllo dipendenze

Prima di iniziare una task, verifica le dipendenze usando il **file di progresso** (dopo il pull e' gia' aggiornato con il lavoro di tutti gli sviluppatori).

La regola e' semplice: una dipendenza e' soddisfatta quando il suo stato nel file di progresso e' **"Completata"**. Non serve nessun controllo sugli stream — le dipendenze cross-stream sono gestite tramite merge task esplicite inserite nel piano da sdlc-analyzer.

Logica di verifica per ogni dipendenza:

1. Esegui il pull della repo profili (se non gia' fatto in questa sessione)
2. Trova la task dipendenza nel file di progresso
3. Verifica che lo stato sia "Completata"
4. Se si', la dipendenza e' soddisfatta — procedi

Se tutte le dipendenze sono soddisfatte, procedi normalmente.

Se una dipendenza non e' soddisfatta, avvisa e blocca:

> La task **T-005** dipende da **T-003**.
> T-003 risulta ancora [stato attuale nel file di progresso]. Non posso procedere finche' non e' completata.
>
> Vuoi:
> 1. Passare a un'altra task senza dipendenze bloccanti?
> 2. Attendere? (ti chiedero' di controllare il progresso piu' tardi)

### Creazione branch

Quando la task e' confermata e le dipendenze sono soddisfatte, crea i branch in TUTTE le repo di codice coinvolte. (La repo profili non riceve mai feature branch — lavora sempre su `main`.)

1. Identifica le repo di codice coinvolte dalla colonna **Area** del piano (es. BE, FE, BE+FE, EM, DM) e i loro path locali forniti in Fase 1.
2. **Determina il nome del branch:**
   - Se il piano ha una colonna **Branch** con un valore per questa task → usa quel nome esatto
   - Se il piano NON ha colonna Branch (retrocompatibilita') → genera il nome: `feature/<task-name>`
3. **Per ogni repo di codice coinvolta**:
   - Verifica il branch corrente nella repo:
     ```bash
     git -C <path-repo-codice> branch --show-current
     ```
   - Crea il feature branch dal base branch del piano:
     ```bash
     git -C <path-repo-codice> checkout -b <nome-branch>
     ```
   - Comunica al developer:
     > Branch creato nella repo **<Nome> (<SIGLA>)**:
     > `<nome-branch>` da `<branch-corrente>`
     > Path: `<path-repo-codice>`

4. Aggiorna il file di progresso (nella repo profili) con il nome del branch e lo stato "In corso", poi committa e pusha la repo profili come da template della sezione "Aggiornamento del progresso".

### Esecuzione con sottoagenti

Per ogni task, l'agente principale (tu) fai da coordinatore. Delega il lavoro concreto a sottoagenti Claude, ognuno con un compito specifico e ben delimitato.

#### Come scomporre una task in sotto-lavori

Leggi la descrizione della task dal piano e dal gap report. Identifica i sotto-lavori necessari, ad esempio:

- Creazione/modifica entità e migration
- Implementazione logica di servizio
- Implementazione controller/API
- Implementazione componenti frontend
- Scrittura test
- Documentazione del codice

#### Come istruire un sottoagente

Ogni sottoagente deve ricevere un prompt autosufficiente che include:

1. **Contesto del progetto** — path del codebase, struttura del progetto, pattern e convenzioni in uso
2. **Cosa fare** — descrizione precisa del lavoro, con riferimento ai file specifici da creare/modificare
3. **Riferimenti** — estratti rilevanti dal gap report (cosa richiede l'AFU, cosa esiste, cosa manca)
4. **Convenzioni** — naming, struttura package, stile di codice del progetto (osservato dai file esistenti)
5. **Vincoli** — cosa NON fare, limiti di scope, attenzioni specifiche dalla task
6. **Output atteso** — file da creare/modificare, test da scrivere, documentazione da aggiungere
7. **Test richiesti** — specifica esplicitamente che il sottoagente deve scrivere test per il suo lavoro, compresi edge case. Elenca gli scenari di test attesi: happy path, input vuoti/null, boundary values, casi di errore. Il sottoagente non puo' dichiarare il lavoro completo senza test.

Esempio di dispatch a un sottoagente:

```
Implementa la seguente modifica nel codebase backend.

Codebase: <path locale BE>
Task: T-003 — Implementare il repository e le query per la lista pratiche monitoraggio

Contesto:
- Il progetto usa Spring Boot con JPA/Hibernate
- Le entità esistenti seguono il pattern in <path>/domain/
- I repository seguono il pattern in <path>/repository/
- [altri pattern osservati]

Cosa fare:
- Creare il repository MonitoringPracticeRepository in <package>
- Implementare le query per: [lista dal gap report]
- Seguire lo stesso pattern di [file analogo esistente]

File di riferimento (leggi questi per capire le convenzioni):
- <path>/repository/ExistingRepository.java
- <path>/domain/ExistingEntity.java

Requisiti dal gap report:
[estratto rilevante dal gap report]

Scrivi anche i test unitari seguendo il pattern in <path>/test/.
Documenta il codice con Javadoc conciso dove il "perché" non è ovvio.
```

#### Parallelizzazione

Se i sotto-lavori sono indipendenti tra loro (es. entità e componente FE), lancia più sottoagenti in parallelo. Se sono dipendenti (es. prima l'entità, poi il repository che la usa), lanciali in sequenza.

#### Verifica del lavoro dei sottoagenti

Dopo che ogni sottoagente completa il suo lavoro, esegui una verifica in 3 fasi:

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

Se trovi discrepanze:

> **Verifica coerenza** — La task richiede [X] ma il codice implementa [Y].
> Lancio un sottoagente di correzione per allineare.

Istruisci un nuovo sottoagente per correggere. Ripeti la Fase B dopo la correzione.

**Fase C — Riesame finale (second look)**

Dopo che le Fasi A e B sono superate, fai un ultimo passaggio con occhio critico:

1. **Rileggere il codice prodotto dall'inizio alla fine** — non fidarti del riepilogo del sottoagente, leggi il codice effettivo
2. **Cercare assunzioni nascoste** — il sottoagente ha fatto assunzioni non esplicite nei requisiti? Ha hardcodato valori che dovrebbero essere configurabili?
3. **Verificare che i test testino realmente** — un test che non asserisce nulla utile e' peggio di nessun test. Ogni test deve avere asserzioni specifiche e significative
4. **Controllare i nomi** — le variabili, i metodi, le classi seguono le convenzioni del progetto?

Se trovi problemi in questa fase, correggi con un sottoagente dedicato e ripeti la Fase C.

Solo quando TUTTE e 3 le fasi sono superate il sotto-step e' considerato verificato.

### Suggerimento commit

L'agente non deve mai committare autonomamente. Quando il lavoro di un sotto-step e' completo e verificato, avvisa lo sviluppatore con suggerimenti separati per ogni repo coinvolta.

**Se la task coinvolge una sola repo di codice:**

> Il lavoro su [descrizione sotto-step] e' completo e verificato:
> - [lista file creati/modificati]
> - Test: [passano / N test, tutti verdi]
> - Build: [compila]
>
> Sarebbe un buon momento per creare un commit. Suggerisco:
> ```
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> Dopo il commit, pusha il branch per rendere il progresso visibile agli altri:
> ```
> git push origin <nome-branch>
> ```
>
> **Repo profili** — il progresso e' gia' stato aggiornato e pushato automaticamente.
>
> Quando hai committato e pushato, dimmelo e proseguo.

**Se la task coinvolge piu' repo di codice:**

> Il lavoro su [descrizione sotto-step] e' completo e verificato.
>
> **Repo <Nome 1> (<SIGLA>)** — `<path-repo-1>`:
> - [lista file creati/modificati nella repo 1]
> Suggerisco:
> ```
> cd <path-repo-1>
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> **Repo <Nome 2> (<SIGLA>)** — `<path-repo-2>`:
> - [lista file creati/modificati nella repo 2]
> Suggerisco:
> ```
> cd <path-repo-2>
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> Dopo i commit, pusha entrambi i branch:
> ```
> cd <path-repo-1> && git push origin <nome-branch>
> cd <path-repo-2> && git push origin <nome-branch>
> ```
>
> **Repo profili** — il progresso e' gia' stato aggiornato e pushato automaticamente.
>
> Quando hai committato e pushato, dimmelo e proseguo.

Aspetta la conferma prima di proseguire con il sotto-step successivo.

### Completamento task

Una task e' completata solo quando TUTTI questi criteri sono soddisfatti e verificati:

1. **Requisiti** — tutto cio' che il gap report e il piano richiedono per questa task e' implementato. Per ogni requisito elencato nella task, esiste codice che lo soddisfa.
2. **Codice completo** — nessun placeholder, nessun TODO, nessuna implementazione parziale
3. **Test completi** — test scritti e tutti verdi, con copertura di:
   - Happy path per ogni funzionalita' implementata
   - Edge case (input vuoti, null, boundary values, liste vuote, overflow)
   - Casi di errore (fallimenti di dipendenze, input malformati, stati invalidi)
4. **Build** — il progetto compila senza errori
5. **Coerenza verificata** — la Fase B (verifica di coerenza col requisito) e' stata superata
6. **Riesame superato** — la Fase C (second look) e' stata superata senza trovare problemi

**Ciclo di verifica finale:**

Prima di dichiarare la task completata, esegui questo ciclo:

1. Elenca ogni requisito dalla descrizione della task nel piano
2. Per ognuno, indica il file e la riga che lo implementa
3. Per ognuno, indica il test che lo verifica
4. Se un requisito non ha implementazione O non ha test → la task NON e' completa

> ## Verifica completamento T-001 — [nome]
>
> | # | Requisito | Implementato | File | Test | Verificato |
> |---|---|---|---|---|---|
> | 1 | [requisito dal piano] | Si | `path/file.java:42` | `TestClass#testMethod` | Si |
> | 2 | [requisito dal piano] | Si | `path/file.java:78` | `TestClass#testEdgeCase` | Si |
> | 3 | [requisito dal piano] | **No** | — | — | — |
>
> **Esito**: [COMPLETA / INCOMPLETA — mancano i requisiti #3]

Se l'esito e' INCOMPLETA, lancia un sottoagente per implementare i requisiti mancanti, poi ripeti il ciclo.

Se l'esito e' COMPLETA:

> La task **T-001 — [nome]** e' completa e verificata.
>
> Checklist:
> - [x] Requisiti implementati: [N/N coperti]
> - [x] Test: [N test totali, di cui X happy path, Y edge case, Z error case — tutti verdi]
> - [x] Build: compila
> - [x] Coerenza verificata: ogni requisito ha implementazione e test corrispondente
> - [x] Riesame superato: nessun problema trovato nel second look
>
> Aggiorno il file di progresso a 100% — stato: **Completata**.

Aggiorna il file di progresso: stato "Completata", progresso 100%, note con riepilogo del lavoro svolto, log attività aggiornato.

Dopo aver aggiornato il progresso, proponi la prossima task disponibile:

> Vuoi procedere con la prossima task **T-005 — [nome]**?

### Completamento di tutte le task — Spostamento in `plans/done/`

Dopo aver completato una task, verifica nel file di progresso se **tutte** le task sono in stato "Completata" **E** se tutti i bug sono chiusi.

**Condizioni di chiusura plan** (Fase 2c, due ondate test in standalone):

| Modalita' | Condizioni (tutte vere) |
|---|---|
| Standalone (v2 template con `origine`) | (a) tutte le task = `Completata` ∧ (b) `bug_tecnici_aperti = 0` ∧ (c) `bug_funzionali_aperti = 0` |
| Legacy (no colonna origine) | (a) tutte le task = `Completata` ∧ (b) `bug_aperti = 0` (counter unico, retrocompat) |

Lettura counter bug da `BUG_REPORT.md` (popolato da `sdlc-debug` — vedi sezione "Lista Bug" nello SKILL.md di sdlc-debug):

```bash
BUG_REPORT="$BASE_PATH/in-progress/<plan>/BUG_REPORT.md"
if [ -f "$BUG_REPORT" ]; then
  # Standalone v2
  TEC_OPEN=$(grep -oP '^- `bug_tecnici_aperti`:\s*\K\d+' "$BUG_REPORT" || echo 0)
  FUNC_OPEN=$(grep -oP '^- `bug_funzionali_aperti`:\s*\K\d+' "$BUG_REPORT" || echo 0)
  # Legacy fallback
  TOTAL_OPEN=$(grep -oP '^- `bug_aperti`:\s*\K\d+' "$BUG_REPORT" || echo 0)
fi
```

Se tutte le condizioni sono soddisfatte:

```bash
git -C "$GIT_REPO_PATH" mv "$BASE_PATH/in-progress/<YYYY-MM-DD>_<nome>/" "$BASE_PATH/done/"
git -C "$GIT_REPO_PATH" add .
git -C "$GIT_REPO_PATH" commit -m "[sdlc-executor] <nome>: tutte le task completate + tutti i bug chiusi, spostato in done"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

Comunica:

> Tutte le task del piano sono completate **e** tutti i bug (tecnici + funzionali) sono chiusi. Cartella del Piano spostata in `$BASE_PATH/done/`.

**Flag `--no-auto-close`**: se TL/PM vuole mantenere il plan aperto (soak in produzione, audit, ulteriori cicli di testing), supporta l'override esplicito che disabilita lo spostamento automatico in `done/`. In quel caso comunica:

> Le condizioni di chiusura sono soddisfatte ma `--no-auto-close` e' attivo. Il plan resta in `in-progress/`. Spostalo manualmente in `done/` quando vuoi.

### Log informativo playbook test (modalita' standalone)

All'avvio di una task UI/frontend (rilevata dal `repository` o dallo `stream` della task — es. sigla `FE`, `MOBILE`, `WEB`), se esiste `$BASE_PATH/<stato>/<plan>/tests/playbook.md` o `playbook.xlsx`, logga un avviso informativo (no enforcement, solo segnale al developer):

> Playbook test funzionale disponibile in `tests/playbook.md` + `tests/playbook.xlsx` (generato da Solaria in F1c). Sara' eseguito **manualmente** dal team funzionale in F2c ondata (b), dopo che i test tecnici team tech avranno passato il quality gate (a). Tieni d'occhio gli scenari di accettazione li' definiti mentre implementi i flussi UI.

Non bloccare l'esecuzione su questo log — e' solo orientativo.

---

## Fase 4 — Gestione Situazioni Speciali

### Task bloccata

Se durante la lavorazione emerge un blocco (dipendenza non prevista, ambiguità nell'AFU, problema tecnico):

1. Segna la task come "Bloccata" nel progresso con la motivazione
2. Avvisa lo sviluppatore e proponi alternative:

> La task **T-003** è bloccata: [motivazione].
>
> Opzioni:
> 1. Passare a un'altra task non bloccata
> 2. Provare a risolvere il blocco (descrivi come)
> 3. Segnalare il blocco e fermarsi

### Ripresa del lavoro

Quando la skill viene invocata con un file di progresso esistente:

1. Leggi lo stato attuale
2. Identifica le task "In corso" dello sviluppatore — riprendi da lì
3. Identifica le task "Bloccate" — verifica se il blocco è stato risolto
4. Mostra il riepilogo e chiedi come procedere

### Conflitti e problemi di merge

Se il lavoro su un branch richiede aggiornamenti dal branch base (es. una dipendenza è stata mergiata):

> Il branch base `feature/[nome]` ha ricevuto aggiornamenti dalla task **T-002**.
> Ti consiglio di fare un merge/rebase dal branch base prima di continuare.
>
> Vuoi che ti guidi nel processo?

Non eseguire merge o rebase automaticamente — guida lo sviluppatore passo per passo.

---

## Regole Fondamentali

1. **Mai committare autonomamente sulle repo di codice** — suggerisci sempre il commit e aspetta che lo sviluppatore lo faccia. La repo profili e' l'unica eccezione: per gli aggiornamenti del PROGRESS.md e per gli spostamenti tra `plans/todo`, `plans/in-progress`, `plans/done`, esegui commit + push automatico per garantire visibilita' a tutti gli sviluppatori.
2. **Mai procedere senza conferma** — tra una task e l'altra, tra un sotto-step e l'altro, chiedi sempre
3. **Mai ignorare le dipendenze** — se una dipendenza non è soddisfatta, blocca e avvisa
4. **Aggiorna sempre il progresso** — il file di progresso è la fonte di verità condivisa tra tutti gli agenti
5. **Verifica prima di dichiarare completo** — test verdi, build che compila, requisiti coperti
6. **Il sottoagente implementa, tu coordini** — non implementare codice direttamente, delega ai sottoagenti e verifica il loro lavoro
