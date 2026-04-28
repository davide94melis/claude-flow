# br-reviewer + Ristrutturazione Cartelle BR — Piano di Implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere la skill br-reviewer (review qualita' documentazione funzionale) e ristrutturare le cartelle plans/ in tutte le skill BR per organizzare i file per BR.

**Architecture:** Nuova skill br-reviewer che produce REVIEW_BR.md con report duale (funzionale + tecnico). Tutte le skill BR adottano la struttura `plans/<stato>/<data>_<nome>/` con retrocompatibilita' flat. La conversione documenti si sposta da br-analyzer a br-reviewer; br-analyzer la esegue solo se non trova file gia' convertiti.

**Tech Stack:** Markdown skill files, doc-to-markdown, markitdown

**Spec:** `docs/superpowers/specs/2026-04-28-br-reviewer-design.md`

---

### Task 1: Creare br-reviewer/SKILL.md

**Files:**
- Create: `~/.claude/skills/br-reviewer/SKILL.md`

- [ ] **Step 1: Creare la directory**

```bash
mkdir -p ~/.claude/skills/br-reviewer
```

- [ ] **Step 2: Scrivere SKILL.md**

Creare `~/.claude/skills/br-reviewer/SKILL.md` con il seguente contenuto completo:

````markdown
---
name: br-reviewer
description: Verifica la qualita', coerenza e completezza della documentazione funzionale di un BR prima dell'analisi tecnica. Produce un report duale — una parte per il team funzionale (problemi da chiarire) e una parte per il team tecnico (assunzioni di default). Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali. Usa questa skill quando l'utente dice "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", "nuovo br da verificare", "c'e' un br da rivedere", o qualsiasi variazione che implichi la necessita' di verificare la qualita' della documentazione funzionale prima di procedere con l'analisi tecnica.
---

# BR Reviewer — Review Qualita' Documentazione Funzionale

Questa skill si posiziona *prima* di `br-analyzer` nel flusso BR. Analizza la documentazione funzionale per qualita', coerenza e completezza, produce un report duale (per il funzionale e per il tecnico) e, se si decide di procedere, passa le assunzioni a br-analyzer tramite handoff automatico.

Il flusso BR completo:
```
br-reviewer → br-analyzer → br-executor → br-updater
                                         ↘ br-progress-report
```

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (tutti i documenti vengono convertiti in MD)
3. **Analisi della documentazione** (intra-documento, inter-documento, vs codice)
4. **Generazione output** (REVIEW_BR.md con report duale)

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finche' l'utente non ha risposto.

### Domanda 1 — Nome del BR

> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Salva il nome. Verra' usato per creare la cartella `plans/todo/<YYYY-MM-DD>_<nome>/`.

### Domanda 2 — Documentazione

> Dove trovo la documentazione del BR? Dammi i path per:
> - **BR** (il documento principale dei requisiti)
> - **Mockup** (se presenti)
> - **Qualsiasi altro file rilevante** (specifiche tecniche, template, mapping, matrici)
>
> Accetto MD, PDF, DOCX, XLSX, PPTX e immagini.

### Domanda 3 — Codebase

