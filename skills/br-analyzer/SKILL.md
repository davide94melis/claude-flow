---
name: br-analyzer
description: Analizza un nuovo Business Requirement (BR) confrontandolo con i codebase esistenti (BE, FE, Document Manager, Email Manager), genera un gap report dettagliato per funzionalità e un piano di implementazione con task indipendenti assegnate a sviluppatori muniti di Claude Code. Usa questa skill quando l'utente dice "abbiamo un nuovo br", "nuovo br", "c'è un br nuovo", "analizza il br", "gap analysis br", "nuovo business requirement", o qualsiasi variazione che implichi l'arrivo di un nuovo documento di requisiti da analizzare e pianificare. Attivala anche quando l'utente menziona la necessità di confrontare documentazione di requisiti con il codice per trovare cosa manca e pianificare lo sviluppo.
---

# BR Analyzer — Gap Report & Piano di Implementazione

Questa skill guida l'analisi di un nuovo Business Requirement: dal confronto con i codebase al piano di sviluppo con task indipendenti per un team di sviluppatori, ognuno munito di Claude Code.

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (tutti i documenti vengono convertiti in MD per ridurre il contesto)
3. **Analisi gap** (confronto documentazione vs codice)
4. **Generazione output** (2 file MD: gap report + piano di implementazione)

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finché l'utente non ha risposto.

### Domanda 1 — Codebase

> Quali sono i path dei codebase coinvolti in questo BR? Servono i path per:
> - **Backend (BE)**
> - **Frontend (FE)**
> - **Document Manager (DM)**
> - **Email Manager (EM)**
>
> Se qualcuno non è coinvolto, dimmelo e lo escludo dall'analisi.

Salva i path forniti. Se l'utente dice che un codebase non è coinvolto, escludilo dalle fasi successive.

### Domanda 2 — Documentazione

> Dove trovo la documentazione del BR? Dammi i path per:
> - **BR** (il documento principale dei requisiti)
> - **Mockup** (se presenti)
> - **Qualsiasi altro file rilevante** (specifiche tecniche, template, mapping, matrici)
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Team di sviluppo

> Chi lavorerà all'implementazione? Per ogni sviluppatore dimmi:
> - **Nome** (o identificativo, es. "Marco", "BE-Senior")
> - **Ruolo**: BE / FE / Fullstack
> - **Seniority**: Junior / Mid / Senior
>
> Esempio: "Marco - BE senior, Luca - FE mid, Anna - BE junior"

### Prima di procedere

Dopo aver raccolto tutti gli input, ricapitola quello che hai ricevuto e chiedi conferma:

> Riepilogo:
> - Codebase: [lista con path]
> - Documentazione: [lista con path]
> - Team: [lista con ruolo e seniority]
>
> Confermo e procedo con l'analisi?

Procedi solo dopo la conferma.

---

## Fase 2 — Conversione Documentazione in Markdown

Prima di iniziare l'analisi, converti tutti i documenti non-MD in formato Markdown. Questo riduce significativamente il contesto necessario e rende i documenti più leggibili per l'analisi.

### Procedura di conversione

Crea una cartella `br-docs-converted/` nella working directory corrente. Per ogni file di documentazione fornito:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `br-docs-converted/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown è disponibile globalmente
markitdown "<path-file>" > "br-docs-converted/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "br-docs-converted/<nome-file>.md"
```

**File `.md`** — Copia direttamente in `br-docs-converted/`.

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

Leggi integralmente ogni documento MD convertito nella cartella `br-docs-converted/`. Per le immagini (mockup), usa Read sul file originale e descrivi nel dettaglio cosa vedi, mappando le UI ai componenti da implementare.

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
- **Frontend** (se FE): componenti, routing, modelli, i18n, servizi
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
- **Moduli coinvolti** (BE, FE, DM, EM)
- **Complessità stimata** (Bassa / Media / Alta)

Il livello di dettaglio deve essere sufficiente perché un agente Claude Code, leggendo solo il gap report, possa capire esattamente cosa va fatto senza dover rileggere il BR originale.

---

## Fase 4 — Generazione Output

