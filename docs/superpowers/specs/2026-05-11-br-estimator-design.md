# BR Estimator — Design Spec

Skill per TL/PM che stima il team necessario per completare un BR entro una deadline, con simulazioni what-if su team, deadline, scope e rischio. Due modalita': rough (pre-analisi, dalla documentazione) e dettagliata (post-analisi, dal piano). Tre sottoagenti dedicati per analisi, storico e simulazione scenari.

## Contesto

Il TL/PM ha bisogno di rispondere a domande come "quanti dev servono per chiudere questo BR entro il 30 maggio?" prima di approvare un piano o allocare risorse. Oggi queste stime sono manuali e non tengono conto di dipendenze, wave, seniority mix, o storico dei BR precedenti.

## Decisioni di design

1. **Due modalita'** — rough (pre-analisi) e dettagliata (post-analisi), stesso motore di calcolo
2. **3 sottoagenti** — analista BR, storico, scenarista (contesto isolato, parallelizzabili)
3. **Modello ibrido deterministico + scenari di rischio** — base deterministica con 3 scenari (ottimistico/realistico/pessimistico) e moltiplicatori per tipo di rischio
4. **Team profile con dev reali** — nomi, seniority, area, disponibilita'
5. **What-if iterativo** — il TL/PM puo' variare team, deadline e scope in ciclo fino a trovare la configurazione desiderata
6. **Scope cutting intelligente** — propone tagli ordinati per rapporto risparmio/impatto, ricalcola con effetto cascata sulle dipendenze
7. **Output triplo** — conversazionale + STIMA_BR.md + Excel con 4 fogli
8. **Non bloccante** — disponibile nella pipeline come azione opzionale, non come stage obbligatorio
9. **Calibrazione storica** — usa metriche da BR completati per correggere i default

---

## 1. Architettura

```
Modalita' Rough (pre-analisi):
  BR docs + profilo + storico BR passati
    → [Analista BR] estrae funzionalita' + stima task (in parallelo)
    → [Storico] scansiona plans/done/ per calibrazione  (in parallelo)
    → [Scenarista] calcola scenari + timeline + bottleneck
    → output: conversazione + STIMA_BR.md + Excel

Modalita' Dettagliata (post-analisi):
  PIANO_IMPLEMENTAZIONE_BR.md + wave + dipendenze
    → lettura diretta (task reali gia' strutturate)
    → [Storico] scansiona plans/done/ per calibrazione
    → [Scenarista] calcola scenari + timeline + bottleneck
    → output: conversazione + STIMA_BR.md + Excel
```

Nessun agente dedicato al calcolo complesso — i sottoagenti sono Claude agents con prompt specifici. Python solo per generazione Excel (openpyxl).

---

## 2. Sottoagenti

### Analista BR (br-estimation-analyst)

**File:** `~/.claude/agents/br-estimation-analyst.md`

