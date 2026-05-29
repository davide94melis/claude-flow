---
name: sdlc-estimator
description: Stima il team necessario per completare un Piano (ex BR, derivato da un'AFU) entro una deadline, con simulazioni what-if su team, deadline, scope e rischio. Due modalita' — rough (pre-analisi, dalla documentazione AFU) e dettagliata (post-analisi, dal TASKS del Piano). Produce scenari ottimistico/realistico/pessimistico con timeline, bottleneck, allocazione team e suggerimenti scope cut. Genera report MD + Excel. Usa questa skill quando l'utente dice "stima il br", "stima il Piano", "stima l'AFU", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", o qualsiasi variazione che implichi la necessita' di stimare l'effort o il team per un BR / AFU / Piano.
---

# SDLC Estimator — Stima Team e Simulazioni What-If

Questa skill stima quanti sviluppatori servono per completare un Piano entro una deadline, con simulazioni interattive per variare team, deadline e scope. Produce 3 scenari (ottimistico/realistico/pessimistico) e report esportabili.

Due modalita':
- **Rough** (pre-analisi) — dalla documentazione AFU, stima approssimativa (±30-40%)
- **Dettagliata** (post-analisi) — dal TASKS, stima precisa (±10-15%)

---

## Risoluzione Path (modalita' duale: standalone | legacy)

Tutte le operazioni su file plan avvengono nella **project_repo** (modalita' standalone, una repo per progetto) o nella repo `deloitte-profiles` (modalita' legacy), **non** nella repo del codice applicativo. Il codice del progetto continua a essere scritto nelle repo del progetto.

### Lettura del file di configurazione locale (`.sdlc-local.json` con fallback `.br-local.json`)

**Lettura compatibile**: il file di configurazione locale può chiamarsi `.sdlc-local.json` (nuovo nome, raccomandato) oppure `.br-local.json` (nome legacy, ancora supportato). Cerca PRIMA `.sdlc-local.json`; se non esiste, fa fallback a `.br-local.json`. Se nessuno dei due esiste, ferma e chiedi all'utente di eseguire `/sdlc-profile-setup`.

Se trovi solo `.br-local.json` (profilo legacy), emetti questo warning soft prima di procedere:

> Nota: profilo legacy `.br-local.json` rilevato. Funziona, ma il nuovo nome è `.sdlc-local.json`. Verrà migrato automaticamente al prossimo `/sdlc-profile-setup`, oppure puoi rinominarlo manualmente quando vuoi.

I comandi `bash` seguenti sono scritti referenziando `.br-local.json` per chiarezza storica — applica equivalentemente la stessa logica al file effettivamente trovato (sia `.sdlc-local.json` che `.br-local.json`).

All'avvio, leggi il file (priorità `.sdlc-local.json`, fallback `.br-local.json`) dalla root della repo corrente:

```bash
# Esempio con .br-local.json — equivalente per .sdlc-local.json
cat .br-local.json 2>/dev/null
```

La presenza del campo `project_repo` o `profiles_repo` discrimina la modalita':

```bash
if grep -q '"project_repo"' .br-local.json 2>/dev/null; then
  MODE="standalone"
  PROJECT_REPO=$(grep -oP '"project_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROJECT_NAME=$(grep -oP '"project_name"\s*:\s*"\K[^"]+' .br-local.json)
  BASE_PATH="$PROJECT_REPO/plans"
  CONST_PATH="$PROJECT_REPO/constitution"
  DATASET_PATH="$PROJECT_REPO/dataset"        # solo standalone (popolato da Solaria-side)
  GIT_REPO_PATH="$PROJECT_REPO"
elif grep -q '"profiles_repo"' .br-local.json 2>/dev/null; then
  MODE="legacy"
  PROFILES_REPO=$(grep -oP '"profiles_repo"\s*:\s*"\K[^"]+' .br-local.json)
  PROFILO=$(grep -oP '"profilo"\s*:\s*"\K[^"]+' .br-local.json)
  PROJECT_NAME="$PROFILO"
  BASE_PATH="$PROFILES_REPO/$PROFILO/plans"
  CONST_PATH="$PROFILES_REPO/$PROFILO/constitution"
  DATASET_PATH=""                              # non esiste in legacy
  GIT_REPO_PATH="$PROFILES_REPO"
fi
```

| Modalita' | `BASE_PATH` | `CONST_PATH` | Stati supportati |
|---|---|---|---|
| Standalone | `$PROJECT_REPO/plans` | `$PROJECT_REPO/constitution` | `draft`, `todo`, `in-progress`, `done` |
| Legacy | `$PROFILES_REPO/$PROFILO/plans` | `$PROFILES_REPO/$PROFILO/constitution` | `todo`, `in-progress`, `done` |

> **Nota**: `plans/draft/` esiste solo in modalita' standalone — area dove Solaria authora l'AFU prima dell'handoff (Fase 1c). Le skill SDLC ignorano `draft/` (e' Solaria-side) tranne `sdlc-reviewer` e `sdlc-clarify` quando esplicitamente invocate su un draft.

