---
name: br-pipeline
description: Orchestratore unico per il ciclo di vita dei Business Requirement. Legge lo stato dal manifest.json di ogni BR nel repo, rileva il ruolo dell'utente (TL/PM o Dev), mostra una dashboard con lo stato di ogni BR e propone/lancia lo stage giusto delegando alle skill esistenti (br-reviewer, br-clarify, br-analyzer, br-executor, br-updater, br-progress-report). Usa questa skill quando l'utente dice "br-pipeline", "pipeline br", "le mie task", "stato dei br", "dashboard br", o qualsiasi variazione che implichi la necessita' di vedere lo stato complessivo dei BR o di procedere con il prossimo step del ciclo di vita.
---

# BR Pipeline — Orchestratore Ciclo di Vita BR

Questa skill e' l'**unico punto di ingresso** per la gestione dei BR. Legge lo stato di ogni BR dal `manifest.json` nel repo, rileva il ruolo dell'utente e propone l'azione giusta — delegando internamente alle 6 skill esistenti senza reimplementare la loro logica.

```
Flusso:

  onboard ──→ review ──→ analyze ──→ approved ──→ execute ──→ done
                 ↕                                    ↕
              clarify                              update

  Stage parallelo (dopo approved):
  ─────────────── debug_attivo ──────────────── debug chiuso
```

Skill delegate:

| Stato | Azione | Skill delegata |
|---|---|---|
| `onboard` | Lancia il review della documentazione | `br-reviewer` |
| `review` | Gestisci le risposte del funzionale | `br-clarify` |
| `clarify` | Gestisci ulteriori risposte o procedi con analisi | `br-clarify` / `br-analyzer` |
| `analyze` | Lancia l'analisi gap e genera il piano | `br-analyzer` |
| `approved` | Il piano e' stato approvato, avvia l'esecuzione | `br-executor` |
| `execute` | Mostra progresso, lavora le task | `br-executor` |
| `done` | Tutte le task completate | — |
| `update` | Il BR e' cambiato, aggiorna il piano | `br-updater` |
| `debug` | Gestisci i bug dal testing funzionale | `br-debug` |

La pipeline NON reimplementa la logica delle skill. Quando l'utente conferma un'azione, la pipeline aggiorna il manifest e invoca la skill corrispondente tramite il tool `Skill`.

---

## Fase 1 — Rilevamento BR

### Ricerca manifest

Cerca tutti i BR attivi nel repo:

```bash
ls brs/*/manifest.json 2>/dev/null
```

Se non trovi nessun manifest:

> Non ho trovato nessun BR attivo in questo repo.
>
> La struttura attesa e':
> ```
> brs/
> └── <nome-br>/
>     └── manifest.json
> ```
>
> Vuoi creare un nuovo BR?

Se l'utente vuole creare un nuovo BR, guida la creazione del manifest iniziale (vedi sezione "Creazione nuovo BR").

### Lettura stato

Per ogni `brs/*/manifest.json` trovato, leggi:
- `nome` — nome del BR
- `stato_pipeline` — stato corrente
- `data_creazione` — quando e' stato creato
- `creato_da` — chi lo ha creato
- `codebase` — repository coinvolte
- `documenti` — documentazione associata
- `team` — sviluppatori assegnati
- `piano.approvato` — se il piano e' stato approvato
- `piano.task` — lista task (se presente)
- `timeline` — cronologia delle azioni

---

## Fase 2 — Dashboard e Rilevamento Ruolo

### Rilevamento ruolo

Determina il ruolo dell'utente in base al trigger usato:

**TL/PM** — l'utente ha detto `"br-pipeline"`, `"pipeline br"`, `"stato dei br"`, `"dashboard br"`, o simili.
Mostra la vista completa con tutti i BR e le azioni disponibili.