> Quali sono le repository/codebase coinvolte in questo BR?
> Per ognuna, dammi:
> - **Nome** (es. "back-end", "front-end", "api-gateway")
> - **Sigla** (un'abbreviazione breve, es. "BE", "FE", "GW")
> - **Path** (il path locale al codebase)
>
> Queste servono per verificare la coerenza della documentazione con il codice esistente.
> Se una repo non e' coinvolta nel BR, non includerla.

Salva i nomi, le sigle e i path. Questi stessi dati verranno riutilizzati da br-analyzer.

### Prima di procedere

Dopo aver raccolto tutti gli input, ricapitola e chiedi conferma:

> Riepilogo:
> - Nome BR: [nome] → cartella `plans/todo/<YYYY-MM-DD>_<nome>/`
> - Documentazione: [lista con path]
> - Repository coinvolte:
>   [per ognuna: Nome (SIGLA) → path]
>
> Confermo e procedo con la review?

Procedi solo dopo la conferma.

---

## Fase 2 — Conversione Documentazione in Markdown

Crea la struttura cartelle:

```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted"
```

Per ogni file di documentazione fornito, converti in MD e salva nella cartella `br-docs-converted/`:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown e' disponibile globalmente
markitdown "<path-file>" > "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/<nome-file>.md"
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
> Procedo con l'analisi della documentazione.

---

## Fase 3 — Analisi della Documentazione

### 3.1 — Analisi intra-documento

Per ogni documento singolo convertito, verifica:

- **Coerenza interna** — le stesse informazioni sono descritte in modo coerente in tutte le sezioni? Un campo e' obbligatorio in una sezione e opzionale in un'altra? Uno stato e' definito diversamente in punti diversi?
- **Completezza dei flussi** — ogni flusso descrive il caso felice E le eccezioni, gli errori, i flussi alternativi? Ci sono scenari utente che iniziano ma non finiscono, o che hanno un esito senza un ingresso?
- **Chiarezza dei requisiti** — ci sono requisiti vaghi ("il sistema deve gestire adeguatamente...", "se opportuno", "quando necessario", "le informazioni necessarie")? Ogni requisito e' interpretabile in un solo modo?
- **Regole di business** — le regole di business sono esplicitate? Gli stati, le transizioni, le condizioni, i vincoli sono definiti? O il BR descrive la UI senza definire la logica dietro?

### 3.2 — Analisi inter-documento

Confronto tra documenti diversi:

- **BR vs mockup** — ogni elemento visuale nel mockup ha un corrispettivo funzionale nel BR? Il BR descrive funzionalita' che il mockup non mostra? I campi, i bottoni, le label sono coerenti?
- **BR vs specifiche tecniche** — se ci sono specifiche tecniche, sono coerenti con i requisiti funzionali? I vincoli tecnici sono compatibili con il flusso descritto?
- **Terminologia** — lo stesso concetto e' chiamato con lo stesso nome in tutti i documenti? Se il BR dice "pratica" e il mockup dice "richiesta", e' un problema.

### 3.3 — Check leggero contro il codice

Per ogni codebase fornito, verifica superficialmente:

- **Entita' e modelli dati** — il BR presuppone strutture dati che nel codice esistono ma sono diverse? (nomi diversi, campi diversi, relazioni diverse)
- **Enum e costanti** — il BR definisce stati o valori che nel codice esistono gia' come enum con valori/nomi diversi?
- **API/endpoint** — il BR descrive operazioni che nel codice corrispondono ad API con naming o struttura diversa?
- **Flussi e stati** — il BR descrive transizioni di stato che nel codice funzionano diversamente?

Lo scopo NON e' fare la gap analysis (quello lo fa `br-analyzer`) ma trovare problemi di *documentazione* visibili solo confrontando col codice: il BR presuppone strutture che nel codice esistono ma sono diverse. Questi disallineamenti vanno segnalati al team funzionale perche' possono essere errori nel BR o evoluzioni non documentate.

Usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase quando possibile.

---

## Fase 4 — Generazione Output

### Categorie di problemi

Ogni problema trovato viene classificato per tipo con flag bloccante si/no:

| Categoria | Descrizione |
|---|---|
| **Incoerenza** | Contraddizioni tra parti della documentazione (intra o inter-documento) |
| **Gap funzionale** | Pezzi mancanti nella descrizione del comportamento (flussi, eccezioni, regole) |
| **Ambiguita'** | Punti interpretabili in piu' modi (requisiti vaghi, condizioni non definite) |
| **Riferimento mancante** | Dipendenze esterne non specificate (integrazioni, processi, fonti dati) |
| **Disallineamento col codice** | Il BR presuppone strutture/terminologie diverse da quelle nel codice |

Per ogni problema documenta:
- **Categoria**: una delle 5 sopra
- **Bloccante**: si/no — un problema e' bloccante quando senza risposta non e' possibile fare una pianificazione affidabile (es. un flusso fondamentale descritto in modo contraddittorio, una regola di business centrale non definita)
- **Dove**: riferimento preciso al documento e sezione/pagina
- **Problema**: descrizione chiara del problema
- **Impatto**: cosa succede se non viene risolto
- **Domanda per il funzionale**: domanda precisa a cui serve risposta
- **Assunzione proposta** (solo per i non-bloccanti): cosa il team tecnico assumera' se non arriva chiarimento, con indicazione del rischio e del costo di correzione se l'assunzione si rivela errata

### Generazione del REVIEW_BR.md

Genera il file `plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md` con questa struttura:

```
# Review Documentazione BR [nome/versione]

Data review: `<data>`

Documentazione analizzata:
- [lista file con path]

Codebase verificati:
- [per ogni repo: SIGLA (nome) → path]

## Esito sintetico

[2-3 frasi: qualita' complessiva della documentazione, numero di problemi
per categoria, presenza o meno di bloccanti]

Problemi trovati: N totali (X bloccanti, Y non bloccanti)

---

## Parte 1 — Per il team funzionale

Questa sezione elenca i punti che richiedono chiarimento o correzione
nella documentazione.

### Problemi bloccanti

[Se presenti. Questi impediscono una pianificazione affidabile.]

#### 1. [Titolo problema]

- **Categoria**: [Incoerenza / Gap funzionale / Ambiguita' / Riferimento mancante / Disallineamento col codice]
- **Bloccante**: Si
- **Dove**: [documento, sezione/pagina]
- **Problema**: [descrizione chiara, comprensibile dal funzionale]
- **Impatto**: [perche' senza risposta non si puo' procedere]
- **Domanda per il funzionale**: [domanda precisa a cui serve risposta]

#### 2. [...]

### Problemi non bloccanti

#### 1. [Titolo problema]

- **Categoria**: [...]
- **Bloccante**: No
- **Dove**: [...]
- **Problema**: [...]
- **Domanda per il funzionale**: [domanda precisa]
- **Nota**: se non arriva chiarimento, il team tecnico procedera'
  con l'assunzione indicata nella Parte 2.

#### 2. [...]

---

## Parte 2 — Per il team tecnico

Questa sezione contiene le assunzioni che il team tecnico adottera'
in assenza di chiarimenti dal funzionale. Ogni assunzione e' legata
a un problema della Parte 1.

### Assunzioni proposte

| # | Problema rif. | Assunzione proposta | Rischio se errata | Costo di correzione |
|---|---|---|---|---|
| A-001 | Problema 3 | [descrizione assunzione] | [cosa succede se sbagliata] | Basso / Medio / Alto |
| A-002 | Problema 5 | [...] | [...] | [...] |

### Disallineamenti col codice

[Sezione specifica per i problemi di categoria "Disallineamento col codice".
Questa info e' solo per il team tecnico — il funzionale non ha contesto
per capirla.]

| # | Concetto BR | Nel codice | File/Classe | Nota |
|---|---|---|---|---|
| D-001 | "stato pratica: Aperta, Chiusa" | enum PracticeStatus: OPEN, CLOSED, SUSPENDED | src/.../PracticeStatus.java | Il BR non menziona SUSPENDED |

---

## Riepilogo per br-analyzer

[Sezione tecnica consumata automaticamente da br-analyzer.
Contiene le assunzioni in formato strutturato che l'analyzer
puo' incorporare direttamente nel gap report e nel piano.]

Assunzioni confermate: [lista A-XXX delle assunzioni validate dall'utente]
Bloccanti aperti: [lista dei bloccanti non ancora risolti, se si procede comunque]
```

### Presentazione all'utente

Dopo aver generato il report, presentalo all'utente per revisione. L'utente puo' chiedere modifiche al report. Quando l'utente conferma:

**Se non ci sono bloccanti:**

> Review completata. Nessun bloccante trovato.
>
> Il report e' salvato in `plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md`.
> Puoi inviare la **Parte 1** al team funzionale per i chiarimenti.
>
> Quando vuoi, puoi procedere con `br-analyzer` per l'analisi tecnica — le assunzioni verranno incorporate automaticamente.

**Se ci sono bloccanti:**

> Review completata. Ci sono **N problemi bloccanti** ancora aperti.
>
> Il report e' salvato in `plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md`.
> Puoi inviare la **Parte 1** al team funzionale per i chiarimenti.
>
> **Ti consiglio di attendere chiarimenti dal funzionale prima di procedere con l'analisi tecnica** — il rischio e' di pianificare lavoro su basi fragili che dovra' essere rifatto.
>
> Pero' la decisione e' tua: se vuoi procedere comunque con `br-analyzer`, le assunzioni proposte verranno incorporate nel piano e i bloccanti aperti saranno segnalati.

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC
- **`markitdown`** — per conversione PDF, PPTX, XLSX (installato come dipendenza di doc-to-markdown, oppure via `pip install 'markitdown[all]'` o `uvx`)
````

- [ ] **Step 3: Verificare il file**

```bash
wc -l ~/.claude/skills/br-reviewer/SKILL.md
```

Verificare che il file esista e abbia contenuto.

- [ ] **Step 4: Commit**

```bash
git add ~/.claude/skills/br-reviewer/SKILL.md
git commit -m "feat: add br-reviewer skill for BR documentation quality review"
```

---

### Task 2: Aggiornare br-analyzer per struttura cartelle e handoff

**Files:**
- Modify: `~/.claude/skills/br-analyzer/SKILL.md`

- [ ] **Step 1: Aggiornare l'introduzione e la lista fasi**

Trovare:
```
Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (tutti i documenti vengono convertiti in MD per ridurre il contesto)
3. **Analisi gap** (confronto documentazione vs codice)
4. **Generazione output** (2 file MD: gap report + piano di implementazione)
```

Sostituire con:
```
Il flusso BR completo:
```
br-reviewer → br-analyzer → br-executor → br-updater
                                         ↘ br-progress-report
```

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (solo se `br-reviewer` non e' stato eseguito prima — se trova `br-docs-converted/` nella cartella del BR, salta questa fase)
3. **Analisi gap** (confronto documentazione vs codice)
4. **Generazione output** (2 file MD: gap report + piano di implementazione, nella cartella del BR)
```

- [ ] **Step 2: Aggiornare Fase 1 — aggiungere ricerca cartella BR e domanda nome**

Trovare:
```
## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finché l'utente non ha risposto.

### Domanda 1 — Codebase
```

Sostituire con:
```
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
- Usa i file in `br-docs-converted/` per l'analisi (salta la Fase 2)
- Salta le domande su documentazione e codebase — leggile dal REVIEW_BR.md
- Procedi direttamente alla Domanda 3 (Team di sviluppo)

**Se non trovi nulla**, chiedi il nome del BR:

> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Poi procedi con le domande successive.

### Domanda 1 — Codebase
```

- [ ] **Step 3: Aggiornare Fase 2 — rendere condizionale**

Trovare:
```
## Fase 2 — Conversione Documentazione in Markdown

Prima di iniziare l'analisi, converti tutti i documenti non-MD in formato Markdown. Questo riduce significativamente il contesto necessario e rende i documenti più leggibili per l'analisi.

### Procedura di conversione

Crea una cartella `br-docs-converted/` nella working directory corrente. Per ogni file di documentazione fornito:
```

Sostituire con:
```
## Fase 2 — Conversione Documentazione in Markdown

**Se `br-reviewer` e' stato eseguito** e la cartella `br-docs-converted/` esiste gia' nella cartella del BR (`plans/todo/<data>_<nome>/br-docs-converted/`), **salta completamente questa fase** e vai alla Fase 3. La conversione e' gia' stata fatta da br-reviewer.

**Se `br-reviewer` non e' stato eseguito**, converti tutti i documenti non-MD in formato Markdown. Questo riduce significativamente il contesto necessario e rende i documenti piu' leggibili per l'analisi.

### Procedura di conversione

Crea la cartella del BR e la sottocartella per i documenti convertiti:

```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted"
```

Per ogni file di documentazione fornito:
```

- [ ] **Step 4: Aggiornare i path di conversione nella Fase 2**

Trovare tutti i riferimenti a `br-docs-converted/` nella Fase 2 e sostituire con il path completo `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`. I comandi di conversione diventano:

Trovare:
```
markitdown "<path-file>" > "br-docs-converted/<nome-file>.md"
```

Sostituire con:
```
markitdown "<path-file>" > "plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/<nome-file>.md"
```

(ripetere per tutte le occorrenze, incluso il blocco uvx)

Trovare:
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `br-docs-converted/`.
```

Sostituire con:
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`.
```

Trovare:
```
**File `.md`** — Copia direttamente in `br-docs-converted/`.
```

Sostituire con:
```
**File `.md`** — Copia direttamente in `plans/todo/<YYYY-MM-DD>_<nome>/br-docs-converted/`.
```

- [ ] **Step 5: Aggiornare Fase 3 — riferimenti a br-docs-converted**

Trovare:
```
Leggi integralmente ogni documento MD convertito nella cartella `br-docs-converted/`.
```

Sostituire con:
```
Leggi integralmente ogni documento MD convertito nella cartella `br-docs-converted/` (dentro la cartella del BR).
```

- [ ] **Step 6: Aggiornare Fase 4 — struttura cartelle output**

Trovare:
```
## Fase 4 — Generazione Output

Crea la struttura di cartelle `plans/` nella working directory corrente (se non esiste già):

```bash
mkdir -p plans/todo plans/in-progress plans/done
```

Genera entrambi i file nella cartella `plans/todo/`. Questo è lo stato iniziale: i file restano in `todo/` finché uno sviluppatore non avvia la lavorazione con `br-executor`, che li sposta in `in-progress/`, e infine in `done/` al completamento di tutte le task.

### 4.1 — Gap Report

**Path file**: `plans/todo/GAP_REPORT_BR_<YYYY-MM-DD>.md`
```

Sostituire con:
```
## Fase 4 — Generazione Output

Se la cartella del BR non esiste ancora (br-reviewer non eseguito), creala:

```bash
mkdir -p "plans/todo/<YYYY-MM-DD>_<nome>" plans/in-progress plans/done
```

Genera entrambi i file nella cartella del BR in `plans/todo/`. Questo e' lo stato iniziale: la cartella intera si sposta in `in-progress/` quando uno sviluppatore avvia la lavorazione con `br-executor`, e in `done/` al completamento di tutte le task.

### 4.1 — Gap Report

**Path file**: `plans/todo/<YYYY-MM-DD>_<nome>/GAP_REPORT_BR.md`
```

- [ ] **Step 7: Aggiornare il template del Gap Report — aggiungere sezione assunzioni**

Nella struttura del Gap Report (dentro il blocco ``` del template), trovare:

```
## Esito sintetico

[2-3 frasi che riassumono lo stato complessivo: cosa è coperto, dove sono i gap principali]
```

Sostituire con:
```
## Assunzioni da review

[Se br-reviewer e' stato eseguito, riporta qui le assunzioni confermate dal REVIEW_BR.md.
Se non e' stato eseguito, scrivi "Nessuna review preventiva eseguita."]

## Esito sintetico

[2-3 frasi che riassumono lo stato complessivo: cosa e' coperto, dove sono i gap principali]
```

- [ ] **Step 8: Aggiornare il path del Piano di Implementazione**

Trovare:
```
**Path file**: `plans/todo/PIANO_IMPLEMENTAZIONE_BR_<YYYY-MM-DD>.md`
```

Sostituire con:
```
**Path file**: `plans/todo/<YYYY-MM-DD>_<nome>/PIANO_IMPLEMENTAZIONE_BR.md`
```

- [ ] **Step 9: Aggiornare la sezione Assunzioni nel template del Piano**

Nel template del Piano di Implementazione, trovare:
```
Assunzioni:
- [contesto, cosa è già completato, perimetro residuo]
```

Sostituire con:
```
Assunzioni:
- [contesto, cosa e' gia' completato, perimetro residuo]
- [se br-reviewer e' stato eseguito, includi qui tutte le assunzioni confermate dalla review, con riferimento al REVIEW_BR.md]
```

