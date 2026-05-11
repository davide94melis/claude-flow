---
name: br-executor
description: Esegue i task del piano di implementazione generato da br-analyzer. Ogni sviluppatore/agente usa questa skill per lavorare le proprie task assegnate, con sottoagenti Claude che implementano codice e test mentre l'agente principale coordina, verifica e traccia il progresso. Supporta qualsiasi composizione di repository — il progetto può avere una o più repo con nomi arbitrari. Usa questa skill quando l'utente dice "lavora il task", "inizia a lavorare", "esegui il piano", "sono lo sviluppatore X", "devo lavorare le mie task", "task executor", "esegui task", o qualsiasi variazione che implichi l'inizio della lavorazione di task da un piano di implementazione BR. Attivala anche quando l'utente menziona un file di progresso o chiede di riprendere il lavoro su task assegnate.
---

# BR Executor — Esecuzione Task da Piano di Implementazione

Questa skill è il complemento operativo di `br-analyzer`. Mentre `br-analyzer` analizza un BR e genera gap report + piano di implementazione, questa skill permette a ogni sviluppatore (assistito da un agente Claude Code) di eseguire le proprie task assegnate.

L'agente principale coordina il lavoro, delega l'implementazione a sottoagenti, verifica i risultati e tiene aggiornato il file di progresso.

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

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — File del piano

Prima di chiedere, verifica se esiste la struttura `plans/` nella working directory. Cerca cartelle BR nelle tre aree:

```bash
ls -d plans/todo/*/ plans/in-progress/*/ plans/done/*/ 2>/dev/null
```

**Se trovi cartelle BR**, elencale e proponi:

> Ho trovato queste cartelle BR:
> - `plans/todo/2026-04-28_booking-v2/` (contiene GAP_REPORT_BR.md, PIANO_IMPLEMENTAZIONE_BR.md)
> - `plans/in-progress/2026-04-15_monitoraggio/` (contiene PROGRESSO_BR.md)
>
> Quale vuoi lavorare? Oppure dammi i path manualmente.