### Se né `.sdlc-local.json` né `.br-local.json` esistono

Ferma l'esecuzione e avvisa:

> Nessun file di configurazione locale trovato (`.sdlc-local.json` né `.br-local.json` legacy). Devi prima eseguire `/sdlc-profile-setup`, che ti chiedera' se vuoi configurare in **modalita' standalone** (raccomandato per nuovi progetti, una repo per progetto con cartella `dataset/` Solaria-side) o **modalita' legacy** (progetti gia' esistenti in `deloitte-profiles`).

### Sincronizzazione prima della lettura

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
```

### Commit e push dopo la scrittura

```bash
git -C "$GIT_REPO_PATH" add .
git -C "$GIT_REPO_PATH" commit -m "<messaggio>"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Caricamento contesto progetto (CONST + PROFILE)

Dopo aver risolto i path con l'helper di detection sopra, prima di eseguire qualsiasi altra fase carica i due file di costituzione del progetto:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
cat "$CONST_PATH/CONST.json"
cat "$CONST_PATH/PROFILE.json"
```

**Errori di loading (uniformi per tutte le skill SDLC):**

| Caso | Messaggio all'utente | Azione |
|---|---|---|
| Né `.sdlc-local.json` né `.br-local.json` (legacy) presenti | "Esegui prima `/sdlc-profile-setup` scegliendo modalita' standalone o legacy" | Stop |
| `CONST.json` manca, `PROFILE.json` esiste | "Il progetto `<PROJECT_NAME>` non ha CONST.json. Eseguire `python claude-flow/scripts/migrate-profile-split.py --apply` per generarlo dal template, oppure crearlo a mano partendo da `const-schema.json`." | Stop |
| `PROFILE.json` manca, `CONST.json` esiste | "Il progetto `<PROJECT_NAME>` non ha PROFILE.json. Stato inconsistente — il profilo e' incompleto. Ripristinare da git history o rifare il setup." | Stop |
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

## Rilevamento Contesto

La skill cerca il TASKS in `$BASE_PATH/`.

## Rilevamento Modalita'

- **Se esiste un TASKS** (`TASKS.md`) → modalita' **dettagliata**
- **Se non esiste un TASKS ma ci sono documenti AFU** → modalita' **rough**

La skill comunica la modalita' rilevata:

> Ho rilevato che il Piano **<nome>** ha un TASKS.
> Uso la modalita' **dettagliata** (precisione ±10-15%).

oppure:

> Il Piano **<nome>** non ha ancora un TASKS. Uso la modalita' **rough** dalla documentazione (precisione ±30-40%).

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — Piano di riferimento

Cerca i Piani attivi:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
ls -d "$BASE_PATH/todo"/*/ "$BASE_PATH/in-progress"/*/ 2>/dev/null
```

Se ne trovi uno, proponilo. Se piu' di uno, chiedi quale. Se nessuno, avvisa che serve almeno la documentazione AFU.

### Domanda 2 — Deadline target

> Entro quando deve essere completato il Piano?
>
> Dammi una data (es. "30 maggio 2026", "fine giugno", "tra 3 settimane")

Converti in data ISO (YYYY-MM-DD). Se la data e' vaga (es. "fine giugno"), usa l'ultimo giorno lavorativo del periodo.

### Domanda 3 — Team

Tenta di proporre il team dai dati disponibili:

1. Se il TASKS ha gia' owner assegnati → proponi quelli con seniority dedotta dal ruolo nel TASKS
2. Se `.br-local.json` ha `developer` → includilo nella proposta
3. Altrimenti chiedi:

> Definisci il team. Per ogni sviluppatore:
> - **Nome**
> - **Seniority**: senior / mid / junior
> - **Area**: BE / FE / BE+FE
> - **Disponibilita'**: percentuale di tempo dedicato a questo Piano (default 100%)
>
> Esempio:
> - Marco, senior, BE, 100%
> - Luca, mid, FE, 80%
> - Anna, junior, BE+FE, 100%

### Domanda 4 — Parametri

> Vuoi usare i parametri di default o personalizzarli?
> 1. **Default** — effort standard (Bassa=0.5gg, Media=1gg, Alta=2gg, Molto Alta=3.5gg)
> 2. **Personalizza** — modifica effort, moltiplicatori seniority o rischio

