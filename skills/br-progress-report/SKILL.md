---
name: br-progress-report
description: Genera o aggiorna un file Excel con il riepilogo completo delle task, progressi e avanzamenti per sviluppatore a partire dal piano e dal file di progresso di br-analyzer/br-executor. Usa questa skill quando l'utente dice "genera il report excel", "aggiorna l'excel", "stato avanzamento excel", "esporta il progresso", "report avanzamento", "excel dei progressi", "aggiorna il foglio", "com'è la situazione delle task", o qualsiasi variazione che implichi la necessità di un report Excel sullo stato di avanzamento delle task di un piano BR.
---

# BR Progress Report — Export Excel Avanzamento Task

Questa skill genera o aggiorna un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo, a partire dal piano e dal file di progresso generati da `br-analyzer` / `br-executor`.

---

## Fase 1 — Individuazione File Sorgente

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

### Verifica Excel esistente

Cerca nella stessa cartella del piano se esiste già un file Excel:

```bash
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

Leggi il piano e il file di progresso. Estrai per ogni task:

| Campo | Fonte |
|---|---|
| ID | Piano — colonna ID |
| Attività | Piano — colonna Attività |
| Descrizione | Piano — colonna Descrizione (testo completo) |
| Owner | Piano — colonna Owner |
| Area | Piano — colonna Area (BE/FE) |
| Priorità | Piano — colonna Priorità (P0/P1/P2) |
| Wave | Piano — sezione Ordine di esecuzione |
| Dipendenze | Piano — colonna Dipendenze |
| Effort stimato | Piano — colonna Effort |
| Branch | Progresso — colonna Branch (se presente) |
| Progresso % | Progresso — colonna Progresso |
| Stato | Progresso — colonna Stato (Da iniziare / In corso / Completata / Mergiata / Bloccata / Annullata / Sospesa) |
| Note | Progresso — colonna Note |

Se il file di progresso non esiste, imposta progresso a 0% e stato a "Da iniziare" per tutte le task.

---

## Fase 3 — Generazione / Aggiornamento Excel

Usa Python con `openpyxl` per generare il file. L'Excel deve contenere 3 fogli:

### Foglio 1 — "Task"

Tabella principale con tutte le task:

| Colonna | Larghezza | Contenuto |
|---|---|---|
| A — ID | 10 | ID task (es. T-001) |
| B — Attività | 30 | Nome della task |
| C — Descrizione | 60 | Descrizione completa dal piano |
| D — Owner | 18 | Sviluppatore assegnato |
| E — Area | 8 | BE / FE / BE+FE |
| F — Priorità | 10 | P0 / P1 / P2 |
| G — Wave | 10 | Wave 0 / 1 / 2 / ... |
| H — Dipendenze | 15 | ID task dipendenze |
| I — Effort | 10 | Giorni stimati |
| J — Branch | 25 | Nome branch |
| K — Progresso | 12 | Percentuale (0-100%) |
| L — Stato | 15 | Da iniziare / In corso / Completata / Mergiata / Bloccata / Annullata / Sospesa |
| M — Note | 40 | Note dal progresso |

Formattazione:
- Header in grassetto con sfondo grigio scuro e testo bianco
- Colonna K (Progresso) con formattazione condizionale:
  - 0% → sfondo rosso chiaro
  - 1-49% → sfondo arancione chiaro
  - 50-99% → sfondo giallo chiaro
  - 100% → sfondo verde chiaro
- Colonna L (Stato) con formattazione condizionale:
  - "Completata" → testo verde scuro, sfondo verde chiaro
  - "Mergiata" → testo verde scuro, sfondo verde (più intenso di Completata, per distinguere)
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
| B — Ruolo | BE / FE / Fullstack |
| C — Seniority | Junior / Mid / Senior |
| D — Task totali | Conteggio |
| E — Completate | Conteggio (include Completata + Mergiata) |
| F — Mergiate | Conteggio (solo Mergiata) |
| G — In corso | Conteggio |
| H — Da iniziare | Conteggio |
| I — Bloccate | Conteggio |
| J — Progresso medio | Media % delle sue task |
| K — Effort totale | Somma giorni stimati |
| L — Effort completato | Somma giorni delle task completate/mergiate |

Stessa formattazione header del Foglio 1.
In fondo alla tabella, una riga "TOTALE" con le somme.

### Foglio 3 — "Riepilogo"

Dashboard complessiva con le metriche chiave:

```
Progetto: [nome BR]
Data generazione: [data]
Ultimo aggiornamento progresso: [data dal file progresso]

STATO COMPLESSIVO
─────────────────
Task totali:        N
Completate:         N  (xx%)  [di cui Mergiate: N]
In corso:           N  (xx%)
Da iniziare:        N  (xx%)
Bloccate:           N  (xx%)
Annullate/Sospese:  N  (xx%)

Progresso complessivo: xx%

EFFORT
──────
Effort totale stimato:    N gg/uomo
Effort completato:        N gg/uomo  (xx%)  [completate + mergiate]
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

Salva nella stessa cartella del piano:
- **Creazione**: `AVANZAMENTO_BR_<YYYY-MM-DD>.xlsx`
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
> - Task totali: N (X completate di cui M mergiate, Y in corso, Z da iniziare)
> - Progresso complessivo: xx%
> - [eventuali task bloccate da segnalare]

---

## Dipendenze

- **`openpyxl`** — libreria Python per generazione Excel (`pip install openpyxl`)