- [ ] **Step 10: Aggiornare la sezione Dipendenze**

Trovare:
```
## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC
- **`markitdown`** — per conversione PDF, PPTX, XLSX (installato come dipendenza di doc-to-markdown, oppure via `pip install 'markitdown[all]'` o `uvx`)
```

Sostituire con:
```
## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC (solo se br-reviewer non e' stato eseguito)
- **`markitdown`** — per conversione PDF, PPTX, XLSX (solo se br-reviewer non e' stato eseguito)
- **`br-reviewer`** — (opzionale ma consigliato) se eseguito prima, br-analyzer ne legge il REVIEW_BR.md e salta la conversione
```

- [ ] **Step 11: Commit**

```bash
git add ~/.claude/skills/br-analyzer/SKILL.md
git commit -m "feat: update br-analyzer for folder structure and br-reviewer handoff"
```

---

### Task 3: Aggiornare br-executor per struttura cartelle

**Files:**
- Modify: `~/.claude/skills/br-executor/SKILL.md`

- [ ] **Step 1: Aggiornare Domanda 1 — ricerca file nella struttura a cartelle**

Trovare:
```
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
```

Sostituire con:
```
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
```

- [ ] **Step 2: Aggiornare lo spostamento in in-progress — cartella intera**

Trovare:
```
### Spostamento in `plans/in-progress/`

Quando lo sviluppatore conferma e la lavorazione sta per iniziare, sposta report e piano da `plans/todo/` a `plans/in-progress/` (se non sono già lì):

```bash
mkdir -p plans/in-progress
mv plans/todo/GAP_REPORT_BR_*.md plans/in-progress/ 2>/dev/null
mv plans/todo/PIANO_IMPLEMENTAZIONE_BR_*.md plans/in-progress/ 2>/dev/null
```

Il file di progresso viene creato (o cercato) direttamente in `plans/in-progress/`.
```

