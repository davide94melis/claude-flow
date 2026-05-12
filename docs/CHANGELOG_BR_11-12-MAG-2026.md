# Changelog BR Skills — 11-12 Maggio 2026

Riepilogo completo di tutte le modifiche e aggiunte alla suite BR Skills di claude-flow e portal-flow nelle giornate dell'11 e 12 maggio 2026.

---

## Numeri complessivi

| Metrica | Valore |
|---|---|
| Commit claude-flow | 23 |
| Commit portal-flow | 7 |
| File nuovi | ~20 |
| File modificati | ~15 |
| Righe aggiunte (claude-flow) | ~7.400 |
| Righe aggiunte (portal-flow) | ~4.600 |
| Skill nuove | 3 (br-debug, br-profile-setup, br-estimator) |
| Agenti nuovi | 5 (br-codebase-explorer, br-verifier, br-estimation-analyst, br-estimation-historian, br-estimation-scenario) |
| Skill modificate | 6 (br-reviewer, br-analyzer, br-executor, br-updater, br-pipeline, br-debug) |

---

## 11 Maggio 2026

### 1. Verifica 3 fasi in br-executor

**Commit:** `d3a781d`

Aggiunta la verifica obbligatoria in 3 fasi al lavoro dei sottoagenti in `br-executor`:
- **Fase A** — Verifica tecnica: test, build, copertura edge case
- **Fase B** — Verifica di coerenza col requisito: ogni requisito mappato al codice
- **Fase C** — Riesame finale (second look): rilettura completa, assunzioni nascoste, nomi e convenzioni

Aggiunta tabella di verifica finale con mapping requisito → file → test prima di dichiarare una task completata.

### 2. Aggiornamento BR_SKILLS_DOCUMENTATION.md

**Commit:** `0bec68c`

Aggiunta la sezione pipeline e la documentazione della verifica 3 fasi alla documentazione centrale.

### 3. br-debug — Nuova skill

**Commit:** `4c09ac8`

Skill completamente nuova per la gestione del ciclo di vita dei bug segnalati dal testing funzionale:
- **Import** da Excel o Jira (con normalizzazione)
- **Assegnazione** automatica ai dev in base all'area e alla complessita'
- **Fix** con sottoagenti dedicati (uno per bug)
- **Verifica 3 fasi** (stesse fasi di br-executor)
- **Chiusura** con validazione funzionale e re-import iterativo
- Integrazione con `manifest.bugs` in portal-flow

File: `skills/br-debug/SKILL.md` (757 righe)

### 4. Agenti generici profilo-aware — Design + Implementazione

**Commit:** `411a1bc` → `75224d3` (12 commit)

Blocco principale della giornata: progettazione e implementazione di agenti generici e profili progetto.

#### 4a. Agente br-codebase-explorer

File: `agents/br-codebase-explorer.md` (218 righe)

Esploratore di codebase profilo-aware. Riceve un profilo progetto e naviga il codice in modo mirato, producendo output strutturato per la gap analysis. Usato da `br-analyzer` e `br-updater`.

#### 4b. Agente br-verifier

File: `agents/br-verifier.md` (137 righe)

Verificatore in 3 fasi profilo-aware. Produce verdict PASS/FAIL strutturato usando le convenzioni dal profilo progetto. Usato da `br-executor` e `br-debug`.

#### 4c. Profili progetto integrati in tutte le skill

Ogni skill esistente e' stata modificata per caricare e usare il profilo progetto:

| Skill | Modifiche |
|---|---|
| **br-reviewer** | Carica profilo, check terminologico arricchito con glossario del dominio |
| **br-analyzer** | Carica profilo, usa br-codebase-explorer per gap analysis profilo-aware |
| **br-executor** | Carica profilo, routing a specialist (es. `spring-boot-engineer`), usa br-verifier |
| **br-updater** | Carica profilo, usa br-codebase-explorer per analisi delta |
| **br-debug** | Carica profilo, routing a specialist, usa br-verifier |
| **br-pipeline** | Mostra info progetto nell'header della dashboard |

#### 4d. Routing a specialist

