---
name: br-progress-report
description: Genera o aggiorna un file Excel con il riepilogo completo delle task, progressi e avanzamenti per sviluppatore a partire dal piano e dal file di progresso di br-analyzer/br-executor. Supporta qualsiasi composizione di repository — i nomi e le sigle vengono letti dinamicamente dal piano. Usa questa skill quando l'utente dice "genera il report excel", "aggiorna l'excel", "stato avanzamento excel", "esporta il progresso", "report avanzamento", "excel dei progressi", "aggiorna il foglio", "com'è la situazione delle task", o qualsiasi variazione che implichi la necessità di un report Excel sullo stato di avanzamento delle task di un piano BR.
---

# BR Progress Report — Export Excel Avanzamento Task

Questa skill genera o aggiorna un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo, a partire dal piano e dal file di progresso generati da `br-analyzer` / `br-executor`.

---

## Fase 1 — Individuazione File Sorgente

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

### Verifica Excel esistente

Cerca nella stessa cartella del BR se esiste gia' un file Excel:

```bash
# Se struttura a cartelle
ls plans/in-progress/*/AVANZAMENTO_BR.xlsx plans/todo/*/AVANZAMENTO_BR.xlsx plans/done/*/AVANZAMENTO_BR.xlsx 2>/dev/null

# Retrocompatibilita' flat
ls plans/in-progress/AVANZAMENTO_BR_*.xlsx plans/todo/AVANZAMENTO_BR_*.xlsx plans/done/AVANZAMENTO_BR_*.xlsx 2>/dev/null
```

- **Se esiste** → modalità aggiornamento (solo i dati cambiano, struttura preservata)
- **Se non esiste** → modalità creazione da zero

Comunica la modalità all'utente:

> [Excel trovato — aggiorno `AVANZAMENTO_BR_2026-04-24.xlsx` con i progressi attuali.]

oppure

> [Nessun Excel trovato — ne creo uno nuovo.]

---

## Fase 2 — Estrazione Dati

### Lettura progresso aggregata (cross-branch)

Prima di estrarre i dati, esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task. Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch — senza aggregazione l'Excel mostrerebbe solo il progresso locale.

1. `git fetch origin` per sincronizzare i branch remoti

2. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre:
   - Gli ID di tutte le task (T-001, T-003, T-005, ...)
   - Se il piano ha una colonna **Branch** nel backlog: estrai i nomi branch di ogni task
   - Il nome del BR dalla cartella (es. `2026-05-04_monitoring` → `monitoring`)