**Dev** — l'utente ha detto `"le mie task"`, `"cosa devo fare"`, `"mie task br"`, o simili.
Mostra solo le task assegnate al developer. Cerca `.br-local.json` nella root del repo per identificare lo sviluppatore.

### Lettura progresso aggregata (cross-branch)

Prima di mostrare la dashboard (sia TL/PM che Dev), esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task. Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch — senza aggregazione si vedrebbe solo il progresso locale.

Per ogni BR con `stato_pipeline` uguale a `"execute"` o `"approved"`:

1. `git fetch origin` per sincronizzare i branch remoti

2. Trova la cartella del BR in `plans/`: `plans/*/YYYY-*_<nome>/`

3. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre:
   - Gli ID di tutte le task (T-001, T-003, T-005, ...)
   - Se il piano ha una colonna **Branch** nel backlog: estrai i nomi branch di ogni task
   - Il nome del BR dalla cartella (es. `2026-05-04_monitoring` → `monitoring`)

4. **Trova i branch remoti da controllare:**
   - **Se il piano ha colonna Branch**: usa direttamente i nomi branch elencati nel piano. Per ogni branch con valore diverso da `—`, verifica che esista come remoto:
     ```bash
     git branch -r | grep "<branch-name>"
     ```
   - **Se il piano NON ha colonna Branch** (retrocompatibilita' con piani pre-esistenti): cerca tutti i branch remoti che contengono il nome del BR:
     ```bash
     git branch -r | grep -i "feature/<nome-br>"
     ```

5. Per ogni branch trovato, prova a leggere il PROGRESSO da 3 percorsi possibili (il file puo' essere in posizioni diverse a seconda dello stato):
   ```bash
   git show origin/<branch>:plans/in-progress/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/todo/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/done/<cartella-br>/PROGRESSO_BR.md
   ```
   Usa il primo che funziona. Se nessuno funziona, skip quel branch.

6. Leggi anche il PROGRESSO dal branch base del piano (con gli stessi 3 percorsi). Se non esiste su nessun percorso, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

7. Aggrega per task con la regola **"highest progress wins"**:
   - Per ogni task, confronta le versioni da tutti i branch (incluso il baseline)
   - Se una versione mostra "Completata" (100%), vince sempre
   - Altrimenti, prendi la versione con il progresso % piu' alto
   - Se due versioni hanno lo stesso %, prendi quella con lo stato piu' avanzato (In corso > Da iniziare)

8. Ricalcola le metriche di riepilogo (task completate, in corso, progresso complessivo %) dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning:

> Impossibile sincronizzare con il remoto. Il progresso mostrato potrebbe non essere aggiornato.

Usa la vista aggregata per tutte le operazioni successive in questa fase.

### Dashboard TL/PM

Mostra una tabella riassuntiva di tutti i BR:

> ## Dashboard BR
>
> | BR | Stato | Creato il | Codebase | Documenti | Team | Ultimo evento |
> |---|---|---|---|---|---|---|
> | monitoring-v2 | `onboard` | 2026-05-04 | BE, FE, EM, DM | 0 doc | 0 dev | BR creato |
> | booking-v3 | `execute` | 2026-04-15 | BE, FE | 3 doc | 3 dev | T-005 completata |
>
> [Per ogni BR, l'ultimo evento viene dalla timeline]

Poi, per ogni BR in ordine di urgenza (stati piu' avanzati con azioni pendenti prima), proponi l'azione:

> ### Azioni suggerite
>
> **monitoring-v2** (`onboard`):
> Il BR e' appena stato creato. Il prossimo passo e' la review della documentazione funzionale.
> → Vuoi lanciare il review? (delega a `br-reviewer`)
>
> **booking-v3** (`execute`):
> 3/10 task completate. Progresso: 30%. *(aggregato da N branch remoti)*
> → Vuoi vedere il dettaglio delle task? Oppure generare l'Excel di avanzamento?

Aspetta che l'utente scelga un'azione.

### Dashboard Dev

Cerca il file `.br-local.json` nella root del repo:

```bash
cat .br-local.json 2>/dev/null
```

Il file ha questo formato:

```json
{
  "nome": "Marco",
  "email": "marco@example.com"
}
```

**Se `.br-local.json` non esiste**, chiedi:

> Per mostrare le tue task, ho bisogno di sapere chi sei.
>
> [Se ci sono BR con team definito, mostra la lista:]
> I piani attivi hanno questi sviluppatori:
> - Marco (BE Senior)
> - Luca (FE Mid)
> - Anna (BE+GW Junior)
>
> Chi sei? Creo il file `.br-local.json` per le prossime volte.

Dopo l'identificazione, crea `.br-local.json` nella root del repo.

**Se `.br-local.json` esiste**, usa il `nome` per filtrare le task.

Trova tutti i BR con `stato_pipeline: "execute"` o `"approved"` e `piano.approvato: true`. Per ognuno, esegui la **lettura progresso aggregata** (vedi sezione sopra) e filtra le task assegnate al developer dalla vista aggregata.

> ## Le tue task
>
> **BR: booking-v3**
>
> | # | ID | Attivita' | Priorita' | Wave | Stato | Progresso |
> |---|---|---|---|---|---|---|
> | 1 | T-003 | Implementare repository pratiche | P0 | Wave 1 | In corso | 40% |
> | 2 | T-007 | Componente tabella monitoraggio | P1 | Wave 2 | Da iniziare | 0% |
>
> Vuoi procedere con **T-003** (in corso) o passare a un'altra task?

Quando l'utente conferma, la pipeline invoca `br-executor` tramite `Skill`.

### Bug assegnati (Dev)

Se ci sono bug assegnati al developer (da `BUG_REPORT_BR.md` nella cartella del BR in `plans/`), mostrali dopo le task:

> ## I tuoi bug
>
> | # | ID | Sev. | Titolo | Fase > Sezione | Stato |
> |---|---|---|---|---|---|
> | 1 | BUG-003 | critico | Login email maiuscola | Accesso > Login | assegnato |
>
> Vuoi continuare con le task o lavorare **BUG-003**?

Se l'utente sceglie un bug, invoca `br-debug` tramite il tool `Skill`.

---

## Fase 3 — Azioni per Stato (Vista TL/PM)

Quando l'utente seleziona un BR e conferma un'azione, la pipeline:
1. Aggiorna il manifest (stato_pipeline e timeline)
2. Invoca la skill delegata tramite il tool `Skill`

### `onboard` — Lancia il review

L'utente conferma di voler lanciare il review.

**Prepara il contesto**: verifica che i documenti siano presenti in `brs/<nome>/` o che l'utente sappia dove trovarli.

**Aggiorna il manifest** prima di delegare:

```json
{
  "stato_pipeline": "onboard",
  "timeline": [
    ...timeline_esistente,
    {
      "data": "<ISO-timestamp>",
      "attore": "<utente>",
      "ruolo": "TL/PM",
      "azione": "Avviato review documentazione",
      "stage": "onboard → review"
    }
  ]
}
```

**Delega**: invoca la skill `br-reviewer` tramite il tool `Skill`.

Comunica all'utente:

> Avvio il review della documentazione per **[nome BR]**.
> Passo il controllo a `br-reviewer`.

Dopo che br-reviewer completa, al prossimo invoco di br-pipeline, aggiorna `stato_pipeline` a `"review"`.

### `review` / `clarify` — Gestisci risposte del funzionale

Due sotto-azioni possibili:

**A) Ci sono risposte dal funzionale:**

> Il BR **[nome]** e' in stato `review`. Sono arrivate risposte dal funzionale?
>
> 1. **Si**, ho le risposte → delego a `br-clarify`
> 2. **No**, procedo con l'analisi (le assunzioni verranno usate cosi' come sono) → delego a `br-analyzer`
> 3. **Aspetto** — non faccio nulla per ora

Se l'utente sceglie 1:
- Aggiorna timeline con "Avviata gestione chiarimenti"
- Invoca `br-clarify` tramite `Skill`
- Dopo br-clarify, aggiorna `stato_pipeline` a `"clarify"`

Se l'utente sceglie 2:
- Aggiorna `stato_pipeline` a `"clarify"` (by-pass)
- Aggiorna timeline con "Saltato chiarimento, procedo con analisi"
- Procedi come stato `clarify` → analisi

**B) Gia' in `clarify` (chiarimenti gia' ricevuti):**

