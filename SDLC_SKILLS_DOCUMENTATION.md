# SDLC Skills Suite — Documentazione Completa

Suite di 9 skill complementari per Claude Code che automatizzano l'intero ciclo di vita di un Business Requirement: dal setup del profilo progetto alla review della documentazione funzionale, dalla gestione delle risposte del funzionale all'analisi gap, dalla stima del team all'esecuzione delle task, dalla gestione degli aggiornamenti al debug post-rilascio, fino alla reportistica Excel. Tutti gli artefatti BR sono centralizzati nella repo `deloitte-profiles`, una repo separata e condivisa tra tutti gli sviluppatori e tutti i progetti.

## Architettura del Flusso

Tutti i path qui sotto sono relativi a `<profiles_repo>/<profilo>/`, dove `<profiles_repo>` e' la repo `deloitte-profiles` clonata in locale e `<profilo>` e' il nome del progetto.

```
BR / Documentazione
        |
        v
  [sdlc-profile-setup]  ──>  constitution/profile.json
        |                  agents/
        |                  references/
        |
        v
  [sdlc-reviewer]   ──>  plans/todo/<data>_<nome>/
        |                  |
        |            CLARIFY.md
        |            CLARIFY.docx
        |            requirements/
        |
        v
  [sdlc-clarify]    ──>  aggiorna CLARIFY.md/.docx
        |               con risposte del funzionale
        |
        v
  [sdlc-estimator]  ──>  plans/todo/<data>_<nome>/
        |                  |
        |            ESTIMATE.md
        |            ESTIMATE.xlsx
        |
        v
  [sdlc-analyzer]   ──>  plans/todo/<data>_<nome>/
        |                  |
        |            PLAN.md
        |            TASKS.md
        |
        v
  [sdlc-executor]   ──>  plans/in-progress/<data>_<nome>/
        |                  |
        |            + PROGRESS.md
        |
        |   (se BR aggiornato)
        |         |
        |         v
        |   [sdlc-updater]  ──>  aggiorna report + piano
        |                      preservando il progresso
        |
        |   (per reportistica)
        |         |
        |         v
        |   [sdlc-progress-report]  ──>  PROGRESS.xlsx
        |
        |   (per bug post-testing)
        |         |
        |         v
        |   [sdlc-debug]  ──>  BUG_REPORT.md
        |                    fix con sottoagenti + verifica
        |
        v
  (tutte le task completate)
        |
        v
                       plans/done/<data>_<nome>/
```

## Struttura Cartelle

Tutti gli artefatti BR sono centralizzati nella repo `deloitte-profiles`. Ogni progetto ha il proprio profilo con costituzione, agenti custom, riferimenti visuali e piani BR. La repo del codice contiene solo `.br-local.json` per puntare al profilo.

```
deloitte-profiles/                       # repo separata, centralizzata per tutti i progetti
└── <nome-progetto>/
    ├── constitution/
    │   └── profile.json
    ├── agents/                          # agenti custom .md per questo progetto
    ├── references/                      # mockup, screenshot, style guide, codice gold-standard
    └── plans/
        ├── todo/
        │   └── <data>_<nome-br>/
        │       ├── requirements/        # documentazione BR convertita in markdown
        │       ├── CLARIFY.md
        │       ├── CLARIFY.docx
        │       ├── PLAN.md
        │       ├── TASKS.md
        │       └── ESTIMATE.md / .xlsx
        ├── in-progress/
        │   └── <data>_<nome-br>/
        │       ├── (tutti i file da todo +)
        │       ├── PROGRESS.md
        │       ├── BUG_REPORT.md
        │       ├── PROGRESS.xlsx
        │       └── screenshots/
        └── done/
            └── <data>_<nome-br>/

repo-progetto/                           # qualsiasi repo del codice del progetto
└── .br-local.json                       # unico file BR nella repo del codice
                                         # contiene: profilo, profiles_repo, developer
```

Ogni cartella BR ha formato `<YYYY-MM-DD>_<nome-br>/` e si sposta come unita' tra le tre aree (`todo` → `in-progress` → `done`).

## Concorrenza

Tutte le skill BR sincronizzano la repo profili prima di leggere (`git pull`) e committano+pushano subito dopo aver scritto. Questo minimizza la finestra di conflitto e garantisce che tutti gli sviluppatori vedano sempre lo stato aggiornato del progresso.

