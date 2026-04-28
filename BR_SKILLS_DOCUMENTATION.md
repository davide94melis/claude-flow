# BR Skills Suite — Documentazione Completa

Suite di 4 skill complementari per Claude Code che automatizzano l'intero ciclo di vita di un Business Requirement: dall'analisi iniziale all'esecuzione delle task, dalla gestione degli aggiornamenti alla reportistica Excel.

## Architettura del Flusso

```
BR / Documentazione
        |
        v
  [br-analyzer]  ──>  plans/todo/
        |                  |
        |            GAP_REPORT_BR_*.md
        |            PIANO_IMPLEMENTAZIONE_BR_*.md
        |
        v
  [br-executor]  ──>  plans/in-progress/
        |                  |
        |            + PROGRESSO_BR_*.md
        |
        |   (se BR aggiornato)
        |         |
        |         v
        |   [br-updater]  ──>  aggiorna report + piano
        |                      preservando il progresso
        |
        |   (per reportistica)
        |         |
        |         v
        |   [br-progress-report]  ──>  AVANZAMENTO_BR_*.xlsx
        |
        v
  (tutte le task completate)
        |
        |   (merge branch → "Mergiata")
        |         |
        |         v
        |   sblocca task cross-stream
        |
        v
  (tutte le task completate/mergiate)
        |
        v
                       plans/done/
```

## Struttura Cartelle

```
plans/
├── todo/              <-- br-analyzer crea report e piano qui
├── in-progress/       <-- br-executor li sposta qui all'avvio + crea progresso + excel
└── done/              <-- br-executor li sposta qui al completamento di tutte le task
```

---

## 1. BR Analyzer

**Skill**: `br-analyzer`
**Path**: `~/.claude/skills/br-analyzer/SKILL.md`
**Trigger**: "abbiamo un nuovo br"

### Scopo

Analizzare un nuovo Business Requirement confrontandolo con i codebase esistenti del progetto, identificare tutti i gap tra documentazione e codice, e produrre un piano di implementazione con task indipendenti assegnabili a sviluppatori muniti di Claude Code.

### Flusso Operativo

La skill opera in 4 fasi sequenziali.

#### Fase 1 — Raccolta Input

Pone 3 domande una alla volta:

1. **Path dei codebase** coinvolti (Backend, Frontend, Document Manager, Email Manager). Se un codebase non e coinvolto, viene escluso dall'analisi.
2. **Path della documentazione** (BR, mockup, specifiche tecniche). Accetta qualsiasi formato: MD, PDF, DOCX, XLSX, PPTX, immagini.
3. **Composizione del team** di sviluppo: nome, ruolo (BE/FE/Fullstack) e seniority (Junior/Mid/Senior) di ogni membro.

Prima di procedere, ricapitola tutti gli input e chiede conferma.

#### Fase 2 — Conversione Documentazione in Markdown

Converte tutti i documenti non-MD in formato Markdown per ridurre il consumo di contesto durante l'analisi:

- **DOCX/DOC**: usa la skill `doc-to-markdown` (`~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py`)
- **PDF/PPTX/XLSX**: usa `markitdown` (stessa dipendenza di doc-to-markdown)
- **MD**: copia diretta
- **Immagini (mockup)**: lette direttamente con supporto multimodale

I file convertiti vengono salvati in `br-docs-converted/`. Se una conversione fallisce, segnala all'utente e usa il Read diretto come fallback. Da questo punto l'analisi lavora solo sui file MD convertiti.

#### Fase 3 — Analisi Gap

1. **Lettura documentazione**: legge integralmente ogni documento MD convertito, estrae tutti i requisiti funzionali e tecnici, descrive nel dettaglio i mockup. Organizza i requisiti per funzionalita (es. "Dashboard", "Booking", "Monitoraggio"), non per documento o modulo tecnico.

2. **Esplorazione codebase**: per ogni codebase analizza struttura del progetto, modello dati (entita, DTO, migration), API/controller, servizi e logica di business, repository e query, componenti frontend, configurazioni. Usa agent di tipo `Explore` per parallelizzare l'esplorazione.

