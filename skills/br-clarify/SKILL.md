---
name: br-clarify
description: Gestisce le risposte del team funzionale alle domande sollevate in REVIEW_BR.md da br-reviewer. Aggiorna il report con le risposte ricevute, ri-valuta bloccanti e assunzioni, e rigenera il DOCX. Supporta risposte via DOCX compilato o conversazione diretta, e puo' essere eseguita piu' volte per risposte parziali. Usa questa skill quando l'utente dice "chiarimenti ricevuti", "risposte ricevute", "aggiorna con i chiarimenti", "il funzionale ha risposto", "ho le risposte", "risposte al review", o qualsiasi variazione che implichi la ricezione di risposte dal team funzionale alle domande del review BR.
---

# BR Clarify — Risposte del Funzionale e Aggiornamento Review

Questa skill si posiziona tra `br-reviewer` e `br-analyzer` nel flusso BR. Riceve le risposte del team funzionale alle domande sollevate nel REVIEW_BR.md, aggiorna il report, ri-valuta bloccanti e assunzioni, e rigenera il DOCX.

Il flusso BR completo:
```
br-reviewer → br-clarify → br-analyzer → br-executor → br-updater
                                                      ↘ br-progress-report
```

Questa skill puo' essere eseguita **piu' volte** sullo stesso REVIEW_BR.md: ogni esecuzione aggiunge le nuove risposte senza sovrascrivere quelle gia' registrate. Questo supporta lo scenario tipico in cui il funzionale risponde a domande diverse in momenti diversi.

