# BR Estimator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `br-estimator` skill with 3 dedicated subagents for team estimation and what-if simulations on BR timelines, integrated as optional actions in the pipeline dashboards.

**Architecture:** Three subagents (analyst for rough estimation from docs, historian for calibration from past BRs, scenario for timeline/bottleneck simulation) orchestrated by a single skill that handles the conversational flow, what-if loop, and output generation (STIMA_BR.md + Excel). Integrated in both pipeline variants as non-blocking TL/PM actions.

**Tech Stack:** Claude Code skills (SKILL.md), Claude Code agents (.md), openpyxl (Python) for Excel generation.

**Design spec:** `docs/superpowers/specs/2026-05-11-br-estimator-design.md`

**Repos coinvolti:**
- `claude-flow/` — skill source, agents source, documentation
- `portal-flow/` — portal skill (br-estimator + br-pipeline modification)

**No co-author attribution in commits.**

---

## Execution Waves

```
Wave 1 (parallel, no deps):
  Task 1: br-estimation-analyst agent
  Task 2: br-estimation-historian agent
  Task 3: br-estimation-scenario agent

Wave 2 (depends on Wave 1):
  Task 4: br-estimator skill (claude-flow + portal-flow)

Wave 3 (parallel, depends on Wave 2):
  Task 5: br-pipeline claude-flow modification
  Task 6: br-pipeline portal-flow modification

Wave 4 (sequential, depends on Wave 3):
  Task 7: BR_SKILLS_DOCUMENTATION.md
  Task 8: README.md claude-flow
  Task 9: CLAUDE.md global triggers
  Task 10: Final verification
```

---

### Task 1: Create br-estimation-analyst agent

**Files:**
- Create: `claude-flow/agents/br-estimation-analyst.md`

- [ ] **Step 1: Create br-estimation-analyst.md**

Create `C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-analyst.md`:

````markdown
---
name: br-estimation-analyst
description: Agente per la stima rough di un BR dalla documentazione. Legge i documenti del BR e il profilo progetto (se disponibile), estrae le funzionalita', stima il numero di task, la complessita' prevalente, il tipo di rischio e l'area. Usato da br-estimator in modalita' rough.
---

# BR Estimation Analyst

Sei un analista di Business Requirements specializzato nella stima dell'effort. Ricevi la documentazione di un BR e, opzionalmente, un profilo progetto. Il tuo compito e' estrarre le funzionalita' richieste e stimare il numero di task, la complessita', il tipo di rischio e l'area per ciascuna.

## Input che ricevi

1. **Documentazione BR** — file MD con i requisiti funzionali e tecnici
2. **Profilo progetto** (opzionale, JSON) — `tech_stack`, `conventions`, `domain`, `design_system`

## Come analizzare

### Estrazione funzionalita'

Leggi tutta la documentazione e identifica ogni funzionalita' discreta:
- Ogni pagina/schermata e' tipicamente 1-3 funzionalita'
- Ogni flusso utente completo (es. "registrazione", "checkout") e' una funzionalita'
- Ogni integrazione esterna (es. "invio email", "export PDF", "chiamata API esterna") e' una funzionalita'
- CRUD semplici su una singola entita' contano come 1 funzionalita'
- Dashboard con grafici/report complessi e' una funzionalita' separata

### Stima task per funzionalita'

Per ogni funzionalita', stima quante task servono considerando:
- **Entita'/modello dati** — creazione/modifica entita', DTO, migration
- **API/Controller** — endpoint, validazione, autorizzazione
- **Logica di servizio** — business logic, workflow
- **Frontend** — componenti, routing, stato, chiamate API
- **Test** — inclusi nella stima (non come task separata)

### Classificazione complessita'

| Complessita' | Criteri |
|---|---|
| Bassa | CRUD semplice, nessuna logica custom, UI standard |
| Media | Logica di business moderata, validazioni custom, UI con stato |
| Alta | Workflow complesso, integrazioni esterne, UI interattiva |
| Molto Alta | Macchine a stati, concorrenza, sicurezza critica, algoritmi complessi |

### Classificazione tipo rischio