Con profilo configurato, `br-executor` e `br-debug` instradano i sottoagenti al `subagent_type` appropriato in base al tech stack del progetto:
- Spring Boot → `spring-boot-engineer`
- Angular → `angular-architect`
- Senza profilo → `general-purpose` (retrocompatibilita')

#### 4e. br-profile-setup — Nuova skill

File: `skills/br-profile-setup/SKILL.md` (381 righe)

Creazione guidata di un profilo progetto in 10 step:
1. Nome progetto
2. Path repo profili centralizzato (`deloitte-profiles`)
3. Codebase coinvolti
4. Auto-detect framework, convenzioni, design system (con sottoagenti paralleli)
5. Conferma e correzione manuale
6. Domande dominio (glossario, regole di business, stati/transizioni)
7. Reference files opzionali
8. Generazione `profile.json`
9. Commit + push su `deloitte-profiles`
10. Aggiornamento `.br-local.json` nei codebase

---

## 12 Maggio 2026

### 5. br-estimator — Design

**Commit:** `ef11200`

Design spec per la skill di stima team e simulazioni what-if:
- Modello ibrido deterministico + rischio con 3 scenari
- Simulazione giorno per giorno con assegnazione task per area e seniority
- Ciclo what-if interattivo
- Scope cutting con effetto cascata sulle dipendenze

File: `docs/superpowers/specs/2026-05-11-br-estimator-design.md` (420 righe)

### 6. br-estimator — Implementazione completa

**Commit:** `d6e33d1` → `18c3ef0` (7 commit)

#### 6a. Tre agenti di stima

| Agente | File | Righe | Ruolo |
|---|---|---|---|
| br-estimation-analyst | `agents/br-estimation-analyst.md` | 102 | Stima rough dalla documentazione: estrae funzionalita', stima task, complessita', rischio e area |
| br-estimation-historian | `agents/br-estimation-historian.md` | 106 | Calibrazione storica: scansiona BR completati, calcola fattore di correzione |
| br-estimation-scenario | `agents/br-estimation-scenario.md` | 166 | Simulazione scenari: timeline giorno per giorno, bottleneck, allocazione team, scope cutting |

#### 6b. Skill br-estimator

File: `skills/br-estimator/SKILL.md` (326 righe)

Due modalita':
- **Rough** (pre-analisi) — dalla documentazione BR, precisione ±30-40%
- **Dettagliata** (post-analisi) — dal piano di implementazione, precisione ±10-15%

5 fasi operative:
1. Raccolta input (BR, deadline, team, parametri)
2. Esecuzione stima (analista + storico in parallelo, poi scenarista)
3. Presentazione 3 scenari (ottimistico/realistico/pessimistico)
4. Ciclo what-if (aggiungi/rimuovi dev, cambia deadline, taglia scope, cambia parametri)
5. Generazione report (STIMA_BR.md + STIMA_BR.xlsx con 4 fogli)

#### 6c. Integrazione pipeline

Azione opzionale nella dashboard TL/PM in entrambe le pipeline:
- Dopo review/clarify: "Stima team (rough)"
- Dopo analyze/approved/execute: "Stima team (dettagliata)"

#### 6d. Documentazione

- `BR_SKILLS_DOCUMENTATION.md` — sezione 12 con sottoagenti, scenari, what-if, output
- `README.md` — skill + 3 agenti + trigger block
- `~/.claude/CLAUDE.md` — trigger globale registrato

---

## Portal-flow — Allineamento

Tutte le nuove skill e modifiche sono state replicate in portal-flow:

| Skill/File | Azione |
|---|---|
| `skill/br-debug/` | SKILL.md + install.sh creati |
| `skill/br-profile-setup/` | SKILL.md + install.sh creati |
| `skill/br-estimator/` | SKILL.md + install.sh creati |
| `skill/br-pipeline/SKILL.md` | Aggiunta integrazione profilo, debug, estimator |

---

## Stato finale della suite

### Skill (10)

| # | Skill | Path |
|---|---|---|
| 1 | br-reviewer | `skills/br-reviewer/` |
| 2 | br-clarify | `skills/br-clarify/` |
| 3 | br-analyzer | `skills/br-analyzer/` |
| 4 | br-executor | `skills/br-executor/` |
| 5 | br-updater | `skills/br-updater/` |
| 6 | br-progress-report | `skills/br-progress-report/` |
| 7 | br-debug | `skills/br-debug/` |
| 8 | br-profile-setup | `skills/br-profile-setup/` |
| 9 | br-estimator | `skills/br-estimator/` |
| 10 | br-pipeline | `skills/br-pipeline/` |

### Agenti generici (5)

| # | Agente | Path |
|---|---|---|
| 1 | br-codebase-explorer | `agents/br-codebase-explorer.md` |
| 2 | br-verifier | `agents/br-verifier.md` |
| 3 | br-estimation-analyst | `agents/br-estimation-analyst.md` |
| 4 | br-estimation-historian | `agents/br-estimation-historian.md` |
| 5 | br-estimation-scenario | `agents/br-estimation-scenario.md` |

### Flusso completo

```
BR / Documentazione
        |
        v
  [br-reviewer]          ←── profilo-aware (glossario, check terminologico)
        |
        v
  [br-clarify]           ←── gestione risposte funzionale
        |
        v                        ┌─────────────────────────┐
  [br-analyzer]          ←──────│ br-codebase-explorer    │ profilo-aware
        |                        │ (gap analysis mirata)    │
        v                        └─────────────────────────┘
  [br-estimator]         ←── 3 agenti: analyst + historian + scenario
        |                     3 scenari + what-if + Excel
        |
        v                        ┌─────────────────────────┐
  [br-executor]          ←──────│ br-verifier             │ profilo-aware
        |                        │ (verifica 3 fasi)        │
        |                        │ routing a specialist     │
        v                        └─────────────────────────┘
  [br-debug]             ←── import bug, fix con sottoagenti, verifica 3 fasi
        |
        v
  [br-progress-report]   ←── Excel con avanzamento per sviluppatore
        |
        v
  [br-pipeline]          ←── orchestratore unico, dashboard per ruolo
        |
  [br-updater]           ←── aggiornamento incrementale piano
  [br-profile-setup]     ←── creazione guidata profilo progetto
```
