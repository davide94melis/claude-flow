# Design — br-reviewer: Review Qualita' Documentazione BR

Data: 2026-04-28

## Contesto

Il flusso BR attuale (br-analyzer → br-executor → br-updater + br-progress-report) prende la documentazione funzionale per buona e procede direttamente con la gap analysis tecnica. Quando la documentazione ha problemi — flussi incompleti, contraddizioni, ambiguita', riferimenti mancanti — questi emergono solo durante l'implementazione, causando rework e assunzioni non validate.

## Obiettivo

Aggiungere una skill `br-reviewer` che si posiziona *prima* di br-analyzer nel flusso. Analizza la documentazione funzionale per qualita', coerenza e completezza, produce un report duale (per il funzionale e per il tecnico) e, se si decide di procedere, passa le assunzioni a br-analyzer tramite handoff automatico.

Contemporaneamente, ristrutturare le cartelle `plans/` in tutte le skill per organizzare i file per BR invece che flat.

## Flusso complessivo

```
br-reviewer → br-analyzer → br-executor → br-updater
                                         ↘ br-progress-report
```

## Nuova struttura cartelle

Ogni BR ha la propria cartella con formato `<YYYY-MM-DD>_<nome-br>/`:

```
plans/
  todo/
    2026-04-28_booking-v2/
      br-docs-converted/          ← creata da br-reviewer (fase 2)
      REVIEW_BR.md                ← output di br-reviewer (fase 4)
      GAP_REPORT_BR.md            ← output di br-analyzer
      PIANO_IMPLEMENTAZIONE_BR.md ← output di br-analyzer
  in-progress/
    2026-04-28_booking-v2/        ← cartella spostata da br-executor
      ...tutto il contenuto...
      PROGRESSO_BR.md             ← creato da br-executor
  done/
    2026-04-28_booking-v2/        ← cartella spostata al completamento
      AVANZAMENTO_BR.xlsx         ← creato da br-progress-report
```

La cartella intera si sposta tra `todo/`, `in-progress/` e `done/` — non i singoli file.

Tutte le skill mantengono un fallback: se non trovano la struttura a cartelle, cercano i file flat come oggi — retrocompatibilita' per BR gia' in corso.

---

## br-reviewer — Design dettagliato

### Fase 1 — Raccolta input

Domande conversazionali, una alla volta:

1. **Nome del BR** — identificativo per la cartella (es. "booking-v2" → `2026-04-28_booking-v2/`)
2. **Documentazione** — path ai file del BR. Accetta MD, PDF, DOCX, XLSX, PPTX, immagini.
3. **Codebase coinvolti** — nome, sigla, path per ogni repository. Servono per il check leggero contro il codice. Non serve il team di sviluppo — quello lo chiede br-analyzer.

Riepilogo e conferma prima di procedere.

### Fase 2 — Conversione documentazione in MD

Stessa logica che oggi ha br-analyzer (doc-to-markdown per DOCX/DOC, markitdown per PDF/PPTX/XLSX, copia diretta per MD, Read per immagini). I file convertiti vanno in `plans/todo/<data>_<nome>/br-docs-converted/`.

Questa fase viene spostata da br-analyzer a br-reviewer. br-analyzer non la rifara' — lavorera' sui file gia' convertiti.

### Fase 3 — Analisi della documentazione

Tre livelli di analisi:

#### 3.1 — Analisi intra-documento