| Tipo | Criteri |
|---|---|
| `standard` | CRUD, logica lineare, nessuna dipendenza esterna |
| `integrazione` | API esterne, servizi terzi, formati file, protocolli |
| `dominio_nuovo` | Concetti di business non presenti nel codebase, primo contatto col dominio |
| `migrazione` | Cambio struttura dati, compatibilita' retroattiva, conversione |

### Classificazione area

| Area | Criteri |
|---|---|
| `BE` | Solo backend: API, servizi, entita', database |
| `FE` | Solo frontend: componenti, routing, stato |
| `BE+FE` | Entrambi: nuova API consumata da un nuovo componente |

### Calibrazione con profilo

**Se il profilo e' disponibile:**
- Usa `tech_stack` per pesare la complessita': uno stack conosciuto (es. Spring Boot + Angular con pattern consolidati) riduce il rischio; uno stack misto o nuovo lo aumenta
- Usa `domain.glossary` per valutare se le funzionalita' toccano concetti gia' modellati (rischio standard) o nuovi (rischio dominio_nuovo)
- Usa `conventions` per stimare se i pattern esistenti coprono la funzionalita' (task in meno) o se serve codice nuovo

**Se il profilo NON e' disponibile:**
- Stima conservativa: assume complessita' Media come default, rischio standard

## Output

Produci una tabella markdown strutturata:

```markdown
## Stima Funzionalita' — <nome BR>

| Funzionalita' | Task stimate | Complessita' prevalente | Tipo rischio | Area | Note |
|---|---|---|---|---|---|
| Dashboard monitoraggio | 4 | Media | standard | BE+FE | 2 BE (API + service) + 2 FE (componenti + routing) |
| Export PDF | 2 | Alta | integrazione | BE | Libreria PDF esterna |
| Gestione notifiche | 3 | Alta | dominio_nuovo | BE+FE | Concetto non presente nel codice |
| CRUD utenti | 2 | Bassa | standard | BE+FE | Pattern gia' esistente |

### Riepilogo

| Metrica | Valore |
|---|---|
| Funzionalita' totali | 4 |
| Task stimate totali | 11 |
| Complessita' media | Media-Alta |
| Area prevalente | BE+FE |
| Rischio prevalente | standard (50%), integrazione (25%), dominio_nuovo (25%) |
```

## Regole

1. **Mai sottostimare** — nel dubbio, arrotonda per eccesso
2. **Task stimate includono i test** — non aggiungere task separate per i test
3. **Granularita' coerente** — ogni task e' circa 0.5-2 giorni di lavoro per un dev senior
4. **Note esplicative** — per ogni riga, spiega brevemente come arrivi al numero
5. **Segnala le incognite** — se un requisito e' ambiguo, segnalalo e stima il caso peggiore
````

- [ ] **Step 2: Install agent globally**

```bash
mkdir -p ~/.claude/agents
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-analyst.md ~/.claude/agents/
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add agents/br-estimation-analyst.md
git commit -m "feat: add br-estimation-analyst agent for rough BR estimation"
```

---

### Task 2: Create br-estimation-historian agent

**Files:**
- Create: `claude-flow/agents/br-estimation-historian.md`

- [ ] **Step 1: Create br-estimation-historian.md**

Create `C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-historian.md`:

````markdown
---
name: br-estimation-historian
description: Agente per l'analisi storica dei BR completati. Scansiona plans/done/ (o brs/*/manifest.json), estrae metriche reali (task, giorni, dev) e calcola un fattore di calibrazione per correggere le stime default. Usato da br-estimator in entrambe le modalita'.
---

# BR Estimation Historian

Sei uno storico dei Business Requirements. Il tuo compito e' scansionare i BR completati, estrarre metriche reali di effort, e calcolare un fattore di calibrazione che corregga le stime teoriche in base all'esperienza reale del team.

## Input che ricevi

1. **Path alla directory dei BR completati:**
   - Claude-flow: `plans/done/`
   - Portal-flow: `brs/*/manifest.json` (filtra quelli con `stato_pipeline: "done"`)
2. **Parametri di default** — effort per complessita' (Bassa=0.5, Media=1.0, Alta=2.0, Molto Alta=3.5)

## Come analizzare

### Scansione BR completati

**Claude-flow:**

```bash
ls -d plans/done/*/ 2>/dev/null
```

