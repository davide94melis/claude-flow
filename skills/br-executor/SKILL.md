---
name: br-executor
description: Esegue i task del piano di implementazione generato da br-analyzer. Ogni sviluppatore/agente usa questa skill per lavorare le proprie task assegnate, con sottoagenti Claude che implementano codice e test mentre l'agente principale coordina, verifica e traccia il progresso. Usa questa skill quando l'utente dice "lavora il task", "inizia a lavorare", "esegui il piano", "sono lo sviluppatore X", "devo lavorare le mie task", "task executor", "esegui task", o qualsiasi variazione che implichi l'inizio della lavorazione di task da un piano di implementazione BR. Attivala anche quando l'utente menziona un file di progresso o chiede di riprendere il lavoro su task assegnate.
---

# BR Executor — Esecuzione Task da Piano di Implementazione

Questa skill è il complemento operativo di `br-analyzer`. Mentre `br-analyzer` analizza un BR e genera gap report + piano di implementazione, questa skill permette a ogni sviluppatore (assistito da un agente Claude Code) di eseguire le proprie task assegnate.

L'agente principale coordina il lavoro, delega l'implementazione a sottoagenti, verifica i risultati e tiene aggiornato il file di progresso.

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — File del piano

Prima di chiedere, verifica se esiste la struttura `plans/` nella working directory. Se trovi file in `plans/todo/`, `plans/in-progress/` o `plans/done/`, proponili direttamente:

> Ho trovato questi file nella cartella `plans/`:
> - `plans/todo/GAP_REPORT_BR_2026-04-24.md`
> - `plans/todo/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
>
> Uso questi? Oppure dammi i path manualmente.

Se non trovi nulla, chiedi:

> Per iniziare mi servono i file generati da br-analyzer:
> 1. **Gap Report** — il file `GAP_REPORT_BR_*.md`
> 2. **Piano di Implementazione** — il file `PIANO_IMPLEMENTAZIONE_BR_*.md`
> 3. **File di Progresso** — se esiste già un file `PROGRESSO_BR_*.md`, dammi il path. Se non esiste ancora, lo creo io.

Leggi tutti i file forniti. Estrai dal gap report e dal piano:
- La lista di tutti i codebase menzionati (con i path originali)
- La lista di tutti i file di documentazione menzionati (con i path originali)
- La lista completa delle task con owner, dipendenze e stato

### Spostamento in `plans/in-progress/`

Quando lo sviluppatore conferma e la lavorazione sta per iniziare, sposta report e piano da `plans/todo/` a `plans/in-progress/` (se non sono già lì):

```bash
mkdir -p plans/in-progress
mv plans/todo/GAP_REPORT_BR_*.md plans/in-progress/ 2>/dev/null
mv plans/todo/PIANO_IMPLEMENTAZIONE_BR_*.md plans/in-progress/ 2>/dev/null
```

Il file di progresso viene creato (o cercato) direttamente in `plans/in-progress/`.

### Domanda 2 — Path dei codebase locali

Dal report e dal piano, estrai i nomi dei codebase referenziati (es. BE, FE, Document Manager, Email Manager). Per ognuno, chiedi il path locale:

> I file di br-analyzer fanno riferimento a questi codebase:
> - **Backend (BE)** — path originale: `<path dal report>`
> - **Frontend (FE)** — path originale: `<path dal report>`
> - [altri se presenti]
>
> Siccome lavori su un PC diverso, dammi i path locali di ogni codebase che hai disponibile.
> Se un codebase non ti serve per le tue task, dimmelo.

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
> - Sviluppatore: [nome] ([ruolo] [seniority])
> - Codebase disponibili: [lista con path locali]
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

Crea il file `PROGRESSO_BR_<YYYY-MM-DD>.md` nella stessa directory del piano di implementazione, con questa struttura:

```
# Progresso Implementazione [Nome BR]

Data creazione: `<data>`
Ultimo aggiornamento: `<data e ora>`

## Riepilogo

| Metrica | Valore |
|---|---|
| Task totali | N |
| Completate | 0 |
| Mergiate | 0 |
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
- Quando una task viene mergiata
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

### Controllo dipendenze

Prima di iniziare una task, verifica le dipendenze dal file di progresso. La regola di sblocco dipende dalla relazione tra gli owner:

**Stesso owner** — La task dipendente è assegnata allo stesso sviluppatore della dipendenza. Il codice è già disponibile localmente (stesso PC, branch accessibile). La dipendenza si sblocca quando lo stato è **"Completata"** (o "Mergiata").

**Owner diverso** — La task dipendente è assegnata a uno sviluppatore diverso. Il codice della dipendenza non è disponibile localmente finché il branch non viene mergiato nel branch base condiviso. La dipendenza si sblocca solo quando lo stato è **"Mergiata"**.

Logica di verifica per ogni dipendenza:

1. Trova la task dipendenza nel progresso
2. Confronta l'owner della dipendenza con l'owner della task corrente
3. Se **stesso owner**: la dipendenza è soddisfatta se stato è "Completata" o "Mergiata"
4. Se **owner diverso**: la dipendenza è soddisfatta solo se stato è "Mergiata"

Se tutte le dipendenze sono soddisfatte, procedi normalmente.

Se una dipendenza non è soddisfatta, avvisa e blocca:

> La task **T-005** dipende da **T-003** (owner: [nome owner T-003]).
>
> [Se stesso owner e task non completata:]
> T-003 risulta ancora [stato attuale]. Non posso procedere finché non è completata.
>
> [Se owner diverso e task completata ma non mergiata:]
> T-003 è completata da [nome owner], ma il branch non è ancora stato mergiato.
> Il codice non è disponibile sul branch base condiviso. Serve il merge di `feature/<task-name>` prima di procedere.
>
> [Se owner diverso e task non completata:]
> T-003 è ancora [stato attuale] ed è assegnata a [nome owner]. Non posso procedere finché non è completata e mergiata.
>
> Vuoi:
> 1. Passare a un'altra task senza dipendenze bloccanti?
> 2. Attendere? (ti chiederò di controllare il progresso più tardi)

### Creazione branch

Quando la task è confermata e le dipendenze sono soddisfatte:

1. Verifica il branch corrente e lo stato del repository
2. Crea il branch dalla base indicata nel piano:

> Creo il branch `feature/<task-name>` dal branch `<branch-base>`.

3. Aggiorna il file di progresso con il nome del branch e lo stato "In corso"

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
3. **Riferimenti** — estratti rilevanti dal gap report (cosa richiede il BR, cosa esiste, cosa manca)
4. **Convenzioni** — naming, struttura package, stile di codice del progetto (osservato dai file esistenti)
5. **Vincoli** — cosa NON fare, limiti di scope, attenzioni specifiche dalla task
6. **Output atteso** — file da creare/modificare, test da scrivere, documentazione da aggiungere

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

Dopo che ogni sottoagente completa il suo lavoro:

1. **Leggi il codice prodotto** — verifica che sia corretto, segua le convenzioni e rispetti i requisiti
2. **Controlla i test** — verifica che esistano e coprano i casi principali
3. **Controlla la documentazione** — verifica che il codice sia documentato dove serve
4. **Esegui i test** — lancia i test e verifica che passino
5. **Verifica la build** — assicurati che il progetto compili

Se qualcosa non va, istruisci un nuovo sottoagente per correggere il problema specifico. Non procedere finché il lavoro non è corretto.

### Suggerimento commit

L'agente non deve mai committare autonomamente. Quando il lavoro di un sotto-step è completo e verificato, avvisa lo sviluppatore:

> Il lavoro su [descrizione sotto-step] è completo e verificato:
> - [lista file creati/modificati]
> - Test: [passano / N test, tutti verdi]
> - Build: [compila]
>
> Sarebbe un buon momento per creare un commit. Suggerisco:
> ```
> feat(<area>): <descrizione concisa>
> ```
>
> Quando hai committato, dimmelo e proseguo.

Aspetta la conferma prima di proseguire con il sotto-step successivo.

### Completamento task

Una task è completata solo quando TUTTI questi criteri sono soddisfatti:

1. **Requisiti** — tutto ciò che il gap report e il piano richiedono per questa task è implementato
2. **Codice completo** — nessun placeholder, nessun TODO, nessuna implementazione parziale
3. **Documentazione** — il codice è documentato dove il "perché" non è ovvio
4. **Test** — test unitari scritti e tutti verdi
5. **Build** — il progetto compila senza errori

Quando tutti i criteri sono soddisfatti:

> La task **T-001 — [nome]** è completa.
>
> Checklist di completamento:
> - [x] Requisiti implementati: [lista]
> - [x] File creati/modificati: [lista con path]
> - [x] Test: N test, tutti verdi
> - [x] Build: compila
> - [x] Codice documentato
>
> Aggiorno il file di progresso a 100% — stato: **Completata**.

Aggiorna il file di progresso: stato "Completata", progresso 100%, note con riepilogo del lavoro svolto, log attività aggiornato.

Dopo aver aggiornato il progresso, verifica se ci sono task di **altri sviluppatori** che dipendono dalla task appena completata. Se sì, avvisa:

> **Nota**: le seguenti task di altri sviluppatori dipendono da T-001:
> - T-007 (owner: [nome]) — attualmente bloccata in attesa del merge
> - T-009 (owner: [nome]) — attualmente bloccata in attesa del merge
>
> Queste task si sbloccheranno solo dopo che il branch `feature/<task-name>` sarà stato mergiato nel branch base.
> Quando hai fatto il merge, dimmi **"task mergiata"** e aggiorno lo stato.

Se non ci sono task di altri sviluppatori che dipendono da questa, proponi direttamente la prossima task:

> Vuoi procedere con la prossima task **T-005 — [nome]**?

### Conferma merge — Transizione a "Mergiata"

Quando lo sviluppatore conferma che il branch di una task completata è stato mergiato (es. "task mergiata", "ho fatto il merge", "mergiato T-001"):

1. Aggiorna lo stato della task nel progresso da "Completata" a **"Mergiata"**
2. Aggiungi una riga al Log Attività: `[data] — T-001 mergiata nel branch base`
3. Verifica se questo sblocca task di altri sviluppatori e comunicalo:

> Task **T-001** segnata come **Mergiata**.
> Task sbloccate: T-007 (owner: [nome]), T-009 (owner: [nome]) — ora lavorabili.

Lo sviluppatore può confermare il merge in qualsiasi momento, anche dopo aver iniziato a lavorare altre sue task (che non richiedevano quel merge).

### Completamento di tutte le task — Spostamento in `plans/done/`

Dopo aver completato o mergiato una task, verifica nel file di progresso se **tutte** le task (non solo quelle dello sviluppatore corrente, ma tutte quelle nel piano) sono in stato "Completata" o "Mergiata". Se sì:

```bash
mkdir -p plans/done
mv plans/in-progress/GAP_REPORT_BR_*.md plans/done/
mv plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_*.md plans/done/
mv plans/in-progress/PROGRESSO_BR_*.md plans/done/
```

Comunica:

> Tutte le task del piano sono completate/mergiate. Report, piano e progresso spostati in `plans/done/`.

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