Se l'utente sceglie personalizza, mostra i default in tabella e permetti di cambiare i valori.

---

## Fase 2 — Esecuzione Stima

### Modalita' Rough

1. Lancia in **parallelo**:
   - **Analista AFU** (`sdlc-estimation-analyst`): leggi le sue istruzioni da `~/.claude/agents/sdlc-estimation-analyst.md`. Passagli la documentazione AFU e il profilo progetto (se disponibile da `.sdlc-local.json`/`.br-local.json` legacy → `profiles_repo`/`profilo`).
   - **Storico** (`sdlc-estimation-historian`): leggi le sue istruzioni da `~/.claude/agents/sdlc-estimation-historian.md`. Passagli il path a `$BASE_PATH/done/` e i parametri di default.

2. Ricevi i risultati:
   - Dall'analista: tabella funzionalita' con task stimate, complessita', rischio, area
   - Dallo storico: fattore di calibrazione (o 1.0x se nessun dato)

3. Mostra un riepilogo dell'analisi all'utente:

> ## Analisi completata
>
> **Funzionalita' rilevate:** N
> **Task stimate:** M
> **Calibrazione storica:** Xx (da K Piani precedenti)
>
> [tabella funzionalita' dall'analista]
>
> Procedo con il calcolo degli scenari?

4. Dopo conferma, lancia lo **Scenarista** (`sdlc-estimation-scenario`): leggi le sue istruzioni da `~/.claude/agents/sdlc-estimation-scenario.md`. Passagli le task stimate, il team, la deadline, il fattore di calibrazione e i parametri.

### Modalita' Dettagliata

1. Leggi il TASKS (`TASKS.md`). Per ogni task, estrai: ID, nome, complessita', area, wave, dipendenze, owner.

2. Lancia lo **Storico** come sopra per il fattore di calibrazione.

3. Lancia lo **Scenarista** con le task reali, il team, la deadline, il fattore di calibrazione e i parametri.

---

## Fase 3 — Presentazione Scenari

Presenta i 3 scenari (ottimistico, realistico, pessimistico) ricevuti dallo scenarista.

Per ogni scenario mostra:
- Metriche chiave (effort, durata, data fine, delta dalla deadline)
- Bottleneck identificati
- Timeline per wave (se disponibile)
- Allocazione team

Evidenzia se lo scenario rientra nella deadline:

> **Scenario Realistico:** Data fine 2026-06-02 — **FUORI DEADLINE** (+2 giorni)
> **Scenario Ottimistico:** Data fine 2026-05-28 — **DENTRO DEADLINE** (-2 giorni)

---

## Fase 4 — Ciclo What-If

Dopo la presentazione dei scenari, proponi le simulazioni:

> Vuoi simulare uno scenario diverso?
> 1. **Aggiungi un dev** — dimmi nome, seniority, area, disponibilita'
> 2. **Rimuovi un dev** — scegli dalla lista
> 3. **Cambia deadline** — nuova data target
> 4. **Taglia scope** — ti mostro le funzionalita' tagliabili con il risparmio stimato
> 5. **Cambia parametri** — effort per complessita', moltiplicatori seniority o rischio
> 6. **Salva e genera report** — salva lo scenario scelto

### Per ogni what-if (opzioni 1-5):

1. Modifica i parametri in base alla scelta dell'utente
2. Re-invoca lo **Scenarista** con i parametri aggiornati (per opzione 4, aggiungi `scope_cutting: true`)
3. Presenta il delta rispetto allo scenario precedente:

> **Delta rispetto allo scenario precedente:**
> - Durata: 14gg → 10gg (-4gg)
> - Data fine: 2026-06-02 → 2026-05-28 (DENTRO DEADLINE)
> - Bottleneck BE risolto: 2 dev senior BE ora
> - Utilizzo team: 76% → 68%

4. Riproponi il menu what-if

Il ciclo continua finche' l'utente non sceglie "Salva e genera report".

### Scope cutting (opzione 4):

Lo scenarista produce la tabella di funzionalita' tagliabili. Mostrala all'utente:

> ## Funzionalita' tagliabili
>
> | # | Funzionalita' | Task | Risparmio | Impatto | Raccomandazione |
> |---|---|---|---|---|---|
> | 1 | Export PDF | T-008, T-009 | 4.5gg | Basso | Tagliabile |
> | 2 | Notifiche email | T-014, T-015, T-016 | 6.5gg | Medio | Differibile |
>
> Tagliando #1 + #3: risparmi 7.5 giorni, rientri nella deadline.
>
> Quali vuoi tagliare? (es. "1 e 3", oppure "nessuno")