**Usato da:** br-estimator (solo modalita' rough)

**Riceve:**
- Documentazione BR (file MD/convertiti)
- Profilo progetto (se disponibile)

**Produce:**

```markdown
| Funzionalita' | Task stimate | Complessita' prevalente | Tipo rischio | Area |
|---|---|---|---|---|
| Dashboard monitoraggio | 4 | Media | standard | BE+FE |
| Export PDF | 2 | Alta | integrazione | BE |
| Gestione notifiche | 3 | Alta | dominio_nuovo | BE+FE |
| CRUD utenti | 2 | Bassa | standard | BE+FE |
```

Se il profilo e' disponibile, l'analista lo usa per calibrare: conosce lo stack, sa quanto costa un controller Spring Boot vs un componente Angular, e pesa di conseguenza.

### Storico (br-estimation-historian)

**File:** `~/.claude/agents/br-estimation-historian.md`

**Usato da:** br-estimator (entrambe le modalita')

**Riceve:**
- Path a `plans/done/` (o `brs/*/manifest.json` in portal-flow)
- Parametri di default (effort per complessita')

**Produce:**

```markdown
| BR | Task totali | Giorni effettivi | Dev coinvolti | Effort medio/task |
|---|---|---|---|---|
| booking-v2 | 18 | 12 | 3 | 0.67gg |
| monitoraggio | 24 | 20 | 2 | 0.83gg |

Fattore di calibrazione: 1.15x (storicamente le task richiedono il 15% in piu' del default)
```

Calcola il fattore di calibrazione confrontando effort reale vs effort teorico (dai default).

**Fallback:** se `plans/done/` e' vuota, restituisce "nessun dato storico" e il modello usa i default senza calibrazione.

### Scenarista (br-estimation-scenario)

**File:** `~/.claude/agents/br-estimation-scenario.md`

**Usato da:** br-estimator (entrambe le modalita', invocato iterativamente per ogni what-if)

**Riceve:**
- Task con complessita', area, tipo rischio, dipendenze/wave
- Team profile (nomi, seniority, area, disponibilita')
- Deadline target
- Fattore calibrazione storica
- Parametri (effort per complessita', moltiplicatori seniority e rischio)

**Calcolo:**

1. Per ogni task: `effort = giorni_complessita * moltiplicatore_seniority_owner * moltiplicatore_rischio * fattore_calibrazione`
2. Raggruppa per wave (dettagliata) o per area (rough)
3. Simula l'esecuzione giorno per giorno:
   - Ogni giorno, ogni dev prende la prossima task disponibile nella sua area
   - Una task e' disponibile se le dipendenze sono completate e la wave e' attiva
   - Dev con area "BE+FE" possono prendere task di entrambe le aree
   - Disponibilita' riduce i giorni effettivi (0.8 = 4 task-days su 5)
4. Ripete per i 3 scenari applicando i rispettivi moltiplicatori di rischio

**Produce:**

```markdown
## Scenario Realistico

| Metrica | Valore |
|---|---|
| Effort totale | 32 giorni/persona |
| Durata con team attuale | 14 giorni lavorativi |
| Data fine stimata | 2026-06-02 |
| Deadline | 2026-05-30 |
| Delta | +2 giorni (FUORI DEADLINE) |
| Utilizzo team | 76% |

### Bottleneck
- Wave 2 BE: 8 task Alta per 1 solo dev senior BE → collo di bottiglia
- FE bloccato 3 giorni in attesa di API da Wave 1 BE

### Timeline per Wave
| Wave | Inizio | Fine | Task | Dev paralleli |
|---|---|---|---|---|
| Wave 1 | 2026-05-19 | 2026-05-23 | 6 | 3 |
| Wave 2 | 2026-05-26 | 2026-06-02 | 11 | 2 |

### Allocazione Team
| Dev | Task assegnate | Giorni occupato | Utilizzo |
|---|---|---|---|
| Marco (Sr BE) | 7 | 14 | 100% |
| Luca (Mid FE) | 5 | 10 | 71% |
| Anna (Jr BE+FE) | 5 | 12 | 86% |
```

---

## 3. Modello dati e parametri

### Effort per complessita' (default, configurabili)

| Complessita' | Giorni/persona |
|---|---|
| Bassa | 0.5 |
| Media | 1.0 |
| Alta | 2.0 |
| Molto Alta | 3.5 |

### Moltiplicatori seniority

| Seniority | Moltiplicatore tempo |
|---|---|
| Senior | 1.0x |
| Mid | 1.3x |
| Junior | 1.8x |

Significato: una task Media assegnata a un Junior richiede 1.0 * 1.8 = 1.8 giorni.

### Moltiplicatori rischio per scenario

| Scenario | Standard | Integrazione | Dominio nuovo | Migrazione |
|---|---|---|---|---|
| Ottimistico | 0.8x | 0.9x | 0.9x | 0.85x |
| Realistico | 1.0x | 1.2x | 1.3x | 1.2x |
| Pessimistico | 1.3x | 1.6x | 1.7x | 1.5x |

I moltiplicatori si applicano per task in base al tipo di rischio. Il sottoagente analista BR e lo scenarista classificano le task.

### Team profile

```json
{
  "team": [
    { "nome": "Marco", "seniority": "senior", "area": "BE", "disponibilita": 1.0 },
    { "nome": "Luca", "seniority": "mid", "area": "FE", "disponibilita": 0.8 },
    { "nome": "Anna", "seniority": "junior", "area": "BE+FE", "disponibilita": 1.0 }
  ],
  "ore_giorno": 6,
  "giorni_settimana": 5
}
```

La `disponibilita` e' un fattore 0-1 (0.8 = il dev lavora 80% su questo BR). Modificabile nelle simulazioni.

---

## 4. Modalita' Rough — stima pre-analisi

**Input:** documentazione BR + profilo progetto (se disponibile)

**Flusso:**

1. La skill chiede il BR e la deadline target
2. Lancia in parallelo:
   - **Analista BR** — legge docs, estrae funzionalita', stima task/complessita'/rischio/area
   - **Storico** — scansiona plans/done/, calcola fattore calibrazione
3. Riceve i risultati, applica calibrazione storica
4. Chiede il team (o lo propone se conosce i dev dal piano/profilo)
5. Lancia lo **Scenarista** con task stimate + team + deadline
6. Presenta i 3 scenari

**Fallback senza storico:** usa default senza calibrazione.
**Fallback senza profilo:** l'analista lavora solo dalla documentazione, stime meno precise.

**Precisione attesa:** ±30-40%

---

## 5. Modalita' Dettagliata — stima post-analisi

**Input:** `PIANO_IMPLEMENTAZIONE_BR.md` (da br-analyzer)

**Flusso:**

1. La skill chiede quale BR stimare (auto-detect da plans/) e la deadline target
2. Legge il piano — task reali con complessita', area, wave, dipendenze, owner
3. Lancia lo **Storico** per il fattore di calibrazione
4. Chiede conferma/modifica team (propone i dev dal piano)
5. Lancia lo **Scenarista** con task reali + team + deadline
6. Presenta i 3 scenari

**Differenze dalla rough:**

| Aspetto | Rough | Dettagliata |
|---|---|---|
| Task | Stimate dall'analista | Reali dal piano |
| Dipendenze | Non modellate | Wave + dipendenze esplicite |
| Critical path | Approssimato | Calcolato dalle wave |
| Assegnazione | Simulata | Parte dagli owner assegnati |
| Precisione | ±30-40% | ±10-15% |

---

## 6. Simulazioni what-if

Dopo il primo output con i 3 scenari, la skill entra in un ciclo interattivo:

> Vuoi simulare uno scenario diverso?
> 1. **Aggiungi un dev** — dimmi nome, seniority, area, disponibilita'
> 2. **Rimuovi un dev** — scegli dalla lista
> 3. **Cambia deadline** — nuova data target
> 4. **Taglia scope** — ti mostro le funzionalita' tagliabili
> 5. **Cambia parametri** — effort, moltiplicatori seniority o rischio
> 6. **Salva e genera report** — salva lo scenario scelto

Per ogni what-if, re-invoca lo scenarista con i parametri modificati e presenta il delta:

> **Delta rispetto allo scenario precedente:**
> - Durata: 14gg → 10gg (-4gg)
> - Data fine: 2026-06-02 → 2026-05-28 (DENTRO DEADLINE)
> - Bottleneck BE risolto: 2 dev senior BE ora

Il ciclo continua finche' il TL/PM non sceglie "Salva e genera report".

---

## 7. Scope cutting

Quando il TL/PM sceglie "Taglia scope", lo scenarista analizza le task e propone tagli ordinati per rapporto risparmio/impatto:

```markdown
| # | Funzionalita' | Task coinvolte | Risparmio (gg) | Impatto | Raccomandazione |
|---|---|---|---|---|---|
| 1 | Export PDF | T-008, T-009 | 4.5 | Basso | Tagliabile |
| 2 | Notifiche email | T-014, T-015, T-016 | 5.0 | Medio | Differibile |
| 3 | Dashboard grafici | T-011, T-012 | 3.0 | Basso | Tagliabile |
| 4 | Multi-lingua | T-018 | 1.5 | Basso | Tagliabile |
| 5 | Validazione avanzata | T-006 | 2.0 | Alto | Sconsigliato |
```

**Classificazione impatto:**
- **Basso** — nice-to-have, esiste workaround, indipendente dal core
- **Medio** — utile ma non critica per il go-live
- **Alto** — core o implicazioni su integrita' dati/sicurezza

**Calcolo risparmio:** non somma semplice — ricalcola la timeline con le dipendenze. Tagliare una task di Wave 1 puo' sbloccare Wave 2 prima, con effetto cascata.

Il TL/PM seleziona i tagli, lo scenarista ri-simula con scope ridotto.

---

## 8. Output

### STIMA_BR.md

Salvato nella cartella del BR:
- Claude-flow: `plans/todo/<data>_<nome>/STIMA_BR.md` o `plans/in-progress/...`
- Portal-flow: `brs/<nome>/STIMA_BR.md`

Struttura:

```markdown
# Stima BR — <nome>

Data stima: <data>
Modalita': <rough|dettagliata>
Deadline target: <data>

## Team
[tabella dev con seniority, area, disponibilita']

## Scenario Selezionato: <realistico>
[metriche, timeline, allocazione, bottleneck]

## Scenari a Confronto
| Metrica | Ottimistico | Realistico | Pessimistico |
|---|---|---|---|
| Durata | 10gg | 14gg | 19gg |
| Data fine | 27/05 | 02/06 | 09/06 |
| Dentro deadline? | Si | No (+2gg) | No (+10gg) |

## Scope Escluso (se applicabile)
[funzionalita' tagliate con risparmio e motivo]

## Parametri Utilizzati
[tabelle effort, moltiplicatori, calibrazione]

## Storico di Riferimento (se disponibile)
[metriche BR passati usate per calibrazione]
```

### STIMA_BR.xlsx

Generato con openpyxl, 4 fogli:

| Foglio | Contenuto |
|---|---|
| **Scenari** | I 3 scenari affiancati con metriche chiave |
| **Timeline** | Gantt-like: righe=task, colonne=giorni, celle colorate per dev |
| **Team** | Allocazione per dev: task, giorni, utilizzo, inattivita' |
| **Parametri** | Tutti i parametri usati (editabili per ricalcolo manuale) |

Colori per dev coerenti con br-progress-report. Bottleneck evidenziati in rosso.

---

## 9. Integrazione pipeline

La skill e' disponibile come azione opzionale nella dashboard TL/PM:

**Dopo review/clarify (stato `review` o `clarify`):**
- Azione: "Stima team (rough)" → delego a `br-estimator`

**Dopo analyze (stato `analyze` o `approved`):**
- Azione: "Stima team (dettagliata)" → delego a `br-estimator`

La pipeline rileva la modalita' in base allo stato del BR: se il piano esiste → dettagliata, altrimenti → rough. Non e' uno stage bloccante.

### Flusso conversazionale

```
TL/PM: "stima il br"

Skill: Rileva BR attivi, propone quale stimare
TL/PM: conferma BR

Skill: Rileva modalita' (rough/dettagliata)
       Chiede deadline target
TL/PM: "entro il 30 maggio"

Skill: Chiede il team (propone dev noti se disponibili)
TL/PM: conferma/modifica team

Skill: Chiede parametri (default o personalizzati)
TL/PM: "default"

Skill: Lancia sottoagenti → presenta 3 scenari

TL/PM: "e se aggiungo un dev senior BE?"
Skill: Re-invoca scenarista → mostra delta

TL/PM: "taglia scope"
Skill: Propone tagli → TL/PM sceglie

TL/PM: "salva e genera report"
Skill: Scrive STIMA_BR.md + STIMA_BR.xlsx, commit
```

---

## 10. Trigger e naming

**Skill:** `br-estimator`
**Trigger:** "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team"

---

## 11. Deliverable

| # | Componente | Tipo | Dove |
|---|---|---|---|
| 1 | br-estimation-analyst.md | Nuovo agente | `~/.claude/agents/` e `claude-flow/agents/` |
| 2 | br-estimation-historian.md | Nuovo agente | `~/.claude/agents/` e `claude-flow/agents/` |
| 3 | br-estimation-scenario.md | Nuovo agente | `~/.claude/agents/` e `claude-flow/agents/` |
| 4 | br-estimator SKILL.md | Nuova skill | `claude-flow/skills/br-estimator/` |
| 5 | br-estimator SKILL.md (portal) | Nuova skill | `portal-flow/skill/br-estimator/` + install.sh |
| 6 | br-pipeline SKILL.md (claude-flow) | Modifica | Azione "Stima team" in dashboard TL/PM |
| 7 | br-pipeline SKILL.md (portal-flow) | Modifica | Azione "Stima team" in dashboard TL/PM |
| 8 | BR_SKILLS_DOCUMENTATION.md | Modifica | Nuova sezione br-estimator |
| 9 | README.md claude-flow | Modifica | Aggiunta br-estimator + 3 agenti |
| 10 | CLAUDE.md globale | Modifica | Trigger per br-estimator |

**Dipendenze:** openpyxl (gia' nell'ecosistema), git CLI.

**Totale: 3 nuovi agenti, 1 nuova skill (x2 repo), 4 file da modificare.**