Per ogni cartella trovata, leggi:
- `PIANO_IMPLEMENTAZIONE_BR.md` — per la lista task con complessita'
- `PROGRESSO_BR.md` — per le date effettive di completamento

**Portal-flow:**

```bash
ls brs/*/manifest.json 2>/dev/null
```

Per ogni manifest con `stato_pipeline: "done"`, leggi `piano.task[]` e `timeline[]`.

### Estrazione metriche per BR

Per ogni BR completato, estrai:

1. **Task totali** — conta tutte le task nel piano
2. **Distribuzione complessita'** — quante Bassa, Media, Alta, Molto Alta
3. **Dev coinvolti** — conta gli owner unici nel piano o nel progresso
4. **Giorni effettivi** — dalla data del primo log di attivita' alla data dell'ultimo completamento
5. **Effort teorico** — somma dei giorni teorici usando i default (es. 5 task Media = 5.0gg, 3 task Alta = 6.0gg)
6. **Effort medio per task** — giorni effettivi / task totali

### Calcolo fattore di calibrazione

```
Per ogni BR:
  effort_teorico = somma(giorni_complessita per ogni task)
  effort_reale = giorni_effettivi * dev_coinvolti  (giorni/persona)
  rapporto = effort_reale / effort_teorico

Fattore di calibrazione = media(rapporti di tutti i BR)
```

Se il fattore e' > 1.0, significa che storicamente le task richiedono piu' tempo del default.
Se il fattore e' < 1.0, il team e' piu' veloce del default.

### Fallback

Se non ci sono BR completati (nessuna cartella in `plans/done/` e nessun manifest con stato `done`), restituisci:

```markdown
Nessun dato storico disponibile. Il modello usera' i parametri default senza calibrazione.
Fattore di calibrazione: 1.0x (default)
```

## Output

```markdown
## Analisi Storica BR

### BR Completati

| BR | Task totali | Complessita' media | Dev | Giorni effettivi | Effort teorico | Effort reale | Rapporto |
|---|---|---|---|---|---|---|---|
| booking-v2 | 18 | Media | 3 | 12 | 22.0gg | 36.0gg/p | 1.64x |
| monitoraggio | 24 | Media-Alta | 2 | 20 | 30.5gg | 40.0gg/p | 1.31x |
| auth-refactor | 8 | Alta | 1 | 6 | 13.0gg | 6.0gg/p | 0.46x |

### Fattore di Calibrazione

| Metrica | Valore |
|---|---|
| BR analizzati | 3 |
| Rapporto medio | 1.14x |
| **Fattore di calibrazione** | **1.14x** |
| Interpretazione | Le task richiedono mediamente il 14% in piu' del default |

### Note
- Il BR `auth-refactor` ha un rapporto molto basso (0.46x): possibile che un dev senior abbia completato task sottostimate. Considerare come outlier.
- Escludendo outlier (rapporto < 0.6 o > 2.0): fattore corretto = 1.48x
```

## Regole

1. **Mai inventare dati** — usa solo metriche estraibili dai file
2. **Segnala outlier** — rapporti molto alti o bassi indicano stime sbagliate, non team lenti/veloci
3. **Minimo 2 BR per calibrazione affidabile** — con 1 solo BR, segnala che il dato e' poco significativo
4. **Fallback esplicito** — se non ci sono dati, dillo chiaramente
5. **Dual-mode** — supporta sia il formato claude-flow (plans/done/) che portal-flow (manifests)
````

- [ ] **Step 2: Install agent globally**

```bash
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-historian.md ~/.claude/agents/
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add agents/br-estimation-historian.md
git commit -m "feat: add br-estimation-historian agent for historical BR calibration"
```

---

### Task 3: Create br-estimation-scenario agent

**Files:**
- Create: `claude-flow/agents/br-estimation-scenario.md`

- [ ] **Step 1: Create br-estimation-scenario.md**

Create `C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-scenario.md`:

````markdown
---
name: br-estimation-scenario
description: Agente per il calcolo di scenari di stima con timeline, bottleneck, allocazione team e scope cutting. Riceve task, team, deadline e parametri, produce 3 scenari (ottimistico/realistico/pessimistico) con metriche dettagliate. Invocato iterativamente per simulazioni what-if. Usato da br-estimator.
---