Il processo si compone di 6 fasi:
1. **Auto-detect** (trova il REVIEW_BR.md)
2. **Modalita' input** (DOCX compilato o conversazione)
3. **Acquisizione risposte** (raccolta e conferma)
4. **Rivalutazione** (aggiorna bloccanti e assunzioni)
5. **Aggiornamento REVIEW_BR.md** (integra risposte e rigenera DOCX)
6. **Riepilogo** (stato aggiornato per l'utente)

---

## Risoluzione Path — deloitte-profiles

Tutte le operazioni su file BR avvengono nella repo `deloitte-profiles`, non nella repo del codice.

### Lettura `.br-local.json`

All'avvio, leggi `.br-local.json` dalla root della repo corrente:

```bash
cat .br-local.json 2>/dev/null
```

Estrai `profiles_repo`, `profilo`, `developer`.

Il **base path** per gli artefatti BR e': `<profiles_repo>/<profilo>/plans/`

### Se `.br-local.json` non esiste

Ferma l'esecuzione e avvisa:

> `.br-local.json` non trovato. Devi prima eseguire `br-profile-setup`.

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

## Fase 1 — Auto-detect REVIEW_BR.md

Cerca automaticamente il report del review nella struttura `plans/` centralizzata:

```bash
git -C "<profiles_repo>" pull origin main --quiet
ls "<profiles_repo>/<profilo>/plans/todo"/*/REVIEW_BR.md 2>/dev/null
ls "<profiles_repo>/<profilo>/plans/in-progress"/*/REVIEW_BR.md 2>/dev/null
```

**Se trovi un solo REVIEW_BR.md**, proponilo:

> Ho trovato il review del BR:
> - `<profiles_repo>/<profilo>/plans/todo/2026-04-28_monitoraggio/REVIEW_BR.md`
>
> Uso questo?

**Se ne trovi piu' di uno**, elenca e chiedi:

> Ho trovato piu' review:
> - `<profiles_repo>/<profilo>/plans/todo/2026-04-28_monitoraggio/REVIEW_BR.md`
> - `<profiles_repo>/<profilo>/plans/todo/2026-04-25_booking-v2/REVIEW_BR.md`
>
> Quale vuoi aggiornare?

**Se non ne trovi nessuno**, informa:

> Non ho trovato nessun REVIEW_BR.md nella struttura `<profiles_repo>/<profilo>/plans/`.
> Devi prima eseguire `br-reviewer` per generare il report con le domande.

Dopo l'identificazione, leggi il REVIEW_BR.md e analizza la sua struttura:
- Conta i **problemi bloccanti** e quanti gia' hanno "Risposta del funzionale"
- Conta i **problemi non bloccanti** e quanti gia' hanno risposta
- Identifica le **assunzioni proposte** e il loro stato
- Calcola quante domande sono ancora **aperte** (senza risposta)

Presenta il riepilogo:

> Stato attuale del review:
> - Problemi bloccanti: N totali (X con risposta, Y ancora aperti)
> - Problemi non bloccanti: N totali (X con risposta, Y ancora aperti)
> - Domande totali ancora aperte: **Z**
>
> Procedo con l'acquisizione delle risposte?

Se tutte le domande hanno gia' risposta:

> Tutte le domande hanno gia' ricevuto risposta.
> Se vuoi aggiornare una risposta specifica, dimmelo. Altrimenti il review e' completo e puoi procedere con `br-analyzer`.

---

## Fase 2 — Modalita' Input

Chiedi come arrivano le risposte:

> Come arrivano le risposte del funzionale?
>
> 1. **DOCX compilato** — il funzionale ha compilato il REVIEW_BR.docx inserendo le risposte sotto ogni domanda
> 2. **Te le dico io** — ho le risposte da email, riunione, chat, o altri canali

Aspetta la risposta prima di procedere.

---

## Fase 3 — Acquisizione Risposte

### Modalita' A — DOCX compilato

1. Chiedi il path del DOCX compilato:

> Dammi il path del REVIEW_BR.docx compilato dal funzionale.

2. Converti il DOCX in markdown con pandoc:

```bash
pandoc -f docx -t markdown "<path-docx-compilato>" -o "<cartella-br>/REVIEW_BR_risposte_temp.md"
```

3. Confronta il file convertito con il REVIEW_BR.md originale. Per ogni domanda, cerca differenze nel testo dopo il campo "**Risposta:**":
   - Se il placeholder `*(inserire qui la risposta)*` e' stato sostituito con testo diverso → risposta rilevata
   - Se il placeholder e' invariato o il campo e' assente → nessuna risposta

4. Presenta le risposte rilevate per conferma, una alla volta:

> **Problema bloccante 1 — [Titolo]**
> Domanda: [domanda originale]
> Risposta rilevata: "[testo estratto dal DOCX]"
>
> Confermo questa risposta? (si / no / correggi)

Per ogni risposta, aspetta la conferma. Se l'utente dice "correggi", chiedi il testo corretto.

5. Dopo aver processato tutte le risposte rilevate, chiedi:

> Ho rilevato N risposte dal DOCX. Ci sono altre risposte che il funzionale ha dato a voce o via email e che non sono nel DOCX?

Se si', passa alla Modalita' B per le domande rimanenti.

6. Rimuovi il file temporaneo:

```bash
rm "<cartella-br>/REVIEW_BR_risposte_temp.md"
```

### Modalita' B — Conversazione

Identifica tutte le domande ancora aperte (senza "Risposta del funzionale"). Presentale una alla volta, raggruppate per priorita': prima i bloccanti, poi i non bloccanti.

Per ogni domanda aperta:

> **[Bloccante/Non bloccante] [N] — [Titolo problema]**
>
> Domanda per il funzionale: [domanda originale]
>
> Qual e' la risposta? (scrivi "salta" se non hai ancora la risposta)

Se l'utente scrive "salta", "non lo so", "ancora niente", o simili → segna come ancora aperta e passa alla successiva.

Dopo tutte le domande:

> Risposte raccolte: N su M domande aperte.
> Domande ancora senza risposta: K
>
> Procedo con l'aggiornamento del review?

---

## Fase 4 — Rivalutazione

Per ogni risposta ricevuta, valuta l'impatto:

### Problemi bloccanti

Per ogni bloccante con risposta, valuta se la risposta **risolve** il problema:

- **Risolto**: la risposta chiarisce il punto in modo univoco, il problema non blocca piu' la pianificazione
  → Stato: `Bloccante: Si` diventa `Bloccante: Si → **RISOLTO**`

- **Non risolto**: la risposta e' parziale, ambigua, o solleva nuove domande
  → Stato: resta `Bloccante: Si`, con nota esplicativa
  → Se la risposta genera una nuova domanda, aggiungila come "Domanda di follow-up"

### Problemi non bloccanti

Per ogni non bloccante con risposta, confronta la risposta con l'assunzione proposta nella Parte 2:

- **Assunzione confermata**: la risposta del funzionale conferma l'assunzione
  → Stato assunzione: `Confermata dal funzionale`

- **Assunzione rigettata**: la risposta del funzionale da' un'indicazione diversa
  → Stato assunzione: `Rigettata — risposta: [fatto corretto]`
  → **Segnala all'utente**: "L'assunzione A-XXX era '[assunzione proposta]' ma il funzionale ha risposto '[risposta]'. L'analisi tecnica usera' la risposta del funzionale."

### Presentazione della rivalutazione

Prima di modificare qualsiasi file, presenta il riepilogo:

> ## Rivalutazione
>
> **Bloccanti risolti**: N
> [per ognuno: titolo → sintesi risposta]
>
> **Bloccanti ancora aperti**: N
> [per ognuno: titolo — motivo]
>
> **Assunzioni confermate**: N
> [lista A-XXX]
>
> **Assunzioni rigettate**: N
> [per ognuna: A-XXX — assunzione proposta → fatto corretto]
>
> **Domande ancora aperte**: N
>
> Procedo con l'aggiornamento del REVIEW_BR.md?

Aspetta conferma.

---

## Fase 5 — Aggiornamento REVIEW_BR.md e DOCX

### 5.1 — Aggiornamento problemi (Parte 1)

Per ogni problema che ha ricevuto risposta, aggiorna il blocco nel REVIEW_BR.md aggiungendo i campi:

**Per i bloccanti risolti:**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: Si → **RISOLTO**
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Impatto**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta]
- **Data risposta**: <YYYY-MM-DD>
```

**Per i bloccanti non ancora risolti (risposta parziale):**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: Si
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Impatto**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta parziale]
- **Data risposta**: <YYYY-MM-DD>
- **Nota**: La risposta non risolve completamente il bloccante. [spiegazione]
- **Domanda di follow-up**: [nuova domanda se necessaria]
```

