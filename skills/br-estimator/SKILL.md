---
name: br-estimator
description: Stima il team necessario per completare un BR entro una deadline, con simulazioni what-if su team, deadline, scope e rischio. Due modalita' — rough (pre-analisi, dalla documentazione) e dettagliata (post-analisi, dal piano). Produce scenari ottimistico/realistico/pessimistico con timeline, bottleneck, allocazione team e suggerimenti scope cut. Genera report MD + Excel. Usa questa skill quando l'utente dice "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", o qualsiasi variazione che implichi la necessita' di stimare l'effort o il team per un BR.
---

# BR Estimator — Stima Team e Simulazioni What-If

Questa skill stima quanti sviluppatori servono per completare un BR entro una deadline, con simulazioni interattive per variare team, deadline e scope. Produce 3 scenari (ottimistico/realistico/pessimistico) e report esportabili.

Due modalita':
- **Rough** (pre-analisi) — dalla documentazione BR, stima approssimativa (±30-40%)
- **Dettagliata** (post-analisi) — dal piano di implementazione, stima precisa (±10-15%)

---

## Rilevamento Contesto

La skill rileva automaticamente il contesto operativo:

- **Se trova `brs/<nome>/manifest.json`** → modalita' **portal-flow**
- **Se trova `plans/*/PIANO_IMPLEMENTAZIONE_BR.md` senza manifest** → modalita' **claude-flow**

## Rilevamento Modalita'

- **Se esiste un piano** (`PIANO_IMPLEMENTAZIONE_BR.md` o `manifest.piano.task[]`) → modalita' **dettagliata**
- **Se non esiste un piano ma ci sono documenti BR** → modalita' **rough**

La skill comunica la modalita' rilevata:

> Ho rilevato che il BR **<nome>** ha un piano di implementazione.
> Uso la modalita' **dettagliata** (precisione ±10-15%).

oppure:

> Il BR **<nome>** non ha ancora un piano. Uso la modalita' **rough** dalla documentazione (precisione ±30-40%).

---

## Fase 1 — Raccolta Input

Poni ogni domanda singolarmente, aspetta la risposta, poi passa alla successiva.

### Domanda 1 — BR di riferimento

Cerca i BR attivi in base al contesto:

**Claude-flow:**
```bash
ls -d plans/todo/*/ plans/in-progress/*/ 2>/dev/null
```

**Portal-flow:**
```bash
ls brs/*/manifest.json 2>/dev/null
```

Se ne trovi uno, proponilo. Se piu' di uno, chiedi quale. Se nessuno, avvisa che serve almeno la documentazione BR.

### Domanda 2 — Deadline target

> Entro quando deve essere completato il BR?
>
> Dammi una data (es. "30 maggio 2026", "fine giugno", "tra 3 settimane")

Converti in data ISO (YYYY-MM-DD). Se la data e' vaga (es. "fine giugno"), usa l'ultimo giorno lavorativo del periodo.

### Domanda 3 — Team

Tenta di proporre il team dai dati disponibili:

1. Se il piano ha gia' owner assegnati → proponi quelli con seniority dedotta dal ruolo nel piano
2. Se `.br-local.json` ha `developer` → includilo nella proposta
3. Altrimenti chiedi:

> Definisci il team. Per ogni sviluppatore:
> - **Nome**
> - **Seniority**: senior / mid / junior
> - **Area**: BE / FE / BE+FE
> - **Disponibilita'**: percentuale di tempo dedicato a questo BR (default 100%)
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
   - **Analista BR** (`br-estimation-analyst`): leggi le sue istruzioni da `~/.claude/agents/br-estimation-analyst.md`. Passagli la documentazione BR e il profilo progetto (se disponibile da `.br-local.json` → `profiles_repo`/`profilo`).
   - **Storico** (`br-estimation-historian`): leggi le sue istruzioni da `~/.claude/agents/br-estimation-historian.md`. Passagli il path a `plans/done/` (claude-flow) o `brs/` (portal-flow) e i parametri di default.

2. Ricevi i risultati:
   - Dall'analista: tabella funzionalita' con task stimate, complessita', rischio, area
   - Dallo storico: fattore di calibrazione (o 1.0x se nessun dato)

3. Mostra un riepilogo dell'analisi all'utente:

> ## Analisi completata
>
> **Funzionalita' rilevate:** N
> **Task stimate:** M
> **Calibrazione storica:** Xx (da K BR precedenti)
>
> [tabella funzionalita' dall'analista]
>
> Procedo con il calcolo degli scenari?

4. Dopo conferma, lancia lo **Scenarista** (`br-estimation-scenario`): leggi le sue istruzioni da `~/.claude/agents/br-estimation-scenario.md`. Passagli le task stimate, il team, la deadline, il fattore di calibrazione e i parametri.

### Modalita' Dettagliata

1. Leggi il piano (`PIANO_IMPLEMENTAZIONE_BR.md` o `manifest.piano.task[]`). Per ogni task, estrai: ID, nome, complessita', area, wave, dipendenze, owner.

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

### STIMA_BR.md

Scrivi il file nella cartella del BR:
- Claude-flow: `plans/todo/<data>_<nome>/STIMA_BR.md` o `plans/in-progress/<data>_<nome>/STIMA_BR.md`
- Portal-flow: `brs/<nome>/STIMA_BR.md`

Struttura:

```markdown
# Stima BR — <nome>

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
Fattore: Xx (da N BR precedenti)

## Storico di Riferimento

(presente solo se ci sono dati storici)

[tabella BR passati dallo storico]
```

### STIMA_BR.xlsx

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
- Usare colori distinti per dev (stesso schema di br-progress-report se disponibile)

**Foglio 3 — Team:**
- Tabella: Dev | Seniority | Area | Task assegnate | Giorni occupato | Giorni libero | Utilizzo
- Barra colorata proporzionale all'utilizzo

**Foglio 4 — Parametri:**
- Tutte le tabelle dei parametri usati
- Celle editabili (non protette) per ricalcolo manuale esterno

Salva il file nella stessa cartella del STIMA_BR.md.

### Commit

Dopo aver scritto entrambi i file:

```bash
git add <cartella-br>/STIMA_BR.md <cartella-br>/STIMA_BR.xlsx
git commit -m "[br-estimator] <nome-br>: stima team (<modalita'>)"
```

---

## Regole Fondamentali

1. **Mai procedere senza conferma** — tra una fase e l'altra, aspetta l'utente
2. **Il sottoagente analizza, la skill orchestra** — non stimare direttamente, usa i sottoagenti
3. **Delta espliciti** — ogni what-if mostra il confronto col precedente
4. **Parametri trasparenti** — mostra sempre come il numero e' calcolato
5. **Fallback senza dati** — funziona anche senza storico e senza profilo
6. **Supportare entrambe le modalita'** (claude-flow e portal-flow) senza compromessi
7. **Scope cutting con cascata** — il risparmio tiene conto delle dipendenze

---

## Dipendenze

| Dipendenza | Usata per | Installazione |
|---|---|---|
| `openpyxl` (Python) | Generazione Excel | `pip install openpyxl` |
| Agente `br-estimation-analyst` | Stima rough | `~/.claude/agents/` |
| Agente `br-estimation-historian` | Calibrazione storica | `~/.claude/agents/` |
| Agente `br-estimation-scenario` | Calcolo scenari | `~/.claude/agents/` |