# BR Estimation Scenario

Sei uno scenarista per la pianificazione di team software. Ricevi una lista di task con complessita' e rischio, un team con seniority e disponibilita', una deadline, e i parametri di calcolo. Produci 3 scenari (ottimistico/realistico/pessimistico) con timeline, bottleneck e allocazione team.

## Input che ricevi

1. **Task** — lista con per ogni task: id (o nome), complessita' (Bassa/Media/Alta/Molto Alta), area (BE/FE/BE+FE), tipo rischio (standard/integrazione/dominio_nuovo/migrazione), wave (se disponibile), dipendenze (se disponibili)
2. **Team** — lista dev con nome, seniority (senior/mid/junior), area (BE/FE/BE+FE), disponibilita' (0-1)
3. **Deadline target** — data entro cui completare
4. **Fattore calibrazione storica** — moltiplicatore (default 1.0)
5. **Parametri** — effort per complessita', moltiplicatori seniority, moltiplicatori rischio per scenario

### Parametri default (se non forniti)

**Effort per complessita':**

| Complessita' | Giorni/persona |
|---|---|
| Bassa | 0.5 |
| Media | 1.0 |
| Alta | 2.0 |
| Molto Alta | 3.5 |

**Moltiplicatori seniority:**

| Seniority | Moltiplicatore |
|---|---|
| Senior | 1.0x |
| Mid | 1.3x |
| Junior | 1.8x |

**Moltiplicatori rischio per scenario:**

| Scenario | Standard | Integrazione | Dominio nuovo | Migrazione |
|---|---|---|---|---|
| Ottimistico | 0.8x | 0.9x | 0.9x | 0.85x |
| Realistico | 1.0x | 1.2x | 1.3x | 1.2x |
| Pessimistico | 1.3x | 1.6x | 1.7x | 1.5x |

## Algoritmo di calcolo

### 1. Calcolo effort per task

Per ogni task, per ogni scenario:

```
effort_task = giorni_complessita * moltiplicatore_rischio_scenario * fattore_calibrazione
```

Nota: il moltiplicatore seniority si applica quando la task viene assegnata a un dev specifico (nel passo successivo).

### 2. Simulazione giorno per giorno

Per ogni scenario, simula l'esecuzione:

```
giorno = data_inizio
task_completate = []
task_in_corso = {}  // dev → (task, giorni_rimanenti)

while task_non_completate:
    per ogni dev nel team:
        se dev ha una task in corso:
            giorni_rimanenti -= disponibilita
            se giorni_rimanenti <= 0:
                task_completate.append(task)
                dev diventa libero
        
        se dev e' libero:
            prossima_task = trova_prossima_task(dev.area, wave_corrente, dipendenze)
            se prossima_task esiste:
                effort = effort_task * moltiplicatore_seniority_dev
                task_in_corso[dev] = (prossima_task, effort)
    
    giorno += 1 giorno lavorativo (salta weekend)
```

### 3. Regole di assegnazione task

- Un dev puo' lavorare solo su task della sua area (BE per dev BE, FE per dev FE, entrambe per dev BE+FE)
- Se ci sono wave, le task della wave N+1 non sono disponibili finche' tutte le task della wave N non sono complete
- Le dipendenze esplicite (T-001 → T-005) bloccano la task dipendente
- Tra le task disponibili, prendi quella con complessita' piu' alta (le task difficili prima)

### 4. Rilevamento bottleneck

Un bottleneck si verifica quando:
- Un dev e' al 100% di utilizzo per piu' di 3 giorni consecutivi
- Un'area (BE o FE) ha task in coda ma nessun dev disponibile
- Una wave non puo' iniziare perche' la precedente ha task non assegnabili

### 5. Scope cutting (se richiesto)

Quando ricevi il flag `scope_cutting: true`:

1. Raggruppa le task per funzionalita' (dal campo nome/funzionalita' o raggruppando per prefisso)
2. Per ogni funzionalita', calcola:
   - Risparmio lordo: somma effort delle task
   - Risparmio netto: ricalcola la timeline SENZA quelle task e misura il delta reale (effetto cascata su dipendenze e wave)