**Per i non bloccanti:**

```
#### N. [Titolo]

- **Categoria**: [invariata]
- **Bloccante**: No
- **Dove**: [invariato]
- **Problema**: [invariato]
- **Domanda per il funzionale**: [invariata]
- **Risposta del funzionale**: [testo della risposta]
- **Data risposta**: <YYYY-MM-DD>
```

### 5.2 — Aggiornamento assunzioni (Parte 2)

Aggiorna la tabella delle assunzioni aggiungendo le colonne "Stato" e "Risposta funzionale":

```
| # | Problema rif. | Assunzione proposta | Rischio se errata | Costo | Stato | Risposta funzionale |
|---|---|---|---|---|---|---|
| A-001 | NB-1 | [assunzione] | [rischio] | Basso | **Confermata** | "Si', confermato" |
| A-002 | NB-2 | [assunzione] | [rischio] | Basso | *In attesa* | — |
| A-005 | NB-5 | [assunzione] | [rischio] | Basso | **Rigettata** | "[risposta diversa]" |
```

### 5.3 — Aggiornamento "Riepilogo per br-analyzer"

Sostituisci l'intera sezione "Riepilogo per br-analyzer" con il formato arricchito:

```
## Riepilogo per br-analyzer

Ultimo aggiornamento: <YYYY-MM-DD> (br-clarify)

### Bloccanti risolti

1. [B1] [Titolo] → [sintesi risposta in 1-2 frasi]
2. [B2] [Titolo] → [sintesi risposta]
[...]

### Bloccanti ancora aperti

N. [BN] [Titolo] — in attesa di risposta
[...]

[Se non ci sono bloccanti aperti:]
Nessun bloccante aperto. Tutti i bloccanti sono stati risolti.

### Stato assunzioni

Assunzioni confermate dal funzionale: A-001, A-003, A-007
Assunzioni adottate (nessuna risposta, si procede con l'assunzione proposta): A-002, A-004
Assunzioni rigettate (risposta diversa dall'assunzione):
- A-005: assunzione era "[testo]" → il funzionale ha risposto "[testo]"
[...]

### Repository coinvolte

- SIGLA (nome) → path
[...]
```

### 5.4 — Rigenerazione DOCX

Dopo aver aggiornato il REVIEW_BR.md, rigenera il DOCX:

```bash
pandoc -f markdown -t docx "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.md" -o "<profiles_repo>/<profilo>/plans/todo/<YYYY-MM-DD>_<nome>/REVIEW_BR.docx"
```

Se il file si trova in `<profiles_repo>/<profilo>/plans/in-progress/`, usa quel path:

```bash
pandoc -f markdown -t docx "<profiles_repo>/<profilo>/plans/in-progress/<YYYY-MM-DD>_<nome>/REVIEW_BR.md" -o "<profiles_repo>/<profilo>/plans/in-progress/<YYYY-MM-DD>_<nome>/REVIEW_BR.docx"
```

### 5.5 — Commit e push su deloitte-profiles

Dopo la rigenerazione del DOCX, effettua commit e push su `deloitte-profiles`:

```bash
git -C "<profiles_repo>" add "<profilo>/plans/"
git -C "<profiles_repo>" commit -m "[br-clarify] <nome>: aggiornato review con risposte funzionale"
git -C "<profiles_repo>" push origin main --quiet
```

---

## Fase 6 — Riepilogo Finale

Presenta all'utente il riepilogo completo:

**Se tutti i bloccanti sono risolti:**

> ## Aggiornamento review completato
>
> **File aggiornati**:
> - `[path]/REVIEW_BR.md` — aggiornato con N risposte
> - `[path]/REVIEW_BR.docx` — rigenerato
>
> **Stato**:
> - Bloccanti: tutti risolti (N su N)
> - Assunzioni confermate: X | Rigettate: Y | In attesa: Z
> - Domande ancora aperte: K
>
> **Il review e' pronto per `br-analyzer`**. Puoi procedere con l'analisi tecnica — le risposte e le assunzioni verranno incorporate automaticamente nel gap report e nel piano di implementazione.

**Se ci sono ancora bloccanti aperti:**

> ## Aggiornamento review completato
>
> **File aggiornati**:
> - `[path]/REVIEW_BR.md` — aggiornato con N risposte
> - `[path]/REVIEW_BR.docx` — rigenerato
>
> **Stato**:
> - Bloccanti risolti: X su N
> - **Bloccanti ancora aperti: Y**
>   [lista dei bloccanti aperti]
> - Assunzioni confermate: X | Rigettate: Y | In attesa: Z
> - Domande ancora aperte: K
>
> **Ci sono ancora bloccanti aperti.** Puoi:
> 1. Attendere le risposte rimanenti e rieseguire `br-clarify`
> 2. Procedere comunque con `br-analyzer` (i bloccanti verranno segnalati come "Da chiarire" nel gap report)

**Se ci sono assunzioni rigettate:**

Aggiungi al riepilogo:

> **Attenzione — Assunzioni rigettate:**
> Le seguenti assunzioni del team tecnico sono state corrette dal funzionale:
> - A-XXX: "[assunzione]" → "[risposta corretta]"
>
> Queste correzioni verranno automaticamente incorporate da `br-analyzer`.

---

## Regole Fondamentali

1. **Mai modificare le domande o le categorie originali** — i problemi restano invariati, solo le risposte vengono aggiunte
2. **Mai sovrascrivere risposte precedenti** — in caso di round multipli, ogni risposta viene aggiunta, non sostituita. Se una risposta deve essere corretta, l'utente lo dice esplicitamente
3. **Sempre chiedere conferma** — prima di scrivere sul REVIEW_BR.md, mostra la rivalutazione e aspetta conferma
4. **Sempre rigenerare il DOCX** — dopo ogni modifica al MD, il DOCX deve essere rigenerato
5. **Preservare la tracciabilita'** — ogni risposta ha la data, ogni assunzione ha lo stato. La storia completa e' sempre leggibile
6. **Non interpretare le risposte** — riporta la risposta del funzionale cosi' com'e'. La rivalutazione (risolto/non risolto, confermata/rigettata) e' una tua valutazione tecnica che presenti all'utente per conferma

---

## Dipendenze

- **`pandoc`** — per conversione DOCX ↔ MD e rigenerazione DOCX. Deve essere disponibile su PATH.
- **`br-reviewer`** — deve essere stato eseguito prima (REVIEW_BR.md deve esistere)