3. **Confronto e classificazione**: per ogni funzionalita richiesta dal BR, confronta con il codice esistente e classifica come:

| Stato | Significato |
|---|---|
| Coperto | Implementato correttamente, nessun gap |
| Parziale | Implementato in parte, manca qualcosa di specifico |
| Mancante | Non implementato, da sviluppare da zero |
| Discrepanza | Implementato ma diverso da quanto richiesto dal BR |
| Da chiarire | Il BR e ambiguo o il codice suggerisce un'interpretazione diversa |

Per ogni gap documenta: cosa richiede il BR (con riferimento a sezione/pagina), cosa esiste nel codice (con path esatti a file/classi/metodi), cosa manca o e diverso, moduli coinvolti, complessita stimata. Il livello di dettaglio e sufficiente perche un agente Claude Code possa lavorare senza rileggere il BR originale.

#### Fase 4 — Generazione Output

Crea la struttura `plans/todo/`, `plans/in-progress/`, `plans/done/` e genera due file in `plans/todo/`:

**GAP_REPORT_BR_\<data\>.md** contiene:
- Metadati: data verifica, branch verificati, perimetro documentale, codebase verificati
- Esito sintetico: 2-3 frasi sullo stato complessivo
- Matrice di verifica: una riga per ogni requisito con stato FE/BE, evidenze con path esatti, descrizione del gap
- Gap aperti reali: sezione dettagliata per ogni gap con cosa richiede il BR, cosa esiste, cosa manca, impatto sui moduli
- Conclusione finale: riepilogo per funzionalita

**PIANO_IMPLEMENTAZIONE_BR_\<data\>.md** contiene:
- Assunzioni e team disponibile
- Obiettivo (massimizzare parallelismo)
- Strategia di esecuzione (fondazioni, stream paralleli, integrazione)
- Distribuzione team consigliata (per competenza e seniority)
- Definizione degli stream funzionali (es. `stream-booking`, `stream-monitoraggio`, `stream-fondazioni`)
- Backlog operativo in tabella: ID, Stream, Owner, Area, Priorita, Attivita, Descrizione dettagliata, Dipendenze, Effort
- Ordine di esecuzione per wave (Wave 0 fondazioni, Wave 1..N sviluppo, Wave finale integrazione/UAT)
- Dipendenze critiche
- Piano per persona con lista task e note su pairing/review
- Stima complessiva con effort gg/uomo e durata calendario (scenario realistico + aggressivo)
- Rischi principali
- Raccomandazioni operative
- Deliverable minimi

### Principi per la Creazione delle Task

- **Organizzazione in stream**: le task sono raggruppate in stream funzionali coesi. Le task nello stesso stream condividono il contesto di codice e si sbloccano senza merge. Le dipendenze cross-stream richiedono merge. Le fondazioni condivise vanno in `stream-fondazioni`.
- **Indipendenza massima**: ogni task deve poter essere sviluppata in parallelo. Le dipendenze condivise vanno nella wave precedente. Minimizzare le dipendenze cross-stream.
- **Assegnazione per competenza e seniority**: task BE a sviluppatori BE, FE a FE. Task complesse ai senior/mid, task con scope chiuso ai junior con review assegnata. I senior non vanno caricati di implementazione continua.
- **Granularita giusta**: ogni task completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala.
- **Branch convention**: ogni task ha un branch `feature/<task-name>` dal branch principale della feature. Ordine di merge basato sulle dipendenze.
- **Autosufficiente per Claude Code**: ogni task contiene file esatti da modificare/creare, pattern da seguire, criteri di completamento verificabili, note specifiche.

### Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (via pip o uvx)

---

## 2. BR Executor

**Skill**: `br-executor`
**Path**: `~/.claude/skills/br-executor/SKILL.md`
**Trigger**: "lavora il task", "inizia a lavorare", "esegui il piano"

