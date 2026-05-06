# BR Skills Suite — Documentazione Completa

Suite di 7 skill complementari per Claude Code che automatizzano l'intero ciclo di vita di un Business Requirement: dalla review della documentazione funzionale alla gestione delle risposte del funzionale, dall'analisi gap all'esecuzione delle task, dalla gestione degli aggiornamenti alla reportistica Excel, con un orchestratore pipeline che coordina il tutto.

## Architettura del Flusso

```
BR / Documentazione
        |
        v
  [br-reviewer]   ──>  plans/todo/<data>_<nome>/
        |                  |
        |            REVIEW_BR.md
        |            REVIEW_BR.docx
        |            br-docs-converted/
        |
        v
  [br-clarify]    ──>  aggiorna REVIEW_BR.md/.docx
        |               con risposte del funzionale
        |
        v
  [br-analyzer]   ──>  plans/todo/<data>_<nome>/
        |                  |
        |            GAP_REPORT_BR.md
        |            PIANO_IMPLEMENTAZIONE_BR.md
        |
        v
  [br-executor]   ──>  plans/in-progress/<data>_<nome>/
        |                  |
        |            + PROGRESSO_BR.md
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
        |   [br-progress-report]  ──>  AVANZAMENTO_BR.xlsx
        |
        v
  (tutte le task completate)
        |
        v
                       plans/done/<data>_<nome>/
```

## Struttura Cartelle

Ogni BR ha la propria cartella con formato `<YYYY-MM-DD>_<nome-br>/`. La cartella si sposta come unità tra le tre aree:

```
plans/
├── todo/                              <-- br-reviewer e br-analyzer creano i report qui
│   └── 2026-04-28_booking-v2/
│       ├── br-docs-converted/         <-- documentazione convertita in MD (da br-reviewer)
│       ├── REVIEW_BR.md               <-- output di br-reviewer (aggiornato da br-clarify)
│       ├── REVIEW_BR.docx             <-- output di br-reviewer (per il funzionale)
│       ├── GAP_REPORT_BR.md           <-- output di br-analyzer
│       └── PIANO_IMPLEMENTAZIONE_BR.md
├── in-progress/                       <-- br-executor sposta qui la cartella all'avvio
│   └── 2026-04-28_booking-v2/
│       ├── ...tutto il contenuto...
│       └── PROGRESSO_BR.md            <-- creato da br-executor
└── done/                              <-- br-executor sposta qui al completamento
    └── 2026-04-28_booking-v2/
        └── AVANZAMENTO_BR.xlsx        <-- creato da br-progress-report
```

Tutte le skill mantengono retrocompatibilità con il vecchio formato flat (es. `GAP_REPORT_BR_2026-04-28.md`).

---

## 1. BR Reviewer

**Skill**: `br-reviewer`
**Path**: `~/.claude/skills/br-reviewer/SKILL.md`
**Trigger**: "rivedi il br", "review del br", "controlla la documentazione", "verifica il br"

### Scopo

Validare la qualità, coerenza e completezza della documentazione funzionale di un BR *prima* dell'analisi tecnica (br-analyzer). Produce un report duale:
- **Parte 1 — Per il team funzionale**: elenca i problemi trovati (bloccanti e non) con domande precise a cui serve risposta
- **Parte 2 — Per il team tecnico**: assunzioni di default che il team adotterà in assenza di chiarimenti, e disallineamenti tra terminologia/strutture del BR e del codice

Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali — non una gap analysis completa (quella la fa br-analyzer), ma problemi di documentazione visibili solo confrontando col codebase.

### Flusso Operativo

La skill opera in 4 fasi sequenziali.

#### Fase 1 — Raccolta Input

Pone 3 domande una alla volta:

1. **Nome del BR** — identificativo per la cartella (es. "booking-v2" crea `plans/todo/2026-04-28_booking-v2/`)
2. **Documentazione** — path ai file del BR. Accetta MD, PDF, DOCX, XLSX, PPTX, immagini.
3. **Codebase coinvolti** — nome, sigla, path per ogni repository. Servono per il check leggero contro il codice.

Prima di procedere, ricapitola tutti gli input e chiede conferma.

#### Fase 2 — Conversione Documentazione in MD

Stessa logica di conversione delle altre skill (doc-to-markdown per DOCX/DOC, markitdown per PDF/PPTX/XLSX, copia diretta per MD, Read per immagini). I file convertiti vanno nella cartella del BR: `plans/todo/<data>_<nome>/br-docs-converted/`.

Questa fase viene eseguita da br-reviewer: br-analyzer non la ripete se trova i file gia convertiti.

#### Fase 3 — Analisi della Documentazione

Tre livelli di analisi:

1. **Analisi intra-documento** — coerenza interna, completezza dei flussi (caso felice + eccezioni + errori), chiarezza dei requisiti, definizione delle regole di business
2. **Analisi inter-documento** — BR vs mockup (corrispondenza elementi visuali/funzionali), BR vs specifiche tecniche, coerenza terminologica tra tutti i documenti
3. **Check leggero contro il codice** — verifica superficiale di entita/modelli dati, enum/costanti, API/endpoint, flussi e stati gia implementati

Ogni problema viene classificato per categoria e gravita:

| Categoria | Descrizione |
|---|---|
| **Incoerenza** | Contraddizioni tra parti della documentazione |
| **Gap funzionale** | Pezzi mancanti nella descrizione del comportamento |
| **Ambiguita** | Punti interpretabili in piu modi |
| **Riferimento mancante** | Dipendenze esterne non specificate |
| **Disallineamento col codice** | Il BR presuppone strutture/terminologie diverse da quelle nel codice |

#### Fase 4 — Generazione Output

Genera `REVIEW_BR.md` nella cartella del BR con:
- Esito sintetico (qualita complessiva, conteggio problemi, presenza bloccanti)
- **Parte 1 — Per il team funzionale**: problemi bloccanti e non bloccanti con domande precise
- **Parte 2 — Per il team tecnico**: tabella assunzioni proposte con rischio e costo di correzione, tabella disallineamenti col codice
- **Riepilogo per br-analyzer**: sezione tecnica consumata automaticamente da br-analyzer per incorporare le assunzioni nel piano

Dopo il MD, genera automaticamente `REVIEW_BR.docx` con pandoc. Il DOCX contiene placeholder "*(inserire qui la risposta)*" sotto ogni domanda, pronti per la compilazione da parte del funzionale.

Se ci sono bloccanti, consiglia di attendere chiarimenti dal funzionale prima di procedere con br-analyzer, ma la decisione e dell'utente. Suggerisce di usare `br-clarify` quando arrivano le risposte.

### Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (via pip o uvx)
- `pandoc` — per generazione REVIEW_BR.docx

---

## 2. BR Clarify

**Skill**: `br-clarify`
**Path**: `~/.claude/skills/br-clarify/SKILL.md`
**Trigger**: "chiarimenti ricevuti", "risposte ricevute", "il funzionale ha risposto", "ho le risposte"

### Scopo

Gestire le risposte del team funzionale alle domande sollevate da br-reviewer nel REVIEW_BR.md. Aggiorna il report con le risposte, ri-valuta i bloccanti e le assunzioni, e rigenera il DOCX. Supporta risposte parziali e round multipli.

### Flusso Operativo

#### Fase 1 — Auto-detect REVIEW_BR.md

Cerca automaticamente `plans/todo/*/REVIEW_BR.md` e `plans/in-progress/*/REVIEW_BR.md`. Se ne trova uno lo propone, se piu di uno chiede quale usare, se nessuno informa che serve prima br-reviewer. Analizza lo stato: quante domande hanno gia risposta e quante sono ancora aperte.

#### Fase 2 — Modalita Input