> Il BR **[nome]** ha gia' ricevuto chiarimenti. Vuoi:
>
> 1. **Aggiungere altre risposte** → delego a `br-clarify` (supporta round multipli)
> 2. **Procedere con l'analisi gap** → delego a `br-analyzer`

### `analyze` — Lancia l'analisi gap

> Il BR **[nome]** e' pronto per l'analisi gap.
> Questo generera' il gap report e il piano di implementazione.
>
> → Vuoi lanciare l'analisi? (delega a `br-analyzer`)

Se l'utente conferma:
- Aggiorna timeline con "Avviata analisi gap"
- Invoca `br-analyzer` tramite `Skill`
- Dopo br-analyzer, aggiorna `stato_pipeline` a `"approve"`

### `approve` — Approva il piano

Leggi il `PIANO_IMPLEMENTAZIONE_BR.md` dalla cartella del BR in `plans/`.

> Il BR **[nome]** ha un piano di implementazione pronto.
>
> Riepilogo:
> - Task totali: N
> - Stream: [lista stream]
> - Effort stimato: X gg/uomo
> - Durata calendario: Y settimane
> - Sviluppatori: [lista]
>
> Vuoi **approvare** il piano e rendere le task disponibili per l'esecuzione?

Se l'utente approva:
- Aggiorna il manifest:
  ```json
  {
    "stato_pipeline": "approved",
    "piano": {
      "approvato": true,
      "data_approvazione": "<ISO-timestamp>",
      "approvato_da": "<utente>"
    },
    "timeline": [
      ...timeline_esistente,
      {
        "data": "<ISO-timestamp>",
        "attore": "<utente>",
        "ruolo": "TL/PM",
        "azione": "Piano approvato",
        "stage": "approve"
      }
    ]
  }
  ```

