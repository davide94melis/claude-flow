---
name: br-updater
description: Aggiorna gap report e piano di implementazione quando il BR o la documentazione viene modificata. Confronta la nuova documentazione con quella precedente, identifica i delta, e aggiorna report e piano preservando il progresso delle task già completate o in corso. Supporta qualsiasi composizione di repository — le sigle e i nomi vengono letti dinamicamente dai file esistenti. Usa questa skill quando l'utente dice "il br è stato aggiornato", "nuova versione del br", "aggiorna il piano", "documentazione aggiornata", "c'è un aggiornamento al br", "mockup aggiornati", "nuova versione documentazione", o qualsiasi variazione che implichi una modifica alla documentazione di un BR già analizzato.
---

# BR Updater — Aggiornamento Report e Piano su Documentazione Modificata

Questa skill è il terzo tassello del flusso BR, dopo `br-analyzer` (analisi iniziale) e `br-executor` (esecuzione task). Si attiva quando la documentazione del BR viene aggiornata e bisogna propagare le modifiche al gap report e al piano di implementazione, senza perdere il lavoro già fatto.

Il principio guida: **mai sovrascrivere il progresso**. Le task completate restano completate, quelle in corso restano in corso. Solo i gap nuovi o modificati generano aggiornamenti al piano.

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

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — File esistenti

Cerca automaticamente cartelle BR nella struttura `plans/`:

```bash
ls -d plans/in-progress/*/ plans/todo/*/ 2>/dev/null
```

**Se trovi cartelle BR**, elencale con il loro contenuto:

> Ho trovato questa cartella BR:
> - `plans/in-progress/2026-04-28_booking-v2/`
>   - `GAP_REPORT_BR.md`
>   - `PIANO_IMPLEMENTAZIONE_BR.md`
>   - `PROGRESSO_BR.md`
>   - `REVIEW_BR.md`
>
> Uso questa come base? Oppure dammi i path manualmente.