Supporta due modalita:

1. **DOCX compilato**: il funzionale ha compilato il REVIEW_BR.docx inserendo le risposte sotto i placeholder. La skill converte il DOCX con pandoc, confronta con l'originale per rilevare le risposte, e le presenta all'utente per conferma.

2. **Conversazione**: la skill presenta ogni domanda aperta una alla volta (prima i bloccanti, poi i non bloccanti). L'utente riporta la risposta o dice "salta" per le domande ancora senza risposta.

Le due modalita possono combinarsi: dopo aver processato il DOCX, la skill chiede se ci sono risposte aggiuntive da riportare a voce.

#### Fase 3 — Rivalutazione

Per ogni risposta ricevuta:

- **Bloccanti**: valuta se la risposta risolve il problema. Se si, lo stato diventa "Si → **RISOLTO**". Se la risposta e parziale o ambigua, resta bloccante con nota esplicativa e eventuale domanda di follow-up.
- **Non bloccanti**: confronta la risposta con l'assunzione proposta. L'assunzione viene classificata come **Confermata** (il funzionale concorda), **Rigettata** (il funzionale da un'indicazione diversa — la risposta del funzionale prevale), o resta **In attesa** (nessuna risposta).

Prima di modificare i file, presenta il riepilogo completo della rivalutazione e aspetta conferma.

#### Fase 4 — Aggiornamento Output

Aggiorna REVIEW_BR.md:
- Aggiunge "Risposta del funzionale" e "Data risposta" a ogni problema risposto
- Aggiorna la tabella assunzioni con colonne "Stato" e "Risposta funzionale"
- Sostituisce la sezione "Riepilogo per br-analyzer" con formato arricchito: bloccanti risolti con sintesi risposta, bloccanti ancora aperti, stato di ogni assunzione (confermata/rigettata/in attesa), marcatore "Ultimo aggiornamento: \<data\> (br-clarify)"

Rigenera REVIEW_BR.docx con pandoc.

#### Round Multipli

La skill puo essere eseguita piu volte sullo stesso REVIEW_BR.md. A ogni esecuzione:
- Rileva le domande gia risposte e presenta solo quelle ancora aperte
- Non sovrascrive mai risposte precedenti
- Se tutte le domande hanno risposta, informa che il review e completo

### Regole Fondamentali

1. Mai modificare le domande o le categorie originali
2. Mai sovrascrivere risposte precedenti
3. Sempre chiedere conferma prima di scrivere
4. Sempre rigenerare il DOCX dopo ogni modifica al MD
5. Non interpretare le risposte — riportarle cosi come sono, la rivalutazione e presentata all'utente per conferma

### Dipendenze

- `pandoc` — per conversione DOCX↔MD e rigenerazione DOCX
- `br-reviewer` — deve essere stato eseguito prima

---

## 3. BR Analyzer

**Skill**: `br-analyzer`
**Path**: `~/.claude/skills/br-analyzer/SKILL.md`
**Trigger**: "abbiamo un nuovo br"

### Scopo

Analizzare un nuovo Business Requirement confrontandolo con i codebase esistenti del progetto, identificare tutti i gap tra documentazione e codice, e produrre un piano di implementazione con task indipendenti assegnabili a sviluppatori muniti di Claude Code. Se br-reviewer e stato eseguito prima, ne legge le assunzioni e salta la conversione dei documenti.

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
- Backlog operativo in tabella: ID, Stream, Owner, Area, Branch, Priorita, Attivita, Descrizione dettagliata, Dipendenze, Effort
- Ordine di esecuzione per wave (Wave 0 fondazioni, Wave 1..N sviluppo, Wave finale integrazione/UAT)
- Dipendenze critiche
- Piano per persona con lista task e note su pairing/review
- Stima complessiva con effort gg/uomo e durata calendario (scenario realistico + aggressivo)
- Rischi principali
- Raccomandazioni operative
- Deliverable minimi

### Principi per la Creazione delle Task

- **Organizzazione in stream**: le task sono raggruppate in stream funzionali coesi. Le task nello stesso stream condividono il contesto di codice e possono dipendere direttamente. Per le dipendenze cross-stream, br-analyzer inserisce automaticamente **merge task** (`T-MERGE-NNN`) tra la task sorgente e quella dipendente. Le fondazioni condivise vanno in `stream-fondazioni`.
- **Indipendenza massima**: ogni task deve poter essere sviluppata in parallelo. Le dipendenze condivise vanno nella wave precedente. Minimizzare le dipendenze cross-stream.
- **Assegnazione per competenza e seniority**: task BE a sviluppatori BE, FE a FE. Task complesse ai senior/mid, task con scope chiuso ai junior con review assegnata. I senior non vanno caricati di implementazione continua.
- **Granularita giusta**: ogni task completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala.
- **Branch convention**: ogni task ha un branch specificato nella colonna Branch del backlog, con naming `feature/<br-name>-<slug-attivita>`. Per task multi-repo (Area = BE+FE), lo stesso nome branch viene usato in tutte le repo. Per le merge task il branch e' `—`. Ordine di merge basato sulle dipendenze.
- **Autosufficiente per Claude Code**: ogni task contiene file esatti da modificare/creare, pattern da seguire, criteri di completamento verificabili, note specifiche.

### Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (via pip o uvx)

---

## 4. BR Executor

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

Aggiorna il progresso a ogni cambio di stato significativo: task che passa a "In corso", sottoagente che completa una parte, task completata, task bloccata.

#### Fase 3 — Lavorazione Task

**Selezione task**: presenta le task assegnate allo sviluppatore in ordine di priorita (P0 > P1 > P2) e wave, chiede conferma prima di iniziare.

**Controllo dipendenze con aggregazione cross-branch**: prima di verificare le dipendenze, l'executor esegue un'aggregazione del progresso da tutti i feature branch remoti (vedi sezione "Aggregazione Cross-Branch del Progresso" in fondo). Questo permette di vedere se una dipendenza e stata completata da un altro sviluppatore sul suo branch, senza attendere la merge. La regola e semplice — una dipendenza e soddisfatta quando il suo stato nella vista aggregata e **"Completata"**. Non serve nessun controllo sugli stream: le dipendenze cross-stream sono gestite tramite merge task esplicite (`T-MERGE-*`) inserite nel piano da br-analyzer. Le merge task (T-MERGE-*) sono task speciali: quando l'executor le incontra, guida lo sviluppatore nel merge del branch e nella verifica della build, senza lanciare sottoagenti per implementazione di codice.

Se le dipendenze non sono soddisfatte, blocca e propone alternative: passare a un'altra task senza dipendenze bloccanti, oppure attendere.

**Creazione branch multi-repo**: identifica tutte le repo coinvolte dalla colonna Area del piano (es. BE, FE, BE+FE) e crea il feature branch `feature/<task-name>` in ognuna. Nella repo del piano crea il branch di tracking (con aggiornamento PROGRESSO), nelle repo esterne crea il branch di codice. Se la task riguarda solo la repo del piano, crea un solo branch.

**Esecuzione con sottoagenti**: l'agente principale coordina, i sottoagenti implementano. Per ogni task:

1. Legge la descrizione dal piano e dal gap report
2. Scompone in sotto-lavori (entita, servizi, controller, componenti FE, test, documentazione)
3. Lancia sottoagenti con prompt autosufficienti che includono: contesto del progetto, cosa fare con file specifici, riferimenti al gap report, convenzioni osservate, vincoli, output atteso
4. Parallelizza sotto-lavori indipendenti, sequenzia quelli dipendenti

**Verifica**: dopo ogni sottoagente controlla correttezza del codice, esistenza dei test, copertura dei casi principali, documentazione, esecuzione test e build.

**Suggerimento commit con push reminder**: non committa mai autonomamente. Quando un sotto-step e completo e verificato, avvisa lo sviluppatore con suggerimenti separati per ogni repo coinvolta (lista file, stato test/build, messaggio di commit suggerito). Dopo il commit, suggerisce di pushare il branch per rendere il progresso visibile agli altri sviluppatori. Aspetta conferma prima di proseguire.

**Completamento task**: una task e completa solo quando TUTTI i criteri sono soddisfatti:
- Requisiti implementati (tutto cio che il gap report e il piano richiedono)
- Codice completo (nessun placeholder, nessun TODO)
- Documentazione (codice documentato dove il "perche" non e ovvio)
- Test unitari scritti e tutti verdi
- Build compila senza errori

Al completamento, aggiorna il progresso a 100% con stato "Completata" e propone la prossima task disponibile.

**Spostamento in done**: quando tutte le task del piano (non solo quelle dello sviluppatore) sono in stato "Completata", sposta tutti i file in `plans/done/`.

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

## 5. BR Updater

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
  - Se "Completata": nuova task di adeguamento (es. `T-001-fix`)
- Task nuove: ID sequenziale, assegnate per competenza e carico attuale, inserite nella wave corretta
- Task da rimuovere:
  - Se "Da iniziare": segnata come ANNULLATA
  - Se "In corso": segnata come SOSPESA, sviluppatore avvisato
  - Se "Completata": resta nello stato attuale con nota `[REQUISITO RIMOSSO <data>]`
- Ricalcolo di wave, piano per persona, stima, rischi

**Aggiornamento File di Progresso**: task nuove a 0%, task annullate/sospese aggiornate, metriche ricalcolate, log aggiornato.

#### Fase 4 — Riepilogo Finale

Presenta riepilogo completo: file aggiornati, task aggiunte/modificate/annullate, task in corso impattate, rischi nuovi.

### Regole Fondamentali

1. Mai sovrascrivere il progresso (task completate restano nel loro stato)
2. Mai cancellare (sempre segnare come RIMOSSO/ANNULLATA per tracciabilita)
3. Sempre chiedere conferma prima di applicare modifiche
4. Nuove task con ID sequenziali (non riusare ID di task annullate)
5. Segnalare sempre i conflitti con task in corso o completate

---

## 6. BR Progress Report

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

Prima di estrarre i dati, esegue un'**aggregazione cross-branch** del progresso (vedi sezione "Aggregazione Cross-Branch del Progresso" in fondo) per ottenere una vista aggiornata di tutte le task, anche quelle in lavorazione su branch non ancora mergiati. Dalla vista aggregata e dal piano, estrae per ogni task: ID, nome attivita, descrizione completa, owner, area (BE/FE), priorita (P0/P1/P2), wave, dipendenze, effort stimato, branch, progresso %, stato, note. Il foglio "Riepilogo" dell'Excel include anche il numero di branch remoti aggregati e il timestamp dell'ultimo fetch.

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
| Stato | Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa |
| Note | Note dal progresso |

Formattazione:
- Header in grassetto con sfondo grigio scuro e testo bianco
- Progresso con colori condizionali: rosso (0%), arancione (1-49%), giallo (50-99%), verde (100%)
- Stato con colori condizionali: verde (Completata), blu (In corso), rosso (Bloccata), grigio (Annullata/Sospesa)
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
| Completate | Conteggio |
| In corso | Conteggio |
| Da iniziare | Conteggio |
| Bloccate | Conteggio |
| Progresso medio | Media % delle sue task |
| Effort totale | Somma giorni stimati |
| Effort completato | Somma giorni delle task completate |

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

## 7. BR Pipeline

**Skill**: `br-pipeline`
**Path**: `~/.claude/skills/br-pipeline/SKILL.md`
**Trigger**: "br-pipeline", "pipeline br", "le mie task", "stato dei br"

### Scopo

Orchestratore unico per il ciclo di vita dei BR. Legge lo stato dal `manifest.json` di ogni BR nel repo, rileva il ruolo dell'utente (TL/PM o Dev) e mostra una dashboard con lo stato di ogni BR, proponendo il prossimo step e delegando alle skill appropriate (br-reviewer, br-clarify, br-analyzer, br-executor, br-updater, br-progress-report). La pipeline NON reimplementa la logica delle skill — propone e delega.

### Flusso Pipeline

```
onboard --> review --> clarify --> analyze --> approve --> execute --> done
                                                            |
                                                         update
```

| Stage | Chi lo avvia | Skill delegata |
|---|---|---|
| onboard | Funzionale | — (creazione BR) |
| review | TL/PM | br-reviewer |
| clarify | Funzionale | br-clarify |
| analyze | TL/PM | br-analyzer |
| approve | TL/PM | — (gate esplicito) |
| execute | Dev | br-executor |
| update | TL/PM | br-updater |

### Viste per Ruolo

**TL/PM** — Dashboard completa di tutti i BR con stato, ultimo evento, azioni suggerite. Puo' lanciare review, analisi, approvare il piano.

**Dev** — Solo le proprie task assegnate, filtrate tramite `.br-local.json`. Puo' procedere con l'esecuzione delle task.

### Aggregazione Cross-Branch

Prima di mostrare la dashboard, la pipeline esegue l'aggregazione cross-branch del progresso (vedi sezione dedicata) per mostrare dati aggiornati da tutti i feature branch remoti.

### Manifest JSON

Ogni BR ha un `manifest.json` in `brs/<nome-br>/` che funge da single source of truth: stato pipeline, codebase, documenti, team, review, piano con task, timeline. La pipeline rileva automaticamente lo stato dagli artefatti presenti nel repo per correggere eventuali disallineamenti.

### Regole Fondamentali

1. Mai reimplementare la logica delle skill delegate
2. Sempre aggiornare il manifest con timestamp, attore e descrizione
3. Sempre chiedere conferma prima di ogni transizione di stato
4. Rilevare lo stato dagli artefatti, non solo dal manifest
5. Rispettare il ruolo (TL/PM vede tutto, Dev vede solo le sue task)

---

## Ciclo di Vita delle Task

```
Da iniziare → In corso → Completata
                  |
                  v
              Bloccata
```

| Stato | Significato |
|---|---|
| Da iniziare | Task non ancora avviata |
| In corso | Sviluppatore sta lavorando la task |
| Completata | Codice scritto, test verdi, build ok — task terminata |
| Bloccata | Dipendenza non soddisfatta o problema tecnico |
| Annullata | Requisito rimosso dal BR (task non ancora iniziata) |
| Sospesa | Requisito rimosso dal BR (task era in corso) |

### Dipendenze cross-stream

Le dipendenze cross-stream sono gestite tramite **merge task esplicite** (`T-MERGE-NNN`) inserite nel piano da br-analyzer. Non esiste una logica di sblocco basata sugli stream nell'executor: tutte le dipendenze si sbloccano semplicemente quando lo stato e "Completata".

---

## Dipendenze Globali

| Dipendenza | Usata da | Installazione |
|---|---|---|
| `doc-to-markdown` skill | br-reviewer, br-analyzer, br-updater | gia installata in `~/.claude/skills/doc-to-markdown/` |
| `markitdown` | br-reviewer, br-analyzer, br-updater | `pip install 'markitdown[all]'` oppure via `uvx` |
| `pandoc` | br-reviewer, br-clarify | disponibile su PATH |
| `openpyxl` | br-progress-report | `pip install openpyxl` |

## Trigger Registrati (CLAUDE.md)

| Frase | Skill |
|---|---|
| "rivedi il br" / "review del br" / "controlla la documentazione" / "verifica il br" | br-reviewer |
| "chiarimenti ricevuti" / "risposte ricevute" / "il funzionale ha risposto" / "ho le risposte" | br-clarify |
| "abbiamo un nuovo br" | br-analyzer |
| "lavora il task" / "inizia a lavorare" / "esegui il piano" | br-executor |
| "il br e stato aggiornato" / "aggiorna il piano" / "nuova versione del br" | br-updater |
| "genera il report excel" / "aggiorna l'excel" / "stato avanzamento" / "esporta il progresso" | br-progress-report |
| "br-pipeline" / "pipeline br" / "le mie task" / "stato dei br" | br-pipeline |

---

## Aggregazione Cross-Branch del Progresso

Quando piu' sviluppatori lavorano in parallelo su feature branch diversi, ognuno aggiorna il file PROGRESSO_BR.md sul proprio branch. Per garantire visibilita' del progresso a tutti senza attendere le merge, le skill di lettura (br-executor, br-pipeline, br-progress-report) eseguono un'aggregazione cross-branch.

### Algoritmo

1. `git fetch origin` per sincronizzare i branch remoti
2. Lettura del PIANO per estrarre gli ID di tutte le task e, se presente, la colonna **Branch** con i nomi dei branch di ogni task. Estrazione del nome BR dalla cartella (es. `2026-05-04_monitoring` → `monitoring`).
3. Ricerca dei feature branch remoti:
   - **Se il piano ha colonna Branch**: usa direttamente i nomi branch dal piano
   - **Se il piano NON ha colonna Branch** (retrocompatibilita'): cerca per pattern sul nome del BR: `git branch -r | grep -i "feature/<nome-br>"`
4. Per ogni branch trovato, lettura del PROGRESSO provando 3 percorsi: `plans/in-progress/<br>/`, `plans/todo/<br>/`, `plans/done/<br>/` (usa il primo che funziona)
5. Lettura del PROGRESSO dal branch base del piano (stessi 3 percorsi). Se non esiste, genera un baseline dal PIANO con tutte le task a 0%.
6. Aggregazione per task con regola **"highest progress wins"**: per ogni task, la versione con il progresso piu' alto vince. Se una versione mostra "Completata" (100%), vince sempre.
7. Ricalcolo metriche di riepilogo dalla vista aggregata

### Colonna Branch nel Piano

I piani generati da br-analyzer includono una colonna **Branch** nel backlog operativo che specifica il nome esatto del branch per ogni task (es. `feature/monitoring-enum-entities-core`). L'executor usa questo nome per creare i branch. Per le merge task, il valore e' `—`. Per piani creati prima di questa modifica, l'aggregazione usa il fallback per pattern sul nome del BR.

### Fallback

Se `git fetch` fallisce (no rete), le skill usano il file di progresso locale e mostrano un warning.

### Skill che la usano

| Skill | Dove | Scopo |
|---|---|---|
| br-executor | Controllo dipendenze | Verificare se le dipendenze sono completate da altri developer sui loro branch |
| br-pipeline | Dashboard TL/PM e Dev | Mostrare il progresso reale di tutte le task |
| br-progress-report | Estrazione dati per Excel | Generare l'Excel con dati aggiornati da tutti i branch |

### Creazione Branch Multi-Repo

L'executor crea feature branch in tutte le repo coinvolte nella task (identificate dalla colonna Area del piano). Nella repo del piano crea il branch di tracking (con aggiornamento PROGRESSO), nelle repo esterne (FE, EM, DM, ...) crea il branch per il codice. Prerequisito: tutti gli sviluppatori devono avere un clone locale di tutte le repo coinvolte.

### Push Reminder

Dopo ogni suggerimento di commit che include aggiornamenti al PROGRESSO, l'executor ricorda allo sviluppatore di pushare il branch per rendere il progresso visibile: `git push origin <nome-branch>`. Il push non e' obbligatorio ma e' il meccanismo che rende il progresso visibile agli altri.
