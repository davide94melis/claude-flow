# BR Debug — Design Spec

Skill per la gestione dei bug segnalati dai funzionali durante e dopo il testing di un Business Requirement. Copre l'intero ciclo: importazione dei bug (da Excel o Jira), analisi e assegnazione, esecuzione del fix con sottoagenti e verifica in 3 fasi, chiusura con validazione funzionale, e re-import iterativo.

## Contesto

La suite BR attuale copre il ciclo documentazione -> review -> analisi gap -> piano -> esecuzione -> done. Manca uno stage dedicato ai bug trovati dai funzionali. I bug possono arrivare sia durante l'esecuzione (task completate e deployate mentre altre sono in corso) sia in una fase UAT formale finale.

## Decisioni di design

- **Approccio A+C**: sezione dedicata `bugs` nel manifest (portal-flow) + file `BUG_REPORT_BR.md` come artefatto autonomo (claude-flow) o vista retrocompatibile (portal-flow)
- **Stage parallelo**: il debug coesiste con execute, non e' sequenziale
- **Ciclo di verifica completo**: tutti i bug seguono le 3 fasi (tecnica + coerenza + riesame) indipendentemente dalla severita'
- **Assegnazione mista**: default all'owner della task collegata, override dal TL/PM
- **Dual-mode**: funziona sia in claude-flow (standalone, MD come source of truth) sia in portal-flow (manifest come source of truth)

---

## 1. Posizionamento nella pipeline e ciclo di vita

### Stage parallelo

Il debug non e' un nuovo stage sequenziale. Si attiva in qualsiasi momento dopo `approved` e coesiste con `execute`:

```
stato_pipeline:  approved ──→ execute ──→ done
debug:           ─────────── debug_attivo ─────── debug chiuso
```

Le due dimensioni sono indipendenti. Il BR passa a `done` solo quando tutte le task sono completate E tutti i bug sono chiusi.

In portal-flow il manifest usa `bugs.debug_attivo: true/false`. In claude-flow la presenza di `BUG_REPORT_BR.md` nella cartella del BR indica bug attivi.

### Ciclo di vita del singolo bug

```
aperto → assegnato → in_corso → verificato → chiuso
                        ↓
                     bloccato
```

| Stato | Significato |
|---|---|
| `aperto` | Bug importato, non ancora assegnato |
| `assegnato` | Owner definito, non ancora in lavorazione |
| `in_corso` | Lo sviluppatore sta lavorando il fix |
| `verificato` | Fix implementato e verificato tecnicamente, in attesa di validazione funzionale |
| `chiuso` | Il funzionale conferma che il bug e' risolto |
| `bloccato` | Il fix e' bloccato da un impedimento |

### Severita'

| Livello | Significato |
|---|---|
| `critico` | Blocca l'uso della funzionalita' |
| `maggiore` | Funzionalita' degradata ma utilizzabile |
| `minore` | Difetto estetico o marginale |

Tutti i livelli seguono il ciclo di verifica completo (3 fasi).

---

## 2. Doppia modalita' di funzionamento

| Contesto | Source of truth | Artefatti |
|---|---|---|
| **claude-flow** (standalone) | `BUG_REPORT_BR.md` nella cartella del BR in `plans/` | File MD diretto, nessun manifest |
| **portal-flow** (con pipeline) | `manifest.bugs[]` in `brs/<nome>/manifest.json` | Manifest + vista MD generata |

La skill rileva automaticamente il contesto:
- Se trova `brs/<nome>/manifest.json` -> modalita' portal-flow
- Se trova `plans/*/PIANO_IMPLEMENTAZIONE_BR.md` senza manifest -> modalita' claude-flow

---

## 3. Importazione bug (Fase 1)

### Domanda 1 — BR di riferimento

Auto-detect:
- Portal-flow: `brs/*/manifest.json` con `stato_pipeline` in `approved|execute`
- Claude-flow: cartelle in `plans/in-progress/` e `plans/todo/`

Se ne trova uno lo propone, se piu' di uno chiede quale.

### Domanda 2 — Sorgente dei bug

Tre opzioni: File Excel, Jira, o entrambi.

### Import da Excel — Mapping intelligente

La skill legge la prima riga (header) e tenta un mapping automatico basato su pattern riconoscibili (case-insensitive):

