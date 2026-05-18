---
name: br-reviewer
description: Verifica la qualita', coerenza e completezza della documentazione funzionale di un BR prima dell'analisi tecnica. Produce un report duale — una parte per il team funzionale (problemi da chiarire) e una parte per il team tecnico (assunzioni di default). Esegue anche un check leggero contro il codice per trovare disallineamenti terminologici e strutturali. Usa questa skill quando l'utente dice "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", "nuovo br da verificare", "c'e' un br da rivedere", o qualsiasi variazione che implichi la necessita' di verificare la qualita' della documentazione funzionale prima di procedere con l'analisi tecnica.
---

# BR Reviewer — Review Qualita' Documentazione Funzionale

Questa skill si posiziona *prima* di `br-analyzer` nel flusso BR. Analizza la documentazione funzionale per qualita', coerenza e completezza, produce un report duale (per il funzionale e per il tecnico) e, se si decide di procedere, passa le assunzioni a br-analyzer tramite handoff automatico.

Il flusso BR completo:
```
br-reviewer → br-clarify → br-analyzer → br-executor → br-updater
                                                      ↘ br-progress-report
```

Il processo si compone di 4 fasi:
1. **Raccolta input** (domande conversazionali, una alla volta)
2. **Conversione documentazione** (tutti i documenti vengono convertiti in MD)
3. **Analisi della documentazione** (intra-documento, inter-documento, vs codice)
4. **Generazione output** (REVIEW_BR.md con report duale)

---

## Risoluzione Path — deloitte-profiles

Tutte le operazioni su file BR (piani, report, progressi) avvengono nella repo `deloitte-profiles`, non nella repo del codice.

### Lettura `.br-local.json`

All'avvio, leggi `.br-local.json` dalla root della repo corrente:

```bash
cat .br-local.json 2>/dev/null
```

Estrai i campi:
- `profiles_repo` — path assoluto al clone locale di `deloitte-profiles`
- `profilo` — nome della cartella progetto in `deloitte-profiles`
- `developer` — nome dello sviluppatore (opzionale per skill TL/PM)

Il **base path** per tutti gli artefatti BR e': `<profiles_repo>/<profilo>/plans/`

### Se `.br-local.json` non esiste

Ferma l'esecuzione e avvisa:

> `.br-local.json` non trovato. Devi prima eseguire `br-profile-setup` per creare il profilo del progetto e configurare il collegamento.

### Sincronizzazione prima della lettura

Prima di leggere qualsiasi file dalla repo profili:

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

### Commit e push dopo la scrittura

Dopo ogni scrittura di artefatti nella repo profili:

```bash
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "<messaggio>"
git -C "<profiles_repo>" push origin main --quiet
```

Se il push fallisce, avvisa l'utente e proponi: (1) riprovare, (2) creare un branch, (3) lasciare il commit locale.

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva. Non anticipare domande e non procedere finche' l'utente non ha risposto.

### Domanda 1 — Nome del BR

> Come vuoi chiamare questo BR? Il nome verra' usato per creare la cartella di lavoro.
>
> Esempio: "booking-v2", "monitoraggio-dashboard", "auth-refactor"

Salva il nome. Verra' usato per creare la cartella `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`.

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
> - Nome BR: [nome] → cartella `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`
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
git -C "<profiles_repo>" pull origin main --quiet
mkdir -p "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements"
```

Per ogni file di documentazione fornito, converti in MD e salva nella cartella `requirements/`:

**File `.docx` / `.doc`** — Usa la skill `doc-to-markdown` installata in `~/.claude/skills/doc-to-markdown/`:
```bash
python3 ~/.claude/skills/doc-to-markdown/convert_word_to_markdown.py "<path-file>"
```
Sposta il file `.md` risultante e l'eventuale cartella `_images/` in `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements/`.

**File `.pdf` / `.pptx` / `.xlsx`** — Usa `markitdown` (la stessa dipendenza di doc-to-markdown):
```bash
# Se markitdown e' disponibile globalmente
markitdown "<path-file>" > "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"