**Se trovi file flat** (retrocompatibilita' con vecchio formato):

> Ho trovato questi file nella cartella `plans/`:
> - `plans/todo/GAP_REPORT_BR_2026-04-24.md`
> - `plans/todo/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
>
> Uso questi? Oppure dammi i path manualmente.

**Se non trovi nulla**, chiedi:

> Per iniziare mi servono i file generati da br-analyzer:
> 1. **Gap Report** — il file `GAP_REPORT_BR.md`
> 2. **Piano di Implementazione** — il file `PIANO_IMPLEMENTAZIONE_BR.md`
> 3. **File di Progresso** — se esiste gia' un file `PROGRESSO_BR.md`, dammi il path. Se non esiste ancora, lo creo io.

Leggi tutti i file forniti. Estrai dal gap report e dal piano:
- La lista di tutti i codebase menzionati (con i path originali)
- La lista di tutti i file di documentazione menzionati (con i path originali)
- La lista completa delle task con owner, dipendenze e stato

### Spostamento in `plans/in-progress/`

Quando lo sviluppatore conferma e la lavorazione sta per iniziare, sposta l'intera cartella del BR da `plans/todo/` a `plans/in-progress/` (se non e' gia' li'):

```bash
mkdir -p plans/in-progress
mv "plans/todo/<YYYY-MM-DD>_<nome>/" "plans/in-progress/" 2>/dev/null
```

Se stai lavorando con file flat (retrocompatibilita'), sposta i singoli file come prima:

```bash
mkdir -p plans/in-progress
mv plans/todo/GAP_REPORT_BR_*.md plans/in-progress/ 2>/dev/null
mv plans/todo/PIANO_IMPLEMENTAZIONE_BR_*.md plans/in-progress/ 2>/dev/null
```

Il file di progresso viene creato (o cercato) dentro la cartella del BR in `plans/in-progress/`.

### Domanda 2 — Path dei codebase locali

Dal report e dal piano, estrai tutti i nomi e le sigle dei codebase/repository referenziati. Per ognuno, chiedi il path locale:

> I file di br-analyzer fanno riferimento a queste repository:
> [per ogni repo trovata nei file:]
> - **<Nome> (<SIGLA>)** — path originale: `<path dal report>`
>
> Siccome lavori su un PC diverso, dammi i path locali di ogni repository che hai disponibile.
> Se una repo non ti serve per le tue task, dimmelo.

### Domanda 3 — Path della documentazione locale

Dal report, estrai i nomi dei file di documentazione referenziati. Per ognuno, chiedi il path locale:

> Il report fa riferimento a questi documenti:
> - **BR**: `<nome file originale>`
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

Crea il file `PROGRESSO_BR.md` nella stessa cartella del BR (es. `plans/in-progress/<YYYY-MM-DD>_<nome>/PROGRESSO_BR.md`), con questa struttura:

```
# Progresso Implementazione [Nome BR]

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

### Lettura progresso aggregata (cross-branch)

Prima di leggere il file di progresso per qualsiasi operazione (controllo dipendenze, stato task), esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task, non solo quelle visibili sul branch corrente.

Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch. Senza aggregazione, il progresso degli altri non e' visibile.

1. `git fetch origin` per sincronizzare i branch remoti

2. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre:
   - Gli ID di tutte le task (T-001, T-003, T-005, ...)
   - Se il piano ha una colonna **Branch** nel backlog: estrai i nomi branch di ogni task
   - Il nome del BR dalla cartella (es. `2026-05-04_monitoring` → `monitoring`)

3. **Trova i branch remoti da controllare:**
   - **Se il piano ha colonna Branch**: usa direttamente i nomi branch elencati nel piano. Per ogni branch con valore diverso da `—`, verifica che esista come remoto:
     ```bash
     git branch -r | grep "<branch-name>"
     ```
   - **Se il piano NON ha colonna Branch** (retrocompatibilita' con piani pre-esistenti): cerca tutti i branch remoti che contengono il nome del BR:
     ```bash
     git branch -r | grep -i "feature/<nome-br>"
     ```

4. Per ogni branch trovato, prova a leggere il PROGRESSO da 3 percorsi possibili (il file puo' essere in posizioni diverse a seconda dello stato):
   ```bash
   git show origin/<branch>:plans/in-progress/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/todo/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/done/<cartella-br>/PROGRESSO_BR.md
   ```
   Usa il primo che funziona. Se nessuno funziona, skip quel branch.

5. Leggi anche il PROGRESSO dal branch base del piano (con gli stessi 3 percorsi). Se non esiste su nessun percorso, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

6. Aggrega per task con la regola **"highest progress wins"**:
   - Per ogni task, confronta le versioni da tutti i branch (incluso il baseline)
   - Se una versione mostra "Completata" (100%), vince sempre
   - Altrimenti, prendi la versione con il progresso % piu' alto
   - Se due versioni hanno lo stesso %, prendi quella con lo stato piu' avanzato (In corso > Da iniziare)

7. Ricalcola le metriche di riepilogo (task completate, in corso, progresso complessivo %) dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning:

> Impossibile sincronizzare con il remoto. Il progresso mostrato potrebbe non essere aggiornato.

Usa la vista aggregata per tutte le operazioni successive (controllo dipendenze, selezione task).

### Controllo dipendenze

Prima di iniziare una task, verifica le dipendenze usando la **vista aggregata** (vedi sezione "Lettura progresso aggregata" sopra). NON usare il file di progresso locale — potrebbe non riflettere il lavoro completato da altri sviluppatori sui loro branch.

La regola e' semplice: una dipendenza e' soddisfatta quando il suo stato nella vista aggregata e' **"Completata"**. Non serve nessun controllo sugli stream — le dipendenze cross-stream sono gestite tramite merge task esplicite inserite nel piano da br-analyzer.

Logica di verifica per ogni dipendenza:

1. Esegui la lettura progresso aggregata (se non gia' fatta in questa sessione)
2. Trova la task dipendenza nella vista aggregata
3. Verifica che lo stato sia "Completata"
4. Se si', la dipendenza e' soddisfatta — procedi

Se tutte le dipendenze sono soddisfatte, procedi normalmente.

Se una dipendenza non e' soddisfatta, avvisa e blocca:

> La task **T-005** dipende da **T-003**.
> T-003 risulta ancora [stato attuale nella vista aggregata]. Non posso procedere finche' non e' completata.
>
> Vuoi:
> 1. Passare a un'altra task senza dipendenze bloccanti?
> 2. Attendere? (ti chiedero' di controllare il progresso piu' tardi)

### Creazione branch

Quando la task e' confermata e le dipendenze sono soddisfatte, crea i branch in TUTTE le repo coinvolte.

1. Identifica le repo coinvolte dalla colonna **Area** del piano (es. BE, FE, BE+FE, EM, DM)
2. **Determina il nome del branch:**
   - Se il piano ha una colonna **Branch** con un valore per questa task → usa quel nome esatto
   - Se il piano NON ha colonna Branch (retrocompatibilita') → genera il nome: `feature/<task-name>`
3. **Repo del piano** (la repo corrente, dove stai lavorando):
   - Verifica il branch corrente e lo stato del repository
   - Crea il branch dal base branch del piano:
     > Creo il branch `<nome-branch>` dal branch `<branch-base>`.
   - Aggiorna il file di progresso con il nome del branch e lo stato "In corso"

4. **Per ogni altra repo coinvolta** (identificata dalla colonna Area e dai path locali forniti in Fase 1):
   - Verifica il branch corrente nella repo esterna:
     ```bash
     git -C <path-repo-esterna> branch --show-current
     ```
   - Crea il feature branch nella repo esterna con lo stesso nome:
     ```bash
     git -C <path-repo-esterna> checkout -b <nome-branch>
     ```
   - Comunica al developer:
     > Branch creato anche nella repo **<Nome> (<SIGLA>)**:
     > `<nome-branch>` da `<branch-corrente>`
     > Path: `<path-repo-esterna>`

4. Se la task riguarda SOLO la repo del piano (es. Area = "BE" e il piano sta in BE), crea un solo branch come al punto 2.

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

#### Come istruire un sottoagente

Ogni sottoagente deve ricevere un prompt autosufficiente che include:

1. **Contesto del progetto** — path del codebase, struttura del progetto, pattern e convenzioni in uso
2. **Cosa fare** — descrizione precisa del lavoro, con riferimento ai file specifici da creare/modificare
3. **Riferimenti** — estratti rilevanti dal gap report (cosa richiede il BR, cosa esiste, cosa manca)
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

**Se il profilo progetto e' disponibile:**

Delega la verifica all'agente `br-verifier` (leggendo le sue istruzioni da `~/.claude/agents/br-verifier.md`). Costruisci un prompt che includa:

1. **Requisiti** — descrizione della task dal piano e dal gap report
2. **File modificati** — lista completa dei file creati/modificati dal sottoagente
3. **Risultati test** — esegui prima la suite di test e passa l'output
4. **Convenzioni dal profilo** — `test_naming`, `base_entity`, `package_structure`, `commit_convention`

Lancia il verifier e attendi il verdict. Se il verdict e' FAIL, leggi i dettagli e lancia un sottoagente di correzione. Ripeti la verifica. Solo quando il verdict e' PASS, il sotto-step e' considerato verificato.

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

**Se la task coinvolge solo la repo del piano:**

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
> Quando hai committato e pushato, dimmelo e proseguo.

**Se la task coinvolge piu' repo:**

> Il lavoro su [descrizione sotto-step] e' completo e verificato.
>
> **Repo <Nome Piano> (<SIGLA>)** — `<path-repo-piano>`:
> - [lista file creati/modificati nella repo piano, incluso PROGRESSO_BR.md]
> Suggerisco:
> ```
> git add [file specifici]
> git commit -m "[br-progress] <task-id> -> <progresso>%"
> ```
>
> **Repo <Nome Esterna> (<SIGLA>)** — `<path-repo-esterna>`:
> - [lista file creati/modificati nella repo esterna]
> Suggerisco:
> ```
> cd <path-repo-esterna>
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> Dopo i commit, pusha entrambi i branch:
> ```
> git push origin <nome-branch>
> cd <path-repo-esterna> && git push origin <nome-branch>
> ```
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

Dopo aver completato una task, verifica nel file di progresso se **tutte** le task (non solo quelle dello sviluppatore corrente, ma tutte quelle nel piano) sono in stato "Completata". Se si':

```bash
mkdir -p plans/done
mv "plans/in-progress/<YYYY-MM-DD>_<nome>/" "plans/done/" 2>/dev/null
```

Se stai lavorando con file flat (retrocompatibilita'):

```bash
mkdir -p plans/done
mv plans/in-progress/GAP_REPORT_BR_*.md plans/done/
mv plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_*.md plans/done/
mv plans/in-progress/PROGRESSO_BR_*.md plans/done/
```

Comunica:

> Tutte le task del piano sono completate. Cartella del BR spostata in `plans/done/`.

---

## Fase 4 — Gestione Situazioni Speciali

### Task bloccata

Se durante la lavorazione emerge un blocco (dipendenza non prevista, ambiguità nel BR, problema tecnico):

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

1. **Mai committare autonomamente** — suggerisci sempre il commit e aspetta che lo sviluppatore lo faccia
2. **Mai procedere senza conferma** — tra una task e l'altra, tra un sotto-step e l'altro, chiedi sempre
3. **Mai ignorare le dipendenze** — se una dipendenza non è soddisfatta, blocca e avvisa
4. **Aggiorna sempre il progresso** — il file di progresso è la fonte di verità condivisa tra tutti gli agenti
5. **Verifica prima di dichiarare completo** — test verdi, build che compila, requisiti coperti
6. **Il sottoagente implementa, tu coordini** — non implementare codice direttamente, delega ai sottoagenti e verifica il loro lavoro