Per ogni documento singolo, verifica:
- Coerenza interna (stesse informazioni descritte in modo coerente in tutte le sezioni)
- Completezza dei flussi (caso felice + eccezioni + errori)
- Chiarezza dei requisiti (nessuna ambiguita', nessun "se opportuno")
- Definizione di regole di business (stati, transizioni, condizioni, vincoli)

#### 3.2 — Analisi inter-documento

Confronto tra documenti diversi:
- BR vs mockup: ogni elemento visuale ha un corrispettivo funzionale e viceversa
- BR vs specifiche tecniche: coerenza tra requisiti e vincoli tecnici
- Terminologia coerente tra tutti i documenti

#### 3.3 — Check leggero contro il codice

Per ogni codebase fornito, verifica superficiale contro:
- Entita' e modelli dati esistenti (nomi, campi, relazioni)
- Enum e costanti (valori, naming)
- API/endpoint esistenti (naming, struttura)
- Flussi e stati gia' implementati

Lo scopo non e' fare la gap analysis (quello lo fa br-analyzer) ma trovare problemi di *documentazione* visibili solo confrontando col codice: il BR presuppone strutture che nel codice esistono ma sono diverse.

### Fase 4 — Generazione output

#### Categorie di problemi

Ogni problema trovato viene classificato per tipo con flag bloccante si/no:

| Categoria | Descrizione |
|---|---|
| **Incoerenza** | Contraddizioni tra parti della documentazione |
| **Gap funzionale** | Pezzi mancanti nella descrizione del comportamento |
| **Ambiguita'** | Punti interpretabili in piu' modi |
| **Riferimento mancante** | Dipendenze esterne non specificate |
| **Disallineamento col codice** | Problemi visibili solo confrontando col codebase |

Per ogni problema:
- **Categoria**: una delle 5 sopra
- **Bloccante**: si/no
- **Dove**: riferimento al documento e sezione
- **Problema**: descrizione precisa
- **Impatto**: cosa succede se non viene risolto
- **Assunzione proposta** (solo per i non-bloccanti): cosa il team tecnico assumera' se non arriva chiarimento

#### Struttura del REVIEW_BR.md

```
# Review Documentazione BR [nome/versione]

Data review: `<data>`

Documentazione analizzata:
- [lista file con path]

Codebase verificati:
- [per ogni repo: SIGLA (nome) → path]

## Esito sintetico

[2-3 frasi: qualita' complessiva, numero problemi per categoria,
presenza o meno di bloccanti]

Problemi trovati: N totali (X bloccanti, Y non bloccanti)

---

## Parte 1 — Per il team funzionale

Questa sezione elenca i punti che richiedono chiarimento o correzione.

### Problemi bloccanti

[Se presenti. Impediscono una pianificazione affidabile.]

#### 1. [Titolo problema]

- **Categoria**: [Incoerenza / Gap funzionale / Ambiguita' / ...]
- **Dove**: [documento, sezione/pagina]
- **Problema**: [descrizione chiara, comprensibile dal funzionale]
- **Impatto**: [perche' senza risposta non si puo' procedere]
- **Domanda per il funzionale**: [domanda precisa a cui serve risposta]

#### 2. [...]

### Problemi non bloccanti

#### 1. [Titolo problema]

- **Categoria**: [...]
- **Dove**: [...]
- **Problema**: [...]
- **Domanda per il funzionale**: [domanda precisa]
- **Nota**: se non arriva chiarimento, il team tecnico procedera'
  con l'assunzione indicata nella Parte 2.

#### 2. [...]

---

## Parte 2 — Per il team tecnico

Assunzioni che il team tecnico adottera' in assenza di chiarimenti.

### Assunzioni proposte

| # | Problema rif. | Assunzione proposta | Rischio se errata | Costo di correzione |
|---|---|---|---|---|
| A-001 | Problema 3 | [descrizione] | [impatto] | Basso / Medio / Alto |

### Disallineamenti col codice

| # | Concetto BR | Nel codice | File/Classe | Nota |
|---|---|---|---|---|
| D-001 | [termine/concetto BR] | [cosa esiste nel codice] | [path] | [discrepanza] |

---

## Riepilogo per br-analyzer

[Sezione tecnica consumata automaticamente da br-analyzer.]

Assunzioni confermate: [lista A-XXX]
Bloccanti aperti: [lista bloccanti non risolti, se si procede comunque]
```

#### Presentazione all'utente e chiusura

Dopo aver generato il report, la skill lo presenta all'utente per revisione. L'utente puo' chiedere modifiche.

Quando l'utente conferma il report:

**Se non ci sono bloccanti:**
> Review completata. Nessun bloccante trovato. Puoi procedere con br-analyzer.

**Se ci sono bloccanti:**
> Review completata. Ci sono **N problemi bloccanti** ancora aperti.
> Ti consiglio di attendere chiarimenti dal funzionale prima di procedere
> con l'analisi tecnica — il rischio e' di pianificare lavoro su basi fragili
> che dovra' essere rifatto.
> Pero' la decisione e' tua: se vuoi procedere comunque, le assunzioni
> proposte verranno incorporate nel piano.

---

## Modifiche alle skill esistenti

### br-analyzer

- **Fase 1** aggiunge domanda "nome del BR" per la cartella. Se trova una cartella in `plans/todo/` con `REVIEW_BR.md`, la propone direttamente saltando la domanda. Se invocato senza br-reviewer, crea la cartella lui e esegue la conversione come oggi
- **Handoff automatico**: all'avvio cerca `REVIEW_BR.md` nella cartella del BR. Se lo trova, legge la sezione "Riepilogo per br-analyzer" e incorpora le assunzioni nella sezione "Assunzioni" del piano di implementazione. Se trova `br-docs-converted/`, salta la conversione
- **Se REVIEW_BR.md non esiste**: br-analyzer funziona come oggi (conversione + analisi), ma crea l'output nella nuova struttura a cartelle. La review non e' un prerequisito obbligatorio — e' fortemente consigliata ma non bloccante
- **Output** va dentro la cartella del BR (`plans/todo/<data>_<nome>/`), non flat
- **Retrocompatibilita'**: se non trova struttura a cartelle, cerca i file flat come oggi

### br-executor

- Sposta l'intera cartella da `todo/` a `in-progress/`, non i singoli file
- Cerca i file dentro la cartella del BR
- Crea `PROGRESSO_BR.md` dentro la cartella
- Retrocompatibilita' con file flat

### br-updater

- Cerca la cartella del BR in `plans/in-progress/` o `plans/todo/`
- Aggiorna i file dentro la cartella
- Retrocompatibilita' con file flat

### br-progress-report

- Cerca e salva l'Excel dentro la cartella del BR
- Retrocompatibilita' con file flat

---

## Trigger e registrazione

**Nome skill**: `br-reviewer`

**Trigger phrases**: "rivedi il br", "review del br", "controlla la documentazione", "verifica il br", "nuovo br da verificare", "c'e' un br da rivedere"

**Registrazione CLAUDE.md** — blocco posizionato prima di br-analyzer:

```markdown
# br-reviewer
- **br-reviewer** (`~/.claude/skills/br-reviewer/SKILL.md`) - review qualita'
  della documentazione funzionale prima dell'analisi tecnica.
  Trigger: "rivedi il br", "review del br"
When the user says "rivedi il br", "review del br", "controlla la documentazione",
"verifica il br", or similar phrases about reviewing BR documentation quality,
invoke the Skill tool with `skill: "br-reviewer"` before doing anything else.
```

## Dipendenze

- `doc-to-markdown` skill (`~/.claude/skills/doc-to-markdown/`)
- `markitdown` (per PDF, PPTX, XLSX)