Se l'utente vuole modifiche, guida la discussione e aggiorna il piano prima di ri-proporre l'approvazione.

### `approved` / `execute` — Esecuzione task

Mostra lo stato di avanzamento:

> **BR: [nome]** — Esecuzione in corso
>
> | Metrica | Valore |
> |---|---|
> | Task totali | N |
> | Completate | X (xx%) |
> | In corso | Y |
> | Da iniziare | Z |
> | Bloccate | W |
>
> Azioni disponibili:
> 1. **Lavora le task** (come sviluppatore) → delego a `br-executor`
> 2. **Genera il report Excel** → delego a `br-progress-report`
> 3. **Il BR e' stato aggiornato** → delego a `br-updater`

Quando l'utente sceglie:
- Opzione 1: aggiorna `stato_pipeline` a `"execute"` (se non lo e' gia'), invoca `br-executor`
- Opzione 2: invoca `br-progress-report` (non cambia lo stato)
- Opzione 3: aggiorna `stato_pipeline` a `"update"`, invoca `br-updater`

### Debug attivo

Quando un BR ha bug attivi (esiste `BUG_REPORT_BR.md` nella cartella del BR in `plans/`), mostra una sezione aggiuntiva nella dashboard:

> **[nome BR]** (`execute` + debug attivo):
> Task: X/N completate (Y%)
> Bug: A aperti, B in corso, C verificati, D chiusi — **E totali**
>
> Azioni disponibili:
> 1. **Lavora le task** → delego a `br-executor`
> 2. **Gestisci i bug** → delego a `br-debug`
> 3. **Genera il report Excel** → delego a `br-progress-report`
> 4. **Il BR e' stato aggiornato** → delego a `br-updater`