### Scopo

Permettere a ogni sviluppatore, assistito da un agente Claude Code, di eseguire le task assegnate dal piano generato da br-analyzer. L'agente principale coordina il lavoro, delega l'implementazione a sottoagenti Claude, verifica i risultati e tiene aggiornato un file di progresso condiviso.

### Flusso Operativo

#### Fase 1 — Raccolta Input

Cerca automaticamente i file nella struttura `plans/` e li propone. Pone le domande una alla volta:

1. **File del piano**: gap report, piano di implementazione, file di progresso (opzionale). Se trova file in `plans/todo/` o `plans/in-progress/`, li propone direttamente.
2. **Path dei codebase locali**: poiche lo sviluppatore lavora su un PC diverso, estrae tutti i path dei codebase menzionati nel report e chiede i corrispondenti path locali.
3. **Path della documentazione locale**: estrae i nomi dei file di documentazione dal report e chiede i path locali. Se non sono tutti disponibili, lavora dal gap report che contiene gia i dettagli estratti.
4. **Identita sviluppatore**: mostra la lista dal piano e chiede quale sviluppatore si e.

Alla conferma, sposta report e piano da `plans/todo/` a `plans/in-progress/`.

#### Fase 2 — Gestione del File di Progresso

Se il file non esiste, lo crea (`PROGRESSO_BR_<data>.md`) in `plans/in-progress/` con:
- Tabella riepilogativa (task totali, completate, in corso, da iniziare, bloccate, progresso complessivo)
- Tabella stato task (ID, Attivita, Owner, Progresso %, Stato, Branch, Note) con tutte le task a 0%
- Log attivita cronologico

Se il file esiste, lo legge, sincronizza con il piano e mostra lo stato attuale delle task dello sviluppatore.

Aggiorna il progresso a ogni cambio di stato significativo: task che passa a "In corso", sottoagente che completa una parte, task completata, task mergiata, task bloccata.

#### Fase 3 — Lavorazione Task

**Selezione task**: presenta le task assegnate allo sviluppatore in ordine di priorita (P0 > P1 > P2) e wave, chiede conferma prima di iniziare.

**Controllo dipendenze — logica basata sullo stream**: la regola di sblocco dipende dallo **stream** delle task (campo assegnato nel piano da br-analyzer), non dall'owner:

- **Stesso stream**: la dipendenza si sblocca quando lo stato e **"Completata"** o "Mergiata". Il codice e disponibile localmente perche le task dello stesso stream lavorano in sequenza sullo stesso flusso di branch.
- **Stream diverso**: la dipendenza si sblocca solo quando lo stato e **"Mergiata"**. Il codice non e disponibile finche il branch non viene mergiato nel branch base condiviso — anche se l'owner e lo stesso sviluppatore.

Se le dipendenze non sono soddisfatte, blocca e propone alternative: passare a un'altra task senza dipendenze bloccanti, oppure attendere.

**Creazione branch**: crea il branch `feature/<task-name>` dalla base indicata nel piano, aggiorna il progresso.

**Esecuzione con sottoagenti**: l'agente principale coordina, i sottoagenti implementano. Per ogni task:

1. Legge la descrizione dal piano e dal gap report
2. Scompone in sotto-lavori (entita, servizi, controller, componenti FE, test, documentazione)
3. Lancia sottoagenti con prompt autosufficienti che includono: contesto del progetto, cosa fare con file specifici, riferimenti al gap report, convenzioni osservate, vincoli, output atteso
4. Parallelizza sotto-lavori indipendenti, sequenzia quelli dipendenti

**Verifica**: dopo ogni sottoagente controlla correttezza del codice, esistenza dei test, copertura dei casi principali, documentazione, esecuzione test e build.

**Suggerimento commit**: non committa mai autonomamente. Quando un sotto-step e completo e verificato, avvisa lo sviluppatore con lista file, stato test/build e messaggio di commit suggerito. Aspetta conferma prima di proseguire.