Sostituire con:
```
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
```

- [ ] **Step 3: Aggiornare il path di creazione del file di progresso**

Trovare:
```
Crea il file `PROGRESSO_BR_<YYYY-MM-DD>.md` nella stessa directory del piano di implementazione, con questa struttura:
```

Sostituire con:
```
Crea il file `PROGRESSO_BR.md` nella stessa cartella del BR (es. `plans/in-progress/<YYYY-MM-DD>_<nome>/PROGRESSO_BR.md`), con questa struttura:
```

- [ ] **Step 4: Aggiornare lo spostamento in done — cartella intera**

Trovare:
```
### Completamento di tutte le task — Spostamento in `plans/done/`

Dopo aver completato una task, verifica nel file di progresso se **tutte** le task (non solo quelle dello sviluppatore corrente, ma tutte quelle nel piano) sono in stato "Completata". Se sì:

```bash
mkdir -p plans/done
mv plans/in-progress/GAP_REPORT_BR_*.md plans/done/
mv plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_*.md plans/done/
mv plans/in-progress/PROGRESSO_BR_*.md plans/done/
```

Comunica:

> Tutte le task del piano sono completate. Report, piano e progresso spostati in `plans/done/`.
```

Sostituire con:
```
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
```

- [ ] **Step 5: Commit**