Se l'utente sceglie "Gestisci i bug":
- Aggiungi entry alla timeline: "Avviata gestione bug"
- Invoca `br-debug` tramite il tool `Skill`

### `update` — BR aggiornato

> Il BR **[nome]** e' stato segnalato come aggiornato.
> Lancio l'aggiornamento del piano preservando il progresso.
>
> → Procedo? (delega a `br-updater`)

Dopo br-updater, aggiorna `stato_pipeline` a `"execute"` (ritorna in esecuzione con il piano aggiornato).

### `done` — Completato

> Il BR **[nome]** e' completato. Tutte le task sono state eseguite.
>
> Azioni disponibili:
> 1. **Genera il report Excel finale** → delego a `br-progress-report`
> 2. **Nessuna azione** — il BR e' chiuso

---

## Fase 4 — Creazione Nuovo BR

Quando l'utente vuole creare un nuovo BR (dalla dashboard o esplicitamente):

### Raccolta dati

Poni le domande una alla volta:

**Domanda 1 — Nome del BR:**

> Come vuoi chiamare questo BR?
>
> Esempio: "monitoring-v2", "booking-v3", "auth-refactor"

Verifica che non esista gia' una cartella `brs/<nome>/`.

**Domanda 2 — Repository coinvolte:**

> Quali repository sono coinvolte in questo BR?
> Per ognuna, dammi:
> - **Nome** (es. "back end", "front end")
> - **Sigla** (es. "BE", "FE")
>
> Esempio: "back end (BE), front end (FE), email manager (EM)"

**Domanda 3 — Chi lo crea:**

> Chi sta creando questo BR? (nome o email)

### Creazione manifest

```bash
mkdir -p "brs/<nome>"
```

Genera `brs/<nome>/manifest.json`:

```json
{
  "version": "1.0",
  "nome": "<nome>",
  "data_creazione": "<YYYY-MM-DD>",
  "creato_da": "<utente>",
  "stato_pipeline": "onboard",
  "codebase": [
    {
      "nome": "<nome repo>",
      "sigla": "<SIGLA>"
    }
  ],
  "documenti": [],
  "team": [],
  "review": {
    "data": null,
    "esito": null,
    "problemi": [],
    "assunzioni": [],
    "disallineamenti_codice": []
  },
  "qa": {
    "criteri_accettazione": []
  },
  "gap_analysis": {
    "data": null,
    "matrice": [],
    "gap_aperti": []
  },
  "piano": {
    "approvato": false,
    "data_approvazione": null,
    "approvato_da": null,
    "stream": [],
    "task": []
  },
  "timeline": [
    {
      "data": "<ISO-timestamp>",
      "attore": "<utente>",
      "ruolo": "funzionale",
      "azione": "BR creato",
      "stage": "onboard"
    }
  ]
}
```

Conferma:

> BR **[nome]** creato in `brs/<nome>/manifest.json`.
>
> Stato: `onboard` — pronto per il review della documentazione.
> Vuoi lanciare il review adesso?

---

## Fase 5 — Aggiornamento Manifest

### Quando aggiornare

Il manifest viene aggiornato:
1. **Prima di delegare** a una skill — per registrare l'inizio della transizione
2. **Al ritorno alla pipeline** — per rilevare il completamento della fase precedente

### Rilevamento automatico dello stato

Quando la pipeline viene invocata, oltre a leggere `stato_pipeline` dal manifest, verifica la presenza di artefatti per correggere eventuali disallineamenti:

| Artefatto trovato | Stato corretto |
|---|---|
| `plans/todo/<data>_<nome>/REVIEW_BR.md` esiste | almeno `review` |
| `plans/todo/<data>_<nome>/GAP_REPORT_BR.md` esiste | almeno `analyze` |
| `plans/todo/<data>_<nome>/PIANO_IMPLEMENTAZIONE_BR.md` esiste | almeno `approve` |
| `piano.approvato == true` nel manifest | almeno `approved` |
| `plans/in-progress/<data>_<nome>/PROGRESSO_BR.md` esiste | almeno `execute` |
| `plans/done/<data>_<nome>/` esiste | `done` |
| `BUG_REPORT_BR.md` esiste nella cartella del BR | debug attivo |

Per trovare la cartella del BR in `plans/`, cerca il pattern `plans/*/YYYY-*_<nome>/` dove `<nome>` corrisponde al `nome` nel manifest.

Se lo stato nel manifest e' indietro rispetto agli artefatti trovati, aggiorna silenziosamente il manifest e aggiungi una entry nella timeline:

```json
{
  "data": "<ISO-timestamp>",
  "attore": "sistema",
  "ruolo": "pipeline",
  "azione": "Stato corretto da '<vecchio>' a '<nuovo>' (rilevato da artefatti)",
  "stage": "<nuovo_stato>"
}
```

### Formato aggiornamento timeline

Ogni azione della pipeline aggiunge una entry alla timeline:

```json
{
  "data": "<ISO-timestamp>",
  "attore": "<nome utente o email>",
  "ruolo": "<TL/PM | Dev | pipeline>",
  "azione": "<descrizione azione>",
  "stage": "<stato_corrente o transizione>"
}
```

### Come scrivere il manifest

Usa il tool `Write` per riscrivere l'intero `manifest.json`. Non usare `Edit` — il JSON deve essere sempre valido e completo. Leggi il manifest corrente, modifica in memoria, riscrivi.

---

## Fase 6 — Transizioni di Stato Complete

Mappa completa delle transizioni:

```
onboard ──[br-reviewer completato]──→ review
review ──[br-clarify completato]──→ clarify
review ──[skip chiarimenti]──→ clarify (bypass)
clarify ──[br-analyzer completato]──→ approve
approve ──[utente approva piano]──→ approved
approved ──[br-executor avviato]──→ execute
execute ──[tutte le task completate E tutti i bug chiusi (o nessun bug)]──→ done
execute ──[BR aggiornato, br-updater completato]──→ execute (aggiornato)
```

Transizioni eccezionali:
- Da qualsiasi stato dopo `approve` → `update` → poi ritorna a `execute`
- `done` → nessuna transizione (stato terminale)
- `review` → direttamente a `analyze` (se non servono chiarimenti)

---

## Regole Fondamentali

1. **Mai reimplementare la logica** — la pipeline propone e delega, non esegue. Ogni fase e' gestita dalla skill dedicata.
2. **Sempre aggiornare il manifest** — ogni azione viene registrata nella timeline con timestamp, attore, ruolo e descrizione.
3. **Sempre chiedere conferma** — prima di ogni transizione di stato, mostra l'azione proposta e aspetta conferma.
4. **Rilevare lo stato dagli artefatti** — non fidarsi solo del `stato_pipeline`: verificare la presenza di REVIEW_BR.md, GAP_REPORT_BR.md, PIANO_IMPLEMENTAZIONE_BR.md, PROGRESSO_BR.md per correggere eventuali disallineamenti.
5. **Rispettare il ruolo** — TL/PM vede tutto e decide le transizioni; Dev vede solo le sue task e lavora.
6. **Unico punto di ingresso** — questa skill e' progettata per essere l'interfaccia primaria. L'utente non deve sapere quale skill invocare — la pipeline lo fa per lui.
7. **Non toccare le skill esistenti** — le 6 skill (br-reviewer, br-clarify, br-analyzer, br-executor, br-updater, br-progress-report) restano invariate e autonome.
