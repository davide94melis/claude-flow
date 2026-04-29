---
name: br-analyzer
description: Analizza un nuovo Business Requirement (BR) confrontandolo con i codebase esistenti del progetto, genera un gap report dettagliato per funzionalità e un piano di implementazione con task indipendenti assegnate a sviluppatori muniti di Claude Code. Usa questa skill quando l'utente dice "abbiamo un nuovo br", "nuovo br", "c'è un br nuovo", "analizza il br", "gap analysis br", "nuovo business requirement", o qualsiasi variazione che implichi l'arrivo di un nuovo documento di requisiti da analizzare e pianificare. Attivala anche quando l'utente menziona la necessità di confrontare documentazione di requisiti con il codice per trovare cosa manca e pianificare lo sviluppo.
---

# BR Analyzer — Gap Report & Piano di Implementazione

Questa skill guida l'analisi di un nuovo Business Requirement: dal confronto con i codebase al piano di sviluppo con task indipendenti per un team di sviluppatori, ognuno munito di Claude Code.

Il flusso BR completo:
```
br-reviewer → br-clarify → br-analyzer → br-executor → br-updater
                                                      ↘ br-progress-report
```

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (solo se `br-reviewer` non e' stato eseguito prima — se trova `br-docs-converted/` nella cartella del BR, salta questa fase)
3. **Analisi gap** (confronto documentazione vs codice)
4. **Generazione output** (2 file MD: gap report + piano di implementazione, nella cartella del BR)

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finche' l'utente non ha risposto.

### Domanda 0 — Cartella BR esistente

Prima di chiedere qualsiasi cosa, verifica se esiste una cartella BR in `plans/todo/` con un `REVIEW_BR.md` (segno che `br-reviewer` e' stato eseguito):

```bash
ls plans/todo/*/REVIEW_BR.md 2>/dev/null
```

**Se trovi una cartella con REVIEW_BR.md**, proponila:

> Ho trovato una cartella BR con review gia' completata:
> - `plans/todo/2026-04-28_booking-v2/REVIEW_BR.md`
> - Documentazione convertita in `br-docs-converted/`
>
> Uso questa come base? Le assunzioni dalla review verranno incorporate nel piano.

Se l'utente conferma:
- Leggi il `REVIEW_BR.md`, in particolare la sezione "Riepilogo per br-analyzer"
- Controlla se `br-clarify` e' stato eseguito: cerca "Ultimo aggiornamento:" con "(br-clarify)" nel riepilogo
- **Se br-clarify e' stato eseguito**:
  - Estrai i bloccanti risolti → usali come fatti certi nell'analisi gap
  - Estrai le assunzioni confermate dal funzionale → usale come fatti
  - Estrai le assunzioni rigettate → usa la risposta del funzionale al posto dell'assunzione
  - Estrai le assunzioni adottate senza risposta → usale con rischio segnalato
  - Mostra all'utente: "Review con chiarimenti: N bloccanti risolti, M assunzioni confermate, K bloccanti ancora aperti"
  - I bloccanti ancora aperti vengono segnalati come "Da chiarire" nel gap report
- **Se br-clarify NON e' stato eseguito**:
  - Usa la sezione "Riepilogo per br-analyzer" nella sua forma originale (assunzioni confermate dall'utente e bloccanti aperti)
- Usa i file in `br-docs-converted/` per l'analisi (salta la Fase 2)
- Salta le domande su documentazione e codebase — leggile dal REVIEW_BR.md
- Procedi direttamente alla Domanda 3 (Team di sviluppo)

**Se non trovi nulla**, chiedi il nome del BR:

> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Poi procedi con le domande successive.

### Domanda 1 — Codebase

> Quali sono le repository/codebase coinvolte in questo BR?
> Per ognuna, dammi:
> - **Nome** (es. "back-end", "front-end", "api-gateway", "mobile-app", "notification-service" — qualsiasi nome che identifichi la repo)
> - **Sigla** (un'abbreviazione breve, es. "BE", "FE", "GW", "MOB", "NS" — verrà usata nelle tabelle e nei report)
> - **Path** (il path locale al codebase)
>
> Elenca tutte quelle coinvolte, senza limiti. Se una repo non è coinvolta nel BR, non includerla.
>
> Esempio:
> - Back-end (BE) → `/path/to/backend`
> - Front-end (FE) → `/path/to/frontend`
> - Notification Service (NS) → `/path/to/notifications`

Salva i nomi, le sigle e i path forniti. Usa le sigle dell'utente in tutto il report e nel piano. Se l'utente fornisce una sola repo, è perfettamente valido — non forzare una lista lunga.

### Domanda 2 — Documentazione

> Dove trovo la documentazione del BR? Dammi i path per:
> - **BR** (il documento principale dei requisiti)
> - **Mockup** (se presenti)
> - **Qualsiasi altro file rilevante** (specifiche tecniche, template, mapping, matrici)
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Team di sviluppo

> Chi lavorerà all'implementazione? Per ogni sviluppatore dimmi:
> - **Nome** (o identificativo, es. "Marco", "Dev-Senior")
> - **Ruolo/Area**: su quali repository lavora (usa le sigle definite prima, es. "BE", "FE", "BE+FE", "GW+NS", o qualsiasi combinazione)
> - **Seniority**: Junior / Mid / Senior
>
> Esempio: "Marco - BE senior, Luca - FE mid, Anna - BE+GW junior"

### Prima di procedere

Dopo aver raccolto tutti gli input, ricapitola quello che hai ricevuto e chiedi conferma:

> Riepilogo:
> - Repository coinvolte:
>   [per ognuna: Nome (SIGLA) → path]
> - Documentazione: [lista con path]
> - Team: [lista con ruolo e seniority]
>
> Confermo e procedo con l'analisi?

Procedi solo dopo la conferma.

---

## Fase 2 — Conversione Documentazione in Markdown

**Se `br-reviewer` e' stato eseguito** e la cartella `br-docs-converted/` esiste gia' nella cartella del BR (`plans/todo/<data>_<nome>/br-docs-converted/`), **salta completamente questa fase** e vai alla Fase 3. La conversione e' gia' stata fatta da br-reviewer.

**Se `br-reviewer` non e' stato eseguito**, converti tutti i documenti non-MD in formato Markdown. Questo riduce significativamente il contesto necessario e rende i documenti piu' leggibili per l'analisi.

### Procedura di conversione

Crea la cartella del BR e la sottocartella per i documenti convertiti:

```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted"
```

Per ogni file di documentazione fornito:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown è disponibile globalmente
markitdown "<path-file>" > "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/<nome-file>.md"
```

**File `.md`** — Copia direttamente in `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`.

**Immagini (mockup `.png`, `.jpg`, ecc.)** — Non convertire. Leggile con Read (supporto multimodale) durante la fase di analisi e descrivi nel dettaglio cosa vedi.

### Verifica conversione

Dopo la conversione, verifica che ogni file MD generato contenga contenuto valido. Se un file risulta vuoto o corrotto, segnalalo all'utente e usa il Read diretto sul file originale come fallback.

Comunica all'utente lo stato della conversione:

> Conversione completata:
> - `BR_v24.docx` → `br-docs-converted/BR_v24.md` (OK)
> - `Mockup_Booking.pptx` → `br-docs-converted/Mockup_Booking.md` (OK)
> - `mockup_dashboard.png` → letto direttamente come immagine
>
> Procedo con l'analisi gap.

Da questo punto in poi, l'analisi lavora sui file MD convertiti in `br-docs-converted/`, non sui file originali.

---

## Fase 3 — Analisi Gap

### 3.1 — Lettura della documentazione

Leggi integralmente ogni documento MD convertito nella cartella `br-docs-converted/` (dentro la cartella del BR). Per le immagini (mockup), usa Read sul file originale e descrivi nel dettaglio cosa vedi, mappando le UI ai componenti da implementare.

Da ogni documento, estrai:
- Ogni requisito funzionale (cosa deve fare il sistema)
- Ogni requisito tecnico (come deve farlo, vincoli, integrazioni)
- Ogni elemento visuale dai mockup (layout, componenti, flussi utente)

Organizza i requisiti per **funzionalità** (es. "Dashboard", "Booking", "Monitoraggio"), non per documento o per modulo tecnico.

### 3.2 — Esplorazione dei codebase

Per ogni codebase fornito, analizza:
- **Struttura del progetto**: package, moduli, layer architetturali
- **Modello dati**: entità, DTO, migration, relazioni
- **API/Controller**: endpoint esposti, payload, validazioni
- **Servizi**: logica di business, workflow, macchine a stati
- **Repository**: query, viste, materializzazioni
- **Frontend** (se applicabile): componenti, routing, modelli, i18n, servizi
- **Configurazione**: properties, feature flag, sicurezza

Usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase quando possibile.

### 3.3 — Confronto e classificazione gap

Per ogni funzionalità richiesta dal BR, confronta con il codice esistente e classifica:

| Stato | Significato |
|---|---|
| **Coperto** | Implementato correttamente, nessun gap |
| **Parziale** | Implementato in parte, manca qualcosa di specifico |
| **Mancante** | Non implementato, da sviluppare da zero |
| **Discrepanza** | Implementato ma diverso da quanto richiesto dal BR |
| **Da chiarire** | Il BR è ambiguo o il codice suggerisce un'interpretazione diversa |

Per ogni gap, documenta:
- **Cosa richiede il BR** (con riferimento a sezione/pagina del documento)
- **Cosa esiste nel codice** (con path esatti a file/classi/metodi)
- **Cosa manca o è diverso** (con dettaglio sufficiente per implementare)
- **Repository coinvolte** (usa le sigle fornite dall'utente)
- **Complessità stimata** (Bassa / Media / Alta)

Il livello di dettaglio deve essere sufficiente perché un agente Claude Code, leggendo solo il gap report, possa capire esattamente cosa va fatto senza dover rileggere il BR originale.

---

## Fase 4 — Generazione Output

Se la cartella del BR non esiste ancora (br-reviewer non eseguito), creala:

```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>" plans/in-progress plans/done
```

Genera entrambi i file nella cartella del BR in `plans/todo/`. Questo e' lo stato iniziale: la cartella intera si sposta in `in-progress/` quando uno sviluppatore avvia la lavorazione con `br-executor`, e in `done/` al completamento di tutte le task.

### 4.1 — Gap Report

**Path file**: `plans/todo/<YYYY-MM-DD>_<nome>/GAP_REPORT_BR.md`

Struttura:

```
# Report Verifica BR [nome/versione]

Data verifica: `<data>`

Branch verificato:
[per ogni repo coinvolta:]
- <SIGLA>: `<branch>`

Perimetro documentale verificato:
- BR: `<path>`
- Mockup: `<path>`
[altri documenti]

Codebase verificati:
[per ogni repo coinvolta:]
- <SIGLA> (<nome completo>): `<path>`

## Assunzioni da review

[Se br-reviewer non e' stato eseguito:]
Nessuna review preventiva eseguita.

[Se br-reviewer eseguito ma br-clarify NON eseguito:]
Assunzioni confermate dall'utente: [lista A-XXX dal REVIEW_BR.md]
Bloccanti aperti: [lista dal REVIEW_BR.md, segnalati come "Da chiarire" nei gap]

[Se br-clarify e' stato eseguito:]
Bloccanti risolti (risposte del funzionale, usate come fatti nell'analisi):
- [B1] [Titolo] → [sintesi risposta]
[...]

Bloccanti ancora aperti (segnalati come "Da chiarire" nei gap):
- [BN] [Titolo]
[...]

Assunzioni confermate dal funzionale (usate come fatti): A-001, A-003
Assunzioni rigettate dal funzionale (usata la risposta al posto dell'assunzione):
- A-005: "[risposta corretta del funzionale]"
[...]
Assunzioni adottate senza risposta (usate con rischio segnalato): A-002, A-004

## Esito sintetico

[2-3 frasi che riassumono lo stato complessivo: cosa e' coperto, dove sono i gap principali]

## Matrice di verifica

Genera dinamicamente una colonna per ogni repository coinvolta, usando le sigle fornite dall'utente.

| Requisito | <SIGLA_1> | <SIGLA_2> | ... <SIGLA_N> | Stato | Evidenze | Gap |
|---|---|---|---|---|---|---|
| [Requisito dal BR] | [Implementato/Non implementato/N/A] | [Implementato/Non implementato/N/A] | ... | [Coperto/Parziale/Mancante/Discrepanza/Da chiarire] | [Path esatti a file e classi rilevanti, per ogni repo] | [Descrizione precisa del gap, o "Nessuno"] |

[Una riga per ogni requisito identificato, raggruppate per funzionalità. Se il progetto ha una sola repo, la matrice avrà una sola colonna repo.]

## Gap aperti reali

### 1. [Nome gap]

[Dettaglio completo del gap:]
- Cosa richiede il BR
- Cosa esiste nel codice (con path)
- Cosa manca
- Impatto su quali moduli

### 2. [Nome gap]
[...]

## Conclusione finale

[Riepilogo: cosa è coperto, cosa è mancante, cosa è da chiarire.
 Organizzato per funzionalità, con lo stato di ognuna.]
```

Ogni riga della matrice e ogni gap aperto deve contenere path esatti ai file rilevanti, in modo che gli agenti Claude Code possano navigare direttamente al codice interessato.

### 4.2 — Piano di Implementazione

**Path file**: `plans/todo/<YYYY-MM-DD>_<nome>/PIANO_IMPLEMENTAZIONE_BR.md`

Struttura:

```
# Piano Implementazione [Nome feature/BR]

Data: `<data>`

Assunzioni:
- [contesto, cosa e' gia' completato, perimetro residuo]
- [se br-reviewer e' stato eseguito, includi qui tutte le assunzioni confermate dalla review, con riferimento al REVIEW_BR.md]
- team disponibile:
  - [per ogni sviluppatore: ruolo e seniority]

## Obiettivo

[1-2 frasi: massimizzare parallelismo, ridurre colli di bottiglia]

## Strategia di esecuzione

[Come è diviso il lavoro: fondazioni, stream paralleli, integrazione.
 Quali sono i punti di congelamento iniziali che bloccano tutto il resto.]

## Distribuzione team consigliata

[Per ogni sviluppatore, descrivere il tipo di lavoro assegnato,
 tenendo conto della seniority reale:
 - Senior: governance, design, review, pairing, sblocco
 - Mid: stream core a media-alta complessità
 - Junior: stream guidati, scope ben chiuso, con review frequente]

## Definizione degli Stream

Ogni stream rappresenta un flusso di lavoro funzionalmente coeso: un insieme di task che appartengono alla stessa area funzionale e lavorano sullo stesso branch o su branch sequenziali. Le task all'interno dello stesso stream condividono il contesto di codice — il completamento di una rende il codice disponibile localmente per la successiva senza bisogno di merge.

Definisci gli stream basandoti sulle funzionalità del BR, non sulla struttura tecnica. Esempi:
- `stream-booking` — tutte le task relative alla funzionalità Booking
- `stream-monitoraggio` — tutte le task relative al Monitoraggio
- `stream-fondazioni` — task di base che creano entità/enum/migration condivise

Regole:
- Uno stream può avere più owner (es. task BE e FE della stessa funzionalità)
- Un owner può lavorare su più stream
- Le task di Wave 0 (fondazioni) vanno tipicamente in uno stream dedicato `stream-fondazioni`
- Lo stream è un campo organizzativo per raggruppare le task — NON ha ruolo nella logica di sblocco delle dipendenze dell'executor

**Dipendenze cross-stream e merge task automatici**: quando una task in uno stream dipende da una task in un altro stream, br-analyzer inserisce automaticamente una **merge task** tra le due. La merge task rappresenta l'atto di mergiare il branch dello stream sorgente nel branch base condiviso. Questo rende esplicita la dipendenza: l'executor non deve conoscere la logica degli stream — tutte le dipendenze si sbloccano semplicemente quando lo stato è "Completata". All'interno dello stesso stream, le dipendenze dirette sono sufficienti e non serve alcuna merge task.

[Lista degli stream identificati con descrizione, es:]
- `stream-fondazioni` — entità, enum, migration condivise
- `stream-booking` — funzionalità di gestione booking
- `stream-monitoraggio` — dashboard e pratiche monitoraggio
[...]

## Backlog operativo

| ID | Stream | Owner | Area | Priorità | Attività | Descrizione | Dipendenze | Effort |
|---|---|---|---|---:|---|---|---|---:|
| `T-001` | `stream-fondazioni` | `[Dev]` | BE/FE | P0/P1/P2 | [Nome task] | [Descrizione dettagliata, con riferimento ai gap del report, file da toccare, pattern da seguire] | [ID dipendenze o "Nessuna"] | `N gg` |

[Una riga per ogni task]

**Nota sulle merge task**: le task di tipo merge usano il formato ID `T-MERGE-NNN` (dove NNN è l'ID numerico della task sorgente che viene mergiata, es. `T-MERGE-005`). Hanno type "merge", effort ~0.5gg, e la descrizione specifica quale branch mergiare, in quale branch base, e di verificare la build dopo il merge.

## Ordine di esecuzione

### Wave 0 — Fondazioni (`stream-fondazioni`)
- [task fondazionali che sbloccano tutto il resto]

### Merge tasks (tra wave)
- [merge task generate automaticamente per dipendenze cross-stream, es. T-MERGE-005]

### Wave 1
- [Per ogni stream attivo in questa wave, lista task]

### Wave 2
[...]

### Wave N — Integrazione e UAT
[...]

## Dipendenze critiche

- [lista delle dipendenze che possono creare colli di bottiglia]

## Piano per persona

### [Nome/ID sviluppatore]
- [lista task assegnate in ordine]
- [note su pairing, review, supporto]

[Ripeti per ogni sviluppatore]

## Stima complessiva

### Effort
[per ogni repository/area coinvolta:]
- <SIGLA>: circa `N gg/uomo`
- Integrazione e UAT: circa `N gg/uomo`

### Durata calendario realistica
[Scenario realistico settimana per settimana]
[Scenario aggressivo con rischi]

## Rischi principali

- [rischi tecnici, organizzativi, di scope]

## Raccomandazioni operative

- [consigli pratici per l'esecuzione]

## Deliverable minimi

- [lista di cosa deve funzionare per considerare il perimetro chiuso]
```

### Principi per la creazione delle task

Quando scomponi il lavoro in task, questi principi guidano le decisioni:

**Organizzazione in stream** — Raggruppa le task in stream funzionali coesi (es. `stream-booking`, `stream-monitoraggio`). Le task nello stesso stream condividono il contesto di codice e possono dipendere direttamente tra loro. Per le dipendenze cross-stream, inserisci sempre una merge task esplicita tra la task sorgente e quella dipendente.

**Merge task per dipendenze cross-stream** — Quando una task in stream-X dipende da una task in stream-Y, br-analyzer DEVE inserire una merge task tra di esse (es. `T-005` in `stream-fondazioni` -> `T-MERGE-005` -> `T-010` in `stream-booking`). La merge task:
- Appartiene allo stream sorgente (stream-Y)
- Ha come owner suggerito lo sviluppatore che ha completato la task sorgente
- Ha effort ~0.5gg e type "merge"
- La descrizione specifica: quale branch mergiare (`feature/<task-name>`), in quale branch base, verificare la build dopo il merge
- All'interno dello stesso stream non serve alcuna merge task — la dipendenza diretta è sufficiente
- Le merge task si collocano tipicamente tra le wave, fungendo da punto di sincronizzazione

**Indipendenza massima** — Ogni task deve poter essere sviluppata in parallelo. Se due task condividono una dipendenza (es. una nuova entità DB), la task che crea la dipendenza va nella wave precedente e deve essere completata prima. Minimizza le dipendenze cross-stream: le fondazioni condivise vanno in `stream-fondazioni` completato e mergiato prima che gli altri stream inizino.

**Assegnazione per competenza e seniority** — Assegna le task agli sviluppatori in base alla loro area di competenza e alla repository coinvolta. Task complesse o architetturali ai senior/mid. Task ripetitive o con scope ben chiuso ai junior, sempre con review assegnata. I senior non vanno caricati di implementazione continua: il loro valore è nel design, review, e sblocco tecnico.

**Granularità giusta** — Ogni task deve essere completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala con task correlate.

**Branch convention** — Ogni task ha un branch `feature/<task-name>` creato dal branch principale della feature. Specifica l'ordine di merge basato sulle dipendenze.

**Autosufficiente per Claude Code** — Ogni task deve contenere abbastanza contesto perché un agente Claude Code possa implementarla leggendo solo la task e il gap report. Includi: file esatti da modificare/creare, pattern del progetto da seguire, criteri di completamento verificabili, e note specifiche (convenzioni, attenzioni, edge case).

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (solo se br-reviewer non e' stato eseguito)
- **`markitdown`** — per conversione PDF, PPTX, XLSX (solo se br-reviewer non e' stato eseguito)
- **`br-reviewer`** — (opzionale ma consigliato) se eseguito prima, br-analyzer ne legge il REVIEW_BR.md e salta la conversione