```bash
git add ~/.claude/skills/br-executor/SKILL.md
git commit -m "feat: update br-executor for BR folder structure"
```

---

### Task 4: Aggiornare br-updater per struttura cartelle

**Files:**
- Modify: `~/.claude/skills/br-updater/SKILL.md`

- [ ] **Step 1: Aggiornare Domanda 1 — ricerca file nella struttura a cartelle**

Trovare:
```
### Domanda 1 — File esistenti

Cerca automaticamente nella struttura `plans/`:

```bash
ls plans/in-progress/ plans/todo/ 2>/dev/null
```

Se trovi file, proponili:

> Ho trovato questi file:
> - `plans/in-progress/GAP_REPORT_BR_2026-04-24.md`
> - `plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
> - `plans/in-progress/PROGRESSO_BR_2026-04-24.md`
>
> Uso questi come base? Oppure dammi i path manualmente.

Se non trovi nulla, chiedi:

> Dammi i path dei file da aggiornare:
> 1. **Gap Report** esistente
> 2. **Piano di Implementazione** esistente
> 3. **File di Progresso** (se esiste)
```

Sostituire con:
```
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
```

- [ ] **Step 2: Aggiornare il path di conversione dei nuovi documenti**

Trovare:
```
Salva in `br-docs-converted/` sovrascrivendo i file precedenti dove applicabile.
```

Sostituire con:
```
Salva nella cartella `br-docs-converted/` dentro la cartella del BR (es. `plans/in-progress/<YYYY-MM-DD>_<nome>/br-docs-converted/`), sovrascrivendo i file precedenti dove applicabile. Se stai lavorando con file flat, salva in `br-docs-converted/` nella working directory corrente.
```

- [ ] **Step 3: Commit**

```bash
git add ~/.claude/skills/br-updater/SKILL.md
git commit -m "feat: update br-updater for BR folder structure"
```

---

### Task 5: Aggiornare br-progress-report per struttura cartelle

**Files:**
- Modify: `~/.claude/skills/br-progress-report/SKILL.md`

- [ ] **Step 1: Aggiornare la ricerca automatica dei file sorgente**

Trovare:
```
### Ricerca automatica

