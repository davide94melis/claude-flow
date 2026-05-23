# Roadmap Nuove Skill Claude-Flow

## Contesto

Analisi del pipeline SDLC attuale e identificazione dei gap nel ciclo di vita dei Piani (ex Business Requirement / nuovo termine: AFU per il documento input, Piano per l'unità di lavoro). Le skill proposte sono complementari a quelle esistenti e coprono sia il lato funzionale che tecnico/deploy.

## Pipeline Attuale

```
AFU arriva → sdlc-reviewer → sdlc-clarify → sdlc-analyzer → sdlc-estimator → sdlc-executor → sdlc-progress-report → sdlc-debug → sdlc-updater
                                                                                                              ↑
                                                                                                    sdlc-pipeline (orchestratore)
```

## Gap Identificati

### Lato Funzionale

Il team funzionale (BA, PM) oggi non ha strumenti strutturati all'interno del pipeline per:
- Preparare piani di test/UAT prima dello sviluppo
- Generare documentazione di rilascio per il cliente
- Valutare l'impatto di un nuovo Piano (derivato da una nuova AFU) su Piani precedenti o in corso

### Lato Tecnico/Deploy

- Nessuna checklist automatica per il deploy in ambiente bancario
- Nessun collegamento formale requisito → codice → test → bug

---

## Skill Proposte

### 1. `sdlc-test-plan` — Generazione Piano di Test/UAT

**Priorita'**: 1 (alta)
**Posizione nel pipeline**: dopo `sdlc-analyzer`, prima di `sdlc-executor`
**Destinatari**: team funzionale

**Problema**: il funzionale testa ad-hoc dopo lo sviluppo e riporta bug via `sdlc-debug`. Non esiste un piano di test strutturato pre-sviluppo, il che porta a bug trovati tardi e disallineamento tra aspettative funzionali e implementazione tecnica.

**Cosa fa**:
- Legge la documentazione AFU e il gap report di `sdlc-analyzer`
- Genera scenari di test per ogni funzionalita' dell'AFU
- Struttura ogni scenario con: pre-condizioni, passi, risultato atteso, dati di test suggeriti
- Distingue tra test funzionali, test di regressione e test edge-case
- Produce output in formato Excel (per il funzionale) e MD (per gli sviluppatori)

**Output**:
- `TEST_PLAN_BR_<nome>.xlsx` — piano di test per il team funzionale
- `TEST_PLAN_BR_<nome>.md` — versione markdown per gli sviluppatori

**Integrazione con skill esistenti**:
- Legge il gap report e piano da `sdlc-analyzer`
- I risultati dei test alimentano `sdlc-debug` (segnalazione bug strutturata)
- `sdlc-updater` aggiorna il test plan quando l'AFU cambia

---

### 2. `sdlc-release-notes` — Generazione Note di Rilascio

**Priorita'**: 2 (alta)
**Posizione nel pipeline**: dopo completamento Piano o a fine sprint/wave
**Destinatari**: PM, cliente

**Problema**: a fine sprint nessuno genera un documento strutturato di cosa e' cambiato. Il PM compila manualmente le note per lo sprint review e la comunicazione al cliente.

**Cosa fa**:
- Legge i piani completati, il file di progresso e la git history dei Piani chiusi nello sprint
- Aggrega le modifiche per area funzionale (non per repo/file)
- Classifica: nuove funzionalita', miglioramenti, bug fix, breaking changes
- Genera note per il deploy (configurazioni, script DB, attenzioni)
- Produce output leggibile dal cliente (non tecnico)

**Output**:
- `RELEASE_NOTES_<sprint>.md` — note di rilascio per il cliente
- `RELEASE_NOTES_<sprint>.xlsx` — versione Excel per PM

**Integrazione con skill esistenti**:
- Legge progresso da `sdlc-progress-report`
- Legge bug chiusi da `sdlc-debug`
- Legge piani da `sdlc-analyzer`

---

### 3. `sdlc-impact-analysis` — Analisi Impatto Cross-Piano

**Priorita'**: 3 (media-alta)
**Posizione nel pipeline**: prima di `sdlc-analyzer`, appena arriva l'AFU
**Destinatari**: TL, PM

**Problema**: quando arriva una nuova AFU, non c'e' analisi strutturata di cosa tocca rispetto ai Piani precedenti o in corso. Con entita' complesse (PSM con 26+ eventi, moduli interconnessi Agency Desk/Post-Closing/GenAI), il rischio di conflitto e regressione e' alto.

**Cosa fa**:
- Legge la documentazione della nuova AFU
- Scansiona i manifest dei Piani attivi/completati in `plans/`
- Identifica entita'/moduli in comune
- Mappa le dipendenze tra Piani (stesso controller, stessa tabella, stesso enum)
- Valuta rischio di conflitto (BASSO/MEDIO/ALTO) per ogni sovrapposizione
- Suggerisce ordine di lavorazione e precauzioni

**Output**:
- `IMPACT_ANALYSIS_BR_<nome>.md` — report impatto con matrice di sovrapposizione

**Integrazione con skill esistenti**:
- Si posiziona prima di `sdlc-analyzer` nel pipeline
- `sdlc-pipeline` mostra l'impatto nella dashboard
- Alimenta le stime di `sdlc-estimator` (rischio piu' alto = effort maggiore)

---

### 4. `sdlc-deploy-checklist` — Checklist di Deploy

**Priorita'**: 4 (media)
**Posizione nel pipeline**: dopo `sdlc-executor`, prima del rilascio
**Destinatari**: TL, DevOps

**Problema**: il deploy in ambiente bancario (ISP) e' delicato. Non esiste una checklist automatica che elenchi cosa serve per rilasciare un Piano.

**Cosa fa**:
- Analizza il piano e il codice implementato
- Identifica: script DB da eseguire, nuove variabili d'ambiente, configurazioni da aggiornare, nuove dipendenze
- Determina l'ordine di deploy dei microservizi (GA → BE → EM → DM → FE)
- Segnala breaking change che richiedono coordinamento
- Genera checklist con checkbox per tracciare l'esecuzione

**Output**:
- `DEPLOY_CHECKLIST_BR_<nome>.md` — checklist di deploy

**Integrazione con skill esistenti**:
- Legge piano e progresso da `sdlc-analyzer` / `sdlc-executor`
- Complementare a `sdlc-release-notes`

---

### 5. `sdlc-traceability` — Matrice di Tracciabilita'

**Priorita'**: 5 (bassa)
**Posizione nel pipeline**: consultabile in qualsiasi momento, aggiornata automaticamente
**Destinatari**: PM, audit/compliance

**Problema**: nessun collegamento formale tra requisiti dell'AFU, codice modificato, test case e bug. In ambito bancario la tracciabilita' e' importante per audit e compliance.

**Cosa fa**:
- Costruisce e mantiene una matrice che collega: requisito AFU → task del Piano → file modificati → test case (da `sdlc-test-plan`) → bug (da `sdlc-debug`)
- Evidenzia requisiti non coperti da test
- Evidenzia requisiti con bug aperti
- Aggiornata automaticamente dalle altre skill

**Output**:
- `TRACEABILITY_MATRIX_BR_<nome>.xlsx` — matrice di tracciabilita'
- `TRACEABILITY_MATRIX_BR_<nome>.md` — versione markdown

**Integrazione con skill esistenti**:
- Alimentata da `sdlc-analyzer`, `sdlc-test-plan`, `sdlc-executor`, `sdlc-debug`
- Consultabile da `sdlc-pipeline`

---

## Ordine di Sviluppo Suggerito

| Fase | Skill | Effort stimato | Dipendenze |
|------|-------|---------------|------------|
| 1 | `sdlc-test-plan` | Medio | sdlc-analyzer (lettura gap report) |
| 2 | `sdlc-release-notes` | Basso | sdlc-progress-report, sdlc-debug (lettura dati) |
| 3 | `sdlc-impact-analysis` | Medio-alto | sdlc-pipeline (lettura manifest Piano) |
| 4 | `sdlc-deploy-checklist` | Basso-medio | sdlc-executor (lettura piano/progresso) |
| 5 | `sdlc-traceability` | Alto | tutte le altre skill (integrazione bidirezionale) |

## Note

- Tutte le skill leggono il `profile.json` da deloitte-profiles per il contesto di dominio
- Il formato output Excel e' coerente con `sdlc-progress-report` per uniformita'
- Ogni skill si integra nel `sdlc-pipeline` come stage aggiuntivo nel manifest
- La `sdlc-traceability` e' la piu' complessa perche' richiede integrazione bidirezionale con tutte le altre skill — da sviluppare per ultima