Se l'utente sceglie dei tagli, rimuovi le task corrispondenti e re-invoca lo scenarista.

---

## Fase 5 — Generazione Report

Quando l'utente sceglie "Salva e genera report":

### ESTIMATE.md

Scrivi il file nella cartella del Piano:
`$BASE_PATH/todo/<data>_<nome>/ESTIMATE.md` (o `in-progress/` se il Piano è già in lavorazione)

Struttura:

```markdown
# Stima Piano — <nome>

Data stima: <data odierna>
Modalita': <rough|dettagliata>
Deadline target: <data>

## Team

| Dev | Seniority | Area | Disponibilita' |
|---|---|---|---|
| <nome> | <seniority> | <area> | <disponibilita>% |

## Scenario Selezionato: <nome scenario>

[metriche, timeline, allocazione, bottleneck dallo scenarista]

## Scenari a Confronto

| Metrica | Ottimistico | Realistico | Pessimistico |
|---|---|---|---|
| Effort totale | Xgg/p | Ygg/p | Zgg/p |
| Durata | Xgg | Ygg | Zgg |
| Data fine | DD/MM | DD/MM | DD/MM |
| Dentro deadline? | Si/No | Si/No | Si/No |
| Utilizzo team | X% | Y% | Z% |

## Scope Escluso

(presente solo se il TL/PM ha tagliato scope)

| Funzionalita' | Risparmio | Motivo esclusione |
|---|---|---|
| <nome> | Xgg | <motivo> |

## Parametri Utilizzati

### Effort per complessita'
| Complessita' | Giorni/persona |
|---|---|
| Bassa | 0.5 |
| Media | 1.0 |
| Alta | 2.0 |
| Molto Alta | 3.5 |

### Moltiplicatori seniority
| Seniority | Moltiplicatore |
|---|---|
| Senior | 1.0x |
| Mid | 1.3x |
| Junior | 1.8x |

### Calibrazione storica
Fattore: Xx (da N Piani precedenti)

## Storico di Riferimento

(presente solo se ci sono dati storici)

[tabella Piani passati dallo storico]
```

### ESTIMATE.xlsx

Genera con Python + openpyxl un file Excel con 4 fogli:

**Foglio 1 — Scenari:**
- Colonne: Metrica | Ottimistico | Realistico | Pessimistico
- Righe: effort totale, durata, data fine, delta deadline, utilizzo team
- Colora in verde le celle "DENTRO DEADLINE", in rosso le "FUORI DEADLINE"

**Foglio 2 — Timeline:**
- Riga 1: intestazioni con date (un giorno per colonna, solo lavorativi)
- Righe successive: una riga per task
- Celle colorate con il colore del dev assegnato per i giorni in cui lavora sulla task
- Bottleneck evidenziati con sfondo rosso
- Usare colori distinti per dev (stesso schema di sdlc-progress-report se disponibile)

**Foglio 3 — Team:**
- Tabella: Dev | Seniority | Area | Task assegnate | Giorni occupato | Giorni libero | Utilizzo
- Barra colorata proporzionale all'utilizzo

**Foglio 4 — Parametri:**
- Tutte le tabelle dei parametri usati
- Celle editabili (non protette) per ricalcolo manuale esterno

Salva il file nella stessa cartella del ESTIMATE.md.

### Commit

Dopo aver scritto entrambi i file:

```bash
git -C "$GIT_REPO_PATH" add "<profilo>/plans/"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-estimator] <piano-name>: stima team (<modalita'>)"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

---

## Regole Fondamentali

1. **Mai procedere senza conferma** — tra una fase e l'altra, aspetta l'utente
2. **Il sottoagente analizza, la skill orchestra** — non stimare direttamente, usa i sottoagenti
3. **Delta espliciti** — ogni what-if mostra il confronto col precedente
4. **Parametri trasparenti** — mostra sempre come il numero e' calcolato
5. **Fallback senza dati** — funziona anche senza storico e senza profilo
6. **Scope cutting con cascata** — il risparmio tiene conto delle dipendenze

---

## Dipendenze

| Dipendenza | Usata per | Installazione |
|---|---|---|
| `openpyxl` (Python) | Generazione Excel | `pip install openpyxl` |
| Agente `sdlc-estimation-analyst` | Stima rough | `~/.claude/agents/` |
| Agente `sdlc-estimation-historian` | Calibrazione storica | `~/.claude/agents/` |
| Agente `sdlc-estimation-scenario` | Calcolo scenari | `~/.claude/agents/` |