Cerca i file sorgente nella struttura `plans/`, in ordine di priorità:

```bash
ls plans/in-progress/ plans/todo/ plans/done/ 2>/dev/null
```

Serve trovare:
- **Piano di Implementazione** (`PIANO_IMPLEMENTAZIONE_BR_*.md`) — obbligatorio
- **File di Progresso** (`PROGRESSO_BR_*.md`) — opzionale, se non esiste le task partono tutte da 0%
- **Gap Report** (`GAP_REPORT_BR_*.md`) — opzionale, usato per arricchire le descrizioni

Se trovi file, proponili:

> Ho trovato:
> - `plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
> - `plans/in-progress/PROGRESSO_BR_2026-04-24.md`
>
> Uso questi per generare l'Excel?

Se non trovi nulla, chiedi i path manualmente.
```

Sostituire con:
```
### Ricerca automatica

Cerca cartelle BR nella struttura `plans/`, in ordine di priorita':

```bash
ls -d plans/in-progress/*/ plans/todo/*/ plans/done/*/ 2>/dev/null
```

Serve trovare:
- **Piano di Implementazione** (`PIANO_IMPLEMENTAZIONE_BR.md`) — obbligatorio
- **File di Progresso** (`PROGRESSO_BR.md`) — opzionale, se non esiste le task partono tutte da 0%
- **Gap Report** (`GAP_REPORT_BR.md`) — opzionale, usato per arricchire le descrizioni

**Se trovi cartelle BR**, proponile:

> Ho trovato:
> - `plans/in-progress/2026-04-28_booking-v2/`
>   - `PIANO_IMPLEMENTAZIONE_BR.md`
>   - `PROGRESSO_BR.md`
>
> Uso questa cartella per generare l'Excel?

**Se trovi file flat** (retrocompatibilita'):

> Ho trovato:
> - `plans/in-progress/PIANO_IMPLEMENTAZIONE_BR_2026-04-24.md`
> - `plans/in-progress/PROGRESSO_BR_2026-04-24.md`
>
> Uso questi per generare l'Excel?

Se non trovi nulla, chiedi i path manualmente.
```

- [ ] **Step 2: Aggiornare la ricerca dell'Excel esistente**

Trovare:
```
### Verifica Excel esistente

Cerca nella stessa cartella del piano se esiste già un file Excel:

```bash
ls plans/in-progress/AVANZAMENTO_BR_*.xlsx plans/todo/AVANZAMENTO_BR_*.xlsx plans/done/AVANZAMENTO_BR_*.xlsx 2>/dev/null
```
```

Sostituire con:
```
### Verifica Excel esistente

Cerca nella stessa cartella del BR se esiste gia' un file Excel:

```bash
# Se struttura a cartelle
ls plans/in-progress/*/AVANZAMENTO_BR.xlsx plans/todo/*/AVANZAMENTO_BR.xlsx plans/done/*/AVANZAMENTO_BR.xlsx 2>/dev/null