| Campo interno | Pattern riconosciuti |
|---|---|
| `id` | id, #, numero |
| `fase` | fase, fase processo, area, modulo |
| `sezione` | sezione, sotto-sezione, pagina |
| `utente` | utente, user, profilo, ruolo utente |
| `titolo` | titolo, problema riscontrato, summary, title |
| `descrizione` | descrizione, descrizione del problema, description |
| `screenshot` | screen, screenshot, allegati, immagini |
| `riferimento` | rif, rif. pratica, reference, ticket |
| `tipo` | tipo, tipo segnalazione, type, category |
| `stato_originale` | stato, status |
| `data` | data, date, data segnalazione |
| `note_dev` | note team sviluppo, note dev, dev notes |
| `note_funzionale` | note team funzionale, note funzionali |

Se una colonna non viene mappata automaticamente, la skill la presenta e chiede se e' rilevante.

### Mapping dei tipi segnalazione

| Tipo segnalazione (Excel) | Tipo (interno) | Severita' (default) |
|---|---|---|
| `DEFECT/BUG` | `bug` | `maggiore` |
| `MINOR` | `bug` | `minore` |
| `CAMBIO LABEL` | `label` | `minore` |
| `CR` | `change_request` | `minore` (fisso) |

Le CR hanno sempre severita' `minore` — non modificabile. Per gli altri tipi il TL/PM puo' cambiare la severita' in fase di conferma.

### Filtro per stato

La skill importa solo i bug con stato diverso da "Chiuso". Quelli gia' chiusi vengono conteggiati ma non importati. L'utente puo' filtrare ulteriormente per tipo.

### Screenshot

Se il file ha un foglio "Screen" con immagini referenziate, la skill le estrae e le salva nella cartella del BR.

### Import da Jira

Usa la skill `jira` o l'MCP Jira se configurato. Chiede progetto e filtri (tipo = Bug, stato = Open/To Do, opzionalmente sprint o label). Mappa i campi Jira standard ai campi interni.

### Domanda 3 — Collegamento alle funzionalita'

La skill tenta un collegamento automatico usando `fase` + `sezione` del bug confrontati con stream e task del piano. Presenta la mappatura proposta per conferma e correzione.

### Domanda 4 — Assegnazione

Default: owner della task collegata. Il TL/PM puo' riassegnare. Per bug senza match, chiede esplicitamente.

Bug senza collegamento a task/stream vengono categorizzati sotto lo pseudo-stream `debug-generico`.

Dopo la conferma, scrive i bug nella source of truth (MD o manifest).

---

## 4. Struttura dati del bug

### Campi

| Campo | Tipo | Descrizione |
|---|---|---|
| `id` | string | `BUG-001`, `BUG-002`... sequenziale |
| `id_originale` | string/number | ID dal file sorgente o ticket Jira |
| `tipo` | enum | `bug`, `label`, `change_request` |
| `severita` | enum | `critico`, `maggiore`, `minore` |
| `fase` | string | Area funzionale (es. "Dashboard", "Accesso") |
| `sezione` | string | Sotto-sezione (es. "Tabella Pratiche Attive") |
| `utente` | string | Profilo utente impattato (es. "Banca", "ALL") |
| `titolo` | string | Titolo breve del problema |
| `descrizione` | string | Descrizione completa (inclusi Update) |
| `screenshot` | string[] | Path agli screenshot estratti |
| `riferimento` | string | Rif. pratica o ticket esterno |
| `task_collegata` | string | ID della task del piano collegata (es. `T-012`) |
| `stream_collegato` | string | Stream di appartenenza (es. `stream-booking`) |
| `owner` | string | Sviluppatore assegnato |
| `stato` | enum | `aperto`, `assegnato`, `in_corso`, `verificato`, `chiuso`, `bloccato` |
| `progresso` | number | 0-100% |
| `branch` | string | Branch del fix (es. `fix/BUG-001-login-case`) |
| `data_segnalazione` | date | Data originale dal file/Jira |
| `data_assegnazione` | date | Quando e' stato assegnato |
| `data_chiusura` | date | Quando e' stato chiuso |
| `note_dev` | string | Note dal team sviluppo |
| `note_funzionale` | string | Note dal team funzionale |
| `fix_summary` | string | Riepilogo del fix applicato (compilato al completamento) |

### Branch convention

`fix/<br-name>-BUG-<NNN>-<slug>` (es. `fix/monitoring-BUG-003-table-sort`).