# Altrimenti via uvx
uvx markitdown "<path-file>" > "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/requirements/<nome-file>.md"
```

**File `.md`** — Copia direttamente in `requirements/`.

**Immagini (mockup `.png`, `.jpg`, ecc.)** — Non convertire. Leggile con Read (supporto multimodale) durante la fase di analisi e descrivi nel dettaglio cosa vedi.

### Verifica conversione

Dopo la conversione, verifica che ogni file MD generato contenga contenuto valido. Se un file risulta vuoto o corrotto, segnalalo all'utente e usa il Read diretto sul file originale come fallback.

Comunica all'utente lo stato della conversione:

> Conversione completata:
> - `BR_v24.docx` → `requirements/BR_v24.md` (OK)
> - `Mockup_Booking.pptx` → `requirements/Mockup_Booking.md` (OK)
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

Genera il file `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md` con questa struttura:

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
- **Risposta:** *(inserire qui la risposta)*

#### 2. [...]

### Problemi non bloccanti

#### 1. [Titolo problema]

- **Categoria**: [...]
- **Bloccante**: No
- **Dove**: [...]
- **Problema**: [...]
- **Domanda per il funzionale**: [domanda precisa]
- **Risposta:** *(inserire qui la risposta)*
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

### Generazione REVIEW_BR.docx

Dopo aver generato REVIEW_BR.md, converti in DOCX per facilitare la compilazione da parte del team funzionale:

```bash
pandoc -f markdown -t docx "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md" -o "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.docx"
```

Entrambi i file (MD e DOCX) vengono salvati nella cartella del BR. Il DOCX contiene i placeholder "*(inserire qui la risposta)*" sotto ogni domanda, pronti per la compilazione.

### Commit e push degli artefatti

Dopo la generazione di REVIEW_BR.md e REVIEW_BR.docx, fai commit e push nella repo profili:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/"
git -C "<profiles_repo>" commit -m "[br-reviewer] <nome>: review documentazione completata"
git -C "<profiles_repo>" push origin main --quiet
```

Se il push fallisce, avvisa l'utente e proponi: (1) riprovare, (2) creare un branch, (3) lasciare il commit locale.

### Presentazione all'utente

Dopo aver generato report e DOCX, presentali all'utente per revisione. L'utente puo' chiedere modifiche al report. Quando l'utente conferma:

**Se non ci sono bloccanti:**

> Review completata. Nessun bloccante trovato.
>
> I report sono salvati in `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`:
> - `REVIEW_BR.md` — versione markdown
> - `REVIEW_BR.docx` — versione Word, pronta per la compilazione
>
> Puoi inviare il **DOCX** al team funzionale: contiene i placeholder per le risposte sotto ogni domanda.
>
> Quando ricevi le risposte, usa `br-clarify` per integrarle nel review.
> Quando vuoi, puoi procedere con `br-analyzer` per l'analisi tecnica — le assunzioni verranno incorporate automaticamente.

**Se ci sono bloccanti:**

> Review completata. Ci sono **N problemi bloccanti** ancora aperti.
>
> I report sono salvati in `<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/`:
> - `REVIEW_BR.md` — versione markdown
> - `REVIEW_BR.docx` — versione Word, pronta per la compilazione
>
> Puoi inviare il **DOCX** al team funzionale: contiene i placeholder per le risposte sotto ogni domanda.
>
> **Ti consiglio di attendere chiarimenti dal funzionale prima di procedere con l'analisi tecnica** — il rischio e' di pianificare lavoro su basi fragili che dovra' essere rifatto.
>
> Quando ricevi le risposte, usa `br-clarify` per integrarle nel review.
>
> Pero' la decisione e' tua: se vuoi procedere comunque con `br-analyzer`, le assunzioni proposte verranno incorporate nel piano e i bloccanti aperti saranno segnalati.

---

## Dipendenze

- **`doc-to-markdown`** skill (`~/.claude/skills/doc-to-markdown/`) — per conversione DOCX/DOC in input
- **`markitdown`** — per conversione PDF, PPTX, XLSX (installato come dipendenza di doc-to-markdown, oppure via `pip install 'markitdown[all]'` o `uvx`)
- **`pandoc`** — per generazione REVIEW_BR.docx. Deve essere disponibile su PATH.