# Retrocompatibilita' flat
ls plans/in-progress/AVANZAMENTO_BR_*.xlsx plans/todo/AVANZAMENTO_BR_*.xlsx plans/done/AVANZAMENTO_BR_*.xlsx 2>/dev/null
```
```

- [ ] **Step 3: Aggiornare il nome e la posizione del file Excel**

Nella sezione "Nome e posizione file", trovare:
```
Salva nella stessa cartella del piano:
- **Creazione**: `AVANZAMENTO_BR_<YYYY-MM-DD>.xlsx`
- **Aggiornamento**: sovrascrivi il file esistente
```

Sostituire con:
```
Salva nella stessa cartella del BR:
- **Se struttura a cartelle**: `plans/<stato>/<YYYY-MM-DD>_<nome>/AVANZAMENTO_BR.xlsx`
- **Se flat (retrocompatibilita')**: `plans/<stato>/AVANZAMENTO_BR_<YYYY-MM-DD>.xlsx`
- **Aggiornamento**: sovrascrivi il file esistente
```

- [ ] **Step 4: Commit**

```bash
git add ~/.claude/skills/br-progress-report/SKILL.md
git commit -m "feat: update br-progress-report for BR folder structure"
```

---

### Task 6: Aggiornare CLAUDE.md — registrare br-reviewer

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Aggiungere il blocco br-reviewer prima di br-analyzer**

Trovare:
```
# br-analyzer
- **br-analyzer** (`~/.claude/skills/br-analyzer/SKILL.md`) - analisi gap tra BR e codice + piano di implementazione. Trigger: "abbiamo un nuovo br"
When the user says "abbiamo un nuovo br" (or similar phrases about a new business requirement), invoke the Skill tool with `skill: "br-analyzer"` before doing anything else.
```

Sostituire con:
```
# br-reviewer
- **br-reviewer** (`~/.claude/skills/br-reviewer/SKILL.md`) - review qualita' della documentazione funzionale prima dell'analisi tecnica. Trigger: "rivedi il br", "review del br", "controlla la documentazione"
When the user says "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", "nuovo br da verificare", or similar phrases about reviewing BR documentation quality, invoke the Skill tool with `skill: "br-reviewer"` before doing anything else.

# br-analyzer
- **br-analyzer** (`~/.claude/skills/br-analyzer/SKILL.md`) - analisi gap tra BR e codice + piano di implementazione. Trigger: "abbiamo un nuovo br"
When the user says "abbiamo un nuovo br" (or similar phrases about a new business requirement), invoke the Skill tool with `skill: "br-analyzer"` before doing anything else.
```

- [ ] **Step 2: Commit**

```bash
git add ~/.claude/CLAUDE.md
git commit -m "feat: register br-reviewer skill in CLAUDE.md"
```

---

### Task 7: Commit finale del design doc e del piano

**Files:**
- Add: `docs/superpowers/specs/2026-04-28-br-reviewer-design.md`
- Add: `docs/superpowers/plans/2026-04-28-br-reviewer.md`

- [ ] **Step 1: Commit**

```bash
git add docs/superpowers/specs/2026-04-28-br-reviewer-design.md
git add docs/superpowers/plans/2026-04-28-br-reviewer.md
git commit -m "docs: add br-reviewer design spec and implementation plan"
```