**Completamento task**: una task e completa solo quando TUTTI i criteri sono soddisfatti:
- Requisiti implementati (tutto cio che il gap report e il piano richiedono)
- Codice completo (nessun placeholder, nessun TODO)
- Documentazione (codice documentato dove il "perche" non e ovvio)
- Test unitari scritti e tutti verdi
- Build compila senza errori

Al completamento, aggiorna il progresso a 100% con stato "Completata". Se ci sono task di **altri stream** che dipendono da questa, avvisa che si sbloccheranno solo dopo il merge. Propone la prossima task dello stesso stream (che non richiede merge per sbloccarsi).

**Conferma merge — transizione a "Mergiata"**: quando lo sviluppatore conferma che il branch e stato mergiato nel branch base (es. "task mergiata", "ho fatto il merge"), lo stato passa da "Completata" a "Mergiata" e le task **cross-stream** dipendenti vengono sbloccate. Il merge puo essere confermato in qualsiasi momento, anche dopo aver iniziato altre task dello stesso stream.

**Spostamento in done**: quando tutte le task del piano (non solo quelle dello sviluppatore) sono in stato "Completata" o "Mergiata", sposta tutti i file in `plans/done/`.

#### Fase 4 — Gestione Situazioni Speciali

- **Task bloccata**: segna come "Bloccata" nel progresso con motivazione, propone alternative (altra task, risolvere il blocco, fermarsi)
- **Ripresa del lavoro**: quando invocata con progresso esistente, riprende le task "In corso", verifica se i blocchi sono stati risolti
- **Conflitti di merge**: guida lo sviluppatore passo per passo nel merge/rebase, senza eseguire automaticamente

### Regole Fondamentali

1. Mai committare autonomamente
2. Mai procedere senza conferma
3. Mai ignorare le dipendenze
4. Aggiornare sempre il progresso
5. Verificare prima di dichiarare completo
6. Il sottoagente implementa, l'agente principale coordina

---

## 3. BR Updater

**Skill**: `br-updater`
**Path**: `~/.claude/skills/br-updater/SKILL.md`
**Trigger**: "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br"

### Scopo

Quando il BR o la documentazione vengono aggiornati, propagare le modifiche al gap report e al piano di implementazione senza perdere il lavoro gia fatto. Principio guida: mai sovrascrivere il progresso.

### Flusso Operativo

#### Fase 1 — Raccolta Input

Cerca automaticamente i file esistenti in `plans/` e pone le domande una alla volta:

1. **File esistenti**: gap report, piano, progresso da usare come base
2. **Documentazione aggiornata**: path dei file nuovi/modificati, specificando se sostituiscono un documento esistente o sono nuovi
3. **Codebase**: conferma se i path sono cambiati o invariati
4. **Team**: conferma se la composizione e cambiata (sviluppatori aggiunti, rimossi, ruoli cambiati)

#### Fase 2 — Analisi Delta Documentazione

1. **Conversione**: converte i nuovi documenti in MD (stessa procedura di br-analyzer)
2. **Identificazione delta**: confronta la documentazione aggiornata con quella referenziata nel report e identifica:
   - **Requisiti nuovi**: presenti nella nuova documentazione ma assenti dal report
   - **Requisiti modificati**: presenti in entrambi ma con differenze
   - **Requisiti rimossi**: presenti nel report ma assenti dalla nuova documentazione
   - **Requisiti invariati**: identici
3. **Verifica contro il codice**: per ogni requisito nuovo o modificato, verifica lo stato nel codice attuale e genera la classificazione gap

#### Fase 3 — Aggiornamento

Prima di modificare qualsiasi file, presenta il riepilogo dei delta (requisiti nuovi/modificati/rimossi, impatto sulle task) e aspetta conferma.

**Aggiornamento Gap Report**:
- Aggiorna header con data e documenti aggiornati
- Aggiunge sezione "Storico Aggiornamenti" con data, documenti, conteggio delta, motivazione
- Aggiorna la matrice: nuove righe, stati modificati, requisiti segnati come RIMOSSO (mai cancellati)
- Aggiorna gap aperti, esito sintetico, conclusione finale