3. Classifica l'impatto: Basso (task non in critical path, nessuna dipendenza), Medio (task con dipendenze ma non bloccanti), Alto (task nel critical path o con implicazioni su integrita')
4. Ordina per rapporto risparmio_netto/impatto (migliori tagli prima)

## Output

Per ogni scenario (ottimistico, realistico, pessimistico), produci:

```markdown
## Scenario <Nome>

| Metrica | Valore |
|---|---|
| Effort totale | XX giorni/persona |
| Durata con team attuale | XX giorni lavorativi |
| Data inizio | YYYY-MM-DD |
| Data fine stimata | YYYY-MM-DD |
| Deadline | YYYY-MM-DD |
| Delta | +/- X giorni (DENTRO/FUORI DEADLINE) |
| Utilizzo team medio | XX% |

### Bottleneck
- [descrizione bottleneck 1]
- [descrizione bottleneck 2]
(oppure "Nessun bottleneck rilevato" se tutto scorre)

### Timeline per Wave
| Wave | Inizio | Fine | Task | Dev paralleli |
|---|---|---|---|---|
| Wave 1 | YYYY-MM-DD | YYYY-MM-DD | N | X |
| Wave 2 | YYYY-MM-DD | YYYY-MM-DD | N | X |

(Se non ci sono wave, mostra "Timeline lineare" con una riga per area BE e una per FE)

### Allocazione Team
| Dev | Seniority | Area | Task assegnate | Giorni occupato | Utilizzo |
|---|---|---|---|---|---|
| Nome | Sr/Mid/Jr | BE/FE | N | X | XX% |
```

### Output scope cutting (se richiesto)

```markdown
## Funzionalita' Tagliabili

| # | Funzionalita' | Task coinvolte | Risparmio lordo | Risparmio netto | Impatto | Raccomandazione |
|---|---|---|---|---|---|---|
| 1 | Export PDF | T-008, T-009 | 4.5gg | 4.0gg | Basso | Tagliabile |
| 2 | Notifiche email | T-014, T-015, T-016 | 5.0gg | 6.5gg | Medio | Differibile |

Nota: il risparmio netto puo' essere > del lordo per effetto cascata (sblocco wave anticipato).

Combinazione suggerita: tagliando #1 + #3 si risparmiano X giorni, rientrando nella deadline.
```

## Regole

1. **Mai saltare il weekend** — i giorni lavorativi sono lun-ven
2. **Disponibilita' precisa** — un dev con disponibilita' 0.8 lavora effettivamente 4 giorni su 5
3. **Wave rigide** — non anticipare task della wave successiva
4. **Bottleneck espliciti** — segnala sempre le cause di rallentamento
5. **Scope cutting con cascata** — il risparmio netto deve considerare l'effetto sulle dipendenze
6. **Determinismo** — a parita' di input, il risultato deve essere identico (niente random)
````

- [ ] **Step 2: Install agent globally**

```bash
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-scenario.md ~/.claude/agents/
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add agents/br-estimation-scenario.md
git commit -m "feat: add br-estimation-scenario agent for timeline and what-if simulations"
```

---

### Task 4: Create br-estimator skill

**Files:**
- Create: `claude-flow/skills/br-estimator/SKILL.md`
- Create: `portal-flow/skill/br-estimator/SKILL.md`
- Create: `portal-flow/skill/br-estimator/install.sh`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator
mkdir -p C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator
```

- [ ] **Step 2: Create SKILL.md in claude-flow**

Create `C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator/SKILL.md`:

````markdown
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
````

- [ ] **Step 3: Copy SKILL.md to portal-flow**

```bash
cp C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator/SKILL.md C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/
```

- [ ] **Step 4: Create install.sh in portal-flow**

Create `C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/br-estimator"

echo "=== br-estimator installer ==="
echo ""

if [ -L "$SKILL_DIR" ]; then
    EXISTING_TARGET="$(readlink "$SKILL_DIR")"
    if [ "$EXISTING_TARGET" = "$SCRIPT_DIR" ]; then
        echo "Symlink already exists and points to the correct location."
    else
        echo "Symlink exists but points to: $EXISTING_TARGET"
        echo "Updating to: $SCRIPT_DIR"
        rm "$SKILL_DIR"
        ln -s "$SCRIPT_DIR" "$SKILL_DIR"
        echo "Symlink updated."
    fi
