---
name: sdlc-progress-report
description: Genera o aggiorna un file Excel con il riepilogo completo delle task, progressi e avanzamenti per sviluppatore a partire dal piano e dal file di progresso di sdlc-analyzer/sdlc-executor. Supporta qualsiasi composizione di repository — i nomi e le sigle vengono letti dinamicamente dal piano. Usa questa skill quando l'utente dice "genera il report excel", "aggiorna l'excel", "stato avanzamento excel", "esporta il progresso", "report avanzamento", "excel dei progressi", "aggiorna il foglio", "com'è la situazione delle task", o qualsiasi variazione che implichi la necessità di un report Excel sullo stato di avanzamento delle task di un piano BR.
---

# SDLC Progress Report — Export Excel Avanzamento Task

Questa skill genera o aggiorna un file Excel con il riepilogo completo delle task, dei progressi per sviluppatore e dello stato di avanzamento complessivo, a partire dal piano e dal file di progresso generati da `sdlc-analyzer` / `sdlc-executor`.

---

## Risoluzione Path — deloitte-profiles

Tutte le operazioni su file BR avvengono nella repo `deloitte-profiles`, non nella repo del codice.

### Lettura `.br-local.json`

```bash
cat .br-local.json 2>/dev/null
```

Estrai `profiles_repo`, `profilo`, `developer`.

Il **base path** per gli artefatti BR e': `<profiles_repo>/<profilo>/plans/`

### Se `.br-local.json` non esiste

Ferma l'esecuzione e avvisa:

> `.br-local.json` non trovato. Devi prima eseguire `sdlc-profile-setup`.

### Sincronizzazione prima della lettura

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

### Commit e push dopo la scrittura

```bash
git -C "<profiles_repo>" add .
git -C "<profiles_repo>" commit -m "<messaggio>"
git -C "<profiles_repo>" push origin main --quiet
```

---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path (`profiles_repo`, `profilo`) e prima di eseguire qualsiasi altra fase, carica i due file di costituzione del progetto:

```bash
git -C "<profiles_repo>" pull origin main --quiet
cat "<profiles_repo>/<profilo>/constitution/CONST.json"
cat "<profiles_repo>/<profilo>/constitution/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| `.br-local.json` manca | "Esegui prima `/sdlc-profile-setup`" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il profilo `<nome>` non ha CONST.json. Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il profilo `<nome>` non ha PROFILE.json. Stato inconsistente — il profilo è incompleto. Ripristinare da git history o rifare il setup." | Stop |
| Entrambi mancano, esiste `profile.json` (legacy) | "Profilo in formato vecchio (pre-split CONST/PROFILE). Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per fare lo split automaticamente." | Stop |
| JSON malformed | Mostra errore di parse + path | Stop |

**Semantica d'uso:**

- **CONST** = vincoli inviolabili per ogni output generato. Ogni piano, task, fix, review, bug analysis che produci DEVE rispettare:
  - `inviolable_principles` (security/a11y/responsiveness/privacy)
  - `quality_standards` (coverage, error handling, logging, performance)
  - `code_style` (limiti dimensionali, no magic numbers)
  - `git_workflow` (branch/commit pattern)
  - `architectural_patterns` (layering, response envelope, AAA, validazione boundary)
- **PROFILE** = "lingua" del progetto. Usa i dettagli (tech stack, repositories con sigle, dominio, glossario, design system) per nominare le task con le sigle corrette, proporre snippet con il framework/versione giusti, usare il vocabolario di dominio, e riferire componenti del design system.

Entrambi i file restano disponibili come contesto per tutta la durata della skill.

---

## Fase 1 — Individuazione File Sorgente

### Ricerca automatica

Cerca cartelle BR nella struttura `plans/` centralizzata in `deloitte-profiles`, in ordine di priorita':

```bash
git -C "<profiles_repo>" pull origin main --quiet
ls -d "<profiles_repo>/<profilo>/plans/in-progress"/*/ "<profiles_repo>/<profilo>/plans/todo"/*/ "<profiles_repo>/<profilo>/plans/done"/*/ 2>/dev/null
```

Serve trovare:
- **TASKS** (`TASKS.md`) — obbligatorio
- **File di Progresso** (`PROGRESS.md`) — opzionale, se non esiste le task partono tutte da 0%
- **PLAN** (`PLAN.md`) — opzionale, usato per arricchire le descrizioni

**Se trovi cartelle BR**, proponile:

> Ho trovato:
> - `<profiles_repo>/<profilo>/plans/in-progress/2026-04-28_booking-v2/`
>   - `TASKS.md`
>   - `PROGRESS.md`
>
> Uso questa cartella per generare l'Excel?

Se non trovi nulla, chiedi i path manualmente.

### Verifica Excel esistente

Cerca nella stessa cartella del BR se esiste gia' un file Excel:

```bash
ls "<profiles_repo>/<profilo>/plans/in-progress"/*/PROGRESS.xlsx "<profiles_repo>/<profilo>/plans/todo"/*/PROGRESS.xlsx "<profiles_repo>/<profilo>/plans/done"/*/PROGRESS.xlsx 2>/dev/null
```

- **Se esiste** → modalità aggiornamento (solo i dati cambiano, struttura preservata)
- **Se non esiste** → modalità creazione da zero

Comunica la modalità all'utente:

> [Excel trovato — aggiorno `PROGRESS.xlsx` con i progressi attuali.]

oppure

> [Nessun Excel trovato — ne creo uno nuovo.]

---

## Fase 2 — Estrazione Dati

### Lettura progresso

Sincronizza la repo profili prima di leggere:

```bash
git -C "<profiles_repo>" pull origin main --quiet
```

Leggi il PROGRESS.md dalla cartella del BR in `<profiles_repo>/<profilo>/plans/<stato>/<data>_<nome>/PROGRESS.md`. Il file e' sempre aggiornato dopo il pull perche' tutti gli sviluppatori scrivono nella repo centralizzata.

### Estrazione campi

Dal PROGRESS.md e dal piano, estrai per ogni task:

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
| Branch | PROGRESS.md — colonna Branch |
| Progresso % | PROGRESS.md — colonna Progresso |
| Stato | PROGRESS.md — colonna Stato (Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa) |
| Note | PROGRESS.md — colonna Note |

Se il file di progresso non esiste, imposta progresso a 0% e stato a "Da iniziare" per tutte le task.

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

Salva nella stessa cartella del BR all'interno della repo centralizzata:
- **Path**: `<profiles_repo>/<profilo>/plans/<stato>/<YYYY-MM-DD>_<nome>/PROGRESS.xlsx`
- **Aggiornamento**: sovrascrivi il file esistente

### Modalità aggiornamento

Se il file esiste già, non ricrearlo da zero. Aggiorna solo:
- I valori di progresso e stato (dal file di progresso aggiornato)
- Eventuali task nuove (aggiunte da `sdlc-updater`)
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

### Commit e push su deloitte-profiles

Dopo aver salvato l'Excel, fai commit e push nella repo centralizzata:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[sdlc-progress-report] <nome>: aggiornato Excel avanzamento"
git -C "<profiles_repo>" push origin main --quiet
```

### Comunicazione finale

> Excel [creato / aggiornato]: `<profiles_repo>/<profilo>/plans/in-progress/<YYYY-MM-DD>_<nome>/PROGRESS.xlsx`
>
> Riepilogo:
> - Task totali: N (X completate, Y in corso, Z da iniziare)
> - Progresso complessivo: xx%
> - [eventuali task bloccate da segnalare]

---

## Dipendenze

- **`openpyxl`** — libreria Python per generazione Excel (`pip install openpyxl`)