**Aggiornamento Piano di Implementazione**:
- Task invariate: non toccate
- Task da modificare:
  - Se "Da iniziare": aggiornata liberamente
  - Se "In corso": nota `[AGGIORNATO <data>]` aggiunta in cima alla descrizione
  - Se "Completata" o "Mergiata": nuova task di adeguamento (es. `T-001-fix`)
- Task nuove: ID sequenziale, assegnate per competenza e carico attuale, inserite nella wave corretta
- Task da rimuovere:
  - Se "Da iniziare": segnata come ANNULLATA
  - Se "In corso": segnata come SOSPESA, sviluppatore avvisato
  - Se "Completata" o "Mergiata": resta nello stato attuale con nota `[REQUISITO RIMOSSO <data>]`
- Ricalcolo di wave, piano per persona, stima, rischi

**Aggiornamento File di Progresso**: task nuove a 0%, task annullate/sospese aggiornate, metriche ricalcolate, log aggiornato.

#### Fase 4 — Riepilogo Finale

Presenta riepilogo completo: file aggiornati, task aggiunte/modificate/annullate, task in corso impattate, rischi nuovi.

### Regole Fondamentali

1. Mai sovrascrivere il progresso (task completate/mergiate restano nel loro stato)
2. Mai cancellare (sempre segnare come RIMOSSO/ANNULLATA per tracciabilita)
3. Sempre chiedere conferma prima di applicare modifiche
4. Nuove task con ID sequenziali (non riusare ID di task annullate)
5. Segnalare sempre i conflitti con task in corso, completate o mergiate

---

## 4. BR Progress Report

**Skill**: `br-progress-report`
**Path**: `~/.claude/skills/br-progress-report/SKILL.md`
**Trigger**: "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso"

### Scopo

Generare o aggiornare un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo. Pensato per la reportistica verso il management e il tracking visuale del progetto.

### Flusso Operativo

#### Fase 1 — Individuazione File Sorgente

Cerca automaticamente nella struttura `plans/`:
- **Piano di Implementazione** (obbligatorio)
- **File di Progresso** (opzionale — se non esiste, tutte le task partono da 0%)
- **Gap Report** (opzionale — usato per arricchire le descrizioni)

Verifica se esiste gia un file `AVANZAMENTO_BR_*.xlsx`:
- **Se esiste**: modalita aggiornamento (solo i dati cambiano, note manuali preservate)
- **Se non esiste**: modalita creazione da zero

#### Fase 2 — Estrazione Dati

Legge piano e progresso, estrae per ogni task: ID, nome attivita, descrizione completa, owner, area (BE/FE), priorita (P0/P1/P2), wave, dipendenze, effort stimato, branch, progresso %, stato, note.

#### Fase 3 — Generazione Excel

Usa Python con `openpyxl`. Il file contiene 3 fogli:

**Foglio "Task"** — Tabella principale con 13 colonne:

| Colonna | Contenuto |
|---|---|
| ID | ID task (es. T-001) |
| Stream | Stream funzionale (es. stream-booking) |
| Attivita | Nome della task |
| Descrizione | Descrizione completa dal piano |
| Owner | Sviluppatore assegnato |
| Area | BE / FE / BE+FE |
| Priorita | P0 / P1 / P2 |
| Wave | Wave 0 / 1 / 2 / ... |
| Dipendenze | ID task dipendenze |
| Effort | Giorni stimati |
| Branch | Nome branch |
| Progresso | Percentuale 0-100% |
| Stato | Da iniziare / In corso / Completata / Mergiata / Bloccata / Annullata / Sospesa |
| Note | Note dal progresso |

