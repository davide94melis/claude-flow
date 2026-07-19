# Integrazione Workflow + Ultracode nelle Skill SDLC — Design

> Documento di design. Definisce **come** integrare una modalità opt-in `workflow+ultracode`
> nelle 9 skill SDLC di claude-flow, affiancata alla modalità classica esistente.
> Vedi anche: [`SDLC_SKILLS_DOCUMENTATION.md`](../SDLC_SKILLS_DOCUMENTATION.md) ·
> [`SOLARIA_SDLC_INTEGRATION.md`](./SOLARIA_SDLC_INTEGRATION.md) ·
> [`ROADMAP_NEW_SKILLS.md`](./ROADMAP_NEW_SKILLS.md)

**Stato:** design approvato e **rollout completo implementato** (2026-05-30): step 1+2 (flag + sezione "## Modalità di orchestrazione" in tutte e 9 le SKILL.md), step 3-5 (5 workflow heavy in `workflows/`: analyzer-gap, executor-wave, debug-fixwave, updater-delta, reviewer-quality + wiring `deep`), step 6 (cerchio light: estimator/clarify/progress-report/profile-setup, solo coherence-critic). Tutti i workflow superati da review adversariale statica. **Golden-test del pilota SALTATO per decisione utente** (risparmio token sul run su codebase reale): il pattern è stato propagato sulla sola forza della review statica, non del run empirico. Il run resta facoltativo (strumenti pronti, vedi [`GOLDEN_TEST_ANALYZER.md`](./GOLDEN_TEST_ANALYZER.md)).
**Data:** 2026-05-29 (design) · 2026-05-30 (rollout completo step 1-6).
**Metodo:** analisi prodotta con un workflow multi-agent (15 agent: 9 mapper-skill + 2 mapper infra/docs + 1 sintesi + 3 critiche adversariali), poi consolidata con l'utente via 4 decisioni chiave.

---

## Indice