3. **Trova i branch remoti da controllare:**
   - **Se il piano ha colonna Branch**: usa direttamente i nomi branch elencati nel piano. Per ogni branch con valore diverso da `—`, verifica che esista come remoto:
     ```bash
     git branch -r | grep "<branch-name>"
     ```
   - **Se il piano NON ha colonna Branch** (retrocompatibilita' con piani pre-esistenti): cerca tutti i branch remoti che contengono il nome del BR:
     ```bash
     git branch -r | grep -i "feature/<nome-br>"
     ```

4. Per ogni branch trovato, prova a leggere il PROGRESSO da 3 percorsi possibili (il file puo' essere in posizioni diverse a seconda dello stato):
   ```bash
   git show origin/<branch>:plans/in-progress/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/todo/<cartella-br>/PROGRESSO_BR.md
   git show origin/<branch>:plans/done/<cartella-br>/PROGRESSO_BR.md
   ```
   Usa il primo che funziona. Se nessuno funziona, skip quel branch.

5. Leggi anche il PROGRESSO dal branch base del piano (con gli stessi 3 percorsi). Se non esiste su nessun percorso, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

6. Aggrega per task con la regola **"highest progress wins"**:
   - Per ogni task, confronta le versioni da tutti i branch (incluso il baseline)
   - Se una versione mostra "Completata" (100%), vince sempre
   - Altrimenti, prendi la versione con il progresso % piu' alto
   - Se due versioni hanno lo stesso %, prendi quella con lo stato piu' avanzato (In corso > Da iniziare)

7. Ricalcola le metriche di riepilogo dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning all'utente.

### Estrazione campi

Dalla vista aggregata e dal piano, estrai per ogni task:

| Campo | Fonte |
|---|---|
| ID | Piano — colonna ID |
| Attivita' | Piano — colonna Attivita' |
| Descrizione | Piano — colonna Descrizione (testo completo) |
| Owner | Piano — colonna Owner |
| Area | Piano — colonna Area (BE/FE) |
| Priorita' | Piano — colonna Priorita' (P0/P1/P2) |
| Wave | Piano — sezione Ordine di esecuzione |
| Dipendenze | Piano — colonna Dipendenze |
| Effort stimato | Piano — colonna Effort |
| Branch | Vista aggregata — colonna Branch |
| Progresso % | Vista aggregata — colonna Progresso |
| Stato | Vista aggregata — colonna Stato (Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa) |
| Note | Vista aggregata — colonna Note |

Se il file di progresso non esiste e l'aggregazione non trova nessun branch remoto, imposta progresso a 0% e stato a "Da iniziare" per tutte le task.

---

## Fase 3 — Generazione / Aggiornamento Excel

Usa Python con `openpyxl` per generare il file. L'Excel deve contenere 3 fogli:

### Foglio 1 — "Task"

Tabella principale con tutte le task:

| Colonna | Larghezza | Contenuto |
|---|---|---|
| A — ID | 10 | ID task (es. T-001) |
| B — Stream | 18 | Stream funzionale (es. stream-booking) |
| C — Attività | 30 | Nome della task |
| D — Descrizione | 60 | Descrizione completa dal piano |
| E — Owner | 18 | Sviluppatore assegnato |
| F — Area | 8 | Sigla/e delle repo coinvolte (es. BE, FE, BE+FE, GW, ecc.) |
| G — Priorità | 10 | P0 / P1 / P2 |
| H — Wave | 10 | Wave 0 / 1 / 2 / ... |
| I — Dipendenze | 15 | ID task dipendenze |
| J — Effort | 10 | Giorni stimati |
| K — Branch | 25 | Nome branch |
| L — Progresso | 12 | Percentuale (0-100%) |
| M — Stato | 15 | Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa |
| N — Note | 40 | Note dal progresso |

Formattazione:
- Header in grassetto con sfondo grigio scuro e testo bianco
- Colonna K (Progresso) con formattazione condizionale:
  - 0% → sfondo rosso chiaro
  - 1-49% → sfondo arancione chiaro
  - 50-99% → sfondo giallo chiaro
  - 100% → sfondo verde chiaro
- Colonna L (Stato) con formattazione condizionale:
  - "Completata" → testo verde scuro, sfondo verde chiaro
  - "In corso" → testo blu scuro, sfondo blu chiaro
  - "Bloccata" → testo rosso scuro, sfondo rosso chiaro
  - "Annullata" / "Sospesa" → testo grigio, sfondo grigio chiaro
  - "Da iniziare" → nessuna formattazione speciale
- Filtri attivi su tutte le colonne
- Righe alternate con sfondo leggermente diverso per leggibilità
- Testo della colonna Descrizione con "wrap text" attivo

### Foglio 2 — "Per Sviluppatore"

Riepilogo per ogni sviluppatore:

| Colonna | Contenuto |
|---|---|
| A — Sviluppatore | Nome/ID |
| B — Ruolo | Area/sigle repo (come definite nel piano) |
| C — Seniority | Junior / Mid / Senior |
| D — Task totali | Conteggio |
| E — Completate | Conteggio |
| F — In corso | Conteggio |
| G — Da iniziare | Conteggio |
| H — Bloccate | Conteggio |
| I — Progresso medio | Media % delle sue task |
| J — Effort totale | Somma giorni stimati |
| K — Effort completato | Somma giorni delle task completate |

Stessa formattazione header del Foglio 1.
In fondo alla tabella, una riga "TOTALE" con le somme.

### Foglio 3 — "Riepilogo"

Dashboard complessiva con le metriche chiave:

```
Progetto: [nome BR]
Data generazione: [data]
Ultimo aggiornamento progresso: [data dal file progresso]
Dati aggregati da: [N] branch remoti
Ultimo fetch: [data e ora del git fetch]

STATO COMPLESSIVO
─────────────────
Task totali:        N
Completate:         N  (xx%)
In corso:           N  (xx%)
Da iniziare:        N  (xx%)
Bloccate:           N  (xx%)
Annullate/Sospese:  N  (xx%)

Progresso complessivo: xx%

EFFORT
──────
Effort totale stimato:    N gg/uomo
Effort completato:        N gg/uomo  (xx%)
Effort rimanente:         N gg/uomo

PER WAVE
────────
Wave 0: xx% completata (N/M task)
Wave 1: xx% completata (N/M task)
Wave 2: xx% completata (N/M task)
...
```

Formatta questa sezione come testo leggibile, non come tabella. Usa merge di celle per i titoli.

---

## Fase 4 — Salvataggio e Comunicazione

### Nome e posizione file

Salva nella stessa cartella del BR:
- **Se struttura a cartelle**: `plans/<stato>/<YYYY-MM-DD>_<nome>/AVANZAMENTO_BR.xlsx`
- **Se flat (retrocompatibilita')**: `plans/<stato>/AVANZAMENTO_BR_<YYYY-MM-DD>.xlsx`
- **Aggiornamento**: sovrascrivi il file esistente

### Modalità aggiornamento

Se il file esiste già, non ricrearlo da zero. Aggiorna solo:
- I valori di progresso e stato (dal file di progresso aggiornato)
- Eventuali task nuove (aggiunte da `br-updater`)
- Eventuali task annullate/sospese
- Il foglio "Per Sviluppatore" e "Riepilogo" ricalcolati
- Preserva eventuali note manuali aggiunte dall'utente nelle celle Note

### Script Python

Genera ed esegui uno script Python con `openpyxl`. Se `openpyxl` non è installato:

```bash
pip install openpyxl
```

Lo script deve:
1. Parsare il piano MD per estrarre le task
2. Parsare il progresso MD per estrarre stati e percentuali
3. Se l'Excel esiste, leggerlo e preservare le note manuali
4. Generare/aggiornare i 3 fogli
5. Applicare formattazione e formattazione condizionale
6. Salvare il file

### Comunicazione finale

> Excel [creato / aggiornato]: `plans/in-progress/AVANZAMENTO_BR_2026-04-24.xlsx`
>
> Riepilogo:
> - Task totali: N (X completate, Y in corso, Z da iniziare)
> - Progresso complessivo: xx%
> - [eventuali task bloccate da segnalare]

---

## Dipendenze

- **`openpyxl`** — libreria Python per generazione Excel (`pip install openpyxl`)