Non sono necessari lock, file separati per developer, o aggregazione cross-branch — il modello centralizzato semplifica drasticamente la concorrenza.

---

## 1. BR Profile Setup

**Skill**: `sdlc-profile-setup`
**Path**: `~/.claude/skills/sdlc-profile-setup/SKILL.md`
**Trigger**: "crea profilo progetto", "setup profilo", "nuovo profilo", "configura il profilo"

### Scopo

Creare un nuovo profilo progetto in `deloitte-profiles` con auto-detect del codebase, domande guidate su dominio e design system, e configurazione automatica di `.br-local.json` nella repo del codice. E' il primo passo per qualsiasi nuovo progetto BR.

### Flusso Operativo

1. **Auto-detect codebase**: ispeziona la repo del codice in cui viene invocata (linguaggi, framework, struttura cartelle, package manager, file di configurazione) e propone una bozza di profilo.
2. **Domande guidate**: pone domande mirate su dominio funzionale (es. "booking", "ecommerce", "fintech"), design system in uso, convenzioni di naming, vincoli architetturali.
3. **Creazione struttura**: in `<profiles_repo>/<nome-progetto>/` crea:
   - `constitution/profile.json` — costituzione del progetto (dominio, vincoli, design)
   - `agents/` — cartella per agenti custom MD (vuota inizialmente)
   - `references/` — cartella per mockup/screenshot/gold-standard (vuota inizialmente)
   - `plans/todo/`, `plans/in-progress/`, `plans/done/` — strutture vuote
4. **Configurazione locale**: scrive `.br-local.json` nella repo del codice con: nome profilo, path della repo profili, nome sviluppatore.
5. **Commit & push**: commit della struttura iniziale sulla repo profili e push immediato per rendere il profilo visibile agli altri sviluppatori.

### Regole Fondamentali

1. Mai sovrascrivere un profilo esistente senza conferma esplicita
2. Sempre committare+pushare la struttura iniziale
3. Validare che `<profiles_repo>` sia raggiungibile prima di scrivere
4. Validare che la repo del codice non abbia gia' un `.br-local.json` (in tal caso chiedere conferma per sovrascrivere)

---

## 2. BR Reviewer

**Skill**: `sdlc-reviewer`
**Path**: `~/.claude/skills/sdlc-reviewer/SKILL.md`
**Trigger**: "rivedi il br", "review del br", "controlla la documentazione", "verifica il br"

### Scopo

Validare la qualita, coerenza e completezza della documentazione funzionale di un BR *prima* dell'analisi tecnica (sdlc-analyzer). Produce un report duale:
- **Parte 1 — Per il team funzionale**: elenca i problemi trovati (bloccanti e non) con domande precise a cui serve risposta
- **Parte 2 — Per il team tecnico**: assunzioni di default che il team adottera in assenza di chiarimenti, e disallineamenti tra terminologia/strutture del BR e del codice

Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali — non una gap analysis completa (quella la fa sdlc-analyzer), ma problemi di documentazione visibili solo confrontando col codebase.

### Flusso Operativo

La skill opera in 4 fasi sequenziali. Prima di ogni operazione legge `.br-local.json` per individuare la repo profili e il profilo, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

#### Fase 1 — Raccolta Input

Pone 3 domande una alla volta:

1. **Nome del BR** — identificativo per la cartella (es. "booking-v2" crea `<profiles_repo>/<profilo>/plans/todo/2026-04-28_booking-v2/`)
2. **Documentazione** — path ai file del BR. Accetta MD, PDF, DOCX, XLSX, PPTX, immagini.
3. **Codebase coinvolti** — nome, sigla, path per ogni repository. Servono per il check leggero contro il codice.

Prima di procedere, ricapitola tutti gli input e chiede conferma.

#### Fase 2 — Conversione Documentazione in MD

Stessa logica di conversione delle altre skill (doc-to-markdown per DOCX/DOC, markitdown per PDF/PPTX/XLSX, copia diretta per MD, Read per immagini). I file convertiti vanno nella cartella del BR: `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/requirements/`.

Questa fase viene eseguita da sdlc-reviewer: sdlc-analyzer non la ripete se trova i file gia convertiti.

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