**Se trovi file flat** (retrocompatibilita'):

> Ho trovato questi file:
> - `plans/in-progress/GAP_REPORT_BR_2026-04-24.md`
> - `plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
> - `plans/in-progress/PROGRESSO_BR_2026-04-24.md`
>
> Uso questi come base? Oppure dammi i path manualmente.

**Se non trovi nulla**, chiedi:

> Dammi i path dei file da aggiornare:
> 1. **Gap Report** esistente
> 2. **Piano di Implementazione** esistente
> 3. **File di Progresso** (se esiste)

Leggi tutti i file. Estrai lo stato attuale completo: task, progresso, codebase, documentazione originale.

### Domanda 2 — Documentazione aggiornata

> Quali documenti sono stati aggiornati? Dammi i path dei file nuovi/modificati.
> Per ognuno, dimmi se:
> - **Sostituisce** un documento esistente (nuova versione dello stesso file)
> - **È un documento nuovo** che si aggiunge ai precedenti
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Repository

> Le repository coinvolte o i loro path sono cambiati rispetto all'analisi precedente?
> - Se **no**, uso quelli già nel report.
> - Se **sì**, dimmi le modifiche (path cambiati, repo aggiunte, repo rimosse).
> - Se ci sono **nuove repository** non presenti nel report precedente, dammi: nome, sigla e path.

### Domanda 4 — Team

> Il team è cambiato rispetto al piano attuale?
> - Se **no**, mantengo la composizione attuale.
> - Se **sì**, dimmi le modifiche (sviluppatori aggiunti, rimossi, ruoli cambiati).

### Riepilogo e conferma

> Riepilogo aggiornamento:
> - Report base: [path]
> - Piano base: [path]
> - Progresso: [path o "non presente"]
> - Documenti aggiornati: [lista]
> - Repository: [invariate / aggiornate — dettaglio modifiche]
> - Team: [invariato / modifiche]
>
> Procedo con l'analisi dei delta?

---

## Fase 2 — Conversione e Analisi Delta Documentazione

### 2.1 — Conversione documenti aggiornati

Converti i nuovi documenti in MD (stessa procedura di `br-analyzer`):

- DOCX/DOC → `~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py`
- PDF/PPTX/XLSX → `markitdown`
- MD → copia diretta
- Immagini → Read diretto

Salva nella cartella `br-docs-converted/` dentro la cartella del BR (es. `plans/in-progress/<YYYY-MM-DD>_<nome>/br-docs-converted/`), sovrascrivendo i file precedenti dove applicabile. Se stai lavorando con file flat, salva in `br-docs-converted/` nella working directory corrente.

### 2.2 — Identificazione delta

Confronta la documentazione aggiornata con quella referenziata nel report esistente. Identifica:

**Requisiti nuovi** — presenti nella nuova documentazione ma assenti dal report attuale.

**Requisiti modificati** — presenti in entrambi ma con differenze (campo, logica, UI, vincoli).

**Requisiti rimossi** — presenti nel report attuale ma assenti dalla nuova documentazione.

**Requisiti invariati** — identici tra vecchia e nuova documentazione.

Per ogni delta, documenta:
- **Tipo**: NUOVO / MODIFICATO / RIMOSSO
- **Funzionalità** di riferimento
- **Cosa cambia** (descrizione precisa)
- **Riferimento** al documento aggiornato (sezione/pagina)
- **Impatto** sulle task esistenti nel piano

### 2.3 — Verifica delta contro il codice

Per ogni requisito nuovo o modificato, verifica lo stato nel codice attuale (come nella Fase 3 di `br-analyzer`):
- Esiste già? Parzialmente? Per niente?
- Genera la classificazione gap: Coperto / Parziale / Mancante / Discrepanza / Da chiarire

Per i requisiti rimossi, verifica se il codice corrispondente era già stato implementato (task completate nel progresso).

### Ri-esplorazione con br-codebase-explorer

**Se il profilo progetto e' disponibile:**

Per ogni codebase coinvolto nel delta, lancia un agente `br-codebase-explorer` (leggendo le sue istruzioni da `~/.claude/agents/br-codebase-explorer.md`) con:
- Il profilo progetto completo (JSON)
- I NUOVI requisiti dalla documentazione aggiornata
- Il path del codebase da esplorare

L'explorer usa il profilo per navigare in modo mirato e confrontare la terminologia. L'output strutturato viene usato per aggiornare il gap report.

**Se il profilo NON e' disponibile (retrocompatibilita'):**

Esplora il codebase direttamente come oggi, analizzando struttura, modello dati, API, servizi, frontend e configurazione.

---

## Fase 3 — Aggiornamento Report

### Comunicazione delta all'utente

Prima di modificare qualsiasi file, presenta il riepilogo dei delta:

> ## Delta identificati
>
> **Requisiti nuovi**: N
> - [lista con breve descrizione]
>
> **Requisiti modificati**: N
> - [lista con cosa cambia]
>
> **Requisiti rimossi**: N
> - [lista — ATTENZIONE: se task già completate sono legate a requisiti rimossi, segnalalo]
>
> **Impatto sul piano**:
> - Task da aggiungere: N
> - Task da modificare: N
> - Task da rimuovere/annullare: N
> - Task invariate: N
>
> Procedo con l'aggiornamento?

Aspetta conferma.

### 3.1 — Aggiornamento Gap Report

Aggiorna il file gap report esistente (non crearne uno nuovo):

1. **Aggiorna l'header** — data aggiornamento, lista documenti aggiornata
2. **Aggiungi una sezione "Storico aggiornamenti"** in fondo al report:

```
## Storico Aggiornamenti

### Aggiornamento <data>
- Documenti aggiornati: [lista]
- Requisiti nuovi: N
- Requisiti modificati: N
- Requisiti rimossi: N
- Motivazione: [breve descrizione del perché il BR è cambiato, se noto]
```

3. **Aggiorna la matrice di verifica**:
   - Aggiungi righe per i requisiti nuovi
   - Aggiorna lo stato per i requisiti modificati
   - Segna come `RIMOSSO` (non cancellare) i requisiti eliminati, con nota sulla data di rimozione
4. **Aggiorna "Gap aperti reali"** — aggiungi i nuovi gap, aggiorna quelli modificati, segna come risolti quelli rimossi
5. **Aggiorna "Esito sintetico"** e "Conclusione finale"

### 3.2 — Aggiornamento Piano di Implementazione

Aggiorna il piano preservando il progresso.

**Pre-step: colonna Branch** — Se il backlog operativo del piano NON ha una colonna **Branch**, aggiungila PRIMA di qualsiasi altra modifica. Per ogni task esistente, genera il nome branch seguendo il pattern `feature/<br-name>-<slug-attivita>` (dove `<br-name>` e' il nome del BR e `<slug>` e' derivato dal nome dell'attivita'). Per le merge task (T-MERGE-*), il valore e' `—`. Comunica all'utente:

> Il piano non aveva la colonna Branch. L'ho aggiunta con i nomi branch generati per ogni task.
> Verifica che i nomi siano corretti — se qualche task e' gia' stata lavorata su un branch diverso, aggiorna il nome.

**Task invariate** — non toccarle, mantieni ID, owner, descrizione, effort, branch.

**Task da modificare** (requisito cambiato):
- Aggiorna la descrizione con i nuovi requisiti
- Se la task è "Da iniziare": aggiorna liberamente
- Se la task è "In corso": aggiungi una nota `[AGGIORNATO <data>]: [cosa è cambiato]` in cima alla descrizione, senza cancellare il lavoro già fatto
- Se la task è "Completata": crea una nuova task di adeguamento (es. `T-001-fix`) collegata alla originale

**Task nuove** (requisito nuovo):
- Assegna un nuovo ID sequenziale che continua dalla numerazione esistente
- Assegna lo **stream** appropriato: usa uno stream esistente se la task appartiene alla stessa area funzionale, oppure crea un nuovo stream se rappresenta una funzionalità nuova
- Assegna un nome **Branch** seguendo lo stesso pattern del piano (`feature/<br-name>-<slug-attivita>`)
- Assegnale al developer più adatto in base a ruolo, seniority e carico attuale (dal progresso)
- Inseriscile nella wave appropriata rispettando le dipendenze
- Se il team è cambiato, ridistribuisci considerando i nuovi membri

**Task da rimuovere** (requisito rimosso):
- Se "Da iniziare": segna come `ANNULLATA` nel piano con motivazione, non cancellarla
- Se "In corso": avvisa lo sviluppatore, segna come `SOSPESA` con motivazione
- Se "Completata": lasciala nello stato attuale, aggiungi nota `[REQUISITO RIMOSSO <data>]`

**Aggiorna le sezioni del piano**:
- Backlog operativo — aggiungi/modifica/annulla task
- Ordine di esecuzione — ricalcola le wave
- Piano per persona — ribilancia i carichi
- Stima complessiva — aggiorna effort e timeline
- Rischi — aggiungi rischi derivanti dai cambiamenti
- Aggiungi una sezione "Storico Aggiornamenti" analoga a quella del report

### 3.3 — Aggiornamento File di Progresso

Se il file di progresso esiste, aggiornalo:
- Aggiungi le task nuove con stato "Da iniziare" e progresso 0%
- Segna le task annullate con stato "Annullata"
- Segna le task sospese con stato "Sospesa"
- Aggiorna il riepilogo (totali, percentuali)
- Aggiungi voce al log attività: `[data] — Aggiornamento piano da nuova documentazione BR: N task aggiunte, M modificate, K annullate`

---

## Fase 4 — Riepilogo Finale

Al termine, presenta un riepilogo completo:

> ## Aggiornamento completato
>
> **File aggiornati**:
> - [path report] — aggiornato
> - [path piano] — aggiornato
> - [path progresso] — aggiornato (se presente)
>
> **Impatto**:
> - Task aggiunte: [lista con ID e owner]
> - Task modificate: [lista con ID e cosa è cambiato]
> - Task annullate/sospese: [lista con ID e motivazione]
> - Task invariate: N
>
> **Attenzione**:
> - [eventuali task in corso impattate — lo sviluppatore deve essere avvisato]
> - [eventuali task completate il cui requisito è stato rimosso]
> - [rischi nuovi]

---

## Regole Fondamentali

1. **Mai sovrascrivere il progresso** — le task completate restano nel loro stato, quelle in corso restano in corso
2. **Mai cancellare** — i requisiti rimossi vengono segnati come RIMOSSO/ANNULLATA, non eliminati, per preservare la tracciabilità
3. **Sempre chiedere conferma** — prima di applicare qualsiasi modifica, mostra il delta e aspetta conferma
4. **Nuove task con ID sequenziali** — continua la numerazione esistente, non riusare ID di task annullate
5. **Segnalare sempre i conflitti** — se una modifica impatta task in corso o completate, avvisa esplicitamente