Crea la struttura di cartelle `plans/` nella working directory corrente (se non esiste già):

```bash
mkdir -p plans/todo plans/in-progress plans/done
```

Genera entrambi i file nella cartella `plans/todo/`. Questo è lo stato iniziale: i file restano in `todo/` finché uno sviluppatore non avvia la lavorazione con `br-executor`, che li sposta in `in-progress/`, e infine in `done/` al completamento di tutte le task.

### 4.1 — Gap Report

**Path file**: `plans/todo/GAP_REPORT_BR_<YYYY-MM-DD>.md`

Struttura:

```
# Report Verifica BR [nome/versione]

Data verifica: `<data>`

Branch verificato:
- FE: `<branch>`
- BE: `<branch>`
[altri codebase se presenti]

Perimetro documentale verificato:
- BR: `<path>`
- Mockup: `<path>`
[altri documenti]

Codebase verificati:
- FE: `<path>`
- BE: `<path>`
[altri codebase]

## Esito sintetico

[2-3 frasi che riassumono lo stato complessivo: cosa è coperto, dove sono i gap principali]

## Matrice di verifica

| Requisito | FE | BE | Stato | Evidenze | Gap |
|---|---|---|---|---|---|
| [Requisito dal BR] | [Implementato/Non implementato/N/A] | [Implementato/Non implementato/N/A] | [Coperto/Parziale/Mancante/Discrepanza/Da chiarire] | [Path esatti a file e classi rilevanti, sia FE che BE] | [Descrizione precisa del gap, o "Nessuno"] |

[Una riga per ogni requisito identificato, raggruppate per funzionalità]

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

**Path file**: `plans/todo/PIANO_IMPLEMENTAZIONE_BR_<YYYY-MM-DD>.md`

Struttura:

```
# Piano Implementazione [Nome feature/BR]

Data: `<data>`

Assunzioni:
- [contesto, cosa è già completato, perimetro residuo]
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

## Backlog operativo

| ID | Owner | Area | Priorità | Attività | Descrizione | Dipendenze | Effort |
|---|---|---|---:|---|---|---|---:|
| `T-001` | `[Dev]` | BE/FE | P0/P1/P2 | [Nome task] | [Descrizione dettagliata, con riferimento ai gap del report, file da toccare, pattern da seguire] | [ID dipendenze o "Nessuna"] | `N gg` |

[Una riga per ogni task]

## Ordine di esecuzione

### Wave 0 — Fondazioni
- [task fondazionali che sbloccano tutto il resto]

### Wave 1
- Backend: [lista task]
- Frontend: [lista task]

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
- Backend: circa `N gg/uomo`
- Frontend: circa `N gg/uomo`
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

**Indipendenza massima** — Ogni task deve poter essere sviluppata in parallelo. Se due task condividono una dipendenza (es. una nuova entità DB), la task che crea la dipendenza va nella wave precedente e deve essere completata prima.

**Assegnazione per competenza e seniority** — Task BE a sviluppatori BE, FE a FE. Task complesse o architetturali ai senior/mid. Task ripetitive o con scope ben chiuso ai junior, sempre con review assegnata. I senior non vanno caricati di implementazione continua: il loro valore è nel design, review, e sblocco tecnico.

**Granularità giusta** — Ogni task deve essere completabile in 1-5 giorni. Troppo grande: spezzala. Troppo piccola (< 2 ore): accorpala con task correlate.

**Branch convention** — Ogni task ha un branch `feature/<task-name>` creato dal branch principale della feature. Specifica l'ordine di merge basato sulle dipendenze.

**Autosufficiente per Claude Code** — Ogni task deve contenere abbastanza contesto perché un agente Claude Code possa implementarla leggendo solo la task e il gap report. Includi: file esatti da modificare/creare, pattern del progetto da seguire, criteri di completamento verificabili, e note specifiche (convenzioni, attenzioni, edge case).

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC
- **`markitdown`** — per conversione PDF, PPTX, XLSX (installato come dipendenza di doc-to-markdown, oppure via `pip install 'markitdown[all]'` o `uvx`)