elif [ -d "$SKILL_DIR" ]; then
    echo "ERROR: $SKILL_DIR exists as a directory (not a symlink)."
    echo "Remove it manually and re-run this script."
    exit 1
else
    mkdir -p "$(dirname "$SKILL_DIR")"
    ln -s "$SCRIPT_DIR" "$SKILL_DIR"
    echo "Symlink created: $SKILL_DIR -> $SCRIPT_DIR"
fi

if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo "Verification: SKILL.md found at $SKILL_DIR/SKILL.md"
else
    echo "ERROR: SKILL.md not found after symlink. Something went wrong."
    exit 1
fi

echo ""
echo "=== Add this to ~/.claude/CLAUDE.md ==="
echo ""
cat <<'BLOCK'
# br-estimator
- **br-estimator** (`~/.claude/skills/br-estimator/SKILL.md`) - stima team e simulazioni what-if per BR. Trigger: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort"
When the user says "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR, invoke the Skill tool with `skill: "br-estimator"` before doing anything else.
BLOCK

echo ""
echo "Done."
```

Make it executable: `chmod +x C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/install.sh`

- [ ] **Step 5: Commit in both repos**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-estimator/SKILL.md
git commit -m "feat: add br-estimator skill for team estimation and what-if simulations"
```

```bash
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow
git add skill/br-estimator/SKILL.md skill/br-estimator/install.sh
git commit -m "feat: add br-estimator skill for team estimation and what-if simulations"
```

---

### Task 5: Modify br-pipeline (claude-flow) — add estimation action

**Files:**
- Modify: `claude-flow/skills/br-pipeline/SKILL.md`

- [ ] **Step 1: Add estimation action to review/clarify states**

In `skills/br-pipeline/SKILL.md`, find the section for `review` and `clarify` states. These are in the Fase 3 actions. After the existing actions for these states (around line 170-180, where it shows actions for each BR state), add for BR in `review` or `clarify` state:

```markdown
> - **Stima team (rough)** → delego a `br-estimator`
```

- [ ] **Step 2: Add estimation action to approved/execute states**

Find section `### \`approved\` / \`execute\` — Esecuzione task` (around line 371). In the "Azioni disponibili" list (line 385-388), add after the existing options:

```markdown
> 4. **Stima team (dettagliata)** → delego a `br-estimator`
```

Also update the "Debug attivo" variant (around line 403-407) — add after option 4:

```markdown
> 5. **Stima team (dettagliata)** → delego a `br-estimator`
```

- [ ] **Step 3: Add skill delegation entry**

Find the "Skill delegate" table at the top of the file. Add:

```markdown
| `estimate` | Stima team e simulazioni what-if | `br-estimator` |
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add skills/br-pipeline/SKILL.md
git commit -m "feat: add estimation action to br-pipeline dashboard"
```

---

### Task 6: Modify br-pipeline (portal-flow) — add estimation action

**Files:**
- Modify: `portal-flow/skill/br-pipeline/SKILL.md`

- [ ] **Step 1: Add estimation to stage table**

In `portal-flow/skill/br-pipeline/SKILL.md`, find the stage table. Add after the Debug row:

```markdown
| Estimate | S9 | TL/PM | Claude Code | Stima team e simulazioni what-if |
```

- [ ] **Step 2: Add estimation to TL/PM next step suggestions**

Find the section where next steps are proposed for each `stato_pipeline` (around line 99-115). Add for `review` and `clarify`:

```markdown
- Dopo `review` o `clarify`: aggiungi "Stima team (rough) → `br-estimator`"
- Dopo `analyze` o `approved`: aggiungi "Stima team (dettagliata) → `br-estimator`"
```

Specifically, after line 101 (`- \`review\` → "Attendere risposte funzionale"`), add:

```markdown
  - "Stima team (rough)" → `br-estimator` (opzionale, non bloccante)
```

After line 105 (`- \`execute\` → "Monitorare progresso"`), add:

```markdown
  - "Stima team (dettagliata)" → `br-estimator` (opzionale, non bloccante)
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow
git add skill/br-pipeline/SKILL.md
git commit -m "feat: add estimation action to br-pipeline dashboard"
```

---

### Task 7: Update BR_SKILLS_DOCUMENTATION.md

**Files:**
- Modify: `claude-flow/BR_SKILLS_DOCUMENTATION.md`

- [ ] **Step 1: Add br-estimator section**

Find the end of section 11 (BR Profile Setup). After it, add:

```markdown
---

## 12. BR Estimator

**Skill**: `br-estimator`
**Path**: `~/.claude/skills/br-estimator/SKILL.md`
**Trigger**: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort"

### Scopo

Stima il team necessario per completare un BR entro una deadline, con simulazioni what-if su team, deadline, scope e rischio.

### Due Modalita'

| Modalita' | Quando | Input | Precisione |
|---|---|---|---|
| Rough | Pre-analisi (prima di br-analyzer) | Documentazione BR | ±30-40% |
| Dettagliata | Post-analisi (dopo br-analyzer) | Piano di implementazione | ±10-15% |

### Sottoagenti

| Agente | File | Usato in | Ruolo |
|---|---|---|---|
| br-estimation-analyst | `~/.claude/agents/br-estimation-analyst.md` | Solo rough | Estrae funzionalita' e stima task dalla documentazione |
| br-estimation-historian | `~/.claude/agents/br-estimation-historian.md` | Entrambe | Scansiona BR completati per calibrazione storica |
| br-estimation-scenario | `~/.claude/agents/br-estimation-scenario.md` | Entrambe | Calcola scenari, timeline, bottleneck, scope cutting |

### Scenari

Modello ibrido deterministico + rischio. Ogni stima produce 3 scenari:
- **Ottimistico** — moltiplicatori ridotti
- **Realistico** — moltiplicatori standard
- **Pessimistico** — moltiplicatori aumentati

Con moltiplicatori differenziati per tipo di rischio (standard, integrazione, dominio nuovo, migrazione).

### Simulazioni What-If

Ciclo interattivo: aggiungi/rimuovi dev, cambia deadline, taglia scope, modifica parametri. Ogni what-if mostra il delta rispetto allo scenario precedente.

### Output

- **STIMA_BR.md** — report dettagliato con scenari, team, parametri, storico
- **STIMA_BR.xlsx** — Excel con 4 fogli (Scenari, Timeline Gantt-like, Team allocation, Parametri)

### Integrazione Pipeline

Azione opzionale nella dashboard TL/PM:
- Dopo review/clarify: "Stima team (rough)"
- Dopo analyze/approved: "Stima team (dettagliata)"
```

- [ ] **Step 2: Update trigger table**

Find the "Trigger Registrati" table. Add:

```markdown
| "stima il br" / "quanti sviluppatori servono" / "simulazione team" / "stima effort" / "stima team" | br-estimator |
```

- [ ] **Step 3: Update intro skill count**

Find the intro line with the skill count. Update to reflect 10 skills (was 9 after agents+profiles).

- [ ] **Step 4: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add BR_SKILLS_DOCUMENTATION.md
git commit -m "docs: add br-estimator section to BR skills documentation"
```

---

### Task 8: Update README.md claude-flow

**Files:**
- Modify: `claude-flow/README.md`

- [ ] **Step 1: Update skill count**

Find "9 skill e 2 agenti generici" and change to "10 skill e 5 agenti generici".

- [ ] **Step 2: Add br-estimator section**

After the `### br-profile-setup` section and before `### br-pipeline`, add:

```markdown

### br-estimator

Stima il team necessario per completare un BR entro una deadline. Due modalita': rough (dalla documentazione, ±30-40%) e dettagliata (dal piano, ±10-15%). Produce scenari ottimistico/realistico/pessimistico con timeline, bottleneck e allocazione team. Simulazioni what-if interattive per variare team, deadline e scope. Genera report MD + Excel.

**Trigger**: `stima il br`, `quanti sviluppatori servono`, `simulazione team`, `stima effort`
```

- [ ] **Step 3: Update agents section**

Find the "## Agenti Generici" section. Add after the "Routing a specialist" paragraph:

```markdown

### br-estimation-analyst

Analista per stima rough. Estrae funzionalita' dalla documentazione BR e stima task, complessita', rischio e area.

### br-estimation-historian

Storico per calibrazione. Scansiona BR completati ed estrae metriche reali per correggere le stime default.

### br-estimation-scenario

Scenarista per simulazioni. Calcola timeline giorno per giorno, identifica bottleneck, produce 3 scenari con allocazione team. Supporta scope cutting con effetto cascata.
```

- [ ] **Step 4: Update installation count**

Find "9 skill e i 2 agenti" and change to "10 skill e i 5 agenti generici".

- [ ] **Step 5: Add trigger block**

Find the `# br-profile-setup` trigger block. After it and before `# br-pipeline`, add:

```markdown

# br-estimator
- **br-estimator** (`~/.claude/skills/br-estimator/SKILL.md`) - stima team e simulazioni what-if per BR. Trigger: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort"
When the user says "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR, invoke the Skill tool with `skill: "br-estimator"` before doing anything else.
```

- [ ] **Step 6: Commit**

```bash
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow
git add README.md
git commit -m "docs: add br-estimator skill and estimation agents to README"
```

---

### Task 9: Register br-estimator trigger in global CLAUDE.md

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Add br-estimator trigger block**

In `~/.claude/CLAUDE.md`, find the `# br-profile-setup` block. After it and before `# jarvis-polling`, insert:

```markdown

# br-estimator
- **br-estimator** (`~/.claude/skills/br-estimator/SKILL.md`) - stima team e simulazioni what-if per completare un BR entro una deadline. Due modalita' (rough e dettagliata), 3 scenari, scope cutting, report MD + Excel. Trigger: "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort"
When the user says "stima il br", "quanti sviluppatori servono", "simulazione team", "stima effort", "stima team", or similar phrases about estimating team size or effort for a BR, invoke the Skill tool with `skill: "br-estimator"` before doing anything else.
```

- [ ] **Step 2: Verify format**

Compare with existing trigger blocks (br-profile-setup, br-debug) to confirm format matches:
- Header: `# br-estimator`
- Bullet with path, description, trigger phrases
- `When the user says...` instruction

No commit needed — `~/.claude/CLAUDE.md` is not in a git repo.

---

### Task 10: Final verification

- [ ] **Step 1: Verify all new files exist**

```bash
# Agents
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-analyst.md
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-historian.md
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/agents/br-estimation-scenario.md
ls ~/.claude/agents/br-estimation-analyst.md
ls ~/.claude/agents/br-estimation-historian.md
ls ~/.claude/agents/br-estimation-scenario.md

# Skill
ls C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator/SKILL.md
ls C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/SKILL.md
ls C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/install.sh
```

- [ ] **Step 2: Verify skill consistency**

```bash
diff C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator/SKILL.md \
     C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-estimator/SKILL.md
```

Should show no differences.

- [ ] **Step 3: Verify pipeline integration**

```bash
grep -l "br-estimator" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-pipeline/SKILL.md \
  C:/Users/davmelis/Documents/MyGitHub/portal-flow/skill/br-pipeline/SKILL.md
```

Both should match.

- [ ] **Step 4: Verify documentation**

```bash
grep -n "br-estimator" C:/Users/davmelis/Documents/MyGitHub/claude-flow/BR_SKILLS_DOCUMENTATION.md
grep -n "br-estimator" C:/Users/davmelis/Documents/MyGitHub/claude-flow/README.md
grep -n "br-estimator" ~/.claude/CLAUDE.md
```

All three should show matches.

- [ ] **Step 5: Verify agent references in skill**

```bash
grep "br-estimation-analyst\|br-estimation-historian\|br-estimation-scenario" \
  C:/Users/davmelis/Documents/MyGitHub/claude-flow/skills/br-estimator/SKILL.md
```

Should show all 3 agent names referenced.

- [ ] **Step 6: Git log summary**

```bash
echo "=== claude-flow ===" && \
cd C:/Users/davmelis/Documents/MyGitHub/claude-flow && git log --oneline -8 && \
echo "" && echo "=== portal-flow ===" && \
cd C:/Users/davmelis/Documents/MyGitHub/portal-flow && git log --oneline -5
```