Formattazione:
- Header in grassetto con sfondo grigio scuro e testo bianco
- Progresso con colori condizionali: rosso (0%), arancione (1-49%), giallo (50-99%), verde (100%)
- Stato con colori condizionali: verde (Completata), verde intenso (Mergiata), blu (In corso), rosso (Bloccata), grigio (Annullata/Sospesa)
- Filtri attivi su tutte le colonne
- Righe alternate per leggibilita
- Wrap text sulla colonna Descrizione

**Foglio "Per Sviluppatore"** — Una riga per sviluppatore:

| Colonna | Contenuto |
|---|---|
| Sviluppatore | Nome/ID |
| Ruolo | BE / FE / Fullstack |
| Seniority | Junior / Mid / Senior |
| Task totali | Conteggio |
| Completate | Conteggio (include Completata + Mergiata) |
| Mergiate | Conteggio (solo Mergiata) |
| In corso | Conteggio |
| Da iniziare | Conteggio |
| Bloccate | Conteggio |
| Progresso medio | Media % delle sue task |
| Effort totale | Somma giorni stimati |
| Effort completato | Somma giorni delle task completate/mergiate |

Riga "TOTALE" in fondo con le somme.

**Foglio "Riepilogo"** — Dashboard complessiva:
- Stato complessivo: task totali e conteggio/percentuale per stato
- Effort: totale stimato, completato, rimanente
- Progresso per wave: percentuale di completamento per ogni wave

#### Fase 4 — Salvataggio

Salva `AVANZAMENTO_BR_<data>.xlsx` nella stessa cartella del piano. In modalita aggiornamento preserva eventuali note manuali aggiunte dall'utente. Comunica riepilogo: task totali, completate, in corso, progresso complessivo, eventuali task bloccate.

### Dipendenze

- `openpyxl` (Python) — `pip install openpyxl`

---

## Ciclo di Vita delle Task

```
Da iniziare → In corso → Completata → Mergiata
                  |                       |
                  v                       v
              Bloccata            (sblocca task
                                  cross-stream)
```

| Stato | Significato |
|---|---|
| Da iniziare | Task non ancora avviata |
| In corso | Sviluppatore sta lavorando la task |
| Completata | Codice scritto, test verdi, build ok — pronta per review/merge |
| Mergiata | Branch mergiato nel branch base condiviso — codice disponibile per tutti |
| Bloccata | Dipendenza non soddisfatta o problema tecnico |
| Annullata | Requisito rimosso dal BR (task non ancora iniziata) |
| Sospesa | Requisito rimosso dal BR (task era in corso) |

### Regola di sblocco dipendenze

La transizione da "Completata" a "Mergiata" e fondamentale per il flusso multi-stream:

- **Stesso stream**: la task dipendente si sblocca gia a "Completata", perche le task dello stesso stream lavorano in sequenza sullo stesso flusso di branch e il codice e disponibile localmente.
- **Stream diverso**: la task dipendente si sblocca solo a "Mergiata", perche il codice non e disponibile sul branch di un altro stream finche non viene mergiato nel branch base condiviso — anche se l'owner e lo stesso sviluppatore.

Questo evita che si inizi a lavorare su codice che non e ancora disponibile sul branch dello stream corrente.

---

## Dipendenze Globali

| Dipendenza | Usata da | Installazione |
|---|---|---|
| `doc-to-markdown` skill | br-analyzer, br-updater | gia installata in `~/.claude/skills/doc-to-markdown/` |
| `markitdown` | br-analyzer, br-updater | `pip install 'markitdown[all]'` oppure via `uvx` |
| `openpyxl` | br-progress-report | `pip install openpyxl` |

## Trigger Registrati (CLAUDE.md)

| Frase | Skill |
|---|---|
| "abbiamo un nuovo br" | br-analyzer |
| "lavora il task" / "inizia a lavorare" / "esegui il piano" | br-executor |
| "il br e stato aggiornato" / "aggiorna il piano" / "nuova versione del br" | br-updater |
| "genera il report excel" / "aggiorna l'excel" / "stato avanzamento" / "esporta il progresso" | br-progress-report |