Genera `CLARIFY.md` nella cartella del BR con:
- Esito sintetico (qualita complessiva, conteggio problemi, presenza bloccanti)
- **Parte 1 — Per il team funzionale**: problemi bloccanti e non bloccanti con domande precise
- **Parte 2 — Per il team tecnico**: tabella assunzioni proposte con rischio e costo di correzione, tabella disallineamenti col codice
- **Riepilogo per sdlc-analyzer**: sezione tecnica consumata automaticamente da sdlc-analyzer per incorporare le assunzioni nel piano

Dopo il MD, genera automaticamente `CLARIFY.docx` con pandoc. Il DOCX contiene placeholder "*(inserire qui la risposta)*" sotto ogni domanda, pronti per la compilazione da parte del funzionale.

Se ci sono bloccanti, consiglia di attendere chiarimenti dal funzionale prima di procedere con sdlc-analyzer, ma la decisione e dell'utente. Suggerisce di usare `sdlc-clarify` quando arrivano le risposte.

### Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (via pip o uvx)
- `pandoc` — per generazione CLARIFY.docx

---

## 3. BR Clarify

**Skill**: `sdlc-clarify`
**Path**: `~/.claude/skills/sdlc-clarify/SKILL.md`
**Trigger**: "chiarimenti ricevuti", "risposte ricevute", "il funzionale ha risposto", "ho le risposte"

### Scopo

Gestire le risposte del team funzionale alle domande sollevate da sdlc-reviewer nel CLARIFY.md. Aggiorna il report con le risposte, ri-valuta i bloccanti e le assunzioni, e rigenera il DOCX. Supporta risposte parziali e round multipli.

### Flusso Operativo

#### Fase 1 — Auto-detect CLARIFY.md

Esegue `git pull` sulla repo profili, poi cerca automaticamente `<profiles_repo>/<profilo>/plans/todo/*/CLARIFY.md` e `<profiles_repo>/<profilo>/plans/in-progress/*/CLARIFY.md`. Se ne trova uno lo propone, se piu di uno chiede quale usare, se nessuno informa che serve prima sdlc-reviewer. Analizza lo stato: quante domande hanno gia risposta e quante sono ancora aperte.

#### Fase 2 — Modalita Input

Supporta due modalita:

1. **DOCX compilato**: il funzionale ha compilato il CLARIFY.docx inserendo le risposte sotto i placeholder. La skill converte il DOCX con pandoc, confronta con l'originale per rilevare le risposte, e le presenta all'utente per conferma.

2. **Conversazione**: la skill presenta ogni domanda aperta una alla volta (prima i bloccanti, poi i non bloccanti). L'utente riporta la risposta o dice "salta" per le domande ancora senza risposta.

Le due modalita possono combinarsi: dopo aver processato il DOCX, la skill chiede se ci sono risposte aggiuntive da riportare a voce.

#### Fase 3 — Rivalutazione

Per ogni risposta ricevuta:

- **Bloccanti**: valuta se la risposta risolve il problema. Se si, lo stato diventa "Si → **RISOLTO**". Se la risposta e parziale o ambigua, resta bloccante con nota esplicativa e eventuale domanda di follow-up.
- **Non bloccanti**: confronta la risposta con l'assunzione proposta. L'assunzione viene classificata come **Confermata** (il funzionale concorda), **Rigettata** (il funzionale da un'indicazione diversa — la risposta del funzionale prevale), o resta **In attesa** (nessuna risposta).

Prima di modificare i file, presenta il riepilogo completo della rivalutazione e aspetta conferma.

#### Fase 4 — Aggiornamento Output

Aggiorna CLARIFY.md:
- Aggiunge "Risposta del funzionale" e "Data risposta" a ogni problema risposto
- Aggiorna la tabella assunzioni con colonne "Stato" e "Risposta funzionale"
- Sostituisce la sezione "Riepilogo per sdlc-analyzer" con formato arricchito: bloccanti risolti con sintesi risposta, bloccanti ancora aperti, stato di ogni assunzione (confermata/rigettata/in attesa), marcatore "Ultimo aggiornamento: \<data\> (sdlc-clarify)"

Rigenera CLARIFY.docx con pandoc. Committa+pusha subito dopo la scrittura.

#### Round Multipli

La skill puo essere eseguita piu volte sullo stesso CLARIFY.md. A ogni esecuzione:
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
- `sdlc-reviewer` — deve essere stato eseguito prima

---

## 4. BR Analyzer

**Skill**: `sdlc-analyzer`
**Path**: `~/.claude/skills/sdlc-analyzer/SKILL.md`
**Trigger**: "abbiamo un nuovo br"

### Scopo

Analizzare un nuovo Business Requirement confrontandolo con i codebase esistenti del progetto, identificare tutti i gap tra documentazione e codice, e produrre un piano di implementazione con task indipendenti assegnabili a sviluppatori muniti di Claude Code. Se sdlc-reviewer e stato eseguito prima, ne legge le assunzioni e salta la conversione dei documenti.

### Flusso Operativo

La skill opera in 4 fasi sequenziali. Prima di ogni operazione legge `.br-local.json`, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

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

I file convertiti vengono salvati in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/requirements/`. Se una conversione fallisce, segnala all'utente e usa il Read diretto come fallback. Da questo punto l'analisi lavora solo sui file MD convertiti.

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

Crea la struttura `<profiles_repo>/<profilo>/plans/todo/`, `<profiles_repo>/<profilo>/plans/in-progress/`, `<profiles_repo>/<profilo>/plans/done/` (se non esiste) e genera due file in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/`:

**PLAN.md** contiene:
- Metadati: data verifica, branch verificati, perimetro documentale, codebase verificati
- Esito sintetico: 2-3 frasi sullo stato complessivo
- Matrice di verifica: una riga per ogni requisito con stato FE/BE, evidenze con path esatti, descrizione del gap
- Gap aperti reali: sezione dettagliata per ogni gap con cosa richiede il BR, cosa esiste, cosa manca, impatto sui moduli
- Conclusione finale: riepilogo per funzionalita

**TASKS.md** contiene:
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

- **Organizzazione in stream**: le task sono raggruppate in stream funzionali coesi. Le task nello stesso stream condividono il contesto di codice e possono dipendere direttamente. Per le dipendenze cross-stream, sdlc-analyzer inserisce automaticamente **merge task** (`T-MERGE-NNN`) tra la task sorgente e quella dipendente. Le fondazioni condivise vanno in `stream-fondazioni`.
- **Indipendenza massima**: ogni task deve poter essere sviluppata in parallelo. Le dipendenze condivise vanno nella wave precedente. Minimizzare le dipendenze cross-stream.
- **Assegnazione per competenza e seniority**: task BE a sviluppatori BE, FE a FE. Task complesse ai senior/mid, task con scope chiuso ai junior con review assegnata. I senior non vanno caricati di implementazione continua.
- **Granularita giusta**: ogni task completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala.
- **Branch convention**: ogni task ha un branch `feature/<task-name>` dal branch principale della feature. Ordine di merge basato sulle dipendenze.
- **Autosufficiente per Claude Code**: ogni task contiene file esatti da modificare/creare, pattern da seguire, criteri di completamento verificabili, note specifiche.

### Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (via pip o uvx)

---

## 5. BR Executor

**Skill**: `sdlc-executor`
**Path**: `~/.claude/skills/sdlc-executor/SKILL.md`
**Trigger**: "lavora il task", "inizia a lavorare", "esegui il piano"

### Scopo

Permettere a ogni sviluppatore, assistito da un agente Claude Code, di eseguire le task assegnate dal piano generato da sdlc-analyzer. L'agente principale coordina il lavoro, delega l'implementazione a sottoagenti Claude, verifica i risultati e tiene aggiornato un file di progresso condiviso nella repo profili centralizzata.

### Flusso Operativo

Prima di ogni operazione legge `.br-local.json` per identificare la repo profili e lo sviluppatore, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver aggiornato il progresso.

#### Fase 1 — Raccolta Input

Cerca automaticamente i file nella struttura `<profiles_repo>/<profilo>/plans/` e li propone. Pone le domande una alla volta:

1. **File del piano**: gap report, piano di implementazione, file di progresso (opzionale). Se trova file in `<profiles_repo>/<profilo>/plans/todo/` o `<profiles_repo>/<profilo>/plans/in-progress/`, li propone direttamente.
2. **Path dei codebase locali**: poiche lo sviluppatore lavora su un PC diverso, estrae tutti i path dei codebase menzionati nel report e chiede i corrispondenti path locali.
3. **Path della documentazione locale**: estrae i nomi dei file di documentazione dal report e chiede i path locali. Se non sono tutti disponibili, lavora dal gap report che contiene gia i dettagli estratti.
4. **Identita sviluppatore**: legge il developer da `.br-local.json` e propone la lista delle sue task dal piano. Se manca, mostra la lista completa dal piano e chiede.

Alla conferma, sposta report e piano da `<profiles_repo>/<profilo>/plans/todo/` a `<profiles_repo>/<profilo>/plans/in-progress/`.

#### Fase 2 — Gestione del File di Progresso

Se il file non esiste, lo crea (`PROGRESS.md`) in `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/` con:
- Tabella riepilogativa (task totali, completate, in corso, da iniziare, bloccate, progresso complessivo)
- Tabella stato task (ID, Attivita, Owner, Progresso %, Stato, Branch, Note) con tutte le task a 0%
- Log attivita cronologico

Se il file esiste, lo legge, sincronizza con il piano e mostra lo stato attuale delle task dello sviluppatore.

Aggiorna il progresso a ogni cambio di stato significativo: task che passa a "In corso", sottoagente che completa una parte, task completata, task bloccata. Dopo ogni aggiornamento, commit+push immediato sulla repo profili.

#### Fase 3 — Lavorazione Task

**Selezione task**: presenta le task assegnate allo sviluppatore in ordine di priorita (P0 > P1 > P2) e wave, chiede conferma prima di iniziare.

**Controllo dipendenze**: la regola e semplice — una dipendenza e soddisfatta quando il suo stato e **"Completata"**. Non serve nessun controllo sugli stream: le dipendenze cross-stream sono gestite tramite merge task esplicite (`T-MERGE-*`) inserite nel piano da sdlc-analyzer. Le merge task (T-MERGE-*) sono task speciali: quando l'executor le incontra, guida lo sviluppatore nel merge del branch e nella verifica della build, senza lanciare sottoagenti per implementazione di codice.

Se le dipendenze non sono soddisfatte, blocca e propone alternative: passare a un'altra task senza dipendenze bloccanti, oppure attendere.

**Creazione branch**: crea il branch `feature/<task-name>` dalla base indicata nel piano, aggiorna il progresso.

**Esecuzione con sottoagenti**: l'agente principale coordina, i sottoagenti implementano. Per ogni task:

1. Legge la descrizione dal piano e dal gap report
2. Scompone in sotto-lavori (entita, servizi, controller, componenti FE, test, documentazione)
3. Lancia sottoagenti con prompt autosufficienti che includono: contesto del progetto, cosa fare con file specifici, riferimenti al gap report, convenzioni osservate, vincoli, output atteso
4. Parallelizza sotto-lavori indipendenti, sequenzia quelli dipendenti

**Verifica in 3 fasi**: dopo ogni sotto-step il lavoro viene verificato con un ciclo strutturato:

- **Fase A -- Tecnica**: test tutti verdi (happy path + edge case + error case), build compila senza errori, nessun warning critico
- **Fase B -- Coerenza**: ogni requisito della task viene verificato contro il codice effettivamente prodotto. Se un requisito non e coperto, si torna a implementare prima di procedere
- **Fase C -- Riesame**: second look critico sul codice (leggibilita, naming, separation of concerns), sulle asserzioni dei test (verificano davvero il comportamento atteso?), e sulla copertura degli edge case

Se una qualsiasi fase fallisce, il sottoagente corregge e il ciclo riparte dalla Fase A. Solo quando tutte e tre le fasi passano il sotto-step e considerato verificato.

**Suggerimento commit**: non committa mai autonomamente sul codice. Quando un sotto-step e completo e verificato, avvisa lo sviluppatore con lista file, stato test/build e messaggio di commit suggerito. Aspetta conferma prima di proseguire. (Il commit+push sulla repo profili per il file di progresso e' invece automatico.)

**Completamento task — Ciclo di verifica finale**: una task e completa solo quando TUTTI i criteri sono soddisfatti e il ciclo di verifica finale e superato:

1. Requisiti implementati (tutto cio che il gap report e il piano richiedono)
2. Codice completo (nessun placeholder, nessun TODO)
3. Documentazione (codice documentato dove il "perche" non e ovvio)
4. Test unitari scritti e tutti verdi — inclusi obbligatoriamente:
   - **Happy path**: il flusso principale funziona come atteso
   - **Edge case**: valori limite, input vuoti, liste vuote, null/undefined, valori massimi
   - **Error case**: input invalidi, errori di rete/DB, permessi negati, risorse non trovate
5. Build compila senza errori
6. **Tabella di tracciabilita**: prima di dichiarare completa, l'agente produce una tabella che mappa ogni requisito della task al codice che lo implementa e ai test che lo verificano:

   | Requisito | File/Funzione | Test |
   |---|---|---|
   | Req-1: ... | src/... metodo X | test/... "should ..." |
   | Req-2: ... | src/... metodo Y | test/... "should ..." |

   Se una riga della tabella ha colonne vuote (codice o test mancanti), la task NON e completa

Al completamento, aggiorna il progresso a 100% con stato "Completata" e propone la prossima task disponibile.

**Spostamento in done**: quando tutte le task del piano (non solo quelle dello sviluppatore) sono in stato "Completata", sposta tutti i file in `<profiles_repo>/<profilo>/plans/done/<data>_<nome>/`.

#### Fase 4 — Gestione Situazioni Speciali

- **Task bloccata**: segna come "Bloccata" nel progresso con motivazione, propone alternative (altra task, risolvere il blocco, fermarsi)
- **Ripresa del lavoro**: quando invocata con progresso esistente, riprende le task "In corso", verifica se i blocchi sono stati risolti
- **Conflitti di merge**: guida lo sviluppatore passo per passo nel merge/rebase, senza eseguire automaticamente

### Regole Fondamentali

1. Mai committare autonomamente sulla repo del codice
2. Mai procedere senza conferma
3. Mai ignorare le dipendenze
4. Aggiornare sempre il progresso e fare commit+push immediato sulla repo profili
5. Verificare prima di dichiarare completo
6. Il sottoagente implementa, l'agente principale coordina

---

## 6. BR Updater

**Skill**: `sdlc-updater`
**Path**: `~/.claude/skills/sdlc-updater/SKILL.md`
**Trigger**: "il br e stato aggiornato", "aggiorna il piano", "nuova versione del br"

### Scopo

Quando il BR o la documentazione vengono aggiornati, propagare le modifiche al gap report e al piano di implementazione senza perdere il lavoro gia fatto. Principio guida: mai sovrascrivere il progresso.

### Flusso Operativo

Prima di ogni operazione legge `.br-local.json`, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

#### Fase 1 — Raccolta Input

Cerca automaticamente i file esistenti in `<profiles_repo>/<profilo>/plans/` e pone le domande una alla volta:

1. **File esistenti**: gap report, piano, progresso da usare come base
2. **Documentazione aggiornata**: path dei file nuovi/modificati, specificando se sostituiscono un documento esistente o sono nuovi
3. **Codebase**: conferma se i path sono cambiati o invariati
4. **Team**: conferma se la composizione e cambiata (sviluppatori aggiunti, rimossi, ruoli cambiati)

#### Fase 2 — Analisi Delta Documentazione

1. **Conversione**: converte i nuovi documenti in MD (stessa procedura di sdlc-analyzer) in `<profiles_repo>/<profilo>/plans/<area>/<data>_<nome>/requirements/`
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

## 7. BR Debug

**Skill**: `sdlc-debug`
**Path**: `~/.claude/skills/sdlc-debug/SKILL.md`
**Trigger**: "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "lavora il bug", "fix il bug", "debug br"

### Scopo

Gestire i bug segnalati dai funzionali durante e dopo il testing di un Business Requirement. Importa bug da Excel o Jira, li collega alle task del piano, li assegna agli sviluppatori, esegue i fix con sottoagenti Claude e li verifica in 3 fasi, gestisce la chiusura con validazione funzionale e il re-import iterativo.

### Flusso Operativo

Prima di ogni operazione legge `.br-local.json`, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

#### Fase 1 — Import Bug

Due modalita supportate:

1. **Excel**: l'utente fornisce un file Excel con i bug segnalati. La skill legge le colonne (ID, Titolo, Descrizione, Severita, Owner, Stato, ...), normalizza i campi e propone un riepilogo.
2. **Jira**: tramite la skill `jira` o l'integrazione MCP, importa i ticket della query/filtro specificato.

I bug importati vengono salvati in `BUG_REPORT.md` nella cartella `<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/`. Ogni bug viene collegato (quando possibile) alla task del piano di provenienza.

#### Fase 2 — Assegnazione

Assegna i bug agli sviluppatori basandosi su: owner della task collegata, competenza (BE/FE), carico attuale. L'utente puo' confermare o modificare le assegnazioni.

#### Fase 3 — Fix con Sottoagenti

Per ogni bug:

1. **Riproduzione**: legge la descrizione, esplora il codice impattato, identifica la root cause
2. **Implementazione**: lancia un sottoagente con prompt autosufficiente per implementare il fix
3. **Verifica in 3 fasi** (stessa di sdlc-executor):
   - **Fase A -- Tecnica**: test verdi, build pulita, regressione esistente non rotta
   - **Fase B -- Coerenza**: il fix risolve effettivamente il bug descritto
   - **Fase C -- Riesame**: il fix non introduce nuovi problemi, e' nel posto giusto, e' minimo

#### Fase 4 — Chiusura

Dopo il fix verificato, lo stato del bug passa a "Fix pronto". L'utente conferma di averlo testato col funzionale. Solo dopo conferma funzionale, lo stato passa a "Chiuso".

#### Fase 5 — Re-Import Iterativo

La skill puo' essere re-eseguita con un nuovo Excel/import Jira per importare bug aggiunti, riaperti, o aggiornati. I bug esistenti non vengono sovrascritti — solo aggiornati nei campi che cambiano (stato, note).

### Regole Fondamentali

1. Mai chiudere un bug senza conferma del funzionale
2. Mai sovrascrivere bug gia' fissati (solo aggiornare stato)
3. Sempre eseguire la verifica in 3 fasi
4. Sempre commit+push sulla repo profili dopo ogni aggiornamento

### Dipendenze

- `openpyxl` (Python) — per lettura Excel bug
- `jira` skill o MCP — per import da Jira (opzionale)

---

## 8. BR Progress Report

**Skill**: `sdlc-progress-report`
**Path**: `~/.claude/skills/sdlc-progress-report/SKILL.md`
**Trigger**: "genera il report excel", "aggiorna l'excel", "stato avanzamento", "esporta il progresso"

### Scopo

Generare o aggiornare un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo. Pensato per la reportistica verso il management e il tracking visuale del progetto.

### Flusso Operativo

Prima di ogni operazione legge `.br-local.json`, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

#### Fase 1 — Individuazione File Sorgente

Cerca automaticamente nella struttura `<profiles_repo>/<profilo>/plans/`:
- **Piano di Implementazione** (obbligatorio)
- **File di Progresso** (opzionale — se non esiste, tutte le task partono da 0%)
- **Gap Report** (opzionale — usato per arricchire le descrizioni)

Verifica se esiste gia un file `PROGRESS.xlsx`:
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

Salva `PROGRESS.xlsx` nella stessa cartella del piano (`<profiles_repo>/<profilo>/plans/in-progress/<data>_<nome>/`). In modalita aggiornamento preserva eventuali note manuali aggiunte dall'utente. Comunica riepilogo: task totali, completate, in corso, progresso complessivo, eventuali task bloccate.

### Dipendenze

- `openpyxl` (Python) — `pip install openpyxl`

---

## 9. BR Estimator

**Skill**: `sdlc-estimator`
**Path**: `~/.claude/skills/sdlc-estimator/SKILL.md`
**Trigger**: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team"

### Scopo

Stimare il team necessario per completare un BR entro una deadline, con simulazioni what-if su team, deadline, scope e rischio. Produce scenari ottimistico/realistico/pessimistico con timeline, bottleneck, allocazione team e suggerimenti scope cut. Genera report MD + Excel.

### Modalita

Due modalita supportate:

1. **Rough (pre-analisi)**: stima derivata dalla documentazione BR convertita in markdown, prima che sdlc-analyzer sia stato eseguito. Utile per fornire indicazioni iniziali sul team in fase di pre-vendita o pianificazione.
2. **Dettagliata (post-analisi)**: stima derivata dal `TASKS.md` e dal `PLAN.md`. Molto piu' precisa, usa la granularita' delle task e le wave del piano.

### Flusso Operativo

Prima di ogni operazione legge `.br-local.json`, esegue `git pull` sulla repo profili, e committa+pusha subito dopo aver scritto.

#### Fase 1 — Identificazione Modalita

Cerca in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/` la presenza di `TASKS.md`:
- Se presente → modalita dettagliata
- Se assente ma `requirements/` presente → modalita rough
- Se entrambi assenti → richiede di eseguire prima sdlc-reviewer (per requirements) o sdlc-analyzer (per piano)

#### Fase 2 — Raccolta Input

- **Deadline**: data target di consegna
- **Pool risorse disponibili**: composizione del team disponibile (numero per ruolo/seniority)
- **Costo (opzionale)**: per stime di budget
- **Rischio**: fattore di buffer (low/medium/high) — default: medium

#### Fase 3 — Calcolo Scenari

Tre scenari sempre calcolati:

- **Ottimistico**: massima parallelizzazione, team senior, nessun blocco esterno
- **Realistico**: parallelizzazione tipica, mix di seniority, qualche blocco
- **Pessimistico**: bottleneck attesi, team meno esperto, blocchi esterni

Per ogni scenario calcola: durata calendario, FTE necessari per ruolo, picco team, bottleneck identificati, fattibilita' della deadline.

#### Fase 4 — Simulazioni What-If

Permette di simulare:
- Aumento/riduzione team
- Modifica deadline
- Scope cut: suggerisce quali task tagliare per rispettare la deadline con team dato
- Cambio mix di seniority

#### Fase 5 — Output

Genera in `<profiles_repo>/<profilo>/plans/todo/<data>_<nome>/`:
- `ESTIMATE.md`: report completo con scenari, simulazioni, bottleneck, raccomandazioni
- `ESTIMATE.xlsx`: foglio Excel con tabelle scenari, allocazione team per settimana, what-if

### Dipendenze

- `openpyxl` (Python) — per generazione Excel

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

Le dipendenze cross-stream sono gestite tramite **merge task esplicite** (`T-MERGE-NNN`) inserite nel piano da sdlc-analyzer. Non esiste una logica di sblocco basata sugli stream nell'executor: tutte le dipendenze si sbloccano semplicemente quando lo stato e "Completata".

---

## Dipendenze Globali

| Dipendenza | Usata da | Installazione |
|---|---|---|
| `doc-to-markdown` skill | sdlc-reviewer, sdlc-analyzer, sdlc-updater | gia installata in `~/.claude/skills/doc-to-markdown/` |
| `markitdown` | sdlc-reviewer, sdlc-analyzer, sdlc-updater | `pip install 'markitdown[all]'` oppure via `uvx` |
| `pandoc` | sdlc-reviewer, sdlc-clarify | disponibile su PATH |
| `openpyxl` | sdlc-progress-report, sdlc-debug, sdlc-estimator | `pip install openpyxl` |
| `git` | tutte (sync repo profili) | disponibile su PATH |
| `jira` skill / MCP | sdlc-debug (opzionale) | configurato globalmente |

## Trigger Registrati (CLAUDE.md)

| Frase | Skill |
|---|---|
| "crea profilo progetto" / "setup profilo" / "nuovo profilo" / "configura il profilo" | sdlc-profile-setup |
| "rivedi il br" / "review del br" / "controlla la documentazione" / "verifica il br" | sdlc-reviewer |
| "chiarimenti ricevuti" / "risposte ricevute" / "il funzionale ha risposto" / "ho le risposte" | sdlc-clarify |
| "abbiamo un nuovo br" | sdlc-analyzer |
| "lavora il task" / "inizia a lavorare" / "esegui il piano" | sdlc-executor |
| "il br e stato aggiornato" / "aggiorna il piano" / "nuova versione del br" | sdlc-updater |
| "ci sono dei bug" / "bug dal funzionale" / "lavora il bug" / "debug br" | sdlc-debug |
| "genera il report excel" / "aggiorna l'excel" / "stato avanzamento" / "esporta il progresso" | sdlc-progress-report |
| "stima il br" / "quanti sviluppatori servono" / "simulazione team" / "stima effort" | sdlc-estimator |