Per bug minori raggruppabili (es. piu' cambi label nella stessa sezione), la skill puo' proporre un branch unico: `fix/<br-name>-label-<sezione>`.

### Struttura manifest (portal-flow)

```json
{
  "bugs": {
    "debug_attivo": true,
    "data_ultimo_import": "2026-05-11",
    "sorgente": "excel",
    "sorgente_file": "20260430_SegnalazioniTest_v01.xlsx",
    "riepilogo": {
      "totali": 33,
      "aperti": 20,
      "in_corso": 5,
      "verificati": 3,
      "chiusi": 5,
      "bloccati": 0
    },
    "lista": [
      {
        "id": "BUG-001",
        "id_originale": 1,
        "tipo": "bug",
        "severita": "maggiore",
        "...": "...tutti i campi..."
      }
    ]
  }
}
```

### Struttura BUG_REPORT_BR.md (claude-flow / vista portal-flow)

```markdown
# Bug Report — <nome BR>

Data import: <data>
Sorgente: <file/jira>
Ultimo aggiornamento: <data e ora>

## Riepilogo

| Metrica | Valore |
|---|---|
| Bug totali | N |
| Aperti | X |
| In corso | Y |
| Verificati | Z |
| Chiusi | W |
| Bloccati | K |

## Lista Bug

| ID | Tipo | Sev. | Fase | Sezione | Titolo | Owner | Stato | Task | Branch |
|---|---|---|---|---|---|---|---|---|---|
| BUG-001 | bug | maggiore | Dashboard | Tabella Pratiche | ... | Marco | assegnato | T-012 | — |

## Dettaglio Bug

### BUG-001 — <titolo>

- **Tipo**: bug | **Severita'**: maggiore
- **Fase**: Dashboard > Tabella Pratiche Attive
- **Utente**: Banca
- **Task collegata**: T-012
- **Owner**: Marco
- **Stato**: assegnato

**Descrizione:**
<descrizione completa>

**Screenshot:** [link se presente]
**Note dev:** —
**Note funzionale:** —
**Fix summary:** —

---

## Log Attivita'

### <data>
- Import di N bug da <sorgente>
```

---

## 5. Esecuzione del fix (Fase 2)

### Selezione bug

La skill mostra i bug assegnati allo sviluppatore, ordinati per severita' (critico > maggiore > minore) e poi per tipo (bug > label > change_request). Le CR finiscono sempre in coda.

### Analisi del bug prima del fix

Prima di lanciare il sottoagente, la skill:

1. Legge la descrizione completa del bug (inclusi Update inline)
2. Legge la task collegata dal piano e dal gap report per il contesto funzionale
3. Localizza il codice coinvolto usando fase/sezione e file della task collegata. Se necessario, usa un agente Explore
4. Legge gli screenshot se presenti
5. Formula un'ipotesi di root cause

Presenta l'analisi allo sviluppatore e aspetta conferma prima di procedere.

### Creazione branch

Dopo la conferma, crea il branch `fix/<br-name>-BUG-<NNN>-<slug>` in tutte le repo coinvolte. Stessa logica di br-executor per multi-repo.

### Esecuzione con sottoagenti

Lancia un sottoagente con prompt autosufficiente che include:

1. Il bug — descrizione completa, screenshot, utente impattato
2. Il contesto — task originale, file coinvolti, pattern del progetto
3. L'ipotesi di root cause
4. Cosa deve fare — fix + test specifici:
   - Test che riproduce il bug (deve fallire PRIMA del fix)
   - Test che verifica il fix (deve passare DOPO)
   - Test di regressione (comportamento corretto preesistente)

### Verifica in 3 fasi

Identica a br-executor:

- **Fase A — Tecnica**: test tutti verdi, build compila, copertura happy path + edge case + error case
- **Fase B — Coerenza col bug**: il fix risolve effettivamente il problema descritto? Tutti gli scenari del bug (inclusi Update) sono coperti?
- **Fase C — Riesame**: nessuna regressione introdotta, nessuna assunzione nascosta, nomi seguono le convenzioni

### Suggerimento commit

Mai committa autonomamente. Suggerisce per ogni repo:

```
git add [file specifici]
git commit -m "fix(<area>): <descrizione del fix> (BUG-NNN)"
```

### Completamento bug

Quando il fix e' implementato e verificato tecnicamente, la skill produce la tabella di verifica e porta il bug a stato `verificato`:

| # | Aspetto | Verificato | Dettaglio |
|---|---|---|---|
| 1 | Bug riprodotto nel test | Si/No | nome test |
| 2 | Fix implementato | Si/No | file:riga |
| 3 | Test di regressione | Si/No | nome test |
| 4 | Build | Si/No | stato |

Il campo `fix_summary` viene compilato con un riepilogo del fix.

Stato `verificato` = "tecnicamente fixato, in attesa validazione funzionale". Il passaggio a `chiuso` avviene quando il funzionale conferma.

### Raggruppamento bug minori

Per bug di tipo `label` o `minore` nella stessa sezione, la skill propone di lavorarli insieme su un unico branch `fix/<br-name>-label-<sezione>`.

---

## 6. Chiusura bug e re-import

### Chiusura da parte del funzionale

Tre flussi supportati:

**Flusso 1 — Excel aggiornato:** il funzionale aggiorna il file Excel cambiando lo stato. La skill confronta con lo stato attuale e mostra i delta per conferma.

**Flusso 2 — Jira:** se l'import originale era da Jira, la skill rilegge lo stato dei ticket per sincronizzare.

**Flusso 3 — Conversazione:** l'utente riporta a voce quali bug sono confermati e quali riaperti.

### Bug riaperti

Quando un bug torna da `verificato` a `aperto`:

1. Stato torna a `aperto`
2. Nota del funzionale aggiunta a `note_funzionale`
3. Descrizione preservata con append: `[Riapertura <data>]: <nota>`
4. Branch precedente riutilizzato se esiste, altrimenti nuovo
5. `fix_summary` precedente preservato con prefisso `[Fix precedente]: `

### Re-import iterativo

La skill puo' essere invocata piu' volte sullo stesso BR:

- Bug gia' importati (per `id_originale`) non vengono duplicati
- Nuovi bug nel file/Jira vengono aggiunti con ID sequenziale
- Bug con stato cambiato vengono sincronizzati
- Presenta sempre il delta prima di applicare

### Condizione di completamento debug

Quando tutti i bug hanno stato `chiuso`:
- Portal-flow: `manifest.bugs.debug_attivo` -> `false`, entry nella timeline
- Claude-flow: sezione "Debug completato" aggiunta al BUG_REPORT_BR.md

---

## 7. Integrazione con la pipeline

### Dashboard TL/PM (portal-flow)

Mostra i bug come sezione separata per ogni BR con debug attivo, con conteggi e azioni suggerite.

### Dashboard Dev (portal-flow)

Mostra bug e task in sezioni separate. Lo sviluppatore sceglie se continuare una task o lavorare un bug.

### Commit format

`[br-debug] <nome>: <azione>`

Esempi:
- `[br-debug] booking-v2: importati 33 bug da Excel`
- `[br-debug] booking-v2: BUG-003 stato → in_corso`
- `[br-debug] booking-v2: BUG-003 stato → verificato`
- `[br-debug] booking-v2: re-import — 5 nuovi, 3 chiusi`

### Generazione vista MD (portal-flow)

Dopo ogni modifica ai bug nel manifest, rigenera `brs/<nome>/BUG_REPORT_BR.md`.

### Lettura progresso aggregata

I bug seguono la stessa logica delle task per l'aggregazione cross-branch. La pipeline legge `manifest.bugs.lista[]` da tutti i branch remoti e aggrega con la regola "highest progress wins".

---

## 8. Trigger

| Frase | Modalita' |
|---|---|
| "ci sono dei bug", "bug dal funzionale", "segnalazioni test", "defect ricevuti" | import |
| "lavora il bug", "fix il bug", "debug br" | esecuzione |
| "il funzionale ha testato", "bug confermati", "aggiorna i bug" | chiusura/re-import |

La skill rileva automaticamente la modalita':
- Se non esiste BUG_REPORT_BR.md / manifest.bugs -> import mode
- Se esiste e ci sono bug assegnati allo sviluppatore -> execution mode
- Se l'utente menziona risposte/conferme del funzionale -> chiusura mode

---

## 9. Dipendenze

| Dipendenza | Usata per | Installazione |
|---|---|---|
| `openpyxl` (Python) | Lettura Excel | `pip install openpyxl` |
| skill `jira` | Import da Jira (opzionale) | gia' nell'ecosistema |
| skill `doc-to-markdown` | Conversione allegati (se necessario) | gia' installata |

---

## 10. Regole fondamentali

1. Mai committare autonomamente nel codebase del progetto — suggerisci e aspetta conferma
2. Mai procedere senza conferma — tra un bug e l'altro, prima di ogni modifica
3. Verificare prima di dichiarare verificato — 3 fasi complete per ogni bug
4. Mai duplicare bug al re-import — confronta sempre per `id_originale`
5. Mai sovrascrivere note precedenti — append, non replace
6. Il sottoagente implementa, l'agente principale coordina
7. Supportare entrambe le modalita' (claude-flow e portal-flow) senza compromessi