1. [Obiettivo e vincoli](#1-obiettivo-e-vincoli)
2. [Stato attuale: come orchestrano le skill oggi](#2-stato-attuale-come-orchestrano-le-skill-oggi)
3. [Il nodo architetturale e le 3 opzioni](#3-il-nodo-architetturale-e-le-3-opzioni)
4. [Decisioni di progetto](#4-decisioni-di-progetto)
5. [Meccanismo di opt-in](#5-meccanismo-di-opt-in)
6. [I due cerchi: heavy e light](#6-i-due-cerchi-heavy-e-light)
7. [Blueprint per skill (ramo `deep`)](#7-blueprint-per-skill-ramo-deep)
8. [Tensioni risolte](#8-tensioni-risolte)
9. [Convenzioni condivise e invarianti inviolabili](#9-convenzioni-condivise-e-invarianti-inviolabili)
10. [Struttura file in repo](#10-struttura-file-in-repo)
11. [Ordine di costruzione](#11-ordine-di-costruzione)
12. [Capability detection e fallback](#12-capability-detection-e-fallback)
13. [Correzioni rispetto alla bozza (dalle critiche)](#13-correzioni-rispetto-alla-bozza-dalle-critiche)

---

## 1. Obiettivo e vincoli

**Obiettivo.** Quando l'utente usa una skill SDLC deve poter **scegliere** se eseguirla:
- in **modalità classica** (`classic`) — sequenziale, leggera, pochi token; il comportamento attuale;
- in **modalità workflow + approfondita** (`deep`) — orchestrazione parallela multi-agent + verifica adversariale, più lenta e costosa ma più esaustiva.

**Vincoli (dai requisiti + dalle critiche):**

| # | Vincolo | Origine |
|---|---|---|
| V1 | L'utente DEVE poter scegliere (mai escalation silenziosa verso `deep` con spesa a sorpresa). | requisito |
| V2 | Il meccanismo di scelta deve essere **coerente** tra tutte e 9 le skill. | requisito |
| V3 | Deve **degradare con grazia** se il Workflow tool non è disponibile. | requisito |
| V4 | Retrocompatibilità totale: chi non conosce la feature vede il comportamento attuale. | critica UX |
| V5 | Niente doppia-manutenzione incontrollata: la logica `deep` non deve divergere silenziosamente dalla `classic`. | critica rischio |
| V6 | Gli invarianti SDLC (gate utente, no auto-commit sul codice, single-writer sui file source-of-truth) restano inviolati in entrambe le modalità. | critica rischio |

---

## 2. Stato attuale: come orchestrano le skill oggi

Le skill SDLC **non** sono monoblocchi sequenziali: usano già i sottoagenti via il tool `Task`/`Agent`, ma in modo **opportunistico e model-driven** — è il modello a decidere se/quando parallelizzare, senza determinismo né garanzie di barriera.

### 2.1 Il layer agent è già "workflow-ready"

I 5 agent in [`agents/`](../agents) sono prompt-di-sistema riusabili, **read-only**, separati dagli implementatori. Mappano quasi 1:1 sulle primitive del Workflow tool.

| Agent | Ruolo | Unità di… |
|---|---|---|
| [`sdlc-codebase-explorer`](../agents/sdlc-codebase-explorer.md) (`subagent_type: Explore`) | gap analysis doc-vs-codice, 1 per codebase; 3 tabelle (Struttura, Gap per Funzionalità, Discrepanze Terminologiche) | `parallel()` per repo |
| [`sdlc-verifier`](../agents/sdlc-verifier.md) | verifica 3 fasi (A tecnica / B coerenza requisito / C riesame) → verdetto binario PASS/FAIL; non corregge mai | stage *verify* / `adversarial-verify` |
| [`sdlc-estimation-analyst`](../agents/sdlc-estimation-analyst.md) | stima rough dalla doc (pre-analisi) | fan-out finder |
| [`sdlc-estimation-historian`](../agents/sdlc-estimation-historian.md) | calibrazione storica dai plan in `done/` | fan-out per cartella |
| [`sdlc-estimation-scenario`](../agents/sdlc-estimation-scenario.md) | 3 scenari deterministici, invocato iterativamente | loop what-if (deterministico) |

### 2.2 Come le skill li invocano oggi

- **Pattern "prompt-as-file"**: la skill istruisce "leggi `~/.claude/agents/X.md` e lancia un Task con quel prompt" — usato da estimator (analyst/historian/scenario), executor e debug (verifier).
- **Pattern `subagent_type` nativo**: `Explore` in `sdlc-analyzer:324` ("Usa gli agent di tipo `Explore` per parallelizzare l'esplorazione dei diversi codebase"); routing per-stack (`spring-boot-engineer`, `angular-architect`, … fallback `general-purpose`) nei fix di `sdlc-debug`.

### 2.3 Tooling deterministico a parte

Gli script in [`scripts/`](../scripts) (`aggregate-progress.py` (**deprecato**, vedi #4), `bug-template-v2.py`, i migrator, `sync-installed.sh`) sono utility di manutenzione/aggregazione, **non** orchestrazione runtime. **Restano invariati** in entrambe le modalità: cambia solo l'orchestratore che li chiama.

---

## 3. Il nodo architetturale e le 3 opzioni

**Fatto tecnico centrale:** una `SKILL.md` è Markdown iniettato nel main-loop di Claude. **Non** può chiamare `parallel()`/`pipeline()`/`agent({schema})` — quelle sono primitive JS del **Workflow tool**, un orchestratore deterministico separato. Una skill dispone solo del tool `Task`/`Agent` nativo (ritorno testo libero, niente schema validati, niente barriere garantite).

**Ma** una skill **può istruire Claude a invocare il Workflow tool.** La documentazione del Workflow tool elenca esplicitamente tra gli opt-in validi: *"The user invoked a skill whose instructions tell you to call Workflow."* Quindi è il pattern **ufficialmente supportato**.

| | Opzione A — Task fan-out in main-loop | **Opzione C — la skill invoca il Workflow tool** ⭐ | Opzione B — layer workflow separato |
|---|---|---|---|
| **Come** | la prosa dice "lancia più Task nello stesso turno + verifica testuale" | la prosa dice "invoca il Workflow tool con `workflows/<skill>.js`", che fa il vero `parallel`/`pipeline`/`adversarial-verify` con i 5 agentType | orchestratore JS sopra le skill; il flag instrada lì |
| **Garanzie** | nessuna barriera reale, niente schema, niente isolamento → **race sui fix paralleli** | barriere vere, schema validati, **`isolation:'worktree'`** risolve i conflitti file | massime |
| **Sforzo** | minimo (solo prosa) | medio: 1 script JS versionato per skill heavy | alto: riscrittura |
| **Manutenzione** | singola | doppia ma **confinata** (prosa `classic` + script JS), solo skill heavy | doppia totale |

**Decisione: Opzione C** (vedi §4). Il Workflow tool ha già `isolation:'worktree'`, che è la risposta nativa al rischio più grave sollevato dalle critiche (fix paralleli che si pestano su entità/NgModule/barrel condivisi). Il ramo `classic` resta default e fallback.

---

## 4. Decisioni di progetto

Le 4 decisioni chiave prese con l'utente:

| # | Decisione | Scelta |
|---|---|---|
| D1 | **Architettura** | **Opzione C** — la skill resta `classic` di default; in modalità `deep` istruisce Claude a invocare il Workflow tool con uno script per-skill (`workflows/*.js`). |
| D2 | **Scope rollout** | **Tutte e 9 le skill** (coerenza cross-skill totale). Mitigazione YAGNI: vedi §6 (i due cerchi). |
| D3 | **`/effort ultracode` globale** | **Conferma una volta per sessione**: la prima skill SDLC chiede se applicare `deep` a tutte le skill SDLC della sessione, poi lo ricorda. |
| D4 | **Degradazione** | **Banner "COPERTURA RIDOTTA" nell'artefatto** quando si gira/degrada a `classic`: workflow trova *di più*, quindi gli artefatti NON sono equivalenti e va dichiarato. |
| D5 | **Capability detection** | **Assume-disponibile + fallback esplicito**: nessun probe preventivo; se il Workflow tool è assente o l'invocazione fallisce, l'agente principale intercetta e prosegue `classic` con segnalazione rumorosa. Vedi §12. |

---

## 5. Meccanismo di opt-in

Una sezione standard `## Modalità di orchestrazione` viene iniettata in tutte e 9 le `SKILL.md`, subito dopo il blocco condiviso "Risoluzione Path + detection modalità" (lo stesso punto già uniforme tra le skill). L'iniezione avviene con uno script idempotente analogo a [`scripts/dualize-paths.py`](../scripts/dualize-paths.py) — **precedente valido ed esistente**.

### 5.1 Flag persistente (FLAT, non annidato)

In `.sdlc-local.json` (fallback `.br-local.json` per profili legacy). **Flat** per restare compatibile col `grep -oP` già usato nel bootstrap — un oggetto annidato richiederebbe `jq`/python, non garantiti su Git-bash Windows:

```json
{
  "orchestration_mode":  "classic",
  "orchestration_depth": "standard",
  "orchestration_max_concurrency": 10,
  "orchestration_verifier_panel": 3
}
```

Assente ⇒ default `classic` / `standard`.

> **Naming:** si usa `depth` (non `effort`). Il termine `effort` è già di dominio (giorni-uomo)
> ed è usato ~8 volte in `sdlc-estimator` e `sdlc-progress-report`: riusarlo per
> l'orchestrazione creerebbe una collisione UX (due "effort" nella stessa schermata).

### 5.2 Cascata di risoluzione (precedenza)

1. **Flag persistente** (`.sdlc-local.json`) — il "ricordo" per-progetto. **Precedenza più alta tra le sorgenti automatiche.**
2. **Keyword** nel trigger ("a fondo", "esaustivo", "in parallelo", "ultracode") — override per-invocazione, ma **declassata sotto il flag**: una scelta `classic` deliberata non deve essere scavalcata silenziosamente da una parola ambigua. Ogni escalation verso `deep` innescata da keyword **passa da conferma esplicita** (V1).
3. **AskUserQuestion** runtime, quando né flag né keyword hanno deciso — in un punto canonico (vedi §8.1 per il caso executor) + auto-suggeritore (sotto).

**Default globale = `classic`** (V4).

### 5.3 Auto-suggeritore (propone, non forza)

Durante la raccolta input, se la dimensione supera una soglia (es. ≥3 repo, ≥25 task, ondata ≥8 bug, changelog AFU ampio) la AskUserQuestion viene posta **mostrando il razionale** ("rilevati 4 repo: propongo `deep` perché il fan-out su esplorazione codebase ha ROI alto"). La pre-selezione del default resta su `classic` per non indurre spese a sorpresa (V1). Le soglie sono configurabili nel flag.

### 5.4 `/effort ultracode` di sessione (D3)

Se `/effort ultracode` è attivo a livello sessione, la **prima** skill SDLC invocata chiede una volta: *"Applico la modalità workflow+approfondita a tutte le skill SDLC di questa sessione?"*. La risposta è ricordata per la sessione. Evita sia la spesa a sorpresa (auto-eredità cieca) sia la sorpresa opposta (ultracode chiesto ma ignorato).

### 5.5 Banner e degradazione (D4 + V3)

- **Banner di modalità** sempre a video all'avvio del lavoro pesante: *"Eseguo in modalità Workflow+approfondita: ~N agent, più lento/costoso"* oppure *"Modalità classica"*.
- **Capability check**: nessun probe preventivo (assume-disponibile); se l'invocazione del Workflow tool non è possibile o fallisce ⇒ fallback esplicito a `classic` (vedi §12).
- **Banner "COPERTURA RIDOTTA" nell'artefatto** (PLAN/CLARIFY/…): quando l'esecuzione è/diventa `classic`, l'artefatto riporta in testa che è stato prodotto **senza** completeness-critic/adversarial-verify. La degradazione è **rumorosa**, non silenziosa: un gap report è un documento contrattuale verso il team, fingere "stessi artefatti" è il rischio peggiore.

### 5.6 Confronto tra i canali (perché la cascata e non un canale solo)

| Canale | PRO | CONTRO | Ruolo |
|---|---|---|---|
| Flag config | persiste per-progetto, coerente col dual-mode esistente, zero attrito ricorrente | "appiccicoso" per casi atipici; va scoperto | base |
| Keyword trigger | naturale, override puntuale | scoperta scarsa, ambiguo, non persiste | override (con conferma) |
| AskUserQuestion | esplicito, decisione informata | attrito ripetuto, fuori luogo in batch non-interattivi | fallback quando manca il flag |
| Auto-detect | zero attrito | viola V1 se decide da solo | solo suggeritore |

Nessun canale singolo soddisfa V1+V2 da solo; la cascata `flag > keyword(con conferma) > domanda(con suggeritore)` li copre tutti.

---

## 6. I due cerchi: heavy e light

D2 impone l'opt-in su **tutte e 9** (coerenza). Per non violare YAGNI, il **ramo `deep`** ha due pesi:

| Cerchio | Skill | Ramo `deep` |
|---|---|---|
| **Heavy** — script JS dedicato in `workflows/` | `sdlc-analyzer` · `sdlc-executor` · `sdlc-debug` · `sdlc-updater` · `sdlc-reviewer` | vero fan-out + `adversarial-verify` + completeness-critic + `isolation:'worktree'` |
| **Light** — nessuno script pesante | `sdlc-estimator` · `sdlc-clarify` · `sdlc-progress-report` · `sdlc-profile-setup` | solo un **completeness/coherence-critic** (1 sub-step di verifica); stesso flag/banner per coerenza, costo quasi nullo |

Così il cerchio light ha l'opt-in uniforme (V2) senza pagare la doppia manutenzione di uno script JS (V5).

---

## 7. Blueprint per skill (ramo `deep`)

Per ogni skill: dove si applica il fan-out, dove resta sequenziale/stateful, e dove l'approfondimento (ultracode) aggiunge valore reale.

### 7.1 `sdlc-analyzer` — heavy (ROI massimo)

- **Fan-out:** Fase 3.2 esplorazione codebase → `parallel(thunks per repo)` con `agentType:'sdlc-codebase-explorer'` e **barriera** prima della 3.3. In `deep`, fan-out per **layer** (dati/API/servizi/repo/FE/config) = più finder per repo → riduce i falsi "Mancante".
- **Verifica (ultracode):** dopo la sintesi gap, `completeness-critic` (ogni requisito AFU estratto in 3.1 ha una riga in matrice = nessun requisito orfano) + `adversarial-verify` (N scettici cercano controprove alle classificazioni Coperto/Mancante nel codice) + `judge-panel` sul TASKS (auto-sufficienza task, granularità 1-5gg, correttezza merge task `T-MERGE-NNN`).
- **Stateful (mai fan-out):** bootstrap, Fase 1 interattiva, sintesi 3.3, scrittura PLAN→TASKS, commit/push.

### 7.2 `sdlc-executor` — heavy

- **Fan-out:** *dentro una task*, `parallel(thunks)` per i sotto-lavori indipendenti (entità + FE) in **worktree isolati**; `agent()` concatenati per i dipendenti (entità→repository). Verifica → `agent(agentType:'sdlc-verifier')`, potenziata in `deep` ad `adversarial-verify` (panel scettico su Fase B/C: assunzioni nascoste, hardcoded, test che non asseriscono). Loop fix→riverifica = `loop-until-dry`.
- **Stateful:** PROGRESS.md (pull→edit→commit→push serializzato), spostamenti todo/in-progress/done, merge task, branch-prima-di-impl, **tutti i gate di conferma** (vedi §8.1 per la risoluzione gate vs barriera).

### 7.3 `sdlc-debug` — heavy

- **Fan-out:** Fase 1 import → `pipeline(bugs, classify, link-to-task, suggest-owner)`; Fase 2 root-cause → `parallel` di explorer read-only per bug; Fase 2 fix → `parallel` di fix su **file/aree disgiunte** con routing per-stack e **`isolation:'worktree'`**, gating su conflitti.
- **Verifica (ultracode):** `adversarial-verify`/`judge-panel` su `sdlc-verifier` (prezioso per bug `critico`). Loop fix→verifica = `loop-until-dry`.
- **Stateful:** BUG_REPORT.md (source of truth, append non replace), commit/push, ID sequenziali al re-import, dedup per `id_originale`, counter chiusura `bug_tecnici`/`bug_funzionali`. Validazione funzionale (Fase 3) resta **umana**.

### 7.4 `sdlc-updater` — heavy

- **Fan-out:** classificazione delta + gap-check su codice → `pipeline`/`parallel` di explorer per repo.
- **Verifica (ultracode):** `completeness-critic` sul **delta** (il rischio grave è un requisito modificato/rimosso non rilevato; sanity-check incrociato con `manifest.changelog`) + `adversarial-verify` sui MODIFICATO che ricadono su task **già Completate** (falso "invariato" = lavoro perso; falso "modificato" = T-fix inutili).
- **Stateful:** scrittura PLAN→TASKS→PROGRESS single-writer; mai sovrascrivere progresso, mai cancellare.

### 7.5 `sdlc-reviewer` — heavy

- **Fan-out:** analisi documenti → `parallel` per documento (schema `problemi[]={categoria,bloccante,dove,impatto,domanda}`); check vs codice → `parallel` di explorer per repo/area.
- **Verifica (ultracode):** `completeness-critic` + `adversarial-verify` (N scettici cercano bloccanti/ambiguità mancati, rileggono i doc con lenti diverse: regole business, eccezioni, terminologia) + `judge-panel` sulle assunzioni di Parte 2 ("è davvero non-bloccante?").
- **Stateful:** sintesi con ID univoci A-XXX/D-XXX, scrittura CLARIFY.md single-file, DOCX, commit/push.

### 7.6 Cerchio light (solo coherence-critic)

- **`sdlc-estimator`:** valore confinato a historian (calibrazione, fan-out per cartella `done/`) e analyst (rough, multi-finder sulla doc AFU). **I 3 scenari restano deterministici** (Regola "niente random"): non si parallelizzano in modo da introdurre variabilità.
- **`sdlc-clarify`:** opzionale; in `deep` un finder sull'estrazione risposte ambigue (diff/DOCX) + `adversarial-verify` **solo** sulle assunzioni "rigettata" (un rigetto errato inietta un fatto sbagliato in sdlc-analyzer). Il fan-out **classifica, non riscrive** le risposte (Regola verbatim).
- **`sdlc-progress-report`:** valore = solo `completeness-critic` di coerenza-dati (ogni riga TASKS mappata? stati PROGRESS riconciliati? somme per-wave coerenti tra i 3 fogli?). Nessun fan-out pesante.
- **`sdlc-profile-setup`:** in `deep`, auto-detect multi-repo con explorer in modalità "senza profilo" + `completeness-critic` sul PROFILE prima della conferma (un CONST/PROFILE sbagliato è ereditato da TUTTE le altre 8 skill). **Eccezione:** non carica CONST+PROFILE all'avvio (li crea), quindi il flag va letto da `.sdlc-local.json` se esiste, altrimenti via AskUserQuestion dopo lo Step MODE.

---

## 8. Tensioni risolte

### 8.1 executor — gate-per-substep vs barriera-fine-wave

Il fan-out parallelo si applica alla **fase implementazione+verifica dei sotto-lavori *dentro una task*** (in worktree isolati). I **gate umani e il commit restano serializzati a valle, una task alla volta**. NON si parallelizzano N task con commit sospesi in N aree. Si guadagna sul lavoro *interno* alla task senza perdere la Regola "mai auto-commit sul codice" e "mai procedere senza conferma".

### 8.2 Fallimento parziale della barriera

Regola esplicita: se k/N agent falliscono (timeout/budget/errore), lo script ritorna i k riusciti come **proposte non applicate**. Il single-writer (PROGRESS/BUG_REPORT/CLARIFY) **non scrive nulla parzialmente**; l'agente principale presenta lo stato e l'utente decide. Niente stato misto sui file source-of-truth.

### 8.3 Riproducibilità dei verdetti adversariali

L'output `deep` è **additivo e segnalato** (banner copertura), non sostituisce in modo silenzioso la classifica single-pass. Per `sdlc-estimator` gli scenari restano **deterministici**: l'adversarial tocca solo calibrazione/scope, mai il calcolo. Dove un panel può divergere (Coperto/Mancante), va definita una regola di riconciliazione (es. maggioranza ≥2/3; in pareggio prevale la classificazione più conservativa "Da chiarire").

### 8.4 Conflitti file nei fix paralleli

`isolation:'worktree'` del Workflow tool: ogni fix in una copia isolata del repo, merge controllato a valle. Risolve il rischio "due fix toccano lo stesso barrel/NgModule/entità condivisa" senza assumere a priori una disgiunzione che spesso non regge.

---

## 9. Convenzioni condivise e invarianti inviolabili

**Blocco standard** iniettato in ogni `SKILL.md` (risoluzione flag → capability check → banner → degrado). Mapping di fallback `deep`→`classic` per ogni primitiva:

| Primitiva `deep` | Fallback `classic` |
|---|---|
| `parallel`/`pipeline` | loop sequenziale sugli stessi thunk (comportamento attuale) |
| `agent({agentType,schema})` | "leggi `~/.claude/agents/<agentType>.md` e lancia un Task" + parsing MD |
| `adversarial-verify`/`judge-panel` | singola verifica `sdlc-verifier` inline |
| `completeness-critic` | checklist manuale già presente |
| `loop-until-dry` | ciclo fix/riverifica già descritto |

**Invarianti inviolabili in ENTRAMBE le modalità (V6):**
1. Tutti i gate di conferma utente ("mai procedere senza conferma").
2. Mai auto-commit sulle repo di **codice**.
3. Il sottoagente implementa, l'agente principale coordina.
4. Scritture sui file source-of-truth (PROGRESS, BUG_REPORT, CLARIFY, PLAN/TASKS) sempre single-writer serializzato (pull→edit→commit→push).
5. Gli agent di verifica/esplorazione restano read-only.
6. Barriere obbligatorie dove la fase a valle richiede lo stato completo (prima della gap-synthesis, tra wave, prima della presentazione unica dell'auto-detect).

**Note di naming:** gli `agentType` coincidono con i 5 file in `agents/`. I "ruoli" di verifica (`completeness-critic`, `adversarial-verifier`, `judge`) sono **alias/parametri** di `sdlc-verifier` istanziato N volte con prompt scettici, **non** nuovi file `.md` (no moltiplicazione dei prompt). Gli schema JSON vivono **negli script `workflows/*.js`**, non nel frontmatter degli agent (lì sarebbero ignorati dal tool Task).

---

## 10. Struttura file in repo

```
claude-flow/
├── workflows/                          ← NUOVO: uno script per skill heavy
│   ├── sdlc-analyzer-gap.js
│   ├── sdlc-executor-wave.js
│   ├── sdlc-debug-fixwave.js
│   ├── sdlc-updater-delta.js
│   └── sdlc-reviewer-quality.js
├── agents/                             ← INVARIATI (= gli agentType degli script)
├── scripts/
│   ├── inject-orchestration.py         ← NUOVO: inietta il blocco opt-in nelle 9 SKILL.md (idempotente)
│   └── sync-installed.sh               ← AGGIORNATO: deploya anche workflows/
├── skills/sdlc-*/SKILL.md              ← + sezione "## Modalità di orchestrazione"
└── docs/ORCHESTRATION_INTEGRATION_DESIGN.md   ← questo documento
```

`.sdlc-local.json` (nella repo applicativa del developer) → + i 4 campi `orchestration_*` flat.

---

## 11. Ordine di costruzione

Nonostante D2 ("tutte e 9"), il rollout **valida prima su una skill** per accorgersi di eventuali divergenze tra i due rami prima di moltiplicarle ×9.

1. ✅ **`sdlc-profile-setup`** *(fatto 2026-05-30)*: estendere `.sdlc-local.json` col flag + default `classic` → posto canonico da cui le altre leggono.
2. ✅ **`inject-orchestration.py`** + aggiornare `sync-installed.sh` *(fatto 2026-05-30)*: blocco opt-in in tutte e 9 (coerenza by-construction) + mapping di degrado uniforme. Lo script supporta `--replace` per ri-sincronizzare il blocco senza divergenza fonte/artefatti (V5).
3. 🔧 **Pilota `sdlc-analyzer`** *(strumenti pronti 2026-05-30; golden-test run SALTATO per decisione utente)*: `workflows/sdlc-analyzer-gap.js`, ramo `deep` in §3.2/§3.3/Fase 4, comparatore `scripts/golden-compare-gap.py`. Il **golden-test `classic` vs `deep`** resta facoltativo (vedi [`GOLDEN_TEST_ANALYZER.md`](./GOLDEN_TEST_ANALYZER.md)).
4. ✅ **`sdlc-executor` + `sdlc-debug`** *(fatto 2026-05-30)*: `workflows/sdlc-executor-wave.js` + `sdlc-debug-fixwave.js` (worktree + sdlc-verifier panel; contratto patch→git apply).
5. ✅ **`sdlc-updater` + `sdlc-reviewer`** *(fatto 2026-05-30)*: `workflows/sdlc-updater-delta.js` + `sdlc-reviewer-quality.js` (gap/delta + judge-panel).
6. ✅ **Cerchio light** *(fatto 2026-05-30)*: estimator/clarify/progress-report/profile-setup — solo coherence-critic, nessun JS.

> Il golden-test allo step 3 era la difesa contro il rischio V5. **È stato saltato per decisione utente** (costo token del run): in sostituzione, ogni workflow ha superato una **review adversariale statica** (lettura, non esecuzione). Resta che la divergenza `classic` vs `deep` non è stata misurata empiricamente su un input reale — il run del golden-test è la verifica raccomandata prima di affidarsi alla modalità `deep` in produzione.

---

## 12. Capability detection e fallback

**Decisione (D5): assume-disponibile + fallback esplicito.** Il ramo `deep` **non** esegue un probe preventivo del Workflow tool: procede assumendolo presente e ne istruisce l'invocazione. Se l'invocazione **non è possibile** (il Workflow tool non è nel set di tool disponibili) **oppure fallisce/non completa**, l'agente principale **intercetta esplicitamente** la condizione e prosegue nel ramo `classic`, con segnalazione rumorosa (V3 + D4):

1. banner a video: *"Workflow tool non disponibile: eseguo in modalità classica sequenziale"*;
2. banner **"COPERTURA RIDOTTA"** nell'artefatto (prodotto senza completeness-critic/adversarial-verify).

Perché questa e non il probe esplicito: evita un check fragile e non-deterministico a monte (un LLM che "prova" una primitiva e deve "capire" se è fallita), ed elimina un passo extra nel caso normale (tool presente). Il blocco standard iniettato (§9) contiene l'istruzione di fallback in prosa, **uniforme tra le 9 skill**.

> **Distinzione importante.** Questo fallback riguarda il Workflow tool **assente o che non parte**. È diverso dal **fallimento parziale della barriera** (§8.2), in cui il workflow *parte e gira* ma k/N agent falliscono: lì valgono le regole di §8.2 (proposte non applicate, single-writer non scrive parzialmente). Il blocco standard deve gestire **entrambi** i casi.

---

## 13. Correzioni rispetto alla bozza (dalle critiche)

La bozza iniziale è stata sottoposta a 3 critiche adversariali (coerenza-UX, fattibilità-tecnica, rischio-degradazione). Correzioni recepite in questo design:

| Rilievo | Correzione |
|---|---|
| `orchestration.effort` collide col termine dominio "effort" (giorni-uomo) | rinominato `depth` (§5.1) |
| Una `SKILL.md` non può chiamare `parallel()`/`agent({schema})` | architettura Opzione C: la skill **invoca il Workflow tool**; gli schema vivono negli script JS (§3, §9) |
| `schema` nel frontmatter `.md` non è onorato dal tool Task | confermato: schema solo negli script `workflows/*.js` (§9) |
| Keyword scavalca il flag → spesa a sorpresa | keyword declassata sotto il flag; escalation con conferma (§5.2) |
| Degradazione "silenziosa, stessi artefatti" è contraddittoria | degradazione **rumorosa**, banner copertura nell'artefatto (§5.5, D4) |
| Gate per-substep vs barriera-fine-wave | risolto: fan-out *interno* alla task, gate/commit serializzati a valle (§8.1) |
| Fallimento parziale della barriera lascia stato misto | proposte non applicate, single-writer non scrive parzialmente (§8.2) |
| File-disgiunti non garantiti | `isolation:'worktree'` (§8.4) |
| Oggetto `orchestration{}` annidato non parsabile col `grep -oP` | flag **flat** (§5.1) |
| `/effort ultracode` globale non risolto | conferma una volta per sessione (§5.4, D3) |
| Sovra-ingegnerizzazione skill leggere | due cerchi: light = solo coherence-critic (§6) |
| Divergenza dei due path non rilevabile | golden-test allo step 3 del rollout (§11) |
| *Errata corrige critica:* "`dualize-paths.py` non esiste" | **esiste** in `scripts/dualize-paths.py`: precedente di iniezione valido (§5) |
